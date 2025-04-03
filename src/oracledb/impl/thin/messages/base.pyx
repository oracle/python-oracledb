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
# base.pyx
#
# Cython file defining the base classes used for messages sent to the database
# and the responses that are received by the client (embedded in
# thin_impl.pyx).
#------------------------------------------------------------------------------

@cython.freelist(20)
cdef class _OracleErrorInfo:
    cdef:
        uint32_t num
        uint16_t cursor_id
        uint64_t pos
        uint64_t rowcount
        str message
        Rowid rowid
        list batcherrors


cdef class Message:
    cdef:
        BaseThinConnImpl conn_impl
        BaseThinDbObjectTypeCache type_cache
        PipelineOpResultImpl pipeline_result_impl
        _OracleErrorInfo error_info
        uint8_t message_type
        uint8_t function_code
        uint32_t call_status
        uint16_t end_to_end_seq_num
        uint64_t token_num
        bint end_of_response
        bint error_occurred
        bint flush_out_binds
        bint resend
        bint retry
        object warning

    cdef int _check_and_raise_exception(self) except -1:
        """
        Checks to see if an error has occurred. If one has, an error object is
        created and then the appropriate exception raised. Note that if a "dead
        connection" error is detected, the connection is forced closed
        immediately.
        """
        if self.error_occurred:
            error = errors._Error(self.error_info.message,
                                  code=self.error_info.num,
                                  offset=self.error_info.pos)
            if error.is_session_dead:
                self.conn_impl._protocol._force_close()
            raise error.exc_type(error)

    cdef int _initialize(self, BaseThinConnImpl conn_impl) except -1:
        """
        Initializes the message to contain the connection and a place to store
        error information. For DRCP, the status of the connection may change
        after the first round-trip to the database so this information needs to
        be preserved. Child classes may have their own initialization. In order
        to avoid overhead using the constructor, a special hook method is used
        instead.
        """
        conn_impl._protocol._read_buf._check_connected()
        self.conn_impl = conn_impl
        self.message_type = TNS_MSG_TYPE_FUNCTION
        self.error_info = _OracleErrorInfo.__new__(_OracleErrorInfo)
        self._initialize_hook()

    cdef int _initialize_hook(self) except -1:
        """
        A hook that is used by subclasses to perform any necessary
        initialization specific to that class.
        """
        pass

    cdef int _process_error_info(self, ReadBuffer buf) except -1:
        cdef:
            uint32_t num_bytes, i, offset, num_offsets
            _OracleErrorInfo info = self.error_info
            uint16_t temp16, num_errors, error_code
            uint8_t first_byte, flags
            int16_t error_pos
            str error_msg
        buf.read_ub4(&self.call_status)     # end of call status
        buf.skip_ub2()                      # end to end seq#
        buf.skip_ub4()                      # current row number
        buf.skip_ub2()                      # error number
        buf.skip_ub2()                      # array elem error
        buf.skip_ub2()                      # array elem error
        buf.read_ub2(&info.cursor_id)       # cursor id
        buf.read_sb2(&error_pos)            # error position
        buf.skip_ub1()                      # sql type (19c and earlier)
        buf.skip_ub1()                      # fatal?
        buf.skip_ub1()                      # flags
        buf.skip_ub1()                      # user cursor options
        buf.skip_ub1()                      # UPI parameter
        buf.read_ub1(&flags)
        if flags & 0x20:
            self.warning = errors._create_warning(errors.WRN_COMPILATION_ERROR)
        buf.read_rowid(&info.rowid)         # rowid
        buf.skip_ub4()                      # OS error
        buf.skip_ub1()                      # statement number
        buf.skip_ub1()                      # call number
        buf.skip_ub2()                      # padding
        buf.skip_ub4()                      # success iters
        buf.read_ub4(&num_bytes)            # oerrdd (logical rowid)
        if num_bytes > 0:
            buf.skip_raw_bytes_chunked()

        # batch error codes
        buf.read_ub2(&num_errors)           # batch error codes array
        if num_errors > 0:
            info.batcherrors = []
            buf.read_ub1(&first_byte)
            for i in range(num_errors):
                if first_byte == TNS_LONG_LENGTH_INDICATOR:
                    buf.skip_ub4()          # chunk length ignored
                buf.read_ub2(&error_code)
                info.batcherrors.append(errors._Error(code=error_code))
            if first_byte == TNS_LONG_LENGTH_INDICATOR:
                buf.skip_raw_bytes(1)       # ignore end marker

        # batch error offsets
        buf.read_ub4(&num_offsets)          # batch error row offset array
        if num_offsets > 0:
            if num_offsets > 65535:
                errors._raise_err(errors.ERR_TOO_MANY_BATCH_ERRORS)
            buf.read_ub1(&first_byte)
            for i in range(num_offsets):
                if first_byte == TNS_LONG_LENGTH_INDICATOR:
                    buf.skip_ub4()          # chunk length ignored
                buf.read_ub4(&offset)
                if i < num_errors:
                    info.batcherrors[i].offset = offset
            if first_byte == TNS_LONG_LENGTH_INDICATOR:
                buf.skip_raw_bytes(1)       # ignore end marker

        # batch error messages
        buf.read_ub2(&temp16)               # batch error messages array
        if temp16 > 0:
            buf.skip_raw_bytes(1)           # ignore packed size
            for i in range(temp16):
                buf.skip_ub2()              # skip chunk length
                info.batcherrors[i].message = \
                        buf.read_str(CS_FORM_IMPLICIT).rstrip()
                info.batcherrors[i]._make_adjustments()
                buf.skip_raw_bytes(2)       # ignore end marker

        buf.read_ub4(&info.num)             # error number (extended)
        buf.read_ub8(&info.rowcount)        # row number (extended)

        # fields added in Oracle Database 20c
        if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_20_1:
            buf.skip_ub4()                  # sql type
            buf.skip_ub4()                  # server checksum

        # error message
        if info.num != 0:
            self.error_occurred = True
            if error_pos > 0:
                info.pos = error_pos
            info.message = buf.read_str(CS_FORM_IMPLICIT).rstrip()

        # an error message marks the end of a response if no explicit end of
        # response is available
        if not buf._caps.supports_end_of_response:
            self.end_of_response = True

    cdef int _process_message(self, ReadBuffer buf,
                              uint8_t message_type) except -1:
        cdef uint64_t token_num
        if message_type == TNS_MSG_TYPE_ERROR:
            self._process_error_info(buf)
        elif message_type == TNS_MSG_TYPE_WARNING:
            self._process_warning_info(buf)
        elif message_type == TNS_MSG_TYPE_TOKEN:
            buf.read_ub8(&token_num)
            if token_num != self.token_num:
                errors._raise_err(errors.ERR_MISMATCHED_TOKEN,
                                  token_num=token_num,
                                  expected_token_num=self.token_num)
        elif message_type == TNS_MSG_TYPE_STATUS:
            buf.read_ub4(&self.call_status)
            buf.read_ub2(&self.end_to_end_seq_num)
            if not buf._caps.supports_end_of_response:
                self.end_of_response = True
        elif message_type == TNS_MSG_TYPE_PARAMETER:
            self._process_return_parameters(buf)
        elif message_type == TNS_MSG_TYPE_SERVER_SIDE_PIGGYBACK:
            self._process_server_side_piggyback(buf)
        elif message_type == TNS_MSG_TYPE_END_OF_RESPONSE:
            self.end_of_response = True
        else:
            errors._raise_err(errors.ERR_MESSAGE_TYPE_UNKNOWN,
                              message_type=message_type,
                              position=buf._pos - 1)

    cdef OracleMetadata _process_metadata(self, ReadBuffer buf):
        """
        Process metadata from the buffer and return it.
        """
        cdef:
            uint32_t uds_flags, num_annotations, i
            ThinDbObjectTypeImpl typ_impl
            str schema, name, key, value
            uint8_t ora_type_num, csfrm
            OracleMetadata metadata
            uint8_t nulls_allowed
            int cache_num
            bytes oid
        buf.read_ub1(&ora_type_num)
        metadata = OracleMetadata.__new__(OracleMetadata)
        buf.skip_ub1()                      # flags
        buf.read_sb1(&metadata.precision)
        buf.read_sb1(&metadata.scale)
        buf.read_ub4(&metadata.buffer_size)
        buf.skip_ub4()                      # max number of array elements
        buf.skip_ub8()                      # cont flags
        oid = buf.read_bytes_with_length()
        buf.skip_ub2()                      # version
        buf.skip_ub2()                      # character set id
        buf.read_ub1(&csfrm)                # character set form
        metadata.dbtype = DbType._from_ora_type_and_csfrm(ora_type_num, csfrm)
        buf.read_ub4(&metadata.max_size)
        if ora_type_num == ORA_TYPE_NUM_RAW:
            metadata.max_size = metadata.buffer_size
        if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_12_2:
            buf.skip_ub4()                  # oaccolid
        buf.read_ub1(&nulls_allowed)
        metadata.nulls_allowed = nulls_allowed
        buf.skip_ub1()                      # v7 length of name
        metadata.name = buf.read_str_with_length()
        schema = buf.read_str_with_length()
        name = buf.read_str_with_length()
        buf.skip_ub2()                      # column position
        buf.read_ub4(&uds_flags)
        metadata.is_json = uds_flags & TNS_UDS_FLAGS_IS_JSON
        metadata.is_oson = uds_flags & TNS_UDS_FLAGS_IS_OSON
        if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_23_1:
            metadata.domain_schema = buf.read_str_with_length()
            metadata.domain_name = buf.read_str_with_length()
        if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_23_1_EXT_3:
            buf.read_ub4(&num_annotations)
            if num_annotations > 0:
                buf.skip_ub1()
                metadata.annotations = {}
                buf.read_ub4(&num_annotations)
                buf.skip_ub1()
                for i in range(num_annotations):
                    key = buf.read_str_with_length()
                    value = buf.read_str_with_length()
                    if value is None:
                        value = ""
                    metadata.annotations[key] = value
                    buf.skip_ub4()          # flags
                buf.skip_ub4()              # flags
        if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_23_4:
            buf.read_ub4(&metadata.vector_dimensions)
            buf.read_ub1(&metadata.vector_format)
            buf.read_ub1(&metadata.vector_flags)
        if ora_type_num == ORA_TYPE_NUM_OBJECT:
            if self.type_cache is None:
                cache_num = self.conn_impl._dbobject_type_cache_num
                self.type_cache = get_dbobject_type_cache(cache_num)
            typ_impl = self.type_cache.get_type_for_info(oid, schema, None,
                                                         name)
            if typ_impl.is_xml_type:
                metadata.dbtype = DB_TYPE_XMLTYPE
            else:
                metadata.objtype = typ_impl
        return metadata

    cdef int _process_return_parameters(self, ReadBuffer buf) except -1:
        raise NotImplementedError()

    cdef int _process_server_side_piggyback(self, ReadBuffer buf) except -1:
        cdef:
            uint16_t num_elements, i, temp16
            uint32_t num_bytes, flags
            uint8_t opcode
        buf.read_ub1(&opcode)
        if opcode == TNS_SERVER_PIGGYBACK_LTXID:
            self.conn_impl._ltxid = buf.read_bytes_with_length()
        elif opcode == TNS_SERVER_PIGGYBACK_QUERY_CACHE_INVALIDATION \
                or opcode == TNS_SERVER_PIGGYBACK_TRACE_EVENT:
            pass
        elif opcode == TNS_SERVER_PIGGYBACK_OS_PID_MTS:
            buf.read_ub2(&temp16)
            buf.skip_raw_bytes_chunked()
        elif opcode == TNS_SERVER_PIGGYBACK_SYNC:
            buf.skip_ub2()                  # skip number of DTYs
            buf.skip_ub1()                  # skip length of DTYs
            buf.read_ub2(&num_elements)
            buf.skip_ub1()                  # skip length
            for i in range(num_elements):
                buf.read_ub2(&temp16)
                if temp16 > 0:              # skip key
                    buf.skip_raw_bytes_chunked()
                buf.read_ub2(&temp16)
                if temp16 > 0:              # skip value
                    buf.skip_raw_bytes_chunked()
                buf.skip_ub2()              # skip flags
            buf.skip_ub4()                  # skip overall flags
        elif opcode == TNS_SERVER_PIGGYBACK_EXT_SYNC:
            buf.skip_ub2()                  # skip number of DTYs
            buf.skip_ub1()                  # skip length of DTYs
        elif opcode == TNS_SERVER_PIGGYBACK_AC_REPLAY_CONTEXT:
            buf.skip_ub2()                  # skip number of DTYs
            buf.skip_ub1()                  # skip length of DTYs
            buf.skip_ub4()                  # skip flags
            buf.skip_ub4()                  # skip error code
            buf.skip_ub1()                  # skip queue
            buf.read_ub4(&num_bytes)        # skip replay context
            if num_bytes > 0:
                buf.skip_raw_bytes_chunked()
        elif opcode == TNS_SERVER_PIGGYBACK_SESS_RET:
            buf.skip_ub2()
            buf.skip_ub1()
            buf.read_ub2(&num_elements)
            if num_elements > 0:
                buf.skip_ub1()
                for i in range(num_elements):
                    buf.read_ub2(&temp16)
                    if temp16 > 0:          # skip key
                        buf.skip_raw_bytes_chunked()
                    buf.read_ub2(&temp16)
                    if temp16 > 0:          # skip value
                        buf.skip_raw_bytes_chunked()
                    buf.skip_ub2()          # skip flags
            buf.read_ub4(&flags)            # session flags
            if flags & TNS_SESSGET_SESSION_CHANGED:
                if self.conn_impl._drcp_establish_session:
                    self.conn_impl._statement_cache.clear_open_cursors()
            self.conn_impl._drcp_establish_session = False
            buf.read_ub4(&self.conn_impl._session_id)
            buf.read_ub2(&self.conn_impl._serial_num)
        elif opcode == TNS_SERVER_PIGGYBACK_SESS_SIGNATURE:
            buf.skip_ub2()                  # number of dtys
            buf.skip_ub1()                  # length of dty
            buf.skip_ub8()                  # signature flags
            buf.skip_ub8()                  # client signature
            buf.skip_ub8()                  # server signature
        else:
            errors._raise_err(errors.ERR_UNKNOWN_SERVER_PIGGYBACK,
                              opcode=opcode)

    cdef int _process_warning_info(self, ReadBuffer buf) except -1:
        cdef:
            uint16_t num_bytes, error_num
            str message
        buf.read_ub2(&error_num)            # error number
        buf.read_ub2(&num_bytes)            # length of error message
        buf.skip_ub2()                      # flags
        if error_num != 0 and num_bytes > 0:
            message = buf.read_str(CS_FORM_IMPLICIT).rstrip()
            self.warning = errors._Error(message, code=error_num,
                                         iswarning=True)

    cdef int _write_begin_pipeline_piggyback(self, WriteBuffer buf) except -1:
        """
        Writes the piggyback to the server that informs the server that a
        pipeline is beginning.
        """
        buf._data_flags |= TNS_DATA_FLAGS_BEGIN_PIPELINE
        self._write_piggyback_code(buf, TNS_FUNC_PIPELINE_BEGIN)
        buf.write_ub2(0)                    # error set ID
        buf.write_uint8(0)                  # error set mode
        buf.write_uint8(self.conn_impl.pipeline_mode)

    cdef int _write_close_cursors_piggyback(self, WriteBuffer buf) except -1:
        """
        Writes the piggyback that informs the server of the cursors that can be
        closed.
        """
        self._write_piggyback_code(buf, TNS_FUNC_CLOSE_CURSORS)
        buf.write_uint8(1)                  # pointer
        self.conn_impl._statement_cache.write_cursors_to_close(buf)

    cdef int _write_current_schema_piggyback(self, WriteBuffer buf) except -1:
        """
        Writes the piggyback that informs the server that a new current schema
        is desired.
        """
        cdef bytes schema_bytes
        self._write_piggyback_code(buf, TNS_FUNC_SET_SCHEMA)
        buf.write_uint8(1)                  # pointer
        schema_bytes = self.conn_impl._current_schema.encode()
        buf.write_ub4(len(schema_bytes))
        buf.write_bytes_with_length(schema_bytes)

    cdef int _write_close_temp_lobs_piggyback(self,
                                              WriteBuffer buf) except -1:
        """
        Writes the piggyback that informs the server of the temporary LOBs that
        can be closed.
        """
        cdef:
            list lobs_to_close = self.conn_impl._temp_lobs_to_close
            uint64_t total_size = 0
        self._write_piggyback_code(buf, TNS_FUNC_LOB_OP)
        op_code = TNS_LOB_OP_FREE_TEMP | TNS_LOB_OP_ARRAY

        # temp lob data
        buf.write_uint8(1)                  # pointer
        buf.write_ub4(self.conn_impl._temp_lobs_total_size)
        buf.write_uint8(0)                  # dest lob locator
        buf.write_ub4(0)
        buf.write_ub4(0)                    # source lob locator
        buf.write_ub4(0)
        buf.write_uint8(0)                  # source lob offset
        buf.write_uint8(0)                  # dest lob offset
        buf.write_uint8(0)                  # charset
        buf.write_ub4(op_code)
        buf.write_uint8(0)                  # scn
        buf.write_ub4(0)                    # losbscn
        buf.write_ub8(0)                    # lobscnl
        buf.write_ub8(0)
        buf.write_uint8(0)

        # array lob fields
        buf.write_uint8(0)
        buf.write_ub4(0)
        buf.write_uint8(0)
        buf.write_ub4(0)
        buf.write_uint8(0)
        buf.write_ub4(0)
        for i in range(len(lobs_to_close)):
            buf.write_bytes(lobs_to_close[i])

        # reset values
        self.conn_impl._temp_lobs_to_close = None
        self.conn_impl._temp_lobs_total_size = 0

    cdef int _write_end_to_end_piggyback(self, WriteBuffer buf) except -1:
        """
        Writes the piggyback that informs the server of end-to-end attributes
        that are being changed.
        """
        cdef:
            bytes action_bytes, client_identifier_bytes, client_info_bytes
            BaseThinConnImpl conn_impl = self.conn_impl
            bytes module_bytes, dbop_bytes
            uint32_t flags = 0

        # determine which flags to send
        if conn_impl._action_modified:
            flags |= TNS_END_TO_END_ACTION
        if conn_impl._client_identifier_modified:
            flags |= TNS_END_TO_END_CLIENT_IDENTIFIER
        if conn_impl._client_info_modified:
            flags |= TNS_END_TO_END_CLIENT_INFO
        if conn_impl._module_modified:
            flags |= TNS_END_TO_END_MODULE
        if conn_impl._dbop_modified:
            flags |= TNS_END_TO_END_DBOP

        # write initial packet data
        self._write_piggyback_code(buf, TNS_FUNC_SET_END_TO_END_ATTR)
        buf.write_uint8(0)                  # pointer (cidnam)
        buf.write_uint8(0)                  # pointer (cidser)
        buf.write_ub4(flags)

        # write client identifier header info
        if conn_impl._client_identifier_modified:
            buf.write_uint8(1)              # pointer (client identifier)
            if conn_impl._client_identifier is None:
                buf.write_ub4(0)
            else:
                client_identifier_bytes = conn_impl._client_identifier.encode()
                buf.write_ub4(len(client_identifier_bytes))
        else:
            buf.write_uint8(0)              # pointer (client identifier)
            buf.write_ub4(0)                # length of client identifier

        # write module header info
        if conn_impl._module_modified:
            buf.write_uint8(1)              # pointer (module)
            if conn_impl._module is None:
                buf.write_ub4(0)
            else:
                module_bytes = conn_impl._module.encode()
                buf.write_ub4(len(module_bytes))
        else:
            buf.write_uint8(0)              # pointer (module)
            buf.write_ub4(0)                # length of module

        # write action header info
        if conn_impl._action_modified:
            buf.write_uint8(1)              # pointer (action)
            if conn_impl._action is None:
                buf.write_ub4(0)
            else:
                action_bytes = conn_impl._action.encode()
                buf.write_ub4(len(action_bytes))
        else:
            buf.write_uint8(0)              # pointer (action)
            buf.write_ub4(0)                # length of action

        # write unsupported bits
        buf.write_uint8(0)                  # pointer (cideci)
        buf.write_ub4(0)                    # length (cideci)
        buf.write_uint8(0)                  # cidcct
        buf.write_ub4(0)                    # cidecs

        # write client info header info
        if conn_impl._client_info_modified:
            buf.write_uint8(1)              # pointer (client info)
            if conn_impl._client_info is None:
                buf.write_ub4(0)
            else:
                client_info_bytes = conn_impl._client_info.encode()
                buf.write_ub4(len(client_info_bytes))
        else:
            buf.write_uint8(0)              # pointer (client info)
            buf.write_ub4(0)                # length of client info

        # write more unsupported bits
        buf.write_uint8(0)                  # pointer (cidkstk)
        buf.write_ub4(0)                    # length (cidkstk)
        buf.write_uint8(0)                  # pointer (cidktgt)
        buf.write_ub4(0)                    # length (cidktgt)

        # write dbop header info
        if conn_impl._dbop_modified:
            buf.write_uint8(1)              # pointer (dbop)
            if conn_impl._dbop is None:
                buf.write_ub4(0)
            else:
                dbop_bytes = conn_impl._dbop.encode()
                buf.write_ub4(len(dbop_bytes))
        else:
            buf.write_uint8(0)              # pointer (dbop)
            buf.write_ub4(0)                # length of dbop

        # write strings
        if conn_impl._client_identifier_modified \
                and conn_impl._client_identifier is not None:
            buf.write_bytes_with_length(client_identifier_bytes)
        if conn_impl._module_modified and conn_impl._module is not None:
            buf.write_bytes_with_length(module_bytes)
        if conn_impl._action_modified and conn_impl._action is not None:
            buf.write_bytes_with_length(action_bytes)
        if conn_impl._client_info_modified \
                and conn_impl._client_info is not None:
            buf.write_bytes_with_length(client_info_bytes)
        if conn_impl._dbop_modified and conn_impl._dbop is not None:
            buf.write_bytes_with_length(dbop_bytes)

        # reset flags and values
        conn_impl._action_modified = False
        conn_impl._action = None
        conn_impl._client_identifier_modified = False
        conn_impl._client_identifier = None
        conn_impl._client_info_modified = False
        conn_impl._client_info = None
        conn_impl._dbop_modified = False
        conn_impl._dbop = None
        conn_impl._module_modified = False
        conn_impl._module = None

    cdef int _write_function_code(self, WriteBuffer buf) except -1:
        self._write_piggybacks(buf)
        buf.write_uint8(self.message_type)
        buf.write_uint8(self.function_code)
        buf.write_seq_num()
        if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_23_1_EXT_1:
            buf.write_ub8(self.token_num)

    cdef int _write_message(self, WriteBuffer buf) except -1:
        self._write_function_code(buf)

    cdef int _write_piggyback_code(self, WriteBuffer buf,
                                   uint8_t code) except -1:
        """
        Writes the header for piggybacks for the specified function code.
        """
        buf.write_uint8(TNS_MSG_TYPE_PIGGYBACK)
        buf.write_uint8(code)
        buf.write_seq_num()
        if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_23_1_EXT_1:
            buf.write_ub8(self.token_num)

    cdef int _write_piggybacks(self, WriteBuffer buf) except -1:
        """
        Writes all of the piggybacks to the server.
        """
        if self.conn_impl.pipeline_mode != 0:
            self._write_begin_pipeline_piggyback(buf)
            self.conn_impl.pipeline_mode = 0
        if self.conn_impl._current_schema_modified:
            self._write_current_schema_piggyback(buf)
        if self.conn_impl._statement_cache is not None \
                and self.conn_impl._statement_cache._num_cursors_to_close > 0 \
                and not self.conn_impl._drcp_establish_session:
            self._write_close_cursors_piggyback(buf)
        if self.conn_impl._action_modified \
                or self.conn_impl._client_identifier_modified \
                or self.conn_impl._client_info_modified \
                or self.conn_impl._dbop_modified \
                or self.conn_impl._module_modified:
            self._write_end_to_end_piggyback(buf)
        if self.conn_impl._temp_lobs_total_size > 0:
            self._write_close_temp_lobs_piggyback(buf)
        if self.conn_impl._session_state_desired != 0:
            self._write_session_state_piggyback(buf)

    cdef int _write_session_state_piggyback(self, WriteBuffer buf) except -1:
        """
        Write the session state piggyback. This is used to let the database
        know when the client is beginning and ending a request. The database
        uses this information to optimise its resources.
        """
        cdef uint8_t state = self.conn_impl._session_state_desired
        self._write_piggyback_code(buf, TNS_FUNC_SESSION_STATE)
        buf.write_ub8(state | TNS_SESSION_STATE_EXPLICIT_BOUNDARY)
        self.conn_impl._session_state_desired = 0

    cdef int postprocess(self) except -1:
        pass

    async def postprocess_async(self):
        pass

    cdef int preprocess(self) except -1:
        pass

    cdef int process(self, ReadBuffer buf) except -1:
        cdef uint8_t message_type
        self.end_of_response = False
        self.flush_out_binds = False
        while not self.end_of_response:
            buf.save_point()
            buf.read_ub1(&message_type)
            self._process_message(buf, message_type)

    cdef int send(self, WriteBuffer buf) except -1:
        buf.start_request(TNS_PACKET_TYPE_DATA)
        self._write_message(buf)
        if self.pipeline_result_impl is not None:
            buf._data_flags |= TNS_DATA_FLAGS_END_OF_REQUEST
        buf.end_request()


cdef class MessageWithData(Message):
    cdef:
        BaseThinCursorImpl cursor_impl
        array.array bit_vector_buf
        const char_type *bit_vector
        bint arraydmlrowcounts
        uint32_t row_index
        uint32_t num_execs
        uint16_t num_columns_sent
        list dmlrowcounts
        bint batcherrors
        list out_var_impls
        bint in_fetch
        bint parse_only
        object cursor
        uint32_t offset

    cdef int _adjust_metadata(self, ThinVarImpl prev_var_impl,
                              OracleMetadata metadata) except -1:
        """
        When a query is re-executed but the data type of a column has changed
        the server returns the type information of the new type. However, if
        the data type returned now is a CLOB or BLOB and the data type
        previously returned was CHAR/VARCHAR/RAW (or the equivalent long
        types), then the server returns the data as LONG (RAW), similarly to
        what happens when a define is done to return CLOB/BLOB as string/bytes.
        Detect these situations and adjust the fetch type appropriately.
        """
        cdef uint8_t type_num, prev_type_num, csfrm
        type_num = metadata.dbtype._ora_type_num
        prev_type_num = prev_var_impl._fetch_metadata.dbtype._ora_type_num
        if type_num == ORA_TYPE_NUM_CLOB \
                and prev_type_num in (ORA_TYPE_NUM_CHAR,
                                      ORA_TYPE_NUM_LONG,
                                      ORA_TYPE_NUM_VARCHAR):
            type_num = ORA_TYPE_NUM_LONG
            csfrm = prev_var_impl._fetch_metadata.dbtype._csfrm
            metadata.dbtype = DbType._from_ora_type_and_csfrm(type_num, csfrm)
        elif type_num == ORA_TYPE_NUM_BLOB \
                and prev_type_num in (ORA_TYPE_NUM_RAW, ORA_TYPE_NUM_LONG_RAW):
            type_num = ORA_TYPE_NUM_LONG_RAW
            metadata.dbtype = DbType._from_ora_type_and_csfrm(type_num, 0)

    cdef object _create_cursor_from_describe(self, ReadBuffer buf,
                                             object cursor=None):
        cdef BaseThinCursorImpl cursor_impl
        if cursor is None:
            cursor = self.cursor.connection.cursor()
        cursor_impl = cursor._impl
        cursor_impl._statement = self.conn_impl._get_statement()
        cursor_impl._more_rows_to_fetch = True
        cursor_impl._statement._is_query = True
        self._process_describe_info(buf, cursor, cursor_impl)
        return cursor

    cdef int _get_bit_vector(self, ReadBuffer buf,
                             ssize_t num_bytes) except -1:
        """
        Gets the bit vector from the buffer and stores it for later use by the
        row processing code. Since it is possible that the packet buffer may be
        overwritten by subsequent packet retrieval, the bit vector must be
        copied. An array is stored and a pointer to the underlying memory is
        used for performance reasons.
        """
        cdef const char_type *ptr = buf.read_raw_bytes(num_bytes)
        if self.bit_vector_buf is None:
            self.bit_vector_buf = array.array('B')
            array.resize(self.bit_vector_buf, num_bytes)
        self.bit_vector = <const char_type*> self.bit_vector_buf.data.as_chars
        memcpy(<void*> self.bit_vector, ptr, num_bytes)

    cdef bint _is_duplicate_data(self, uint32_t column_num):
        """
        Returns a boolean indicating if the given column contains data
        duplicated from the previous row. When duplicate data exists, the
        server sends a bit vector. Bits that are set indicate that data is sent
        with the row data; bits that are not set indicate that data should be
        duplicated from the previous row.
        """
        cdef int byte_num, bit_num
        if self.bit_vector == NULL:
            return False
        byte_num = column_num // 8
        bit_num = column_num % 8
        return self.bit_vector[byte_num] & (1 << bit_num) == 0

    cdef int _write_bind_params(self, WriteBuffer buf, list params) except -1:
        cdef:
            bint has_data = False
            list bind_var_impls
            BindInfo bind_info
        bind_var_impls = []
        for bind_info in params:
            if not bind_info._is_return_bind:
                has_data = True
            bind_var_impls.append(bind_info._bind_var_impl)
        self._write_column_metadata(buf, bind_var_impls)

        # write parameter values unless statement contains only returning binds
        if has_data:
            for i in range(self.num_execs):
                buf.write_uint8(TNS_MSG_TYPE_ROW_DATA)
                self._write_bind_params_row(buf, params, i)

    cdef int _preprocess_query(self) except -1:
        """
        Actions that takes place before query data is processed.
        """
        cdef:
            BaseThinCursorImpl cursor_impl = self.cursor_impl
            Statement statement = cursor_impl._statement
            object type_handler, conn
            ThinVarImpl var_impl
            ssize_t i, num_vals
            bint uses_metadata

        # set values to indicate the start of a new fetch operation
        self.in_fetch = True
        cursor_impl._more_rows_to_fetch = True
        cursor_impl._buffer_rowcount = cursor_impl._buffer_index = 0
        self.row_index = 0

        # if no fetch variables exist, nothing further to do at this point; the
        # processing that follows will take the metadata returned by the server
        # and use it to create new fetch variables
        if statement._fetch_var_impls is None:
            return 0

        # if the type handler set on the cursor or connection does not match
        # the one that was used during the last fetch, rebuild the fetch
        # variables in order to take the new type handler into account
        conn = self.cursor.connection
        type_handler = cursor_impl._get_output_type_handler(&uses_metadata)
        if type_handler is not statement._last_output_type_handler:
            for i, var_impl in enumerate(cursor_impl.fetch_var_impls):
                cursor_impl._create_fetch_var(conn, self.cursor, type_handler,
                                              uses_metadata, i,
                                              var_impl._fetch_metadata)
            statement._last_output_type_handler = type_handler

        # Create OracleArrowArray if fetching arrow is enabled
        if cursor_impl.fetching_arrow:
            cursor_impl._create_arrow_arrays()

        # the list of output variables is equivalent to the fetch variables
        self.out_var_impls = cursor_impl.fetch_var_impls

    cdef int _process_bit_vector(self, ReadBuffer buf) except -1:
        cdef ssize_t num_bytes
        buf.read_ub2(&self.num_columns_sent)
        num_bytes = self.cursor_impl._num_columns // 8
        if self.cursor_impl._num_columns % 8 > 0:
            num_bytes += 1
        self._get_bit_vector(buf, num_bytes)

    cdef object _process_column_data(self, ReadBuffer buf,
                                     ThinVarImpl var_impl, uint32_t pos):
        cdef:
            uint8_t num_bytes, ora_type_num, csfrm
            ThinDbObjectTypeImpl typ_impl
            BaseThinCursorImpl cursor_impl
            object column_value = None
            ThinDbObjectImpl obj_impl
            int32_t actual_num_bytes
            OracleMetadata metadata
            OracleData data
            Rowid rowid
        if self.in_fetch:
            metadata = var_impl._fetch_metadata
        else:
            metadata = var_impl.metadata
        ora_type_num = metadata.dbtype._ora_type_num
        csfrm =  metadata.dbtype._csfrm
        if var_impl.bypass_decode:
            ora_type_num = ORA_TYPE_NUM_RAW
        if metadata.buffer_size == 0 and self.in_fetch \
                and ora_type_num not in (ORA_TYPE_NUM_LONG,
                                         ORA_TYPE_NUM_LONG_RAW,
                                         ORA_TYPE_NUM_UROWID):
            column_value = None             # column is null by describe
        elif ora_type_num == ORA_TYPE_NUM_ROWID:
            if not self.in_fetch:
                column_value = buf.read_str(CS_FORM_IMPLICIT)
            else:
                buf.read_ub1(&num_bytes)
                if num_bytes == 0 or num_bytes == TNS_NULL_LENGTH_INDICATOR:
                    column_value = None
                else:
                    buf.read_rowid(&rowid)
                    column_value = _encode_rowid(&rowid)
        elif ora_type_num == ORA_TYPE_NUM_UROWID:
            if not self.in_fetch:
                column_value = buf.read_str(CS_FORM_IMPLICIT)
            else:
                column_value = buf.read_urowid()
        elif ora_type_num == ORA_TYPE_NUM_CURSOR:
            buf.skip_ub1()                  # length (fixed value)
            if not self.in_fetch:
                column_value = var_impl._values[pos]
            column_value = self._create_cursor_from_describe(buf, column_value)
            cursor_impl = column_value._impl
            buf.read_ub2(&cursor_impl._statement._cursor_id)
            if self.in_fetch:
                cursor_impl._statement._is_nested = True
        elif ora_type_num in (ORA_TYPE_NUM_CLOB,
                              ORA_TYPE_NUM_BLOB,
                              ORA_TYPE_NUM_BFILE):
            if self.cursor_impl._statement._is_plsql:
                column_value = var_impl._values[pos]
            column_value = buf.read_lob_with_length(self.conn_impl,
                                                    metadata.dbtype,
                                                    column_value)
        elif ora_type_num == ORA_TYPE_NUM_JSON:
            column_value = buf.read_oson()
        elif ora_type_num == ORA_TYPE_NUM_VECTOR:
            column_value = buf.read_vector()
        elif ora_type_num == ORA_TYPE_NUM_OBJECT:
            typ_impl = metadata.objtype
            if typ_impl is None:
                column_value = buf.read_xmltype(self.conn_impl)
            else:
                obj_impl = buf.read_dbobject(typ_impl)
                if obj_impl is not None:
                    if self.cursor_impl._statement._is_plsql:
                        column_value = var_impl._values[pos]
                    if column_value is not None:
                        column_value._impl = obj_impl
                    else:
                        column_value = PY_TYPE_DB_OBJECT._from_impl(obj_impl)
        else:
            buf.read_oracle_data(metadata, &data, from_dbobject=False)
            if metadata.dbtype._csfrm == CS_FORM_NCHAR:
                buf._caps._check_ncharset_id()
            if self.cursor_impl.fetching_arrow:
                convert_oracle_data_to_arrow(
                    metadata, var_impl.metadata, &data, var_impl._arrow_array
                )
            else:
                column_value = convert_oracle_data_to_python(
                    metadata, var_impl.metadata, &data,
                    var_impl._encoding_errors, from_dbobject=False
                )
        if not self.in_fetch:
            buf.read_sb4(&actual_num_bytes)
            if actual_num_bytes < 0 and ora_type_num == ORA_TYPE_NUM_BOOLEAN:
                column_value = None
            elif actual_num_bytes != 0 and column_value is not None:
                unit_type = "bytes" if isinstance(column_value, bytes) \
                            else "characters"
                errors._raise_err(errors.ERR_COLUMN_TRUNCATED,
                                  col_value_len=len(column_value),
                                  unit=unit_type, actual_len=actual_num_bytes)
        elif ora_type_num == ORA_TYPE_NUM_LONG \
                or ora_type_num == ORA_TYPE_NUM_LONG_RAW:
            buf.skip_sb4()                  # null indicator
            buf.skip_ub4()                  # return code
        return column_value

    cdef int _process_describe_info(self, ReadBuffer buf,
                                    object cursor,
                                    BaseThinCursorImpl cursor_impl) except -1:
        cdef:
            Statement stmt = cursor_impl._statement
            list prev_fetch_var_impls
            object type_handler, conn
            OracleMetadata metadata
            uint32_t num_bytes, i
            bint uses_metadata
            str message
        buf.skip_ub4()                      # max row size
        buf.read_ub4(&cursor_impl._num_columns)
        prev_fetch_var_impls = stmt._fetch_var_impls
        cursor_impl._init_fetch_vars(cursor_impl._num_columns)
        if cursor_impl._num_columns > 0:
            buf.skip_ub1()
        type_handler = cursor_impl._get_output_type_handler(&uses_metadata)
        conn = self.cursor.connection
        for i in range(cursor_impl._num_columns):
            metadata = self._process_metadata(buf)
            if prev_fetch_var_impls is not None \
                    and i < len(prev_fetch_var_impls):
                self._adjust_metadata(prev_fetch_var_impls[i], metadata)
            if metadata.dbtype._ora_type_num in (ORA_TYPE_NUM_BLOB,
                                                 ORA_TYPE_NUM_CLOB,
                                                 ORA_TYPE_NUM_JSON,
                                                 ORA_TYPE_NUM_VECTOR):
                stmt._requires_define = True
                stmt._no_prefetch = True
            cursor_impl._create_fetch_var(conn, self.cursor, type_handler,
                                          uses_metadata, i, metadata)
        buf.read_ub4(&num_bytes)
        if num_bytes > 0:
            buf.skip_raw_bytes_chunked()    # current date
        buf.skip_ub4()                      # dcbflag
        buf.skip_ub4()                      # dcbmdbz
        buf.skip_ub4()                      # dcbmnpr
        buf.skip_ub4()                      # dcbmxpr
        buf.read_ub4(&num_bytes)
        if num_bytes > 0:
            buf.skip_raw_bytes_chunked()    # dcbqcky
        stmt._fetch_metadata = cursor_impl.fetch_metadata
        stmt._fetch_vars = cursor_impl.fetch_vars
        stmt._fetch_var_impls = cursor_impl.fetch_var_impls
        stmt._num_columns = cursor_impl._num_columns
        stmt._last_output_type_handler = type_handler

    cdef int _process_error_info(self, ReadBuffer buf) except -1:
        cdef:
            BaseThinCursorImpl cursor_impl = self.cursor_impl
            BaseThinConnImpl conn_impl = self.conn_impl
            object exc_type
        Message._process_error_info(self, buf)
        if self.error_info.cursor_id != 0:
            cursor_impl._statement._cursor_id = self.error_info.cursor_id
        if not cursor_impl._statement._is_plsql and not self.in_fetch:
            cursor_impl.rowcount = self.error_info.rowcount
        elif self.in_fetch and self.row_index > 0:
            cursor_impl._statement._requires_define = False
        cursor_impl._lastrowid = self.error_info.rowid
        cursor_impl._batcherrors = self.error_info.batcherrors
        if self.batcherrors and cursor_impl._batcherrors is None:
            cursor_impl._batcherrors = []
        if self.error_info.num == TNS_ERR_NO_DATA_FOUND and self.in_fetch:
            self.error_info.num = 0
            cursor_impl._more_rows_to_fetch = False
            cursor_impl._last_row_index = 0
            cursor_impl._statement._requires_define = False
            self.error_occurred = False
        elif self.error_info.num == TNS_ERR_ARRAY_DML_ERRORS:
            self.error_info.num = 0
            self.error_occurred = False
        elif self.retry:
            self.retry = False
        elif cursor_impl._statement._is_query \
                and self.error_info.num in (TNS_ERR_VAR_NOT_IN_SELECT_LIST,
                                            TNS_ERR_INCONSISTENT_DATA_TYPES):
            self.retry = True
            conn_impl._statement_cache.clear_cursor(cursor_impl._statement)
        elif self.error_info.num != 0 and self.error_info.cursor_id != 0:
            if self.error_info.num not in errors.ERR_INTEGRITY_ERROR_CODES:
                conn_impl._statement_cache.clear_cursor(cursor_impl._statement)

    cdef int _process_implicit_result(self, ReadBuffer buf) except -1:
        cdef:
            BaseThinCursorImpl child_cursor_impl
            uint32_t i, num_results
            object child_cursor
            uint8_t num_bytes
        self.cursor_impl._implicit_resultsets = []
        buf.read_ub4(&num_results)
        for i in range(num_results):
            buf.read_ub1(&num_bytes)
            buf.skip_raw_bytes(num_bytes)
            child_cursor = self._create_cursor_from_describe(buf)
            child_cursor_impl = child_cursor._impl
            buf.read_ub2(&child_cursor_impl._statement._cursor_id)
            self.cursor_impl._implicit_resultsets.append(child_cursor)

    cdef int _process_io_vector(self, ReadBuffer buf) except -1:
        """
        An I/O vector is sent by the database in response to a PL/SQL execute.
        It indicates whether binds are IN only, IN/OUT or OUT only.
        """
        cdef:
            uint16_t i, num_bytes, temp16
            uint32_t temp32, num_binds
            BindInfo bind_info
        buf.skip_ub1()                      # flag
        buf.read_ub2(&temp16)               # num requests
        buf.read_ub4(&temp32)               # num iters
        num_binds = temp32 * 256 + temp16
        buf.skip_ub4()                      # num iters this time
        buf.skip_ub2()                      # uac buffer length
        buf.read_ub2(&num_bytes)            # bit vector for fast fetch
        if num_bytes > 0:
            buf.skip_raw_bytes(num_bytes)
        buf.read_ub2(&num_bytes)            # rowid
        if num_bytes > 0:
            buf.skip_raw_bytes(num_bytes)
        self.out_var_impls = []
        for i in range(num_binds):          # bind directions
            bind_info = self.cursor_impl._statement._bind_info_list[i]
            buf.read_ub1(&bind_info.bind_dir)
            if bind_info.bind_dir == TNS_BIND_DIR_INPUT:
                continue
            self.out_var_impls.append(bind_info._bind_var_impl)

    cdef int _process_message(self, ReadBuffer buf,
                              uint8_t message_type) except -1:
        if message_type == TNS_MSG_TYPE_ROW_HEADER:
            self._process_row_header(buf)
        elif message_type == TNS_MSG_TYPE_ROW_DATA:
            self._process_row_data(buf)
        elif message_type == TNS_MSG_TYPE_FLUSH_OUT_BINDS:
            self.flush_out_binds = True
            self.end_of_response = True
        elif message_type == TNS_MSG_TYPE_DESCRIBE_INFO:
            buf.skip_raw_bytes_chunked()
            self._process_describe_info(buf, self.cursor, self.cursor_impl)
            self.out_var_impls = self.cursor_impl.fetch_var_impls
        elif message_type == TNS_MSG_TYPE_ERROR:
            self._process_error_info(buf)
        elif message_type == TNS_MSG_TYPE_BIT_VECTOR:
            self._process_bit_vector(buf)
        elif message_type == TNS_MSG_TYPE_IO_VECTOR:
            self._process_io_vector(buf)
        elif message_type == TNS_MSG_TYPE_IMPLICIT_RESULTSET:
            self._process_implicit_result(buf)
        else:
            Message._process_message(self, buf, message_type)

    cdef int _process_return_parameters(self, ReadBuffer buf) except -1:
        cdef:
            uint16_t keyword_num, num_params, num_bytes
            uint32_t num_rows, i
            uint64_t rowcount
            bytes key_value
            list rowcounts
        buf.read_ub2(&num_params)           # al8o4l (ignored)
        for i in range(num_params):
            buf.skip_ub4()
        buf.read_ub2(&num_bytes)            # al8txl (ignored)
        if num_bytes > 0:
            buf.skip_raw_bytes(num_bytes)
        buf.read_ub2(&num_params)           # num key/value pairs
        for i in range(num_params):
            buf.read_ub2(&num_bytes)        # key
            if num_bytes > 0:
                key_value = buf.read_bytes()
            buf.read_ub2(&num_bytes)        # value
            if num_bytes > 0:
                buf.skip_raw_bytes_chunked()
            buf.read_ub2(&keyword_num)      # keyword num
            if keyword_num == TNS_KEYWORD_NUM_CURRENT_SCHEMA:
                self.conn_impl._current_schema = key_value.decode()
            elif keyword_num == TNS_KEYWORD_NUM_EDITION:
                self.conn_impl._edition = key_value.decode()
        buf.read_ub2(&num_bytes)            # registration
        if num_bytes > 0:
            buf.skip_raw_bytes(num_bytes)
        if self.arraydmlrowcounts:
            buf.read_ub4(&num_rows)
            rowcounts = self.cursor_impl._dmlrowcounts = []
            for i in range(num_rows):
                buf.read_ub8(&rowcount)
                rowcounts.append(rowcount)

    cdef int _process_row_data(self, ReadBuffer buf) except -1:
        cdef:
            uint32_t num_rows, pos
            ThinVarImpl var_impl
            ssize_t i, j
            object value
            list values
        for i, var_impl in enumerate(self.out_var_impls):
            if var_impl.is_array:
                buf.read_ub4(&var_impl.num_elements_in_array)
                for pos in range(var_impl.num_elements_in_array):
                    value = self._process_column_data(buf, var_impl, pos)
                    var_impl._values[pos] = value
            elif self.cursor_impl._statement._is_returning:
                buf.read_ub4(&num_rows)
                values = [None] * num_rows
                for j in range(num_rows):
                    values[j] = self._process_column_data(buf, var_impl, j)
                var_impl._values[self.row_index] = values
                var_impl._has_returned_data = True
            elif self.cursor_impl.fetching_arrow:
                if self._is_duplicate_data(i):
                    var_impl._arrow_array.append_last_value(
                        var_impl._last_arrow_array
                    )
                else:
                    self._process_column_data(buf, var_impl, self.row_index)
                var_impl._last_arrow_array = None
            elif self._is_duplicate_data(i):
                if self.row_index == 0 and var_impl.outconverter is not None:
                    value = var_impl._last_raw_value
                else:
                    value = var_impl._values[self.cursor_impl._last_row_index]
                var_impl._values[self.row_index] = value
            else:
                value = self._process_column_data(buf, var_impl,
                                                  self.row_index)
                var_impl._values[self.row_index] = value
        self.row_index += 1
        if self.in_fetch:
            self.cursor_impl._last_row_index = self.row_index - 1
            self.cursor_impl._buffer_rowcount = self.row_index
            self.bit_vector = NULL

    cdef int _process_row_header(self, ReadBuffer buf) except -1:
        cdef uint32_t num_bytes
        buf.skip_ub1()                      # flags
        buf.skip_ub2()                      # num requests
        buf.skip_ub4()                      # iteration number
        buf.skip_ub4()                      # num iters
        buf.skip_ub2()                      # buffer length
        buf.read_ub4(&num_bytes)
        if num_bytes > 0:
            buf.skip_ub1()                  # skip repeated length
            self._get_bit_vector(buf, num_bytes)
        buf.read_ub4(&num_bytes)
        if num_bytes > 0:
            buf.skip_raw_bytes_chunked()    # rxhrid

    cdef int _write_column_metadata(self, WriteBuffer buf,
                                    list bind_var_impls) except -1:
        cdef:
            uint32_t buffer_size, cont_flag, lob_prefetch_length
            ThinDbObjectTypeImpl typ_impl
            uint8_t ora_type_num, flag
            OracleMetadata metadata
            ThinVarImpl var_impl
        for var_impl in bind_var_impls:
            metadata = var_impl.metadata
            ora_type_num = metadata.dbtype._ora_type_num
            buffer_size = metadata.buffer_size
            if ora_type_num in (ORA_TYPE_NUM_ROWID, ORA_TYPE_NUM_UROWID):
                ora_type_num = ORA_TYPE_NUM_VARCHAR
                buffer_size = TNS_MAX_UROWID_LENGTH
            flag = TNS_BIND_USE_INDICATORS
            if var_impl.is_array:
                flag |= TNS_BIND_ARRAY
            cont_flag = 0
            lob_prefetch_length = 0
            if ora_type_num in (ORA_TYPE_NUM_BLOB,
                                ORA_TYPE_NUM_CLOB):
                cont_flag = TNS_LOB_PREFETCH_FLAG
            elif ora_type_num == ORA_TYPE_NUM_JSON:
                cont_flag = TNS_LOB_PREFETCH_FLAG
                buffer_size = lob_prefetch_length = TNS_JSON_MAX_LENGTH
            elif ora_type_num == ORA_TYPE_NUM_VECTOR:
                cont_flag = TNS_LOB_PREFETCH_FLAG
                buffer_size = lob_prefetch_length = TNS_VECTOR_MAX_LENGTH
            buf.write_uint8(ora_type_num)
            buf.write_uint8(flag)
            # precision and scale are always written as zero as the server
            # expects that and complains if any other value is sent!
            buf.write_uint8(0)
            buf.write_uint8(0)
            buf.write_ub4(buffer_size)
            if var_impl.is_array:
                buf.write_ub4(var_impl.num_elements)
            else:
                buf.write_ub4(0)            # max num elements
            buf.write_ub8(cont_flag)
            if metadata.objtype is not None:
                typ_impl = metadata.objtype
                buf.write_ub4(len(typ_impl.oid))
                buf.write_bytes_with_length(typ_impl.oid)
                buf.write_ub4(typ_impl.version)
            else:
                buf.write_ub4(0)            # OID
                buf.write_ub2(0)            # version
            if metadata.dbtype._csfrm != 0:
                buf.write_ub2(TNS_CHARSET_UTF8)
            else:
                buf.write_ub2(0)
            buf.write_uint8(metadata.dbtype._csfrm)
            buf.write_ub4(lob_prefetch_length)  # max chars (LOB prefetch)
            if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_12_2:
                buf.write_ub4(0)            # oaccolid

    cdef int _write_bind_params_column(self, WriteBuffer buf,
                                       OracleMetadata metadata,
                                       object value) except -1:
        cdef:
            uint8_t ora_type_num = metadata.dbtype._ora_type_num
            ThinDbObjectTypeImpl typ_impl
            BaseThinCursorImpl cursor_impl
            BaseThinLobImpl lob_impl
            uint32_t num_bytes
            bytes temp_bytes
        if value is None:
            if ora_type_num == ORA_TYPE_NUM_BOOLEAN:
                buf.write_uint8(TNS_ESCAPE_CHAR)
                buf.write_uint8(1)
            elif ora_type_num == ORA_TYPE_NUM_OBJECT:
                buf.write_ub4(0)                # TOID
                buf.write_ub4(0)                # OID
                buf.write_ub4(0)                # snapshot
                buf.write_ub2(0)                # version
                buf.write_ub4(0)                # packed data length
                buf.write_ub4(TNS_OBJ_TOP_LEVEL)    # flags
            else:
                buf.write_uint8(0)
        elif ora_type_num == ORA_TYPE_NUM_VARCHAR \
                or ora_type_num == ORA_TYPE_NUM_CHAR \
                or ora_type_num == ORA_TYPE_NUM_LONG:
            if metadata.dbtype._csfrm == CS_FORM_IMPLICIT:
                temp_bytes = (<str> value).encode()
            else:
                buf._caps._check_ncharset_id()
                temp_bytes = (<str> value).encode(ENCODING_UTF16)
            buf.write_bytes_with_length(temp_bytes)
        elif ora_type_num == ORA_TYPE_NUM_RAW \
                or ora_type_num == ORA_TYPE_NUM_LONG_RAW:
            buf.write_bytes_with_length(value)
        elif ora_type_num == ORA_TYPE_NUM_NUMBER \
                or ora_type_num == ORA_TYPE_NUM_BINARY_INTEGER:
            if isinstance(value, bool):
                temp_bytes = b'1' if value is True else b'0'
            else:
                temp_bytes = (<str> cpython.PyObject_Str(value)).encode()
            buf.write_oracle_number(temp_bytes)
        elif ora_type_num == ORA_TYPE_NUM_DATE \
                or ora_type_num == ORA_TYPE_NUM_TIMESTAMP \
                or ora_type_num == ORA_TYPE_NUM_TIMESTAMP_TZ \
                or ora_type_num == ORA_TYPE_NUM_TIMESTAMP_LTZ:
            buf.write_oracle_date(value, metadata.dbtype._buffer_size_factor)
        elif ora_type_num == ORA_TYPE_NUM_BINARY_DOUBLE:
            buf.write_binary_double(value)
        elif ora_type_num == ORA_TYPE_NUM_BINARY_FLOAT:
            buf.write_binary_float(value)
        elif ora_type_num == ORA_TYPE_NUM_CURSOR:
            cursor_impl = value._impl
            if cursor_impl is None:
                errors._raise_err(errors.ERR_CURSOR_NOT_OPEN)
            if cursor_impl._statement is None:
                cursor_impl._statement = self.conn_impl._get_statement()
            if cursor_impl._statement._cursor_id == 0:
                buf.write_uint8(1)
                buf.write_uint8(0)
            else:
                buf.write_ub4(1)
                buf.write_ub4(cursor_impl._statement._cursor_id)
            cursor_impl.statement = None
        elif ora_type_num == ORA_TYPE_NUM_BOOLEAN:
            buf.write_bool(value)
        elif ora_type_num == ORA_TYPE_NUM_INTERVAL_DS:
            buf.write_interval_ds(value)
        elif ora_type_num == ORA_TYPE_NUM_INTERVAL_YM:
            buf.write_interval_ym(value)
        elif ora_type_num in (
                ORA_TYPE_NUM_BLOB,
                ORA_TYPE_NUM_CLOB,
                ORA_TYPE_NUM_BFILE
            ):
            buf.write_lob_with_length(value._impl)
        elif ora_type_num in (ORA_TYPE_NUM_ROWID, ORA_TYPE_NUM_UROWID):
            temp_bytes = (<str> value).encode()
            buf.write_bytes_with_length(temp_bytes)
        elif ora_type_num == ORA_TYPE_NUM_OBJECT:
            buf.write_dbobject(value._impl)
        elif ora_type_num == ORA_TYPE_NUM_JSON:
            buf.write_oson(value, self.conn_impl._oson_max_fname_size)
        elif ora_type_num == ORA_TYPE_NUM_VECTOR:
            buf.write_vector(value)
        else:
            errors._raise_err(errors.ERR_DB_TYPE_NOT_SUPPORTED,
                              name=metadata.dbtype.name)

    cdef int _write_bind_params_row(self, WriteBuffer buf, list params,
                                    uint32_t pos) except -1:
        """
        Write a row of bind parameters. Note that non-LONG values are written
        first followed by any LONG values.
        """
        cdef:
            uint32_t i, num_elements, offset = self.offset
            bint found_long = False
            OracleMetadata metadata
            ThinVarImpl var_impl
            BindInfo bind_info
        for i, bind_info in enumerate(params):
            if bind_info._is_return_bind:
                continue
            var_impl = bind_info._bind_var_impl
            metadata = var_impl.metadata
            if var_impl.is_array:
                num_elements = var_impl.num_elements_in_array
                buf.write_ub4(num_elements)
                for value in var_impl._values[:num_elements]:
                    self._write_bind_params_column(buf, metadata, value)
            else:
                if not self.cursor_impl._statement._is_plsql \
                        and metadata.buffer_size > buf._caps.max_string_size:
                    found_long = True
                    continue
                self._write_bind_params_column(buf, metadata,
                                               var_impl._values[pos + offset])
        if found_long:
            for i, bind_info in enumerate(params):
                if bind_info._is_return_bind:
                    continue
                var_impl = bind_info._bind_var_impl
                metadata = var_impl.metadata
                if metadata.buffer_size <= buf._caps.max_string_size:
                    continue
                self._write_bind_params_column(buf, metadata,
                                               var_impl._values[pos + offset])

    cdef int postprocess(self) except -1:
        """
        Run any variable out converter functions on all non-null values that
        were returned in the current database response. This must be done
        independently since the out converter function may itself invoke a
        database round-trip.
        """
        cdef:
            uint32_t i, j, num_elements
            object value, element_value
            ThinVarImpl var_impl
        if self.out_var_impls is None:
            return 0
        for var_impl in self.out_var_impls:
            if var_impl is None or var_impl.outconverter is None:
                continue
            if not self.cursor_impl.fetching_arrow:
                var_impl._last_raw_value = \
                        var_impl._values[self.cursor_impl._last_row_index]
            if var_impl.is_array:
                num_elements = var_impl.num_elements_in_array
            else:
                num_elements = self.row_index
            for i in range(num_elements):
                value = var_impl._values[i]
                if value is None and not var_impl.convert_nulls:
                    continue
                if isinstance(value, list):
                    for j, element_value in enumerate(value):
                        if element_value is None:
                            continue
                        value[j] = var_impl.outconverter(element_value)
                else:
                    var_impl._values[i] = var_impl.outconverter(value)

    async def postprocess_async(self):
        """
        Run any variable out converter functions on all non-null values that
        were returned in the current database response. This must be done
        independently since the out converter function may itself invoke a
        database round-trip.
        """
        cdef:
            object value, element_value, fn
            uint32_t i, j, num_elements
            ThinVarImpl var_impl
        if self.out_var_impls is None:
            return 0
        for var_impl in self.out_var_impls:
            if var_impl is None or var_impl.outconverter is None:
                continue
            if not self.cursor_impl.fetching_arrow:
                var_impl._last_raw_value = \
                        var_impl._values[self.cursor_impl._last_row_index]
            if var_impl.is_array:
                num_elements = var_impl.num_elements_in_array
            else:
                num_elements = self.row_index
            fn = var_impl.outconverter
            for i in range(num_elements):
                value = var_impl._values[i]
                if value is None and not var_impl.convert_nulls:
                    continue
                if isinstance(value, list):
                    for j, element_value in enumerate(value):
                        if element_value is None:
                            continue
                        element_value = fn(element_value)
                        if inspect.isawaitable(element_value):
                            element_value = await element_value
                        value[j] = element_value
                else:
                    value = fn(value)
                    if inspect.isawaitable(value):
                        value = await value
                    var_impl._values[i] = value

    cdef int preprocess(self) except -1:
        cdef:
            Statement statement = self.cursor_impl._statement
            BindInfo bind_info
        if statement._is_returning and not self.parse_only:
            self.out_var_impls = []
            for bind_info in statement._bind_info_list:
                if not bind_info._is_return_bind:
                    continue
                self.out_var_impls.append(bind_info._bind_var_impl)
        elif statement._is_query:
            self._preprocess_query()
