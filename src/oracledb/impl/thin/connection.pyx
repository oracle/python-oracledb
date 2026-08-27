#------------------------------------------------------------------------------
# Copyright (c) 2020, 2026, Oracle and/or its affiliates.
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
# connection.pyx
#
# Cython file defining the thin Connection implementation class (embedded in
# thin_impl.pyx).
#------------------------------------------------------------------------------

cdef class _SessionlessData:

    cdef:
        bytes transaction_id
        uint32_t operation
        uint32_t flags
        uint32_t timeout
        bint piggyback_pending
        bint started_on_server

    cdef TransactionSwitchMessage create_message(self,
                                                 BaseThinConnImpl conn_impl):
        """
        Returns the message used for sending the request to the database.
        """
        cdef:
            uint32_t sessionless_format_id = 0x4e5c3e
            TransactionSwitchMessage message
        message = conn_impl._create_message(TransactionSwitchMessage)
        if self.operation & TNS_TPC_TXN_START:
            message.xid = (sessionless_format_id, self.transaction_id, b"")
        message.timeout = self.timeout
        message.operation = self.operation
        message.flags = self.flags | TPC_TXN_FLAGS_SESSIONLESS
        return message


cdef class BaseThinConnImpl(BaseConnImpl):

    cdef:
        StatementCache _statement_cache
        BaseProtocol _protocol
        uint32_t _session_id
        uint16_t _serial_num
        str _action
        bint _action_modified
        str _dbop
        bint _dbop_modified
        str _client_info
        bint _client_info_modified
        str _client_identifier
        bint _client_identifier_modified
        str _module
        bint _module_modified
        bytes _ltxid
        str _current_schema
        bint _current_schema_modified
        str _txn_priority
        bint _txn_priority_modified
        uint8_t _max_identifier_length
        uint32_t _max_open_cursors
        str _db_domain
        str _db_name
        str _db_unique_name
        str _edition
        str _instance_name
        str _internal_name
        str _external_name
        str _service_name
        bint _drcp_enabled
        bint _drcp_establish_session
        double _time_created
        double _time_returned
        list _temp_lobs_to_close
        uint32_t _temp_lobs_total_size
        uint32_t _call_timeout
        str _cclass
        int _dbobject_type_cache_num
        bytes _combo_key
        bytes _connection_id_bytes
        str _connection_id
        bint _is_pooled
        bytes _pool_id
        bint _is_pool_extra
        bytes _transaction_context
        dict _app_context
        uint8_t pipeline_mode
        uint8_t _session_state_desired
        _SessionlessData _sessionless_data
        ConnectParamsImpl _connect_params
        EndUserSecurityContextImpl security_context
        bint _send_ha_readiness

    def __init__(self, str dsn, ConnectParamsImpl params):
        _check_cryptography()
        BaseConnImpl.__init__(self, dsn, params)
        self._connect_params = params
        self.thin = True
        self._app_context = None

    cdef int _clear_dbobject_type_cache(self) except -1:
        """
        """
        cdef int cache_num
        if self._dbobject_type_cache_num > 0:
            cache_num = self._dbobject_type_cache_num
            self._dbobject_type_cache_num = 0
            remove_dbobject_type_cache(cache_num)

    cdef int _close_socket(self) except -1:
        """
        Forces the socket closed for the connection. This is only used when a
        subscription is destroyed and the connection established for that
        subscription must be closed. Since the subscription is always waiting
        for more messages and the server never informs the client that no
        further messages will be coming, this approach must be used.
        """
        cdef object sock
        if self._protocol._transport is not None:
            sock = self._protocol._transport._transport
            if sock is not None:
                sock.shutdown(socket.SHUT_RDWR)

    cdef ThinLobImpl _create_lob_impl(self, DbType dbtype, bytes locator=None):
        """
        Create and return a LOB implementation object.
        """
        cdef ThinLobImpl lob_impl
        lob_impl = ThinLobImpl.__new__(ThinLobImpl)
        lob_impl._conn_impl = self
        lob_impl.dbtype = dbtype
        lob_impl._locator = locator
        return lob_impl

    cdef BaseCursorImpl _create_cursor_impl(self):
        """
        Internal method for creating an empty cursor implementation object.
        """
        return ThinCursorImpl.__new__(ThinCursorImpl, self)

    cdef Message _create_message(self, type typ):
        """
        Creates a message object that is used to send a request to the database
        and receive back its response.
        """
        cdef Message message
        message = typ.__new__(typ)
        message._initialize(self)
        return message

    def _create_message_for_pipeline_op(
        self, object conn, PipelineOpImpl op_impl
    ):
        """
        Creates a single message for a pipeline operation.
        """
        cdef:
            ThinCursorImpl cursor_impl
            MessageWithData message
            uint32_t num_execs = 1
            object cursor
        if op_impl.op_type == PIPELINE_OP_TYPE_COMMIT:
            return self._create_message(CommitMessage)
        cursor = conn.cursor()
        cursor_impl = cursor._impl
        if op_impl.op_type == PIPELINE_OP_TYPE_CALL_FUNC:
            execute_args = cursor._call_get_execute_args(
                op_impl.name,
                op_impl.parameters,
                op_impl.keyword_parameters,
                cursor.var(op_impl.return_type)
            )
            cursor._prepare_for_execute(*execute_args)
        elif op_impl.op_type == PIPELINE_OP_TYPE_CALL_PROC:
            execute_args = cursor._call_get_execute_args(
                op_impl.name,
                op_impl.parameters,
                op_impl.keyword_parameters
            )
            cursor._prepare_for_execute(*execute_args)
        elif op_impl.op_type == PIPELINE_OP_TYPE_EXECUTE:
            cursor._prepare_for_execute(op_impl.statement, op_impl.parameters)
        elif op_impl.op_type == PIPELINE_OP_TYPE_EXECUTE_MANY:
            op_impl.batch_load_manager = cursor_impl._prepare_for_executemany(
                cursor,
                op_impl.statement,
                op_impl.parameters,
                2 ** 32 - 1
            )
            op_impl.num_execs = op_impl.batch_load_manager.num_rows
            if not cursor_impl._statement.requires_single_execute():
                num_execs = op_impl.num_execs
        elif op_impl.op_type == PIPELINE_OP_TYPE_FETCH_ONE:
            cursor._prepare_for_execute(op_impl.statement, op_impl.parameters)
            cursor_impl.prefetchrows = 1
            cursor_impl.arraysize = 1
            cursor_impl.rowfactory = op_impl.rowfactory
            cursor_impl.fetch_lobs = op_impl.fetch_lobs
            cursor_impl.fetch_decimals = op_impl.fetch_decimals
        elif op_impl.op_type == PIPELINE_OP_TYPE_FETCH_MANY:
            cursor._prepare_for_execute(op_impl.statement, op_impl.parameters)
            cursor_impl.prefetchrows = op_impl.num_rows
            cursor_impl.arraysize = op_impl.num_rows
            cursor_impl.rowfactory = op_impl.rowfactory
            cursor_impl.fetch_lobs = op_impl.fetch_lobs
            cursor_impl.fetch_decimals = op_impl.fetch_decimals
        elif op_impl.op_type == PIPELINE_OP_TYPE_FETCH_ALL:
            cursor._prepare_for_execute(op_impl.statement, op_impl.parameters)
            cursor_impl.prefetchrows = op_impl.arraysize
            cursor_impl.arraysize = op_impl.arraysize
            cursor_impl.rowfactory = op_impl.rowfactory
            cursor_impl.fetch_lobs = op_impl.fetch_lobs
            cursor_impl.fetch_decimals = op_impl.fetch_decimals
        else:
            errors._raise_err(errors.ERR_UNSUPPORTED_PIPELINE_OPERATION,
                              op_type=op_impl.op_type)
        yield from cursor_impl._preprocess_execute(conn)
        message = cursor_impl._create_message(ExecuteMessage, cursor)
        message.num_execs = num_execs
        return message

    def _create_messages_for_pipeline(
        self, object conn, list results, bint continue_on_error
    ):
        """
        Creates a list of messages for the pipeline and returns them after they
        have been submitted to the database for processing.
        """
        cdef:
            PipelineOpResultImpl result_impl
            PipelineOpImpl op_impl
            uint64_t token_num
            Message message
            object result
            list messages
        messages = []
        token_num = 1
        for result in results:
            result_impl = result._impl
            op_impl = result_impl.operation
            try:
                message = yield from self._create_message_for_pipeline_op(
                    conn, op_impl
                )
            except Exception as e:
                if not continue_on_error:
                    raise
                result_impl._capture_err(e)
                continue
            message.pipeline_result_impl = result_impl
            message.token_num = token_num
            token_num += 1
            messages.append(message)
        return messages

    cdef Message _create_tpc_rollback_message(self, object xid=None):
        """
        Creates a two-phase commit rollback message suitable for use in both
        the close() method and explicitly by the user.
        """
        cdef TransactionChangeStateMessage message
        message = self._create_message(TransactionChangeStateMessage)
        message.operation = TNS_TPC_TXN_ABORT
        message.state = TNS_TPC_TXN_STATE_ABORTED
        message.xid = xid
        message.context = self._transaction_context
        return message

    cdef Statement _get_statement(self, str sql = None,
                                  bint cache_statement = False):
        """
        Get a statement from the statement cache, or prepare a new statement
        for use.
        """
        return self._statement_cache.get_statement(
            sql, cache_statement, self._drcp_establish_session
        )

    cdef int _post_connect_phase_one(self, Description description,
                                     ConnectParamsImpl params) except -1:
        """
        Called after the connection has been partially established to perform
        common tasks.
        """
        self._drcp_enabled = description.server_type == "pooled"
        if self._cclass is None:
            self._cclass = description.cclass
        if self._cclass is None:
            self._cclass = params._default_description.cclass

    cdef int _post_connect_phase_two(self, ConnectParamsImpl params) except -1:
        """
        Called after the connection has been fully established to perform
        common tasks.
        """
        self._statement_cache = StatementCache.__new__(StatementCache)
        self._statement_cache.initialize(params.stmtcachesize,
                                         self._max_open_cursors)
        self._dbobject_type_cache_num = create_new_dbobject_type_cache(self)
        self.invoke_session_callback = True
        if self._protocol._caps.supports_ha_readiness:
            self._send_ha_readiness = True

    cdef int _pre_connect(self, ConnectParamsImpl params) except -1:
        """
        Called before the connection is established to perform common tasks.
        """
        params._check_credentials()
        self._connection_id_bytes = secrets.token_bytes(16)
        self._connection_id = \
                base64.b64encode(self._connection_id_bytes).decode()

    cdef int _return_statement(self, Statement statement) except -1:
        """
        Return the statement to the statement cache, if applicable.
        """
        self._statement_cache.return_statement(statement)

    def _run_pipeline_op_without_pipelining(
        self, object conn, PipelineOpResultImpl result_impl
    ):
        """
        Runs a pipeline operation without the use of pipelining.
        """
        cdef:
            PipelineOpImpl op_impl = result_impl.operation
            object cursor
        if op_impl.op_type == PIPELINE_OP_TYPE_COMMIT:
            yield from conn._commit()
            return
        cursor = conn.cursor()
        if op_impl.op_type == PIPELINE_OP_TYPE_CALL_FUNC:
            result_impl.return_value = yield from cursor._callfunc(
                op_impl.name,
                op_impl.return_type,
                op_impl.parameters,
                op_impl.keyword_parameters,
            )
        elif op_impl.op_type == PIPELINE_OP_TYPE_CALL_PROC:
            yield from cursor._callproc(
                op_impl.name, op_impl.parameters, op_impl.keyword_parameters
            )
        elif op_impl.op_type == PIPELINE_OP_TYPE_EXECUTE:
            yield from cursor._execute(op_impl.statement, op_impl.parameters)
        elif op_impl.op_type == PIPELINE_OP_TYPE_EXECUTE_MANY:
            yield from cursor._executemany(
                op_impl.statement, op_impl.parameters
            )
        elif op_impl.op_type == PIPELINE_OP_TYPE_FETCH_ALL:
            yield from cursor._execute(op_impl.statement, op_impl.parameters)
            cursor.rowfactory = op_impl.rowfactory
            result_impl.rows = yield from cursor._fetchall()
        elif op_impl.op_type == PIPELINE_OP_TYPE_FETCH_MANY:
            yield from cursor._execute(op_impl.statement, op_impl.parameters)
            cursor.rowfactory = op_impl.rowfactory
            result_impl.rows = yield from cursor._fetchmany(op_impl.num_rows)
        elif op_impl.op_type == PIPELINE_OP_TYPE_FETCH_ONE:
            yield from cursor._execute(op_impl.statement, op_impl.parameters)
            cursor.rowfactory = op_impl.rowfactory
            result_impl.rows = yield from cursor._fetchmany(1)
        else:
            errors._raise_err(errors.ERR_UNSUPPORTED_PIPELINE_OPERATION,
                              op_type=op_impl.op_type)
        result_impl.warning = cursor.warning
        result_impl.fetch_metadata = cursor._impl.fetch_metadata

    cdef int _start_sessionless_transaction(
        self,
        bytes transaction_id,
        uint32_t timeout,
        uint32_t flags,
        bint defer_round_trip
    ) except -1:
        """
        Starts (either begins or resumes) a sessionless transaction. A message
        is returned if the request is not going to be deferred.
        """
        if self._sessionless_data is not None:
            errors._raise_err(errors.ERR_SESSIONLESS_ALREADY_ACTIVE)
        self._sessionless_data = _SessionlessData.__new__(_SessionlessData)
        self._sessionless_data.transaction_id = transaction_id
        self._sessionless_data.timeout = timeout
        self._sessionless_data.operation = TNS_TPC_TXN_START
        self._sessionless_data.flags = flags
        if defer_round_trip:
            self._sessionless_data.piggyback_pending = True

    def begin_sessionless_transaction(
        self,
        bytes transaction_id,
        int timeout,
        bint defer_round_trip
    ):
        """
        Begins a sessionless transaction.
        """
        self._start_sessionless_transaction(
            transaction_id, timeout, TPC_TXN_FLAGS_NEW, defer_round_trip
        )
        if not defer_round_trip:
            yield self._sessionless_data.create_message(self)

    def cancel(self):
        self._protocol._break_external()

    def change_password(self, str old_password, str new_password):
        """
        Change the password of the logged on user.
        """
        cdef AuthMessage message
        message = self._create_message(AuthMessage)
        message.change_password = True
        message.function_code = TNS_FUNC_AUTH_PHASE_TWO
        message.user_bytes = self.username.encode()
        message.user_bytes_len = len(message.user_bytes)
        message.auth_mode = TNS_AUTH_MODE_WITH_PASSWORD | \
                TNS_AUTH_MODE_CHANGE_PASSWORD
        message.password = old_password.encode()
        message.newpassword = new_password.encode()
        message.resend = False
        yield message

    def clear_end_user_security_context(self):
        """
        Clears the end user security context.
        """
        self.security_context = None

    def commit(self):
        """
        Commits the current transaction.
        """
        yield self._create_message(CommitMessage)

    def create_msg_props_impl(self):
        cdef ThinMsgPropsImpl impl
        impl = ThinMsgPropsImpl()
        impl._conn_impl = self
        return impl

    def create_queue_impl(self):
        return ThinQueueImpl.__new__(ThinQueueImpl)

    def create_temp_lob_impl(self, DbType dbtype):
        cdef ThinLobImpl lob_impl = self._create_lob_impl(dbtype)
        yield from lob_impl.create_temp()
        return lob_impl

    def direct_path_load(self, str schema_name, str table_name,
                         list column_names, object data,
                         uint32_t batch_size):
        """
        Performs a direct path load.
        """
        cdef:
            DirectPathPrepareMessage prepare_message
            DirectPathLoadStreamMessage load_message
            DirectPathOpMessage op_message
            BatchLoadManager manager

        # prepare message
        prepare_message = self._create_message(DirectPathPrepareMessage)
        prepare_message.schema_name = schema_name
        prepare_message.table_name = table_name
        prepare_message.column_names = column_names
        yield prepare_message

        # setup op message
        op_message = self._create_message(DirectPathOpMessage)
        op_message.prepare(prepare_message.cursor_id, TNS_DP_OP_ABORT)

        # load message
        load_message = self._create_message(DirectPathLoadStreamMessage)
        try:
            manager = BatchLoadManager.create_for_direct_path_load(
                data, prepare_message.column_metadata, batch_size
            )
            while manager.num_rows > 0:
                load_message.prepare(
                    prepare_message.cursor_id,
                    manager,
                    prepare_message.column_metadata
                )
                yield load_message
                manager.next_batch()
            op_message.op_code = TNS_DP_OP_FINISH
        finally:
            yield op_message

    def get_call_timeout(self):
        return self._call_timeout

    def get_current_schema(self):
        return self._current_schema

    def get_db_domain(self):
        if self._db_domain:
            return self._db_domain

    def get_db_name(self):
        return self._db_name

    def get_db_unique_name(self):
        return self._db_unique_name

    def get_session_id(self):
        return self._session_id

    def get_serial_num(self):
        return self._serial_num

    def get_edition(self):
        return self._edition

    def get_external_name(self):
        return self._external_name

    def get_host(self):
        return self._protocol._transport._address.host

    def get_instance_name(self):
        return self._instance_name

    def get_internal_name(self):
        return self._internal_name

    def get_is_healthy(self):
        return self._protocol._get_is_healthy()

    def get_ltxid(self):
        return self._ltxid or b''

    def get_max_identifier_length(self):
        return self._max_identifier_length

    def get_max_open_cursors(self):
        return self._max_open_cursors

    def get_port(self):
        return self._protocol._transport._address.port

    def get_protocol(self):
        return self._protocol._transport._address.protocol

    def get_sdu(self):
        return self._protocol._caps.sdu

    def get_service_name(self):
        return self._service_name

    def get_stmt_cache_size(self):
        return self._statement_cache._max_size

    def get_transaction_in_progress(self):
        return self._protocol._txn_in_progress

    def get_transaction_priority(self):
        if not self._protocol._caps.supports_txn_priority:
            errors._raise_err(errors.ERR_UNSUPPORTED_TXN_PRIORITY)
        return self._txn_priority

    def get_type(self, object conn, str name):
        """
        Returns a type given its name.
        """
        cdef ThinDbObjectTypeCache cache
        cache = get_dbobject_type_cache(self._dbobject_type_cache_num)
        return (yield from cache.get_type(conn, name))

    def ping(self):
        """
        Sends a "ping" to the database.
        """
        yield self._create_message(PingMessage)

    def resume_sessionless_transaction(
        self,
        bytes transaction_id,
        int timeout,
        bint defer_round_trip
    ):
        """
        Resumes a sessionless transaction.
        """
        self._start_sessionless_transaction(
            transaction_id, timeout, TPC_TXN_FLAGS_RESUME, defer_round_trip
        )
        if not defer_round_trip:
            yield self._sessionless_data.create_message(self)

    def rollback(self):
        """
        Rolls back the current transaction.
        """
        yield self._create_message(RollbackMessage)

    def run_pipeline_with_pipelining(
        self, object conn, list results, bint continue_on_error
    ):
        """
        Run the pipeline with pipelining when the database supports it.
        """
        cdef EndPipelineMessage message
        message = self._create_message(EndPipelineMessage)
        message.messages = yield from self._create_messages_for_pipeline(
            conn, results, continue_on_error
        )
        message.continue_on_error = continue_on_error
        if message.messages:
            self._protocol._read_buf.reset_packets()
            if continue_on_error:
                self.pipeline_mode = TNS_PIPELINE_MODE_CONTINUE_ON_ERROR
            else:
                self.pipeline_mode = TNS_PIPELINE_MODE_ABORT_ON_ERROR
            yield message
            yield from message._resend_messages()
            yield message
            yield from message._complete_pipeline_ops()

    def run_pipeline_without_pipelining(
        self, object conn, list results, bint continue_on_error
    ):
        """
        Run the pipeline without pipelining when the database doesn't support
        pipelining or when only one operation is being processed. Call timeouts
        are disabled for consistency with when run with pipelining.
        """
        cdef:
            uint32_t call_timeout = self._call_timeout
            PipelineOpResultImpl result_impl
            object result
        try:
            for result in results:
                result_impl = result._impl
                try:
                    yield from self._run_pipeline_op_without_pipelining(
                        conn, result_impl
                    )
                except Exception as e:
                    if not continue_on_error:
                        raise
                    result_impl._capture_err(e)
        finally:
            self._call_timeout = call_timeout

    def set_action(self, str value):
        self._action = value
        self._action_modified = True

    def clear_app_context(self, str namespace):
        if self._app_context is None:
            self._app_context = {}
        self._app_context[namespace] = {}

    def set_app_context(self, str namespace, **values):
        cdef dict entries
        if self._app_context is None:
            self._app_context = {}
        entries = self._app_context.setdefault(namespace, {})
        entries.update(values)

    def set_client_identifier(self, str value):
        self._client_identifier = value
        self._client_identifier_modified = True

    def set_client_info(self, str value):
        self._client_info = value
        self._client_info_modified = True

    def set_current_schema(self, value):
        self._current_schema = value
        self._current_schema_modified = True

    def set_dbop(self, str value):
        self._dbop = value
        self._dbop_modified = True

    def set_end_user_security_context(self, context):
        """
        Internal method that sets the end user security context.
        """
        if self._protocol._transport is not None \
                and self._protocol._transport._ssl_context is None:
            errors._raise_err(
                errors.ERR_END_USER_SECURITY_CONTEXT_REQUIRES_TCPS
            )
        if not self._protocol._caps.supports_end_user_security_context:
            errors._raise_err(
                errors.ERR_UNSUPPORTED_DEEP_DATA_SECURITY_FEATURE
            )
        self.security_context = context

    def set_external_name(self, value):
        self._external_name = value

    def set_internal_name(self, value):
        self._internal_name = value

    def set_module(self, str value):
        self._module = value
        self._module_modified = True
        # setting the module by itself results in an error so always force the
        # action to be set as well (which eliminates this error)
        self._action_modified = True

    def set_stmt_cache_size(self, uint32_t value):
        self._statement_cache.resize(value)

    def set_call_timeout(self, uint32_t value):
        self._protocol._transport.set_timeout(value / 1000)
        self._call_timeout = value

    def set_transaction_priority(self, value):
        if not self._protocol._caps.supports_txn_priority:
            errors._raise_err(errors.ERR_UNSUPPORTED_TXN_PRIORITY)
        self._txn_priority = value
        self._txn_priority_modified = True

    def supports_pipelining(self):
        """
        Returns whether the connection supports pipelining. Currently this is
        only supported with asyncio and Oracle Database version 23, and later.
        """
        return self._protocol._transport._is_async \
                and self._protocol._caps.supports_pipelining

    def suspend_sessionless_transaction(self):
        """
        Suspend a sessionless transaction.
        """
        cdef TransactionSwitchMessage message
        if self._sessionless_data is None:
            errors._raise_err(errors.ERR_SESSIONLESS_INACTIVE)
        elif self._sessionless_data.started_on_server:
            errors._raise_err(errors.ERR_SESSIONLESS_DIFFERING_METHODS)
        message = self._create_message(TransactionSwitchMessage)
        message.operation = TNS_TPC_TXN_DETACH
        message.flags = TPC_TXN_FLAGS_SESSIONLESS
        yield message

    def tpc_begin(self, xid, uint32_t flags, uint32_t timeout):
        """
        Begin a Two-Phase Commit (TPC) on a global transaction.
        """
        cdef TransactionSwitchMessage message
        message = self._create_message(TransactionSwitchMessage)
        message.operation = TNS_TPC_TXN_START
        message.xid = xid
        message.flags = flags
        message.timeout = timeout
        yield message
        self._transaction_context = message.context

    def tpc_commit(self, xid, bint one_phase):
        """
        Commit a global transaction.
        """
        cdef TransactionChangeStateMessage message
        message = self._create_message(TransactionChangeStateMessage)
        message.operation = TNS_TPC_TXN_COMMIT
        message.state = TNS_TPC_TXN_STATE_READ_ONLY if one_phase \
                else TNS_TPC_TXN_STATE_COMMITTED
        message.xid = xid
        message.context = self._transaction_context
        yield message
        if one_phase and message.state not in (TNS_TPC_TXN_STATE_READ_ONLY,
                                               TNS_TPC_TXN_STATE_COMMITTED) \
                or not one_phase \
                and message.state != TNS_TPC_TXN_STATE_FORGOTTEN:
            errors._raise_err(errors.ERR_UNKNOWN_TRANSACTION_STATE,
                              state=message.state)
        self._transaction_context = None

    def tpc_end(self, xid, uint32_t flags):
        """
        Ends a global transaction.
        """
        cdef TransactionSwitchMessage message
        message = self._create_message(TransactionSwitchMessage)
        message.operation = TNS_TPC_TXN_DETACH
        message.xid = xid
        message.context = self._transaction_context
        message.flags = flags
        yield message
        self._transaction_context = None

    def tpc_prepare(self, xid):
        """
        Prepares a global transaction for commit.
        """
        cdef TransactionChangeStateMessage message
        message = self._create_message(TransactionChangeStateMessage)
        message.operation = TNS_TPC_TXN_PREPARE
        message.xid = xid
        message.context = self._transaction_context
        yield message
        if message.state == TNS_TPC_TXN_STATE_REQUIRES_COMMIT:
            return True
        elif message.state == TNS_TPC_TXN_STATE_READ_ONLY:
            return False
        errors._raise_err(errors.ERR_UNKNOWN_TRANSACTION_STATE,
                          state=message.state)

    def tpc_rollback(self, xid):
        """
        Roll back a global transaction.
        """
        cdef TransactionChangeStateMessage message
        message = self._create_tpc_rollback_message(xid)
        yield message
        if message.state != TNS_TPC_TXN_STATE_ABORTED:
            errors._raise_err(errors.ERR_UNKNOWN_TRANSACTION_STATE,
                              state=message.state)


cdef class ThinConnImpl(BaseThinConnImpl):

    def __init__(self, str dsn, ConnectParamsImpl params):
        BaseThinConnImpl.__init__(self, dsn, params)
        self._protocol = Protocol()

    cdef int _close(self):
        """
        Internal method for closing the connection.
        """
        cdef Protocol protocol = <Protocol> self._protocol
        protocol._close(self)

    cdef int _connect_with_address(self, Address address,
                                   Description description,
                                   ConnectParamsImpl params,
                                   str connect_string,
                                   bint raise_exception) except -1:
        """
        Internal method used for connecting with the given description and
        address.
        """
        cdef Protocol protocol = <Protocol> self._protocol
        try:
            protocol._connect_phase_one(self, params, description,
                                        address, connect_string)
        except (exceptions.DatabaseError, socket.gaierror, OSError) as e:
            if raise_exception:
                errors._raise_err(errors.ERR_CONNECTION_FAILED, cause=e,
                                  connection_id=description.connection_id)
            return 0
        except Exception as e:
            errors._raise_err(errors.ERR_CONNECTION_FAILED, cause=e,
                              connection_id=description.connection_id)
        self._post_connect_phase_one(description, params)
        protocol._connect_phase_two(self, description, address, params)

    cdef int _connect_with_description(self, Description description,
                                       ConnectParamsImpl params,
                                       bint final_desc) except -1:
        """
        Internal method used for connecting with the given description. Retry
        connecting to the socket if an attempt fails and retry_count is
        specified in the connect string.
        """
        cdef:
            uint32_t i, j, k, num_attempts, num_lists, num_addresses
            AddressList address_list
            bint raise_exc = False
            str connect_string
            Address address
        num_lists = len(description.active_children)
        num_attempts = description.retry_count + 1
        connect_string = _get_connect_data(description, self._connection_id,
                                           params)
        if connect_string is None:
            errors._raise_err(errors.ERR_FEATURE_NOT_SUPPORTED,
                              feature="bequeath", driver_type="thick")
        for i in range(num_attempts):
            for j, address_list in enumerate(description.active_children):
                num_addresses = len(address_list.active_children)
                for k, address in enumerate(address_list.active_children):
                    if final_desc:
                        raise_exc = i == num_attempts - 1 \
                                and j == num_lists - 1 \
                                and k == num_addresses - 1
                    self._connect_with_address(address, description, params,
                                               connect_string, raise_exc)
                    if not self._protocol._in_connect:
                        return 0
            time.sleep(description.retry_delay)

    cdef int _connect_with_params(self, ConnectParamsImpl params) except -1:
        """
        Internal method used for connecting with the given parameters.
        """
        cdef:
            DescriptionList description_list = params.description_list
            ssize_t i, num_descriptions
            Description description
            bint final_desc
        description_list.set_active_children()
        num_descriptions = len(description_list.active_children)
        for i, description in enumerate(description_list.active_children):
            final_desc = (i == num_descriptions - 1)
            self._connect_with_description(description, params, final_desc)
            if not self._protocol._in_connect:
                break

    def close(self, bint in_del=False):
        """
        Internal method for closing the connection to the database.
        """
        cdef Protocol protocol = <Protocol> self._protocol
        self.security_context = None
        try:
            protocol.close(self, in_del)
        except (ssl.SSLError, exceptions.DatabaseError):
            pass

    def connect(self, ConnectParamsImpl params):
        cdef Protocol protocol = <Protocol> self._protocol
        try:
            self._pre_connect(params)
            self._connect_with_params(params)
            self._post_connect_phase_two(params)
        except:
            protocol._disconnect()
            raise

    def create_subscr_impl(self, object conn, object callback,
                           uint32_t namespace, str name, uint32_t protocol,
                           str ip_address, uint32_t port, uint32_t timeout,
                           uint32_t operations, uint32_t qos,
                           uint8_t grouping_class, uint32_t grouping_value,
                           uint8_t grouping_type, bint client_initiated):
        cdef ThinSubscrImpl impl = ThinSubscrImpl.__new__(ThinSubscrImpl)
        impl.connection = conn
        impl.callback = callback
        impl.namespace = namespace
        impl.name = name
        impl.protocol = protocol
        impl.ip_address = ip_address
        impl.port = port
        impl.timeout = timeout
        impl.operations = operations
        impl.qos = qos
        impl.grouping_class = grouping_class
        impl.grouping_value = grouping_value
        impl.grouping_type = grouping_type
        if not client_initiated:
            errors._raise_not_supported("server initiated subscription")
        impl.client_initiated = client_initiated
        return impl

    def process_sync_operation(self, object generator):
        """
        Processes a database operation synchronously. The generator returns
        messages that need to be processed by the database.
        """
        cdef:
            Protocol protocol = <Protocol> self._protocol
            Message message
        while True:
            try:
                message = next(generator)
                protocol._process_single_message(message)
            except StopIteration as e:
                return e.value


cdef class AsyncThinConnImpl(BaseThinConnImpl):

    def __init__(self, str dsn, ConnectParamsImpl params):
        BaseThinConnImpl.__init__(self, dsn, params)
        self._protocol = AsyncProtocol()

    async def _connect_with_address(self, Address address,
                                    Description description,
                                    ConnectParamsImpl params,
                                    str connect_string,
                                    bint raise_exception):
        """
        Internal method used for connecting with the given description and
        address.
        """
        cdef:
            BaseAsyncProtocol protocol = <BaseAsyncProtocol> self._protocol
        try:
            await protocol._connect_phase_one(self, params, description,
                                              address, connect_string)
        except (exceptions.DatabaseError, socket.gaierror,
                ConnectionRefusedError) as e:
            if raise_exception:
                errors._raise_err(errors.ERR_CONNECTION_FAILED, cause=e,
                                  connection_id=description.connection_id)
            return 0
        except Exception as e:
            errors._raise_err(errors.ERR_CONNECTION_FAILED, cause=e,
                              connection_id=description.connection_id)
        self._post_connect_phase_one(description, params)
        await self._protocol._connect_phase_two(self, description, address,
                                                params)

    async def _connect_with_description(self, Description description,
                                        ConnectParamsImpl params,
                                        bint final_desc):
        """
        Internal method used for connecting with the given description. Retry
        connecting to the socket if an attempt fails and retry_count is
        specified in the connect string.
        """
        cdef:
            uint32_t i, j, k, num_attempts, num_lists, num_addresses
            AddressList address_list
            bint raise_exc = False
            str connect_string
            Address address
        num_lists = len(description.active_children)
        num_attempts = description.retry_count + 1
        connect_string = _get_connect_data(description, self._connection_id, params)
        for i in range(num_attempts):
            for j, address_list in enumerate(description.active_children):
                num_addresses = len(address_list.active_children)
                for k, address in enumerate(address_list.active_children):
                    if final_desc:
                        raise_exc = i == num_attempts - 1 \
                                and j == num_lists - 1 \
                                and k == num_addresses - 1
                    await self._connect_with_address(address, description,
                                                     params, connect_string,
                                                     raise_exc)
                    if not self._protocol._in_connect:
                        return 0
            await asyncio.sleep(description.retry_delay)

    async def _connect_with_params(self, ConnectParamsImpl params):
        """
        Internal method used for connecting with the given parameters.
        """
        cdef:
            DescriptionList description_list = params.description_list
            ssize_t i, num_descriptions
            Description description
            bint final_desc
        description_list.set_active_children()
        num_descriptions = len(description_list.active_children)
        for i, description in enumerate(description_list.active_children):
            final_desc = (i == num_descriptions - 1)
            await self._connect_with_description(description, params,
                                                 final_desc)
            if not self._protocol._in_connect:
                break

    async def close(self, bint in_del=False):
        """
        Sends the messages needed to disconnect from the database.
        """
        cdef BaseAsyncProtocol protocol = <BaseAsyncProtocol> self._protocol
        try:
            await protocol.close(self, in_del)
        except (ssl.SSLError, exceptions.DatabaseError):
            pass

    async def connect(self, ConnectParamsImpl params):
        """
        Sends the messages needed to connect to the database.
        """
        cdef BaseAsyncProtocol protocol = <BaseAsyncProtocol> self._protocol
        protocol._read_buf._loop = asyncio.get_running_loop()
        try:
            self._pre_connect(params)
            await self._connect_with_params(params)
            self._post_connect_phase_two(params)
        except:
            protocol._disconnect()
            raise

    async def process_async_operation(self, object generator):
        """
        Processes a database operation asynchronously. The generator returns
        messages that need to be processed by the database.
        """
        cdef:
            BaseAsyncProtocol protocol = <BaseAsyncProtocol> self._protocol
            Message message
        while True:
            try:
                message = next(generator)
                await protocol._process_single_message(message)
            except StopIteration as e:
                return e.value
