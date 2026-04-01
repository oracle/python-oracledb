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
# notification.pyx
#
# Cython file defining the messages that are sent to the database and the
# responses that are received by the client for notifying subscriber for an
# AQ Queue.
# (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

@cython.final
cdef class NotifyMessage(AqBaseMessage):
    cdef:
        uint32_t namespace
        bytes client_id
        object subscr

    cdef int _initialize_hook(self) except -1:
        """
        Perform initialization.
        """
        self.function_code = TNS_FUNC_NOTIFY

    cdef int _process_message(self, ReadBuffer buf,
                              uint8_t message_type) except -1:
        """
        Processes a single TTC message. In this case, notification only
        supports one message type and all others will result in an error.
        """
        if message_type == TNS_MSG_TYPE_OAC:
            while not self.end_of_response:
                self._process_oac(buf)
            self.subscr._impl = None
        else:
            errors._raise_err(errors.ERR_MESSAGE_TYPE_UNKNOWN,
                              message_type=message_type,
                              position=buf._pos - 1)

    cdef int _process_oac(self, ReadBuffer buf) except -1:
        """
        Processes the record returned by the server.
        """
        cdef:
            uint32_t message_type, num_props
            ThinMsgPropsImpl props_impl
            object py_message

        # create a new message that will be supplied as the argument to the
        # user's callback
        py_message = PY_TYPE_MESSAGE(self.subscr)
        py_message._dbname = self.conn_impl._db_name

        # first part is the notification header
        buf.read_ub4(&message_type)
        if message_type == TNS_SUBSCR_STOP_NOTIF:
            self.end_of_response = True
            return 0
        buf.skip_ub4()                  # error code
        buf.skip_ub4()                  # registration ID
        py_message._queue_name = buf.read_str_with_length()
        py_message._consumer_name = buf.read_str_with_length()

        # second part is the message properties
        py_message._msgid = buf.read_bytes_with_length()
        buf.read_ub4(&num_props)
        if num_props > 0:
            props_impl = ThinMsgPropsImpl.__new__(ThinMsgPropsImpl)
            buf.skip_ub1()              # skip invalid length
            self._process_msg_props(buf, props_impl)
        buf.skip_bytes_with_length()    # JMS message properties

        # third part is the payload (not for AQ without a flag which is
        # currently not supported by the driver)
        payload = None
        if self.namespace != SUBSCR_NAMESPACE_AQ:
            buf.skip_ub4()                  # payload type
            buf.skip_ub4()                  # payload flags
            buf.skip_ub4()                  # chunk number
            payload = buf.read_bytes_with_length()
            buf.skip_bytes_with_length()    # DbObject/JSON payload
        self._process_notification_payload(payload, py_message)

        # invoke the callback with the message that was created
        self.subscr.callback(py_message)

    cdef int _process_notification_payload(self, bytes payload,
                                           object py_message) except -1:
        """
        Processes the payload and populates the message that will be sent to
        the callback.
        """
        cdef:
            uint32_t registration_id, event_type
            uint16_t version, dbname_length
            const char_type* dbname_ptr
            Buffer buf

        # the payload is ignored for AQ notification
        if self.namespace == SUBSCR_NAMESPACE_AQ:
            py_message._type = EVENT_AQ

        # if the payload is empty for database/query change notification, the
        # registration has been discarded so mark the subscription as invalid
        # and cause the loop to terminate
        elif payload is None:
            py_message._type = EVENT_DEREG
            self.end_of_response = True

        # process the payload which contains information about the
        # database/query change notification
        else:
            if self.subscr.qos & SUBSCR_QOS_DEREG_NFY:
                py_message._registered = False
                self.end_of_response = True
            else:
                py_message._registered = True
            buf = Buffer.__new__(Buffer)
            buf._populate_from_bytes(payload)
            buf.read_uint16be(&version)
            buf.read_uint32be(&registration_id)
            buf.read_uint32be(&event_type)
            py_message._type = event_type
            buf.read_uint16be(&dbname_length)
            dbname_ptr = buf.read_raw_bytes(dbname_length)
            py_message._dbname = dbname_ptr[:dbname_length].decode()
            buf.skip_raw_bytes(14)          # skip transaction id and SCN
            if event_type == EVENT_OBJCHANGE:
                self._process_tables(buf, py_message._tables)
            elif event_type == EVENT_QUERYCHANGE:
                self._process_queries(buf, py_message._queries)

    cdef int _process_queries(self, Buffer buf, list queries) except -1:
        """
        Processes the queries found in the notification.
        """
        cdef:
            uint32_t query_id_msb, query_id_lsb, operation
            uint16_t num_queries, i
            object py_query
        buf.read_uint16be(&num_queries)
        for i in range(num_queries):
            py_query = PY_TYPE_MESSAGE_QUERY()
            buf.read_uint32be(&query_id_lsb)
            buf.read_uint32be(&query_id_msb)
            py_query._id = (<uint64_t> query_id_msb) << 32 | query_id_lsb
            buf.read_uint32be(&operation)
            py_query._operation = operation
            self._process_tables(buf, py_query._tables)
            queries.append(py_query)

    cdef int _process_rows(self, Buffer buf, list rows) except -1:
        """
        Processes the rows found in the notification.
        """
        cdef:
            uint16_t rowid_len, num_rows, i
            const char_type* rowid_ptr
            uint32_t operation
            object py_row
        buf.read_uint16be(&num_rows)
        for i in range(num_rows):
            py_row = PY_TYPE_MESSAGE_ROW()
            buf.read_uint32be(&operation)
            py_row._operation = operation
            buf.read_uint16be(&rowid_len)
            rowid_ptr = buf.read_raw_bytes(rowid_len)
            py_row._rowid = rowid_ptr[:rowid_len].decode()
            rows.append(py_row)

    cdef int _process_tables(self, Buffer buf, list tables) except -1:
        """
        Processes the tables found in the notification.
        """
        cdef:
            uint16_t num_tables, i, table_name_len
            const char_type* table_name_ptr
            uint32_t operation, object_num
            object py_table
        buf.read_uint16be(&num_tables)
        for i in range(num_tables):
            py_table = PY_TYPE_MESSAGE_TABLE()
            buf.read_uint32be(&operation)
            py_table._operation = operation
            buf.read_uint16be(&table_name_len)
            table_name_ptr = buf.read_raw_bytes(table_name_len)
            py_table._name = table_name_ptr[:table_name_len].decode()
            buf.read_uint32be(&object_num)
            if operation & OPCODE_ALLROWS == 0:
                self._process_rows(buf, py_table._rows)
            tables.append(py_table)

    cdef int _write_message(self, WriteBuffer buf) except -1:
        """
        Write message to the network buffers.
        """
        buf._data_flags = TNS_DATA_FLAGS_END_OF_REQUEST
        self._write_function_code(buf)
        buf.write_ub4(len(self.client_id))
        buf.write_bytes_with_length(self.client_id)
        buf.write_uint8(TNS_INIT_KPNDRREQ)
        buf.write_ub4(0)
