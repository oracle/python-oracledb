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
# Cython file defining the thick Variable implementation class (embedded in
# thick_impl.pyx).
#------------------------------------------------------------------------------

cdef class ThickVarImpl(BaseVarImpl):
    cdef:
        dpiVar *_handle
        dpiData *_data
        StringBuffer _buf
        object _conn

    def __dealloc__(self):
        if self._handle != NULL:
            dpiVar_release(self._handle)

    cdef int _bind(self, object conn, BaseCursorImpl cursor_impl,
                   uint32_t num_execs, object name, uint32_t pos) except -1:
        cdef:
            ThickCursorImpl thick_cursor_impl = <ThickCursorImpl> cursor_impl
            uint32_t name_length, i
            dpiDataBuffer *dbvalue
            const char *name_ptr
            bytes name_bytes
            object cursor
        if self.metadata.dbtype.num == DB_TYPE_NUM_CURSOR:
            for i, cursor in enumerate(self._values):
                if cursor is not None and cursor._impl is None:
                    errors._raise_err(errors.ERR_CURSOR_NOT_OPEN)
                if self._data[i].isNull:
                    continue
                dbvalue = &self._data[i].value
                if dbvalue.asStmt == thick_cursor_impl._handle:
                    errors._raise_err(errors.ERR_SELF_BIND_NOT_SUPPORTED)
        if name is not None:
            name_bytes = name.encode()
            name_ptr = name_bytes
            name_length = <uint32_t> len(name_bytes)
            if dpiStmt_bindByName(thick_cursor_impl._handle, name_ptr,
                                  name_length, self._handle) < 0:
                _raise_from_odpi()
        else:
            if dpiStmt_bindByPos(thick_cursor_impl._handle, pos,
                                 self._handle) < 0:
                _raise_from_odpi()
        if thick_cursor_impl._stmt_info.isReturning and not self._is_value_set:
            self._has_returned_data = True
        self._is_value_set = False

    cdef int _create_handle(self) except -1:
        cdef:
             ThickConnImpl conn_impl = self._conn_impl
             dpiObjectType *obj_type_handle = NULL
             ThickDbObjectTypeImpl obj_type_impl
        if self._handle != NULL:
             dpiVar_release(self._handle)
             self._handle = NULL
        if self.metadata.objtype is not None:
             obj_type_impl = <ThickDbObjectTypeImpl> self.metadata.objtype
             obj_type_handle = obj_type_impl._handle
        if dpiConn_newVar(conn_impl._handle, self.metadata.dbtype.num,
                          self.metadata.dbtype._native_num, self.num_elements,
                          self.metadata.max_size, 0, self.is_array,
                          obj_type_handle, &self._handle, &self._data) < 0:
             _raise_from_odpi()

    cdef int _finalize_init(self) except -1:
        """
        Internal method that finalizes initialization of the variable.
        """
        BaseVarImpl._finalize_init(self)
        if self.metadata.dbtype._native_num in (
            DPI_NATIVE_TYPE_LOB,
            DPI_NATIVE_TYPE_OBJECT,
            DPI_NATIVE_TYPE_STMT,
        ):
            self._values = [None] * self.num_elements
        self._create_handle()

    cdef list _get_array_value(self):
        """
        Internal method to return the value of the array.
        """
        cdef uint32_t i
        return [self._get_scalar_value(i) \
                for i in range(self.num_elements_in_array)]

    cdef object _get_cursor_value(self, dpiDataBuffer *dbvalue, uint32_t pos):
        """
        Returns the cursor stored in the variable at the given position. If a
        cursor was previously available, use it instead of creating a new one.
        """
        cdef:
            ThickCursorImpl cursor_impl
            object cursor
        cursor = self._values[pos]
        if cursor is None:
            cursor = self._conn.cursor()
        cursor_impl = <ThickCursorImpl> cursor._impl
        if dpiStmt_addRef(dbvalue.asStmt) < 0:
            _raise_from_odpi()
        cursor_impl._handle = dbvalue.asStmt
        cursor_impl._fixup_ref_cursor = True
        return cursor

    cdef object _get_dbobject_value(self, dpiDataBuffer *dbvalue,
                                    uint32_t pos):
        """
        Returns the DbObject stored in the variable at the given position. If a
        DbObject was previously available, use it instead of creating a new
        one, unless the handle has changed.
        """
        cdef:
            ThickDbObjectImpl obj_impl
            object obj = None
        if not self._has_returned_data:
            obj = self._values[pos]
        if obj is not None:
            obj_impl = <ThickDbObjectImpl> obj._impl
            if obj_impl._handle == dbvalue.asObject:
                return obj
        obj_impl = ThickDbObjectImpl.__new__(ThickDbObjectImpl)
        obj_impl.type = self.metadata.objtype
        if dpiObject_addRef(dbvalue.asObject) < 0:
            _raise_from_odpi()
        obj_impl._handle = dbvalue.asObject
        return PY_TYPE_DB_OBJECT._from_impl(obj_impl)

    cdef object _get_lob_value(self, dpiDataBuffer *dbvalue, uint32_t pos):
        """
        Returns the LOB stored in the variable at the given position. If a LOB
        was previously created, use it instead of creating a new one, unless
        the handle has changed.
        """
        cdef:
            ThickLobImpl lob_impl
            object lob = None
        if not self._has_returned_data:
            lob = self._values[pos]
        if lob is not None:
            lob_impl = <ThickLobImpl> lob._impl
            if lob_impl._handle == dbvalue.asLOB:
                return lob
        lob_impl = ThickLobImpl._create(self._conn_impl, self.metadata.dbtype,
                                        dbvalue.asLOB)
        return PY_TYPE_LOB._from_impl(lob_impl)

    cdef object _get_scalar_value(self, uint32_t pos):
        """
        Internal method to return the value of the variable at the given
        position.
        """
        cdef:
            uint32_t num_returned_rows
            dpiData *returned_data
            object value
        if self._has_returned_data:
            if dpiVar_getReturnedData(self._handle, pos, &num_returned_rows,
                                      &returned_data) < 0:
                _raise_from_odpi()
            return self._transform_array_to_python(num_returned_rows,
                                                   returned_data)
        value = self._transform_element_to_python(pos, self._data)
        if self.metadata.dbtype._native_num in (
            DPI_NATIVE_TYPE_LOB,
            DPI_NATIVE_TYPE_OBJECT,
            DPI_NATIVE_TYPE_STMT,
        ):
            self._values[pos] = value
        return value

    cdef int _on_reset_bind(self, uint32_t num_rows) except -1:
        """
        Called when the bind variable is being reset, just prior to performing
        a bind operation.
        """
        cdef:
            dpiStmtInfo stmt_info
            uint32_t i
        BaseVarImpl._on_reset_bind(self, num_rows)
        if self.metadata.dbtype.num == DB_TYPE_NUM_CURSOR:
            for i in range(self.num_elements):
                if self._data[i].isNull:
                    continue
                if dpiStmt_getInfo(self._data[i].value.asStmt, &stmt_info) < 0:
                    self._create_handle()
                    break

    cdef int _resize(self, uint32_t new_size) except -1:
        """
        Resize the variable to the new size provided.
        """
        cdef:
            dpiVar *orig_handle = NULL
            uint32_t num_elements, i
            dpiData *source_data
            dpiData *orig_data
        BaseVarImpl._resize(self, new_size)
        orig_data = self._data
        orig_handle = self._handle
        self._handle = NULL
        try:
            self._create_handle()
            if self.is_array:
                if dpiVar_getNumElementsInArray(orig_handle,
                                                &num_elements) < 0:
                    _raise_from_odpi()
                if dpiVar_setNumElementsInArray(self._handle,
                                                num_elements) < 0:
                    _raise_from_odpi()
            for i in range(self.num_elements):
                source_data = &orig_data[i]
                if source_data.isNull:
                    continue
                if dpiVar_setFromBytes(self._handle, i,
                        source_data.value.asBytes.ptr,
                        source_data.value.asBytes.length) < 0:
                    _raise_from_odpi()
        finally:
            dpiVar_release(orig_handle)

    cdef int _set_cursor_value(self, object cursor, uint32_t pos) except -1:
        """
        Sets a cursor value in the variable. If the cursor does not have a
        statement handle already, associate the one created by the variable.
        """
        cdef:
            ThickCursorImpl cursor_impl = cursor._impl
            dpiData *data

        # if the cursor already has a handle, use it directly
        if cursor_impl._handle != NULL:
            if dpiVar_setFromStmt(self._handle, pos, cursor_impl._handle) < 0:
                _raise_from_odpi()

        # otherwise, make use of the statement handle allocated by the variable
        else:
            data = &self._data[pos]
            if dpiStmt_addRef(data.value.asStmt) < 0:
                _raise_from_odpi()
            cursor_impl._handle = data.value.asStmt
        self._values[pos] = cursor
        cursor_impl._fixup_ref_cursor = True
        cursor_impl.statement = None

    cdef int _set_dbobject_value(self, object obj, uint32_t pos) except -1:
        """
        Sets an object value in the variable. The object is retained so that
        multiple calls to getvalue() return the same instance.
        """
        cdef ThickDbObjectImpl obj_impl = <ThickDbObjectImpl> obj._impl
        if dpiVar_setFromObject(self._handle, pos, obj_impl._handle) < 0:
            _raise_from_odpi()
        self._values[pos] = obj

    cdef int _set_lob_value(self, object lob, uint32_t pos) except -1:
        """
        Sets a LOB value in the variable. The LOB is retained so that multiple
        calls to getvalue() return the same instance.
        """
        cdef ThickLobImpl lob_impl = <ThickLobImpl> lob._impl
        if dpiVar_setFromLob(self._handle, pos, lob_impl._handle) < 0:
            _raise_from_odpi()
        self._values[pos] = lob

    cdef int _set_num_elements_in_array(self, uint32_t num_elements) except -1:
        """
        Sets the number of elements in the array.
        """
        BaseVarImpl._set_num_elements_in_array(self, num_elements)
        if dpiVar_setNumElementsInArray(self._handle, num_elements) < 0:
            _raise_from_odpi()

    cdef int _set_scalar_value(self, uint32_t pos, object value) except -1:
        """
        Set the value of the variable at the given position. At this point it
        is assumed that all checks have been performed!
        """
        cdef:
            dpiDataBuffer temp_dbvalue
            dpiDataBuffer *dbvalue
            uint32_t native_num
            dpiBytes *as_bytes
            dpiData *data
        data = &self._data[pos]
        data.isNull = (value is None)
        if not data.isNull:
            native_num = self.metadata.dbtype._native_num
            if native_num == DPI_NATIVE_TYPE_STMT:
                self._set_cursor_value(value, pos)
            elif native_num == DPI_NATIVE_TYPE_LOB:
                self._set_lob_value(value, pos)
            elif native_num == DPI_NATIVE_TYPE_OBJECT:
                self._set_dbobject_value(value, pos)
            else:
                if native_num == DPI_NATIVE_TYPE_BYTES:
                    dbvalue = &temp_dbvalue
                else:
                    dbvalue = &data.value
                if self._buf is None:
                    self._buf = StringBuffer.__new__(StringBuffer)
                _convert_from_python(value, self.metadata, dbvalue, self._buf)
                if native_num == DPI_NATIVE_TYPE_BYTES:
                    as_bytes = &dbvalue.asBytes
                    if dpiVar_setFromBytes(self._handle, pos, as_bytes.ptr,
                                           as_bytes.length) < 0:
                        _raise_from_odpi()

    cdef object _transform_array_to_python(self, uint32_t num_elements,
                                           dpiData *data):
        """
        Transforms an array from ODPI-C to a Python list.
        """
        cdef:
            object element_value
            list return_value
            uint32_t i
        return_value = cpython.PyList_New(num_elements)
        for i in range(num_elements):
            element_value = self._transform_element_to_python(i, data)
            cpython.Py_INCREF(element_value)
            cpython.PyList_SET_ITEM(return_value, i, element_value)
        return return_value

    cdef int _transform_element_to_arrow(self, uint32_t pos):
        """
        Transforms a single element from the value supplied by ODPI-C to its
        equivalent Arrow format.
        """
        cdef:
            dpiData *data = &self._data[pos]
            uint32_t ora_type_num
            OracleData ora_data
            dpiBytes *as_bytes
        ora_data.is_null = data.isNull
        if not data.isNull:
            ora_type_num = self._fetch_metadata.dbtype.num
            if ora_type_num == DPI_ORACLE_TYPE_NATIVE_DOUBLE:
                ora_data.buffer.as_double = data.value.asDouble
            elif ora_type_num == DPI_ORACLE_TYPE_NATIVE_FLOAT:
                ora_data.buffer.as_float = data.value.asFloat
            elif ora_type_num == DPI_ORACLE_TYPE_BOOLEAN:
                ora_data.buffer.as_bool = data.value.asBoolean
            elif ora_type_num in (
                DPI_ORACLE_TYPE_CHAR,
                DPI_ORACLE_TYPE_LONG_VARCHAR,
                DPI_ORACLE_TYPE_LONG_RAW,
                DPI_ORACLE_TYPE_RAW,
                DPI_ORACLE_TYPE_VARCHAR,
            ):
                as_bytes = &data.value.asBytes;
                ora_data.buffer.as_raw_bytes.ptr = \
                        <const char_type *> as_bytes.ptr;
                ora_data.buffer.as_raw_bytes.num_bytes = as_bytes.length;
            elif ora_type_num in (
                DPI_ORACLE_TYPE_DATE,
                DPI_ORACLE_TYPE_TIMESTAMP,
                DPI_ORACLE_TYPE_TIMESTAMP_LTZ,
                DPI_ORACLE_TYPE_TIMESTAMP_TZ,
            ):
                ora_data.buffer.as_date.year = data.value.asTimestamp.year;
                ora_data.buffer.as_date.month = data.value.asTimestamp.month;
                ora_data.buffer.as_date.day = data.value.asTimestamp.day;
                ora_data.buffer.as_date.hour = data.value.asTimestamp.hour;
                ora_data.buffer.as_date.minute = data.value.asTimestamp.minute;
                ora_data.buffer.as_date.second = data.value.asTimestamp.second;
                ora_data.buffer.as_date.fsecond = \
                        data.value.asTimestamp.fsecond // 1000;
                ora_data.buffer.as_date.tz_hour_offset = \
                        data.value.asTimestamp.tzHourOffset;
                ora_data.buffer.as_date.tz_minute_offset = \
                        data.value.asTimestamp.tzMinuteOffset;
            elif ora_type_num == DPI_ORACLE_TYPE_INTERVAL_DS:
                ora_data.buffer.as_interval_ds.days = \
                        data.value.asIntervalDS.days;
                ora_data.buffer.as_interval_ds.hours = \
                        data.value.asIntervalDS.hours;
                ora_data.buffer.as_interval_ds.minutes = \
                        data.value.asIntervalDS.minutes;
                ora_data.buffer.as_interval_ds.seconds = \
                        data.value.asIntervalDS.seconds;
                ora_data.buffer.as_interval_ds.fseconds = \
                        data.value.asIntervalDS.fseconds;
            elif ora_type_num == DPI_ORACLE_TYPE_INTERVAL_YM:
                ora_data.buffer.as_interval_ym.years = \
                        data.value.asIntervalYM.years;
                ora_data.buffer.as_interval_ym.months = \
                        data.value.asIntervalYM.months;
            elif ora_type_num == DPI_ORACLE_TYPE_NUMBER:
                as_bytes = &data.value.asBytes;
                ora_data.buffer.as_number.is_max_negative_value = 0;
                ora_data.buffer.as_number.is_integer = \
                        memchr(as_bytes.ptr, b'.', as_bytes.length) == NULL;
                memcpy(ora_data.buffer.as_number.chars, as_bytes.ptr,
                        as_bytes.length);
                ora_data.buffer.as_number.num_chars = as_bytes.length;
            else:
                errors._raise_err(errors.ERR_DB_TYPE_NOT_SUPPORTED,
                                  name=self._fetch_metadata.dbtype.name)
        convert_oracle_data_to_arrow(self._fetch_metadata, self.metadata,
                                     &ora_data, self._arrow_array)

    cdef object _transform_element_to_python(self, uint32_t pos,
                                             dpiData *data):
        """
        Transforms a single element from the value supplied by ODPI-C to its
        equivalent Python value.
        """
        cdef:
            uint32_t native_num
            object value
        data = &data[pos]
        if not data.isNull:
            native_num = self.metadata.dbtype._native_num
            if native_num == DPI_NATIVE_TYPE_STMT:
                value = self._get_cursor_value(&data.value, pos)
            elif native_num == DPI_NATIVE_TYPE_LOB:
                value = self._get_lob_value(&data.value, pos)
            elif native_num == DPI_NATIVE_TYPE_OBJECT:
                value = self._get_dbobject_value(&data.value, pos)
            else:
                value = _convert_to_python(self._conn_impl, self.metadata,
                                           &data.value, self.bypass_decode,
                                           self._encoding_errors)
            if self.outconverter is not None:
                value = self.outconverter(value)
            return value
        elif self.convert_nulls:
            return self.outconverter(None)
