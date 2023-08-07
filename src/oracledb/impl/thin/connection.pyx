#------------------------------------------------------------------------------
# Copyright (c) 2020, 2023, Oracle and/or its affiliates.
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

cdef class ThinConnImpl(BaseConnImpl):

    cdef:
        object _statement_cache
        uint32_t _statement_cache_size
        object _statement_cache_lock
        Protocol _protocol
        str _server_version
        uint32_t _session_id
        uint32_t _serial_num
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
        ThinPoolImpl _pool
        bytes _ltxid
        str _current_schema
        bint _current_schema_modified
        str _edition
        str _instance_name
        str _internal_name
        str _external_name
        array.array _cursors_to_close
        ssize_t _num_cursors_to_close
        bint _drcp_enabled
        bint _drcp_establish_session
        double _time_in_pool
        list _temp_lobs_to_close
        uint32_t _temp_lobs_total_size
        uint32_t _call_timeout
        str _cclass
        int _dbobject_type_cache_num
        bytes _combo_key
        str _connection_id
        bint _is_pool_extra

    def __init__(self, str dsn, ConnectParamsImpl params):
        if not HAS_CRYPTOGRAPHY:
            errors._raise_err(errors.ERR_NO_CRYPTOGRAPHY_PACKAGE)
        BaseConnImpl.__init__(self, dsn, params)
        self._protocol = Protocol()

    cdef int _add_cursor_to_close(self, Statement stmt) except -1:
        if self._num_cursors_to_close == TNS_MAX_CURSORS_TO_CLOSE:
            errors._raise_err(errors.ERR_TOO_MANY_CURSORS_TO_CLOSE,
                              num_cursors=TNS_MAX_CURSORS_TO_CLOSE)
        self._cursors_to_close[self._num_cursors_to_close] = stmt._cursor_id
        self._num_cursors_to_close += 1

    cdef int _adjust_statement_cache(self) except -1:
        cdef Statement stmt
        while len(self._statement_cache) > self._statement_cache_size:
            stmt = <Statement> self._statement_cache.popitem(last=False)[1]
            if stmt._in_use:
                stmt._return_to_cache = False
            elif stmt._cursor_id != 0:
                self._add_cursor_to_close(stmt)

    cdef int _connect_with_address(self, Address address,
                                   Description description,
                                   ConnectParamsImpl params,
                                   str connect_string,
                                   bint raise_exception) except -1:
        """
        Internal method used for connecting with the given description and
        address.
        """
        cdef ConnectionCookie cookie
        try:
            cookie = self._protocol._connect_phase_one(self, params,
                                                       description, address,
                                                       connect_string)
        except (exceptions.DatabaseError, socket.gaierror,
                ConnectionRefusedError) as e:
            if raise_exception:
                errors._raise_err(errors.ERR_CONNECTION_FAILED, cause=e,
                                  connection_id=description.connection_id)
            return 0
        except Exception as e:
            errors._raise_err(errors.ERR_CONNECTION_FAILED, cause=e,
                              connection_id=description.connection_id)
        self._drcp_enabled = description.server_type == "pooled"
        if self._cclass is None:
            self._cclass = description.cclass
        if self._cclass is None and self._pool is not None \
                and self._drcp_enabled:
            gen_uuid = uuid.uuid4()
            self._cclass = f"DPY:{base64.b64encode(gen_uuid.bytes).decode()}"
            params._default_description.cclass = self._cclass
        self._protocol._connect_phase_two(self, cookie, description, params)

    cdef int _connect_with_description(self, Description description,
                                       ConnectParamsImpl params,
                                       bint final_desc) except -1:
        """
        Internal method used for connecting with the given description.
        """
        cdef:
            bint load_balance = description.load_balance
            bint raise_exc = False
            list address_lists = description.address_lists
            uint32_t i, j, k, num_addresses, idx1, idx2
            uint32_t num_attempts = description.retry_count + 1
            uint32_t num_lists = len(address_lists)
            AddressList address_list
            str connect_string
            Address address

        # Retry connecting to the socket if an attempt fails and retry_count
        # is specified in the connect string. If an attempt succeeds, return
        # the socket and the valid address object.
        connect_string = _get_connect_data(description, self._connection_id)
        for i in range(num_attempts):

            # iterate through each address_list in the description; if the
            # description level load_balance is on, keep track of the least
            # recently used address for subsequent connections; otherwise,
            # iterate through the list in order; note that if source_route is
            # enabled that only the first address list is examined as the rest
            # are used for routing on the server
            if description.source_route and num_lists > 0:
                num_lists = 1
            for j in range(num_lists):
                if load_balance:
                    idx1 = (j + description.lru_index) % num_lists
                else:
                    idx1 = j

                # iterate through each address in an address_list; if the
                # address_list level load_balance is on, keep track of the
                # least recently used address for subsequent connections;
                # otherwise, iterate through the list in order; note that if
                # source_route is enabled that only the first address is
                # examined and the rest are used for routing on the server
                address_list = address_lists[idx1]
                num_addresses = len(address_list.addresses)
                if address_list.source_route and num_addresses > 0:
                    num_addresses = 1
                for k in range(num_addresses):
                    if address_list.load_balance:
                        idx2 = (k + address_list.lru_index) % num_addresses
                    else:
                        idx2 = k
                    address = address_list.addresses[idx2]
                    if final_desc:
                        raise_exc = i == num_attempts - 1 \
                                and j == num_lists - 1 \
                                and k == num_addresses - 1
                    self._connect_with_address(address, description, params,
                                               connect_string, raise_exc)
                    if self._protocol._in_connect:
                        continue
                    address_list.lru_index = (idx1 + 1) % num_addresses
                    description.lru_index = (idx2 + 1) % num_lists
                    return 0
            time.sleep(description.retry_delay)

    cdef int _connect_with_params(self, ConnectParamsImpl params) except -1:
        """
        Internal method used for connecting with the given parameters.
        """
        cdef:
            DescriptionList description_list = params.description_list
            list descriptions = description_list.descriptions
            ssize_t i, idx, num_descriptions = len(descriptions)
            Description description
            bint final_desc = False
        if description_list.source_route and num_descriptions > 0:
            num_descriptions = 1
        for i in range(num_descriptions):
            if i == num_descriptions - 1:
                final_desc = True
            if description_list.load_balance:
                idx = (i + description_list.lru_index) % num_descriptions
            else:
                idx = i
            description = descriptions[idx]
            self._connect_with_description(description, params, final_desc)
            if not self._protocol._in_connect:
                description_list.lru_index = (idx + 1) % num_descriptions
                break

    cdef Message _create_message(self, type typ):
        """
        Creates a message object that is used to send a request to the database
        and receive back its response.
        """
        cdef Message message
        message = typ.__new__(typ)
        message._initialize(self)
        return message

    cdef int _force_close(self) except -1:
        self._pool = None
        if self._dbobject_type_cache_num > 0:
            remove_dbobject_type_cache(self._dbobject_type_cache_num)
            self._dbobject_type_cache_num = 0
        self._protocol._force_close()

    cdef Statement _get_statement(self, str sql, bint cache_statement):
        """
        Get a statement from the statement cache, or prepare a new statement
        for use. If a statement is already in use a copy will be made and
        returned (and will not be returned to the cache). If a statement is
        being executed for the first time after releasing a DRCP session, a
        copy will also be made (and will not be returned to the cache) since it
        is unknown at this point whether the original session or a new session
        is going to be used.
        """
        cdef Statement statement
        with self._statement_cache_lock:
            statement = self._statement_cache.get(sql)
            if statement is None:
                statement = Statement()
                statement._prepare(sql)
                if cache_statement and not self._drcp_establish_session \
                        and not statement._is_ddl \
                        and self._statement_cache_size > 0:
                    statement._return_to_cache = True
                    self._statement_cache[sql] = statement
                    self._adjust_statement_cache()
            elif statement._in_use or not cache_statement \
                    or self._drcp_establish_session:
                if not cache_statement:
                    del self._statement_cache[sql]
                    statement._return_to_cache = False
                if statement._in_use or self._drcp_establish_session:
                    statement = statement.copy()
            else:
                self._statement_cache.move_to_end(sql)
            statement._in_use = True
            return statement

    cdef int _reset_statement_cache(self) except -1:
        """
        Reset the statement cache. This clears all statements and the list of
        cursors that need to be cleared.
        """
        with self._statement_cache_lock:
            self._statement_cache.clear()
            self._num_cursors_to_close = 0

    cdef int _return_statement(self, Statement statement) except -1:
        """
        Return the statement to the statement cache, if applicable. If the
        statement must not be returned to the statement cache, add the cursor
        id to the list of cursor ids to close on the next round trip to the
        database. Clear all bind variables and fetch variables in order to
        ensure that unnecessary references are not retained.
        """
        cdef:
            ThinVarImpl var_impl
            BindInfo bind_info
        if statement._bind_info_list is not None:
            for bind_info in statement._bind_info_list:
                bind_info._bind_var_impl = None
        if statement._fetch_var_impls is not None:
            for var_impl in statement._fetch_var_impls:
                var_impl._values = [None] * var_impl.num_elements
        with self._statement_cache_lock:
            if statement._return_to_cache:
                statement._in_use = False
            elif statement._cursor_id != 0:
                self._add_cursor_to_close(statement)

    def cancel(self):
        self._protocol._break_external()

    def change_password(self, str old_password, str new_password):
        cdef ChangePasswordMessage message
        message = self._create_message(ChangePasswordMessage)
        message.password = old_password.encode()
        message.newpassword = new_password.encode()
        self._protocol._process_single_message(message)

    def close(self, bint in_del=False):
        try:
            self._protocol._close(self)
        except (ssl.SSLError, exceptions.DatabaseError):
            pass

    def commit(self):
        cdef Message message
        message = self._create_message(CommitMessage)
        self._protocol._process_single_message(message)

    def connect(self, ConnectParamsImpl params):
        params._check_credentials()
        self._connection_id = base64.b64encode(secrets.token_bytes(16)).decode()
        try:
            self._connect_with_params(params)
            self._statement_cache = collections.OrderedDict()
            self._statement_cache_size = params.stmtcachesize
            self._statement_cache_lock = threading.Lock()
            self._dbobject_type_cache_num = create_new_dbobject_type_cache(self)
            self._cursors_to_close = array.array('I')
            array.resize(self._cursors_to_close, TNS_MAX_CURSORS_TO_CLOSE)
            self.invoke_session_callback = True
        except:
            self._force_close()
            raise

    def create_cursor_impl(self):
        return ThinCursorImpl.__new__(ThinCursorImpl, self)

    def create_temp_lob_impl(self, DbType dbtype):
        return ThinLobImpl._create(self, dbtype)

    def get_call_timeout(self):
        return self._call_timeout

    def get_current_schema(self):
        return self._current_schema

    def get_edition(self):
        return self._edition

    def get_external_name(self):
        return self._external_name

    def get_instance_name(self):
        return self._instance_name

    def get_internal_name(self):
        return self._internal_name

    def get_is_healthy(self):
        return self._protocol._socket is not None \
                and not self._protocol._read_buf._session_needs_to_be_closed

    def get_ltxid(self):
        return self._ltxid or b''

    def get_stmt_cache_size(self):
        return self._statement_cache_size

    def get_type(self, object conn, str name):
        cdef ThinDbObjectTypeCache cache = \
                get_dbobject_type_cache(self._dbobject_type_cache_num)
        return cache.get_type(conn, name)

    def get_version(self):
        return self._server_version

    def ping(self):
        cdef Message message
        message = self._create_message(PingMessage)
        self._protocol._process_single_message(message)

    def rollback(self):
        cdef Message message
        message = self._create_message(RollbackMessage)
        self._protocol._process_single_message(message)

    def set_action(self, str value):
        self._action = value
        self._action_modified = True

    def set_call_timeout(self, uint32_t value):
        timeout = None if value == 0 else value / 1000
        self._protocol._socket.settimeout(timeout)
        self._call_timeout = value

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
        self._statement_cache_size = value
        self._adjust_statement_cache()
