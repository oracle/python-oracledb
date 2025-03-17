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
# enq.pyx
#
# Cython file defining the messages that are sent to the database and the
# responses that are received by the client for enqueuing an AQ message
# (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

@cython.final
cdef class EnqMessage(Message):
    cdef:
        BaseThinQueueImpl queue_impl
        ThinEnqOptionsImpl enq_options_impl
        ThinMsgPropsImpl props_impl

    cdef int _initialize_hook(self) except -1:
        """
        perform initialization
        """
        self.function_code = TNS_FUNC_AQ_ENQ

    cdef int _process_return_parameters(self, ReadBuffer buf) except -1:
        """
        Process the return parameters for the AQ enqueue request.
        """
        cdef const char_type *ptr = buf._get_raw(TNS_AQ_MESSAGE_ID_LENGTH)
        self.props_impl.msgid = ptr[:TNS_AQ_MESSAGE_ID_LENGTH]
        buf.skip_ub2()                          # extensions length

    cdef int _write_message(self, WriteBuffer buf) except -1:
        """
        Write message to the network buffers.
        """
        cdef:
            bytes queue_name_bytes
            bytes correlation_bytes
            bytes exceptionq_bytes
            int enq_flags

        self._write_function_code(buf)
        queue_name_bytes = self.queue_impl.name.encode()
        buf.write_uint8(1)                      # queue name (pointer)
        buf.write_ub4(len(queue_name_bytes))    # queue name length
        buf.write_ub4(self.props_impl.priority)
        buf.write_ub4(self.props_impl.delay)
        buf.write_sb4(self.props_impl.expiration)
        if self.props_impl.correlation is None:
            buf.write_ub4(0)                    # correlation
        else:
            correlation_bytes = self.props_impl.correlation.encode()
            buf.write_ub4(len(correlation_bytes))
            buf.write_bytes_with_length(correlation_bytes)
        buf.write_ub4(0)                        # number of attempts
        if self.props_impl.exceptionq is None:
            buf.write_ub4(0)                    # exception queue
        else:
            exceptionq_bytes = self.props_impl.exceptionq.encode()
            buf.write_ub4(len(exceptionq_bytes))
            buf.write_bytes_with_length(exceptionq_bytes)
        buf.write_ub4(self.props_impl.state)    # message state
        buf.write_ub4(0)                        # enqueue time length
        if self.props_impl.enq_txn_id is None:
            buf.write_ub4(0)                    # enqueue txn id length
        else:
            buf.write_ub4(len(self.props_impl.enq_txn_id))
            buf.write_bytes_with_length(self.props_impl.enq_txn_id)
        buf.write_ub4(4)                        # number of extensions
        buf.write_uint8(0x0e)                   # unknown extra byte
        buf.write_extension_values(None, None, TNS_AQ_EXT_KEYWORD_AGENT_NAME)
        buf.write_extension_values(None, None, TNS_AQ_EXT_KEYWORD_AGENT_ADDRESS)
        buf.write_extension_values(None, b'\x00',
                                 TNS_AQ_EXT_KEYWORD_AGENT_PROTOCOL)
        buf.write_extension_values(None, None,
                                 TNS_AQ_EXT_KEYWORD_ORIGINAL_MSGID)
        buf.write_ub4(0)                        # user property
        buf.write_ub4(0)                        # cscn
        buf.write_ub4(0)                        # dscn
        buf.write_ub4(0)                        # flags
        if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_21_1:
            buf.write_ub4(0xffffffffl)          # shard id

        if self.props_impl.recipients is None:
            buf.write_uint8(0)                  # recipients (pointer)
            buf.write_ub4(0)                    # number of key/value pairs
        else:
            buf.write_uint8(1)
            buf.write_ub4(len(self.props_impl.recipients) * 3)
        buf.write_ub4(self.enq_options_impl.visibility)
        buf.write_uint8(0)                      # relative message id
        buf.write_ub4(0)                        # relative message length
        buf.write_ub4(0)                        # sequence deviation
        buf.write_uint8(1)                      # TOID of payload (pointer)
        buf.write_ub4(16)                       # TOID of payload length
        buf.write_ub2(self.props_impl.version)
        if self.queue_impl.is_json:
            buf.write_uint8(0)                  # payload (pointer)
            buf.write_uint8(0)                  # RAW payload (pointer)
            buf.write_ub4(0)                    # RAW payload length
        elif self.queue_impl.payload_type is not None:
            buf.write_uint8(1)                  # payload (pointer)
            buf.write_uint8(0)                  # RAW payload (pointer)
            buf.write_ub4(0)                    # RAW payload (length)
        else:
            buf.write_uint8(0)                  # payload (pointer)
            buf.write_uint8(1)                  # RAW payload (pointer)
            buf.write_ub4(len(self.props_impl.payloadObject))
        buf.write_uint8(1)                      # return message id (pointer)
        buf.write_ub4(TNS_AQ_MESSAGE_ID_LENGTH) # return message id length
        enq_flags = 0
        if self.enq_options_impl.delivery_mode == TNS_AQ_MSG_BUFFERED:
            enq_flags |= TNS_KPD_AQ_BUFMSG
        buf.write_ub4(enq_flags)                # enqueue flags
        buf.write_uint8(0)                      # extensions 1 (pointer)
        buf.write_ub4(0)                        # number of extensions 1
        buf.write_uint8(0)                      # extensions 2 (pointer)
        buf.write_ub4(0)                        # number of extensions 2
        buf.write_uint8(0)                      # source sequence number
        buf.write_ub4(0)                        # source sequence length
        buf.write_uint8(0)                      # max sequence number
        buf.write_ub4(0)                        # max sequence length
        buf.write_uint8(0)                      # output ack length
        buf.write_uint8(0)                      # correlation (pointer)
        buf.write_ub4(0)                        # correlation length
        buf.write_uint8(0)                      # sender name (pointer)
        buf.write_ub4(0)                        # sender name length
        buf.write_uint8(0)                      # sender address (pointer)
        buf.write_ub4(0)                        # sender address length
        buf.write_uint8(0)                      # sender charset id (pointer)
        buf.write_uint8(0)                      # sender ncharset id (pointer)
        if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_20_1:
            if self.queue_impl.is_json:
                buf.write_uint8(1)              # JSON payload (pointer)
            else:
                buf.write_uint8(0)              # JSON payload (pointer)

        buf.write_bytes_with_length(queue_name_bytes)
        buf.write_bytes(self.queue_impl.payload_toid)
        if not self.queue_impl.is_json:
            if self.queue_impl.payload_type is not None:
                buf.write_dbobject(self.props_impl.payloadObject)
            else:
                buf.write_bytes(self.props_impl.payloadObject)
        if self.queue_impl.is_json:
            buf.write_oson(self.props_impl.payloadObject,
                self.conn_impl._oson_max_fname_size, False)
