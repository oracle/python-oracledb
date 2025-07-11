#------------------------------------------------------------------------------
# Copyright (c) 2025, Oracle and/or its affiliates.
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
# array.pyx
#
# Cython implementation of the ArrowArrayImpl class.
#------------------------------------------------------------------------------

cdef class ArrowArrayImpl:

    def __cinit__(self, ArrowType arrow_type, str name, int8_t precision,
                  int8_t scale, ArrowTimeUnit time_unit,
                  ArrowType child_arrow_type):
        cdef ArrowType storage_type = arrow_type
        self.arrow_type = arrow_type
        self.child_arrow_type = child_arrow_type
        self.time_unit = time_unit
        self.name = name
        self.arrow_array = \
                <ArrowArray*> cpython.PyMem_Malloc(sizeof(ArrowArray))
        if arrow_type == NANOARROW_TYPE_TIMESTAMP:
            storage_type = NANOARROW_TYPE_INT64
        if time_unit == NANOARROW_TIME_UNIT_MILLI:
            self.factor = 1e3
        elif time_unit == NANOARROW_TIME_UNIT_MICRO:
            self.factor = 1e6
        elif time_unit == NANOARROW_TIME_UNIT_NANO:
            self.factor = 1e9
        else:
            self.factor = 1

        self.arrow_schema = \
                <ArrowSchema*> cpython.PyMem_Malloc(sizeof(ArrowSchema))
        if arrow_type == NANOARROW_TYPE_DECIMAL128:
            self.precision = precision
            self.scale = scale
            ArrowSchemaInit(self.arrow_schema)
            _check_nanoarrow(
                ArrowSchemaSetTypeDecimal(
                    self.arrow_schema,
                    arrow_type,
                    precision,
                    scale
                )
            )
        elif arrow_type == NANOARROW_TYPE_STRUCT:
            # Currently struct is used for Sparse vector only
            build_arrow_schema_for_sparse_vector(self.arrow_schema,
                                                 child_arrow_type)
        else:
            _check_nanoarrow(
                ArrowSchemaInitFromType(
                    self.arrow_schema,
                    storage_type
                )
            )
            if arrow_type == NANOARROW_TYPE_TIMESTAMP:
                _check_nanoarrow(
                    ArrowSchemaSetTypeDateTime(
                        self.arrow_schema,
                        arrow_type,
                        time_unit,
                        NULL
                    )
                )
        if arrow_type == NANOARROW_TYPE_LIST:
            # Set the schema for child using child_arrow_type
            _check_nanoarrow(
                ArrowSchemaSetType(
                    self.arrow_schema.children[0],
                    child_arrow_type
                )
            )
            _check_nanoarrow(
                ArrowArrayInitFromSchema(
                    self.arrow_array,
                    self.arrow_schema,
                    NULL
                )
            )
        elif arrow_type == NANOARROW_TYPE_STRUCT:
            _check_nanoarrow(
                ArrowArrayInitFromSchema(
                    self.arrow_array,
                    self.arrow_schema,
                    NULL
                )
            )
        else: # primitive type array init
            _check_nanoarrow(
                ArrowArrayInitFromType(
                    self.arrow_array,
                    storage_type
                )
            )
        _check_nanoarrow(ArrowArrayStartAppending(self.arrow_array))
        _check_nanoarrow(ArrowSchemaSetName(self.arrow_schema, name.encode()))

    def __dealloc__(self):
        if self.arrow_array != NULL:
            if self.arrow_array.release != NULL:
                ArrowArrayRelease(self.arrow_array)
            cpython.PyMem_Free(self.arrow_array)
        if self.arrow_schema != NULL:
            if self.arrow_schema.release != NULL:
                ArrowSchemaRelease(self.arrow_schema)
            cpython.PyMem_Free(self.arrow_schema)

    cdef int append_bytes(self, void* ptr, int64_t num_bytes) except -1:
        """
        Append a value of type bytes to the array.
        """
        cdef ArrowBufferView data
        data.data.data = ptr
        data.size_bytes = num_bytes
        _check_nanoarrow(ArrowArrayAppendBytes(self.arrow_array, data))

    cdef int append_decimal(self, void* ptr, int64_t num_bytes) except -1:
        """
        Append a value of type ArrowDecimal to the array

        Arrow decimals are fixed-point decimal numbers encoded as a
        scaled integer. decimal128(7, 3) can exactly represent the numbers
        1234.567 and -1234.567 encoded internally as the 128-bit integers
        1234567 and -1234567, respectively.
        """
        cdef:
            ArrowStringView decimal_view
            ArrowDecimal decimal
        decimal_view.data = <char*> ptr
        decimal_view.size_bytes = num_bytes
        ArrowDecimalInit(&decimal, 128, self.precision, self.scale)
        _check_nanoarrow(ArrowDecimalSetDigits(&decimal, decimal_view))
        _check_nanoarrow(ArrowArrayAppendDecimal(self.arrow_array, &decimal))

    cdef int append_double(self, double value) except -1:
        """
        Append a value of type double to the array.
        """
        _check_nanoarrow(ArrowArrayAppendDouble(self.arrow_array, value))

    cdef int append_float(self, float value) except -1:
        """
        Append a value of type float to the array.
        """
        self.append_double(value)

    cdef int append_int64(self, int64_t value) except -1:
        """
        Append a value of type int64_t to the array.
        """
        _check_nanoarrow(ArrowArrayAppendInt(self.arrow_array, value))

    cdef int append_last_value(self, ArrowArrayImpl array) except -1:
        """
        Appends the last value of the given array to this array.
        """
        cdef:
            int32_t start_offset, end_offset
            ArrowBuffer *offsets_buffer
            ArrowBuffer *data_buffer
            ArrowDecimal decimal
            int64_t *as_int64
            int32_t *as_int32
            double *as_double
            float *as_float
            int8_t as_bool
            int64_t index
            uint8_t *ptr
            void* temp
            ArrowBitmap *bitamp
        if array is None:
            array = self
        index = array.arrow_array.length - 1
        bitmap = ArrowArrayValidityBitmap(array.arrow_array)
        if bitmap != NULL and bitmap.buffer.data != NULL:
            as_bool = ArrowBitGet(bitmap.buffer.data, index)
            if not as_bool:
                self.append_null()
                return 0
        if array.arrow_type in (NANOARROW_TYPE_INT64, NANOARROW_TYPE_TIMESTAMP):
            data_buffer = ArrowArrayBuffer(array.arrow_array, 1)
            as_int64 = <int64_t*> data_buffer.data
            self.append_int64(as_int64[index])
        elif array.arrow_type == NANOARROW_TYPE_DOUBLE:
            data_buffer = ArrowArrayBuffer(array.arrow_array, 1)
            as_double = <double*> data_buffer.data
            self.append_double(as_double[index])
        elif array.arrow_type == NANOARROW_TYPE_FLOAT:
            data_buffer = ArrowArrayBuffer(array.arrow_array, 1)
            as_float = <float*> data_buffer.data
            self.append_double(as_float[index])
        elif array.arrow_type == NANOARROW_TYPE_BOOL:
            data_buffer = ArrowArrayBuffer(array.arrow_array, 1)
            as_bool = ArrowBitGet(data_buffer.data, index)
            self.append_int64(as_bool)
        elif array.arrow_type == NANOARROW_TYPE_DECIMAL128:
            data_buffer = ArrowArrayBuffer(array.arrow_array, 1)
            ArrowDecimalInit(&decimal, 128, self.precision, self.scale)
            ptr = data_buffer.data + index * 16
            ArrowDecimalSetBytes(&decimal, ptr)
            _check_nanoarrow(ArrowArrayAppendDecimal(self.arrow_array,
                                                     &decimal))
        elif array.arrow_type in (
                NANOARROW_TYPE_BINARY,
                NANOARROW_TYPE_STRING
        ):
            offsets_buffer = ArrowArrayBuffer(array.arrow_array, 1)
            data_buffer = ArrowArrayBuffer(array.arrow_array, 2)
            as_int32 = <int32_t*> offsets_buffer.data
            start_offset = as_int32[index]
            end_offset = as_int32[index + 1]
            temp = cpython.PyMem_Malloc(end_offset - start_offset)
            memcpy(temp, &data_buffer.data[start_offset],
                   end_offset - start_offset)
            try:
                self.append_bytes(temp, end_offset - start_offset)
            finally:
                cpython.PyMem_Free(temp)

        elif array.arrow_type in (
                NANOARROW_TYPE_LARGE_BINARY,
                NANOARROW_TYPE_LARGE_STRING
        ):
            offsets_buffer = ArrowArrayBuffer(array.arrow_array, 1)
            data_buffer = ArrowArrayBuffer(array.arrow_array, 2)
            as_int64 = <int64_t*> offsets_buffer.data
            start_offset = as_int64[index]
            end_offset = as_int64[index + 1]
            temp = cpython.PyMem_Malloc(end_offset - start_offset)
            memcpy(temp, &data_buffer.data[start_offset],
                   end_offset - start_offset)
            try:
                self.append_bytes(temp, end_offset - start_offset)
            finally:
                cpython.PyMem_Free(temp)

    cdef int append_null(self) except -1:
        """
        Append a null value to the array.
        """
        _check_nanoarrow(ArrowArrayAppendNull(self.arrow_array, 1))

    cdef int append_vector(self, array.array value) except -1:
        """
        Append a vector to the array.
        """
        if self.child_arrow_type == NANOARROW_TYPE_FLOAT:
            append_float_array(self.arrow_array, value)
        elif self.child_arrow_type == NANOARROW_TYPE_DOUBLE:
            append_double_array(self.arrow_array, value)
        elif self.child_arrow_type == NANOARROW_TYPE_INT8:
            append_int8_array(self.arrow_array, value)
        elif self.child_arrow_type == NANOARROW_TYPE_UINT8:
            append_uint8_array(self.arrow_array, value)

    cdef int append_sparse_vector(self,
                                  int64_t num_dims,
                                  array.array indices,
                                  array.array values) except -1:
        """
        Append a sparse vector to the array.
        """
        cdef ArrowArray *array

        # validate that the array supports sparse vectors
        if self.arrow_type != NANOARROW_TYPE_STRUCT:
            errors._raise_err(errors.ERR_ARROW_SPARSE_VECTOR_NOT_ALLOWED)

        # append number of dimensions
        array = self.arrow_array.children[0]
        _check_nanoarrow(ArrowArrayAppendInt(array, num_dims))

        # append indices array
        array = self.arrow_array.children[1]
        append_uint32_array(array, indices)

        # append values array
        array = self.arrow_array.children[2]
        if self.child_arrow_type == NANOARROW_TYPE_FLOAT:
            append_float_array(array, values)
        elif self.child_arrow_type == NANOARROW_TYPE_DOUBLE:
            append_double_array(array, values)
        elif self.child_arrow_type == NANOARROW_TYPE_INT8:
            append_int8_array(array, values)
        elif self.child_arrow_type == NANOARROW_TYPE_UINT8:
            append_uint8_array(array, values)

        # indicate structure is completed
        _check_nanoarrow(ArrowArrayFinishElement(self.arrow_array))

    cdef int finish_building(self) except -1:
        """
        Finish building the array. No more data will be added to it.
        """
        _check_nanoarrow(ArrowArrayFinishBuildingDefault(self.arrow_array,
                                                         NULL))

    def get_array_capsule(self):
        """
        Internal method for getting a PyCapsule pointer to the array.
        """
        cdef ArrowArray *array
        array = <ArrowArray*> cpython.PyMem_Malloc(sizeof(ArrowArray))
        try:
            copy_arrow_array(self, self.arrow_array, array)
        except:
            cpython.PyMem_Free(array)
            raise
        return cpython.PyCapsule_New(
            array, 'arrow_array', &pycapsule_array_deleter
        )

    def get_data_type(self):
        """
        Internal method for getting the data type associated with the array.
        """
        cdef char buffer[81]
        ArrowSchemaToString(self.arrow_schema, buffer, sizeof(buffer), 0)
        return buffer.decode()

    def get_name(self):
        """
        Internal method for getting the name associated with the array.
        """
        return self.name

    def get_null_count(self):
        """
        Internal method for getting the number of rows containing null values.
        """
        return self.arrow_array.null_count

    def get_num_rows(self):
        """
        Internal method for getting the number of rows in the array.
        """
        return self.arrow_array.length

    def get_schema_capsule(self):
        """
        Internal method for getting a PyCapsule pointer to the schema.
        """
        cdef ArrowSchema *schema
        schema = <ArrowSchema*> cpython.PyMem_Malloc(sizeof(ArrowSchema))
        try:
            _check_nanoarrow(ArrowSchemaDeepCopy(self.arrow_schema, schema))
        except:
            cpython.PyMem_Free(schema)
            raise
        return cpython.PyCapsule_New(
            schema, 'arrow_schema', &pycapsule_schema_deleter
        )


cdef void pycapsule_array_deleter(object array_capsule) noexcept:
    """
    Called when the PyCapsule pointer is no longer required and performs the
    necessary cleanup.
    """
    cdef ArrowArray* array
    array = <ArrowArray*> cpython.PyCapsule_GetPointer(
        array_capsule, "arrow_array"
    )
    if array.release != NULL:
        ArrowArrayRelease(array)
    cpython.PyMem_Free(array)


cdef void pycapsule_schema_deleter(object schema_capsule) noexcept:
    """
    Called when the PyCapsule pointer is no longer required and performs the
    necessary cleanup.
    """
    cdef ArrowSchema* schema
    schema = <ArrowSchema*> cpython.PyCapsule_GetPointer(
        schema_capsule, "arrow_schema"
    )
    if schema.release != NULL:
        ArrowSchemaRelease(schema)
    cpython.PyMem_Free(schema)
