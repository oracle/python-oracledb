#------------------------------------------------------------------------------
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
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

@cython.freelist(20)
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
        cdef uint32_t size

        # call in converter, if applicable
        if self.inconverter is not None:
            value = self.inconverter(value)

        # check the value and verify it is acceptable
        value = self._conn_impl._check_value(self.metadata, value, was_set)
        if was_set != NULL and not was_set[0]:
            return 0

        # resize variable, if applicable
        if value is not None and self.metadata.dbtype.default_size != 0:
            size = <uint32_t> len(value)
            if size > self.metadata.max_size:
                self._resize(size)

        # set value
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
            errors._raise_err(errors.ERR_INCORRECT_VAR_ARRAYSIZE,
                              var_arraysize=self.num_elements,
                              required_arraysize=num_elements_in_array)

        # check and set each of the element's values
        for i, element_value in enumerate(<list> value):
            self._check_and_set_scalar_value(i, element_value, was_set)
            if was_set != NULL and not was_set[0]:
                return 0
        self._set_num_elements_in_array(num_elements_in_array)

    cdef DbType _check_fetch_conversion(self):
        """
        Checks to see if the fetch type can be transformed into the requested
        type. This is only called during fetch when an output type handler is
        specified and the supplied variable has a type other than the fetch
        type. All matches are done using the underlying Oracle type and the
        character set form of the variable metadata is adjusted to
        use the character set form of the fetch metadata where applicable. The
        type to use for the metadata is returned.
        """
        cdef uint8_t from_ora_type_num, to_ora_type_num
        from_ora_type_num = self._fetch_metadata.dbtype._ora_type_num
        to_ora_type_num = self.metadata.dbtype._ora_type_num

        # Oracle BINARY_DOUBLE, BINARY_FLOAT
        if from_ora_type_num in (ORA_TYPE_NUM_BINARY_DOUBLE,
                                 ORA_TYPE_NUM_BINARY_FLOAT):
            if to_ora_type_num == ORA_TYPE_NUM_BINARY_INTEGER:
                self.metadata._py_type_num = PY_TYPE_NUM_INT
                return self._get_adjusted_type(to_ora_type_num)
            elif to_ora_type_num in (ORA_TYPE_NUM_BINARY_DOUBLE,
                                     ORA_TYPE_NUM_BINARY_FLOAT,
                                     ORA_TYPE_NUM_NUMBER):
                self.metadata._py_type_num = PY_TYPE_NUM_FLOAT
                return self._get_adjusted_type(to_ora_type_num)
            elif to_ora_type_num in (ORA_TYPE_NUM_CHAR,
                                     ORA_TYPE_NUM_LONG,
                                     ORA_TYPE_NUM_VARCHAR):
                return self._get_adjusted_type(to_ora_type_num)

        # Oracle BINARY_INTEGER
        elif from_ora_type_num == ORA_TYPE_NUM_BINARY_INTEGER:
            if to_ora_type_num == ORA_TYPE_NUM_NUMBER:
                self.metadata._py_type_num = PY_TYPE_NUM_FLOAT
                return self._get_adjusted_type(to_ora_type_num)
            elif to_ora_type_num in (ORA_TYPE_NUM_CHAR,
                                     ORA_TYPE_NUM_LONG,
                                     ORA_TYPE_NUM_VARCHAR):
                return self._get_adjusted_type(to_ora_type_num)

        # Oracle BLOB
        elif from_ora_type_num == ORA_TYPE_NUM_BLOB:
            if to_ora_type_num in (ORA_TYPE_NUM_RAW, ORA_TYPE_NUM_LONG_RAW):
                self._fetch_metadata.dbtype = DB_TYPE_LONG_RAW
                return self._fetch_metadata.dbtype

        # Oracle CHAR, LONG or VARCHAR
        elif from_ora_type_num in (ORA_TYPE_NUM_CHAR,
                                   ORA_TYPE_NUM_LONG,
                                   ORA_TYPE_NUM_VARCHAR):
            if to_ora_type_num in (ORA_TYPE_NUM_BINARY_DOUBLE,
                                   ORA_TYPE_NUM_BINARY_FLOAT,
                                   ORA_TYPE_NUM_NUMBER):
                self.metadata._py_type_num = PY_TYPE_NUM_FLOAT
                return self._get_adjusted_type(to_ora_type_num)
            elif to_ora_type_num == ORA_TYPE_NUM_BINARY_INTEGER:
                self.metadata._py_type_num = PY_TYPE_NUM_INT
                return self._get_adjusted_type(to_ora_type_num)
            elif to_ora_type_num in (ORA_TYPE_NUM_CHAR,
                                     ORA_TYPE_NUM_LONG,
                                     ORA_TYPE_NUM_VARCHAR):
                return self._get_adjusted_type(to_ora_type_num)

        # Oracle CLOB
        elif from_ora_type_num == ORA_TYPE_NUM_CLOB:
            if to_ora_type_num in (ORA_TYPE_NUM_CHAR,
                                   ORA_TYPE_NUM_LONG,
                                   ORA_TYPE_NUM_VARCHAR):
                self._fetch_metadata.dbtype = \
                        self._get_adjusted_type(ORA_TYPE_NUM_LONG)
                return self._fetch_metadata.dbtype

        # Oracle DATE, TIMESTAMP (WITH (LOCAL) TIME ZONE)
        elif from_ora_type_num in (ORA_TYPE_NUM_DATE,
                                   ORA_TYPE_NUM_TIMESTAMP,
                                   ORA_TYPE_NUM_TIMESTAMP_LTZ,
                                   ORA_TYPE_NUM_TIMESTAMP_TZ):
            if to_ora_type_num in (ORA_TYPE_NUM_DATE,
                                   ORA_TYPE_NUM_TIMESTAMP,
                                   ORA_TYPE_NUM_TIMESTAMP_LTZ,
                                   ORA_TYPE_NUM_TIMESTAMP_TZ,
                                   ORA_TYPE_NUM_CHAR,
                                   ORA_TYPE_NUM_LONG,
                                   ORA_TYPE_NUM_VARCHAR):
                return self._get_adjusted_type(to_ora_type_num)

        # Oracle INTERVAL DAY TO SECOND, INTERVAL YEAR TO MONTH, ROWID
        elif from_ora_type_num in (ORA_TYPE_NUM_INTERVAL_DS,
                                   ORA_TYPE_NUM_INTERVAL_YM,
                                   ORA_TYPE_NUM_ROWID):
            if to_ora_type_num in (ORA_TYPE_NUM_CHAR,
                                   ORA_TYPE_NUM_LONG,
                                   ORA_TYPE_NUM_VARCHAR):
                return self._get_adjusted_type(to_ora_type_num)

        # Oracle JSON
        elif from_ora_type_num == ORA_TYPE_NUM_JSON:
            if to_ora_type_num in (ORA_TYPE_NUM_CHAR,
                                   ORA_TYPE_NUM_VARCHAR):
                # the server won't accept LONG being defined but even so it
                # still sends back LONG data!
                self._fetch_metadata.dbtype = DB_TYPE_LONG
                return DB_TYPE_VARCHAR
            elif to_ora_type_num == ORA_TYPE_NUM_RAW:
                self._fetch_metadata.dbtype = DB_TYPE_RAW
                return self._fetch_metadata.dbtype

        # Oracle NUMBER
        elif from_ora_type_num == ORA_TYPE_NUM_NUMBER:
            if to_ora_type_num == ORA_TYPE_NUM_BINARY_INTEGER:
                self.metadata._py_type_num = PY_TYPE_NUM_INT
                return self._get_adjusted_type(to_ora_type_num)
            elif to_ora_type_num in (ORA_TYPE_NUM_BINARY_DOUBLE,
                                     ORA_TYPE_NUM_BINARY_FLOAT):
                self.metadata._py_type_num = PY_TYPE_NUM_FLOAT
                return self._get_adjusted_type(to_ora_type_num)
            elif to_ora_type_num in (ORA_TYPE_NUM_CHAR,
                                     ORA_TYPE_NUM_LONG,
                                     ORA_TYPE_NUM_VARCHAR):
                return self._get_adjusted_type(to_ora_type_num)

        # Oracle VECTOR
        elif from_ora_type_num == ORA_TYPE_NUM_VECTOR:
            if to_ora_type_num in (ORA_TYPE_NUM_CHAR,
                                   ORA_TYPE_NUM_LONG,
                                   ORA_TYPE_NUM_VARCHAR):
                self._fetch_metadata.dbtype = DB_TYPE_LONG
                return self._fetch_metadata.dbtype
            elif to_ora_type_num == ORA_TYPE_NUM_CLOB:
                self._fetch_metadata.dbtype = DB_TYPE_CLOB
                return self._fetch_metadata.dbtype

        # conversion not supported
        errors._raise_err(errors.ERR_INCONSISTENT_DATATYPES,
                          input_type=self._fetch_metadata.dbtype.name,
                          output_type=self.metadata.dbtype.name)

    cdef int _create_arrow_array(self) except -1:
        """
        Creates an Arrow array based on the type information selected by the
        user.
        """
        cdef ArrowTimeUnit time_unit = NANOARROW_TIME_UNIT_SECOND
        self.metadata._set_arrow_type()
        if self.metadata._arrow_type == NANOARROW_TYPE_TIMESTAMP:
            if self.metadata.scale > 0 and self.metadata.scale <= 3:
                time_unit = NANOARROW_TIME_UNIT_MILLI
            elif self.metadata.scale > 3 and self.metadata.scale <= 6:
                time_unit = NANOARROW_TIME_UNIT_MICRO
            elif self.metadata.scale > 6 and self.metadata.scale <= 9:
                time_unit = NANOARROW_TIME_UNIT_NANO
        self._arrow_array = OracleArrowArray(
            arrow_type=self.metadata._arrow_type,
            name=self.metadata.name,
            precision=self.metadata.precision,
            scale=self.metadata.scale,
            time_unit=time_unit,
        )

    cdef int _finalize_init(self) except -1:
        """
        Internal method that finalizes initialization of the variable.
        """
        self.metadata._finalize_init()
        if self.num_elements == 0:
            self.num_elements = 1
        self._has_returned_data = False

    cdef OracleArrowArray _finish_building_arrow_array(self):
        """
        Finish building the Arrow array associated with the variable and then
        return that array (after clearing it in the variable so that a new
        array will be built if more rows are fetched).
        """
        cdef OracleArrowArray array = self._arrow_array
        array.finish_building()
        self._arrow_array = None
        return array

    cdef DbType _get_adjusted_type(self, uint8_t ora_type_num):
        """
        Returns an adjusted type based on the desired Oracle type and the
        character set form from the fetch metadata. The intent of this function
        is to ensure that the character set form is not changed. For example,
        if the user requests the use of NVARCHAR but the data being fetched is
        of type CLOB, the type will be adjusted to VARCHAR. For those types
        which do not require a character set form, CS_FORM_IMPLICIT is always
        used.
        """
        cdef uint8_t csfrm
        if self.metadata.dbtype._csfrm == 0:
            csfrm = 0
        elif self._fetch_metadata.dbtype._csfrm == 0:
            csfrm = CS_FORM_IMPLICIT
        else:
            csfrm = self._fetch_metadata.dbtype._csfrm
        return DbType._from_ora_type_and_csfrm(ora_type_num, csfrm)

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
        self.metadata.max_size = new_size
        self.metadata.buffer_size = 0
        self.metadata._finalize_init()

    cdef int _set_metadata_from_type(self, object typ) except -1:
        """
        Sets the type and size of the variable given a Python type.
        """
        self.metadata = OracleMetadata.from_type(typ)

    cdef int _set_metadata_from_value(self, object value,
                                      bint is_plsql) except -1:
        """
        Sets the type and size of the variable given a Python value. This
        method is called once for scalars and once per element in a list for
        array values. If a different type is detected an error is raised.
        """
        cdef OracleMetadata metadata
        metadata = OracleMetadata.from_value(value)
        if metadata.dbtype is DB_TYPE_BOOLEAN \
                and not self._conn_impl.supports_bool and not is_plsql:
            metadata.dbtype = DB_TYPE_BINARY_INTEGER
        if self.metadata is None:
            self.metadata = metadata
        elif metadata.dbtype is not self.metadata.dbtype \
                or metadata.objtype is not self.metadata.objtype:
            errors._raise_err(errors.ERR_MIXED_ELEMENT_TYPES, element=value)
        elif metadata.max_size > self.metadata.max_size:
            self.metadata.max_size = metadata.max_size

    cdef int _set_num_elements_in_array(self, uint32_t num_elements) except -1:
        """
        Sets the number of elements in the array.
        """
        self.num_elements_in_array = num_elements

    cdef int _set_scalar_value(self, uint32_t pos, object value) except -1:
        """
        Set the value of the variable at the given position. At this point it
        is assumed that all checks have been performed!
        """
        raise NotImplementedError()

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
