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
# pool.pyx
#
# Cython file defining the pool implementation class (embedded in
# thin_impl.pyx).
#------------------------------------------------------------------------------

cdef class ThinPoolImpl(BasePoolImpl):

    cdef:
        list _free_new_conn_impls
        list _free_used_conn_impls
        list _busy_conn_impls
        list _conn_impls_to_drop
        list _extra_conn_impls
        uint32_t _getmode
        uint32_t _stmt_cache_size
        uint32_t _timeout
        uint32_t _max_lifetime_session
        uint32_t _num_waiters
        uint32_t _auth_mode
        uint32_t _num_to_create
        int _ping_interval
        object _wait_timeout
        object _bg_exc
        object _bg_thread
        object _bg_thread_condition
        object _timer_thread
        object _condition
        bint _force_get
        bint _open

    def __init__(self, str dsn, PoolParamsImpl params):
        if not HAS_CRYPTOGRAPHY:
            errors._raise_err(errors.ERR_NO_CRYPTOGRAPHY_PACKAGE)
        params._check_credentials()
        self.connect_params = params
        self.username = params.user
        self.dsn = dsn
        self.min = params.min
        self.max = params.max
        self.increment = params.increment
        self.homogeneous = params.homogeneous
        self.set_getmode(params.getmode)
        self.set_wait_timeout(params.wait_timeout)
        self.set_timeout(params.timeout)
        self._stmt_cache_size = params.stmtcachesize
        self._ping_interval = params.ping_interval
        self._free_new_conn_impls = []
        self._free_used_conn_impls = []
        self._busy_conn_impls = []
        self._conn_impls_to_drop = []
        self._extra_conn_impls = []
        self._auth_mode = AUTH_MODE_DEFAULT
        self._open = True
        self._condition = threading.Condition()
        self._bg_thread_condition = threading.Condition()
        self._bg_thread = threading.Thread(target=self._bg_thread_func,
                                           daemon=True)
        self._bg_thread.start()

    cdef ThinConnImpl _create_conn_impl(self, ConnectParamsImpl params=None):
        """
        Create a single connection using the pool's information. This
        connection may be placed in the pool or may be returned directly (such
        as when the pool is full and POOL_GETMODE_FORCEGET is being used).
        """
        cdef ThinConnImpl conn_impl
        conn_impl = ThinConnImpl(self.dsn, self.connect_params)
        conn_impl._cclass = self.connect_params._default_description.cclass
        if params is not None:
            conn_impl._cclass = params._default_description.cclass
        conn_impl._pool = self
        conn_impl.connect(self.connect_params)
        conn_impl._time_in_pool = time.monotonic()
        return conn_impl

    def _bg_thread_func(self):
        """
        Method which runs in a dedicated thread and is used to create
        connections and close them when needed. When first started, it creates
        pool.min connections. After that, it creates pool.increment connections
        up to the value of pool.max when needed and destroys connections when
        needed. The thread terminates automatically when the pool is closed.
        """
        cdef:
            uint32_t open_count, num_to_create
            list conn_impls_to_drop
            bint wait

        # create connections and close connections as needed
        while True:
            conn_impls_to_drop = []
            wait = True

            # determine if there is any work to do
            with self._condition:
                open_count = self.get_open_count()
                if self._open and self._num_to_create == 0:
                    if open_count < self.min:
                        self._num_to_create = self.min - open_count
                    elif self._num_waiters > 0:
                        self._num_to_create = min(self.increment,
                                              self.max - open_count)
                if not self._open or self._bg_exc is None:
                    conn_impls_to_drop = self._conn_impls_to_drop
                    self._conn_impls_to_drop = []

            # create connections, if needed
            if self._num_to_create > 0:
                wait = False
                num_to_create = self._num_to_create
                self._create_conn_impls_helper()
                if num_to_create > 1:
                    self._check_timeout()

            # close connections, if needed
            if conn_impls_to_drop:
                wait = False
                self._drop_conn_impls_helper(conn_impls_to_drop)

            # if pool has closed, stop thread!
            if not self._open:
                break

            # otherwise, if nothing needed to be done, wait for notification
            if wait:
                with self._bg_thread_condition:
                    self._bg_thread_condition.wait()

    cdef int _check_timeout(self) except -1:
        """
        Checks whether a timeout is in effect and that the number of
        connections exceeds the minimum and if so, starts a timer to ensure
        if these connections have expired. Only one thread is ever started.
        The timeout value is increased by a second to allow for small time
        discrepancies.
        """
        if self._timer_thread is None and self._timeout > 0 \
                and self.get_open_count() > self.min:
            self._timer_thread = threading.Timer(self._timeout + 1,
                                                 self._process_timeout)
            self._timer_thread.start()

    cdef int _create_conn_impls_helper(self) except -1:
        """
        Helper method which creates the specified number of connections. In
        order to prevent the thread from dying, exceptions are captured and
        stored on the pool object. The next attempt to acquire a connection
        will return this exception.
        """
        cdef:
            ThinConnImpl conn_impl
            object exc
        while self._num_to_create > 0:
            conn_impl = None
            try:
                conn_impl = self._create_conn_impl()
            except Exception as e:
                exc = e
            with self._condition:
                if conn_impl is not None:
                    if self._open:
                        self._free_new_conn_impls.append(conn_impl)
                        self._num_to_create -= 1
                    else:
                        conn_impl._force_close()
                        break
                else:
                    self._bg_exc = exc
                self._condition.notify()
                if conn_impl is None:
                    break

    cdef int _drop_conn_impl(self, ThinConnImpl conn_impl) except -1:
        """
        Helper method which adds a connection to the list of connections to be
        closed and notifies the background thread.
        """
        if conn_impl._protocol._socket is not None:
            self._conn_impls_to_drop.append(conn_impl)
            with self._bg_thread_condition:
                self._bg_thread_condition.notify()

    cdef int _drop_conn_impls_helper(self, list conn_impls_to_drop) except -1:
        """
        Helper method which drops the requested list of connections. When the
        pool is closed, exceptions are ignored.
        """
        cdef ThinConnImpl conn_impl
        for conn_impl in conn_impls_to_drop:
            try:
                conn_impl._force_close()
            except Exception as e:
                if self._open:
                    self._bg_exc = e

    cdef object _get_connection(self, bint wants_new, bint cclass_matches,
                                str cclass, bint* must_reconnect):
        """
        Returns a connection from the pool if one is available. If one is not
        available and a new connection needs to be created, the value True is
        returned.
        """
        cdef:
            ThinConnImpl conn_impl
            uint32_t open_count
            object exc
            ssize_t i

        # if an exception was raised in the background thread, raise it now
        if self._bg_exc is not None:
            exc = self._bg_exc
            self._bg_exc = None
            raise exc

        # check for an available used connection (only permitted if a new
        # connection is not required); in addition, ensure that the cclass
        # matches
        if not wants_new and self._free_used_conn_impls:
            for i, conn_impl in enumerate(reversed(self._free_used_conn_impls)):
                if cclass is None or conn_impl._cclass == cclass:
                    i = len(self._free_used_conn_impls) - i - 1
                    self._free_used_conn_impls.pop(i)
                    return conn_impl

        # check for an available new connection (only permitted if the cclass
        # matches)
        if cclass_matches and self._free_new_conn_impls:
            return self._free_new_conn_impls.pop()

        # no matching connections are available; if the pool is full, see if
        # any connections are available and if so, return one of them (but let
        # the caller know that it must be discarded and a new connection
        # created); if no connections are available to replace but the force
        # get flag is set, return True which signals that a new "extra"
        # connection will be created; a new "extra" connection is also created
        # if the connection class doesn't match, since the background thread
        # will only create connections with the pool's connection class
        open_count = self.get_open_count() + self._num_to_create
        if open_count >= self.max:
            if self._free_new_conn_impls:
                must_reconnect[0] = True
                return self._free_new_conn_impls.pop()
            elif self._free_used_conn_impls:
                must_reconnect[0] = True
                return self._free_used_conn_impls.pop()
            elif self._force_get:
                return True
        elif not cclass_matches:
            return True

        # wake up the background thread to create a connection if the pool
        # is not already full
        if open_count < self.max:
            with self._bg_thread_condition:
                self._bg_thread_condition.notify()

    cdef ThinConnImpl _acquire_helper(self, ConnectParamsImpl params):
        cdef:
            ConnectParamsImpl creation_params = self.connect_params
            bint wants_new, cclass_matches, must_reconnect = False
            object result, predicate
            str pool_cclass, cclass
            ThinConnImpl conn_impl
            ssize_t i

        # initialize values used in determining which connection can be
        # returned from the pool
        cclass = params._default_description.cclass
        pool_cclass = creation_params._default_description.cclass
        wants_new = (params._default_description.purity == PURITY_NEW)
        cclass_matches = (cclass is None or cclass == pool_cclass)
        predicate = lambda: self._get_connection(wants_new, cclass_matches,
                                                 cclass, &must_reconnect)

        # get a connection from the pool; if one is not immediately available,
        # wait as long as requested for one to be made available.
        with self._condition:
            self._num_waiters += 1
            try:
                result = self._condition.wait_for(predicate,
                                                  self._wait_timeout)
            finally:
                self._num_waiters -= 1
            if result is None:
                errors._raise_err(errors.ERR_POOL_NO_CONNECTION_AVAILABLE)
            if isinstance(result, ThinConnImpl):
                self._busy_conn_impls.append(result)
                if not must_reconnect:
                    return result

        # no connection was returned from the pool so a new connection needs to
        # be created
        conn_impl = self._create_conn_impl(params=params)
        with self._condition:
            if must_reconnect:
                self._busy_conn_impls.remove(result)
                self._busy_conn_impls.append(conn_impl)
            else:
                conn_impl._is_pool_extra = True
                self._extra_conn_impls.append(conn_impl)
        return conn_impl

    def _process_timeout(self):
        """
        Processes the timeout after the timer thread expires. Drops any free
        connections that have expired (while maintaining the minimum number of
        connections in the pool).
        """
        self._timer_thread = None
        self._timeout_helper(self._free_new_conn_impls)
        self._timeout_helper(self._free_used_conn_impls)
        self._check_timeout()

    cdef int _return_connection(self, ThinConnImpl conn_impl) except -1:
        """
        Returns the connection to the pool. If the connection was closed for
        some reason it will be dropped; otherwise, it will be returned to the
        list of connections available for further use. If an "extra" connection
        was created (because the pool has a mode of "force" get or because a
        different connection class than that used by the pool was requested)
        then it will be added to the pool or will replace an unused new
        connection or will be discarded depending on the current pool size.
        """
        cdef:
            bint is_open = conn_impl._protocol._socket is not None
            ThinDbObjectTypeCache type_cache
            uint32_t open_count
            int cache_num
        with self._condition:
            if conn_impl._dbobject_type_cache_num > 0:
                cache_num = conn_impl._dbobject_type_cache_num
                type_cache = get_dbobject_type_cache(cache_num)
                type_cache._clear_meta_cursor()
            if conn_impl._is_pool_extra:
                self._extra_conn_impls.remove(conn_impl)
                conn_impl._is_pool_extra = False
                open_count = self.get_open_count() + self._num_to_create
                if is_open and open_count >= self.max:
                    if self._free_new_conn_impls and open_count == self.max:
                        self._drop_conn_impl(self._free_new_conn_impls.pop(0))
                    else:
                        self._drop_conn_impl(conn_impl)
                        is_open = False
            else:
                self._busy_conn_impls.remove(conn_impl)
            if is_open:
                self._free_used_conn_impls.append(conn_impl)
                conn_impl._time_in_pool = time.monotonic()
            self._check_timeout()
            self._condition.notify()

    cdef int _timeout_helper(self, list conn_impls_to_check) except -1:
        """
        Helper method which checks the list of connections to see if any
        connections have expired (while maintaining the minimum number of
        connections in the pool).
        """
        cdef ThinConnImpl conn_impl
        current_time = time.monotonic()
        while self.get_open_count() > self.min and conn_impls_to_check:
            conn_impl = conn_impls_to_check[0]
            if current_time - conn_impl._time_in_pool < self._timeout:
                break
            conn_impls_to_check.pop(0)
            self._drop_conn_impl(conn_impl)

    def acquire(self, ConnectParamsImpl params):
        """
        Internal method for acquiring a connection from the pool.
        """
        cdef:
            ThinConnImpl conn_impl
            double elapsed_time
            ReadBuffer read_buf
            bint requires_ping
            Message message

        # if pool is closed, raise an exception
        if not self._open:
            errors._raise_err(errors.ERR_POOL_NOT_OPEN)

        # session tagging has not been implemented yet
        if params.tag is not None:
            raise NotImplementedError("Tagging has not been implemented yet")

        # acquire a connection from the pool and perform a ping if the ping
        # interval is set to 0 or if the connection was previously used and
        # has been idle for a time greater than the value of ping interval
        while True:
            requires_ping = False
            conn_impl = self._acquire_helper(params)
            read_buf = conn_impl._protocol._read_buf
            if not read_buf._session_needs_to_be_closed:
                socket_list = [conn_impl._protocol._socket]
                while not read_buf._session_needs_to_be_closed:
                    read_socks, _, _ = select.select(socket_list, [], [], 0)
                    if not read_socks:
                        break
                    read_buf.check_control_packet()
            if read_buf._session_needs_to_be_closed:
                with self._condition:
                    self._busy_conn_impls.remove(conn_impl)
                    self._drop_conn_impl(conn_impl)
                continue
            if self._ping_interval == 0:
                requires_ping = True
            elif self._ping_interval > 0:
                elapsed_time = time.monotonic() - conn_impl._time_in_pool
                if elapsed_time > self._ping_interval:
                    requires_ping = True
            if not requires_ping:
                break
            try:
                message = conn_impl._create_message(PingMessage)
                conn_impl._protocol._process_message(message)
                break
            except exceptions.DatabaseError:
                with self._condition:
                    self._busy_conn_impls.remove(conn_impl)
                    self._drop_conn_impl(conn_impl)
        return conn_impl

    def close(self, bint force):
        """
        Internal method for closing the pool.
        """
        cdef:
            ThinConnImpl conn_impl

        with self._condition:

            # if force parameter is not True and busy connections exist in the
            # pool, raise an exception
            if not force and self.get_busy_count() > 0:
                errors._raise_err(errors.ERR_POOL_HAS_BUSY_CONNECTIONS)

            # close all connections in the pool; this is done by simply adding
            # to the list of connections that require closing and then waking
            # up the background thread to perform the work
            self._open = False
            for lst in (self._free_used_conn_impls,
                        self._free_new_conn_impls,
                        self._busy_conn_impls,
                        self._extra_conn_impls):
                self._conn_impls_to_drop.extend(lst)
                for conn_impl in lst:
                    conn_impl._pool = None
                lst.clear()
            with self._bg_thread_condition:
                self._bg_thread_condition.notify()

        # wait for background thread to complete its tasks
        self._bg_thread.join()

    def drop(self, ThinConnImpl conn_impl):
        """
        Internal method for dropping a connection from the pool.
        """
        with self._condition:
            self._busy_conn_impls.remove(conn_impl)
            conn_impl._pool = None
            self._drop_conn_impl(conn_impl)
            self._condition.notify()

    def get_busy_count(self):
        """
        Internal method for getting the number of busy connections in the pool.
        """
        return len(self._busy_conn_impls)

    def get_getmode(self):
        """
        Internal method for getting the method by which connections are
        acquired from the pool.
        """
        return self._getmode

    def get_max_lifetime_session(self):
        """
        Internal method for getting the maximum lifetime of each session.
        """
        return self._max_lifetime_session

    def get_open_count(self):
        """
        Internal method for getting the number of connections in the pool.
        """
        return len(self._busy_conn_impls) + \
               len(self._free_used_conn_impls) + \
               len(self._free_new_conn_impls)

    def get_ping_interval(self):
        """
        Internal method for getting the value of the pool-ping-interval.
        """
        return self._ping_interval

    def get_stmt_cache_size(self):
        """
        Internal method for getting the size of the statement cache.
        """
        return self._stmt_cache_size

    def get_timeout(self):
        """
        Internal method for getting the timeout for idle sessions.
        """
        return self._timeout

    def get_wait_timeout(self):
        """
        Internal method for getting the wait timeout for acquiring sessions.
        """
        if self._getmode == POOL_GETMODE_TIMEDWAIT:
            return self._wait_timeout
        return 0

    def set_getmode(self, uint32_t value):
        """
        Internal method for setting the method by which connections are
        acquired from the pool.
        """
        if self._getmode != value:
            self._getmode = value
            self._force_get = (self._getmode == POOL_GETMODE_FORCEGET)
            if self._getmode == POOL_GETMODE_TIMEDWAIT \
                    or self._getmode == POOL_GETMODE_NOWAIT:
                self._wait_timeout = 0
            else:
                self._wait_timeout = None

    def set_max_lifetime_session(self, uint32_t value):
        """
        Internal method for setting the maximum lifetime of each session.
        """
        self._max_lifetime_session = value

    def set_ping_interval(self, int value):
        """
        Internal method for setting the value of the pool-ping-interval.
        """
        self._ping_interval = value

    def set_stmt_cache_size(self, uint32_t value):
        """
        Internal method for setting the size of the statement cache.
        """
        self._stmt_cache_size = value

    def set_timeout(self, uint32_t value):
        """
        Internal method for setting the timeout for idle sessions.
        """
        self._timeout = value

    def set_wait_timeout(self, uint32_t value):
        """
        Internal method for setting the wait timeout for acquiring sessions.
        """
        if self._getmode == POOL_GETMODE_TIMEDWAIT:
            self._wait_timeout = value / 1000
        elif self._getmode == POOL_GETMODE_NOWAIT:
            self._wait_timeout = 0
        else:
            self._wait_timeout = None
