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
# aq_deq.pyx
#
# Cython file defining the messages that are sent to the database and the
# responses that are received by the client for dequeuing an AQ message
# (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

@cython.final
cdef class AqDeqMessage(AqBaseMessage):
    cdef:
        ThinMsgPropsImpl props_impl

    cdef int _initialize_hook(self) except -1:
        """
        Perform initialization
        """
        self.function_code = TNS_FUNC_AQ_DEQ

    cdef int _process_return_parameters(self, ReadBuffer buf) except -1:
        """
        Process the return parameters of the AQ Dequeue request.
        """
        cdef:
            uint32_t num_bytes
            uint16_t keyword
            uint32_t imageLength
            ThinDbObjectImpl obj_impl
            ThinDbObjectTypeImpl type_impl
        buf.read_ub4(&num_bytes)
        if num_bytes > 0:
            self._process_msg_props(buf, self.props_impl)
            self.props_impl.recipients = self._process_recipients(buf)
            self.props_impl.payload = self._process_payload(buf)
            self.props_impl.msgid = self._process_msg_id(buf)

    cdef int _write_message(self, WriteBuffer buf) except -1:
        """
        Write message to the network buffers.
        """
        cdef:
             bytes queue_name_bytes
             bytes consumer_name_bytes
             bytes correlation_bytes
             bytes condition_bytes
             uint16_t delivery_mode
             int deq_flags
        self._write_function_code(buf)
        queue_name_bytes = self.queue_impl.name.encode()
        buf.write_uint8(1)                      # queue name (pointer)
        buf.write_ub4(len(queue_name_bytes))    # queue name length
        buf.write_uint8(1)                      # message properties
        buf.write_uint8(1)                      # msg props length
        buf.write_uint8(1)                      # recipient list
        buf.write_uint8(1)                      # recipient list length
        if self.deq_options_impl.consumer_name:
            consumer_name_bytes = self.deq_options_impl.consumer_name.encode()
            buf.write_uint8(1)                  # consumer name
            buf.write_ub4(len(consumer_name_bytes))
        else:
            consumer_name_bytes = None
            buf.write_uint8(0)                  # consumer name
            buf.write_ub4(0)                    # consumer name length
        buf.write_sb4(self.deq_options_impl.mode) # dequeue mode
        buf.write_sb4(self.deq_options_impl.navigation) # navigation
        buf.write_sb4(self.deq_options_impl.visibility) # visibility
        buf.write_sb4(self.deq_options_impl.wait) # wait
        if self.deq_options_impl.msgid:
            buf.write_uint8(1)                  # select mesg id
            buf.write_ub4(TNS_AQ_MESSAGE_ID_LENGTH) # mesg id len
        else:
            buf.write_uint8(0)                  # select mesg id
            buf.write_ub4(0)                    # select mesg id length
        if self.deq_options_impl.correlation:
            correlation_bytes = self.deq_options_impl.correlation.encode()
            buf.write_uint8(1)                  # correlation id
            buf.write_ub4(len(correlation_bytes)) # correlation id len
        else:
            correlation_bytes = None
            buf.write_uint8(0)                  # correlation id
            buf.write_ub4(0)                    # correlation id len
        buf.write_uint8(1)                      # toid of payload
        buf.write_ub4(16)                       # toid length
        buf.write_ub2(TNS_AQ_MESSAGE_VERSION)
        buf.write_uint8(1)                      # payload
        buf.write_uint8(1)                      # return msg id
        buf.write_ub4(TNS_AQ_MESSAGE_ID_LENGTH)
        deq_flags = 0
        delivery_mode = self.deq_options_impl.delivery_mode
        if (delivery_mode == TNS_AQ_MSG_BUFFERED):
            deq_flags |= TNS_KPD_AQ_BUFMSG
        elif (delivery_mode == TNS_AQ_MSG_PERSISTENT_OR_BUFFERED):
            deq_flags |= TNS_KPD_AQ_EITHER
        buf.write_ub4(deq_flags)                # dequeue flags
        if self.deq_options_impl.condition:
            condition_bytes = self.deq_options_impl.condition.encode()
            buf.write_uint8(1)                  # condition (pointer)
            buf.write_ub4(len(condition_bytes)) # condition length
        else:
            condition_bytes = None
            buf.write_uint8(0)                  # condition
            buf.write_ub4(0)                    # condition length
        buf.write_uint8(0)                      # extensions
        buf.write_ub4(0)                        # number of extensions
        if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_20_1:
            buf.write_uint8(0)                  # JSON payload
        if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_21_1:
            buf.write_ub4(-1)                   # shard id

        buf.write_bytes_with_length(queue_name_bytes)
        if consumer_name_bytes is not None:
            buf.write_bytes_with_length(consumer_name_bytes)
        if self.deq_options_impl.msgid:
            buf.write_bytes(self.deq_options_impl.msgid)
        if correlation_bytes is not None:
            buf.write_bytes_with_length(correlation_bytes)
        buf.write_bytes(self.queue_impl.payload_toid)
        if condition_bytes is not None:
            buf.write_bytes_with_length(condition_bytes)
