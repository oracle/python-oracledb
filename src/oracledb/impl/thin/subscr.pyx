#------------------------------------------------------------------------------
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
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
# subscr.pyx
#
# Cython file defining the thin Subscription implementation class (embedded in
# thin_impl.pyx).
#------------------------------------------------------------------------------

cdef class ThinSubscrImpl(BaseSubscrImpl):

    cdef:
        ThinConnImpl _conn_impl
        bytes _client_id
        object _bg_task
        object _bg_task_exc

    cdef SubscrMessage _create_subscr_message(self, ThinConnImpl conn_impl,
                                              uint8_t opcode):
        """
        Create the message for creating the subscription.
        """
        cdef SubscrMessage message
        message = conn_impl._create_message(SubscrMessage, "subscribe")
        message.subscr_impl = self
        message.opcode = opcode
        return message

    def _bg_task_func(self, object subscr, ThinConnImpl conn_impl,
                      object event):
        """
        Method which runs in a dedicated thread and is used to establish a
        separate connection to the database (which uses the EMON process) and
        wait for notifications. Notifications are sent in response to a single
        message sent to the database. The database never sends back a
        notification that no further messages will be sent, so the background
        wait is interrupted by forcing the socket closed. This results in an
        exception which is ignored if unsubscription is in progress.
        """
        cdef:
            NotifyMessage message
            Protocol protocol
        self._conn_impl = ThinConnImpl()
        try:
            self._conn_impl.process_sync_operation(
                self, "create_connection", (conn_impl,), {},
            )
            protocol = <Protocol> self._conn_impl._protocol
            message = self._conn_impl._create_message(NotifyMessage, "notify")
            message.client_id = self._client_id
            message.subscr = subscr
            message.namespace = self.namespace
            message.send(protocol._write_buf)
            event.set()
            protocol._receive_packet(message, check_request_boundary=False)
            message.process(protocol._read_buf)
        except BaseException as e:
            self._bg_task_exc = e
            event.set()
        if self._conn_impl is not None:
            self._conn_impl._protocol._disconnect()

    def _create_connection(self, ThinConnImpl conn_impl):
        """
        Creates a separate connection to the database (which uses the EMON
        process).
        """
        cdef:
            ConnectParamsImpl params
            Description description
        params = conn_impl.connect_params.copy()
        params.operation_callback = None
        params.round_trip_callback = None
        for description in params.description_list.children:
            description.server_type = "emon"
        self._conn_impl.dsn = conn_impl.dsn
        self._conn_impl.connect_params = params
        yield from self._conn_impl.connect()
        self._conn_impl._send_ha_readiness = False

    def register_query(self, str sql, object args):
        """
        Internal method for registering a query.
        """
        cdef:
            ThinCursorImpl cursor_impl
            object cursor
        cursor = self.connection.cursor()
        cursor_impl = <ThinCursorImpl> cursor._impl
        cursor_impl._prepare_for_execute(cursor, sql, args, None)
        if not cursor_impl._statement._is_query:
            errors._raise_err(errors.ERR_NOT_A_QUERY)
        cursor_impl._registration_id = self.id
        yield from cursor_impl.execute(cursor)
        return cursor_impl._query_id

    def subscribe(self, object subscr, ThinConnImpl conn_impl):
        """
        Internal method for creating the subscription.
        """
        cdef SubscrMessage message
        if self.namespace == SUBSCR_NAMESPACE_AQ and not self.qos:
            self.qos = TNS_SUBSCR_QOS_SECURE
        message = self._create_subscr_message(conn_impl,
                                              TNS_SUBSCR_OP_REGISTER)
        yield message
        self._client_id = message.client_id
        self.id = message.registration_id
        event = threading.Event()
        self._bg_task = threading.Thread(target=self._bg_task_func,
                                         args=(subscr, conn_impl, event))
        self._bg_task.daemon = True
        self._bg_task.start()
        event.wait()
        if self._bg_task_exc is not None:
            errors._raise_err(
                errors.ERR_SUBSCR_FAILED,
                cause=self._bg_task_exc
            )

    def unsubscribe(self, object subscr, ThinConnImpl conn_impl):
        """
        Internal method for destroying the subscription.
        """
        cdef:
            ThinConnImpl notification_conn_impl
            SubscrMessage message
        message = self._create_subscr_message(conn_impl,
                                              TNS_SUBSCR_OP_UNREGISTER)
        message.registration_id = self.id
        message.client_id = self._client_id
        yield message
        notification_conn_impl = self._conn_impl
        self._conn_impl = None
        notification_conn_impl._close_socket()
        self._bg_task.join()
