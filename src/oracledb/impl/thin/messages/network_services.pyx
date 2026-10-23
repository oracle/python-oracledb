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
# network_services.pyx
#
# Cython file defining the messages that are sent to the database and the
# responses that are received by the client for negotiating the network
# services (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

# network data types
cdef enum:
    TNS_NETWORK_TYPE_STRING = 0
    TNS_NETWORK_TYPE_RAW = 1
    TNS_NETWORK_TYPE_UB1 = 2
    TNS_NETWORK_TYPE_UB2 = 3
    TNS_NETWORK_TYPE_VERSION = 5
    TNS_NETWORK_TYPE_STATUS = 6

# network service numbers
cdef enum:
    TNS_NETWORK_SERVICE_AUTH = 1
    TNS_NETWORK_SERVICE_ENCRYPTION = 2
    TNS_NETWORK_SERVICE_DATA_INTEGRITY = 3
    TNS_NETWORK_SERVICE_SUPERVISOR = 4

# network authentication service constants
cdef enum:
    TNS_NETWORK_AUTH_TYPE_CLIENT_SERVER = 0xe0e1
    TNS_NETWORK_AUTH_STATUS_OK = 0xfaff
    TNS_NETWORK_AUTH_STATUS_DONT_USE_AUTH = 0xfbff
    TNS_NETWORK_AUTH_STATUS_NOT_REQUIRED = 0xfcff

# other network services constants
cdef uint32_t TNS_NETWORK_MAGIC = 0xdeadbeef
cdef uint32_t TNS_NETWORK_VERSION = 0x17700000   # 23.7.0.0.0
cdef uint8_t TNS_NETWORK_ALG_TLS = 21

cdef class NetworkService:

    cdef:
        TlsWrapper tls_wrapper

    cdef uint16_t get_data_size(self, bint in_negotiation):
        """
        Returns the size of the data sent by the service.
        """
        return 0

    cdef uint16_t get_header_size(self):
        """
        Returns the size of the header (service type plus number of sub packets
        plus error).
        """
        return 2 + 2 + 4

    cdef int on_enable_eztls(self):
        """
        Called when EZTLS has been enabled and performs any necessary setup
        specific to the service.
        """
        pass

    cdef int on_complete_negotiation(self) except -1:
        """
        Called when negotiation is taking place and performs any necessary
        setup for the negotiation specific to the service.
        """
        pass

    cdef int read_response(self, ReadBuffer buf,
                           NetworkServicesMessage message) except -1:
        """
        Reads the response from the server for the given service.
        """
        cdef:
            uint16_t num_subpackets, i
            uint32_t temp32
        buf.skip_raw_bytes(2)               # service num
        buf.read_uint16be(&num_subpackets)
        buf.read_uint32be(&temp32)          # error num
        if temp32 != 0:
            errors._raise_err(errors.ERR_LISTENER_REFUSED_CONNECTION,
                              error_code=temp32)
        self.read_subpackets(buf, num_subpackets, message)

    cdef int read_status(self, ReadBuffer buf, uint16_t *status) except -1:
        """
        Reads the status from the response.
        """
        buf.skip_raw_bytes(4)               # length and data type
        buf.read_uint16be(status)

    cdef int read_subpackets(self, ReadBuffer buf,
                             uint16_t num_subpackets,
                             NetworkServicesMessage message) except -1:
        """
        Reads the sub packets from the response and discards them.
        """
        for i in range(num_subpackets):
            self.skip_subpacket(buf)

    cdef int skip_subpacket(self, ReadBuffer buf) except -1:
        """
        Skips the subpacket data from the server response.
        """
        cdef uint16_t data_length, data_type
        buf.read_uint16be(&data_length)
        buf.skip_raw_bytes(2)               # data type
        buf.skip_raw_bytes(data_length)

    cdef int write_data(self, WriteBuffer buf, bint in_negotiation,
                        bytes connection_id_bytes) except -1:
        """
        Writes the data for the service to the buffer.
        """
        raise NotImplementedError()

    cdef int write_header(self, WriteBuffer buf, uint16_t service_num,
                          uint16_t num_sub_packets) except -1:
        """
        Writes the service header to the buffer.
        """
        buf.write_uint16be(service_num)
        buf.write_uint16be(num_sub_packets)
        buf.write_uint32be(0)

    cdef int write_version(self, WriteBuffer buf) except -1:
        """
        Writes the version to the buffer.
        """
        buf.write_uint16be(4)           # length
        buf.write_uint16be(TNS_NETWORK_TYPE_VERSION)
        buf.write_uint32be(TNS_NETWORK_VERSION)


cdef class AuthenticationService(NetworkService):

    cdef uint16_t get_data_size(self, bint in_negotiation):
        """
        Returns the size of the data sent by the service. All that is currently
        supported is TCPS authentication.
        """
        cdef uint16_t data_size
        if in_negotiation:
            return 0
        data_size = self.get_header_size() + 8 + 6 + 6
        if self.tls_wrapper is None:
            data_size += 5 + 8
        return data_size

    cdef int read_subpackets(self, ReadBuffer buf,
                             uint16_t num_subpackets,
                             NetworkServicesMessage message) except -1:
        """
        Reads the sub packets from the response.
        """
        cdef uint16_t status
        self.skip_subpacket(buf)            # version
        self.read_status(buf, &status)
        if status == TNS_NETWORK_AUTH_STATUS_OK:
            message.external_auth_configured = True
            self.skip_subpacket(buf)        # skip ids (only one allowed)
            self.skip_subpacket(buf)        # skip string (only one allowed)
        elif status != TNS_NETWORK_AUTH_STATUS_DONT_USE_AUTH:
            errors._raise_err(errors.ERR_ANO_STATUS_FAILURE,
                              service_name="authentication")

    cdef int write_data(self, WriteBuffer buf, bint in_negotiation,
                        bytes connection_id_bytes) except -1:
        """
        Writes the data for the service to the buffer.
        """
        cdef uint16_t num_sub_packets = 3

        # nothing to write in negotiation
        if in_negotiation:
            return 0

        # write header and version (sub packet 1)
        if self.tls_wrapper is None:
            num_sub_packets += 2
        self.write_header(
            buf, TNS_NETWORK_SERVICE_AUTH, num_sub_packets=num_sub_packets
        )
        self.write_version(buf)

        # write auth type (sub packet 2)
        buf.write_uint16be(2)           # length
        buf.write_uint16be(TNS_NETWORK_TYPE_UB2)
        buf.write_uint16be(TNS_NETWORK_AUTH_TYPE_CLIENT_SERVER)

        # write status (sub packet 3)
        buf.write_uint16be(2)           # length
        buf.write_uint16be(TNS_NETWORK_TYPE_STATUS)
        buf.write_uint16be(TNS_NETWORK_AUTH_STATUS_NOT_REQUIRED)

        if self.tls_wrapper is None:
            # write authentication ids (sub packet 4)
            buf.write_uint16be(1)           # length
            buf.write_uint16be(TNS_NETWORK_TYPE_UB1)
            buf.write_uint8(2)              # TCPS authentication id

            # write authentication names (sub packet 5)
            buf.write_uint16be(4)           # length
            buf.write_uint16be(TNS_NETWORK_TYPE_STRING)
            buf.write_bytes(b"tcps")        # TCPS authentication name


cdef class DataIntegrityService(NetworkService):

    cdef uint16_t get_data_size(self, bint in_negotiation):
        """
        Returns the size of the service.
        """
        if in_negotiation:
            return 0
        return self.get_header_size() + 8 + 5

    cdef int write_data(self, WriteBuffer buf, bint in_negotiation,
                        bytes connection_id_bytes) except -1:
        """
        Writes the data for the service to the buffer.
        """
        # nothing to write in negotiation
        if in_negotiation:
            return 0

        # write header and version (sub packet 1)
        self.write_header(buf, TNS_NETWORK_SERVICE_DATA_INTEGRITY,
                          num_sub_packets=2)
        self.write_version(buf)

        # write options (sub packet 2)
        buf.write_uint16be(1)               # length
        buf.write_uint16be(TNS_NETWORK_TYPE_RAW)
        buf.write_uint8(0)                  # no data integrity


cdef class EncryptionService(NetworkService):
    cdef:
        bytes outgoing_data

    cdef uint16_t get_data_size(self, bint in_negotiation):
        """
        Returns the size of the service.
        """
        cdef uint16_t data_size
        if in_negotiation:
            return self.get_header_size() + 4 + len(self.outgoing_data)
        data_size = self.get_header_size() + 8 + 5
        if self.tls_wrapper is not None:
            data_size += 1 + len(self.outgoing_data) + 4
        return data_size

    cdef int on_enable_eztls(self):
        """
        Called when EZTLS has been enabled and performs any necessary setup
        specific to the service.
        """
        self.outgoing_data = self.tls_wrapper.read_outgoing_data()

    cdef int on_complete_negotiation(self) except -1:
        """
        Called when negotiation is taking place and performs any necessary
        setup for the negotiation specific to the service.
        """
        self.outgoing_data = self.tls_wrapper.read_outgoing_data()

    cdef int read_subpackets(self, ReadBuffer buf,
                             uint16_t num_subpackets,
                             NetworkServicesMessage message) except -1:
        """
        Reads the sub packets from the response.
        """
        cdef:
            uint16_t data_length, i
            bint enabled = False
            const char_type *ptr
            uint8_t alg
        if self.tls_wrapper is None:
            return NetworkService.read_subpackets(
                self, buf, num_subpackets, message
            )
        self.skip_subpacket(buf)            # version
        buf.read_uint16be(&data_length)
        buf.skip_raw_bytes(2)               # data type
        for i in range(data_length):
            buf.read_ub1(&alg)
            if alg == TNS_NETWORK_ALG_TLS:
                enabled = True
        if not enabled:
            errors._raise_err(errors.ERR_SERVER_REFUSED_EZTLS, protocol="tcp")
        buf.read_uint16be(&data_length)
        buf.skip_raw_bytes(2)               # data type
        ptr = buf.read_raw_bytes(data_length)
        self.outgoing_data = \
                self.tls_wrapper.continue_handshake(ptr[:data_length])

    cdef int write_data(self, WriteBuffer buf, bint in_negotiation,
                        bytes connection_id_bytes) except -1:
        """
        Writes the data for the service to the buffer.
        """
        cdef uint16_t num_sub_packets, num_algos

        # determine the number of options (initial packet) and subpackets
        if in_negotiation:
            num_sub_packets = 1
        elif self.tls_wrapper is not None:
            num_sub_packets = 3
            num_algos = 2
        else:
            num_sub_packets = 2
            num_algos = 1

        self.write_header(buf, TNS_NETWORK_SERVICE_ENCRYPTION,
                          num_sub_packets=num_sub_packets)

        # in negotiation, only write the TLS wrapper outgoing data
        if in_negotiation:
            buf.write_uint16be(<uint16_t> len(self.outgoing_data))
            buf.write_uint16be(TNS_NETWORK_TYPE_RAW)
            buf.write_bytes(self.outgoing_data)

        # otherwise, write the normal data
        else:
            self.write_version(buf)

            # write options (sub packet 2)
            buf.write_uint16be(num_algos)       # length (number of algorithms)
            buf.write_uint16be(TNS_NETWORK_TYPE_RAW)
            buf.write_uint8(0)                  # no encryption
            if self.tls_wrapper is not None:
                buf.write_uint8(TNS_NETWORK_ALG_TLS)

            # write ClientHello (sub packet 3)
            if self.tls_wrapper is not None:
                buf.write_uint16be(<uint16_t> len(self.outgoing_data))
                buf.write_uint16be(TNS_NETWORK_TYPE_RAW)
                buf.write_bytes(self.outgoing_data)


cdef class SupervisorService(NetworkService):

    cdef uint16_t get_data_size(self, bint in_negotiation):
        """
        Returns the size of the service.
        """
        if in_negotiation:
            return 0
        return self.get_header_size() + 8 + 12 + 22

    cdef int read_subpackets(self, ReadBuffer buf,
                             uint16_t num_subpackets,
                             NetworkServicesMessage message) except -1:
        """
        Reads the sub packets from the response.
        """
        cdef uint16_t status
        self.skip_subpacket(buf)            # version
        self.read_status(buf, &status)
        if status != 0x1f:
            errors._raise_err(errors.ERR_ANO_STATUS_FAILURE,
                              service_name="supervisor")
        self.skip_subpacket(buf)            # array of services

    cdef int write_data(self, WriteBuffer buf, bint in_negotiation,
                        bytes connection_id_bytes) except -1:
        """
        Writes the data for the service to the buffer.
        """

        # nothing to write in negotiation
        if in_negotiation:
            return 0

        # write header and version (sub packet 1)
        self.write_header(buf, TNS_NETWORK_SERVICE_SUPERVISOR,
                          num_sub_packets=3)
        self.write_version(buf)

        # write CID (sub packet 2)
        buf.write_uint16be(8)           # length
        buf.write_uint16be(TNS_NETWORK_TYPE_RAW)
        buf.write_bytes(connection_id_bytes[:8])

        # write supervised services array (sub packet 3)
        buf.write_uint16be(18)          # length
        buf.write_uint16be(TNS_NETWORK_TYPE_RAW)
        buf.write_uint32be(TNS_NETWORK_MAGIC)
        buf.write_uint16be(TNS_NETWORK_TYPE_UB2)
        buf.write_uint32be(4)           # length of array
        buf.write_uint16be(TNS_NETWORK_SERVICE_SUPERVISOR)
        buf.write_uint16be(TNS_NETWORK_SERVICE_AUTH)
        buf.write_uint16be(TNS_NETWORK_SERVICE_ENCRYPTION)
        buf.write_uint16be(TNS_NETWORK_SERVICE_DATA_INTEGRITY)


@cython.final
cdef class NetworkServicesMessage(Message):
    cdef:
        bint external_auth_configured
        TlsWrapper tls_wrapper
        bint in_negotiation
        list services

    cdef int _initialize_hook(self) except -1:
        """
        A hook that is used by subclasses to perform any necessary
        initialization specific to that class.
        """
        self.services = [
            SupervisorService(),
            AuthenticationService(),
            EncryptionService(),
            DataIntegrityService()
        ]

    cdef int _write_message(self, WriteBuffer buf) except -1:
        """
        Write the message to the buffer.
        """
        cdef:
            uint16_t packet_length, service_data_length, num_services
            NetworkService service

        # calculate length of packet
        num_services = 0
        packet_length = 4 + 2 + 4 + 2 + 1
        for service in self.services:
            service_data_length = service.get_data_size(self.in_negotiation)
            if service_data_length != 0:
                num_services += 1
                packet_length += service_data_length

        # write header
        buf.write_uint32be(TNS_NETWORK_MAGIC)
        buf.write_uint16be(packet_length)
        buf.write_uint32be(TNS_NETWORK_VERSION)
        buf.write_uint16be(num_services)
        buf.write_uint8(0)                  # flags

        # write service data
        for service in self.services:
            service.write_data(buf, self.in_negotiation,
                               self.conn_impl._connection_id_bytes)

    cdef int enable_eztls(self) except -1:
        """
        Adds a TLS wrapper to the network services for enabling TLS over TCP.
        """
        cdef NetworkService service
        self.tls_wrapper = TlsWrapper()
        for service in self.services:
            service.tls_wrapper = self.tls_wrapper
            service.on_enable_eztls()

    cdef int complete_negotiation(self) except -1:
        """
        Completes any negotiation that is required.
        """
        cdef NetworkService service
        for service in self.services:
            service.on_complete_negotiation()
        self.in_negotiation = True

    cdef int process(self, ReadBuffer buf) except -1:
        """
        Process the response from the server.
        """
        cdef:
            NetworkService service
            uint32_t temp32
        buf.read_uint32be(&temp32)          # network magic num
        if temp32 != TNS_NETWORK_MAGIC:
            errors._raise_err(errors.ERR_UNEXPECTED_DATA, data=hex(temp32))
        buf.skip_raw_bytes(2)               # length of packet
        buf.skip_raw_bytes(4)               # version
        buf.skip_raw_bytes(2)               # number of services
        buf.skip_raw_bytes(1)               # error flags
        for service in self.services:
            service.read_response(buf, self)
