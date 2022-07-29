#------------------------------------------------------------------------------
# Copyright (c) 2020, 2022, Oracle and/or its affiliates.
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
# messages.pyx
#
# Cython file defining the various messages that are sent to the database and
# the responses that are received by the client (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

@cython.freelist(20)
cdef class _OracleErrorInfo:
    cdef:
        uint32_t num
        uint16_t cursor_id
        uint16_t pos
        uint64_t rowcount
        bint is_warning
        str message
        Rowid rowid
        list batcherrors


cdef class Message:
    cdef:
        ThinConnImpl conn_impl
        _OracleErrorInfo error_info
        uint8_t message_type
        uint8_t function_code
        uint32_t call_status
        uint16_t end_to_end_seq_num
        uint8_t packet_type
        uint8_t packet_flags
        bint error_occurred
        bint flush_out_binds
        bint processed_error
        bint resend

    cdef bint _has_more_data(self, ReadBuffer buf):
        return buf.bytes_left() > 0 and not self.flush_out_binds

    cdef int _initialize(self, ThinConnImpl conn_impl) except -1:
        """
        Initializes the message to contain the connection and a place to store
        error information. For DRCP, the status of the connection may change
        after the first round-trip to the database so this information needs to
        be preserved. Child classes may have their own initialization. In order
        to avoid overhead using the constructor, a special hook method is used
        instead.
        """
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

    cdef int _preprocess(self) except -1:
        pass

    cdef int _postprocess(self) except -1:
        pass

    cdef int _process_error_info(self, ReadBuffer buf) except -1:
        cdef:
            _OracleErrorInfo info = self.error_info
            uint16_t num_entries, error_code
            uint32_t num_bytes, i, offset
            uint8_t first_byte
            str error_msg
        buf.read_ub4(&self.call_status)     # end of call status
        buf.skip_ub2()                      # end to end seq#
        buf.skip_ub4()                      # current row number
        buf.skip_ub2()                      # error number
        buf.skip_ub2()                      # array elem error
        buf.skip_ub2()                      # array elem error
        buf.read_ub2(&info.cursor_id)       # cursor id
        buf.read_ub2(&info.pos)             # error position
        buf.skip_ub1()                      # sql type
        buf.skip_ub1()                      # fatal?
        buf.skip_ub2()                      # flags
        buf.skip_ub2()                      # user cursor options
        buf.skip_ub1()                      # UPI parameter
        buf.skip_ub1()                      # warning flag
        buf.read_rowid(&info.rowid)         # rowid
        buf.skip_ub4()                      # OS error
        buf.skip_ub1()                      # statement number
        buf.skip_ub1()                      # call number
        buf.skip_ub2()                      # padding
        buf.skip_ub4()                      # success iters
        buf.read_ub4(&num_bytes)            # oerrdd (logical rowid)
        if num_bytes > 0:
            buf.skip_raw_bytes_chunked()
        self.processed_error = True

        # batch error codes
        buf.read_ub2(&num_entries)          # batch error codes array
        if num_entries > 0:
            info.batcherrors = []
            buf.read_ub1(&first_byte)
            for i in range(num_entries):
                if first_byte == TNS_LONG_LENGTH_INDICATOR:
                    buf.skip_ub4()          # chunk length ignored
                buf.read_ub2(&error_code)
                info.batcherrors.append(errors._Error(code=error_code))
            if first_byte == TNS_LONG_LENGTH_INDICATOR:
                buf.skip_raw_bytes(1)       # ignore end marker

        # batch error offsets
        buf.read_ub2(&num_entries)          # batch error row offset array
        if num_entries > 0:
            buf.read_ub1(&first_byte)
            for i in range(num_entries):
                if first_byte == TNS_LONG_LENGTH_INDICATOR:
                    buf.skip_ub4()          # chunk length ignored
                buf.read_ub4(&offset)
                info.batcherrors[i].offset = offset
            if first_byte == TNS_LONG_LENGTH_INDICATOR:
                buf.skip_raw_bytes(1)       # ignore end marker

        # batch error messages
        buf.read_ub2(&num_entries)          # batch error messages array
        if num_entries > 0:
            buf.skip_raw_bytes(1)           # ignore packed size
            for i in range(num_entries):
                buf.skip_ub2()              # skip chunk length
                info.batcherrors[i].message = \
                        buf.read_str(TNS_CS_IMPLICIT).rstrip()
                buf.skip_raw_bytes(2)       # ignore end marker

        buf.read_ub4(&info.num)             # error number (extended)
        buf.read_ub8(&info.rowcount)        # row number (extended)
        if info.num != 0:
            self.error_occurred = True
            info.message = buf.read_str(TNS_CS_IMPLICIT).rstrip()
        info.is_warning = False

    cdef int _process_message(self, ReadBuffer buf,
                              uint8_t message_type) except -1:
        if message_type == TNS_MSG_TYPE_ERROR:
            self._process_error_info(buf)
        elif message_type == TNS_MSG_TYPE_WARNING:
            self._process_warning_info(buf)
        elif message_type == TNS_MSG_TYPE_STATUS:
            buf.read_ub4(&self.call_status)
            buf.read_ub2(&self.end_to_end_seq_num)
        elif message_type == TNS_MSG_TYPE_PARAMETER:
            self._process_return_parameters(buf)
        elif message_type == TNS_MSG_TYPE_SERVER_SIDE_PIGGYBACK:
            self._process_server_side_piggyback(buf)
        else:
            errors._raise_err(errors.ERR_MESSAGE_TYPE_UNKNOWN,
                              message_type=message_type)

    cdef int _process_return_parameters(self, ReadBuffer buf) except -1:
        raise NotImplementedError()

    cdef int _process_server_side_piggyback(self, ReadBuffer buf) except -1:
        cdef:
            uint16_t num_elements, i, temp16
            uint32_t num_bytes, flags
            uint8_t opcode
        buf.read_ub1(&opcode)
        if opcode == TNS_SERVER_PIGGYBACK_LTXID:
            buf.read_ub4(&num_bytes)
            if num_bytes > 0:
                buf.skip_raw_bytes(num_bytes)
        elif opcode == TNS_SERVER_PIGGYBACK_QUERY_CACHE_INVALIDATION \
                or opcode == TNS_SERVER_PIGGYBACK_TRACE_EVENT:
            pass
        elif opcode == TNS_SERVER_PIGGYBACK_OS_PID_MTS:
            buf.read_ub2(&temp16)
            buf.skip_raw_bytes(temp16 + 1)
        elif opcode == TNS_SERVER_PIGGYBACK_SYNC:
            buf.skip_ub2()                  # skip number of DTYs
            buf.skip_ub1()                  # skip length of DTYs
            buf.read_ub2(&num_elements)
            buf.skip_ub1()                  # skip length
            for i in range(num_elements):
                buf.read_ub2(&temp16)
                if temp16 > 0:              # skip key
                    buf.skip_raw_bytes(temp16 + 1)
                buf.read_ub2(&temp16)
                if temp16 > 0:              # skip value
                    buf.skip_raw_bytes(temp16 + 1)
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
                buf.skip_raw_bytes(num_bytes)
        elif opcode == TNS_SERVER_PIGGYBACK_SESS_RET:
            buf.skip_ub2()
            buf.skip_ub1()
            buf.read_ub2(&num_elements)
            if num_elements > 0:
                buf.skip_ub1()
                for i in range(num_elements):
                    buf.read_ub2(&temp16)
                    if temp16 > 0:          # skip key
                        buf.skip_raw_bytes(temp16 + 1)
                    buf.read_ub2(&temp16)
                    if temp16 > 0:          # skip value
                        buf.skip_raw_bytes(temp16 + 1)
                    buf.skip_ub2()          # skip flags
            buf.read_ub4(&flags)            # session flags
            if flags & TNS_SESSGET_SESSION_CHANGED:
                if self.conn_impl._drcp_establish_session:
                    self.conn_impl._reset_statement_cache()
            self.conn_impl._drcp_establish_session = False
            buf.skip_ub4()                  # session id
            buf.skip_ub2()                  # serial number
        else:
            msg = f"Unhandled server side piggyback opcode: {opcode}"
            raise Exception(msg)

    cdef int _process_warning_info(self, ReadBuffer buf) except -1:
        cdef:
            _OracleErrorInfo info = self.error_info
            const char_type *ptr
            uint16_t num_bytes, temp16
        buf.read_ub2(&temp16)               # error number
        info.num = temp16
        buf.read_ub2(&num_bytes)            # length of error message
        buf.skip_ub2()                      # flags
        if info.num != 0 and num_bytes > 0:
            ptr = buf.read_raw_bytes(num_bytes)
            info.message = ptr[:num_bytes].decode().rstrip()
        info.is_warning = True

    cdef int _write_function_code(self, WriteBuffer buf) except -1:
        buf.write_uint8(self.message_type)
        buf.write_uint8(self.function_code)
        buf.write_seq_num()

    cdef int _write_message(self, WriteBuffer buf) except -1:
        self._write_function_code(buf)

    cdef int process(self, ReadBuffer buf) except -1:
        cdef uint8_t message_type
        self.flush_out_binds = False
        self.processed_error = False
        self._preprocess()
        buf.skip_raw_bytes(2)               # skip data flags
        while self._has_more_data(buf):
            buf.read_ub1(&message_type)
            self._process_message(buf, message_type)
        self._postprocess()

    cdef int send(self, WriteBuffer buf) except -1:
        buf.start_request(TNS_PACKET_TYPE_DATA)
        self._write_message(buf)
        buf.end_request()


cdef class MessageWithData(Message):
    cdef:
        ThinCursorImpl cursor_impl
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

    cdef int _adjust_fetch_info(self,
                                ThinVarImpl prev_var_impl,
                                FetchInfo fetch_info) except -1:
        """
        When a query is re-executed but the data type of a column has changed
        the server returns the type information of the new type. However, if
        the data type returned now is a CLOB or BLOB and the data type
        previously returned was CHAR/VARCHAR/RAW (or the equivalent long
        types), then the server returns the data as LONG (RAW), similarly to
        what happens when a define is done to return CLOB/BLOB as string/bytes.
        Detect this situation and adjust the fetch type appropriately.
        """
        cdef:
            FetchInfo prev_fetch_info = prev_var_impl._fetch_info
            uint8_t csfrm = prev_var_impl.dbtype._csfrm
            uint8_t type_num
        if fetch_info._dbtype._ora_type_num == TNS_DATA_TYPE_CLOB \
                and prev_fetch_info._dbtype._ora_type_num in \
                        (TNS_DATA_TYPE_CHAR, TNS_DATA_TYPE_VARCHAR,
                         TNS_DATA_TYPE_LONG):
            type_num = TNS_DATA_TYPE_LONG
            fetch_info._dbtype = DbType._from_ora_type_and_csfrm(type_num,
                                                                 csfrm)
        elif fetch_info._dbtype._ora_type_num == TNS_DATA_TYPE_BLOB \
                and prev_fetch_info._dbtype._ora_type_num in \
                        (TNS_DATA_TYPE_RAW, TNS_DATA_TYPE_LONG_RAW):
            type_num = TNS_DATA_TYPE_LONG_RAW
            fetch_info._dbtype = DbType._from_ora_type_and_csfrm(type_num,
                                                                 csfrm)

    cdef object _create_cursor_from_describe(self, ReadBuffer buf,
                                             object cursor=None):
        cdef ThinCursorImpl cursor_impl
        if cursor is None:
            cursor = self.cursor.connection.cursor()
        cursor_impl = cursor._impl
        cursor_impl._statement = Statement()
        cursor_impl._fetch_array_size = cursor.arraysize + cursor.prefetchrows
        cursor_impl._more_rows_to_fetch = True
        cursor_impl._statement._is_query = True
        cursor_impl._statement._requires_full_execute = True
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
        cdef const char_type *ptr = buf._get_raw(num_bytes)
        if self.bit_vector_buf is None:
            self.bit_vector_buf = array.array('B')
            array.resize(self.bit_vector_buf, num_bytes)
        self.bit_vector = <const char_type*> self.bit_vector_buf.data.as_chars
        memcpy(<void*> self.bit_vector, ptr, num_bytes)

    cdef bint _has_more_data(self, ReadBuffer buf):
        return not self.processed_error and not self.flush_out_binds

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
            bint returning_only = True, all_values_null = True
            list bind_var_impls, bind_vals
            uint32_t i
            BindInfo bind_info
        bind_var_impls = []
        for bind_info in params:
            if not bind_info._is_return_bind:
                returning_only = False
            bind_vals = bind_info._bind_var_impl._values
            for i in range(len(bind_vals)):
                if cpython.PyList_GET_ITEM(bind_vals, i) is not \
                        <cpython.ref.PyObject*> None:
                    all_values_null = False
                    break
            bind_var_impls.append(bind_info._bind_var_impl)
        self._write_column_metadata(buf, bind_var_impls)

        # plsql batch executions without bind values
        if self.cursor_impl._statement._is_plsql and self.num_execs > 1 \
                and not all_values_null:
            buf.write_uint8(TNS_MSG_TYPE_ROW_DATA)
            buf.write_uint8(TNS_ESCAPE_CHAR)
            buf.write_uint8(1)

        # write parameter values unless statement contains only returning binds
        elif not returning_only:
            for i in range(self.num_execs):
                buf.write_uint8(TNS_MSG_TYPE_ROW_DATA)
                self._write_bind_params_row(buf, params, i)

    cdef int _preprocess(self) except -1:
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

    cdef int _preprocess_query(self) except -1:
        """
        Actions that takes place before query data is processed.
        """
        cdef:
            ThinCursorImpl cursor_impl = self.cursor_impl
            Statement statement = cursor_impl._statement
            object type_handler, conn
            ThinVarImpl var_impl
            ssize_t i, num_vals

        # set values to indicate the start of a new fetch operation
        self.in_fetch = True
        cursor_impl._more_rows_to_fetch = True
        cursor_impl._buffer_rowcount = cursor_impl._buffer_index = 0

        # if no fetch variables exist, nothing further to do at this point; the
        # processing that follows will take the metadata returned by the server
        # and use it to create new fetch variables
        if cursor_impl.fetch_var_impls is None:
            return 0

        # if the type handler set on the cursor or connection does not match
        # the one that was used during the last fetch, rebuild the fetch
        # variables in order to take the new type handler into account
        conn = self.cursor.connection
        type_handler = cursor_impl._get_output_type_handler()
        if type_handler is not statement._last_output_type_handler:
            for i, var_impl in enumerate(cursor_impl.fetch_var_impls):
                cursor_impl._create_fetch_var(conn, self.cursor, type_handler,
                                              i, var_impl._fetch_info)
            statement._last_output_type_handler = type_handler

        # the list of output variables is equivalent to the fetch variables
        self.out_var_impls = cursor_impl.fetch_var_impls

        # resize fetch variables, if necessary, to allow room in each variable
        # for the fetch array size
        for var_impl in self.out_var_impls:
            if var_impl.num_elements >= cursor_impl._fetch_array_size:
                continue
            num_vals = (cursor_impl._fetch_array_size - var_impl.num_elements)
            var_impl.num_elements = cursor_impl._fetch_array_size
            var_impl._values.extend([None] * num_vals)

    cdef int _postprocess(self) except -1:
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
            if var_impl.outconverter is None:
                continue
            var_impl._last_raw_value = \
                    var_impl._values[self.cursor_impl._last_row_index]
            if var_impl.is_array:
                num_elements = var_impl.num_elements_in_array
            else:
                num_elements = self.row_index
            for i in range(num_elements):
                value = var_impl._values[i]
                if value is None:
                    continue
                if isinstance(value, list):
                    for j, element_value in enumerate(value):
                        if element_value is None:
                            continue
                        value[j] = var_impl.outconverter(element_value)
                else:
                    var_impl._values[i] = var_impl.outconverter(value)

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
            ThinCursorImpl cursor_impl
            object column_value = None
            int32_t actual_num_bytes
            uint32_t buffer_size
            FetchInfo fetch_info
            Rowid rowid
        fetch_info = var_impl._fetch_info
        if fetch_info is not None:
            ora_type_num = fetch_info._dbtype._ora_type_num
            csfrm =  fetch_info._dbtype._csfrm
            buffer_size = fetch_info._buffer_size
        else:
            ora_type_num = var_impl.dbtype._ora_type_num
            csfrm = var_impl.dbtype._csfrm
            buffer_size = var_impl.buffer_size
        if var_impl.bypass_decode:
            ora_type_num = TNS_DATA_TYPE_RAW
        if buffer_size == 0 and ora_type_num != TNS_DATA_TYPE_LONG \
                and ora_type_num != TNS_DATA_TYPE_LONG_RAW:
            column_value = None             # column is null by describe
        elif ora_type_num == TNS_DATA_TYPE_VARCHAR \
                or ora_type_num == TNS_DATA_TYPE_CHAR \
                or ora_type_num == TNS_DATA_TYPE_LONG:
            if csfrm == TNS_CS_NCHAR:
                buf._caps._check_ncharset_id()
            column_value = buf.read_str(csfrm)
        elif ora_type_num == TNS_DATA_TYPE_RAW \
                or ora_type_num == TNS_DATA_TYPE_LONG_RAW:
            column_value = buf.read_bytes()
        elif ora_type_num == TNS_DATA_TYPE_NUMBER:
            column_value = buf.read_oracle_number(var_impl._preferred_num_type)
        elif ora_type_num == TNS_DATA_TYPE_DATE \
                or ora_type_num == TNS_DATA_TYPE_TIMESTAMP \
                or ora_type_num == TNS_DATA_TYPE_TIMESTAMP_LTZ \
                or ora_type_num == TNS_DATA_TYPE_TIMESTAMP_TZ:
            column_value = buf.read_date()
        elif ora_type_num == TNS_DATA_TYPE_ROWID:
            if not self.in_fetch:
                column_value = buf.read_urowid()
            else:
                buf.read_ub1(&num_bytes)
                if _is_null_length(num_bytes):
                    column_value = None
                else:
                    buf.read_rowid(&rowid)
                    column_value = _encode_rowid(&rowid)
        elif ora_type_num == TNS_DATA_TYPE_UROWID:
            column_value = buf.read_urowid()
        elif ora_type_num == TNS_DATA_TYPE_BINARY_DOUBLE:
            column_value = buf.read_binary_double()
        elif ora_type_num == TNS_DATA_TYPE_BINARY_FLOAT:
            column_value = buf.read_binary_float()
        elif ora_type_num == TNS_DATA_TYPE_BINARY_INTEGER:
            column_value = buf.read_oracle_number(NUM_TYPE_INT)
            if column_value is not None:
                column_value = int(column_value)
        elif ora_type_num == TNS_DATA_TYPE_CURSOR:
            buf.read_ub1(&num_bytes)
            if _is_null_length(num_bytes):
                column_value = None
            else:
                if not self.in_fetch:
                    column_value = var_impl._values[pos]
                column_value = self._create_cursor_from_describe(buf,
                                                                 column_value)
                cursor_impl = column_value._impl
                buf.read_ub2(&cursor_impl._statement._cursor_id)
        elif ora_type_num == TNS_DATA_TYPE_BOOLEAN:
            column_value = buf.read_bool()
        elif ora_type_num == TNS_DATA_TYPE_INTERVAL_DS:
            column_value = buf.read_interval_ds()
        elif ora_type_num in (TNS_DATA_TYPE_CLOB, TNS_DATA_TYPE_BLOB):
            column_value = buf.read_lob(self.conn_impl, var_impl.dbtype)
        else:
            errors._raise_err(errors.ERR_DB_TYPE_NOT_SUPPORTED,
                              name=var_impl.dbtype.name)
        if not self.in_fetch:
            buf.read_sb4(&actual_num_bytes)
            if actual_num_bytes != 0 and column_value is not None:
                unit_type = "bytes" if isinstance(column_value, bytes) \
                            else "characters"
                errors._raise_err(errors.ERR_COLUMN_TRUNCATED,
                                  col_value_len=len(column_value),
                                  unit=unit_type, actual_len=actual_num_bytes)
        elif ora_type_num == TNS_DATA_TYPE_LONG \
                or ora_type_num == TNS_DATA_TYPE_LONG_RAW:
            buf.skip_sb4()                  # null indicator
            buf.skip_ub4()                  # return code
        if column_value is not None:
            if var_impl._conv_func is not None:
                column_value = var_impl._conv_func(column_value)
        return column_value

    cdef FetchInfo _process_column_info(self, ReadBuffer buf,
                                        ThinCursorImpl cursor_impl):
        cdef:
            uint8_t data_type, csfrm
            int8_t precision, scale
            uint8_t nulls_allowed
            FetchInfo fetch_info
            uint32_t num_bytes
        buf.read_ub1(&data_type)
        fetch_info = FetchInfo()
        buf.skip_ub1()                      # flags
        buf.read_sb1(&precision)
        fetch_info._precision = precision
        if data_type == TNS_DATA_TYPE_NUMBER \
                or data_type == TNS_DATA_TYPE_INTERVAL_DS \
                or data_type == TNS_DATA_TYPE_TIMESTAMP \
                or data_type == TNS_DATA_TYPE_TIMESTAMP_LTZ \
                or data_type == TNS_DATA_TYPE_TIMESTAMP_TZ:
            buf.read_sb2(&fetch_info._scale)
        else:
            buf.read_sb1(&scale)
            fetch_info._scale = scale
        buf.read_ub4(&fetch_info._buffer_size)
        buf.skip_ub4()                      # max number of array elements
        buf.skip_ub4()                      # cont flags
        buf.read_ub4(&num_bytes)            # OID
        if num_bytes > 0:
            buf.skip_raw_bytes(num_bytes + 1)
        buf.skip_ub2()                      # version
        buf.skip_ub2()                      # character set id
        buf.read_ub1(&csfrm)                # character set form
        fetch_info._dbtype = DbType._from_ora_type_and_csfrm(data_type, csfrm)
        buf.read_ub4(&fetch_info._size)
        if data_type == TNS_DATA_TYPE_RAW:
            fetch_info._size = fetch_info._buffer_size
        if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_12_2:
            buf.skip_ub4()                  # oaccolid
        buf.read_ub1(&nulls_allowed)
        fetch_info._nulls_allowed = nulls_allowed
        buf.skip_ub1()                      # v7 length of name
        buf.read_ub4(&num_bytes)
        if num_bytes > 0:
            fetch_info._name = buf.read_str(TNS_CS_IMPLICIT)
        buf.read_ub4(&num_bytes)
        if num_bytes > 0:
            buf.skip_ub1()                  # skip repeated length
            buf.skip_raw_bytes(num_bytes)   # schema name
        buf.read_ub4(&num_bytes)
        if num_bytes > 0:
            buf.skip_ub1()                  # skip repeated length
            buf.skip_raw_bytes(num_bytes)   # type name
        buf.skip_ub2()                      # column position
        buf.skip_ub4()                      # uds flag
        return fetch_info

    cdef int _process_describe_info(self, ReadBuffer buf,
                                    object cursor,
                                    ThinCursorImpl cursor_impl) except -1:
        cdef:
            Statement stmt = cursor_impl._statement
            list prev_fetch_var_impls
            object type_handler, conn
            uint32_t num_bytes, i
            FetchInfo fetch_info
            str message
        buf.skip_ub4()                      # max row size
        buf.read_ub4(&cursor_impl._num_columns)
        prev_fetch_var_impls = self.cursor_impl.fetch_var_impls
        cursor_impl._init_fetch_vars(cursor_impl._num_columns)
        if cursor_impl._num_columns > 0:
            buf.skip_ub1()
        type_handler = cursor_impl._get_output_type_handler()
        conn = self.cursor.connection
        for i in range(cursor_impl._num_columns):
            fetch_info = self._process_column_info(buf, cursor_impl)
            if prev_fetch_var_impls is not None:
                self._adjust_fetch_info(prev_fetch_var_impls[i], fetch_info)
            cursor_impl._create_fetch_var(conn, self.cursor, type_handler, i,
                                          fetch_info)
        buf.read_ub4(&num_bytes)
        if num_bytes > 0:
            buf.skip_raw_bytes(num_bytes + 1)   # current date
        buf.skip_ub4()                      # dcbflag
        buf.skip_ub4()                      # dcbmdbz
        buf.skip_ub4()                      # dcbmnpr
        buf.skip_ub4()                      # dcbmxpr
        buf.read_ub4(&num_bytes)
        if num_bytes > 0:
            buf.skip_raw_bytes(num_bytes + 1)   # dcbqcky
        stmt._fetch_vars = cursor_impl.fetch_vars
        stmt._fetch_var_impls = cursor_impl.fetch_var_impls
        stmt._num_columns = cursor_impl._num_columns
        stmt._last_output_type_handler = type_handler

    cdef int _process_error_info(self, ReadBuffer buf) except -1:
        cdef:
            ThinCursorImpl cursor_impl = self.cursor_impl
            ThinConnImpl conn_impl = self.conn_impl
            object exc_type
        Message._process_error_info(self, buf)
        cursor_impl._statement._cursor_id = self.error_info.cursor_id
        if not cursor_impl._statement._is_plsql:
            cursor_impl.rowcount = self.error_info.rowcount
        cursor_impl._lastrowid = self.error_info.rowid
        cursor_impl._batcherrors = self.error_info.batcherrors
        if self.batcherrors and cursor_impl._batcherrors is None:
            cursor_impl._batcherrors = []
        if self.error_info.num == TNS_ERR_NO_DATA_FOUND:
            self.error_info.num = 0
            cursor_impl._more_rows_to_fetch = False
            self.error_occurred = False
        elif self.error_info.num == TNS_ERR_VAR_NOT_IN_SELECT_LIST:
            conn_impl._add_cursor_to_close(cursor_impl._statement)
            cursor_impl._statement._cursor_id = 0
        elif self.error_info.num != 0 and self.error_info.cursor_id != 0:
            exc_type = get_exception_class(self.error_info.num)
            if exc_type is not exceptions.IntegrityError:
                conn_impl._add_cursor_to_close(cursor_impl._statement)
                cursor_impl._statement._cursor_id = 0
        if self.error_info.batcherrors is not None:
            self.error_occurred = False

    cdef int _process_implicit_result(self, ReadBuffer buf) except -1:
        cdef:
            ThinCursorImpl child_cursor_impl
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
            uint16_t i, num_binds, num_bytes, temp16
            BindInfo bind_info
            bint has_in_bind = False
        buf.skip_ub1()                      # flag
        buf.read_ub2(&num_binds)            # num requests
        buf.read_ub4(&self.row_index)       # iter num
        buf.skip_ub4()                      # num iters this time
        buf.read_ub2(&temp16)               # uac buffer length
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
                has_in_bind = True
                continue
            self.out_var_impls.append(bind_info._bind_var_impl)
        if self.cursor_impl._statement._is_plsql and \
                self.out_var_impls and has_in_bind:
            self.cursor_impl._statement._plsql_multiple_execs = True

    cdef int _process_message(self, ReadBuffer buf,
                              uint8_t message_type) except -1:
        if message_type == TNS_MSG_TYPE_ROW_HEADER:
            self._process_row_header(buf)
        elif message_type == TNS_MSG_TYPE_ROW_DATA:
            self._process_row_data(buf)
        elif message_type == TNS_MSG_TYPE_FLUSH_OUT_BINDS:
            self.flush_out_binds = True
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
            buf.skip_raw_bytes(num_bytes + 1)   # rxhrid

    cdef int _write_column_metadata(self, WriteBuffer buf,
                                    list bind_var_impls) except -1:
        cdef:
            uint8_t ora_type_num, flag
            ThinVarImpl var_impl
        for var_impl in bind_var_impls:
            ora_type_num = var_impl.dbtype._ora_type_num
            if ora_type_num == TNS_DATA_TYPE_ROWID:
                ora_type_num = TNS_DATA_TYPE_UROWID
            flag = TNS_BIND_USE_INDICATORS
            if var_impl.is_array:
                flag |= TNS_BIND_ARRAY
            buf.write_uint8(ora_type_num)
            buf.write_uint8(flag)
            # precision and scale are always written as zero as the server
            # expects that and complains if any other value is sent!
            buf.write_uint8(0)
            buf.write_uint8(0)
            if var_impl.buffer_size >= TNS_MIN_LONG_LENGTH:
                buf.write_ub4(TNS_MAX_LONG_LENGTH)
            else:
                buf.write_ub4(var_impl.buffer_size)
            if var_impl.is_array:
                buf.write_ub4(var_impl.num_elements)
            else:
                buf.write_ub4(0)            # max num elements
            buf.write_ub4(0)                # cont flag
            buf.write_ub4(0)                # OID
            buf.write_ub4(0)                # version
            if var_impl.dbtype._csfrm != 0:
                buf.write_ub4(TNS_CHARSET_UTF8)
            else:
                buf.write_ub4(0)
            buf.write_uint8(var_impl.dbtype._csfrm)
            buf.write_ub4(0)                # max chars (not used)
            if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_12_2:
                buf.write_ub4(0)            # oaccolid

    cdef int _write_bind_params_column(self, WriteBuffer buf,
                                       ThinVarImpl var_impl,
                                       object value) except -1:
        cdef:
            uint8_t ora_type_num = var_impl.dbtype._ora_type_num
            ThinCursorImpl cursor_impl
            ThinLobImpl lob_impl
            uint32_t num_bytes
            bytes temp_bytes
        if value is None:
            if ora_type_num == TNS_DATA_TYPE_BOOLEAN:
                buf.write_uint8(TNS_ESCAPE_CHAR)
                buf.write_uint8(1)
            else:
                buf.write_uint8(0)
        elif ora_type_num == TNS_DATA_TYPE_VARCHAR \
                or ora_type_num == TNS_DATA_TYPE_CHAR \
                or ora_type_num == TNS_DATA_TYPE_LONG:
            if var_impl.dbtype._csfrm == TNS_CS_IMPLICIT:
                temp_bytes = (<str> value).encode()
            else:
                buf._caps._check_ncharset_id()
                temp_bytes = (<str> value).encode(TNS_ENCODING_UTF16)
            buf.write_bytes_chunked(temp_bytes)
        elif ora_type_num == TNS_DATA_TYPE_RAW \
                or ora_type_num == TNS_DATA_TYPE_LONG_RAW:
            buf.write_bytes_chunked(value)
        elif ora_type_num == TNS_DATA_TYPE_NUMBER \
                or ora_type_num == TNS_DATA_TYPE_BINARY_INTEGER:
            if isinstance(value, bool):
                temp_bytes = b'1' if value is True else b'0'
            else:
                temp_bytes = (<str> cpython.PyObject_Str(value)).encode()
            buf.write_oracle_number(temp_bytes)
        elif ora_type_num == TNS_DATA_TYPE_DATE \
                or ora_type_num == TNS_DATA_TYPE_TIMESTAMP \
                or ora_type_num == TNS_DATA_TYPE_TIMESTAMP_TZ \
                or ora_type_num == TNS_DATA_TYPE_TIMESTAMP_LTZ:
            buf.write_oracle_date(value, var_impl.dbtype._buffer_size_factor)
        elif ora_type_num == TNS_DATA_TYPE_BINARY_DOUBLE:
            buf.write_binary_double(value)
        elif ora_type_num == TNS_DATA_TYPE_BINARY_FLOAT:
            buf.write_binary_float(value)
        elif ora_type_num == TNS_DATA_TYPE_CURSOR:
            cursor_impl = value._impl
            if cursor_impl._statement is None:
                cursor_impl._statement = Statement()
            if cursor_impl._statement._cursor_id == 0:
                buf.write_uint8(1)
                buf.write_uint8(0)
            else:
                buf.write_ub4(1)
                buf.write_ub4(cursor_impl._statement._cursor_id)
        elif ora_type_num == TNS_DATA_TYPE_BOOLEAN:
            if value:
                buf.write_uint8(2)
                buf.write_uint16(0x0101)
            else:
                buf.write_uint16(0x0100)
        elif ora_type_num == TNS_DATA_TYPE_INTERVAL_DS:
            buf.write_interval_ds(value)
        elif ora_type_num == TNS_DATA_TYPE_CLOB \
                or ora_type_num == TNS_DATA_TYPE_BLOB:
            lob_impl = value._impl
            num_bytes = <uint32_t> len(lob_impl._locator)
            buf.write_ub4(num_bytes)
            buf.write_bytes_chunked(lob_impl._locator)
        else:
            errors._raise_err(errors.ERR_DB_TYPE_NOT_SUPPORTED,
                              name=var_impl.dbtype.name)

    cdef int _write_bind_params_row(self, WriteBuffer buf, list params,
                                    uint32_t pos) except -1:
        """
        Write a row of bind parameters. Note that non-LONG values are written
        first followed by any LONG values.
        """
        cdef:
            uint32_t i, num_elements, offset = self.offset
            bint found_long = False
            ThinVarImpl var_impl
            BindInfo bind_info
        for i, bind_info in enumerate(params):
            if bind_info._is_return_bind:
                continue
            var_impl = bind_info._bind_var_impl
            if var_impl.is_array:
                num_elements = var_impl.num_elements_in_array
                buf.write_ub4(num_elements)
                for value in var_impl._values[:num_elements]:
                    self._write_bind_params_column(buf, var_impl, value)
            else:
                if var_impl.buffer_size >= TNS_MIN_LONG_LENGTH:
                    found_long = True
                    continue
                self._write_bind_params_column(buf, var_impl,
                                               var_impl._values[pos + offset])
        if found_long:
            for i, bind_info in enumerate(params):
                if bind_info._is_return_bind:
                    continue
                var_impl = bind_info._bind_var_impl
                if var_impl.buffer_size < TNS_MIN_LONG_LENGTH:
                    continue
                self._write_bind_params_column(buf, var_impl,
                                               var_impl._values[pos + offset])

    cdef int _write_close_cursors_piggyback(self, WriteBuffer buf) except -1:
        cdef:
            unsigned int *cursor_ids
            ssize_t i
        buf.write_uint8(TNS_MSG_TYPE_PIGGYBACK)
        buf.write_uint8(TNS_FUNC_CLOSE_CURSORS)
        buf.write_seq_num()
        buf.write_uint8(1)                  # pointer
        buf.write_ub4(self.conn_impl._num_cursors_to_close)
        cursor_ids = self.conn_impl._cursors_to_close.data.as_uints
        for i in range(self.conn_impl._num_cursors_to_close):
            buf.write_ub4(cursor_ids[i])
        self.conn_impl._num_cursors_to_close = 0

    cdef int _write_current_schema_piggyback(self, WriteBuffer buf) except -1:
        cdef bytes schema_bytes
        buf.write_uint8(TNS_MSG_TYPE_PIGGYBACK)
        buf.write_uint8(TNS_FUNC_SET_SCHEMA)
        buf.write_seq_num()
        buf.write_uint8(1)                  # pointer
        schema_bytes = self.conn_impl._current_schema.encode()
        buf.write_ub4(len(schema_bytes))
        buf.write_bytes(schema_bytes)

    cdef int _write_close_temp_lobs_piggyback(self,
                                              WriteBuffer buf) except -1:
        cdef:
            list lobs_to_close = self.conn_impl._temp_lobs_to_close
            uint64_t total_size = 0
        buf.write_uint8(TNS_MSG_TYPE_PIGGYBACK)
        buf.write_uint8(TNS_FUNC_LOB_OP)
        op_code = TNS_LOB_OP_FREE_TEMP | TNS_LOB_OP_ARRAY
        buf.write_seq_num()

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
        cdef:
            bytes action_bytes, client_identifier_bytes, client_info_bytes
            ThinConnImpl conn = self.conn_impl
            bytes module_bytes, dbop_bytes
            uint32_t flags = 0

        # determine which flags to send
        if conn._action_modified:
            flags |= TNS_END_TO_END_ACTION
        if conn._client_identifier_modified:
            flags |= TNS_END_TO_END_CLIENT_IDENTIFIER
        if conn._client_info_modified:
            flags |= TNS_END_TO_END_CLIENT_INFO
        if conn._module_modified:
            flags |= TNS_END_TO_END_MODULE
        if conn._dbop_modified:
            flags |= TNS_END_TO_END_DBOP

        # write initial packet data
        buf.write_uint8(TNS_MSG_TYPE_PIGGYBACK)
        buf.write_uint8(TNS_FUNC_SET_END_TO_END_ATTR)
        buf.write_seq_num()
        buf.write_uint8(0)                  # pointer (cidnam)
        buf.write_uint8(0)                  # pointer (cidser)
        buf.write_ub4(flags)

        # write client identifier header info
        if conn._client_identifier_modified:
            buf.write_uint8(1)              # pointer (client identifier)
            if conn._client_identifier is None:
                buf.write_ub4(0)
            else:
                client_identifier_bytes = conn._client_identifier.encode()
                buf.write_ub4(len(client_identifier_bytes))
        else:
            buf.write_uint8(0)              # pointer (client identifier)
            buf.write_ub4(0)                # length of client identifier

        # write module header info
        if conn._module_modified:
            buf.write_uint8(1)              # pointer (module)
            if conn._module is None:
                buf.write_ub4(0)
            else:
                module_bytes = conn._module.encode()
                buf.write_ub4(len(module_bytes))
        else:
            buf.write_uint8(0)              # pointer (module)
            buf.write_ub4(0)                # length of module

        # write action header info
        if conn._action_modified:
            buf.write_uint8(1)              # pointer (action)
            if conn._action is None:
                buf.write_ub4(0)
            else:
                action_bytes = conn._action.encode()
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
        if conn._client_info_modified:
            buf.write_uint8(1)              # pointer (client info)
            if conn._client_info is None:
                buf.write_ub4(0)
            else:
                client_info_bytes = conn._client_info.encode()
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
        if conn._dbop_modified:
            buf.write_uint8(1)              # pointer (dbop)
            if conn._dbop is None:
                buf.write_ub4(0)
            else:
                dbop_bytes = conn._dbop.encode()
                buf.write_ub4(len(dbop_bytes))
        else:
            buf.write_uint8(0)              # pointer (dbop)
            buf.write_ub4(0)                # length of dbop

        # write strings
        if conn._client_identifier_modified \
                and conn._client_identifier is not None:
            buf.write_bytes(client_identifier_bytes)
        if conn._module_modified and conn._module is not None:
            buf.write_bytes(module_bytes)
        if conn._action_modified and conn._action is not None:
            buf.write_bytes(action_bytes)
        if conn._client_info_modified and conn._client_info is not None:
            buf.write_bytes(client_info_bytes)
        if conn._dbop_modified and conn._dbop is not None:
            buf.write_bytes(dbop_bytes)

        # reset flags and values
        conn._action_modified = False
        conn._action = None
        conn._client_identifier_modified = False
        conn._client_identifier = None
        conn._client_info_modified = False
        conn._client_info = None
        conn._dbop_modified = False
        conn._dbop = None
        conn._module_modified = False
        conn._module = None

    cdef int _write_piggybacks(self, WriteBuffer buf) except -1:
        if self.conn_impl._current_schema_modified:
            self._write_current_schema_piggyback(buf)
        if self.conn_impl._num_cursors_to_close > 0 \
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


@cython.final
cdef class AuthMessage(Message):
    cdef:
        str encoded_password
        bytes password
        bytes newpassword
        str encoded_newpassword
        str encoded_jdwp_data
        str debug_jdwp
        str session_key
        str speedy_key
        str proxy_user
        uint8_t purity
        ssize_t user_bytes_len
        bytes user_bytes
        dict session_data
        uint32_t auth_mode
        uint32_t verifier_type

    cdef int _generate_verifier(self, bint verifier_11g) except -1:
        """
        Generate the multi-round verifier.
        """
        cdef bytes jdwp_data

        # create password hash
        verifier_data = bytes.fromhex(self.session_data['AUTH_VFR_DATA'])
        if verifier_11g:
            keylen = 24
            h = hashlib.sha1(self.password)
            h.update(verifier_data)
            password_hash = h.digest() + bytes(4)
        else:
            keylen = 32
            iterations = int(self.session_data['AUTH_PBKDF2_VGEN_COUNT'])
            salt = verifier_data + b'AUTH_PBKDF2_SPEEDY_KEY'
            password_key = get_derived_key(self.password, salt, 64,
                                           iterations)
            h = hashlib.new("sha512")
            h.update(password_key)
            h.update(verifier_data)
            password_hash = h.digest()[:32]

        # decrypt first half of session key
        encoded_server_key = bytes.fromhex(self.session_data['AUTH_SESSKEY'])
        session_key_part_a = decrypt_cbc(password_hash, encoded_server_key)

        # generate second half of session key
        session_key_part_b = secrets.token_bytes(32)
        encoded_client_key = encrypt_cbc(password_hash, session_key_part_b)
        self.session_key = encoded_client_key.hex().upper()[:64]

        # create session key from combo key
        mixing_salt = bytes.fromhex(self.session_data['AUTH_PBKDF2_CSK_SALT'])
        iterations = int(self.session_data['AUTH_PBKDF2_SDER_COUNT'])
        combo_key = session_key_part_b[:keylen] + session_key_part_a[:keylen]
        session_key = get_derived_key(combo_key.hex().upper().encode(),
                                      mixing_salt, keylen, iterations)

        # generate speedy key for 12c verifiers
        if not verifier_11g:
            salt = secrets.token_bytes(16)
            speedy_key = encrypt_cbc(session_key, salt + password_key)
            self.speedy_key = speedy_key[:80].hex().upper()

        # encrypt password
        salt = secrets.token_bytes(16)
        password_with_salt = salt + self.password
        encrypted_password = encrypt_cbc(session_key, password_with_salt)
        self.encoded_password = encrypted_password.hex().upper()

        # encrypt new password
        if self.newpassword is not None:
            newpassword_with_salt = salt + self.newpassword
            encrypted_newpassword = encrypt_cbc(session_key,
                                                newpassword_with_salt)
            self.encoded_newpassword = encrypted_newpassword.hex().upper()

        # check if debug_jdwp is set. if set, encode the data using the
        # combo session key with zeros padding
        if self.debug_jdwp is not None:
            jdwp_data = self.debug_jdwp.encode()
            encrypted_jdwp_data = encrypt_cbc(session_key, jdwp_data, zeros=True)
            # Add a "01" at the end of the hex encrypted data to indicate the
            # use of AES encryption
            self.encoded_jdwp_data = encrypted_jdwp_data.hex().upper() + "01"

    cdef tuple _get_version_tuple(self, ReadBuffer buf):
        """
        Return the 5-tuple for the database version. Note that the format
        changed with Oracle Database 18.
        """
        cdef uint32_t full_version_num
        full_version_num = int(self.session_data["AUTH_VERSION_NO"])
        if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_18_1_EXT_1:
            return ((full_version_num >> 24) & 0xFF,
                    (full_version_num >> 16) & 0xFF,
                    (full_version_num >> 12) & 0x0F,
                    (full_version_num >> 4) & 0xFF,
                    (full_version_num & 0x0F))
        else:
            return ((full_version_num >> 24) & 0xFF,
                    (full_version_num >> 20) & 0x0F,
                    (full_version_num >> 12) & 0x0F,
                    (full_version_num >> 8) & 0x0F,
                    (full_version_num & 0x0F))

    cdef int _initialize_hook(self) except -1:
        """
        Perform initialization.
        """
        self.function_code = TNS_FUNC_AUTH_PHASE_ONE
        self.session_data = {}
        self.user_bytes = self.conn_impl.username.encode()
        self.user_bytes_len = len(self.user_bytes)
        self.resend = True

    cdef int _process_return_parameters(self, ReadBuffer buf) except -1:
        cdef:
            uint16_t num_params, i
            uint32_t num_bytes
            str key, value
        buf.read_ub2(&num_params)
        for i in range(num_params):
            buf.skip_ub4()
            key = buf.read_str(TNS_CS_IMPLICIT)
            buf.read_ub4(&num_bytes)
            if num_bytes > 0:
                value = buf.read_str(TNS_CS_IMPLICIT)
            else:
                value = ""
            if key == "AUTH_VFR_DATA":
                buf.read_ub4(&self.verifier_type)
            else:
                buf.skip_ub4()                  # skip flags
            self.session_data[key] = value
        if self.function_code == TNS_FUNC_AUTH_PHASE_ONE:
            self.function_code = TNS_FUNC_AUTH_PHASE_TWO
        else:
            self.conn_impl._session_id = \
                    <uint32_t> int(self.session_data["AUTH_SESSION_ID"])
            self.conn_impl._serial_num = \
                    <uint32_t> int(self.session_data["AUTH_SERIAL_NUM"])
            self.conn_impl._server_version = \
                    "%d.%d.%d.%d.%d" % self._get_version_tuple(buf)

    cdef int _set_params(self, ConnectParamsImpl params,
                         Description description) except -1:
        """
        Sets the parameters to use for the AuthMessage. The user and auth mode
        are retained in order to avoid duplicating this effort for both trips
        to the server.
        """
        self.password = params._get_password()
        self.newpassword = params._get_new_password()

        # if drcp is used, use purity = NEW as the default purity for
        # standalone connections and purity = SELF for connections that belong
        # to a pool
        if description.purity == PURITY_DEFAULT \
                and self.conn_impl._drcp_enabled:
            if self.conn_impl._pool is None:
                self.purity = PURITY_NEW
            else:
                self.purity = PURITY_SELF
        else:
            self.purity = description.purity

        self.proxy_user = params.proxy_user
        self.debug_jdwp = params.debug_jdwp
        if params._new_password is None:
            self.auth_mode = TNS_AUTH_MODE_LOGON
        if params.mode & constants.AUTH_MODE_SYSDBA:
            self.auth_mode |= TNS_AUTH_MODE_SYSDBA
        if params.mode & constants.AUTH_MODE_SYSOPER:
            self.auth_mode |= TNS_AUTH_MODE_SYSOPER
        if params.mode & constants.AUTH_MODE_SYSASM:
            self.auth_mode |= TNS_AUTH_MODE_SYSASM
        if params.mode & constants.AUTH_MODE_SYSBKP:
            self.auth_mode |= TNS_AUTH_MODE_SYSBKP
        if params.mode & constants.AUTH_MODE_SYSDGD:
            self.auth_mode |= TNS_AUTH_MODE_SYSDGD
        if params.mode & constants.AUTH_MODE_SYSKMT:
            self.auth_mode |= TNS_AUTH_MODE_SYSKMT
        if params.mode & constants.AUTH_MODE_SYSRAC:
            self.auth_mode |= TNS_AUTH_MODE_SYSRAC

    cdef int _write_key_value(self, WriteBuffer buf, str key, str value,
                              uint32_t flags=0) except -1:
        cdef:
            bytes key_bytes = key.encode()
            bytes value_bytes = value.encode()
            uint32_t key_len = <uint32_t> len(key_bytes)
            uint32_t value_len = <uint32_t> len(value_bytes)
        buf.write_ub4(key_len)
        buf.write_bytes_chunked(key_bytes)
        buf.write_ub4(value_len)
        if value_len > 0:
            buf.write_bytes_chunked(value_bytes)
        buf.write_ub4(flags)

    cdef int _write_message(self, WriteBuffer buf) except -1:
        cdef:
            bint verifier_11g = False
            uint32_t num_pairs
        self._write_function_code(buf)
        buf.write_uint8(1)                  # pointer (authusr)
        buf.write_ub4(self.user_bytes_len)
        if self.function_code == TNS_FUNC_AUTH_PHASE_ONE:
            buf.write_ub4(self.auth_mode)   # authentication mode
            buf.write_uint8(1)              # pointer (authivl)
            buf.write_ub4(5)                # number of key/value pairs
            buf.write_uint8(0)              # pointer (authovl)
            buf.write_uint8(1)              # pointer (authovln)
            buf.write_bytes(self.user_bytes)
            self._write_key_value(buf, "AUTH_TERMINAL",
                                  _connect_constants.terminal_name)
            self._write_key_value(buf, "AUTH_PROGRAM_NM",
                                  _connect_constants.program_name)
            self._write_key_value(buf, "AUTH_MACHINE",
                                  _connect_constants.machine_name)
            self._write_key_value(buf, "AUTH_PID", _connect_constants.pid)
            self._write_key_value(buf, "AUTH_SID",
                                  _connect_constants.user_name)
        else:
            num_pairs = 5
            if self.newpassword is not None:
                num_pairs += 1
                self.auth_mode |= TNS_AUTH_MODE_CHANGE_PASSWORD
            if self.proxy_user is not None:
                num_pairs += 1
            if self.conn_impl._cclass is not None:
                num_pairs += 1
            if self.purity != 0:
                num_pairs += 1
            self.auth_mode |= TNS_AUTH_MODE_WITH_PASSWORD

            if self.verifier_type in (TNS_VERIFIER_TYPE_11G_1,
                                      TNS_VERIFIER_TYPE_11G_2):
                verifier_11g = True
            elif self.verifier_type != TNS_VERIFIER_TYPE_12C:
                errors._raise_err(errors.ERR_UNSUPPORTED_VERIFIER_TYPE,
                                  verifier_type=self.verifier_type)
            else:
                num_pairs += 1
            self._generate_verifier(verifier_11g)
            if self.encoded_jdwp_data is not None:
                num_pairs += 1
            buf.write_ub4(self.auth_mode)   # authentication mode
            buf.write_uint8(1)              # pointer (authivl)
            buf.write_ub4(num_pairs)        # number of key/value pairs
            buf.write_uint8(1)              # pointer (authovl)
            buf.write_uint8(1)              # pointer (authovln)
            buf.write_bytes(self.user_bytes)
            if self.proxy_user is not None:
                self._write_key_value(buf, "PROXY_CLIENT_NAME",
                                      self.proxy_user)
            self._write_key_value(buf, "AUTH_SESSKEY", self.session_key, 1)
            self._write_key_value(buf, "AUTH_PASSWORD", self.encoded_password)
            if self.newpassword is not None:
                self._write_key_value(buf, "AUTH_NEWPASSWORD",
                                      self.encoded_newpassword)
            if not verifier_11g:
                self._write_key_value(buf, "AUTH_PBKDF2_SPEEDY_KEY",
                                      self.speedy_key)
            self._write_key_value(buf, "SESSION_CLIENT_CHARSET", "873")
            driver_name = f"{constants.DRIVER_NAME} thn : {VERSION}"
            self._write_key_value(buf, "SESSION_CLIENT_DRIVER_NAME",
                                  driver_name)
            self._write_key_value(buf, "SESSION_CLIENT_VERSION",
                                  str(_connect_constants.full_version_num))
            if self.conn_impl._cclass is not None:
                self._write_key_value(buf, "AUTH_KPPL_CONN_CLASS",
                                      self.conn_impl._cclass)
            if self.purity != 0:
                self._write_key_value(buf, "AUTH_KPPL_PURITY",
                                      str(self.purity), 1)
            if self.encoded_jdwp_data is not None:
                self._write_key_value(buf, "AUTH_ORA_DEBUG_JDWP",
                                      self.encoded_jdwp_data)


@cython.final
cdef class CommitMessage(Message):

    cdef int _initialize_hook(self) except -1:
        """
        Perform initialization.
        """
        self.function_code = TNS_FUNC_COMMIT


@cython.final
cdef class ConnectMessage(Message):
    cdef:
        uint16_t connect_string_len
        bytes connect_string_bytes
        Description description
        str redirect_data
        str host
        int port

    cdef int process(self, ReadBuffer buf) except -1:
        cdef:
            uint16_t redirect_data_length, protocol_version, protocol_options
            const char_type *redirect_data
        if self.packet_type == TNS_PACKET_TYPE_REDIRECT:
            buf.read_uint16(&redirect_data_length)
            buf.receive_packet(&self.packet_type, &self.packet_flags)
            buf.skip_raw_bytes(2)           # skip data flags
            redirect_data = buf._get_raw(redirect_data_length)
            self.redirect_data = \
                    redirect_data[:redirect_data_length].decode()
        elif self.packet_type == TNS_PACKET_TYPE_ACCEPT:
            buf.read_uint16(&protocol_version)
            buf.read_uint16(&protocol_options)
            buf._caps._adjust_for_protocol(protocol_version, protocol_options)
        elif self.packet_type == TNS_PACKET_TYPE_REFUSE:
            response = self.error_info.message
            error_code = "unknown"
            error_code_int = 0
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
            uint16_t service_options = TNS_BASE_SERVICE_OPTIONS
            uint32_t connect_flags_1 = 0, connect_flags_2 = 0
        if buf._caps.supports_oob:
            service_options |= TNS_CAN_RECV_ATTENTION
            connect_flags_2 |= TNS_CHECK_OOB
        buf.start_request(TNS_PACKET_TYPE_CONNECT)
        buf.write_uint16(TNS_VERSION_DESIRED)
        buf.write_uint16(TNS_VERSION_MINIMUM)
        buf.write_uint16(service_options)
        buf.write_uint16(TNS_SDU)
        buf.write_uint16(TNS_TDU)
        buf.write_uint16(TNS_PROTOCOL_CHARACTERISTICS)
        buf.write_uint16(0)                 # line turnaround
        buf.write_uint16(1)                 # value of 1
        buf.write_uint16(self.connect_string_len)
        buf.write_uint16(74)                # offset to connect data
        buf.write_uint32(0)                 # max receivable data
        buf.write_uint16(TNS_CONNECT_FLAGS)
        buf.write_uint64(0)                 # obsolete
        buf.write_uint64(0)                 # obsolete
        buf.write_uint64(0)                 # obsolete
        buf.write_uint32(TNS_SDU)           # SDU (large)
        buf.write_uint32(TNS_TDU)           # TDU (large)
        buf.write_uint32(connect_flags_1)
        buf.write_uint32(connect_flags_2)
        if self.connect_string_len > TNS_MAX_CONNECT_DATA:
            buf.end_request()
            buf.start_request(TNS_PACKET_TYPE_DATA)
        buf.write_bytes(self.connect_string_bytes)
        buf.end_request()


@cython.final
cdef class DataTypesMessage(Message):

    cdef int _write_message(self, WriteBuffer buf) except -1:
        cdef:
            DataType* data_type
            int i

        # write character set and capabilities
        buf.write_uint8(TNS_MSG_TYPE_DATA_TYPES)
        buf.write_uint16(TNS_CHARSET_UTF8, BYTE_ORDER_LSB)
        buf.write_uint16(TNS_CHARSET_UTF8, BYTE_ORDER_LSB)
        buf.write_ub4(len(buf._caps.compile_caps))
        buf.write_bytes(bytes(buf._caps.compile_caps))
        buf.write_uint8(len(buf._caps.runtime_caps))
        buf.write_bytes(bytes(buf._caps.runtime_caps))

        # write data types
        i = 0
        while True:
            data_type = &DATA_TYPES[i]
            if data_type.data_type == 0:
                break
            i += 1
            buf.write_uint16(data_type.data_type)
            buf.write_uint16(data_type.conv_data_type)
            buf.write_uint16(data_type.representation)
            buf.write_uint16(0)
        buf.write_uint16(0)

    cdef int process(self, ReadBuffer buf) except -1:
        pass


@cython.final
cdef class ExecuteMessage(MessageWithData):

    cdef int _postprocess(self) except -1:
        """
        Runs after the database response has been processed. If the statement
        executed requires define and is not a REF cursor (which would already
        have performed the define during its execute), then mark the message as
        needing to be resent. If this is after the second time the message has
        been sent, mark the statement as no longer needing a define (since this
        only needs to happen once).
        """
        MessageWithData._postprocess(self)
        cdef Statement stmt = self.cursor_impl._statement
        if stmt._requires_define and stmt._sql is not None:
            if self.resend:
                stmt._requires_define = False
            else:
                stmt._requires_full_execute = True
                self.resend = True

    cdef int _write_execute_message(self, WriteBuffer buf) except -1:
        """
        Write the message for a full execute.
        """
        cdef:
            uint32_t options, dml_options = 0, num_params = 0, num_iters = 1
            Statement stmt = self.cursor_impl._statement
            ThinCursorImpl cursor_impl = self.cursor_impl
            list params = stmt._bind_info_list

        # determine the options to use for the execute
        options = 0
        if not stmt._requires_define and not self.parse_only \
                and params is not None:
            num_params = <uint32_t> len(params)
        if stmt._requires_define:
            options |= TNS_EXEC_OPTION_DEFINE
        elif not self.parse_only and stmt._sql is not None:
            dml_options = TNS_EXEC_OPTION_IMPLICIT_RESULTSET
            options |= TNS_EXEC_OPTION_EXECUTE
        if stmt._cursor_id == 0 or stmt._is_ddl:
            options |= TNS_EXEC_OPTION_PARSE
        if stmt._is_query:
            if self.parse_only:
                options |= TNS_EXEC_OPTION_DESCRIBE
            else:
                if self.cursor_impl.prefetchrows > 0:
                    options |= TNS_EXEC_OPTION_FETCH
                if stmt._cursor_id == 0 or stmt._requires_define:
                    num_iters = self.cursor_impl.prefetchrows
                    self.cursor_impl._fetch_array_size = num_iters
                else:
                    num_iters = self.cursor_impl._fetch_array_size
        if not stmt._is_plsql:
            options |= TNS_EXEC_OPTION_NOT_PLSQL
        elif num_params > 0:
            options |= TNS_EXEC_OPTION_PLSQL_BIND
        if num_params > 0:
            options |= TNS_EXEC_OPTION_BIND
        if self.batcherrors:
            options |= TNS_EXEC_OPTION_BATCH_ERRORS
        if self.arraydmlrowcounts:
            dml_options = TNS_EXEC_OPTION_DML_ROWCOUNTS
        if self.conn_impl.autocommit:
            options |= TNS_EXEC_OPTION_COMMIT

        # write piggybacks, if needed
        self._write_piggybacks(buf)

        # write body of message
        self._write_function_code(buf)
        buf.write_ub4(options)              # execute options
        buf.write_ub4(stmt._cursor_id)      # cursor id
        if stmt._cursor_id == 0 or stmt._is_ddl:
            buf.write_uint8(1)              # pointer (cursor id)
            buf.write_ub4(stmt._sql_length)
        else:
            buf.write_uint8(0)              # pointer (cursor id)
            buf.write_ub4(0)
        buf.write_uint8(1)                  # pointer (vector)
        buf.write_ub4(13)                   # al8i4 array length
        buf.write_uint8(0)                  # pointer (al8o4)
        buf.write_uint8(0)                  # pointer (al8o4l)
        buf.write_ub4(0)                    # prefetch buffer size
        buf.write_ub4(num_iters)            # prefetch number of rows
        buf.write_ub4(TNS_MAX_LONG_LENGTH)  # maximum long size
        if num_params == 0:
            buf.write_uint8(0)              # pointer (binds)
            buf.write_ub4(0)                # number of binds
        else:
            buf.write_uint8(1)              # pointer (binds)
            buf.write_ub4(num_params)       # number of binds
        buf.write_uint8(0)                  # pointer (al8app)
        buf.write_uint8(0)                  # pointer (al8txn)
        buf.write_uint8(0)                  # pointer (al8txl)
        buf.write_uint8(0)                  # pointer (al8kv)
        buf.write_uint8(0)                  # pointer (al8kvl)
        if stmt._requires_define:
            buf.write_uint8(1)              # pointer (al8doac)
            buf.write_ub4(len(self.cursor_impl.fetch_vars))
                                            # number of defines
        else:
            buf.write_uint8(0)
            buf.write_ub4(0)
        buf.write_ub4(0)                    # registration id
        buf.write_uint8(0)                  # pointer (al8objlist)
        buf.write_uint8(1)                  # pointer (al8objlen)
        buf.write_uint8(0)                  # pointer (al8blv)
        buf.write_ub4(0)                    # al8blvl
        buf.write_uint8(0)                  # pointer (al8dnam)
        buf.write_ub4(0)                    # al8dnaml
        buf.write_ub4(0)                    # al8regid_msb
        if self.arraydmlrowcounts:
            buf.write_uint8(1)              # pointer (al8pidmlrc)
            buf.write_ub4(self.num_execs)   # al8pidmlrcbl
            buf.write_uint8(1)              # pointer (al8pidmlrcl)
        else:
            buf.write_uint8(0)              # pointer (al8pidmlrc)
            buf.write_ub4(0)                # al8pidmlrcbl
            buf.write_uint8(0)              # pointer (al8pidmlrcl)
        if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_12_2:
            buf.write_uint8(0)                  # pointer (al8sqlsig)
            buf.write_ub4(0)                    # SQL signature length
            buf.write_uint8(0)                  # pointer (SQL ID)
            buf.write_ub4(0)                    # allocated size of SQL ID
            buf.write_uint8(0)                  # pointer (length of SQL ID)
            if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_12_2_EXT1:
                buf.write_uint8(0)              # pointer (chunk ids)
                buf.write_ub4(0)                # number of chunk ids
        if stmt._cursor_id == 0 or stmt._is_ddl:
            if stmt._sql_bytes is None:
                errors._raise_err(errors.ERR_INVALID_REF_CURSOR)
            buf.write_bytes(stmt._sql_bytes)
            buf.write_ub4(1)                # al8i4[0] parse
        else:
            buf.write_ub4(0)                # al8i4[0] parse
        if stmt._is_query:
            if stmt._cursor_id == 0:
                buf.write_ub4(0)            # al8i4[1] execution count
            else:
                buf.write_ub4(num_iters)
        else:
            buf.write_ub4(self.num_execs)   # al8i4[1] execution count
        buf.write_ub4(0)                    # al8i4[2]
        buf.write_ub4(0)                    # al8i4[3]
        buf.write_ub4(0)                    # al8i4[4]
        buf.write_ub4(0)                    # al8i4[5] SCN (part 1)
        buf.write_ub4(0)                    # al8i4[6] SCN (part 2)
        buf.write_ub4(stmt._is_query)       # al8i4[7] is query
        buf.write_ub4(0)                    # al8i4[8]
        buf.write_ub4(dml_options)          # al8i4[9] DML row counts/implicit
        buf.write_ub4(0)                    # al8i4[10]
        buf.write_ub4(0)                    # al8i4[11]
        buf.write_ub4(0)                    # al8i4[12]
        if stmt._requires_define:
            self._write_column_metadata(buf, self.cursor_impl.fetch_var_impls)
        elif num_params > 0:
            self._write_bind_params(buf, params)

    cdef int _write_reexecute_message(self, WriteBuffer buf) except -1:
        """
        Write the message for a re-execute.
        """
        cdef:
            uint32_t i, exec_flags_1 = 0, exec_flags_2 = 0, num_iters
            Statement stmt = self.cursor_impl._statement
            list params = stmt._bind_info_list
            BindInfo info

        if params:
            if not stmt._is_query:
                self.out_var_impls = [info._bind_var_impl \
                                      for info in params \
                                      if info.bind_dir != TNS_BIND_DIR_INPUT]
            params = [info for info in params \
                      if info.bind_dir != TNS_BIND_DIR_OUTPUT \
                      and not info._is_return_bind]
        if self.function_code == TNS_FUNC_REEXECUTE_AND_FETCH:
            exec_flags_1 |= TNS_EXEC_OPTION_EXECUTE
            num_iters = self.cursor_impl.prefetchrows
            self.cursor_impl._fetch_array_size = num_iters
        else:
            if self.conn_impl.autocommit:
                exec_flags_2 |= TNS_EXEC_OPTION_COMMIT_REEXECUTE
            num_iters = self.num_execs

        self._write_piggybacks(buf)
        self._write_function_code(buf)
        buf.write_ub4(stmt._cursor_id)
        buf.write_ub4(num_iters)
        buf.write_ub4(exec_flags_1)
        buf.write_ub4(exec_flags_2)
        if params:
            for i in range(self.num_execs):
                buf.write_uint8(TNS_MSG_TYPE_ROW_DATA)
                self._write_bind_params_row(buf, params, i)

    cdef int _write_message(self, WriteBuffer buf) except -1:
        """
        Write the execute message to the buffer. Two types of execute messages
        are possible: one for a full execute and the second, simpler message,
        for when an existing cursor is being re-executed.
        """
        cdef:
            Statement stmt = self.cursor_impl._statement
        if stmt._cursor_id != 0 and not stmt._requires_full_execute \
                and not stmt._is_ddl:
            if stmt._is_query and not stmt._requires_define \
                    and self.cursor_impl.prefetchrows > 0:
                self.function_code = TNS_FUNC_REEXECUTE_AND_FETCH
            else:
                self.function_code = TNS_FUNC_REEXECUTE
            self._write_reexecute_message(buf)
        else:
            self.function_code = TNS_FUNC_EXECUTE
            self._write_execute_message(buf)


@cython.final
cdef class FetchMessage(MessageWithData):

    cdef int _initialize_hook(self) except -1:
        """
        Perform initialization.
        """
        self.function_code = TNS_FUNC_FETCH

    cdef int _write_message(self, WriteBuffer buf) except -1:
        self.cursor_impl._fetch_array_size = self.cursor_impl.arraysize
        self._write_function_code(buf)
        buf.write_ub4(self.cursor_impl._statement._cursor_id)
        buf.write_ub4(self.cursor_impl._fetch_array_size)


@cython.final
cdef class LobOpMessage(Message):
    cdef:
        uint32_t operation
        ThinLobImpl source_lob_impl
        ThinLobImpl dest_lob_impl
        uint64_t source_offset
        uint64_t dest_offset
        int64_t amount
        bint send_amount
        bint bool_flag
        object data

    cdef bint _has_more_data(self, ReadBuffer buf):
        return not self.processed_error

    cdef int _initialize_hook(self) except -1:
        """
        Perform initialization.
        """
        self.function_code = TNS_FUNC_LOB_OP

    cdef int _process_message(self, ReadBuffer buf,
                              uint8_t message_type) except -1:
        cdef:
            const char_type *ptr
            ssize_t num_bytes
            str encoding
        if message_type == TNS_MSG_TYPE_LOB_DATA:
            buf.read_raw_bytes_chunked(&ptr, &num_bytes)
            if self.source_lob_impl.dbtype._ora_type_num == TNS_DATA_TYPE_BLOB:
                self.data = ptr[:num_bytes]
            else:
                encoding = self.source_lob_impl._get_encoding()
                self.data = ptr[:num_bytes].decode(encoding)
        else:
            Message._process_message(self, buf, message_type)

    cdef int _process_return_parameters(self, ReadBuffer buf) except -1:
        cdef:
            cdef const char_type *ptr
            ssize_t num_bytes
            uint16_t temp16
        if self.source_lob_impl is not None:
            num_bytes = len(self.source_lob_impl._locator)
            ptr = buf.read_raw_bytes(num_bytes)
            self.source_lob_impl._locator = ptr[:num_bytes]
        if self.dest_lob_impl is not None:
            num_bytes = len(self.dest_lob_impl._locator)
            ptr = buf.read_raw_bytes(num_bytes)
            self.dest_lob_impl._locator = ptr[:num_bytes]
        if self.operation == TNS_LOB_OP_CREATE_TEMP:
            buf.skip_ub2()                  # skip character set
        if self.send_amount:
            buf.read_sb8(&self.amount)
        if self.operation == TNS_LOB_OP_CREATE_TEMP \
                or self.operation == TNS_LOB_OP_IS_OPEN:
            buf.read_ub2(&temp16)           # flag
            self.bool_flag = temp16 > 0

    cdef int _write_message(self, WriteBuffer buf) except -1:
        cdef int i
        self._write_function_code(buf)
        if self.source_lob_impl is None:
            buf.write_uint8(0)              # source pointer
            buf.write_ub4(0)                # source length
        else:
            buf.write_uint8(1)              # source pointer
            buf.write_ub4(len(self.source_lob_impl._locator))
        if self.dest_lob_impl is None:
            buf.write_uint8(0)              # dest pointer
            buf.write_ub4(0)                # dest length
        else:
            buf.write_uint8(1)              # dest pointer
            buf.write_ub4(len(self.dest_lob_impl._locator))
        buf.write_ub4(0)                    # short source offset
        buf.write_ub4(0)                    # short dest offset
        if self.operation == TNS_LOB_OP_CREATE_TEMP:
            buf.write_uint8(1)              # pointer (character set)
        else:
            buf.write_uint8(0)              # pointer (character set)
        buf.write_uint8(0)                  # pointer (short amount)
        if self.operation == TNS_LOB_OP_CREATE_TEMP \
                or self.operation == TNS_LOB_OP_IS_OPEN:
            buf.write_uint8(1)              # pointer (NULL LOB)
        else:
            buf.write_uint8(0)              # pointer (NULL LOB)
        buf.write_ub4(self.operation)
        buf.write_uint8(0)                  # pointer (SCN array)
        buf.write_uint8(0)                  # SCN array length
        buf.write_ub8(self.source_offset)
        buf.write_ub8(self.dest_offset)
        if self.send_amount:
            buf.write_uint8(1)              # pointer (amount)
        else:
            buf.write_uint8(0)              # pointer (amount)
        for i in range(3):                  # array LOB (not used)
            buf.write_uint16(0)
        if self.source_lob_impl is not None:
            buf.write_bytes(self.source_lob_impl._locator)
        if self.dest_lob_impl is not None:
            buf.write_bytes(self.dest_lob_impl._locator)
        if self.operation == TNS_LOB_OP_CREATE_TEMP:
            if self.source_lob_impl.dbtype._csfrm == TNS_CS_NCHAR:
                buf._caps._check_ncharset_id()
                buf.write_ub4(TNS_CHARSET_UTF16)
            else:
                buf.write_ub4(TNS_CHARSET_UTF8)
        if self.data is not None:
            buf.write_uint8(TNS_MSG_TYPE_LOB_DATA)
            buf.write_bytes_chunked(self.data)
        if self.send_amount:
            buf.write_ub8(self.amount)      # LOB amount


@cython.final
cdef class LogoffMessage(Message):

    cdef int _initialize_hook(self) except -1:
        """
        Perform initialization.
        """
        self.function_code = TNS_FUNC_LOGOFF


@cython.final
cdef class NetworkServicesMessage(Message):

    cdef int _write_message(self, WriteBuffer buf) except -1:
        cdef:
            uint16_t packet_length
            NetworkService service

        # calculate length of packet
        packet_length = TNS_NETWORK_HEADER_SIZE
        for service in TNS_NETWORK_SERVICES:
            packet_length += service.get_data_size()

        # write header
        buf.write_uint32(TNS_NETWORK_MAGIC)
        buf.write_uint16(packet_length)
        buf.write_uint32(TNS_NETWORK_VERSION)
        buf.write_uint16(<uint16_t> len(TNS_NETWORK_SERVICES))
        buf.write_uint8(0)                  # flags

        # write service data
        for service in TNS_NETWORK_SERVICES:
            service.write_data(buf)

    cdef int process(self, ReadBuffer buf) except -1:
        cdef:
            uint16_t num_services, num_subpackets, i, j, data_length
            uint32_t temp32
        buf.skip_raw_bytes(2)               # data flags
        buf.read_uint32(&temp32)            # network magic num
        if temp32 != TNS_NETWORK_MAGIC:
            errors._raise_err(errors.ERR_UNEXPECTED_DATA, data=hex(temp32))
        buf.skip_raw_bytes(2)               # length of packet
        buf.skip_raw_bytes(4)               # version
        buf.read_uint16(&num_services)
        buf.skip_raw_bytes(1)               # error flags
        for i in range(num_services):
            buf.skip_raw_bytes(2)           # service num
            buf.read_uint16(&num_subpackets)
            buf.read_uint32(&temp32)        # error num
            if temp32 != 0:
                errors._raise_err(errors.ERR_LISTENER_REFUSED_CONNECTION,
                                  error_code=temp32)
            for j in range(num_subpackets):
                buf.read_uint16(&data_length)
                buf.skip_raw_bytes(2)       # data type
                buf.skip_raw_bytes(data_length)


@cython.final
cdef class PingMessage(Message):

    cdef int _initialize_hook(self) except -1:
        """
        Perform initialization.
        """
        self.function_code = TNS_FUNC_PING


@cython.final
cdef class ProtocolMessage(Message):

    cdef int _write_message(self, WriteBuffer buf) except -1:
        buf.write_uint8(TNS_MSG_TYPE_PROTOCOL)
        buf.write_uint8(6)                  # protocol version (8.1 and higher)
        buf.write_uint8(0)                  # "array" terminator
        buf.write_str(constants.DRIVER_NAME)
        buf.write_uint8(0)                  # NULL terminator

    cdef int _process_message(self, ReadBuffer buf,
                              uint8_t message_type) except -1:
        cdef:
            uint16_t num_elem, fdo_length
            bytearray server_compile_caps
            bytearray server_runtime_caps
            Capabilities caps = buf._caps
            const char_type *fdo
            ssize_t ix
            uint8_t c
        if message_type == TNS_MSG_TYPE_PROTOCOL:
            buf.skip_raw_bytes(2)           # skip protocol array
            while True:                     # skip server banner
                buf.read_ub1(&c)
                if c == 0:
                    break
            buf.read_uint16(&caps.charset_id, BYTE_ORDER_LSB)
            buf._caps.char_conversion = caps.charset_id != TNS_CHARSET_UTF8
            buf.skip_ub1()                  # skip server flags
            buf.read_uint16(&num_elem, BYTE_ORDER_LSB)
            if num_elem > 0:                # skip elements
                buf.skip_raw_bytes(num_elem * 5)
            buf.read_uint16(&fdo_length)
            fdo = buf.read_raw_bytes(fdo_length)
            ix = 6 + fdo[5] + fdo[6]
            caps.ncharset_id = (fdo[ix + 3] << 8) + fdo[ix + 4]
            server_compile_caps = bytearray(buf.read_bytes())
            server_runtime_caps = bytearray(buf.read_bytes())
            if not server_compile_caps[TNS_CCAP_LOGON_TYPES] & TNS_CCAP_O7LOGON:
                errors._raise_err(errors.ERR_SERVER_LOGON_TYPE_NOT_SUPPORTED)
            buf._caps._adjust_for_server_compile_caps(server_compile_caps)
            buf._caps._adjust_for_server_runtime_caps(server_runtime_caps)
        else:
            Message._process_message(self, buf, message_type)


@cython.final
cdef class RollbackMessage(Message):

    cdef int _initialize_hook(self) except -1:
        """
        Perform initialization.
        """
        self.function_code = TNS_FUNC_ROLLBACK
