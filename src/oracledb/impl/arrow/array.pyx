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

    def __cinit__(self):
        self.arrow_array = \
                <ArrowArray*> cpython.PyMem_Calloc(1, sizeof(ArrowArray))
        self.arrow_schema = \
                <ArrowSchema*> cpython.PyMem_Calloc(1, sizeof(ArrowSchema))

    def __dealloc__(self):
        if self.arrow_array != NULL:
            if self.arrow_array.release != NULL:
                ArrowArrayRelease(self.arrow_array)
            cpython.PyMem_Free(self.arrow_array)
        if self.arrow_schema != NULL:
            if self.arrow_schema.release != NULL:
                ArrowSchemaRelease(self.arrow_schema)
            cpython.PyMem_Free(self.arrow_schema)

    cdef int _get_is_null(self, int64_t index, bint* is_null) except -1:
        """
        Returns whether or not the value at the specified index is null.
        """
        cdef:
            ArrowBitmap *bitamp
            int8_t as_bool
        bitmap = ArrowArrayValidityBitmap(self.arrow_array)
        if bitmap != NULL and bitmap.buffer.data != NULL:
            as_bool = ArrowBitGet(bitmap.buffer.data, index)
            is_null[0] = not as_bool
        else:
            is_null[0] = False

    cdef int _get_list_info(self, int64_t index, ArrowArray* arrow_array,
                            int64_t* offset, int64_t* num_elements) except -1:
        """
        Returns the number of elements in the list stored in the array at the
        given index.
        """
        cdef:
            int32_t end_offset
            int32_t* offsets
        offsets = <int32_t*> arrow_array.buffers[1]
        offset[0] = offsets[index]
        if index >= arrow_array.length - 1:
            end_offset = arrow_array.children[0].length
        else:
            end_offset = offsets[index + 1]
        num_elements[0] = end_offset - offsets[index]

    cdef bint _is_sparse_vector(self) except *:
        """
        Returns a boolean indicating if the schema refers to a sparse vector.
        This requires a structure containing the keys for number of dimensions,
        indices and values.
        """
        cdef:
            ArrowSchemaView view
            ArrowSchema *schema
        if self.arrow_schema.n_children != 3:
            return False
        schema = self.arrow_schema.children[0]
        _check_nanoarrow(ArrowSchemaViewInit(&view, schema, NULL))
        if view.type != NANOARROW_TYPE_INT64 \
                or schema.name != b"num_dimensions":
            return False
        schema = self.arrow_schema.children[1]
        _check_nanoarrow(ArrowSchemaViewInit(&view, schema, NULL))
        if view.type != NANOARROW_TYPE_LIST or schema.name != b"indices":
            return False
        _check_nanoarrow(ArrowSchemaViewInit(&view, schema.children[0], NULL))
        if view.type != NANOARROW_TYPE_UINT32:
            return False
        schema = self.arrow_schema.children[2]
        _check_nanoarrow(ArrowSchemaViewInit(&view, schema, NULL))
        if view.type != NANOARROW_TYPE_LIST or schema.name != b"values":
            return False
        _check_nanoarrow(ArrowSchemaViewInit(&view, schema.children[0], NULL))
        self._set_child_arrow_type(view.type)
        return True

    cdef int _set_child_arrow_type(self, ArrowType child_arrow_type) except -1:
        """
        Set the child Arrow type and the corresponding element size in bytes.
        """
        self.child_arrow_type = child_arrow_type
        if child_arrow_type == NANOARROW_TYPE_DOUBLE:
            self.child_element_size = sizeof(double)
        elif child_arrow_type == NANOARROW_TYPE_FLOAT:
            self.child_element_size = sizeof(float)
        elif child_arrow_type == NANOARROW_TYPE_INT8:
            self.child_element_size = sizeof(int8_t)
        elif child_arrow_type == NANOARROW_TYPE_UINT8:
            self.child_element_size = sizeof(uint8_t)

    cdef int _set_time_unit(self, ArrowTimeUnit time_unit) except -1:
        """
        Sets the time unit and the corresponding factor.
        """
        self.time_unit = time_unit
        if time_unit == NANOARROW_TIME_UNIT_MILLI:
            self.time_factor = 1_000
        elif time_unit == NANOARROW_TIME_UNIT_MICRO:
            self.time_factor = 1_000_000
        elif time_unit == NANOARROW_TIME_UNIT_NANO:
            self.time_factor = 1_000_000_000
        else:
            self.time_factor = 1

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
            bint is_null
            uint8_t *ptr
            void* temp
        if array is None:
            array = self
        index = array.arrow_array.length - 1
        array._get_is_null(index, &is_null)
        if is_null:
            self.append_null()
        elif array.arrow_type in (NANOARROW_TYPE_INT64,
                                  NANOARROW_TYPE_TIMESTAMP):
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

    cdef int get_bool(self, int64_t index, bint* is_null,
                      bint* value) except -1:
        """
        Return boolean at the specified index from the Arrow array.
        """
        cdef uint8_t *ptr
        self._get_is_null(index, is_null)
        if not is_null[0]:
            ptr = <uint8_t*> self.arrow_array.buffers[1]
            value[0] = ArrowBitGet(ptr, index)

    cdef int get_bytes(self, int64_t index, bint* is_null, char **ptr,
                       ssize_t *num_bytes) except -1:
        """
        Return bytes at the specified index from the Arrow array.
        """
        cdef:
            int64_t start_offset, end_offset
            int64_t *as_in64
            int32_t *as_int32
            char *source_ptr
        self._get_is_null(index, is_null)
        if not is_null[0]:
            if self.arrow_type == NANOARROW_TYPE_FIXED_SIZE_BINARY:
                source_ptr = <char*> self.arrow_array.buffers[1]
                start_offset = index * self.fixed_size
                end_offset = start_offset + self.fixed_size
            elif self.arrow_type in (
                NANOARROW_TYPE_BINARY,
                NANOARROW_TYPE_STRING
            ):
                source_ptr = <char*> self.arrow_array.buffers[2]
                as_int32 = <int32_t*> self.arrow_array.buffers[1]
                start_offset = as_int32[index]
                end_offset = as_int32[index + 1]
            else:
                source_ptr = <char*> self.arrow_array.buffers[2]
                as_int64 = <int64_t*> self.arrow_array.buffers[1]
                start_offset = as_int64[index]
                end_offset = as_int64[index + 1]
            ptr[0] = source_ptr + start_offset
            num_bytes[0] = end_offset - start_offset

    cdef bytes get_decimal(self, int64_t index, bint* is_null):
        """
        Return bytes corresponding to the decimal value.
        """
        cdef:
            ArrowDecimal decimal
            ArrowBuffer buf
            uint8_t *ptr
        self._get_is_null(index, is_null)
        if not is_null[0]:
            ptr = <uint8_t*> self.arrow_array.buffers[1]
            ArrowDecimalInit(&decimal, 128, self.precision, self.scale)
            ArrowDecimalSetBytes(&decimal, ptr + index * 16)
            ArrowBufferInit(&buf)
            try:
                _check_nanoarrow(ArrowDecimalAppendStringToBuffer(
                    &decimal, &buf
                ))
                return buf.data[:buf.size_bytes]
            finally:
                ArrowBufferReset(&buf)

    cdef int get_double(self, int64_t index, bint* is_null,
                        double* value) except -1:
        """
        Return a double value at the specified index from the Arrow array.
        """
        cdef double* ptr
        self._get_is_null(index, is_null)
        if not is_null[0]:
            ptr = <double*> self.arrow_array.buffers[1]
            value[0] = ptr[index]

    cdef int get_float(self, int64_t index, bint* is_null,
                       float* value) except -1:
        """
        Return a float value at the specified index from the Arrow array.
        """
        cdef float* ptr
        self._get_is_null(index, is_null)
        if not is_null[0]:
            ptr = <float*> self.arrow_array.buffers[1]
            value[0] = ptr[index]

    cdef int get_int64(self, int64_t index, bint* is_null,
                       int64_t* value) except -1:
        """
        Return an int64_t value at the specified index from the Arrow array.
        """
        cdef int64_t* ptr
        self._get_is_null(index, is_null)
        if not is_null[0]:
            ptr = <int64_t*> self.arrow_array.buffers[1]
            value[0] = ptr[index]

    cdef int get_length(self, int64_t* length) except -1:
        """
        Return the number of rows in the array.
        """
        length[0] = self.arrow_array.length

    cdef object get_sparse_vector(self, int64_t index, bint* is_null):
        """
        Return a sparse vector value at the specified index from the Arrow
        array.
        """
        cdef:
            int64_t num_dimensions, offset, num_elements
            array.array indices, values
            ArrowArray *arrow_array
            uint32_t* uint32_ptr
            int64_t* int64_ptr
            char *source_buf
        self._get_is_null(index, is_null)
        if not is_null[0]:

            # get the number of dimensions from the sparse vector
            int64_ptr = <int64_t*> self.arrow_array.children[0].buffers[1]
            num_dimensions = int64_ptr[index]

            # get the indices from the sparse vector
            arrow_array = self.arrow_array.children[1]
            self._get_list_info(index, arrow_array, &offset, &num_elements)
            indices = array.clone(uint32_template, num_elements, False)
            uint32_ptr = <uint32_t*> arrow_array.children[0].buffers[1]
            memcpy(indices.data.as_voidptr, &uint32_ptr[offset],
                   num_elements * sizeof(uint32_t))

            # get the values from the sparse vector
            arrow_array = self.arrow_array.children[2]
            self._get_list_info(index, arrow_array, &offset, &num_elements)
            source_buf = <char*> arrow_array.children[0].buffers[1] + \
                    offset * self.child_element_size
            if self.child_arrow_type == NANOARROW_TYPE_FLOAT:
                values = array.clone(float_template, num_elements, False)
            elif self.child_arrow_type == NANOARROW_TYPE_DOUBLE:
                values = array.clone(double_template, num_elements, False)
            elif self.child_arrow_type == NANOARROW_TYPE_INT8:
                values = array.clone(int8_template, num_elements, False)
            elif self.child_arrow_type == NANOARROW_TYPE_UINT8:
                values = array.clone(uint8_template, num_elements, False)
            else:
                errors._raise_err(errors.ERR_UNEXPECTED_DATA,
                                  data=self.child_arrow_type)
            memcpy(values.data.as_voidptr, source_buf,
                   num_elements * self.child_element_size)
            return (num_dimensions, indices, values)

    cdef object get_vector(self, int64_t index, bint* is_null):
        """
        Return a vector value at the specified index from the Arrow array.
        """
        cdef:
            int64_t offset, end_offset, num_elements
            ArrowBuffer *offsets_buffer
            array.array result
            int32_t *as_int32
            char *source_buf
        self._get_is_null(index, is_null)
        if not is_null[0]:
            if self.arrow_type == NANOARROW_TYPE_FIXED_SIZE_LIST:
                offset = index * self.fixed_size
                num_elements = self.fixed_size
            else:
                self._get_list_info(index, self.arrow_array, &offset,
                                    &num_elements)
            source_buf = <char*> self.arrow_array.children[0].buffers[1] + \
                    offset * self.child_element_size
            if self.child_arrow_type == NANOARROW_TYPE_FLOAT:
                result = array.clone(float_template, num_elements, False)
            elif self.child_arrow_type == NANOARROW_TYPE_DOUBLE:
                result = array.clone(double_template, num_elements, False)
            elif self.child_arrow_type == NANOARROW_TYPE_INT8:
                result = array.clone(int8_template, num_elements, False)
            elif self.child_arrow_type == NANOARROW_TYPE_UINT8:
                result = array.clone(uint8_template, num_elements, False)
            else:
                errors._raise_err(errors.ERR_UNEXPECTED_DATA,
                                  data=self.child_arrow_type)
            memcpy(result.data.as_voidptr, source_buf,
                   num_elements * self.child_element_size)
            return result

    @classmethod
    def from_arrow_array(cls, obj):
        """
        Create an ArrowArrayImpl instance by extracting the information an
        object implementing the PyCapsule Arrow array interface.
        """
        cdef:
            ArrowArrayImpl array_impl
            ArrowSchema *arrow_schema
            ArrowArray *arrow_array
        schema_capsule, array_capsule = obj.__arrow_c_array__()
        arrow_schema = <ArrowSchema*> cpython.PyCapsule_GetPointer(
            schema_capsule, "arrow_schema"
        )
        arrow_array = <ArrowArray*> cpython.PyCapsule_GetPointer(
            array_capsule, "arrow_array"
        )
        array_impl = ArrowArrayImpl.__new__(ArrowArrayImpl)
        array_impl.populate_from_array(arrow_schema, arrow_array)
        return array_impl

    cdef int populate_from_array(self, ArrowSchema* schema,
                                 ArrowArray* array) except -1:
        """
        Populate the array from another array.
        """
        cdef ArrowSchemaView schema_view
        ArrowSchemaMove(schema, self.arrow_schema)
        ArrowArrayMove(array, self.arrow_array)
        memset(&schema_view, 0, sizeof(ArrowSchemaView))
        _check_nanoarrow(
            ArrowSchemaViewInit(&schema_view, self.arrow_schema, NULL)
        )
        self.arrow_type = schema_view.type
        self.name = schema.name.decode()
        self.precision = schema_view.decimal_precision
        self.scale = schema_view.decimal_scale
        self.fixed_size = schema_view.fixed_size
        if schema_view.type == NANOARROW_TYPE_TIMESTAMP:
            self._set_time_unit(schema_view.time_unit)
        elif schema_view.type in (
            NANOARROW_TYPE_FIXED_SIZE_LIST,
            NANOARROW_TYPE_LIST
        ):
            _check_nanoarrow(
                ArrowSchemaViewInit(
                    &schema_view, self.arrow_schema.children[0], NULL
                )
            )
            self._set_child_arrow_type(schema_view.type)
        elif schema_view.type not in (
            NANOARROW_TYPE_BINARY,
            NANOARROW_TYPE_BOOL,
            NANOARROW_TYPE_DECIMAL128,
            NANOARROW_TYPE_DOUBLE,
            NANOARROW_TYPE_FIXED_SIZE_BINARY,
            NANOARROW_TYPE_FLOAT,
            NANOARROW_TYPE_INT64,
            NANOARROW_TYPE_LARGE_BINARY,
            NANOARROW_TYPE_LARGE_STRING,
            NANOARROW_TYPE_STRING,
        ) and not (
            schema_view.type == NANOARROW_TYPE_STRUCT
            and self._is_sparse_vector()
        ):
            errors._raise_err(errors.ERR_ARROW_UNSUPPORTED_DATA_FORMAT,
                              schema_format=schema.format.decode())
        if self.child_arrow_type != 0 and self.child_element_size == 0:
            errors._raise_err(
                errors.ERR_ARROW_UNSUPPORTED_CHILD_DATA_FORMAT,
                schema_format=schema.children[0].format.decode()
            )


    cdef int populate_from_metadata(self, ArrowType arrow_type, str name,
                                    int8_t precision, int8_t scale,
                                    ArrowTimeUnit time_unit,
                                    ArrowType child_arrow_type) except -1:
        """
        Populate the array from the supplied metadata.
        """
        cdef ArrowType storage_type = arrow_type
        self.arrow_type = arrow_type
        self._set_time_unit(time_unit)
        self._set_child_arrow_type(child_arrow_type)
        self.name = name
        if arrow_type == NANOARROW_TYPE_TIMESTAMP:
            storage_type = NANOARROW_TYPE_INT64

        _check_nanoarrow(ArrowArrayInitFromType(self.arrow_array,
                                                storage_type))
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
