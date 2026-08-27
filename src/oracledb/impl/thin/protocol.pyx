#------------------------------------------------------------------------------
# Copyright (c) 2020, 2026, Oracle and/or its affiliates.
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
# protocol.pyx
#
# Cython file defining the protocol used by the client when communicating with
# the database (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

cdef class BaseProtocol:

    cdef:
        uint8_t _seq_num
        Transport _transport
        Capabilities _caps
        ReadBuffer _read_buf
        WriteBuffer _write_buf
        bint _in_connect
        bint _txn_in_progress
        bint _break_in_progress
        object _request_lock

    def __init__(self):
        self._caps = Capabilities()
        # mark protocol to indicate that connect is in progress; this prevents
        # the normal break/reset mechanism from firing, which is unnecessary
        # since the connection is going to be immediately closed anyway!
        self._in_connect = True
        self._transport = Transport.__new__(Transport)
        self._transport._max_packet_size = self._caps.sdu
        self._read_buf = ReadBuffer(self._transport, self._caps)
        self._write_buf = WriteBuffer(self._transport, self._caps)

    cdef int _break_external(self) except -1:
        """
        Method for sending a break to the server from an external request. A
        separate write buffer is used in order to avoid a potential conflict
        with any in progress writes.
        """
        cdef WriteBuffer buf
        if not self._break_in_progress:
            self._break_in_progress = True
            if self._caps.supports_oob:
                self._transport.send_oob_break()
            else:
                buf = WriteBuffer(self._transport, self._caps)
                self._send_marker(buf, TNS_MARKER_TYPE_INTERRUPT)

    cdef int _check_is_healthy(self) except -1:
        """
        Checks to see if the connection is healthy. If a read failed on the
        transport earlier, the transport is marked closed.
        """
        if self._read_buf._transport is None \
                or self._read_buf._transport._transport is None:
            self._transport = None

    cdef int _disconnect(self) except -1:
        """
        Disconnects from the transport.
        """
        cdef Transport transport = self._transport
        if transport is not None:
            self._transport = None
            self._read_buf._transport = None
            self._write_buf._transport = None
            transport.disconnect()

    cdef bint _get_is_healthy(self):
        """
        Returns a boolean indicating if the connection is considered healthy.
        """
        self._check_is_healthy()
        return self._transport is not None \
                and self._read_buf._pending_error_num == 0

    cdef int _send_marker(self, WriteBuffer buf, uint8_t marker_type):
        """
        Sends a marker of the specified type to the server.
        Internal method for sending a break to the server.
        """
        buf.start_request(TNS_PACKET_TYPE_MARKER)
        buf.write_uint8(1)
        buf.write_uint8(0)
        buf.write_uint8(marker_type)
        buf.end_request()

    cdef int _process_call_status(self, ThinConnImpl conn_impl,
                                  uint32_t call_status) except -1:
        """
        Processes the call status flags returned by the server.
        """
        self._txn_in_progress = call_status & TNS_EOCS_FLAGS_TXN_IN_PROGRESS
        if call_status & TNS_EOCS_FLAGS_SESS_RELEASE:
            conn_impl._statement_cache.clear_open_cursors()


cdef class Protocol(BaseProtocol):

    def __init__(self):
        BaseProtocol.__init__(self)
        self._request_lock = threading.Lock()

    cdef int _connect_tcp(self, ConnectParamsImpl params,
                          Description description, Address address, str host,
                          int port, str connect_string) except -1:
        """
        Creates a socket on which to communicate using the provided parameters.
        If a proxy is configured, a connection to the proxy is established and
        the target host and port is forwarded to the proxy.
        """
        cdef:
            bint use_proxy = (address.https_proxy is not None)
            double timeout = description.tcp_connect_timeout
            bint use_tcps = (address.protocol == "tcps")
            object connect_info, sock, data, reply, m

        # establish connection to appropriate host/port
        if use_proxy:
            if not use_tcps:
                errors._raise_err(errors.ERR_HTTPS_PROXY_REQUIRES_TCPS)
            connect_info = (address.https_proxy, address.https_proxy_port)
        else:
            connect_info = (host, port)
            if not use_tcps and (params._token is not None
                    or params.access_token_callback is not None):
                errors._raise_err(errors.ERR_ACCESS_TOKEN_REQUIRES_TCPS)
        if not use_proxy and description.use_tcp_fast_open:
            sock = socket.socket(address.ip_family, socket.SOCK_STREAM)
            sock.sendto(connect_string.encode(), socket.MSG_FASTOPEN,
                        connect_info)
        else:
            sock = socket.create_connection(connect_info, timeout)

        # complete connection through proxy, if applicable
        if use_proxy:
            data = f"CONNECT {host}:{port} HTTP/1.0\r\n\r\n"
            sock.send(data.encode())
            reply = sock.recv(1024)
            m = re.search('HTTP/1.[01]\\s+(\\d+)\\s+', reply.decode())
            if m is None or m.groups()[0] != '200':
                errors._raise_err(errors.ERR_PROXY_FAILURE,
                                  response=reply.decode())

        # set socket on transport
        self._transport.set_from_socket(sock, params, description, address)

        # for TCPS connections, OOB processing is not supported and TLS
        # negotiation is required
        if use_tcps:
            self._caps.supports_oob = False
            self._transport.create_ssl_context(params, description, address)
            self._transport.negotiate_tls(sock, address, description)

    cdef int _process_message(self, Message message) except -1:
        cdef uint32_t timeout = message.conn_impl._call_timeout
        try:
            self._read_buf.reset_packets()
            message.send(self._write_buf)
            if not message.is_one_way:
                self._receive_packet(message, check_request_boundary=True)
                message.process(self._read_buf)
        except socket.timeout:
            try:
                self._break_external()
                self._receive_packet(message)
                self._break_in_progress = False
                errors._raise_err(errors.ERR_CALL_TIMEOUT_EXCEEDED,
                                  timeout=timeout)
            except socket.timeout:
                self._disconnect()
                errors._raise_err(errors.ERR_CONNECTION_CLOSED,
                                  "socket timed out while recovering from " \
                                  "previous socket timeout")
            raise
        except MarkerDetected:
            self._reset()
            message.process(self._read_buf)
        except BaseException as e:
            if not self._in_connect \
                    and self._write_buf._packet_sent \
                    and self._read_buf._transport is not None \
                    and self._read_buf._transport._transport is not None:
                self._send_marker(self._write_buf, TNS_MARKER_TYPE_BREAK)
                self._reset()
            raise
        if message.flush_out_binds:
            self._write_buf.start_request(TNS_PACKET_TYPE_DATA)
            self._write_buf.write_uint8(TNS_MSG_TYPE_FLUSH_OUT_BINDS)
            self._write_buf.end_request()
            self._receive_packet(message)
            message.process(self._read_buf)
        if self._break_in_progress:
            try:
                if self._caps.supports_oob:
                    self._send_marker(self._write_buf,
                                      TNS_MARKER_TYPE_INTERRUPT)
                self._receive_packet(message)
            except socket.timeout:
                errors._raise_err(errors.ERR_CONNECTION_CLOSED,
                                  "socket timed out while awaiting break " \
                                  "response from server")
            message.process(self._read_buf)
            self._break_in_progress = False
        self._process_call_status(message.conn_impl, message.call_status)
        if message.error_occurred:
            if message.retry:
                message.error_occurred = False
                return self._process_message(message)
            message._check_and_raise_exception()

    cdef int _process_single_message(self, Message message) except -1:
        """
        Process a single message within a request.
        """
        message.preprocess()
        with self._request_lock:
            self._process_message(message)
            if message.resend:
                self._process_message(message)
        message.postprocess()

    cdef int _receive_packet(self, Message message,
                             bint check_request_boundary=False) except -1:
        cdef:
            bint orig_check_request_boundary
            ReadBuffer buf = self._read_buf
            uint16_t refuse_message_len
            const char_type* ptr
        orig_check_request_boundary = buf._check_request_boundary
        buf._check_request_boundary = \
                check_request_boundary and self._caps.supports_end_of_response
        try:
            buf.wait_for_packets_sync()
        finally:
            buf._check_request_boundary = orig_check_request_boundary
        if buf._current_packet.packet_type == TNS_PACKET_TYPE_MARKER:
            self._reset()
        elif buf._current_packet.packet_type == TNS_PACKET_TYPE_REFUSE:
            self._write_buf._packet_sent = False
            buf.skip_raw_bytes(2)
            buf.read_uint16be(&refuse_message_len)
            if refuse_message_len == 0:
                message.error_info.message = None
            else:
                ptr = buf.read_raw_bytes(refuse_message_len)
                message.error_info.message = ptr[:refuse_message_len].decode()

    cdef int _reset(self) except -1:
        cdef uint8_t marker_type, packet_type

        # send reset marker
        self._send_marker(self._write_buf, TNS_MARKER_TYPE_RESET)

        # read and discard all packets until a reset marker is received
        while True:
            packet_type = self._read_buf._current_packet.packet_type
            if packet_type == TNS_PACKET_TYPE_MARKER:
                self._read_buf.skip_raw_bytes(2)
                self._read_buf.read_ub1(&marker_type)
                if marker_type == TNS_MARKER_TYPE_RESET:
                    break
            self._read_buf.wait_for_packets_sync()

        # read error packet; first skip as many marker packets as may be sent
        # by the server; if the server doesn't handle out-of-band breaks
        # properly, some quit immediately and others send multiple reset
        # markers (this addresses both situations without resulting in strange
        # errors)
        while packet_type == TNS_PACKET_TYPE_MARKER:
            self._read_buf.wait_for_packets_sync()
            packet_type = self._read_buf._current_packet.packet_type
        self._break_in_progress = False


cdef class BaseAsyncProtocol(BaseProtocol):

    cdef:
        object _proxy_waiter

    def __init__(self):
        BaseProtocol.__init__(self)
        self._request_lock = asyncio.Lock()
        self._transport._is_async = True
        self._read_buf._loop = asyncio.get_running_loop()
        # asyncio doesn't support OOB processing
        self._caps.supports_oob = False

    async def _connect_tcp(self, ConnectParamsImpl params,
                           Description description, Address address, str host,
                           int port):
        """
        Creates a socket on which to communicate using the provided parameters.
        If a proxy is configured, a connection to the proxy is established and
        the target host and port is forwarded to the proxy.
        """
        cdef:
            bint use_proxy = (address.https_proxy is not None)
            double timeout = description.tcp_connect_timeout
            bint use_tcps = (address.protocol == "tcps")
            object connect_info, data, reply, m
            str connect_host
            int connect_port

        # establish connection to appropriate host/port
        if use_proxy:
            if not use_tcps:
                errors._raise_err(errors.ERR_HTTPS_PROXY_REQUIRES_TCPS)
            connect_host = address.https_proxy
            connect_port = address.https_proxy_port
        else:
            connect_host = host
            connect_port = port
            if not use_tcps and (params._token is not None
                    or params.access_token_callback is not None):
                errors._raise_err(errors.ERR_ACCESS_TOKEN_REQUIRES_TCPS)
        transport, protocol = await self._read_buf._loop.create_connection(
            lambda: self,
            connect_host,
            connect_port
        )

        # complete connection through proxy, if applicable
        if use_proxy:
            self._proxy_waiter = self._read_buf._loop.create_future()
            data = f"CONNECT {host}:{port} HTTP/1.0\r\n\r\n"
            transport.write(data.encode())
            reply = await self._proxy_waiter
            m = re.search('HTTP/1.[01]\\s+(\\d+)\\s+', reply.decode())
            if m is None or m.groups()[0] != '200':
                errors._raise_err(errors.ERR_PROXY_FAILURE,
                                  response=reply.decode())

        # set socket on transport
        self._transport.set_from_socket(transport, params, description,
                                        address)

        # negotiate TLS, if applicable
        if use_tcps:
            self._transport.create_ssl_context(params, description, address)
            return await self._transport.negotiate_tls_async(self, address,
                                                             description)

    async def _process_message(self, Message message):
        """
        Sends a message to the server and processes its response.
        """
        cdef:
            uint32_t timeout = message.conn_impl._call_timeout
            object timeout_obj = (timeout / 1000) or None
        try:
            coroutine = self._process_message_helper(message)
            await asyncio.wait_for(coroutine, timeout_obj)
        except asyncio.TimeoutError:
            try:
                coroutine = self._process_timeout_helper(message, timeout)
                await asyncio.wait_for(coroutine, timeout_obj)
            except asyncio.TimeoutError:
                self._disconnect()
                errors._raise_err(errors.ERR_CONNECTION_CLOSED,
                                  "socket timed out while recovering from " \
                                  "previous socket timeout")
            raise
        except MarkerDetected:
            await self._reset()
            message.process(self._read_buf)
        except:
            if not self._in_connect \
                    and self._write_buf._packet_sent \
                    and self._transport is not None:
                self._send_marker(self._write_buf, TNS_MARKER_TYPE_BREAK)
                await self._reset()
            raise
        if message.flush_out_binds:
            self._write_buf.start_request(TNS_PACKET_TYPE_DATA)
            self._write_buf.write_uint8(TNS_MSG_TYPE_FLUSH_OUT_BINDS)
            self._write_buf.end_request()
            await self._receive_packet(message)
            message.process(self._read_buf)
        if self._break_in_progress:
            try:
                coroutine = self._receive_packet(message)
                await asyncio.wait_for(coroutine, timeout_obj)
            except asyncio.TimeoutError:
                self._disconnect()
                errors._raise_err(errors.ERR_CONNECTION_CLOSED,
                                  "socket timed out while awaiting break " \
                                  "response from server")
            message.process(self._read_buf)
            self._break_in_progress = False
        self._process_call_status(message.conn_impl, message.call_status)
        if message.error_occurred:
            if message.retry:
                message.error_occurred = False
                return await self._process_message(message)
            message._check_and_raise_exception()

    async def _process_message_helper(self, Message message):
        """
        Helper routine that is called to process a message within a timeout.
        """
        self._read_buf.reset_packets()
        message.send(self._write_buf)
        if not message.is_one_way:
            await self._receive_packet(message, check_request_boundary=True)
            while True:
                try:
                    message.process(self._read_buf)
                    break
                except OutOfPackets:
                    await self._receive_packet(message)
                    message.on_out_of_packets()
                    self._read_buf.restore_point()

    async def _process_single_message(self, Message message):
        """
        Process a single message within a request.
        """
        message.preprocess()
        async with self._request_lock:
            if isinstance(message, EndPipelineMessage):
                await message.process_pipeline()
            else:
                await self._process_message(message)
            if message.resend:
                await self._process_message(message)
        await message.postprocess_async()

    async def _process_timeout_helper(self, Message message, uint32_t timeout):
        """
        Helper routine that is called to process a timeout.
        """
        self._break_external()
        await self._receive_packet(message)
        self._break_in_progress = False
        errors._raise_err(errors.ERR_CALL_TIMEOUT_EXCEEDED, timeout=timeout)

    async def _receive_packet(self, Message message,
                              bint check_request_boundary=False,
                              bint in_pipeline=False):
        cdef:
            ReadBuffer buf = self._read_buf
            uint16_t refuse_message_len
            const char_type* ptr
        buf._check_request_boundary = \
                check_request_boundary and self._caps.supports_end_of_response
        await buf.wait_for_packets_async()
        buf._check_request_boundary = False
        if buf._current_packet.packet_type == TNS_PACKET_TYPE_MARKER:
            if in_pipeline:
                # skip to next packet as the marker packet doesn't contain any
                # useful information
                buf.wait_for_packets_sync()
            else:
                await self._reset()
        elif buf._current_packet.packet_type == TNS_PACKET_TYPE_REFUSE:
            self._write_buf._packet_sent = False
            buf.skip_raw_bytes(2)
            buf.read_uint16be(&refuse_message_len)
            if refuse_message_len == 0:
                message.error_info.message = None
            else:
                ptr = buf.read_raw_bytes(refuse_message_len)
                message.error_info.message = ptr[:refuse_message_len].decode()

    async def _reset(self):
        cdef:
            uint8_t marker_type, packet_type

        # send reset marker
        self._send_marker(self._write_buf, TNS_MARKER_TYPE_RESET)

        # read and discard all packets until a reset marker is received
        while True:
            packet_type = self._read_buf._current_packet.packet_type
            if packet_type == TNS_PACKET_TYPE_MARKER:
                self._read_buf.skip_raw_bytes(2)
                self._read_buf.read_ub1(&marker_type)
                if marker_type == TNS_MARKER_TYPE_RESET:
                    break
            await self._read_buf.wait_for_packets_async()

        # read error packet; first skip as many marker packets as may be sent
        # by the server; if the server doesn't handle out-of-band breaks
        # properly, some quit immediately and others send multiple reset
        # markers (this addresses both situations without resulting in strange
        # errors)
        while packet_type == TNS_PACKET_TYPE_MARKER:
            await self._read_buf.wait_for_packets_async()
            packet_type = self._read_buf._current_packet.packet_type
        self._break_in_progress = False

    def connection_lost(self, exc):
        """
        Called when a connection has been lost. The presence of an exception
        indicates an abornmal loss of the connection. If in the process of
        establishing a connection, losing the connection is ignored since this
        can happen normally when a listener redirect is encountered.
        """
        if not self._in_connect:
            self._transport = None
            self._read_buf._transport = None
            self._write_buf._transport = None
            self._read_buf._pending_error_num = TNS_ERR_SESSION_SHUTDOWN
        if self._read_buf._waiter is not None \
                and not self._read_buf._waiter.done():
            error = errors._create_err(errors.ERR_CONNECTION_CLOSED)
            self._read_buf._waiter.set_exception(error.exc_type(error))

    def data_received(self, data):
        """
        Called when data has been received on the transport.
        """
        cdef:
            bint notify_waiter = False
            Packet packet
        if self._proxy_waiter is not None:
            self._proxy_waiter.set_result(data)
            self._proxy_waiter = None
        else:
            packet = self._transport.extract_packet(data)
            while packet is not None:
                self._read_buf._process_packet(packet, &notify_waiter, False)
                if notify_waiter:
                    self._read_buf.notify_packet_received()
                packet = self._transport.extract_packet()


class AsyncProtocol(BaseAsyncProtocol, asyncio.Protocol):
    pass
