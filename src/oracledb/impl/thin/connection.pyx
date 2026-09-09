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
        str round_trip_name
        bint piggyback_pending
        bint started_on_server

    cdef TransactionSwitchMessage create_message(self, ThinConnImpl conn_impl):
        """
        Returns the message used for sending the request to the database.
        """
        cdef:
            uint32_t sessionless_format_id = 0x4e5c3e
            TransactionSwitchMessage message
        message = conn_impl._create_message(
            TransactionSwitchMessage, self.round_trip_name
        )
        if self.operation & TNS_TPC_TXN_START:
            message.xid = (sessionless_format_id, self.transaction_id, b"")
        message.timeout = self.timeout
        message.operation = self.operation
        message.flags = self.flags | TPC_TXN_FLAGS_SESSIONLESS
        return message


cdef class ThinConnImpl(BaseConnImpl):

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
        EndUserSecurityContextImpl security_context
        bint _send_ha_readiness

    def __init__(self, bint is_async = False):
        self.thin = True
        cls = AsyncProtocol if is_async else Protocol
        self._protocol = cls()

    cdef int _clear_dbobject_type_cache(self) except -1:
        """
        Clears the database object type cache.
        """
        cdef int cache_num
        if self._dbobject_type_cache_num > 0:
            cache_num = self._dbobject_type_cache_num
            self._dbobject_type_cache_num = 0
            remove_dbobject_type_cache(cache_num)

    def _close(self):
        """
        Closes the connection to the database.
        """
        cdef WriteBuffer buf = self._protocol._write_buf
        try:
            self._clear_dbobject_type_cache()
            self._protocol._check_is_healthy()
            if self._protocol._transport is not None and not self._drcp_enabled:
                yield self._create_message(LogoffMessage, "logoff")
            self._protocol._check_is_healthy()
            if self._protocol._transport is not None:
                buf.start_request(TNS_PACKET_TYPE_DATA, "eof", 0,
                                  TNS_DATA_FLAGS_EOF)
                buf.end_request()
        finally:
            self._protocol._disconnect()

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

    def _connect(self):
        """
        Internal method used for connecting with the given parameters.
        """
        cdef:
            ConnectParamsImpl params = self.connect_params
            AddressList address_list
            Description description
            Exception exc = None
            str connect_string
            Address address
            ssize_t i
        params.description_list.set_active_children()
        for description in params.description_list.active_children:
            connect_string = _get_connect_data(description,
                                               self._connection_id,
                                               self.connect_params)
            if connect_string is None:
                errors._raise_err(errors.ERR_FEATURE_NOT_SUPPORTED,
                                  feature="bequeath", driver_type="thick")
            for i in range(description.retry_count + 1):
                if i > 0:
                    sleep_sub_op = SleepSubOp.__new__(SleepSubOp)
                    sleep_sub_op.delay = description.retry_delay
                    yield sleep_sub_op
                for address_list in description.active_children:
                    for address in address_list.active_children:
                        try:
                            yield from self._connect_phase_one(
                                description, address, connect_string
                            )
                        except (
                            exceptions.DatabaseError,
                            socket.gaierror,
                            OSError
                        ) as e:
                            exc = errors._create_exception(
                                errors.ERR_CONNECTION_FAILED,
                                cause=e,
                                connection_id=description.connection_id
                            )
                            yield
                            continue
                        except Exception as e:
                            errors._raise_err(
                                errors.ERR_CONNECTION_FAILED,
                                cause=e,
                                connection_id=description.connection_id
                            )
                        yield from self._connect_phase_two(
                            description, address
                        )
                        return
        raise exc

    def _connect_phase_one(self, Description description, Address address,
                           str connect_string):
        """
        Method for performing the required steps for establishing a connection
        within the scope of a retry. If the listener refuses the connection, a
        retry will be performed, if retry_count is set.
        """
        cdef:
            ReadBuffer read_buf = self._protocol._read_buf
            NegotiateTlsSubOp negotiate_tls_sub_op
            ConnectMessage connect_message = None
            uint8_t packet_type, packet_flags = 0
            TcpConnectSubOp tcp_connect_sub_op
            object ssl_context, connect_info
            ConnectParamsImpl temp_params
            Address db_address = address
            Address temp_address
            str redirect_data
            int pos

        # disable OOB processing, if requested
        if self.connect_params.disable_oob:
            self._protocol._caps.supports_oob = False

        # establish initial TCP connection
        tcp_connect_sub_op = TcpConnectSubOp.__new__(TcpConnectSubOp)
        tcp_connect_sub_op.conn_impl = self
        tcp_connect_sub_op.host = address.ip_address
        tcp_connect_sub_op.port = address.port
        tcp_connect_sub_op.connect_string = connect_string
        tcp_connect_sub_op.description = description
        tcp_connect_sub_op.address = db_address
        yield tcp_connect_sub_op

        # send connect message and process response; this may request the
        # message to be resent multiple times; if a redirect packet is
        # detected, a new TCP connection is established first
        while True:

            # create connect message, if needed
            if connect_message is None:
                connect_message = self._create_message(
                    ConnectMessage, "connect"
                )
                connect_message.host = tcp_connect_sub_op.host
                connect_message.port = tcp_connect_sub_op.port
                connect_message.params = self.connect_params
                connect_message.description = description
                connect_message.address = address
                connect_message.connect_string_bytes = connect_string.encode()
                connect_message.connect_string_len = \
                        <uint16_t> len(connect_message.connect_string_bytes)
                connect_message.packet_flags = packet_flags

            # process connection message
            yield connect_message
            packet_type = read_buf._current_packet.packet_type
            if connect_message.redirect_data is not None:
                redirect_data = connect_message.redirect_data
                pos = redirect_data.find('\x00')
                if pos < 0:
                    errors._raise_err(errors.ERR_INVALID_REDIRECT_DATA,
                                      data=redirect_data)
                temp_params = ConnectParamsImpl()
                temp_params._parse_connect_string(redirect_data[:pos])
                temp_address = temp_params._get_addresses()[0]
                db_address = db_address.copy()
                db_address.host = temp_address.host
                db_address.port = temp_address.port
                tcp_connect_sub_op.host = temp_address.host
                tcp_connect_sub_op.port = temp_address.port
                tcp_connect_sub_op.address = db_address
                tcp_connect_sub_op.connect_string = redirect_data[pos + 1:]
                yield tcp_connect_sub_op
                connect_message = None
                packet_flags = TNS_PACKET_FLAG_REDIRECT
            elif packet_type == TNS_PACKET_TYPE_ACCEPT:
                self._protocol._transport._max_packet_size = read_buf._caps.sdu
                self._protocol._write_buf._size_for_sdu()
                break

            # for TCPS connections, if the packet flags indicate that TLS
            # renegotiation is required, this is performed now
            if address.protocol == "tcps":
                packet_flags = read_buf._current_packet.packet_flags
                if packet_flags & TNS_PACKET_FLAG_TLS_RENEG:
                    negotiate_tls_sub_op = \
                            NegotiateTlsSubOp.__new__(NegotiateTlsSubOp)
                    negotiate_tls_sub_op.description = description
                    negotiate_tls_sub_op.address = address
                    negotiate_tls_sub_op.conn_impl = self
                    yield negotiate_tls_sub_op

    def _connect_phase_two(self, Description description, Address address):
        """"
        Method for perfoming the required steps for establishing a connection
        oustide the scope of a retry. If any of the steps in this method fail,
        an exception will be raised.
        """
        cdef:
            DataTypesMessage data_types_message
            FastAuthMessage fast_auth_message
            ProtocolMessage protocol_message
            bint supports_end_of_response
            AuthMessage auth_message
            Capabilities caps

        # setup DRCP attributes
        self._drcp_enabled = description.server_type == "pooled"
        if self._cclass is None:
            self._cclass = description.cclass
        if self._cclass is None:
            self._cclass = self.connect_params._default_description.cclass

        # force the end of response to be disabled for the first packets
        caps = self._protocol._caps
        supports_end_of_response = caps.supports_end_of_response
        caps.supports_end_of_response = False

        # if we can use OOB, send an urgent message now followed by a reset
        # marker to see if the server understands it
        if caps.supports_oob and caps.supports_oob_check:
            self._protocol._transport.send_oob_break()
            self._protocol._send_marker(
                self._protocol._write_buf, TNS_MARKER_TYPE_RESET
            )

        # send the network services message, if applicable
        if self.connect_params.externalauth and address.protocol == "tcps" \
                and description.wallet_location is not None:
            yield self._create_message(
                NetworkServicesMessage, "network_services"
            )

        # create the messages that need to be sent to the server
        protocol_message = self._create_message(ProtocolMessage, "protocol")
        data_types_message = self._create_message(
            DataTypesMessage, "data_types"
        )
        auth_message = self._create_message(AuthMessage, "authorization")
        auth_message._set_params(self.connect_params, description)

        # starting in Oracle Database version 23, fast authentication is
        # possible; use it if the server supports it
        if caps.supports_fast_auth:
            caps.supports_end_of_response = supports_end_of_response
            fast_auth_message = self._create_message(
                FastAuthMessage, "fast_authorization"
            )
            fast_auth_message.protocol_message = protocol_message
            fast_auth_message.data_types_message = data_types_message
            fast_auth_message.auth_message = auth_message
            yield fast_auth_message
            if auth_message.resend:
                auth_message.resend = False
                yield auth_message

        # otherwise, do the normal authentication; disable end of response for
        # the first two messages as the server does not send an end of response
        # for these messages
        else:
            yield protocol_message
            yield data_types_message
            caps.supports_end_of_response = supports_end_of_response
            yield auth_message

        # perform post connect activities
        self._post_connect(auth_message)

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

    cdef Message _create_message(self, type typ, str name):
        """
        Creates a message object that is used to send a request to the database
        and receive back its response.
        """
        cdef Message message
        message = typ.__new__(typ)
        message.name = name
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
            return self._create_message(CommitMessage, "commit")
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
        message = cursor_impl._create_message(
            ExecuteMessage, "execute", cursor
        )
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
        message = self._create_message(
            TransactionChangeStateMessage, "tpc_rollback"
        )
        message.operation = TNS_TPC_TXN_ABORT
        message.state = TNS_TPC_TXN_STATE_ABORTED
        message.xid = xid
        message.context = self._transaction_context
        return message

    def _end_request(self):
        """
        Ends the request to the database. This rolls back any open transaction
        and releases any DRCP session, if applicable.
        """
        cdef:
            ThinDbObjectTypeCache type_cache
            SessionReleaseMessage message
            int cache_num

        # clear end user security context and any pending warning
        self.security_context = None
        self.warning = None

        # clear cursors in database object type cache, if applicable
        if self._dbobject_type_cache_num > 0:
            cache_num = self._dbobject_type_cache_num
            type_cache = get_dbobject_type_cache(cache_num)
            type_cache._clear_cursors()

        # if the connection is healthy, send a rollback message if there is
        # an open transaction or a request is in progress
        self._protocol._check_is_healthy()
        if self._protocol._transport is not None:
            if self._in_request and self._session_state_desired != 0:
                self._in_request = False
            if self._protocol._txn_in_progress or self._in_request:
                if self._in_request:
                    self._session_state_desired = \
                            TNS_SESSION_STATE_REQUEST_END
                    self._in_request = False
                if self._transaction_context is not None:
                    self._transaction_context = None
                    yield self._create_tpc_rollback_message()
                else:
                    yield self._create_message(RollbackMessage, "rollback")

        # if the connection is still healthy and DRCP is in use, process a
        # session release message, note that this a one-way RPC which cannot be
        # piggybacked
        self._protocol._check_is_healthy()
        if self._protocol._transport is not None and self._drcp_enabled:
            message = self._create_message(
                SessionReleaseMessage, "release_drcp_session"
            )
            if not self._is_pooled:
                message.release_mode = DRCP_DEAUTHENTICATE
            yield message
            self._drcp_establish_session = True

        # if the connection is no longer healthy, close it
        if not self._protocol._get_is_healthy():
            try:
                yield from self._close()
            except:
                pass

    cdef Statement _get_statement(self, str sql = None,
                                  bint cache_statement = False):
        """
        Get a statement from the statement cache, or prepare a new statement
        for use.
        """
        return self._statement_cache.get_statement(
            sql, cache_statement, self._drcp_establish_session
        )

    cdef int _post_connect(self, AuthMessage auth_message) except -1:
        """"
        Performs activities after the connection has completed. The protocol
        must be marked to indicate that the connect is no longer in progress,
        which allows the normal break/reset mechanism to fire. The session must
        also be marked as not needing to be closed since for listener redirects
        the packet may indicate EOF for the initial connection that is
        established.
        """
        cdef:
            dict session_data = auth_message.session_data
            ReadBuffer buf = self._protocol._read_buf
        self._session_id = <uint32_t> int(session_data["AUTH_SESSION_ID"])
        self._serial_num = <uint16_t> int(session_data["AUTH_SERIAL_NUM"])
        self._db_domain = session_data.get("AUTH_SC_DB_DOMAIN")
        self._db_name = session_data.get("AUTH_SC_DBUNIQUE_NAME")
        self._db_unique_name = session_data.get("AUTH_SC_REAL_DBUNIQUE_NAME")
        self._max_open_cursors = \
                int(session_data.get("AUTH_MAX_OPEN_CURSORS", 0))
        self._service_name = session_data.get("AUTH_SC_SERVICE_NAME")
        self._instance_name = session_data.get("AUTH_INSTANCENAME")
        self._max_identifier_length = \
                int(session_data.get("AUTH_MAX_IDEN_LENGTH", 30))
        self.server_version = auth_message._get_version_tuple(buf)
        self.supports_bool = \
                buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_23_1
        self._edition = auth_message.edition
        self.warning = auth_message.warning
        buf._pending_error_num = 0
        self._protocol._in_connect = False

    async def _process_async_operation_sub_op(self, object sub_op):
        """
        Processes a sub operation of a synchronous operation. These may either
        be round trips to the database or driver operations.
        """
        cdef BaseAsyncProtocol protocol = <BaseAsyncProtocol> self._protocol
        if isinstance(sub_op, Message):
            await protocol._process_single_message(sub_op)
        else:
            await sub_op.process_async()

    cdef int _process_sync_operation_sub_op(self, object sub_op) except -1:
        """
        Processes a sub operation of a synchronous operation. These may either
        be round trips to the database or driver operations.
        """
        if isinstance(sub_op, Message):
            (<Protocol> self._protocol)._process_single_message(sub_op)
        else:
            sub_op.process()

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
        bint defer_round_trip,
        str round_trip_name
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
        self._sessionless_data.round_trip_name = round_trip_name
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
            transaction_id,
            timeout,
            TPC_TXN_FLAGS_NEW,
            defer_round_trip,
            "begin_sessionless_transaction",
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
        message = self._create_message(AuthMessage, "change_password")
        message.change_password = True
        message.function_code = TNS_FUNC_AUTH_PHASE_TWO
        message.user_bytes = self.connect_params.user.encode()
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

    def close(self):
        """
        Close the connection to the database.
        """
        try:
            yield from self._end_request()
            yield from self._close()
        except (ssl.SSLError, exceptions.DatabaseError):
            pass

    def commit(self):
        """
        Commits the current transaction.
        """
        yield self._create_message(CommitMessage, "commit")

    def connect(self, object pool = None):
        """
        Establishes a connection to the database.
        """

        # thin mode does not currently support sharding
        if self.connect_params.shardingkey is not None \
                or self.connect_params.supershardingkey is not None:
            errors._raise_err(
                errors.ERR_FEATURE_NOT_SUPPORTED,
                feature="sharding",
                driver_type="thick",
            )

        # if a pool is being used, acquire the connection from it and discard
        # the temporary implementation object that was created
        if pool is not None:
            return (yield from pool._impl.acquire(self.connect_params))

        # initial setup before attempting to connect
        _check_cryptography()
        self.connect_params._check_credentials()
        self._connection_id_bytes = secrets.token_bytes(16)
        self._connection_id = \
                base64.b64encode(self._connection_id_bytes).decode()

        # if connection fails, discard the connection
        try:
            yield from self._connect()
        except:
            self._protocol._disconnect()
            raise

        # final setup before returning connection
        self._statement_cache = StatementCache.__new__(StatementCache)
        self._statement_cache.initialize(self.connect_params.stmtcachesize,
                                         self._max_open_cursors)
        self._dbobject_type_cache_num = create_new_dbobject_type_cache(self)
        if self._protocol._caps.supports_ha_readiness:
            self._send_ha_readiness = True

        return self

    def create_msg_props_impl(self):
        cdef ThinMsgPropsImpl impl
        impl = ThinMsgPropsImpl()
        impl._conn_impl = self
        return impl

    def create_queue_impl(self):
        return ThinQueueImpl.__new__(ThinQueueImpl)

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
        prepare_message = self._create_message(
            DirectPathPrepareMessage, "direct_path_prepare"
        )
        prepare_message.schema_name = schema_name
        prepare_message.table_name = table_name
        prepare_message.column_names = column_names
        yield prepare_message

        # setup op message
        op_message = self._create_message(
            DirectPathOpMessage, "direct_path_operation"
        )
        op_message.prepare(prepare_message.cursor_id, TNS_DP_OP_ABORT)

        # load message
        load_message = self._create_message(
            DirectPathLoadStreamMessage, "direct_path_load"
        )
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
        yield self._create_message(PingMessage, "ping")

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
            transaction_id,
            timeout,
            TPC_TXN_FLAGS_RESUME,
            defer_round_trip,
            "resume_sessionless_transaction",
        )
        if not defer_round_trip:
            yield self._sessionless_data.create_message(self)

    def rollback(self):
        """
        Rolls back the current transaction.
        """
        yield self._create_message(RollbackMessage, "rollback")

    def run_pipeline_with_pipelining(
        self, object conn, list results, bint continue_on_error
    ):
        """
        Run the pipeline with pipelining when the database supports it.
        """
        cdef EndPipelineMessage message
        message = self._create_message(EndPipelineMessage, "end_pipeline")
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
        message = self._create_message(
            TransactionSwitchMessage, "suspend_sessionless_transaction"
        )
        message.operation = TNS_TPC_TXN_DETACH
        message.flags = TPC_TXN_FLAGS_SESSIONLESS
        yield message

    def terminate(self):
        """
        Terminates the connection without performing any of the normal logoff
        procedures. This should only be called by the async implementation when
        the event loop is no longer available.
        """
        self._protocol._disconnect()

    def tpc_begin(self, xid, uint32_t flags, uint32_t timeout):
        """
        Begin a Two-Phase Commit (TPC) on a global transaction.
        """
        cdef TransactionSwitchMessage message
        message = self._create_message(TransactionSwitchMessage, "tpc_begin")
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
        message = self._create_message(
            TransactionChangeStateMessage, "tpc_commit"
        )
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
        message = self._create_message(TransactionSwitchMessage, "tpc_end")
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
        message = self._create_message(
            TransactionChangeStateMessage, "tpc_prepare"
        )
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


@cython.final
cdef class SleepSubOp(SubOperation):
    cdef:
        uint32_t delay

    def process(self):
        """
        Runs the callback synchronously.
        """
        time.sleep(self.delay)

    async def process_async(self):
        """
        Runs the callback asynchronously.
        """
        await asyncio.sleep(self.delay)


@cython.final
cdef class TcpConnectSubOp(SubOperation):
    cdef:
        ThinConnImpl conn_impl
        Description description
        Address address
        str connect_string
        str host
        uint32_t port

    def process(self):
        """
        Runs the callback synchronously.
        """
        cdef Protocol protocol = self.conn_impl._protocol
        protocol._connect_tcp(
            self.conn_impl.connect_params,
            self.description,
            self.address,
            self.host,
            self.port,
            self.connect_string,
        )

    async def process_async(self):
        """
        Runs the callback asynchronously.
        """
        cdef BaseAsyncProtocol protocol = self.conn_impl._protocol
        await protocol._connect_tcp(
            self.conn_impl.connect_params,
            self.description,
            self.address,
            self.host,
            self.port,
        )


@cython.final
cdef class NegotiateTlsSubOp(SubOperation):
    cdef:
        ThinConnImpl conn_impl
        Description description
        Address address

    def process(self):
        """
        Runs the callback synchronously.
        """
        self.conn_impl._protocol._transport.renegotiate_tls(
            self.address, self.description
        )

    async def process_async(self):
        """
        Runs the callback asynchronously.
        """
        await self.conn_impl._protocol._transport.negotiate_tls_async(
            self.conn_impl._protocol, self.address, self.description
        )
