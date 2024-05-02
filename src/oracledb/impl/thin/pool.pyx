#------------------------------------------------------------------------------
# Copyright (c) 2020, 2024, Oracle and/or its affiliates.
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

cdef class BaseThinPoolImpl(BasePoolImpl):

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
        object _bg_task
        object _bg_task_condition
        object _condition
        object _timeout_task
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

    cdef int _check_connection(self, BaseThinConnImpl conn_impl,
                               bint *requires_ping) except -1:
        """
        Checks the connection to see if it can be used. First, if any control
        packets are sent that indicate that the connection should be closed,
        the connection is indeed closed. After that, a flag is updated to the
        caller indicating that a ping is required according to the pool
        configuration.
        """
        cdef:
            ReadBuffer buf = conn_impl._protocol._read_buf
            double elapsed_time
            bint has_data_ready
        requires_ping[0] = False
        if not buf._transport._is_async:
            while not buf._session_needs_to_be_closed:
                buf._transport.has_data_ready(&has_data_ready)
                if not has_data_ready:
                    break
                buf.check_control_packet()
        if buf._session_needs_to_be_closed:
            conn_impl._force_close()
        else:
            if self._ping_interval == 0:
                requires_ping[0] = True
            elif self._ping_interval > 0:
                elapsed_time = time.monotonic() - conn_impl._time_in_pool
                if elapsed_time > self._ping_interval:
                    requires_ping[0] = True

    cdef int _check_timeout(self) except -1:
        """
        Checks whether a timeout is in effect and that the number of
        connections exceeds the minimum and if so, starts a timer to check
        if these connections have expired. Only one task is ever started.
        The timeout value is increased by a second to allow for small time
        discrepancies.
        """
        if self._timeout_task is None and self._timeout > 0 \
                and self.get_open_count() > self.min:
            self._start_timeout_task()

    cdef int _close_helper(self, bint force) except -1:
        """
        Helper function that closes all of the connections in the pool.
        """
        cdef BaseThinConnImpl conn_impl

        # if force parameter is not True and busy connections exist in the
        # pool, raise an exception
        if not force and self.get_busy_count() > 0:
            errors._raise_err(errors.ERR_POOL_HAS_BUSY_CONNECTIONS)

        # close all connections in the pool; this is done by simply adding
        # to the list of connections that require closing and then notifying
        # the background task to perform the work
        self._open = False
        for lst in (self._free_used_conn_impls,
                    self._free_new_conn_impls,
                    self._busy_conn_impls,
                    self._extra_conn_impls):
            self._conn_impls_to_drop.extend(lst)
            for conn_impl in lst:
                conn_impl._pool = None
            lst.clear()
        self._notify_bg_task()

    cdef int _drop_conn_impl(self, BaseThinConnImpl conn_impl) except -1:
        """
        Helper method which adds a connection to the list of connections to be
        closed and notifies the background task.
        """
        conn_impl._pool = None
        if conn_impl._protocol._transport is not None:
            self._conn_impls_to_drop.append(conn_impl)
            self._notify_bg_task()

    cdef int _drop_conn_impls_helper(self, list conn_impls_to_drop) except -1:
        """
        Helper method which drops the requested list of connections. When the
        pool is closed, exceptions are ignored.
        """
        cdef BaseThinConnImpl conn_impl
        for conn_impl in conn_impls_to_drop:
            try:
                conn_impl._force_close()
            except Exception as e:
                if self._open:
                    self._bg_exc = e

    cdef object _get_acquire_predicate(self, ConnectParamsImpl params,
                                       bint* must_reconnect):
        """
        Returns the predicate used for waiting for a connection to be available
        in the pool with particular characteristics.
        """
        cdef:
            ConnectParamsImpl creation_params = self.connect_params
            bint wants_new, cclass_matches
            str pool_cclass, cclass
        cclass = params._default_description.cclass
        pool_cclass = creation_params._default_description.cclass
        wants_new = (params._default_description.purity == PURITY_NEW)
        cclass_matches = (cclass is None or cclass == pool_cclass)
        return lambda: self._get_connection(wants_new, cclass_matches,
                                            cclass, must_reconnect)

    cdef object _get_connection(self, bint wants_new, bint cclass_matches,
                                str cclass, bint* must_reconnect):
        """
        Returns a connection from the pool if one is available. If one is not
        available and a new connection needs to be created, the value True is
        returned.
        """
        cdef:
            BaseThinConnImpl conn_impl
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
        must_reconnect[0] = False
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

        # wake up the background task to create a connection if the pool
        # is not already full
        if open_count < self.max:
            self._notify_bg_task()

        # if getmode indicates waiting is undesirable, raise an exception now
        if self._getmode == POOL_GETMODE_NOWAIT:
            errors._raise_err(errors.ERR_POOL_NO_CONNECTION_AVAILABLE)

    cdef int _on_acquire_new(self, BaseThinConnImpl orig_conn_impl,
                             BaseThinConnImpl new_conn_impl) except -1:
        """
        Called when a new connection is created on acquire with the lock held.
        """
        if orig_conn_impl is not None:
            self._busy_conn_impls.append(new_conn_impl)
        else:
            new_conn_impl._is_pool_extra = True
            self._extra_conn_impls.append(new_conn_impl)

    def _process_timeout(self):
        """
        Processes the timeout after the timer task completes. Drops any free
        connections that have expired (while maintaining the minimum number of
        connections in the pool).
        """
        self._timeout_task = None
        self._timeout_helper(self._free_new_conn_impls)
        self._timeout_helper(self._free_used_conn_impls)
        self._check_timeout()

    cdef int _return_connection_helper(self,
                                       BaseThinConnImpl conn_impl) except -1:
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
            bint is_open = conn_impl._protocol._transport is not None
            BaseThinDbObjectTypeCache type_cache
            uint32_t open_count
            int cache_num
        if conn_impl._dbobject_type_cache_num > 0:
            cache_num = conn_impl._dbobject_type_cache_num
            type_cache = get_dbobject_type_cache(cache_num)
            type_cache._clear_cursors()
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
            conn_impl.warning = None
            self._free_used_conn_impls.append(conn_impl)
            conn_impl._time_in_pool = time.monotonic()
        self._check_timeout()
        self._condition.notify()

    cdef int _start_timeout_task(self) except -1:
        """
        Starts the task for checking timeouts (differs for sync and async).
        """
        pass

    cdef int _timeout_helper(self, list conn_impls_to_check) except -1:
        """
        Helper method which checks the list of connections to see if any
        connections have expired (while maintaining the minimum number of
        connections in the pool).
        """
        cdef BaseThinConnImpl conn_impl
        current_time = time.monotonic()
        while self.get_open_count() > self.min and conn_impls_to_check:
            conn_impl = conn_impls_to_check[0]
            if current_time - conn_impl._time_in_pool < self._timeout:
                break
            conn_impls_to_check.pop(0)
            self._drop_conn_impl(conn_impl)

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
            if self._getmode == POOL_GETMODE_TIMEDWAIT:
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
        else:
            self._wait_timeout = None


cdef class ThinPoolImpl(BaseThinPoolImpl):

    cdef:
        object _timer_thread

    def __init__(self, str dsn, PoolParamsImpl params):
        super().__init__(dsn, params)
        self._condition = threading.Condition()
        self._bg_task_condition = threading.Condition()
        self._bg_task = threading.Thread(target=self._bg_task_func)
        self._bg_task.start()

    def _bg_task_func(self):
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

        # add to the list of pools that require closing
        pools_to_close.add(self)

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

            # if pool has closed and no connections to drop, stop thread!
            if not self._open and not self._conn_impls_to_drop:
                break

            # otherwise, if nothing needed to be done, wait for notification
            if wait:
                with self._bg_task_condition:
                    self._bg_task_condition.wait()

        # remove from the list of pools that require closing
        pools_to_close.remove(self)

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

    def _notify_bg_task(self):
        """
        Notify the background task that work needs to be done.
        """
        with self._bg_task_condition:
            self._bg_task_condition.notify()

    cdef int _return_connection(self, BaseThinConnImpl conn_impl) except -1:
        """
        Returns the connection to the pool.
        """
        with self._condition:
            self._return_connection_helper(conn_impl)

    cdef int _start_timeout_task(self) except -1:
        """
        Starts the task for checking timeouts. The timeout value is increased
        by a second to allow for small time discrepancies.
        """
        def handler():
            with self._condition:
                self._process_timeout()
        self._timeout_task = threading.Timer(self._timeout + 1, handler)
        self._timeout_task.start()

    def acquire(self, ConnectParamsImpl params):
        """
        Internal method for acquiring a connection from the pool.
        """
        cdef:
            ThinConnImpl temp_conn_impl = None, conn_impl
            bint must_reconnect = False, requires_ping
            object result, predicate

        # if pool is closed, raise an exception
        if not self._open:
            errors._raise_err(errors.ERR_POOL_NOT_OPEN)

        # session tagging has not been implemented yet
        if params.tag is not None:
            raise NotImplementedError("Tagging has not been implemented yet")

        # loop until an acceptable connection is found
        predicate = self._get_acquire_predicate(params, &must_reconnect)
        while True:

            with self._condition:

                # if a connection is available from a previous iteration of the
                # loop, drop it from the pool
                if temp_conn_impl is not None:
                    self._drop_conn_impl(temp_conn_impl)

                # get a connection from the pool; if one is not immediately
                # available, wait as long as requested for one to be made
                # available; a return value of None indicates that no
                # connection was made available within the allotted time; a
                # value of True indicates that a new connection must be created
                self._num_waiters += 1
                try:
                    result = self._condition.wait_for(predicate,
                                                      self._wait_timeout)
                finally:
                    self._num_waiters -= 1
                if result is None:
                    errors._raise_err(errors.ERR_POOL_NO_CONNECTION_AVAILABLE)
                elif result is True:
                    temp_conn_impl = None
                    break
                temp_conn_impl = <ThinConnImpl> result
                if must_reconnect:
                    break

            # check the connection to see if it can be used
            self._check_connection(temp_conn_impl, &requires_ping)
            if requires_ping:
                try:
                    temp_conn_impl.ping()
                except exceptions.Error:
                    temp_conn_impl._force_close()
            if temp_conn_impl._protocol._transport is not None:
                with self._condition:
                    self._busy_conn_impls.append(temp_conn_impl)
                return temp_conn_impl

        # a new connection needs to be created
        conn_impl = self._create_conn_impl(params=params)
        with self._condition:
            self._on_acquire_new(temp_conn_impl, conn_impl)
        return conn_impl

    def close(self, bint force):
        """
        Internal method for closing the pool. Note that the thread to destroy
        pools gracefully may have already run, so if the close has already
        happened, nothing more needs to be done!
        """
        if self in pools_to_close:
            with self._condition:
                self._close_helper(force)
            self._bg_task.join()

    def drop(self, ThinConnImpl conn_impl):
        """
        Internal method for dropping a connection from the pool.
        """
        with self._condition:
            self._busy_conn_impls.remove(conn_impl)
            self._drop_conn_impl(conn_impl)
            self._condition.notify()


cdef class AsyncThinPoolImpl(BaseThinPoolImpl):

    cdef:
        object _bg_notify_task

    def __init__(self, str dsn, PoolParamsImpl params):
        super().__init__(dsn, params)
        self._condition = asyncio.Condition()
        self._bg_task_condition = asyncio.Condition()
        self._bg_task = asyncio.create_task(self._bg_task_func())

    async def _acquire_helper(self, ConnectParamsImpl params):
        """
        Helper function for acquiring a connection from the pool.
        """
        cdef:
            AsyncThinConnImpl temp_conn_impl = None, conn_impl
            bint must_reconnect = False, requires_ping
            object predicate, result

        # loop until an acceptable connection is found
        predicate = self._get_acquire_predicate(params, &must_reconnect)
        while True:

            async with self._condition:

                # if a connection is available from a previous iteration of the
                # loop, drop it from the pool
                if temp_conn_impl is not None:
                    self._drop_conn_impl(temp_conn_impl)

                # get a connection from the pool; if one is not immediately
                # available, wait as long as requested for one to be made
                # available; a return value of None indicates that no
                # connection was made available within the allotted time; a
                # value of True indicates that a new connection must be created
                self._num_waiters += 1
                try:
                    result = await self._condition.wait_for(predicate)
                finally:
                    self._num_waiters -= 1
                if result is None:
                    errors._raise_err(errors.ERR_POOL_NO_CONNECTION_AVAILABLE)
                elif result is True:
                    temp_conn_impl = None
                    break
                temp_conn_impl = <AsyncThinConnImpl> result
                if must_reconnect:
                    break

            # check the connection to see if it can be used
            self._check_connection(temp_conn_impl, &requires_ping)
            if requires_ping:
                try:
                    await temp_conn_impl.ping()
                except exceptions.Error:
                    temp_conn_impl._force_close()
            if temp_conn_impl._protocol._transport is not None:
                async with self._condition:
                    self._busy_conn_impls.append(temp_conn_impl)
                return temp_conn_impl

        # a new connection needs to be created
        conn_impl = await self._create_conn_impl(params=params)
        async with self._condition:
            self._on_acquire_new(temp_conn_impl, conn_impl)
        return conn_impl

    async def _bg_task_func(self):
        """
        Method which runs in a dedicated task and is used to create connections
        and close them when needed. When first started, it creates pool.min
        connections. After that, it creates pool.increment connections up to
        the value of pool.max when needed and destroys connections when needed.
        The thread terminates automatically when the pool is closed.
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
            async with self._condition:
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
                await self._create_conn_impls_helper()
                if num_to_create > 1:
                    self._check_timeout()

            # close connections, if needed
            if conn_impls_to_drop:
                wait = False
                self._drop_conn_impls_helper(conn_impls_to_drop)

            # if pool has closed and no connections to drop, stop thread!
            if not self._open and not self._conn_impls_to_drop:
                break

            # otherwise, if nothing needed to be done, wait for notification
            if wait:
                async with self._bg_task_condition:
                    await self._bg_task_condition.wait()

    async def _create_conn_impl(self, ConnectParamsImpl params=None):
        """
        Create a single connection using the pool's information. This
        connection may be placed in the pool or may be returned directly (such
        as when the pool is full and POOL_GETMODE_FORCEGET is being used).
        """
        cdef AsyncThinConnImpl conn_impl
        conn_impl = AsyncThinConnImpl(self.dsn, self.connect_params)
        conn_impl._cclass = self.connect_params._default_description.cclass
        if params is not None:
            conn_impl._cclass = params._default_description.cclass
        conn_impl._pool = self
        await conn_impl.connect(self.connect_params)
        conn_impl._time_in_pool = time.monotonic()
        return conn_impl

    async def _create_conn_impls_helper(self):
        """
        Helper method which creates the specified number of connections. In
        order to prevent the thread from dying, exceptions are captured and
        stored on the pool object. The next attempt to acquire a connection
        will return this exception.
        """
        cdef:
            AsyncThinConnImpl conn_impl
            object exc
        while self._num_to_create > 0:
            conn_impl = None
            try:
                conn_impl = await self._create_conn_impl()
            except Exception as e:
                exc = e
            async with self._condition:
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

    def _notify_bg_task(self):
        """
        Notify the background task that work needs to be done.
        """
        if self._bg_notify_task is None or self._bg_notify_task.done():
            async def helper():
                async with self._bg_task_condition:
                    self._bg_task_condition.notify()
            self._bg_notify_task = asyncio.create_task(helper())

    async def _return_connection(self, BaseThinConnImpl conn_impl):
        """
        Returns the connection to the pool.
        """
        async with self._condition:
            self._return_connection_helper(conn_impl)

    cdef int _start_timeout_task(self) except -1:
        """
        Starts the task for checking timeouts. The timeout value is increased
        by a second to allow for small time discrepancies.
        """
        async def process_timeout():
            await asyncio.sleep(self._timeout + 1)
            async with self._condition:
                self._process_timeout()
        self._timeout_task = asyncio.create_task(process_timeout())

    async def acquire(self, ConnectParamsImpl params):
        """
        Internal method for acquiring a connection from the pool.
        """

        # if pool is closed, raise an exception
        if not self._open:
            errors._raise_err(errors.ERR_POOL_NOT_OPEN)

        # session tagging has not been implemented yet
        if params.tag is not None:
            raise NotImplementedError("Tagging has not been implemented yet")

        # use the helper function to allow for a timeout since asyncio
        # condition variables do not have that capability directly
        return await asyncio.wait_for(self._acquire_helper(params),
                                      self._wait_timeout)

    async def close(self, bint force):
        """
        Internal method for closing the pool.
        """
        async with self._condition:
            self._close_helper(force)
        await self._bg_task

    async def drop(self, AsyncThinConnImpl conn_impl):
        """
        Internal method for dropping a connection from the pool.
        """
        async with self._condition:
            self._busy_conn_impls.remove(conn_impl)
            self._drop_conn_impl(conn_impl)
            self._condition.notify()

# keep track of which pools need to be closed and ensure that they are closed
# gracefully when the main thread finishes its work
pools_to_close = set()
def close_pools_gracefully():
    cdef ThinPoolImpl pool_impl
    threading.main_thread().join()          # wait for main thread to finish
    for pool_impl in list(pools_to_close):
        pool_impl.close(True)
threading.Thread(target=close_pools_gracefully).start()
