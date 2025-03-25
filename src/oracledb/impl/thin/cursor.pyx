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
# cursor.pyx
#
# Cython file defining the thin Cursor implementation class (embedded in
# thin_impl.pyx).
#------------------------------------------------------------------------------

cdef class BaseThinCursorImpl(BaseCursorImpl):

    cdef:
        BaseThinConnImpl _conn_impl
        Statement _statement
        list _batcherrors
        list _dmlrowcounts
        list _implicit_resultsets
        uint64_t _buffer_min_row
        uint64_t _buffer_max_row
        uint32_t _num_columns
        uint32_t _last_row_index
        Rowid _lastrowid

    def __cinit__(self, conn_impl):
        self._conn_impl = conn_impl

    cdef int _close(self, bint in_del) except -1:
        if self._statement is not None:
            self._conn_impl._return_statement(self._statement)
            self._statement = None

    cdef MessageWithData _create_message(self, type typ, object cursor):
        """
        Creates a message object that is used to send a request to the database
        and receive back its response.
        """
        cdef MessageWithData message
        message = typ.__new__(typ, cursor, self)
        message._initialize(self._conn_impl)
        message.cursor = cursor
        message.cursor_impl = self
        return message

    cdef ExecuteMessage _create_execute_message(self, object cursor):
        """
        Creates and returns the message used to execute a statement once.
        """
        cdef ExecuteMessage message
        message = self._create_message(ExecuteMessage, cursor)
        message.num_execs = 1
        if self.scrollable:
            message.fetch_orientation = TNS_FETCH_ORIENTATION_CURRENT
            message.fetch_pos = 1
        return message

    cdef ExecuteMessage _create_scroll_message(self, object cursor,
                                               object mode, int32_t offset):
        """
        Creates a message object that is used to send a scroll request to the
        database and receive back its response.
        """
        cdef:
            uint64_t desired_row = 0
            uint32_t orientation = 0
            ExecuteMessage message

        # check mode and calculate desired row
        if mode == "relative":
            if <int64_t> (self.rowcount + offset) < 1:
                errors._raise_err(errors.ERR_SCROLL_OUT_OF_RESULT_SET)
            orientation = TNS_FETCH_ORIENTATION_RELATIVE
            desired_row = self.rowcount + offset
        elif mode == "absolute":
            orientation = TNS_FETCH_ORIENTATION_ABSOLUTE
            desired_row = <uint64_t> offset
        elif mode == "first":
            orientation = TNS_FETCH_ORIENTATION_FIRST
            desired_row = 1
        elif mode == "last":
            orientation = TNS_FETCH_ORIENTATION_LAST
        else:
            errors._raise_err(errors.ERR_WRONG_SCROLL_MODE)

        # determine if the server needs to be contacted at all
        # for "last", the server is always contacted
        if orientation != TNS_FETCH_ORIENTATION_LAST \
                and desired_row >= self._buffer_min_row \
                and desired_row < self._buffer_max_row:
            self._buffer_index = \
                    <uint32_t> (desired_row - self._buffer_min_row)
            self._buffer_rowcount = self._buffer_max_row - desired_row
            self.rowcount = desired_row - 1
            return None

        # build message
        message = self._create_message(ExecuteMessage, cursor)
        message.scroll_operation = self._more_rows_to_fetch
        message.fetch_orientation = orientation
        message.fetch_pos = <uint32_t> desired_row
        return message

    cdef BaseVarImpl _create_var_impl(self, object conn):
        cdef ThinVarImpl var_impl
        var_impl = ThinVarImpl.__new__(ThinVarImpl)
        var_impl._conn_impl = self._conn_impl
        return var_impl

    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef BaseVarImpl _create_fetch_var(self, object conn, object cursor,
                                       object type_handler,
                                       bint uses_metadata, ssize_t pos,
                                       OracleMetadata metadata):
        """
        Internal method that creates a fetch variable. A check is made after
        the variable is created to determine if a conversion is required and
        therefore a define must be performed.
        """
        cdef:
            ThinDbObjectTypeImpl typ_impl
            ThinVarImpl var_impl
        var_impl = <ThinVarImpl> BaseCursorImpl._create_fetch_var(
            self, conn, cursor, type_handler, uses_metadata, pos, metadata
        )
        if metadata.objtype is not None:
            typ_impl = metadata.objtype
            if typ_impl.is_xml_type:
                var_impl.outconverter = \
                        lambda v: v if isinstance(v, str) else v.read()

    cdef BaseConnImpl _get_conn_impl(self):
        """
        Internal method used to return the connection implementation associated
        with the cursor implementation.
        """
        return self._conn_impl

    cdef bint _is_plsql(self):
        return self._statement._is_plsql

    cdef int _prepare(self, str statement, str tag,
                      bint cache_statement) except -1:
        """
        Internal method for preparing a statement for execution.
        """
        BaseCursorImpl._prepare(self, statement, tag, cache_statement)
        if self._statement is not None:
            self._conn_impl._return_statement(self._statement)
            self._statement = None
        self._statement = self._conn_impl._get_statement(statement.strip(),
                                                         cache_statement)
        self.fetch_metadata = self._statement._fetch_metadata
        self.fetch_vars = self._statement._fetch_vars
        self.fetch_var_impls = self._statement._fetch_var_impls
        self._num_columns = self._statement._num_columns

    cdef int _preprocess_execute(self, object conn) except -1:
        cdef BindInfo bind_info
        if self.bind_vars is not None:
            self._perform_binds(conn, 0)
        for bind_info in self._statement._bind_info_list:
            if bind_info._bind_var_impl is None:
                errors._raise_err(errors.ERR_MISSING_BIND_VALUE,
                                  name=bind_info._bind_name)

    cdef int _post_process_scroll(self, ExecuteMessage message) except -1:
        """
        Called after a scroll operation has completed successfully. The row
        count and buffer row counts and indices are updated as required.
        """
        if self._buffer_rowcount == 0:
            if message.fetch_orientation not in (
                TNS_FETCH_ORIENTATION_FIRST,
                TNS_FETCH_ORIENTATION_LAST
            ):
                errors._raise_err(errors.ERR_SCROLL_OUT_OF_RESULT_SET)
            self.rowcount = 0
            self._more_rows_to_fetch = False
            self._buffer_index = 0
            self._buffer_min_row = 0
            self._buffer_max_row = 0
        else:
            self.rowcount = message.error_info.rowcount - self._buffer_rowcount
            self._buffer_min_row = self.rowcount + 1
            self._buffer_max_row = self._buffer_min_row + self._buffer_rowcount
            self._buffer_index = 0

    cdef int _set_fetch_array_size(self, uint32_t value):
        """
        Internal method for setting the fetch array size. This also ensures
        that any fetch variables have enough space to store the fetched rows
        that are returned.
        """
        cdef:
            ThinVarImpl var_impl
            uint32_t num_vals
        self._fetch_array_size = value
        if self.fetch_var_impls is not None:
            for var_impl in self.fetch_var_impls:
                if var_impl.num_elements >= self._fetch_array_size:
                    continue
                num_vals = (self._fetch_array_size - var_impl.num_elements)
                var_impl.num_elements = self._fetch_array_size
                var_impl._values.extend([None] * num_vals)

    def get_array_dml_row_counts(self):
        if self._dmlrowcounts is None:
            errors._raise_err(errors.ERR_ARRAY_DML_ROW_COUNTS_NOT_ENABLED)
        return self._dmlrowcounts

    def get_batch_errors(self):
        return self._batcherrors

    def get_bind_names(self):
        return list(self._statement._bind_info_dict.keys())

    def get_implicit_results(self, connection):
        if self._implicit_resultsets is None:
            errors._raise_err(errors.ERR_NO_STATEMENT_EXECUTED)
        return self._implicit_resultsets

    def get_lastrowid(self):
        if self.rowcount > 0:
            return _encode_rowid(&self._lastrowid)

    def is_query(self, connection):
        return self.fetch_vars is not None



cdef class ThinCursorImpl(BaseThinCursorImpl):

    cdef int _fetch_rows(self, object cursor) except -1:
        """
        Internal method used for fetching rows from the database.
        """
        cdef:
            Protocol protocol = <Protocol> self._conn_impl._protocol
            MessageWithData message
        if self._statement._sql is None:
            message = self._create_message(ExecuteMessage, cursor)
        else:
            message = self._create_message(FetchMessage, cursor)
        protocol._process_single_message(message)
        self._buffer_min_row = self.rowcount + 1
        self._buffer_max_row = self._buffer_min_row + self._buffer_rowcount

    def execute(self, cursor):
        cdef:
            Protocol protocol = <Protocol> self._conn_impl._protocol
            object conn = cursor.connection
            MessageWithData message
        self._preprocess_execute(conn)
        message = self._create_execute_message(cursor)
        protocol._process_single_message(message)
        self.warning = message.warning
        if self._statement._is_query:
            if message.type_cache is not None:
                message.type_cache.populate_partial_types(conn)

    def executemany(self, cursor, num_execs, batcherrors, arraydmlrowcounts):
        cdef:
            Protocol protocol = <Protocol> self._conn_impl._protocol
            MessageWithData messsage
            Statement stmt
            uint32_t i

        # set up message to send
        self._preprocess_execute(cursor.connection)
        message = self._create_message(ExecuteMessage, cursor)
        message.num_execs = num_execs
        message.batcherrors = batcherrors
        message.arraydmlrowcounts = arraydmlrowcounts
        stmt = self._statement

        # only DML statements may use the batch errors or array DML row counts
        # flags
        if not stmt._is_dml and (batcherrors or arraydmlrowcounts):
            errors._raise_err(errors.ERR_EXECUTE_MODE_ONLY_FOR_DML)

        # if a PL/SQL statement requires a full execute, perform only a single
        # iteration in order to allow the determination of input/output binds
        # to be completed; after that, an execution of the remaining iterations
        # can be performed (but only if the cursor remains intact)
        if stmt.requires_single_execute():
            message.num_execs = 1
            while num_execs > 0:
                num_execs -= 1
                protocol._process_single_message(message)
                message.offset += 1
                if stmt._cursor_id != 0:
                    break
        if num_execs > 0:
            message.num_execs = num_execs
            protocol._process_single_message(message)
        self.warning = message.warning

    def parse(self, cursor):
        cdef:
            Protocol protocol = <Protocol> self._conn_impl._protocol
            MessageWithData message
        message = self._create_message(ExecuteMessage, cursor)
        message.parse_only = True
        protocol._process_single_message(message)

    def scroll(self, object cursor, int32_t offset, object mode):
        cdef:
            Protocol protocol = <Protocol> self._conn_impl._protocol
            ExecuteMessage message
        message = self._create_scroll_message(cursor, mode, offset)
        if message is not None:
            protocol._process_single_message(message)
            self._post_process_scroll(message)


cdef class AsyncThinCursorImpl(BaseThinCursorImpl):

    def _build_json_converter_fn(self):
        """
        Internal method for building a JSON converter function with asyncio.
        """
        async def converter(value):
            if isinstance(value, PY_TYPE_ASYNC_LOB):
                value = await value.read()
            if isinstance(value, bytes):
                value = value.decode()
            if value:
                return json.loads(value)
        return converter

    async def _fetch_rows_async(self, object cursor):
        """
        Internal method used for fetching rows from the database.
        """
        cdef MessageWithData message
        if self._statement._sql is None:
            message = self._create_message(ExecuteMessage, cursor)
        else:
            message = self._create_message(FetchMessage, cursor)
        await self._conn_impl._protocol._process_single_message(message)
        self._buffer_min_row = self.rowcount + 1

    async def _preprocess_execute_async(self, object conn):
        """
        Performs the necessary steps required before actually executing the
        statement associated with the cursor.
        """
        cdef:
            ThinVarImpl var_impl
            BindInfo bind_info
            ssize_t idx
        self._preprocess_execute(conn)
        for bind_info in self._statement._bind_info_list:
            var_impl = bind_info._bind_var_impl
            if var_impl._coroutine_indexes is not None:
                for idx in var_impl._coroutine_indexes:
                    var_impl._values[idx] = await var_impl._values[idx]
                var_impl._coroutine_indexes = None

    async def execute(self, cursor):
        cdef:
            object conn = cursor.connection
            BaseAsyncProtocol protocol
            MessageWithData message
        protocol = <BaseAsyncProtocol> self._conn_impl._protocol
        await self._preprocess_execute_async(conn)
        message = self._create_execute_message(cursor)
        await protocol._process_single_message(message)
        self.warning = message.warning
        if self._statement._is_query:
            if message.type_cache is not None:
                await message.type_cache.populate_partial_types(conn)

    async def executemany(self, cursor, num_execs, batcherrors,
                          arraydmlrowcounts):
        cdef:
            BaseAsyncProtocol protocol
            MessageWithData messsage
            Statement stmt
            uint32_t i

        # set up message to send
        protocol = <BaseAsyncProtocol> self._conn_impl._protocol
        await self._preprocess_execute_async(cursor.connection)
        message = self._create_message(ExecuteMessage, cursor)
        message.num_execs = num_execs
        message.batcherrors = batcherrors
        message.arraydmlrowcounts = arraydmlrowcounts
        stmt = self._statement

        # only DML statements may use the batch errors or array DML row counts
        # flags
        if not stmt._is_dml and (batcherrors or arraydmlrowcounts):
            errors._raise_err(errors.ERR_EXECUTE_MODE_ONLY_FOR_DML)

        # if a PL/SQL statement requires a full execute, perform only a single
        # iteration in order to allow the determination of input/output binds
        # to be completed; after that, an execution of the remaining iterations
        # can be performed (but only if the cursor remains intact)
        if stmt.requires_single_execute():
            message.num_execs = 1
            while num_execs > 0:
                num_execs -= 1
                await protocol._process_single_message(message)
                message.offset += 1
                if stmt._cursor_id != 0:
                    break
        if num_execs > 0:
            message.num_execs = num_execs
            await protocol._process_single_message(message)
        self.warning = message.warning

    async def fetch_df_all(self, cursor):
        """
        Internal method used for fetching all data as OracleDataFrame
        """
        while self._more_rows_to_fetch:
            await self._fetch_rows_async(cursor)
        return self._finish_building_arrow_arrays()

    async def fetch_df_batches(self, cursor, int batch_size):
        """
        Internal method used for fetching next batch as OracleDataFrame.
        """
        # Return the prefetched batch
        yield self._finish_building_arrow_arrays()

        while self._more_rows_to_fetch:
            self._create_arrow_arrays()
            await self._fetch_rows_async(cursor)
            if self._buffer_rowcount > 0:
                yield self._finish_building_arrow_arrays()

    async def fetch_next_row(self, cursor):
        """
        Internal method used for fetching the next row from a cursor.
        """
        if self._buffer_rowcount == 0 and self._more_rows_to_fetch:
            await self._fetch_rows_async(cursor)
        if self._buffer_rowcount > 0:
            return self._create_row()

    async def parse(self, cursor):
        cdef:
            BaseAsyncProtocol protocol
            MessageWithData message
        protocol = <BaseAsyncProtocol> self._conn_impl._protocol
        message = self._create_message(ExecuteMessage, cursor)
        message.parse_only = True
        await protocol._process_single_message(message)

    async def scroll(self, object cursor, int32_t offset, object mode):
        cdef:
            BaseAsyncProtocol protocol
            MessageWithData message
        protocol = <BaseAsyncProtocol> self._conn_impl._protocol
        message = self._create_scroll_message(cursor, mode, offset)
        if message is not None:
            await protocol._process_single_message(message)
            self._post_process_scroll(message)
