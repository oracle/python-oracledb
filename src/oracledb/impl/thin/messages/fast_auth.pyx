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
# fast_auth.pyx
#
# Cython file defining the messages that are sent to the database and the
# responses that are received by the client for performing fast authentication
# to the database (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

@cython.final
cdef class FastAuthMessage(Message):
    cdef:
        DataTypesMessage data_types_message
        ProtocolMessage protocol_message
        AuthMessage auth_message

    cdef int _process_message(self, ReadBuffer buf,
                              uint8_t message_type) except -1:
        """
        Processes the messages returned from the server response.
        """
        if message_type == TNS_MSG_TYPE_PROTOCOL:
            ProtocolMessage._process_message(self.protocol_message, buf,
                                             message_type)
        elif message_type == TNS_MSG_TYPE_DATA_TYPES:
            DataTypesMessage._process_message(self.data_types_message, buf,
                                              message_type)
        else:
            AuthMessage._process_message(self.auth_message, buf, message_type)
            self.end_of_response = self.auth_message.end_of_response

    cdef int _write_message(self, WriteBuffer buf) except -1:
        """
        Writes the message to the buffer. This includes not just this message
        but also the protocol, data types and auth messages. This reduces the
        number of round-trips to the database and thereby increases
        performance.
        """
        buf.write_uint8(TNS_MSG_TYPE_FAST_AUTH)
        buf.write_uint8(1)                  # fast auth version
        buf.write_uint8(TNS_SERVER_CONVERTS_CHARS)  # flag 1
        buf.write_uint8(0)                  # flag 2
        ProtocolMessage._write_message(self.protocol_message, buf)
        buf.write_uint16be(0)               # server charset (unused)
        buf.write_uint8(0)                  # server charset flag (unused)
        buf.write_uint16be(0)               # server ncharset (unused)
        buf._caps.ttc_field_version = TNS_CCAP_FIELD_VERSION_19_1_EXT_1
        buf.write_uint8(buf._caps.ttc_field_version)
        DataTypesMessage._write_message(self.data_types_message, buf)
        AuthMessage._write_message(self.auth_message, buf)
        buf._caps.ttc_field_version = TNS_CCAP_FIELD_VERSION_MAX
