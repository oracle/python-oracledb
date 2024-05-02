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
# connection.pyx
#
# Cython file defining the base Connection implementation class (embedded in
# base_impl.pyx).
#------------------------------------------------------------------------------

cdef class BaseConnImpl:

    def __init__(self, str dsn, ConnectParamsImpl params):
        self.dsn = dsn
        self.username = params.user
        self.proxy_user = params.proxy_user
        self._oson_max_fname_size = 255

    cdef object _check_value(self, DbType dbtype, BaseDbObjectTypeImpl objtype,
                             object value, bint* is_ok):
        """
        Checks that the specified Python value is acceptable for the given
        database type. If the "is_ok" parameter is passed as NULL, an exception
        is raised.  The value to use is returned (possibly modified from the
        value passed in).
        """
        cdef:
            uint32_t db_type_num
            BaseLobImpl lob_impl

        # null values are always accepted
        if value is None:
            return value

        # check to see if the Python value is accepted and perform any
        # necessary adjustments
        db_type_num = dbtype.num
        if db_type_num in (DB_TYPE_NUM_NUMBER,
                           DB_TYPE_NUM_BINARY_INTEGER,
                           DB_TYPE_NUM_BINARY_DOUBLE,
                           DB_TYPE_NUM_BINARY_FLOAT):
            if isinstance(value, (PY_TYPE_BOOL, int, float, PY_TYPE_DECIMAL)):
                if db_type_num in (DB_TYPE_NUM_BINARY_FLOAT,
                                   DB_TYPE_NUM_BINARY_DOUBLE):
                    return float(value)
                elif db_type_num == DB_TYPE_NUM_BINARY_INTEGER \
                        or cpython.PyBool_Check(value):
                    return int(value)
                return value
        elif db_type_num in (DB_TYPE_NUM_CHAR,
                             DB_TYPE_NUM_VARCHAR,
                             DB_TYPE_NUM_NCHAR,
                             DB_TYPE_NUM_NVARCHAR,
                             DB_TYPE_NUM_LONG_VARCHAR,
                             DB_TYPE_NUM_LONG_NVARCHAR):
            if isinstance(value, bytes):
                return (<bytes> value).decode()
            elif isinstance(value, str):
                return value
        elif db_type_num in (DB_TYPE_NUM_RAW, DB_TYPE_NUM_LONG_RAW):
            if isinstance(value, str):
                return (<str> value).encode()
            elif isinstance(value, bytes):
                return value
        elif db_type_num in (DB_TYPE_NUM_DATE,
                             DB_TYPE_NUM_TIMESTAMP,
                             DB_TYPE_NUM_TIMESTAMP_LTZ,
                             DB_TYPE_NUM_TIMESTAMP_TZ):
            if cydatetime.PyDateTime_Check(value) \
                    or cydatetime.PyDate_Check(value):
                return value
        elif db_type_num == DB_TYPE_NUM_INTERVAL_DS:
            if isinstance(value, PY_TYPE_TIMEDELTA):
                return value
        elif db_type_num in (DB_TYPE_NUM_CLOB,
                             DB_TYPE_NUM_NCLOB,
                             DB_TYPE_NUM_BLOB):
            if isinstance(value, (PY_TYPE_LOB, PY_TYPE_ASYNC_LOB)):
                lob_impl = value._impl
                if lob_impl.dbtype is not dbtype:
                    if is_ok != NULL:
                        is_ok[0] = False
                        return value
                    errors._raise_err(errors.ERR_LOB_OF_WRONG_TYPE,
                                      actual_type_name=lob_impl.dbtype.name,
                                      expected_type_name=dbtype.name)
                return value
            elif self._allow_bind_str_to_lob \
                    and isinstance(value, (bytes, str)):
                if db_type_num == DB_TYPE_NUM_BLOB:
                    if isinstance(value, str):
                        value = value.encode()
                elif isinstance(value, bytes):
                    value = value.decode()
                lob_impl = self.create_temp_lob_impl(dbtype)
                if value:
                    lob_impl.write(value, 1)
                return PY_TYPE_LOB._from_impl(lob_impl)
        elif db_type_num == DB_TYPE_NUM_OBJECT:
            if isinstance(value, PY_TYPE_DB_OBJECT):
                if value._impl.type != objtype:
                    if is_ok != NULL:
                        is_ok[0] = False
                        return value
                    errors._raise_err(errors.ERR_WRONG_OBJECT_TYPE,
                                      actual_schema=value.type.schema,
                                      actual_name=value.type.name,
                                      expected_schema=objtype.schema,
                                      expected_name=objtype.name)
                return value
        elif db_type_num == DB_TYPE_NUM_CURSOR:
            if isinstance(value, (PY_TYPE_CURSOR, PY_TYPE_ASYNC_CURSOR)):
                return value
        elif db_type_num == DB_TYPE_NUM_BOOLEAN:
            return bool(value)
        elif db_type_num == DB_TYPE_NUM_JSON:
            return value
        elif db_type_num == DB_TYPE_NUM_VECTOR:
            if isinstance(value, list):
                if len(value) == 0:
                    errors._raise_err(errors.ERR_INVALID_VECTOR)
                return array.array('d', value)
            elif isinstance(value, array.array) \
                    and value.typecode in ('f', 'd', 'b'):
                if len(value) == 0:
                    errors._raise_err(errors.ERR_INVALID_VECTOR)
                return value
        elif db_type_num == DB_TYPE_NUM_INTERVAL_YM:
            if isinstance(value, PY_TYPE_INTERVAL_YM):
                return value
        else:
            if is_ok != NULL:
                is_ok[0] = False
                return value
            errors._raise_err(errors.ERR_UNSUPPORTED_TYPE_SET,
                              db_type_name=dbtype.name)

        # the Python value was not considered acceptable
        if is_ok != NULL:
            is_ok[0] = False
            return value
        errors._raise_err(errors.ERR_UNSUPPORTED_PYTHON_TYPE_FOR_DB_TYPE,
                          py_type_name=type(value).__name__,
                          db_type_name=dbtype.name)

    cdef BaseCursorImpl _create_cursor_impl(self):
        """
        Internal method for creating an empty cursor implementation object.
        """
        raise NotImplementedError()

    @utils.CheckImpls("getting a connection OCI attribute")
    def _get_oci_attr(self, uint32_t handle_type, uint32_t attr_num,
                      uint32_t attr_type):
        pass

    @utils.CheckImpls("setting a connection OCI attribute")
    def _set_oci_attr(self, uint32_t handle_type, uint32_t attr_num,
                      uint32_t attr_type, object value):
        pass

    @utils.CheckImpls("aborting a currently executing statement")
    def cancel(self):
        pass

    @utils.CheckImpls("changing a password")
    def change_password(self, old_password, new_password):
        pass

    def decode_oson(self, bytes data):
        """
        Decode OSON encoded bytes and return the object encoded in them.
        """
        cdef OsonDecoder decoder = OsonDecoder.__new__(OsonDecoder)
        return decoder.decode(data)

    def encode_oson(self, object value):
        """
        Return OSON encoded bytes encoded from the supplied object.
        """
        cdef OsonEncoder encoder = OsonEncoder.__new__(OsonEncoder)
        encoder.encode(value, self._oson_max_fname_size)
        return encoder._data[:encoder._pos]

    @utils.CheckImpls("checking if the connection is healthy")
    def get_is_healthy(self):
        pass

    @utils.CheckImpls("closing a connection")
    def close(self, in_del=False):
        pass

    @utils.CheckImpls("committing a transaction")
    def commit(self):
        pass

    def create_cursor_impl(self, bint scrollable):
        """
        Create the cursor implementation object.
        """
        cdef BaseCursorImpl cursor_impl = self._create_cursor_impl()
        cursor_impl.scrollable = scrollable
        cursor_impl.arraysize = C_DEFAULTS.arraysize
        cursor_impl.prefetchrows = C_DEFAULTS.prefetchrows
        return cursor_impl

    @utils.CheckImpls("creating a queue")
    def create_queue_impl(self):
        pass

    @utils.CheckImpls("creating a SODA database object")
    def create_soda_database_impl(self, conn):
        pass

    @utils.CheckImpls("creating a subscription")
    def create_subscr_impl(self, object conn, object callback,
                           uint32_t namespace, str name, uint32_t protocol,
                           str ip_address, uint32_t port, uint32_t timeout,
                           uint32_t operations, uint32_t qos,
                           uint8_t grouping_class, uint32_t grouping_value,
                           uint8_t grouping_type, bint client_initiated):
        pass

    @utils.CheckImpls("creating a temporary LOB")
    def create_temp_lob_impl(self, DbType dbtype):
        pass

    @utils.CheckImpls("getting the call timeout")
    def get_call_timeout(self):
        pass

    @utils.CheckImpls("getting the current schema")
    def get_current_schema(self):
        pass

    @utils.CheckImpls("getting the database domain name")
    def get_db_domain(self):
        pass

    @utils.CheckImpls("getting the database name")
    def get_db_name(self):
        pass

    @utils.CheckImpls("getting the edition")
    def get_edition(self):
        pass

    @utils.CheckImpls("getting the external name")
    def get_external_name(self):
        pass

    @utils.CheckImpls("getting the OCI service context handle")
    def get_handle(self):
        pass

    @utils.CheckImpls("getting the instance name")
    def get_instance_name(self):
        pass

    @utils.CheckImpls("getting the internal name")
    def get_internal_name(self):
        pass

    @utils.CheckImpls("getting the logical transaction id")
    def get_ltxid(self):
        pass

    @utils.CheckImpls("getting the maximum number of open cursors")
    def get_max_open_cursors(self):
        pass

    @utils.CheckImpls("getting the session data unit (SDU)")
    def get_sdu(self):
        pass

    @utils.CheckImpls("getting the service name")
    def get_service_name(self):
        pass

    @utils.CheckImpls("getting the statement cache size")
    def get_stmt_cache_size(self):
        pass

    @utils.CheckImpls("getting if a transaction is in progress")
    def get_transaction_in_progress(self):
        pass

    @utils.CheckImpls("getting an object type")
    def get_type(self, object conn, str name):
        pass

    @utils.CheckImpls("pinging the database")
    def ping(self):
        pass

    @utils.CheckImpls("rolling back a transaction")
    def rollback(self):
        pass

    @utils.CheckImpls("setting the action")
    def set_action(self, value):
        pass

    @utils.CheckImpls("setting the call timeout")
    def set_call_timeout(self, value):
        pass

    @utils.CheckImpls("setting the client identifier")
    def set_client_identifier(self, value):
        pass

    @utils.CheckImpls("setting the client info")
    def set_client_info(self, value):
        pass

    @utils.CheckImpls("setting the current schema")
    def set_current_schema(self, value):
        pass

    @utils.CheckImpls("setting the database operation")
    def set_dbop(self, value):
        pass

    @utils.CheckImpls("setting the execution context id")
    def set_econtext_id(self, value):
        pass

    @utils.CheckImpls("setting the external name")
    def set_external_name(self, value):
        pass

    @utils.CheckImpls("setting the internal name")
    def set_internal_name(self, value):
        pass

    @utils.CheckImpls("setting the module")
    def set_module(self, value):
        pass

    @utils.CheckImpls("setting the statement cache size")
    def set_stmt_cache_size(self, value):
        pass

    @utils.CheckImpls("shutting down the database")
    def shutdown(self, uint32_t mode):
        pass

    @utils.CheckImpls("starting up the database")
    def startup(self, bint force, bint restrict, str pfile):
        pass

    @utils.CheckImpls("starting a TPC (two-phase commit) transaction")
    def tpc_begin(self, xid, uint32_t flags, uint32_t timeout):
        pass

    @utils.CheckImpls("committing a TPC (two-phase commit) transaction")
    def tpc_commit(self, xid, bint one_phase):
        pass

    @utils.CheckImpls("ending a TPC (two-phase commit) transaction")
    def tpc_end(self, xid, uint32_t flags):
        pass

    @utils.CheckImpls("forgetting a TPC (two-phase commit) transaction")
    def tpc_forget(self, xid):
        pass

    @utils.CheckImpls("preparing a TPC (two-phase commit) transaction")
    def tpc_prepare(self, xid):
        pass

    @utils.CheckImpls("rolling back a TPC (two-phase commit) transaction")
    def tpc_rollback(self, xid):
        pass
