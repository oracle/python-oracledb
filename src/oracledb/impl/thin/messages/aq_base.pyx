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
# aq_base.pyx
#
# Cython file defining the base class for messages that are sent to the
# database and the responses that are received by the client for enqueing and
# dequeuing AQ messages (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

cdef class AqBaseMessage(Message):
    cdef:
        BaseThinQueueImpl queue_impl
        ThinDeqOptionsImpl deq_options_impl
        ThinEnqOptionsImpl enq_options_impl
        bint no_msg_found

    cdef object _process_date(self, ReadBuffer buf):
        """
        Processes a date found in the buffer.
        """
        cdef:
            const char_type *ptr
            uint32_t num_bytes
            OracleData data
            ssize_t length
        buf.read_ub4(&num_bytes)
        if num_bytes > 0:
            buf.read_raw_bytes_and_length(&ptr, &length)
            decode_date(ptr, length, &data.buffer)
            return convert_date_to_python(&data.buffer)

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

    cdef int _process_extensions(self, ReadBuffer buf,
                                 ThinMsgPropsImpl props_impl) except -1:
        """
        Processes extensions to the message property object returned by the
        database.
        """
        cdef:
            bytes text_value, binary_value, value
            uint32_t i, num_extensions
            uint16_t keyword
        buf.read_ub4(&num_extensions)
        if num_extensions > 0:
            buf.skip_ub1()
            for i in range(num_extensions):
                text_value = buf.read_bytes_with_length()
                binary_value = buf.read_bytes_with_length()
                value = text_value or binary_value
                buf.read_ub2(&keyword)
                if value is not None:
                    if keyword == TNS_AQ_EXT_KEYWORD_AGENT_NAME:
                        props_impl.sender_agent_name = value
                    elif keyword == TNS_AQ_EXT_KEYWORD_AGENT_ADDRESS:
                        props_impl.sender_agent_address = value
                    elif keyword == TNS_AQ_EXT_KEYWORD_AGENT_PROTOCOL:
                        props_impl.sender_agent_protocol = value
                    elif keyword == TNS_AQ_EXT_KEYWORD_ORIGINAL_MSGID:
                        props_impl.original_msg_id = value

    cdef bytes _process_msg_id(self, ReadBuffer buf):
        """
        Reads a message id from the buffer and returns it.
        """
        cdef const char_type *ptr
        ptr = buf.read_raw_bytes(TNS_AQ_MESSAGE_ID_LENGTH)
        return ptr[:TNS_AQ_MESSAGE_ID_LENGTH]

    cdef int _process_msg_props(self, ReadBuffer buf,
                                ThinMsgPropsImpl props_impl) except -1:
        """
        Processes a message property object returned by the database.
        """
        cdef uint32_t temp32
        buf.read_sb4(&props_impl.priority)
        buf.read_sb4(&props_impl.delay)
        buf.read_sb4(&props_impl.expiration)
        props_impl.correlation = buf.read_str_with_length()
        buf.read_sb4(&props_impl.num_attempts)
        props_impl.exceptionq = buf.read_str_with_length()
        buf.read_sb4(&props_impl.state)
        props_impl.enq_time = self._process_date(buf)
        props_impl.enq_txn_id = buf.read_bytes_with_length()
        self._process_extensions(buf, props_impl)
        buf.read_ub4(&temp32)                       # user properties
        if temp32 > 0:
            errors._raise_err(errors.ERR_NOT_IMPLEMENTED)
        buf.skip_ub4()                              # csn
        buf.skip_ub4()                              # dsn
        buf.skip_ub4()                              # flags
        if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_21_1:
            buf.skip_ub4()                          # shard number

    cdef object _process_payload(self, ReadBuffer buf):
        """
        Processes the payload for an enqueued message returned by the database.
        """
        cdef:
            ThinDbObjectImpl obj_impl
            uint32_t image_length
            bytes payload
        if self.queue_impl.payload_type is not None:
            obj_impl = buf.read_dbobject(self.queue_impl.payload_type)
            if obj_impl is None:
                obj_impl = self.queue_impl.payload_type.create_new_object()
            return PY_TYPE_DB_OBJECT._from_impl(obj_impl)
        else:
            buf.read_bytes_with_length()            # TOID
            buf.read_bytes_with_length()            # OID
            buf.read_bytes_with_length()            # snapshot
            buf.skip_ub2()                          # version no
            buf.read_ub4(&image_length)             # image length
            buf.skip_ub2()                          # flags
            if image_length > 0:
                payload = buf.read_bytes()[4:image_length]
                if self.queue_impl.is_json:
                    return self.conn_impl.decode_oson(payload)
                return payload
            elif not self.queue_impl.is_json:
                return b''

    cdef object _process_recipients(self, ReadBuffer buf):
        """
        Process recipients for a message. Currently this is unsupported.
        """
        cdef uint32_t temp32
        buf.read_ub4(&temp32)
        if temp32 > 0:
            errors._raise_err(errors.ERR_NOT_IMPLEMENTED)
        return []

    cdef int _write_msg_props(self, WriteBuffer buf,
                              ThinMsgPropsImpl props_impl) except -1:
        """
        Write a message property object to the buffer.
        """
        buf.write_ub4(props_impl.priority)
        buf.write_ub4(props_impl.delay)
        buf.write_sb4(props_impl.expiration)
        self._write_value_with_length(buf, props_impl.correlation)
        buf.write_ub4(0)                            # number of attempts
        self._write_value_with_length(buf, props_impl.exceptionq)
        buf.write_ub4(props_impl.state)
        buf.write_ub4(0)                            # enqueue time length
        self._write_value_with_length(buf, props_impl.enq_txn_id)
        buf.write_ub4(4)                            # number of extensions
        buf.write_uint8(0x0e)                       # unknown extra byte
        buf.write_extension_values(None, None, TNS_AQ_EXT_KEYWORD_AGENT_NAME)
        buf.write_extension_values(None, None,
                                   TNS_AQ_EXT_KEYWORD_AGENT_ADDRESS)
        buf.write_extension_values(None, b'\x00',
                                   TNS_AQ_EXT_KEYWORD_AGENT_PROTOCOL)
        buf.write_extension_values(None, None,
                                   TNS_AQ_EXT_KEYWORD_ORIGINAL_MSGID)
        buf.write_ub4(0)                            # user property
        buf.write_ub4(0)                            # cscn
        buf.write_ub4(0)                            # dscn
        buf.write_ub4(0)                            # flags
        if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_21_1:
            buf.write_ub4(0xffffffffl)              # shard id

    cdef int _write_payload(self, WriteBuffer buf,
                            ThinMsgPropsImpl props_impl) except -1:
        """
        Writes the payload of the message property object to the buffer.
        """
        if self.queue_impl.is_json:
            buf.write_oson(props_impl.payload_obj,
                           self.conn_impl._oson_max_fname_size, False)
        elif self.queue_impl.payload_type is not None:
            buf.write_dbobject(props_impl.payload_obj)
        else:
            buf.write_bytes(props_impl.payload_obj)

    cdef int _write_value_with_length(self, WriteBuffer buf,
                                      object value) except -1:
        """
        Write a string to the buffer, prefixed by a length.
        """
        cdef bytes value_bytes
        if value is None:
            buf.write_ub4(0)
        else:
            if isinstance(value, str):
                value_bytes = value.encode()
            else:
                value_bytes = value
            buf.write_ub4(len(value_bytes))
            buf.write_bytes_with_length(value_bytes)
