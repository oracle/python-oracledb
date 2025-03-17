#------------------------------------------------------------------------------
# Copyright (c) 2025, Oracle and/or its affiliates.
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
# aq_array.pyx
#
# Cython file defining the messages that are sent to the database and the
# responses that are received by the client for enqueuing and dequeuing
# an array of AQ messages (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

@cython.final
cdef class AqArrayMessage(AqBaseMessage):
    cdef:
        list props_impls
        int operation
        uint32_t num_iters

    cdef int _initialize_hook(self) except -1:
        """
        Perform initialization
        """
        self.function_code = TNS_FUNC_ARRAY_AQ

    cdef int _process_return_parameters(self, ReadBuffer buf) except -1:
        """
        Process the return parameters of the AQ array enqueue/dequeue request.
        """
        cdef:
            uint32_t i, j, num_iters, temp32
            ThinMsgPropsImpl props_impl
            uint16_t temp16
            bytes msgid
        buf.read_ub4(&num_iters)
        for i in range(num_iters):
            props_impl = self.props_impls[i]
            buf.read_ub2(&temp16)
            if temp16 > 0:
                buf.skip_ub1()
                self._process_msg_props(buf, props_impl)
            self._process_recipients(buf)
            buf.read_ub2(&temp16)
            if temp16 > 0:
                props_impl.payload = self._process_payload(buf)
            msgid = buf.read_bytes_with_length()
            if self.operation == TNS_AQ_ARRAY_ENQ:
                for j, props_impl in enumerate(self.props_impls):
                    props_impl.msgid = msgid[j * 16:(j + 1) * 16]
            else:
                props_impl.msgid = msgid
            buf.read_ub2(&temp16)               # extensions len
            if temp16 > 0:
                errors._raise_err(errors.ERR_NOT_IMPLEMENTED)
            buf.skip_ub2()                      # output ack
        if self.operation == TNS_AQ_ARRAY_ENQ:
            buf.read_ub4(&self.num_iters)
        else:
            self.num_iters = num_iters

    cdef int _write_array_deq(self, WriteBuffer buf) except -1:
        """
        Writes to the buffer the fields specific to the array dqeueue of AQ
        messages.
        """
        cdef:
            bytes consumer_name_bytes = None
            bytes correlation_bytes = None
            bytes condition_bytes = None
            ThinMsgPropsImpl props_impl
            bytes queue_name_bytes
            uint16_t delivery_mode
            uint32_t flags = 0

        # setup
        queue_name_bytes = self.queue_impl.name.encode()
        delivery_mode = self.deq_options_impl.delivery_mode
        if delivery_mode == TNS_AQ_MSG_BUFFERED:
            flags |= TNS_KPD_AQ_BUFMSG
        elif delivery_mode == TNS_AQ_MSG_PERSISTENT_OR_BUFFERED:
            flags |= TNS_KPD_AQ_EITHER
        if self.deq_options_impl.consumer_name:
            consumer_name_bytes = self.deq_options_impl.consumer_name.encode()
        if self.deq_options_impl.condition:
            condition_bytes = self.deq_options_impl.condition.encode()
        if self.deq_options_impl.correlation:
            correlation_bytes = self.deq_options_impl.correlation.encode()

        # write message
        for props_impl in self.props_impls:
            buf.write_ub4(len(queue_name_bytes))
            buf.write_bytes_with_length(queue_name_bytes)
            self._write_msg_props(buf, props_impl)
            buf.write_ub4(0)                        # num recipients
            self._write_value_with_length(buf, consumer_name_bytes)
            buf.write_sb4(self.deq_options_impl.mode)
            buf.write_sb4(self.deq_options_impl.navigation)
            buf.write_sb4(self.deq_options_impl.visibility)
            buf.write_sb4(self.deq_options_impl.wait)
            self._write_value_with_length(buf, self.deq_options_impl.msgid)
            self._write_value_with_length(buf, correlation_bytes)
            self._write_value_with_length(buf, condition_bytes)
            buf.write_ub4(0)                        # extensions
            buf.write_ub4(0)                        # rel msg id
            buf.write_sb4(0)                        # seq deviation
            buf.write_ub4(16)                       # toid length
            buf.write_bytes_with_length(self.queue_impl.payload_toid)
            buf.write_ub2(TNS_AQ_MESSAGE_VERSION)
            buf.write_ub4(0)                        # payload length
            buf.write_ub4(0)                        # raw pay length
            buf.write_ub4(0)
            buf.write_ub4(flags)
            buf.write_ub4(0)                        # extensions len
            buf.write_ub4(0)                        # source seq len

    cdef int _write_array_enq(self, WriteBuffer buf) except -1:
        """
        Writing input parameters incase of array enqueue
        """
        cdef:
            ThinMsgPropsImpl props_impl
            bytes queue_name_bytes
            uint32_t flags = 0

        # setup
        queue_name_bytes = self.queue_impl.name.encode()
        if self.enq_options_impl.delivery_mode == TNS_AQ_MSG_BUFFERED:
            flags |= TNS_KPD_AQ_BUFMSG

        # write message
        buf.write_ub4(0)                            # rel msgid len
        buf.write_uint8(TNS_MSG_TYPE_ROW_HEADER)
        buf.write_ub4(len(queue_name_bytes))
        buf.write_bytes_with_length(queue_name_bytes)
        buf.write_bytes(self.queue_impl.payload_toid)
        buf.write_ub2(TNS_AQ_MESSAGE_VERSION)
        buf.write_ub4(flags)
        for props_impl in self.props_impls:
            buf.write_uint8(TNS_MSG_TYPE_ROW_DATA)
            buf.write_ub4(flags)                    # aqi flags
            self._write_msg_props(buf, props_impl)
            buf.write_ub4(0)                        # num recipients
            buf.write_sb4(self.enq_options_impl.visibility)
            buf.write_ub4(0)                        # relative msg id
            buf.write_sb4(0)                        # seq deviation
            if self.queue_impl.payload_type is None \
                    and not self.queue_impl.is_json:
                buf.write_ub4(len(props_impl.payload_obj))
            self._write_payload(buf, props_impl)
        buf.write_uint8(TNS_MSG_TYPE_STATUS)

    cdef int _write_message(self, WriteBuffer buf) except -1:
        """
        Write message to the network buffers.
        """
        self._write_function_code(buf)
        if self.operation == TNS_AQ_ARRAY_ENQ:
            buf.write_uint8(0)                      # input params
            buf.write_ub4(0)                        # length
        else:
            buf.write_uint8(1)
            buf.write_ub4(self.num_iters)
        buf.write_ub4(TNS_AQ_ARRAY_FLAGS_RETURN_MESSAGE_ID)
        if self.operation == TNS_AQ_ARRAY_ENQ:
            buf.write_uint8(1)                      # output params
            buf.write_uint8(0)                      # length
        else:
            buf.write_uint8(1)
            buf.write_uint8(1)
        buf.write_sb4(self.operation)
        if self.operation == TNS_AQ_ARRAY_ENQ:
            buf.write_uint8(1)                      # num iters (pointer)
        else:
            buf.write_uint8(0)
        if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_21_1:
            buf.write_ub4(0xffff)                   # shard id
        if self.operation == TNS_AQ_ARRAY_ENQ:
            buf.write_ub4(self.num_iters)
        if self.operation == TNS_AQ_ARRAY_ENQ:
            self._write_array_enq(buf)
        else:
            self._write_array_deq(buf)
