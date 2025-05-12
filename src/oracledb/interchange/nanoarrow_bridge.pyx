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
# nanoarrow_bridge.pyx
#
# Cython wrapper around the Arrow C Data interface
#------------------------------------------------------------------------------

cimport cpython

from libc.stdint cimport uintptr_t
from libc.string cimport memcpy, strlen, strchr

from .. import errors

cdef extern from "nanoarrow/nanoarrow.c":

    ctypedef int ArrowErrorCode

    ctypedef void (*ArrowBufferDeallocatorCallback)

    cdef struct ArrowBufferAllocator:
        void *private_data

    cdef struct ArrowBuffer:
        uint8_t *data
        int64_t size_bytes
        ArrowBufferAllocator allocator

    cdef union ArrowBufferViewData:
        const void* data

    cdef struct ArrowBufferView:
        ArrowBufferViewData data
        int64_t size_bytes

    cdef struct ArrowArrayView:
        ArrowBufferView *buffer_views

    cdef struct ArrowDecimal:
        pass

    cdef struct ArrowError:
        pass

    cdef struct ArrowStringView:
        const char* data
        int64_t size_bytes

    cdef ArrowErrorCode NANOARROW_OK

    ArrowErrorCode ArrowArrayAllocateChildren(ArrowArray *array,
                                              int64_t n_children)
    ArrowErrorCode ArrowArrayAppendBytes(ArrowArray* array,
                                         ArrowBufferView value)
    ArrowErrorCode ArrowArrayAppendDecimal(ArrowArray* array,
                                           const ArrowDecimal* value)
    ArrowErrorCode ArrowArrayAppendDouble(ArrowArray* array, double value)
    ArrowErrorCode ArrowArrayAppendInt(ArrowArray* array, int64_t value)
    ArrowErrorCode ArrowArrayAppendNull(ArrowArray* array, int64_t n)
    ArrowBuffer* ArrowArrayBuffer(ArrowArray* array, int64_t i)
    ArrowErrorCode ArrowArrayFinishBuildingDefault(ArrowArray* array,
                                                   ArrowError* error)
    ArrowErrorCode ArrowArrayInitFromType(ArrowArray* array,
                                          ArrowType storage_type)
    void ArrowArrayRelease(ArrowArray *array)
    ArrowErrorCode ArrowArrayReserve(ArrowArray* array,
                                     int64_t additional_size_elements)
    ArrowErrorCode ArrowArrayStartAppending(ArrowArray* array)
    ArrowErrorCode ArrowArrayViewInitFromSchema(ArrowArrayView* array_view,
                                                const ArrowSchema* schema,
                                                ArrowError* error)
    ArrowErrorCode ArrowArrayViewSetArray(ArrowArrayView* array_view,
                                          const ArrowArray* array,
                                          ArrowError* error)
    int8_t ArrowBitGet(const uint8_t* bits, int64_t i)
    ArrowBufferAllocator ArrowBufferDeallocator(ArrowBufferDeallocatorCallback,
                                                void *private_data)
    void ArrowDecimalInit(ArrowDecimal* decimal, int32_t bitwidth,
                          int32_t precision, int32_t scale)
    void ArrowDecimalSetBytes(ArrowDecimal *decimal, const uint8_t* value)
    ArrowErrorCode ArrowDecimalSetDigits(ArrowDecimal* decimal,
                                         ArrowStringView value)
    ArrowErrorCode ArrowSchemaDeepCopy(const ArrowSchema *schema,
                                       ArrowSchema *schema_out)
    void ArrowSchemaInit(ArrowSchema* schema)
    ArrowErrorCode ArrowSchemaInitFromType(ArrowSchema* schema, ArrowType type)
    void ArrowSchemaRelease(ArrowSchema *schema)
    ArrowErrorCode ArrowSchemaSetName(ArrowSchema* schema, const char* name)
    ArrowErrorCode ArrowSchemaSetTypeDateTime(ArrowSchema* schema,
                                              ArrowType arrow_type,
                                              ArrowTimeUnit time_unit,
                                              const char* timezone)
    ArrowErrorCode ArrowSchemaSetTypeDecimal(ArrowSchema* schema,
                                             ArrowType type,
                                             int32_t decimal_precision,
                                             int32_t decimal_scale)
    int64_t ArrowSchemaToString(const ArrowSchema* schema, char* out,
                                int64_t n, char recursive)

cdef int _check_nanoarrow(int code) except -1:
    """
    Checks the return code of the nanoarrow function and raises an exception if
    it is not NANOARROW_OK.
    """
    if code != NANOARROW_OK:
        errors._raise_err(errors.ERR_ARROW_C_API_ERROR, code=code)


cdef void pycapsule_array_deleter(object array_capsule) noexcept:
    cdef ArrowArray* array = <ArrowArray*> cpython.PyCapsule_GetPointer(
        array_capsule, "arrow_array"
    )
    if array.release != NULL:
        ArrowArrayRelease(array)
    cpython.PyMem_Free(array)


cdef void pycapsule_schema_deleter(object schema_capsule) noexcept:
    cdef ArrowSchema* schema = <ArrowSchema*> cpython.PyCapsule_GetPointer(
        schema_capsule, "arrow_schema"
    )
    if schema.release != NULL:
        ArrowSchemaRelease(schema)
    cpython.PyMem_Free(schema)


cdef void arrow_buffer_dealloc_callback(ArrowBufferAllocator *allocator,
                                        uint8_t *ptr, int64_t size):
    """
    ArrowBufferDeallocatorCallback for an ArrowBuffer borrowed from
    OracleArrowArray
    """
    cpython.Py_DECREF(<OracleArrowArray> allocator.private_data)


cdef int copy_arrow_array(OracleArrowArray oracle_arrow_array,
                          ArrowArray *src, ArrowArray *dest) except -1:
    """
    Shallow copy source ArrowArray to destination ArrowArray. The source
    ArrowArray belongs to the wrapper OracleArrowArray. The shallow copy idea
    is borrowed from nanoarrow:
    https://github.com/apache/arrow-nanoarrow/main/blob/python
    """
    cdef:
        ArrowBuffer *dest_buffer
        ssize_t i
    _check_nanoarrow(
        ArrowArrayInitFromType(
            dest, NANOARROW_TYPE_UNINITIALIZED
        )
    )

    # Copy metadata
    dest.length = src.length
    dest.offset = src.offset
    dest.null_count = src.null_count

    # Borrow an ArrowBuffer belonging to OracleArrowArray. The ArrowBuffer can
    # belong to an immediate ArrowArray or a child (in case of nested types).
    # Either way, we PY_INCREF(oracle_arrow_array), so that it is not
    # prematurely garbage collected. The corresponding PY_DECREF happens in the
    # ArrowBufferDeAllocator callback.
    for i in range(src.n_buffers):
        if src.buffers[i] != NULL:
            dest_buffer = ArrowArrayBuffer(dest, i)
            dest_buffer.data = <uint8_t *> src.buffers[i]
            dest_buffer.size_bytes = 0
            dest_buffer.allocator = ArrowBufferDeallocator(
                <ArrowBufferDeallocatorCallback> arrow_buffer_dealloc_callback,
                <void *> oracle_arrow_array
            )
            cpython.Py_INCREF(oracle_arrow_array)
        dest.buffers[i] = src.buffers[i]
    dest.n_buffers = src.n_buffers

    # shallow copy of children (recursive call)
    if src.n_children > 0:
        _check_nanoarrow(ArrowArrayAllocateChildren(dest, src.n_children))
        for i in range(src.n_children):
            copy_arrow_array(
                oracle_arrow_array, src.children[i], dest.children[i]
            )


cdef class OracleArrowArray:

    def __cinit__(self, ArrowType arrow_type, str name, int8_t precision,
                  int8_t scale, ArrowTimeUnit time_unit):
        cdef ArrowType storage_type = arrow_type
        self.arrow_type = arrow_type
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

        _check_nanoarrow(ArrowArrayInitFromType(self.arrow_array,
                                                storage_type))
        self.arrow_schema = \
                <ArrowSchema*> cpython.PyMem_Malloc(sizeof(ArrowSchema))
        _check_nanoarrow(ArrowArrayStartAppending(self.arrow_array))
        if arrow_type == NANOARROW_TYPE_DECIMAL128:
            self.precision = precision
            self.scale = scale
            ArrowSchemaInit(self.arrow_schema)
            _check_nanoarrow(ArrowSchemaSetTypeDecimal(self.arrow_schema,
                                                       arrow_type,
                                                       precision, scale))
        else:
            _check_nanoarrow(ArrowSchemaInitFromType(self.arrow_schema,
                                                     storage_type))
            if arrow_type == NANOARROW_TYPE_TIMESTAMP:
                _check_nanoarrow(ArrowSchemaSetTypeDateTime(self.arrow_schema,
                                                            arrow_type,
                                                            time_unit, NULL))
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

    def __len__(self):
        return self.arrow_array.length

    def __repr__(self):
        return (
            f"OracleArrowArray(name={self.name}, "
            f"len={self.arrow_array.length}, "
            f"type={self._schema_to_string()})"
        )

    def __str__(self):
        return self.__repr__()

    cdef str _schema_to_string(self):
        """
        Converts the schema to a string representation.
        """
        cdef char buffer[81]
        ArrowSchemaToString(self.arrow_schema, buffer, sizeof(buffer), 0)
        return buffer.decode()

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

    cdef int append_last_value(self, OracleArrowArray array) except -1:
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
        if array is None:
            array = self
        index = array.arrow_array.length - 1
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

    cdef int finish_building(self) except -1:
        """
        Finish building the array. No more data will be added to it.
        """
        _check_nanoarrow(ArrowArrayFinishBuildingDefault(self.arrow_array,
                                                         NULL))

    def get_buffer_info(self):
        """
        Get buffer information required by the dataframe interchange logic.
        """
        cdef:
            int64_t n_buffers = self.arrow_array.n_buffers
            ArrowBufferView *buffer
            ArrowArrayView view
        _check_nanoarrow(ArrowArrayViewInitFromSchema(&view, self.arrow_schema,
                                                      NULL))
        _check_nanoarrow(ArrowArrayViewSetArray(&view, self.arrow_array, NULL))

        # initialize all buffers to None to begin with
        buffers = {
            "validity": None,
            "offsets": None,
            "data": None
        }

        # validity buffer
        if n_buffers > 0 and self.arrow_array.null_count > 0:
            buffer = &view.buffer_views[0]
            buffers["validity"] = (
                buffer.size_bytes,
                <uintptr_t> buffer.data.data
            )

        # data / offset buffer
        if n_buffers == 2:
            buffer = &view.buffer_views[1]
            buffers["data"] = (
                buffer.size_bytes,
                <uintptr_t> buffer.data.data
            )
        elif n_buffers == 3:
            buffer = &view.buffer_views[1]
            buffers["offsets"] = (
                buffer.size_bytes,
                <uintptr_t> buffer.data.data
            )
            buffer = &view.buffer_views[2]
            buffers["data"] = (
                buffer.size_bytes,
                <uintptr_t> buffer.data.data
            )

        return buffers

    @property
    def null_count(self) -> int:
        return self.arrow_array.null_count

    @property
    def offset(self) -> int:
        return self.arrow_array.offset

    def __arrow_c_schema__(self):
        """
        Export an ArrowSchema PyCapsule
        """
        cdef ArrowSchema *exported_schema = \
            <ArrowSchema*> cpython.PyMem_Malloc(sizeof(ArrowSchema))
        try:
            _check_nanoarrow(
                ArrowSchemaDeepCopy(
                    self.arrow_schema,
                    exported_schema
                )
            )
        except:
            cpython.PyMem_Free(exported_schema)
            raise
        return cpython.PyCapsule_New(
            exported_schema, 'arrow_schema', &pycapsule_schema_deleter
        )

    def __arrow_c_array__(self, requested_schema=None):
        """
        Returns
        -------
        Tuple[PyCapsule, PyCapsule]
            A pair of PyCapsules containing a C ArrowSchema and ArrowArray,
            respectively.
        """
        if requested_schema is not None:
            raise NotImplementedError("requested_schema")
        cdef ArrowArray *exported_array = \
            <ArrowArray *> cpython.PyMem_Malloc(sizeof(ArrowArray))
        try:
            copy_arrow_array(self, self.arrow_array, exported_array)
            array_capsule = cpython.PyCapsule_New(
                exported_array, 'arrow_array', &pycapsule_array_deleter
            )
        except:
            cpython.PyMem_Free(exported_array)
            raise
        return self.__arrow_c_schema__(), array_capsule
