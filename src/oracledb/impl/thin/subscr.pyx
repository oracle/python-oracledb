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

cdef class BaseThinSubscrImpl(BaseSubscrImpl):

    cdef:
        ThinConnImpl _conn_impl
        bytes _client_id
        object _bg_task
        object _bg_task_exc

    cdef SubscrMessage _create_subscr_message(self, BaseThinConnImpl conn_impl,
                                              uint8_t opcode):
        """
        Create the message for creating the subscription.
        """
        cdef SubscrMessage message
        message = conn_impl._create_message(SubscrMessage)
        message.subscr_impl = self
        message.opcode = opcode
        return message


cdef class ThinSubscrImpl(BaseThinSubscrImpl):

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
            ConnectParamsImpl params
            Description description
            NotifyMessage message
            Protocol protocol
        params = conn_impl._connect_params.copy()
        for description in params.description_list.children:
            description.server_type = "emon"
        self._conn_impl = ThinConnImpl(conn_impl.dsn, params)
        try:
            self._conn_impl.connect(params)
            protocol = <Protocol> self._conn_impl._protocol
            message = self._conn_impl._create_message(NotifyMessage)
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

    def register_query(self, str sql, object args):
        """
        Internal method for registering a query.
        """
        cdef:
            ThinCursorImpl cursor_impl
            object cursor
        cursor = self.connection.cursor()
        cursor._prepare_for_execute(sql, args)
        cursor_impl = <ThinCursorImpl> cursor._impl
        if not cursor_impl._statement._is_query:
            errors._raise_err(errors.ERR_NOT_A_QUERY)
        cursor_impl._registration_id = self.id
        cursor_impl.execute(cursor)
        return cursor_impl._query_id

    def subscribe(self, object subscr, BaseThinConnImpl conn_impl):
        """
        Internal method for creating the subscription.
        """
        cdef:
            Protocol protocol = <Protocol> conn_impl._protocol
            SubscrMessage message
        if self.namespace == SUBSCR_NAMESPACE_AQ and not self.qos:
            self.qos = TNS_SUBSCR_QOS_SECURE
        message = self._create_subscr_message(conn_impl,
                                              TNS_SUBSCR_OP_REGISTER)
        protocol._process_single_message(message)
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
            Protocol protocol = <Protocol> conn_impl._protocol
            ThinConnImpl notification_conn_impl
            SubscrMessage message
        message = self._create_subscr_message(conn_impl,
                                              TNS_SUBSCR_OP_UNREGISTER)
        message.registration_id = self.id
        message.client_id = self._client_id
        protocol._process_single_message(message)
        notification_conn_impl = self._conn_impl
        self._conn_impl = None
        notification_conn_impl._close_socket()
        self._bg_task.join()
