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

    cdef int _create_arrow_schema(self) except -1:
        """
        Creates an Arrow schema for the metadata.
        """
        cdef:
            ArrowTimeUnit time_unit = NANOARROW_TIME_UNIT_SECOND
            ArrowType child_arrow_type = NANOARROW_TYPE_NA
            ArrowType arrow_type = NANOARROW_TYPE_NA
            uint8_t py_type_num = self._py_type_num
            uint32_t db_type_num = self.dbtype.num

        if db_type_num == DB_TYPE_NUM_NUMBER:
            if py_type_num == PY_TYPE_NUM_DECIMAL \
                    and self.precision > 0 and self.precision <= 38:
                arrow_type = NANOARROW_TYPE_DECIMAL128
            elif py_type_num == PY_TYPE_NUM_STR:
                arrow_type = NANOARROW_TYPE_LARGE_STRING
            elif py_type_num == PY_TYPE_NUM_INT and self.scale == 0 \
                    and 0 < self.precision <= 18:
                arrow_type = NANOARROW_TYPE_INT64
            else:
                arrow_type = NANOARROW_TYPE_DOUBLE
        elif db_type_num in (DB_TYPE_NUM_CHAR, DB_TYPE_NUM_VARCHAR,
                             DB_TYPE_NUM_NCHAR, DB_TYPE_NUM_NVARCHAR):
            arrow_type = NANOARROW_TYPE_LARGE_STRING
        elif db_type_num == DB_TYPE_NUM_BINARY_FLOAT:
            arrow_type = NANOARROW_TYPE_FLOAT
        elif db_type_num == DB_TYPE_NUM_BINARY_DOUBLE:
            arrow_type = NANOARROW_TYPE_DOUBLE
        elif db_type_num == DB_TYPE_NUM_BOOLEAN:
            arrow_type = NANOARROW_TYPE_BOOL
        elif db_type_num in (DB_TYPE_NUM_DATE,
                             DB_TYPE_NUM_TIMESTAMP,
                             DB_TYPE_NUM_TIMESTAMP_LTZ,
                             DB_TYPE_NUM_TIMESTAMP_TZ):
            arrow_type = NANOARROW_TYPE_TIMESTAMP
            if self.scale > 0 and self.scale <= 3:
                time_unit = NANOARROW_TIME_UNIT_MILLI
            elif self.scale > 3 and self.scale <= 6:
                time_unit = NANOARROW_TIME_UNIT_MICRO
            elif self.scale > 6 and self.scale <= 9:
                time_unit = NANOARROW_TIME_UNIT_NANO
        elif db_type_num == DB_TYPE_NUM_LONG_RAW:
            arrow_type = NANOARROW_TYPE_LARGE_BINARY
        elif db_type_num in (DB_TYPE_NUM_LONG_VARCHAR,
                             DB_TYPE_NUM_LONG_NVARCHAR):
            arrow_type = NANOARROW_TYPE_LARGE_STRING
        elif db_type_num == DB_TYPE_NUM_RAW:
            arrow_type = NANOARROW_TYPE_LARGE_BINARY
        elif db_type_num == DB_TYPE_NUM_VECTOR:
            if self.vector_flags & VECTOR_META_FLAG_SPARSE_VECTOR:
                arrow_type = NANOARROW_TYPE_STRUCT
            else:
                arrow_type = NANOARROW_TYPE_LIST
            if self.vector_format == VECTOR_FORMAT_FLOAT32:
                child_arrow_type = NANOARROW_TYPE_FLOAT
            elif self.vector_format == VECTOR_FORMAT_FLOAT64:
                child_arrow_type = NANOARROW_TYPE_DOUBLE
            elif self.vector_format == VECTOR_FORMAT_INT8:
                child_arrow_type = NANOARROW_TYPE_INT8
            elif self.vector_format == VECTOR_FORMAT_BINARY:
                child_arrow_type = NANOARROW_TYPE_UINT8
            else:
                errors._raise_err(errors.ERR_ARROW_UNSUPPORTED_VECTOR_FORMAT)
        else:
            errors._raise_err(errors.ERR_ARROW_UNSUPPORTED_DATA_TYPE,
                              db_type_name=self.dbtype.name)

        self._schema_impl = ArrowSchemaImpl.__new__(ArrowSchemaImpl)
        self._schema_impl.populate_from_metadata(
            arrow_type,
            self.name,
            self.precision,
            self.scale,
            time_unit,
            child_arrow_type,
        )

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

    cdef int _set_arrow_schema(self, ArrowSchemaImpl schema_impl) except -1:
        """
        Sets an Arrow schema, which checks to see that the Arrow type is
        compatible with the database type.
        """
        self.check_convert_from_arrow(schema_impl)
        self._finalize_init()
        self._schema_impl = schema_impl

    cdef int check_convert_from_arrow(self,
                                      ArrowSchemaImpl schema_impl) except -1:
        """
        Check that the conversion from the Arrow type to the database type is
        supported.
        """
        cdef:
            ArrowType arrow_type = schema_impl.arrow_type
            uint32_t db_type_num = self.dbtype.num
            bint ok = False

        if arrow_type in (NANOARROW_TYPE_BINARY,
                          NANOARROW_TYPE_FIXED_SIZE_BINARY,
                          NANOARROW_TYPE_LARGE_BINARY):
            if db_type_num in (DB_TYPE_NUM_RAW, DB_TYPE_NUM_LONG_RAW):
                ok = True
        elif arrow_type == NANOARROW_TYPE_BOOL:
            if db_type_num in (DB_TYPE_NUM_BOOLEAN):
                ok = True
        elif arrow_type in (NANOARROW_TYPE_DECIMAL128,
                            NANOARROW_TYPE_INT8,
                            NANOARROW_TYPE_INT16,
                            NANOARROW_TYPE_INT32,
                            NANOARROW_TYPE_INT64,
                            NANOARROW_TYPE_UINT8,
                            NANOARROW_TYPE_UINT16,
                            NANOARROW_TYPE_UINT32,
                            NANOARROW_TYPE_UINT64):
            if db_type_num == DB_TYPE_NUM_NUMBER:
                ok = True
        elif arrow_type in (NANOARROW_TYPE_DATE32,
                            NANOARROW_TYPE_DATE64,
                            NANOARROW_TYPE_TIMESTAMP):
            if db_type_num in (DB_TYPE_NUM_DATE,
                               DB_TYPE_NUM_TIMESTAMP,
                               DB_TYPE_NUM_TIMESTAMP_LTZ,
                               DB_TYPE_NUM_TIMESTAMP_TZ):
                ok = True
        elif arrow_type == NANOARROW_TYPE_FLOAT:
            if db_type_num in (DB_TYPE_NUM_BINARY_DOUBLE,
                               DB_TYPE_NUM_BINARY_FLOAT,
                               DB_TYPE_NUM_NUMBER):
                ok = True
        elif arrow_type == NANOARROW_TYPE_DOUBLE:
            if db_type_num in (DB_TYPE_NUM_BINARY_DOUBLE,
                               DB_TYPE_NUM_BINARY_FLOAT,
                               DB_TYPE_NUM_NUMBER):
                ok = True
        elif arrow_type in (NANOARROW_TYPE_STRING,
                            NANOARROW_TYPE_LARGE_STRING):
            if db_type_num in (DB_TYPE_NUM_CHAR,
                               DB_TYPE_NUM_LONG_VARCHAR,
                               DB_TYPE_NUM_VARCHAR,
                               DB_TYPE_NUM_NCHAR,
                               DB_TYPE_NUM_LONG_NVARCHAR,
                               DB_TYPE_NUM_NVARCHAR):
                ok = True

        if not ok:
            errors._raise_err(errors.ERR_CANNOT_CONVERT_FROM_ARROW_TYPE,
                              arrow_type=schema_impl.get_type_name(),
                              db_type=self.dbtype.name)

    cdef int check_convert_to_arrow(self,
                                    ArrowSchemaImpl schema_impl) except -1:
        """
        Check that the conversion to the Arrow type from the database type is
        supported.
        """
        cdef:
            ArrowType arrow_type = schema_impl.arrow_type
            uint32_t db_type_num = self.dbtype.num
            bint ok = False

        if db_type_num == DB_TYPE_NUM_NUMBER:
            if arrow_type in (
                NANOARROW_TYPE_DECIMAL128,
                NANOARROW_TYPE_DOUBLE,
                NANOARROW_TYPE_FLOAT,
                NANOARROW_TYPE_INT8,
                NANOARROW_TYPE_INT16,
                NANOARROW_TYPE_INT32,
                NANOARROW_TYPE_INT64,
                NANOARROW_TYPE_UINT8,
                NANOARROW_TYPE_UINT16,
                NANOARROW_TYPE_UINT32,
                NANOARROW_TYPE_UINT64
            ):
                ok = True
        elif db_type_num in (
            DB_TYPE_NUM_BLOB,
            DB_TYPE_NUM_RAW,
            DB_TYPE_NUM_LONG_RAW
        ):
            if arrow_type in (
                NANOARROW_TYPE_BINARY,
                NANOARROW_TYPE_FIXED_SIZE_BINARY,
                NANOARROW_TYPE_LARGE_BINARY
            ):
                ok = True
        elif db_type_num == DB_TYPE_NUM_BOOLEAN:
            if arrow_type == NANOARROW_TYPE_BOOL:
                ok = True
        elif db_type_num in (
            DB_TYPE_NUM_DATE,
            DB_TYPE_NUM_TIMESTAMP,
            DB_TYPE_NUM_TIMESTAMP_LTZ,
            DB_TYPE_NUM_TIMESTAMP_TZ
        ):
            if arrow_type in (
                NANOARROW_TYPE_DATE32,
                NANOARROW_TYPE_DATE64,
                NANOARROW_TYPE_TIMESTAMP
            ):
                ok = True
        elif db_type_num in (
            DB_TYPE_NUM_BINARY_DOUBLE,
            DB_TYPE_NUM_BINARY_FLOAT
        ):
            if arrow_type in (NANOARROW_TYPE_DOUBLE, NANOARROW_TYPE_FLOAT):
                ok = True
        elif db_type_num in (
            DB_TYPE_NUM_CHAR,
            DB_TYPE_NUM_CLOB,
            DB_TYPE_NUM_LONG_NVARCHAR,
            DB_TYPE_NUM_LONG_VARCHAR,
            DB_TYPE_NUM_VARCHAR,
            DB_TYPE_NUM_NCHAR,
            DB_TYPE_NUM_NCLOB,
            DB_TYPE_NUM_NVARCHAR
        ):
            if arrow_type in (
                NANOARROW_TYPE_STRING,
                NANOARROW_TYPE_LARGE_STRING
            ):
                ok = True

        if not ok:
            errors._raise_err(errors.ERR_CANNOT_CONVERT_TO_ARROW_TYPE,
                              arrow_type=schema_impl.get_type_name(),
                              db_type=self.dbtype.name)

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
    cdef OracleMetadata from_arrow_schema(ArrowSchemaImpl schema_impl):
        """
        Returns a new OracleMetadata instance with attributes set from an Arrow
        array.
        """
        cdef:
            OracleMetadata metadata = OracleMetadata.__new__(OracleMetadata)
            ArrowType arrow_type = schema_impl.arrow_type
        if arrow_type in (
            NANOARROW_TYPE_DECIMAL128,
            NANOARROW_TYPE_INT8,
            NANOARROW_TYPE_INT16,
            NANOARROW_TYPE_INT32,
            NANOARROW_TYPE_INT64,
            NANOARROW_TYPE_UINT8,
            NANOARROW_TYPE_UINT16,
            NANOARROW_TYPE_UINT32,
            NANOARROW_TYPE_UINT64,
        ):
            metadata.dbtype = DB_TYPE_NUMBER
        elif arrow_type == NANOARROW_TYPE_STRING:
            metadata.dbtype = DB_TYPE_VARCHAR
        elif arrow_type in (NANOARROW_TYPE_BINARY,
                            NANOARROW_TYPE_FIXED_SIZE_BINARY):
            metadata.dbtype = DB_TYPE_RAW
        elif arrow_type == NANOARROW_TYPE_FLOAT:
            metadata.dbtype = DB_TYPE_BINARY_FLOAT
        elif arrow_type == NANOARROW_TYPE_DOUBLE:
            metadata.dbtype = DB_TYPE_BINARY_DOUBLE
        elif arrow_type == NANOARROW_TYPE_BOOL:
            metadata.dbtype = DB_TYPE_BOOLEAN
        elif arrow_type == NANOARROW_TYPE_TIMESTAMP:
            metadata.dbtype = DB_TYPE_TIMESTAMP
        elif arrow_type in (NANOARROW_TYPE_DATE32, NANOARROW_TYPE_DATE64):
            metadata.dbtype = DB_TYPE_DATE
        elif arrow_type == NANOARROW_TYPE_LARGE_STRING:
            metadata.dbtype = DB_TYPE_LONG
        elif arrow_type == NANOARROW_TYPE_LARGE_BINARY:
            metadata.dbtype = DB_TYPE_LONG_RAW
        elif arrow_type in (NANOARROW_TYPE_LIST,
                            NANOARROW_TYPE_STRUCT,
                            NANOARROW_TYPE_FIXED_SIZE_LIST):
            metadata.dbtype = DB_TYPE_VECTOR
        else:
            errors._raise_err(errors.ERR_UNSUPPORTED_ARROW_TYPE,
                              arrow_type=schema_impl.get_type_name())
        metadata._schema_impl = schema_impl
        metadata.name = schema_impl.name
        metadata.precision = schema_impl.precision
        metadata.scale = schema_impl.scale
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
