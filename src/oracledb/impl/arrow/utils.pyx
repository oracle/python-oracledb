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
# utils.pyx
#
# Contains utilities and definitions used by the other files in this module.
#------------------------------------------------------------------------------

cdef extern from "nanoarrow.c":

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

    cdef struct ArrowBitmap:
        ArrowBuffer buffer

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
    ArrowErrorCode ArrowArrayFinishElement(ArrowArray *array)
    ArrowErrorCode ArrowArrayInitFromSchema(ArrowArray *array,
                                            ArrowSchema *schema,
                                            ArrowError *error)
    ArrowErrorCode ArrowArrayInitFromType(ArrowArray* array,
                                          ArrowType storage_type)
    void ArrowArrayRelease(ArrowArray *array)
    ArrowErrorCode ArrowArrayReserve(ArrowArray* array,
                                     int64_t additional_size_elements)
    ArrowErrorCode ArrowArrayStartAppending(ArrowArray* array)
    ArrowBitmap* ArrowArrayValidityBitmap(ArrowArray* array)
    ArrowErrorCode ArrowArrayViewInitFromArray(ArrowArrayView* array_view,
                                               ArrowArray* array)
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
    ArrowErrorCode ArrowSchemaSetType(ArrowSchema * schema, ArrowType type)
    ArrowErrorCode ArrowSchemaSetTypeDateTime(ArrowSchema* schema,
                                              ArrowType arrow_type,
                                              ArrowTimeUnit time_unit,
                                              const char* timezone)
    ArrowErrorCode ArrowSchemaSetTypeStruct(ArrowSchema *schema,
                                            int64_t n_children)
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



cdef int append_double_array(ArrowArray *arrow_array,
                             array.array value) except -1:
    """
    Appends an array of doubles to the Arrow array.
    """
    cdef:
        ArrowArray *child_array = arrow_array.children[0]
        double *double_buf = value.data.as_doubles
        Py_ssize_t i
    for i in range(len(value)):
        _check_nanoarrow(ArrowArrayAppendDouble(child_array, double_buf[i]))
    _check_nanoarrow(ArrowArrayFinishElement(arrow_array))


cdef int append_float_array(ArrowArray *arrow_array,
                            array.array value) except -1:
    """
    Appends an array of floats to the Arrow array.
    """
    cdef:
        ArrowArray *child_array = arrow_array.children[0]
        float *float_buf = value.data.as_floats
        Py_ssize_t i
    for i in range(len(value)):
        _check_nanoarrow(ArrowArrayAppendDouble(child_array, float_buf[i]))
    _check_nanoarrow(ArrowArrayFinishElement(arrow_array))


cdef int append_int8_array(ArrowArray *arrow_array,
                           array.array value) except -1:
    """
    Appends an array of signed one-byte integers to the Arrow array.
    """
    cdef:
        ArrowArray *child_array = arrow_array.children[0]
        int8_t *int8_buf = value.data.as_schars
        Py_ssize_t i
    for i in range(len(value)):
        _check_nanoarrow(ArrowArrayAppendInt(child_array, int8_buf[i]))
    _check_nanoarrow(ArrowArrayFinishElement(arrow_array))


cdef int append_uint8_array(ArrowArray *arrow_array,
                            array.array value) except -1:
    """
    Appends an array of unsigned one-byte integers to the Arrow array.
    """
    cdef:
        ArrowArray *child_array = arrow_array.children[0]
        uint8_t *uint8_buf = value.data.as_uchars
        Py_ssize_t i
    for i in range(len(value)):
        _check_nanoarrow(ArrowArrayAppendInt(child_array, uint8_buf[i]))
    _check_nanoarrow(ArrowArrayFinishElement(arrow_array))


cdef int append_uint32_array(ArrowArray *arrow_array,
                             array.array value) except -1:
    """
    Appends an array of unsigned four-byte integers to the Arrow array. Note
    that Python's array.array doesn't natively support uint32_t but an upper
    layer has verified that the data in the buffer consists of only four byte
    integers.
    """
    cdef:
        uint32_t *uint32_buf = <uint32_t*> value.data.as_voidptr
        ArrowArray *child_array = arrow_array.children[0]
        Py_ssize_t i
    for i in range(len(value)):
        _check_nanoarrow(ArrowArrayAppendInt(child_array, uint32_buf[i]))
    _check_nanoarrow(ArrowArrayFinishElement(arrow_array))


cdef void arrow_buffer_dealloc_callback(ArrowBufferAllocator *allocator,
                                        uint8_t *ptr, int64_t size):
    """
    ArrowBufferDeallocatorCallback for an ArrowBuffer borrowed from an Arrow
    array.
    """
    cpython.Py_DECREF(<ArrowArrayImpl> allocator.private_data)


cdef int copy_arrow_array(ArrowArrayImpl array_impl,
                          ArrowArray *src, ArrowArray *dest) except -1:
    """
    Shallow copy source ArrowArray to destination ArrowArray. The source
    ArrowArray belongs to the wrapper ArrowArrayImpl. The shallow copy idea
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

    # Borrow an ArrowBuffer belonging to ArrowArrayImpl. The ArrowBuffer can
    # belong to an immediate ArrowArray or a child (in case of nested types).
    # Either way, we PY_INCREF(array_impl), so that it is not
    # prematurely garbage collected. The corresponding PY_DECREF happens in the
    # ArrowBufferDeAllocator callback.
    for i in range(src.n_buffers):
        if src.buffers[i] != NULL:
            dest_buffer = ArrowArrayBuffer(dest, i)
            dest_buffer.data = <uint8_t *> src.buffers[i]
            dest_buffer.size_bytes = 0
            dest_buffer.allocator = ArrowBufferDeallocator(
                <ArrowBufferDeallocatorCallback> arrow_buffer_dealloc_callback,
                <void *> array_impl
            )
            cpython.Py_INCREF(array_impl)
        dest.buffers[i] = src.buffers[i]
    dest.n_buffers = src.n_buffers

    # shallow copy of children (recursive call)
    if src.n_children > 0:
        _check_nanoarrow(ArrowArrayAllocateChildren(dest, src.n_children))
        for i in range(src.n_children):
            copy_arrow_array(array_impl, src.children[i], dest.children[i])


cdef int build_arrow_schema_for_sparse_vector(
    ArrowSchema *schema,
    ArrowType vector_value_type
) except -1:

    # Initialize struct with 3 fields - num_dimensions, indices, values
    ArrowSchemaInit(schema)
    _check_nanoarrow(ArrowSchemaSetTypeStruct(schema, 3))

    # first child: "num_dimensions"
    _check_nanoarrow(
        ArrowSchemaSetType(schema.children[0], NANOARROW_TYPE_INT64)
    )
    _check_nanoarrow(ArrowSchemaSetName(schema.children[0], "num_dimensions"))

    # second child: "indices"
    _check_nanoarrow(ArrowSchemaSetType(
            schema.children[1],
            NANOARROW_TYPE_LIST
        )
    )
    _check_nanoarrow(
        ArrowSchemaSetType(
            schema.children[1].children[0],
            NANOARROW_TYPE_UINT32
        )
    )
    _check_nanoarrow(ArrowSchemaSetName(schema.children[1], "indices"))

    # third child: "values"
    _check_nanoarrow(
        ArrowSchemaSetType(
            schema.children[2],
            NANOARROW_TYPE_LIST
        )
    )
    _check_nanoarrow(
        ArrowSchemaSetType(
            schema.children[2].children[0],
            vector_value_type
        )
    )
    _check_nanoarrow(ArrowSchemaSetName(schema.children[2], "values"))
