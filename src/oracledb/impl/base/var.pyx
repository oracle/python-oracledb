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
# var.pyx
#
# Cython file defining the base Variable implementation class (embedded in
# base_impl.pyx).
#------------------------------------------------------------------------------

cdef class BaseVarImpl:

    cdef int _bind(self, object conn, BaseCursorImpl cursor,
                   uint32_t num_execs, object name, uint32_t pos) except -1:
        """
        Binds a variable to the cursor.
        """
        raise NotImplementedError()


    cdef int _check_and_set_scalar_value(self, uint32_t pos, object value,
                                         bint* was_set) except -1:
        """
        Sets a scalar value in the variable at the given position, but first
        checks the type of Python value to see if it is acceptable. The value
        may be modified by the in converter (if one has been set) or adjusted
        to be acceptable (for some cases). If the was_set pointer is NULL, an
        exception is raised when the Python value is found to be unacceptable;
        otherwise, the flag is cleared if the Python value is unacceptable.
        """
        cdef:
            uint32_t db_type_num, size
            bint type_ok = True
            BaseLobImpl lob_impl
            object orig_value

        # call in converter, if applicable
        if self.inconverter is not None:
            value = self.inconverter(value)

        # if value is None, no further checks are needed
        if value is None:
            self._set_scalar_value(pos, value)
            self._is_value_set = True
            return 0

        # check to see that the type of value is accepted; perform any
        # necessary adjustments
        db_type_num = self.dbtype.num
        if db_type_num in (DB_TYPE_NUM_NUMBER, DB_TYPE_NUM_BINARY_INTEGER,
                           DB_TYPE_NUM_BINARY_DOUBLE,
                           DB_TYPE_NUM_BINARY_FLOAT):
            type_ok = isinstance(value,
                                 (PY_TYPE_BOOL, int, float, PY_TYPE_DECIMAL))
            if type_ok:
                if db_type_num in (DB_TYPE_NUM_BINARY_FLOAT,
                                   DB_TYPE_NUM_BINARY_DOUBLE):
                    value = float(value)
                elif db_type_num == DB_TYPE_NUM_BINARY_INTEGER \
                        or cpython.PyBool_Check(value):
                    value = int(value)
        elif db_type_num in (DB_TYPE_NUM_CHAR, DB_TYPE_NUM_VARCHAR,
                             DB_TYPE_NUM_NCHAR, DB_TYPE_NUM_NVARCHAR,
                             DB_TYPE_NUM_LONG_VARCHAR,
                             DB_TYPE_NUM_LONG_NVARCHAR):
            if isinstance(value, bytes):
                value = (<bytes> value).decode()
            else:
                type_ok = isinstance(value, str)
            if type_ok:
                size = <uint32_t> len(<str> value)
                if size > self.size:
                    self._resize(size)
        elif db_type_num in (DB_TYPE_NUM_RAW, DB_TYPE_NUM_LONG_RAW):
            if isinstance(value, str):
                value = (<str> value).encode()
            else:
                type_ok = isinstance(value, bytes)
            if type_ok:
                size = <uint32_t> len(<bytes> value)
                if size > self.size:
                    self._resize(size)
        elif db_type_num in (DB_TYPE_NUM_DATE, DB_TYPE_NUM_TIMESTAMP,
                           DB_TYPE_NUM_TIMESTAMP_LTZ,
                           DB_TYPE_NUM_TIMESTAMP_TZ):
            type_ok = cydatetime.PyDateTime_Check(value) \
                    or cydatetime.PyDate_Check(value)
        elif db_type_num == DB_TYPE_NUM_INTERVAL_DS:
            type_ok = isinstance(value, PY_TYPE_TIMEDELTA)
        elif db_type_num in (DB_TYPE_NUM_CLOB,
                             DB_TYPE_NUM_NCLOB,
                             DB_TYPE_NUM_BLOB):
            if isinstance(value, PY_TYPE_LOB):
                lob_impl = value._impl
                if lob_impl.dbtype is not self.dbtype:
                    if was_set != NULL:
                        was_set[0] = False
                        return 0
                    errors._raise_err(errors.ERR_LOB_OF_WRONG_TYPE,
                                      actual_type_name=lob_impl.dbtype.name,
                                      expected_type_name=self.dbtype.name)
            else:
                type_ok = isinstance(value, (bytes, str))
                if type_ok:
                    orig_value = self._get_scalar_value(pos)
                    if isinstance(orig_value, PY_TYPE_LOB):
                        orig_value.trim()
                        if value:
                            orig_value.write(value)
                        value = orig_value
        elif db_type_num == DB_TYPE_NUM_OBJECT:
            type_ok = isinstance(value, PY_TYPE_DB_OBJECT)
            if type_ok and value._impl.type != self.objtype:
                if was_set != NULL:
                    was_set[0] = False
                    return 0
                errors._raise_err(errors.ERR_WRONG_OBJECT_TYPE,
                                  actual_schema=value.type.schema,
                                  actual_name=value.type.name,
                                  expected_schema=self.objtype.schema,
                                  expected_name=self.objtype.name)
        elif db_type_num == DB_TYPE_NUM_CURSOR:
            type_ok = isinstance(value, PY_TYPE_CURSOR)
        elif db_type_num in (DB_TYPE_NUM_ROWID, DB_TYPE_NUM_UROWID,
                             DB_TYPE_NUM_INTERVAL_YM):
            if was_set != NULL:
                was_set[0] = False
                return 0
            errors._raise_err(errors.ERR_UNSUPPORTED_VAR_SET,
                              db_type_name=self.dbtype.name)
        elif db_type_num == DB_TYPE_NUM_BOOLEAN:
            value = bool(value)
        if not type_ok:
            if was_set != NULL:
                was_set[0] = False
                return 0
            errors._raise_err(errors.ERR_UNSUPPORTED_PYTHON_TYPE_FOR_VAR,
                              py_type_name = type(value).__name__,
                              db_type_name = self.dbtype.name)
        self._set_scalar_value(pos, value)
        self._is_value_set = True

    cdef int _check_and_set_value(self, uint32_t pos, object value,
                                  bint* was_set) except -1:
        """
        Sets the value in the variable at the given position, but first checks
        the type of Python value to see if it is acceptable.
        """
        cdef:
            uint32_t i, num_elements_in_array
            object element_value

        # scalar variables can be checked directly
        if not self.is_array:
            return self._check_and_set_scalar_value(pos, value, was_set)

        # array variables must have a list supplied to them
        if not isinstance(value, list):
            if was_set != NULL:
                was_set[0] = False
                return 0
            errors._raise_err(errors.ERR_EXPECTING_LIST_FOR_ARRAY_VAR)

        # the size of the array must be sufficient to hold all of the
        # elements
        num_elements_in_array = len(<list> value)
        if num_elements_in_array > self.num_elements:
            if was_set != NULL:
                was_set[0] = False
                return 0
            errors._raise_err(errors.ERR_INCORRECT_VAR_ARRAY_SIZE,
                              var_arraysize=self.num_elements,
                              required_arraysize=num_elements_in_array)

        # check and set each of the element's values
        for i, element_value in enumerate(<list> value):
            self._check_and_set_scalar_value(i, element_value, was_set)
            if was_set != NULL and not was_set[0]:
                return 0
        self._set_num_elements_in_array(num_elements_in_array)

    cdef int _finalize_init(self) except -1:
        """
        Internal method that finalizes initialization of the variable.
        """
        if self.dbtype.default_size > 0:
            if self.size == 0:
                self.size = self.dbtype.default_size
            self.buffer_size = self.size * self.dbtype._buffer_size_factor
        else:
            self.buffer_size = self.dbtype._buffer_size_factor
        if self.num_elements == 0:
            self.num_elements = 1

    cdef list _get_array_value(self):
        """
        Internal method to return the value of the array.
        """
        raise NotImplementedError()

    cdef object _get_scalar_value(self, uint32_t pos):
        """
        Internal method to return the value of the variable at the given
        position.
        """
        raise NotImplementedError()

    cdef int _on_reset_bind(self, uint32_t num_rows) except -1:
        """
        Called when the bind variable is being reset, just prior to performing
        a bind operation.
        """
        if self.num_elements < num_rows:
            self.num_elements = num_rows
            self._finalize_init()

    cdef int _resize(self, uint32_t new_size) except -1:
        """
        Resize the variable to the new size provided.
        """
        self.size = new_size
        self.buffer_size = new_size * self.dbtype._buffer_size_factor

    cdef int _set_scalar_value(self, uint32_t pos, object value) except -1:
        """
        Set the value of the variable at the given position. At this point it
        is assumed that all checks have been performed!
        """
        raise NotImplementedError()

    cdef int _set_num_elements_in_array(self, uint32_t num_elements) except -1:
        """
        Sets the number of elements in the array.
        """
        self.num_elements_in_array = num_elements

    cdef int _set_type_info_from_type(self, object typ) except -1:
        """
        Sets the type and size of the variable given a Python type.
        """
        cdef ApiType apitype
        if isinstance(typ, DbType):
            self.dbtype = typ
        elif isinstance(typ, ApiType):
            apitype = typ
            self.dbtype = apitype.dbtypes[0]
        elif isinstance(typ, PY_TYPE_DB_OBJECT_TYPE):
            self.dbtype = DB_TYPE_OBJECT
            self.objtype = typ._impl
        elif not isinstance(typ, type):
            errors._raise_err(errors.ERR_EXPECTING_TYPE)
        elif typ is int:
            self.dbtype = DB_TYPE_NUMBER
            self._preferred_num_type = NUM_TYPE_INT
        elif typ is float:
            self.dbtype = DB_TYPE_NUMBER
            self._preferred_num_type = NUM_TYPE_FLOAT
        elif typ is str:
            self.dbtype = DB_TYPE_VARCHAR
        elif typ is bytes:
            self.dbtype = DB_TYPE_RAW
        elif typ is PY_TYPE_DECIMAL:
            self.dbtype = DB_TYPE_NUMBER
            self._preferred_num_type = NUM_TYPE_DECIMAL
        elif typ is PY_TYPE_BOOL:
            self.dbtype = DB_TYPE_BOOLEAN
        elif typ is PY_TYPE_DATE:
            self.dbtype = DB_TYPE_DATE
        elif typ is PY_TYPE_DATETIME:
            self.dbtype = DB_TYPE_TIMESTAMP
        elif typ is PY_TYPE_TIMEDELTA:
            self.dbtype = DB_TYPE_INTERVAL_DS
        else:
            errors._raise_err(errors.ERR_PYTHON_TYPE_NOT_SUPPORTED, typ=typ)

    cdef int _set_type_info_from_value(self, object value,
                                       bint is_plsql) except -1:
        """
        Sets the type and size of the variable given a Python value. This
        method is called once for scalars and once per element in a list for
        array values. If a different type is detected an error is raised.
        """
        cdef:
            int preferred_num_type = NUM_TYPE_FLOAT
            BaseDbObjectTypeImpl objtype = None
            DbType dbtype = None
            uint32_t size = 0
        if value is None:
            dbtype = DB_TYPE_VARCHAR
            size = 1
        elif isinstance(value, PY_TYPE_BOOL):
            dbtype = DB_TYPE_BOOLEAN if is_plsql else DB_TYPE_BINARY_INTEGER
        elif isinstance(value, str):
            size = <uint32_t> len(value)
            dbtype = DB_TYPE_VARCHAR
        elif isinstance(value, bytes):
            size = <uint32_t> len(value)
            dbtype = DB_TYPE_RAW
        elif isinstance(value, int):
            dbtype = DB_TYPE_NUMBER
            preferred_num_type = NUM_TYPE_INT
        elif isinstance(value, float):
            dbtype = DB_TYPE_NUMBER
            preferred_num_type = NUM_TYPE_FLOAT
        elif isinstance(value, PY_TYPE_DECIMAL):
            dbtype = DB_TYPE_NUMBER
            preferred_num_type = NUM_TYPE_DECIMAL
        elif isinstance(value, (PY_TYPE_DATE, PY_TYPE_DATETIME)):
            dbtype = DB_TYPE_DATE
        elif isinstance(value, PY_TYPE_TIMEDELTA):
            dbtype = DB_TYPE_INTERVAL_DS
        elif isinstance(value, PY_TYPE_DB_OBJECT):
            dbtype = DB_TYPE_OBJECT
            objtype = value.type._impl
        elif isinstance(value, PY_TYPE_LOB):
            dbtype = value.type
        elif isinstance(value, PY_TYPE_CURSOR):
            dbtype = DB_TYPE_CURSOR
        else:
            errors._raise_err(errors.ERR_PYTHON_VALUE_NOT_SUPPORTED,
                              type_name=type(value).__name__)
        if self.dbtype is None:
            self.dbtype = dbtype
            self.objtype = objtype
            self._preferred_num_type = preferred_num_type
        elif dbtype is not self.dbtype or objtype is not self.objtype:
            errors._raise_err(errors.ERR_MIXED_ELEMENT_TYPES, element=value)
        if size > self.size:
            self.size = size

    def get_description(self):
        """
        Return a 7-tuple containing information about the variable: (name,
        type, display_size, internal_size, precision, scale, null_ok).
        """
        cdef:
            uint32_t display_size = 0, size_in_bytes = 0
            FetchInfo fetch_info = self._fetch_info
            DbType dbtype = fetch_info._dbtype
            object precision, scale
        if fetch_info._size > 0:
            display_size = fetch_info._size
            size_in_bytes = fetch_info._buffer_size
        elif dbtype is DB_TYPE_DATE \
                or dbtype is DB_TYPE_TIMESTAMP \
                or dbtype is DB_TYPE_TIMESTAMP_LTZ \
                or dbtype is DB_TYPE_TIMESTAMP_TZ:
            display_size = 23
        elif dbtype is DB_TYPE_BINARY_FLOAT \
                or dbtype is DB_TYPE_BINARY_DOUBLE \
                or dbtype is DB_TYPE_BINARY_INTEGER \
                or dbtype is DB_TYPE_NUMBER:
            if fetch_info._precision:
                display_size = fetch_info._precision + 1
                if fetch_info._scale > 0:
                    display_size += fetch_info._scale + 1
            else:
                display_size = 127
        if fetch_info._precision or fetch_info._scale:
            precision = fetch_info._precision
            scale = fetch_info._scale
        else:
            scale = precision = None
        return (fetch_info._name, dbtype, display_size or None,
                size_in_bytes or None, precision, scale,
                fetch_info._nulls_allowed)

    def get_all_values(self):
        """
        Internal method for returning an array of all of the values stored in
        the variable.
        """
        cdef uint32_t i
        if self.is_array:
            return self._get_array_value()
        return [self._get_scalar_value(i) for i in range(self.num_elements)]

    def get_value(self, uint32_t pos):
        """
        Internal method for getting the value of a variable.
        """
        if self.is_array:
            return self._get_array_value()
        if pos >= self.num_elements:
            raise IndexError("position out of range")
        return self._get_scalar_value(pos)

    def set_value(self, uint32_t pos, object value):
        """
        Internal method for setting a variable's value at the specified
        position.
        """
        if self.is_array:
            if pos > 0:
                errors._raise_err(errors.ERR_ARRAYS_OF_ARRAYS)
        elif pos >= self.num_elements:
            raise IndexError("position out of range")
        self._check_and_set_value(pos, value, NULL)
