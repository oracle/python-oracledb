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
# deq.pyx
#
# Cython file defining the messages that are sent to the database and the
# responses that are received by the client for dequeuing an AQ message
# (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

@cython.final
cdef class DeqMessage(Message):
    cdef:
        BaseThinQueueImpl queue_impl
        ThinDeqOptionsImpl deq_options_impl
        ThinMsgPropsImpl props_impl
        bint no_msg_found

    cdef int _initialize_hook(self) except -1:
        """
        Perform initialization
        """
        self.function_code = TNS_FUNC_AQ_DEQ

    cdef int _process_error_info(self, ReadBuffer buf) except -1:
        """
        Process error information from the buffer. If the error that indicates
        that no messages were received is detected, the error is cleared and
        the flag set so that the dequeue can handle that case.
        """
        Message._process_error_info(self, buf)
        if self.error_info.num == TNS_ERR_NO_MESSAGES_FOUND:
            self.error_info.num = 0
            self.error_occurred = False
            self.no_msg_found = True

    cdef int _process_return_parameters(self, ReadBuffer buf) except -1:
        """
        Process the return parameters of the AQ Dequeue request.
        """
        cdef:
            uint32_t num_bytes, num_extensions, i
            ssize_t temp_num_bytes
            const char_type *ptr
            uint16_t temp16, keyword
            bytes temp
            OracleData data
            uint32_t imageLength
            ThinDbObjectImpl obj_impl
            ThinDbObjectTypeImpl type_impl
        buf.read_ub4(&num_bytes)
        if num_bytes > 0:
            buf.read_sb4(&self.props_impl.priority)      # priority
            buf.read_sb4(&self.props_impl.delay)         # delay
            buf.read_sb4(&self.props_impl.expiration)    # expiration
            # correlation id
            buf.read_ub4(&num_bytes)
            if num_bytes > 0:
                buf.read_raw_bytes_and_length(&ptr, &temp_num_bytes)
                self.props_impl.correlation = ptr[:temp_num_bytes].decode()
            buf.read_sb4(&self.props_impl.num_attempts)
            # exception queue name
            buf.read_ub4(&num_bytes)
            if num_bytes > 0:
                buf.read_raw_bytes_and_length(&ptr, &temp_num_bytes)
                self.props_impl.exceptionq = ptr[:temp_num_bytes].decode()
            buf.read_sb4(&self.props_impl.state)
            buf.read_ub4(&num_bytes)                    # enqueue time
            if num_bytes > 0:
                buf.read_raw_bytes_and_length(&ptr, &temp_num_bytes)
                decode_date(ptr, temp_num_bytes, &data.buffer)
                self.props_impl.enq_time = convert_date_to_python(&data.buffer)
            buf.read_ub4(&num_bytes)                    # transaction id
            if num_bytes > 0:
                ptr = buf._get_raw(num_bytes)
                self.props_impl.enq_txn_id = ptr[:num_bytes]
            else:
                self.props_impl.enq_txn_id = None
            buf.read_ub4(&num_extensions)               # number of extensions
            if num_extensions > 0:
                buf.skip_ub1()
                for i in range(num_extensions):
                    temp = None
                    temp16 = 0
                    buf.read_ub4(&num_bytes)            # text value length
                    if num_bytes > 0:
                        buf.read_raw_bytes_and_length(&ptr, &temp_num_bytes)
                        temp = ptr[:temp_num_bytes]
                        temp16 = temp_num_bytes
                    buf.read_ub4(&num_bytes)            # binary value length
                    if num_bytes > 0:
                        buf.read_raw_bytes_and_length(&ptr, &temp_num_bytes)
                        temp = ptr[:temp_num_bytes]
                    buf.read_ub2(&keyword)              # extension keyword
                    if (keyword == TNS_AQ_EXT_KEYWORD_AGENT_NAME and
                            temp is not None and temp16 > 0):
                        self.props_impl.sender_agent_name = temp
                    if (keyword == TNS_AQ_EXT_KEYWORD_AGENT_ADDRESS and
                            temp is not None and temp16 > 0):
                        self.props_impl.sender_agent_address = temp
                    if (keyword == TNS_AQ_EXT_KEYWORD_AGENT_PROTOCOL and
                            temp is not None):
                        self.props_impl.sender_agent_protocol = temp
                    if (keyword == TNS_AQ_EXT_KEYWORD_ORIGINAL_MSGID and
                            temp is not None):
                        self.props_impl.original_msg_id = temp
            buf.read_ub4(&num_bytes)                    # user properties
            if num_bytes > 0:
                errors._raise_err(errors.ERR_NOT_IMPLEMENTED)
            buf.skip_ub4()                              # csn
            buf.skip_ub4()                              # dsn
            buf.skip_ub4()                              # flags
            if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_21_1:
                buf.skip_ub4()                          # shard number
            buf.read_ub4(&num_bytes)                    # num recipients
            if num_bytes > 0:
                errors._raise_err(errors.ERR_NOT_IMPLEMENTED)
            if self.queue_impl.payload_type is not None:
                type_impl = self.queue_impl.payload_type
                obj_impl = buf.read_dbobject(type_impl)
                if obj_impl is None:
                    obj_impl = type_impl.create_new_object()
                self.props_impl.payload = PY_TYPE_DB_OBJECT._from_impl(obj_impl)
            else:
                buf.read_ub4(&num_bytes)                    # TOID len
                if num_bytes > 0:
                    buf.skip_raw_bytes(num_bytes)
                buf.read_ub4(&num_bytes)                    # OID len
                if num_bytes > 0:
                    buf.skip_raw_bytes(num_bytes)
                buf.read_ub4(&num_bytes)                    # snapshot
                if num_bytes > 0:
                    buf.skip_raw_bytes(num_bytes)
                buf.skip_ub2()                              # version no
                buf.read_ub4(&imageLength)                  # image len
                buf.skip_ub2()                              # flags
                if imageLength > 0:
                    self.props_impl.payload = buf.read_bytes()[4:imageLength]
                    if self.queue_impl.is_json:
                        self.props_impl.payload = \
                            self.conn_impl.decode_oson(self.props_impl.payload)
                else:
                    if not self.queue_impl.is_json:
                        self.props_impl.payload = b''
            ptr = buf._get_raw(TNS_AQ_MESSAGE_ID_LENGTH)
            self.props_impl.msgid = ptr[:TNS_AQ_MESSAGE_ID_LENGTH]

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
        buf.write_ub2(self.props_impl.version)  # version of type
        buf.write_uint8(1)                      # payload
        buf.write_uint8(1)                      # return msg id
        buf.write_ub4(16)                       # mesg id length
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
