#------------------------------------------------------------------------------
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
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
# connect.pyx
#
# Cython file defining the messages that are sent to the database and the
# responses that are received by the client for the initial connection request
# (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

@cython.final
cdef class ConnectMessage(Message):
    cdef:
        bytes connect_string_bytes
        uint16_t connect_string_len, redirect_data_len
        bint read_redirect_data_len
        Description description
        uint8_t packet_flags
        str redirect_data
        str host
        int port

    cdef int process(self, ReadBuffer buf) except -1:
        cdef:
            uint16_t protocol_version, protocol_options
            const char_type *redirect_data
            uint32_t flags2 = 0
            uint8_t flags1
            bytes db_uuid
        if buf._current_packet.packet_type == TNS_PACKET_TYPE_REDIRECT:
            if not self.read_redirect_data_len:
                buf.read_uint16be(&self.redirect_data_len)
                self.read_redirect_data_len = True
            buf.wait_for_packets_sync()
            redirect_data = buf.read_raw_bytes(self.redirect_data_len)
            if self.redirect_data_len > 0:
                self.redirect_data = \
                        redirect_data[:self.redirect_data_len].decode()
            self.read_redirect_data_len = False
        elif buf._current_packet.packet_type == TNS_PACKET_TYPE_ACCEPT:
            buf.read_uint16be(&protocol_version)
            # check if the protocol version supported by the database is high
            # enough; if not, reject the connection immediately
            if protocol_version < TNS_VERSION_MIN_ACCEPTED:
                errors._raise_err(errors.ERR_SERVER_VERSION_NOT_SUPPORTED)
            buf.read_uint16be(&protocol_options)
            buf.skip_raw_bytes(10)
            buf.read_ub1(&flags1)
            if flags1 & TNS_NSI_NA_REQUIRED:
                feature = "Native Network Encryption and Data Integrity"
                errors._raise_not_supported(feature)
            buf.skip_raw_bytes(9)
            buf.read_uint32be(&buf._caps.sdu)
            if protocol_version >= TNS_VERSION_MIN_OOB_CHECK:
                buf.skip_raw_bytes(5)
                buf.read_uint32be(&flags2)
            buf._caps._adjust_for_protocol(protocol_version, protocol_options,
                                           flags2)
            buf._transport._full_packet_size = True
        elif buf._current_packet.packet_type == TNS_PACKET_TYPE_REFUSE:
            response = self.error_info.message
            error_code = "unknown"
            error_code_int = 0
            if response is not None:
                pos = response.find("(ERR=")
                if pos > 0:
                    end_pos = response.find(")", pos)
                    if end_pos > 0:
                        error_code = response[pos + 5:end_pos]
                        error_code_int = int(error_code)
            if error_code_int == 0:
                errors._raise_err(errors.ERR_UNEXPECTED_REFUSE)
            if error_code_int == TNS_ERR_INVALID_SERVICE_NAME:
                errors._raise_err(errors.ERR_INVALID_SERVICE_NAME,
                                  service_name=self.description.service_name,
                                  host=self.host, port=self.port)
            elif error_code_int == TNS_ERR_INVALID_SID:
                errors._raise_err(errors.ERR_INVALID_SID,
                                  sid=self.description.sid,
                                  host=self.host, port=self.port)
            errors._raise_err(errors.ERR_LISTENER_REFUSED_CONNECTION,
                              error_code=error_code)

    cdef int send(self, WriteBuffer buf) except -1:
        cdef:
            uint16_t service_options = TNS_GSO_DONT_CARE
            uint32_t connect_flags_1 = 0, connect_flags_2 = 0
            uint8_t nsi_flags = \
                    TNS_NSI_SUPPORT_SECURITY_RENEG | TNS_NSI_DISABLE_NA
        if buf._caps.supports_oob:
            service_options |= TNS_GSO_CAN_RECV_ATTENTION
            connect_flags_2 |= TNS_CHECK_OOB
        buf.start_request(TNS_PACKET_TYPE_CONNECT, self.packet_flags)
        buf.write_uint16be(TNS_VERSION_DESIRED)
        buf.write_uint16be(TNS_VERSION_MINIMUM)
        buf.write_uint16be(service_options)
        buf.write_uint16be(self.description.sdu)
        buf.write_uint16be(self.description.sdu)
        buf.write_uint16be(TNS_PROTOCOL_CHARACTERISTICS)
        buf.write_uint16be(0)               # line turnaround
        buf.write_uint16be(1)               # value of 1
        buf.write_uint16be(self.connect_string_len)
        buf.write_uint16be(74)              # offset to connect data
        buf.write_uint32be(0)               # max receivable data
        buf.write_uint8(nsi_flags)
        buf.write_uint8(nsi_flags)
        buf.write_uint64be(0)               # obsolete
        buf.write_uint64be(0)               # obsolete
        buf.write_uint64be(0)               # obsolete
        buf.write_uint32be(self.description.sdu)      # SDU (large)
        buf.write_uint32be(self.description.sdu)      # TDU (large)
        buf.write_uint32be(connect_flags_1)
        buf.write_uint32be(connect_flags_2)
        if self.connect_string_len > TNS_MAX_CONNECT_DATA:
            buf.end_request()
            buf.start_request(TNS_PACKET_TYPE_DATA)
        buf.write_bytes(self.connect_string_bytes)
        buf.end_request()
