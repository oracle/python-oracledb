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
# execute.pyx
#
# Cython file defining the messages that are sent to the database and the
# responses that are received by the client for executing a SQL statement
# (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

@cython.final
cdef class ExecuteMessage(MessageWithData):
    cdef:
        uint32_t fetch_orientation
        uint32_t fetch_pos
        bint scroll_operation

    cdef int _write_execute_message(self, WriteBuffer buf) except -1:
        """
        Write the message for a full execute.
        """
        cdef:
            uint32_t options, exec_flags = 0, num_params = 0, num_iters = 1
            Statement stmt = self.cursor_impl._statement
            BaseThinCursorImpl cursor_impl = self.cursor_impl
            list params = stmt._bind_info_list

        # determine the options to use for the execute
        options = 0
        if not stmt._requires_define and not self.parse_only \
                and params is not None:
            num_params = <uint32_t> len(params)
        if stmt._requires_define:
            options |= TNS_EXEC_OPTION_DEFINE
        elif not self.parse_only and stmt._sql is not None:
            exec_flags |= TNS_EXEC_FLAGS_IMPLICIT_RESULTSET
            if not self.scroll_operation:
                options |= TNS_EXEC_OPTION_EXECUTE
        if cursor_impl.scrollable:
            exec_flags |= TNS_EXEC_FLAGS_SCROLLABLE
        if stmt._cursor_id == 0 or stmt._is_ddl:
            options |= TNS_EXEC_OPTION_PARSE
        if stmt._is_query:
            if self.parse_only:
                options |= TNS_EXEC_OPTION_DESCRIBE
            else:
                if stmt._cursor_id == 0 or stmt._requires_define:
                    num_iters = self.cursor_impl.prefetchrows
                else:
                    num_iters = self.cursor_impl.arraysize
                self.cursor_impl._set_fetch_array_size(num_iters)
                if num_iters > 0 and not stmt._no_prefetch:
                    options |= TNS_EXEC_OPTION_FETCH
        if not stmt._is_plsql and not self.parse_only:
            options |= TNS_EXEC_OPTION_NOT_PLSQL
        elif stmt._is_plsql and num_params > 0:
            options |= TNS_EXEC_OPTION_PLSQL_BIND
        if num_params > 0:
            options |= TNS_EXEC_OPTION_BIND
        if self.batcherrors:
            options |= TNS_EXEC_OPTION_BATCH_ERRORS
        if self.arraydmlrowcounts:
            exec_flags |= TNS_EXEC_FLAGS_DML_ROWCOUNTS
        if self.conn_impl.autocommit and not self.parse_only:
            options |= TNS_EXEC_OPTION_COMMIT

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
            buf.write_bytes_with_length(stmt._sql_bytes)
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
        buf.write_ub4(exec_flags)           # al8i4[9] execute flags
        buf.write_ub4(self.fetch_orientation) # al8i4[10] fetch orientation
        buf.write_ub4(self.fetch_pos)       # al8i4[11] fetch pos
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
            uint32_t i, options_1 = 0, options_2 = 0, num_iters
            Statement stmt = self.cursor_impl._statement
            list params = stmt._bind_info_list
            BindInfo info

        if params:
            if not stmt._is_query and not stmt._is_returning:
                self.out_var_impls = [info._bind_var_impl \
                                      for info in params \
                                      if info.bind_dir != TNS_BIND_DIR_INPUT]
            params = [info for info in params \
                      if info.bind_dir != TNS_BIND_DIR_OUTPUT \
                      and not info._is_return_bind]
        if self.function_code == TNS_FUNC_REEXECUTE_AND_FETCH:
            options_1 |= TNS_EXEC_OPTION_EXECUTE
            num_iters = self.cursor_impl.prefetchrows
            self.cursor_impl._set_fetch_array_size(num_iters)
        else:
            if self.conn_impl.autocommit:
                options_2 |= TNS_EXEC_OPTION_COMMIT_REEXECUTE
            num_iters = self.num_execs

        self._write_function_code(buf)
        buf.write_ub4(stmt._cursor_id)
        buf.write_ub4(num_iters)
        buf.write_ub4(options_1)
        buf.write_ub4(options_2)
        if params:
            for i in range(self.num_execs):
                buf.write_uint8(TNS_MSG_TYPE_ROW_DATA)
                self._write_bind_params_row(buf, params, i)

    cdef int _write_message(self, WriteBuffer buf) except -1:
        """
        Write the execute message to the buffer. Two types of execute messages
        are possible: one for a full execute and the second, simpler message,
        for when an existing cursor is being re-executed. A full execute is
        required under the following circumstances:
            - the statement has never been executed
            - the statement refers to a REF cursor (no sql is defined)
            - prefetch is not possible (LOB columns fetched)
            - bind metadata has changed
            - parse is being performed
            - define is being performed
            - DDL is being executed
            - batch errors mode is enabled
        """
        cdef:
            Statement stmt = self.cursor_impl._statement
        if stmt._cursor_id == 0 or not stmt._executed \
                or stmt._sql is None \
                or stmt._no_prefetch \
                or stmt._binds_changed \
                or self.parse_only \
                or stmt._requires_define \
                or stmt._is_ddl \
                or self.batcherrors \
                or self.cursor_impl.scrollable:
            self.function_code = TNS_FUNC_EXECUTE
            self._write_execute_message(buf)
        elif stmt._is_query and self.cursor_impl.prefetchrows > 0:
            self.function_code = TNS_FUNC_REEXECUTE_AND_FETCH
            self._write_reexecute_message(buf)
        else:
            self.function_code = TNS_FUNC_REEXECUTE
            self._write_reexecute_message(buf)
        stmt._binds_changed = False

    cdef int process(self, ReadBuffer buf) except -1:
        """
        Runs after the database response has been processed. If the statement
        executed requires define and is not a REF cursor (which would already
        have performed the define during its execute), then mark the message as
        needing to be resent. If this is after the second time the message has
        been sent, mark the statement as no longer needing a define (since this
        only needs to happen once).
        """
        cdef Statement stmt = self.cursor_impl._statement
        MessageWithData.process(self, buf)
        if self.error_occurred and self.error_info.pos == 0 and stmt._is_plsql:
            self.error_info.pos = self.error_info.rowcount + self.offset
        if not self.parse_only:
            stmt._executed = True
        if stmt._requires_define and stmt._sql is not None:
            if self.resend:
                stmt._requires_define = False
            else:
                self.resend = True
