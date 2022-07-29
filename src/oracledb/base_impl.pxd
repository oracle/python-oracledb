#------------------------------------------------------------------------------
# Copyright (c) 2020, 2022, Oracle and/or its affiliates.
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
# base_impl.pxd
#
# Cython definition file defining the base classes from which the thick and
# thin implementations derive their classes.
#------------------------------------------------------------------------------

# cython: language_level=3

from libc.stdint cimport int8_t, int16_t, int32_t, int64_t
from libc.stdint cimport uint8_t, uint16_t, uint32_t, uint64_t

cdef enum:
    NUM_TYPE_FLOAT = 0
    NUM_TYPE_INT = 1
    NUM_TYPE_DECIMAL = 2
    NUM_TYPE_STR = 3

cdef enum:
    DB_TYPE_NUM_BFILE = 2020
    DB_TYPE_NUM_BINARY_DOUBLE = 2008
    DB_TYPE_NUM_BINARY_FLOAT = 2007
    DB_TYPE_NUM_BINARY_INTEGER = 2009
    DB_TYPE_NUM_BLOB = 2019
    DB_TYPE_NUM_BOOLEAN = 2022
    DB_TYPE_NUM_CHAR = 2003
    DB_TYPE_NUM_CLOB = 2017
    DB_TYPE_NUM_CURSOR = 2021
    DB_TYPE_NUM_DATE = 2011
    DB_TYPE_NUM_INTERVAL_DS = 2015
    DB_TYPE_NUM_INTERVAL_YM = 2016
    DB_TYPE_NUM_JSON = 2027
    DB_TYPE_NUM_LONG_NVARCHAR = 2031
    DB_TYPE_NUM_LONG_RAW = 2025
    DB_TYPE_NUM_LONG_VARCHAR = 2024
    DB_TYPE_NUM_NCHAR = 2004
    DB_TYPE_NUM_NCLOB = 2018
    DB_TYPE_NUM_NUMBER = 2010
    DB_TYPE_NUM_NVARCHAR = 2002
    DB_TYPE_NUM_OBJECT = 2023
    DB_TYPE_NUM_RAW = 2006
    DB_TYPE_NUM_ROWID = 2005
    DB_TYPE_NUM_TIMESTAMP = 2012
    DB_TYPE_NUM_TIMESTAMP_LTZ = 2014
    DB_TYPE_NUM_TIMESTAMP_TZ = 2013
    DB_TYPE_NUM_UROWID = 2030
    DB_TYPE_NUM_VARCHAR = 2001


cdef class ApiType:
    cdef:
        readonly str name
        tuple dbtypes


cdef class DbType:
    cdef:
        readonly uint32_t num
        readonly str name
        readonly uint32_t default_size
        uint32_t _buffer_size_factor
        uint8_t _ora_type_num
        uint8_t _csfrm

    @staticmethod
    cdef DbType _from_num(uint32_t num)

    @staticmethod
    cdef DbType _from_ora_type_and_csfrm(uint8_t ora_type_num, uint8_t csfrm)


cdef class Address:
    cdef:
        public str host
        public uint32_t port
        public str protocol
        public str https_proxy
        public uint32_t https_proxy_port

    cdef str build_connect_string(self)


cdef class AddressList:
    cdef:
        public list addresses
        bint load_balance
        int lru_index

    cdef str build_connect_string(self)


cdef class Description:
    cdef:
        public list address_lists
        public bint load_balance
        public int lru_index
        public uint32_t expire_time
        public uint32_t retry_count
        public uint32_t retry_delay
        public double tcp_connect_timeout
        public str service_name
        public str server_type
        public str sid
        public str cclass
        public uint32_t purity
        public bint ssl_server_dn_match
        public str ssl_server_cert_dn
        public str wallet_location

    cdef str _build_duration_str(self, double value)
    cdef str build_connect_string(self)


cdef class DescriptionList:
    cdef:
        public list descriptions
        bint load_balance
        int lru_index

    cdef str build_connect_string(self)


cdef class TnsnamesFile:
    cdef:
        str file_name
        int mtime
        dict entries


cdef class ConnectParamsImpl:
    cdef:
        public str config_dir
        public str user
        public str proxy_user
        public bint events
        public uint32_t mode
        public str edition
        public list appcontext
        public str tag
        public bint matchanytag
        public list shardingkey
        public list supershardingkey
        public uint32_t stmtcachesize
        public bint disable_oob
        public DescriptionList description_list
        uint64_t _external_handle
        public str debug_jdwp
        Description _default_description
        Address _default_address
        bytearray _password
        bytearray _password_obfuscator
        bytearray _new_password
        bytearray _new_password_obfuscator
        bytearray _wallet_password
        bytearray _wallet_password_obfuscator

    cdef int _copy(self, ConnectParamsImpl other_params) except -1
    cdef bytes _get_new_password(self)
    cdef bytearray _get_obfuscator(self, str password)
    cdef bytes _get_password(self)
    cdef TnsnamesFile _get_tnsnames_file(self)
    cdef str _get_wallet_password(self)
    cdef int _parse_connect_string(self, str connect_string) except -1
    cdef int _process_connect_descriptor(self, dict args) except -1
    cdef int _set_new_password(self, str password) except -1
    cdef int _set_password(self, str password) except -1
    cdef int _set_wallet_password(self, str password) except -1
    cdef bytearray _xor_bytes(self, bytearray a, bytearray b)


cdef class PoolParamsImpl(ConnectParamsImpl):
    cdef:
        public uint32_t min
        public uint32_t max
        public uint32_t increment
        public type connectiontype
        public uint32_t getmode
        public bint homogeneous
        public bint externalauth
        public uint32_t timeout
        public uint32_t wait_timeout
        public uint32_t max_lifetime_session
        public object session_callback
        public uint32_t max_sessions_per_shard
        public bint soda_metadata_cache
        public int ping_interval


cdef class BaseConnImpl:
    cdef:
        readonly str username
        readonly str dsn
        public object inputtypehandler
        public object outputtypehandler
        public bint autocommit
        public bint invoke_session_callback


cdef class BasePoolImpl:
    cdef:
        readonly str dsn
        readonly bint homogeneous
        readonly uint32_t increment
        readonly uint32_t min
        readonly uint32_t max
        readonly str username
        readonly str name
        ConnectParamsImpl connect_params


cdef class BaseCursorImpl:
    cdef:
        readonly str statement
        readonly uint64_t rowcount
        public uint32_t arraysize
        public uint32_t prefetchrows
        public object inputtypehandler
        public object outputtypehandler
        public object rowfactory
        public bint scrollable
        public list fetch_vars
        public list fetch_var_impls
        public list bind_vars
        public type bind_style
        public dict bind_vars_by_name
        uint32_t _buffer_rowcount
        uint32_t _buffer_index
        uint32_t _fetch_array_size
        bint _more_rows_to_fetch

    cdef int _bind_values(self, object cursor, object type_handler,
                          object params, uint32_t num_rows, uint32_t row_num,
                          bint defer_type_assignment) except -1
    cdef int _bind_values_by_name(self, object cursor, object type_handler,
                                  dict params, uint32_t num_rows,
                                  uint32_t row_num,
                                  bint defer_type_assignment) except -1
    cdef int _bind_values_by_position(self, object cursor, object type_handler,
                                      object params, uint32_t num_rows,
                                      uint32_t row_num,
                                      bint defer_type_assignment) except -1
    cdef int _close(self, bint in_del) except -1
    cdef int _create_fetch_var(self, object conn, object cursor,
                               object type_handler, ssize_t pos,
                               FetchInfo fetch_info) except -1
    cdef object _create_row(self)
    cdef BaseVarImpl _create_var_impl(self, object conn)
    cdef int _fetch_rows(self, object cursor) except -1
    cdef BaseConnImpl _get_conn_impl(self)
    cdef object _get_input_type_handler(self)
    cdef object _get_output_type_handler(self)
    cdef int _init_fetch_vars(self, uint32_t num_columns) except -1
    cdef bint _is_plsql(self)
    cdef int _perform_binds(self, object conn, uint32_t num_execs) except -1
    cdef int _reset_bind_vars(self, uint32_t num_rows) except -1
    cdef int _verify_var(self, object var) except -1


cdef class FetchInfo:
    cdef:
        int16_t _precision
        int16_t _scale
        uint32_t _buffer_size
        uint32_t _size
        bint _nulls_allowed
        str _name
        DbType _dbtype
        BaseDbObjectTypeImpl _objtype


cdef class BaseVarImpl:
    cdef:
        readonly str name
        readonly int16_t precision
        readonly int16_t scale
        readonly uint32_t num_elements
        readonly object inconverter
        readonly object outconverter
        readonly uint32_t size
        readonly uint32_t buffer_size
        readonly bint bypass_decode
        readonly bint is_array
        readonly bint nulls_allowed
        public uint32_t num_elements_in_array
        readonly DbType dbtype
        readonly BaseDbObjectTypeImpl objtype
        int _preferred_num_type
        FetchInfo _fetch_info
        bint _is_value_set

    cdef int _bind(self, object conn, BaseCursorImpl cursor,
                   uint32_t num_execs, object name, uint32_t pos) except -1
    cdef int _check_and_set_scalar_value(self, uint32_t pos, object value,
                                         bint* was_set) except -1
    cdef int _check_and_set_value(self, uint32_t pos, object value,
                                  bint* was_set) except -1
    cdef int _finalize_init(self) except -1
    cdef list _get_array_value(self)
    cdef object _get_scalar_value(self, uint32_t pos)
    cdef int _on_reset_bind(self, uint32_t num_rows) except -1
    cdef int _resize(self, uint32_t new_size) except -1
    cdef int _set_scalar_value(self, uint32_t pos, object value) except -1
    cdef int _set_num_elements_in_array(self, uint32_t num_elements) except -1
    cdef int _set_type_info_from_type(self, object typ) except -1
    cdef int _set_type_info_from_value(self, object value,
                                       bint is_plsql) except -1


cdef class BaseLobImpl:
    cdef:
        readonly DbType dbtype


cdef class BaseDbObjectTypeImpl:
    cdef:
        readonly str schema
        readonly str name
        readonly list attrs
        readonly bint is_collection
        readonly dict attrs_by_name
        readonly DbType element_dbtype
        readonly BaseDbObjectTypeImpl element_objtype
        readonly BaseConnImpl _conn_impl


cdef class BaseDbObjectAttrImpl:
    cdef:
        readonly str name
        readonly DbType dbtype
        readonly BaseDbObjectTypeImpl objtype


cdef class BaseDbObjectImpl:
    cdef:
        readonly BaseDbObjectTypeImpl type


cdef class BaseSodaDbImpl:
    cdef:
        object _conn


cdef class BaseSodaCollImpl:
    cdef:
        readonly str name


cdef class BaseSodaDocImpl:
    pass


cdef class BaseSodaDocCursorImpl:
    pass


cdef class BaseQueueImpl:
    cdef:
        readonly str name
        readonly BaseDbObjectTypeImpl payload_type
        readonly BaseDeqOptionsImpl deq_options_impl
        readonly BaseEnqOptionsImpl enq_options_impl


cdef class BaseDeqOptionsImpl:
    pass


cdef class BaseEnqOptionsImpl:
    pass


cdef class BaseMsgPropsImpl:
    cdef:
        public object payload


cdef class BaseSubscrImpl:
    cdef:
        readonly object callback
        readonly object connection
        readonly uint32_t namespace
        readonly str name
        readonly uint32_t protocol
        readonly str ip_address
        readonly uint32_t port
        readonly uint32_t timeout
        readonly uint32_t operations
        readonly uint32_t qos
        readonly uint64_t id
        readonly uint8_t grouping_class
        readonly uint32_t grouping_value
        readonly uint8_t grouping_type
        readonly bint client_initiated


cdef class BindVar:
    cdef:
        object var
        BaseVarImpl var_impl
        object name
        ssize_t pos
        bint has_value

    cdef int _create_var_from_type(self, object conn,
                                   BaseCursorImpl cursor_impl,
                                   object value) except -1
    cdef int _create_var_from_value(self, object conn,
                                    BaseCursorImpl cursor_impl, object value,
                                    uint32_t num_elements) except -1
    cdef int _set_by_type(self, object conn, BaseCursorImpl cursor_impl,
                          object typ) except -1
    cdef int _set_by_value(self, object conn, BaseCursorImpl cursor_impl,
                           object cursor, object value, object type_handler,
                           uint32_t row_num, uint32_t num_elements,
                           bint defer_type_assignment) except -1

cdef object get_exception_class(int32_t code)
