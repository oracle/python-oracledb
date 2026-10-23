#------------------------------------------------------------------------------
# Copyright (c) 2023, 2026, Oracle and/or its affiliates.
#
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl and Apache License
# 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose
# either license.
#
# If you elect to accept the software under the Apache License, Version 2.0,
# the following applies:
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# transport.pyx
#
# Cython file defining the transport class used by the client for sending and
# receiving packets (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

cdef bint DEBUG_PACKETS = ("PYO_DEBUG_PACKETS" in os.environ)

cdef class Transport:

    cdef:
        object _transport
        object _ssl_context
        TlsWrapper _tls_wrapper
        str _ssl_sni_data
        Address _address
        uint32_t _transport_num
        ssize_t _max_packet_size
        uint32_t _op_num
        bytes _session_key
        bytes _server_verify_digest
        bytes _server_verify_key
        bytes _server_verify_iv
        bytes _partial_buf
        bint _requires_verify_write
        bint _requires_verify_read
        bint _full_packet_size
        bint _is_async

    cdef str _calc_sni_data(self, Description description):
        """
        Calculates the string used for the special SNI handling that allows one
        of the TLS negotiations to be bypassed.
        """
        cdef str server_type_part = ""
        if description.server_type is not None:
            server_type_part = f".T1.{description.server_type[:1]}"
        return (
            f"S{len(description.service_name)}.{description.service_name}"
            f"{server_type_part}"
            f".V3.{TNS_VERSION_DESIRED}"
        )

    cdef bytes _get_certificate(self):
        """
        Returns the certificate in use for TLS.
        """
        if self._tls_wrapper is not None:
            ssl_obj = self._tls_wrapper.ssl_obj
        elif self._is_async:
            ssl_obj = self._transport.get_extra_info("ssl_object")
        else:
            ssl_obj = self._transport
        return ssl_obj.getpeercert(binary_form=True)

    cdef str _get_debugging_header(self, str operation):
        """
        Returns the header line used for debugging packets.
        """
        cdef str header
        self._op_num += 1
        current_date = datetime.datetime.now().isoformat(
            sep=" ",
            timespec="milliseconds"
        )
        return (
            f"{current_date} "
            f"{operation} [op {self._op_num}] on socket {self._transport_num}"
        )

    cdef tuple _get_server_verify_key_and_iv(self, uint16_t iterations):
        """
        Returns the key and iv used for encryption during server verification.
        """
        cdef bytes encoded_key, derived_key
        encoded_key = base64.b64encode(self._session_key)
        derived_key = get_derived_key(encoded_key, bytes(32), 64, iterations)
        return (derived_key[:32], derived_key[32:48])

    cdef bytes _get_server_verify_request_data(self, WriteBuffer buf,
                                               bytes packet_data):
        """
        Takes the packet data and creates the server verify request data from
        it and the certificate in use for TLS. Returns the data that needs to
        be sent to the server to request verification.
        """
        cdef:
            uint16_t iterations = 256, tag_len = 16
            bytes data, key, iv
        try:
            # remove extra padding in order to write server verify structure
            if self._tls_wrapper is not None:
                packet_data = packet_data[DATA_PACKET_HEADER_SIZE:]
                buf.set_padding_size(64)
                buf._pos = DATA_PACKET_HEADER_SIZE
            else:
                buf.set_padding_size(0)
                buf._pos = 0

            # write key verify data
            self._server_verify_digest = hmac.digest(
                self._session_key, self._get_certificate(), "sha512"
            )
            buf.write_uint16be(TNS_SERVER_VERIFY_HEADER)
            buf.write_uint16be(TNS_SERVER_VERIFY_TYPE_HMAC_SHA512)
            buf.write_uint16be(<uint16_t> len(self._server_verify_digest))
            buf.write_bytes(self._server_verify_digest)
            buf.write_uint16be(TNS_SERVER_VERIFY_FOOTER)

            # encrypt data using derived key
            key, iv = self._get_server_verify_key_and_iv(iterations)
            encrypted_data = encrypt_gcm(key, packet_data, iv)

            # write encrypted data block
            buf.write_uint16be(TNS_SERVER_VERFIY_ENCRYPT_AES256_GCM)
            buf.write_uint16be(iterations)
            buf.write_uint16be(tag_len)
            buf.write_bytes(encrypted_data[-tag_len:])
            buf.write_uint16be(<uint16_t> len(encrypted_data) - tag_len)
            buf.write_bytes(encrypted_data[:-tag_len])
            data = buf._data[:buf._pos]
            if DEBUG_PACKETS:
                self._print_packet("Sending server verification", data)

            # server verification is needed for the response
            self._requires_verify_write = False
            self._requires_verify_read = True
            return data
        except Exception as e:
            errors._raise_err(errors.ERR_SERVER_VERIFY_FAILED, cause=e)

    cdef bytes _get_server_verify_response_data(self, bytes packet_data):
        """
        Returns the decrypted first packet data after verifying the server.
        """
        cdef:
            uint16_t temp16, verify_type, encrypt_type, data_len, iterations
            Buffer buf = Buffer.__new__(Buffer)
            bytes data, tag
        try:
            # read key verify data
            buf._populate_from_bytes(packet_data)
            if DEBUG_PACKETS:
                self._print_packet("Receiving server verification", packet_data)
            buf.read_uint16be(&temp16)
            if temp16 != TNS_SERVER_VERIFY_HEADER:
                errors._raise_err(errors.ERR_SERVER_VERIFY_FAILED)
            buf.read_uint16be(&verify_type)
            buf.read_uint16be(&data_len)
            data = buf.read_raw_bytes(data_len)[:data_len]
            buf.read_uint16be(&temp16)
            if temp16 != TNS_SERVER_VERIFY_FOOTER:
                errors._raise_err(errors.ERR_SERVER_VERIFY_FAILED)

            # verify server
            cert_obj = x509.load_der_x509_certificate(self._get_certificate())
            public_key = cert_obj.public_key()
            if verify_type == TNS_SERVER_VERIFY_TYPE_ECDSA_SHA256:
                public_key.verify(
                    data, self._server_verify_digest, ec.ECDSA(hashes.SHA256())
                )
            elif verify_type == TNS_SERVER_VERIFY_TYPE_RSA_SHA256:
                public_key.verify(
                    data,
                    self._server_verify_digest,
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )
            else:
                errors._raise_err(errors.ERR_SERVER_VERIFY_FAILED)

            # read encrypted data block
            buf.read_uint16be(&encrypt_type)
            if encrypt_type != TNS_SERVER_VERFIY_ENCRYPT_AES256_GCM:
                errors._raise_err(errors.ERR_SERVER_VERIFY_FAILED)
            buf.read_uint16be(&iterations)
            buf.read_uint16be(&data_len)
            tag = buf.read_raw_bytes(data_len)[:data_len]
            buf.read_uint16be(&data_len)
            data = buf.read_raw_bytes(data_len)[:data_len]

            # decrypt data using derived key
            key, iv = self._get_server_verify_key_and_iv(iterations)
            data = decrypt_gcm(key, data + tag, iv)

            # server verification is no longer needed
            self._requires_verify_read = False
            return data
        except exceptions.DatabaseError:
            raise
        except Exception as e:
            errors._raise_err(errors.ERR_SERVER_VERIFY_FAILED, cause=e)

    cdef int _print_output(self, str text) except -1:
        """
        Prints and flushes the text to stdout to ensure that multiple
        threads don't lose output due to buffering.
        """
        print(text + "\n", flush=True)

    cdef int _print_packet(self, str operation, object data) except -1:
        """
        Print the packet content in a format suitable for debugging.
        """
        offset = 0
        hex_data = memoryview(data).hex().upper()
        output_lines = [self._get_debugging_header(operation)]
        while hex_data:
            line_hex_data = hex_data[:16]
            hex_data = hex_data[16:]
            hex_dump_values = []
            printable_values = []
            for i in range(0, len(line_hex_data), 2):
                hex_byte = line_hex_data[i:i + 2]
                hex_dump_values.append(hex_byte)
                byte_val = ord(bytes.fromhex(hex_byte))
                char_byte = chr(byte_val)
                if char_byte.isprintable() and byte_val < 128 \
                        and char_byte != " ":
                    printable_values.append(char_byte)
                else:
                    printable_values.append(".")
            while len(hex_dump_values) < 8:
                hex_dump_values.append("  ")
                printable_values.append(" ")
            output_lines.append(
                f'{offset:04} : {" ".join(hex_dump_values)} '
                f'|{"".join(printable_values)}|'
            )
            offset += 8
        self._print_output("\n".join(output_lines))

    cdef int disconnect(self) except -1:
        """
        Disconnects the transport.
        """
        if self._transport is not None:
            if DEBUG_PACKETS:
                self._print_output(
                    self._get_debugging_header("Disconnecting transport")
                )
            self._transport.close()
            self._transport = None

    cdef int create_ssl_context(self, ConnectParamsImpl params,
                                Description description,
                                Address address) except -1:
        """
        Creates the SSL context used for establishing TLS communications
        between the database and the client.
        """

        # start with a default SSL context, unless a custom one is supplied
        self._ssl_context = params.ssl_context
        if self._ssl_context is None:
            self._ssl_context = ssl.create_default_context()

        # set the minimum and maximum versions of the TLS protocol
        if description.ssl_version is not None:
            self._ssl_context.minimum_version = description.ssl_version
            self._ssl_context.maximum_version = description.ssl_version

        # if the platform is macOS, check if the certifi package is installed;
        # if certifi is not installed, load the certificates from the macOS
        # keychain in PEM format
        if sys.platform == "darwin" and certifi is None:
            global macos_certs
            if macos_certs is None:
                certs = subprocess.run(["security", "find-certificate",
                                        "-a", "-p"],
                                        stdout=subprocess.PIPE).stdout
                macos_certs = certs.decode("utf-8")
            self._ssl_context.load_verify_locations(cadata=macos_certs)

        # if a wallet is specified, either mTLS is being used or a set of
        # certificates is being loaded to validate the server; note that a
        # special value of SYSTEM is also treated as equivalent to having no
        # wallet location specified (keyword added in 23)
        if description.wallet_location is not None \
                and description.wallet_location.upper() != "SYSTEM":
            pem_file_name = os.path.join(description.wallet_location,
                                         PEM_WALLET_FILE_NAME)
            if not os.path.exists(pem_file_name):
                errors._raise_err(errors.ERR_WALLET_FILE_MISSING,
                                  name=pem_file_name)
            self._ssl_context.load_verify_locations(pem_file_name)
            wallet_password = params._get_wallet_password()
            try:
                self._ssl_context.load_cert_chain(pem_file_name,
                                                  password=wallet_password)
            except ssl.SSLError:
                pass

        # the SSL host name is not checked but the SSL server DN matching
        # algorithm is run instead after the TLS connection has been
        # established
        self._ssl_context.check_hostname = False

        # when using EZTLS, no certificate validation takes place
        if params.use_eztls:
            self._ssl_context.verify_mode = ssl.CERT_NONE

        # calculate the SNI data to send to the server, if applicable
        if description.use_sni:
            self._ssl_sni_data = self._calc_sni_data(description)
        else:
            self._ssl_sni_data = None

    cdef Packet extract_packet(self, bytes data=None):
        """
        Extracts a packet from the data, if possible (after first appending it
        to the partial buffer, if applicable). Any extra data not needed by the
        packet is stored in the partial buffer for a later call to this
        function.
        """
        cdef:
            ssize_t size, packet_size
            Packet packet
            char_type *ptr

        # update the partial buffer with the new data
        if data is not None:
            if self._partial_buf is None:
                self._partial_buf = data
            else:
                self._partial_buf += data
        size = 0 if self._partial_buf is None else len(self._partial_buf)
        if size > 0 and self._requires_verify_read \
                and self._tls_wrapper is None:
            self._partial_buf = \
                    self._get_server_verify_response_data(self._partial_buf)

        # if enough bytes for the packet header, extract the packet size
        if size >= PACKET_HEADER_SIZE:

            # extract the packet size
            ptr = <char_type*> self._partial_buf
            if self._full_packet_size:
                packet_size = decode_uint32be(ptr)
            else:
                packet_size = decode_uint16be(ptr)

            # if enough bytes are available for the packet, return it
            if size >= packet_size:
                packet = Packet.__new__(Packet)
                packet.packet_size = packet_size
                packet.packet_type = ptr[4]
                packet.packet_flags = ptr[5]

                # store the packet buffer and adjust the partial buffer, as
                # needed
                if size == packet_size:
                    packet.buf = self._partial_buf
                    self._partial_buf = None
                else:
                    packet.buf = self._partial_buf[:packet_size]
                    self._partial_buf = self._partial_buf[packet_size:]

                # decrypt packet, if applicable
                if self._tls_wrapper is not None:
                    packet.buf = \
                            self._tls_wrapper.process_incoming_data(packet.buf)
                    if self._requires_verify_read:
                        packet.buf = packet.buf[:DATA_PACKET_HEADER_SIZE] + \
                                self._get_server_verify_response_data(
                                    packet.buf[DATA_PACKET_HEADER_SIZE:]
                                )
                        packet.packet_size = len(packet.buf)

                # display packet, if requested
                if DEBUG_PACKETS:
                    self._print_packet("Receiving packet", packet.buf)
                return packet

    cdef tuple get_host_info(self):
        """
        Return a 2-tuple supplying the host and port to which the transport is
        connected.
        """
        cdef object sock
        if self._is_async:
            sock = self._transport.get_extra_info('socket')
        else:
            sock = self._transport
        return sock.getpeername()[:2]

    cdef int has_data_ready(self, bint *data_ready) except -1:
        """
        Returns true if data is ready to be read on the transport.
        """
        socket_list = [self._transport]
        read_socks, _, _ = select.select(socket_list, [], [], 0)
        data_ready[0] = bool(read_socks)

    cdef int negotiate_tls(self, object sock, ConnectParamsImpl params,
                           Address address, Description description) except -1:
        """
        Negotiate TLS on the socket.
        """
        if DEBUG_PACKETS:
            self._print_output(self._get_debugging_header("Negotiate TLS"))
        self._transport = self._ssl_context.wrap_socket(
            sock, server_hostname=self._ssl_sni_data
        )
        if description.ssl_server_dn_match and not params.use_eztls:
            check_server_dn(self._transport, description.ssl_server_cert_dn,
                            address.host)

    cdef int renegotiate_tls(self, ConnectParamsImpl params, Address address,
                             Description description) except -1:
        """
        Renegotiate TLS on the socket.
        """
        orig_sock = self._transport
        sock = socket.socket(family=orig_sock.family, type=orig_sock.type,
                             proto=orig_sock.proto, fileno=orig_sock.detach())
        self.negotiate_tls(sock, params, address, description)

    async def negotiate_tls_async(self, BaseAsyncProtocol protocol,
                                  ConnectParamsImpl params, Address address,
                                  Description description):
        """
        Negotiate TLS on the socket asynchronously.
        """
        if DEBUG_PACKETS:
            self._print_output(self._get_debugging_header("Negotiate TLS"))
        orig_transport = self._transport
        loop = protocol._read_buf._loop
        self._transport = await loop.start_tls(
            self._transport, protocol,
            self._ssl_context,
            server_hostname=self._ssl_sni_data
        )
        if description.ssl_server_dn_match and not params.use_eztls:
            sock = self._transport.get_extra_info("ssl_object")
            check_server_dn(sock, description.ssl_server_cert_dn, address.host)
        return orig_transport

    cdef int send_oob_break(self) except -1:
        """
        Sends an out-of-band break on the transport.
        """
        if DEBUG_PACKETS:
            self._print_output(
                self._get_debugging_header("Sending out of band break")
            )
        self._transport.send(b"!", socket.MSG_OOB)

    cdef int set_from_socket(self, object transport,
                             ConnectParamsImpl params,
                             Description description,
                             Address address) except -1:
        """
        Sets the transport from a socket.
        """
        cdef object sock
        if self._is_async:
            sock = transport.get_extra_info('socket')
        else:
            sock = transport
        if description.expire_time > 0:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            if hasattr(socket, "TCP_KEEPIDLE") \
                    and hasattr(socket, "TCP_KEEPINTVL") \
                    and hasattr(socket, "TCP_KEEPCNT"):
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE,
                                description.expire_time * 60)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 6)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 10)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        if sock.gettimeout() != 0:
            sock.settimeout(None)
        self._transport = transport
        self._address = address
        self._transport_num = sock.fileno()

    cdef Packet read_packet(self, bint raise_exc=True):
        """
        Reads a packet from the transport.
        """
        cdef:
            Packet packet
            bytes data
        packet = self.extract_packet()
        while packet is None:
            try:
                data = self._transport.recv(self._max_packet_size)
            except ConnectionResetError as e:
                self._transport = None
                if not raise_exc:
                    return None
                errors._raise_err(errors.ERR_CONNECTION_CLOSED, str(e),
                                  cause=e)
            if len(data) == 0:
                self.disconnect()
                if not raise_exc:
                    return None
                errors._raise_err(errors.ERR_CONNECTION_CLOSED)
            packet = self.extract_packet(data)
        return packet

    cdef int set_timeout(self, double value) except -1:
        """
        Sets the timeout on the transport.
        """
        if not self._is_async:
            self._transport.settimeout(value or None)

    cdef int write_packet(self, WriteBuffer buf) except -1:
        """
        Writes a packet on the transport.
        """
        cdef bytes data = buf._data[:buf._pos]
        if DEBUG_PACKETS:
            self._print_packet(f"Sending request {buf._request_name}", data)
        if self._requires_verify_write:
            data = self._get_server_verify_request_data(buf, data)
        if self._tls_wrapper is not None:
            data = self._tls_wrapper.process_outgoing_data(data)
        try:
            if self._is_async:
                self._transport.write(data)
            else:
                self._transport.send(data)
        except OSError as e:
            self.disconnect()
            errors._raise_err(errors.ERR_CONNECTION_CLOSED, cause=e)
