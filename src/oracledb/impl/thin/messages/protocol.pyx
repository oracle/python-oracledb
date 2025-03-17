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
# protocol.pyx
#
# Cython file defining the messages that are sent to the database and the
# responses that are received by the client for establishing the protoocl to
# use during the connection (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

@cython.final
cdef class ProtocolMessage(Message):
    cdef:
        uint8_t server_version
        uint8_t server_flags
        bytes server_compile_caps
        bytes server_runtime_caps
        bytes server_banner

    cdef int _write_message(self, WriteBuffer buf) except -1:
        buf.write_uint8(TNS_MSG_TYPE_PROTOCOL)
        buf.write_uint8(6)                  # protocol version (8.1 and higher)
        buf.write_uint8(0)                  # "array" terminator
        buf.write_str(DRIVER_NAME)
        buf.write_uint8(0)                  # NULL terminator

    cdef int _process_message(self, ReadBuffer buf,
                              uint8_t message_type) except -1:
        if message_type == TNS_MSG_TYPE_PROTOCOL:
            self._process_protocol_info(buf)
            if not buf._caps.supports_end_of_response:
                self.end_of_response = True
        else:
            Message._process_message(self, buf, message_type)

    cdef int _process_protocol_info(self, ReadBuffer buf) except -1:
        """
        Processes the response to the protocol request.
        """
        cdef:
            uint16_t num_elem, fdo_length
            Capabilities caps = buf._caps
            const char_type *fdo
            bytearray temp_array
            ssize_t ix
        buf.read_ub1(&self.server_version)
        buf.skip_ub1()                      # skip zero byte
        self.server_banner = buf.read_null_terminated_bytes()
        buf.read_uint16le(&caps.charset_id)
        buf.read_ub1(&self.server_flags)
        buf.read_uint16le(&num_elem)
        if num_elem > 0:                    # skip elements
            buf.skip_raw_bytes(num_elem * 5)
        buf.read_uint16be(&fdo_length)
        fdo = buf.read_raw_bytes(fdo_length)
        ix = 6 + fdo[5] + fdo[6]
        caps.ncharset_id = (fdo[ix + 3] << 8) + fdo[ix + 4]
        self.server_compile_caps = buf.read_bytes()
        if self.server_compile_caps is not None:
            temp_array = bytearray(self.server_compile_caps)
            caps._adjust_for_server_compile_caps(temp_array)
            if caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_23_1:
                self.conn_impl._oson_max_fname_size = 65535
        self.server_runtime_caps = buf.read_bytes()
        if self.server_runtime_caps is not None:
            temp_array = bytearray(self.server_runtime_caps)
            caps._adjust_for_server_runtime_caps(temp_array)
