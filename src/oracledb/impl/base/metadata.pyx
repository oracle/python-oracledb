#------------------------------------------------------------------------------
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
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
# metadata.pyx
#
# Cython file defining the OracleMetadata class (embedded in base_impl.pyx).
#------------------------------------------------------------------------------

@cython.freelist(30)
cdef class OracleMetadata:

    cdef int _finalize_init(self) except -1:
        """
        Internal method that finalizes the initialization of metadata by
        setting the buffer size, max size and default Python type (if they have
        not already been set).
        """
        if self.dbtype.default_size == 0:
            self.max_size = 0
            self.buffer_size = self.dbtype._buffer_size_factor
        else:
            if self.max_size == 0:
                self.max_size = self.dbtype.default_size
            self.buffer_size = self.max_size * self.dbtype._buffer_size_factor
        if self._py_type_num == 0:
            if self.dbtype._ora_type_num != ORA_TYPE_NUM_NUMBER:
                self._py_type_num = self.dbtype._default_py_type_num
            else:
                if self.scale == 0 or \
                        (self.scale == -127 and self.precision == 0):
                    self._py_type_num = PY_TYPE_NUM_INT
                else:
                    self._py_type_num = PY_TYPE_NUM_FLOAT

    cdef int _set_arrow_type(self) except -1:
        """
        Determine the arrow type to use for the data.
        """
        cdef:
            uint8_t py_type_num = self._py_type_num
            uint32_t db_type_num = self.dbtype.num
        if db_type_num == DB_TYPE_NUM_NUMBER:
            if py_type_num == PY_TYPE_NUM_DECIMAL and self.precision > 0:
                self._arrow_type = NANOARROW_TYPE_DECIMAL128
            elif py_type_num == PY_TYPE_NUM_STR:
                self._arrow_type = NANOARROW_TYPE_STRING
            elif py_type_num == PY_TYPE_NUM_INT and self.scale == 0 \
                    and self.precision <= 18:
                self._arrow_type = NANOARROW_TYPE_INT64
            else:
                self._arrow_type = NANOARROW_TYPE_DOUBLE
        elif db_type_num in (DB_TYPE_NUM_CHAR, DB_TYPE_NUM_VARCHAR):
            self._arrow_type = NANOARROW_TYPE_STRING
        elif db_type_num == DB_TYPE_NUM_BINARY_FLOAT:
            self._arrow_type = NANOARROW_TYPE_FLOAT
        elif db_type_num == DB_TYPE_NUM_BINARY_DOUBLE:
            self._arrow_type = NANOARROW_TYPE_DOUBLE
        elif db_type_num == DB_TYPE_NUM_BOOLEAN:
            self._arrow_type = NANOARROW_TYPE_BOOL
        elif db_type_num in (DB_TYPE_NUM_DATE,
                             DB_TYPE_NUM_TIMESTAMP,
                             DB_TYPE_NUM_TIMESTAMP_LTZ,
                             DB_TYPE_NUM_TIMESTAMP_TZ):
            self._arrow_type = NANOARROW_TYPE_TIMESTAMP
        elif db_type_num == DB_TYPE_NUM_LONG_RAW:
            self._arrow_type = NANOARROW_TYPE_LARGE_BINARY
        elif db_type_num == DB_TYPE_NUM_LONG_VARCHAR:
            self._arrow_type = NANOARROW_TYPE_LARGE_STRING
        elif db_type_num == DB_TYPE_NUM_RAW:
            self._arrow_type = NANOARROW_TYPE_BINARY
        else:
            errors._raise_err(errors.ERR_ARROW_UNSUPPORTED_DATA_TYPE,
                              db_type_name=self.dbtype.name)

    cdef OracleMetadata copy(self):
        """
        Create a copy of the metadata and return it.
        """
        cdef OracleMetadata metadata = OracleMetadata.__new__(OracleMetadata)
        metadata.name = self.name
        metadata.dbtype = self.dbtype
        metadata.objtype = self.objtype
        metadata.precision = self.precision
        metadata.scale = self.scale
        metadata.max_size = self.max_size
        metadata.nulls_allowed = self.nulls_allowed
        metadata.is_json = self.is_json
        metadata.is_oson = self.is_oson
        metadata.domain_schema = self.domain_schema
        metadata.domain_name = self.domain_name
        metadata.annotations = self.annotations
        metadata.vector_dimensions = self.vector_dimensions
        metadata.vector_format = self.vector_format
        metadata.vector_flags = self.vector_flags
        return metadata

    @staticmethod
    cdef OracleMetadata from_type(object typ):
        """
        Returns a new OracleMetadata instance with attributes set according to
        the Python type.
        """
        cdef:
            OracleMetadata metadata = OracleMetadata.__new__(OracleMetadata)
            ApiType apitype
        if isinstance(typ, DbType):
            metadata.dbtype = typ
        elif isinstance(typ, ApiType):
            apitype = typ
            metadata.dbtype = apitype.dbtypes[0]
        elif isinstance(typ, PY_TYPE_DB_OBJECT_TYPE):
            metadata.dbtype = DB_TYPE_OBJECT
            metadata.objtype = typ._impl
        elif not isinstance(typ, type):
            errors._raise_err(errors.ERR_EXPECTING_TYPE)
        elif typ is int:
            metadata.dbtype = DB_TYPE_NUMBER
            metadata._py_type_num = PY_TYPE_NUM_INT
        elif typ is float:
            metadata.dbtype = DB_TYPE_NUMBER
            metadata._py_type_num = PY_TYPE_NUM_FLOAT
        elif typ is str:
            metadata.dbtype = DB_TYPE_VARCHAR
        elif typ is bytes:
            metadata.dbtype = DB_TYPE_RAW
        elif typ is PY_TYPE_DECIMAL:
            metadata.dbtype = DB_TYPE_NUMBER
            metadata._py_type_num = PY_TYPE_NUM_DECIMAL
        elif typ is PY_TYPE_BOOL:
            metadata.dbtype = DB_TYPE_BOOLEAN
        elif typ is PY_TYPE_DATE:
            metadata.dbtype = DB_TYPE_DATE
        elif typ is PY_TYPE_DATETIME:
            metadata.dbtype = DB_TYPE_TIMESTAMP
        elif typ is PY_TYPE_TIMEDELTA:
            metadata.dbtype = DB_TYPE_INTERVAL_DS
        else:
            errors._raise_err(errors.ERR_PYTHON_TYPE_NOT_SUPPORTED, typ=typ)
        return metadata

    @staticmethod
    cdef OracleMetadata from_value(object value):
        """
        Returns a new OracleMetadata instance with attributes set according to
        the Python type.
        """
        cdef OracleMetadata metadata = OracleMetadata.__new__(OracleMetadata)
        if value is None:
            metadata.dbtype = DB_TYPE_VARCHAR
            metadata.max_size = 1
        elif isinstance(value, PY_TYPE_BOOL):
            metadata.dbtype = DB_TYPE_BOOLEAN
        elif isinstance(value, str):
            metadata.dbtype = DB_TYPE_VARCHAR
            metadata.max_size = <uint32_t> len((<str> value).encode())
        elif isinstance(value, bytes):
            metadata.max_size = <uint32_t> len(value)
            metadata.dbtype = DB_TYPE_RAW
        elif isinstance(value, int):
            metadata.dbtype = DB_TYPE_NUMBER
            metadata._py_type_num = PY_TYPE_NUM_INT
        elif isinstance(value, float):
            metadata.dbtype = DB_TYPE_NUMBER
            metadata._py_type_num = PY_TYPE_NUM_FLOAT
        elif isinstance(value, PY_TYPE_DECIMAL):
            metadata.dbtype = DB_TYPE_NUMBER
            metadata._py_type_num = PY_TYPE_NUM_DECIMAL
        elif isinstance(value, (PY_TYPE_DATE, PY_TYPE_DATETIME)):
            metadata.dbtype = DB_TYPE_DATE
        elif isinstance(value, PY_TYPE_TIMEDELTA):
            metadata.dbtype = DB_TYPE_INTERVAL_DS
        elif isinstance(value, PY_TYPE_DB_OBJECT):
            metadata.dbtype = DB_TYPE_OBJECT
            metadata.objtype = value.type._impl
        elif isinstance(value, (PY_TYPE_LOB, PY_TYPE_ASYNC_LOB)):
            metadata.dbtype = value.type
        elif isinstance(value, (PY_TYPE_CURSOR, PY_TYPE_ASYNC_CURSOR)):
            metadata.dbtype = DB_TYPE_CURSOR
        elif isinstance(value, (array.array, PY_TYPE_SPARSE_VECTOR)):
            metadata.dbtype = DB_TYPE_VECTOR
        elif isinstance(value, PY_TYPE_INTERVAL_YM):
            metadata.dbtype = DB_TYPE_INTERVAL_YM
        else:
            errors._raise_err(errors.ERR_PYTHON_VALUE_NOT_SUPPORTED,
                              type_name=type(value).__name__)
        return metadata
