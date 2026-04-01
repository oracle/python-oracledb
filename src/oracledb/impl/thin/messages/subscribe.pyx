#------------------------------------------------------------------------------
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
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
# subscribe.pyx
#
# Cython file defining the messages that are sent to the database and the
# responses that are received by the client for subscribing to an AQ Queue
# (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

@cython.final
cdef class SubscrMessage(Message):
    cdef:
        ThinSubscrImpl subscr_impl
        uint64_t registration_id
        bytes subscriber_name
        bytes client_id
        uint8_t opcode

    cdef int _initialize_hook(self) except -1:
        """
        Perform initialization
        """
        self.function_code = TNS_FUNC_SUBSCRIBE

    cdef int _process_return_parameters(self, ReadBuffer buf) except -1:
        """
        Process the return parameters for the subscribe request.
        """
        cdef uint32_t num_values, i
        buf.read_ub4(&num_values)           # out parameters (kpnrl)
        for i in range(num_values):
            buf.skip_ub4()
        for i in range(num_values):
            buf.skip_ub4()                  # registration id (short)
        buf.read_ub4(&num_values)           # out parameters (kpngrl)
        for i in range(num_values):
            buf.read_ub8(&self.registration_id)
            if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_12_1:
                buf.read_bytes_with_length()    # subscriber name
        if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_12_1:
            buf.read_ub4(&num_values)       # num database instances
            for i in range(num_values):
                buf.read_bytes_with_length()
            buf.read_ub4(&num_values)       # num listener addresses
            for i in range(num_values):
                buf.read_bytes_with_length()
            self.client_id = buf.read_bytes_with_length()

    cdef int _write_message(self, WriteBuffer buf) except -1:
        """
        Write message to the network buffers.
        """
        cdef:
            uint8_t grouping_type
            bytes username_bytes
            uint32_t qos, flags

        # determine the QOS flags to send
        qos = TNS_SUBSCR_QOS_SECURE
        if self.subscr_impl.qos & SUBSCR_QOS_RELIABLE:
            qos |= TNS_SUBSCR_QOS_RELIABLE
        if self.subscr_impl.qos & SUBSCR_QOS_DEREG_NFY:
            qos |= TNS_SUBSCR_QOS_PURGE_ON_NTFN

        # determine the operations flags to send
        flags = self.subscr_impl.operations
        if self.subscr_impl.qos & SUBSCR_QOS_QUERY:
            flags |= TNS_SUBSCR_FLAGS_QUERY
        if self.subscr_impl.qos & SUBSCR_QOS_ROWIDS:
            flags |= TNS_SUBSCR_FLAGS_INCLUDE_ROWIDS

        # determine the grouping type to send; the default value cannot be sent
        # to the server unless the grouping class is also set
        if self.subscr_impl.grouping_class == 0:
            grouping_type = 0
        else:
            grouping_type = self.subscr_impl.grouping_type

        # write the message
        self._write_function_code(buf)
        buf.write_uint8(self.opcode)
        buf.write_ub4(TNS_SUBSCR_MODE_CLIENT_INITIATED)
        if self.conn_impl.username is not None:
            username_bytes = self.conn_impl.username.encode()
            buf.write_uint8(1)              # pointer (username)
            buf.write_ub4(<uint32_t> len(username_bytes))
        else:
            buf.write_uint8(0)              # pointer (username)
            buf.write_ub4(0)                # username length
        if self.client_id is not None:
            buf.write_uint8(1)              # pointer (location)
            buf.write_ub4(len(self.client_id))
        else:
            buf.write_uint8(0)              # pointer (location)
            buf.write_ub4(0)                # location array length
        buf.write_uint8(1)                  # pointer (registration)
        buf.write_ub4(1)                    # num registrations
        buf.write_ub2(1)                    # raw presentation
        buf.write_ub2(6)                    # version for client notification
        buf.write_uint8(0)                  # pointer (namespace out attrs)
        buf.write_uint8(1)                  # pointer (num elements in array)
        buf.write_uint8(0)                  # pointer (generic out attrs)
        buf.write_uint8(1)                  # pointer (num elements in array)
        if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_12_1:
            buf.write_uint8(1)              # pointer (kpninst)
            buf.write_uint8(1)              # pointer (kpninstl)
            buf.write_uint8(1)              # pointer (kpngcret)
            buf.write_uint8(1)              # pointer (kpngcretl)
            buf.write_uint8(1)              # pointer (client id)
            buf.write_ub4(TNS_SUBSCR_CLIENT_ID_LEN)
            buf.write_uint8(1)              # pointer (client id length)
        if username_bytes is not None:
            buf.write_bytes_with_length(username_bytes)
        if self.client_id is not None:
            buf.write_bytes_with_length(self.client_id)
        buf.write_ub4(self.subscr_impl.namespace)
        if self.subscr_impl.name is not None:
            buf.write_bytes_with_two_lengths(self.subscr_impl.name.encode())
        else:
            buf.write_ub4(0)
        buf.write_ub4(0)                    # context length
        buf.write_ub4(0)                    # payload type
        buf.write_ub4(qos)
        buf.write_ub4(0)                    # payload callback length (JMS)
        buf.write_ub4(self.subscr_impl.timeout)
        buf.write_ub4(0)                    # kpdnsd
        buf.write_ub4(flags)
        buf.write_ub4(0)                    # change lag between notifications
        buf.write_ub4(0)                    # change registration id
        buf.write_uint8(self.subscr_impl.grouping_class)
        buf.write_ub4(self.subscr_impl.grouping_value)
        buf.write_uint8(grouping_type)
        buf.write_ub4(0)                    # grouping class start time
        buf.write_sb4(0)                    # grouping repeat count
        buf.write_ub8(self.registration_id)
