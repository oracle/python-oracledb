#------------------------------------------------------------------------------
# Copyright (c) 2023, 2024, Oracle and/or its affiliates.
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
# vector.pyx
#
# Cython file defining the classes and methods used for encoding and decoding
# VECTOR data (embedded in base_impl.pyx).
#------------------------------------------------------------------------------

cdef array.array float_template = array.array('f')
cdef array.array double_template = array.array('d')
cdef array.array int8_template = array.array('b')
cdef array.array uint8_template = array.array('B')

@cython.final
cdef class SparseVectorImpl:

    @classmethod
    def from_values(cls, num_dimensions, indices, values):
        """
        Creates an implementation from its component values.
        """
        cdef SparseVectorImpl impl = cls.__new__(cls)
        impl.num_dimensions = num_dimensions
        impl.indices = indices
        impl.values = values
        return impl


@cython.final
cdef class VectorDecoder(Buffer):

    cdef array.array _decode_values(self, uint32_t num_elements,
                                    uint8_t vector_format):
        """
        Returns an array containing the decoded values.
        """
        cdef:
            uint8_t *uint8_buf = NULL
            double *double_buf = NULL
            uint8_t element_size = 0
            int8_t *int8_buf = NULL
            float *float_buf = NULL
            OracleDataBuffer buffer
            array.array result
            uint32_t i

        # set up buffers based on vector storage format
        if vector_format == VECTOR_FORMAT_FLOAT32:
            result = array.clone(float_template, num_elements, False)
            float_buf = result.data.as_floats
        elif vector_format == VECTOR_FORMAT_FLOAT64:
            result = array.clone(double_template, num_elements, False)
            double_buf = result.data.as_doubles
        elif vector_format == VECTOR_FORMAT_INT8:
            result = array.clone(int8_template, num_elements, False)
            int8_buf = result.data.as_schars
        elif vector_format == VECTOR_FORMAT_BINARY:
            num_elements = num_elements // 8
            result = array.clone(uint8_template, num_elements, False)
            uint8_buf = result.data.as_uchars
        else:
            errors._raise_err(errors.ERR_VECTOR_FORMAT_NOT_SUPPORTED,
                              vector_format=vector_format)

        # parse data
        for i in range(num_elements):
            if vector_format == VECTOR_FORMAT_FLOAT32:
                decode_binary_float(self._get_raw(4), 4, &buffer)
                float_buf[i] = buffer.as_float
            elif vector_format == VECTOR_FORMAT_FLOAT64:
                decode_binary_double(self._get_raw(8), 8, &buffer)
                double_buf[i] = buffer.as_double
            elif vector_format == VECTOR_FORMAT_INT8:
                self.read_sb1(&int8_buf[i])
            else:
                self.read_ub1(&uint8_buf[i])

        return result

    cdef object decode(self, bytes data):
        """
        Returns a Python object corresponding to the encoded VECTOR bytes.
        """
        cdef:
            uint8_t magic_byte, version, vector_format
            uint16_t flags, num_sparse_elements
            SparseVectorImpl sparse_impl
            array.array uint32_template
            uint32_t* sparse_indices
            uint32_t num_elements, i

        # populate the buffer with the data
        self._populate_from_bytes(data)

        # parse header
        self.read_ub1(&magic_byte)
        if magic_byte != TNS_VECTOR_MAGIC_BYTE:
            errors._raise_err(errors.ERR_UNEXPECTED_DATA,
                              data=bytes([magic_byte]))
        self.read_ub1(&version)
        if version > TNS_VECTOR_VERSION_WITH_SPARSE:
            errors._raise_err(errors.ERR_VECTOR_VERSION_NOT_SUPPORTED,
                              version=version)
        self.read_uint16be(&flags)
        self.read_ub1(&vector_format)
        self.read_uint32be(&num_elements)
        if flags & TNS_VECTOR_FLAG_NORM_RESERVED \
                or flags & TNS_VECTOR_FLAG_NORM:
            self.skip_raw_bytes(8)

        # for sparse vectors, only non-zero elements are found in the image
        if flags & TNS_VECTOR_FLAG_SPARSE:
            sparse_impl = SparseVectorImpl.__new__(SparseVectorImpl)
            sparse_impl.num_dimensions = num_elements
            self.read_uint16be(&num_sparse_elements)
            num_elements = num_sparse_elements
            uint32_template = array.array(ARRAY_TYPE_CODE_UINT32)
            sparse_impl.indices = array.clone(uint32_template,
                                              num_sparse_elements, False)
            sparse_indices = <uint32_t*> sparse_impl.indices.data.as_voidptr
            for i in range(num_sparse_elements):
                self.read_uint32be(&sparse_indices[i])
            sparse_impl.values = self._decode_values(num_sparse_elements,
                                                     vector_format)
            return PY_TYPE_SPARSE_VECTOR._from_impl(sparse_impl)

        # all other vectors have just the values
        return self._decode_values(num_elements, vector_format)


@cython.final
cdef class VectorEncoder(GrowableBuffer):

    cdef int _encode_values(self, array.array value, uint32_t num_elements,
                            uint8_t vector_format) except -1:
        """
        Encode the values into the image using the given vector storage format.
        """
        cdef:
            double *double_ptr = value.data.as_doubles
            uint8_t *uint8_ptr = value.data.as_uchars
            float *float_ptr = value.data.as_floats
            int8_t *int8_ptr = value.data.as_schars
            uint32_t i
        if vector_format == VECTOR_FORMAT_INT8:
            self.write_raw(<char_type*> int8_ptr, num_elements)
        elif vector_format == VECTOR_FORMAT_BINARY:
            self.write_raw(<char_type*> uint8_ptr, num_elements // 8)
        else:
            for i in range(num_elements):
                if vector_format == VECTOR_FORMAT_FLOAT32:
                    self.write_binary_float(float_ptr[i], write_length=False)
                elif vector_format == VECTOR_FORMAT_FLOAT64:
                    self.write_binary_double(double_ptr[i], write_length=False)

    cdef uint8_t _get_vector_format(self, array.array value):
        """
        Returns the vector storage format used by the array.
        """
        if value.typecode == 'd':
            return VECTOR_FORMAT_FLOAT64
        elif value.typecode == 'f':
            return VECTOR_FORMAT_FLOAT32
        elif value.typecode == 'b':
            return VECTOR_FORMAT_INT8
        return VECTOR_FORMAT_BINARY

    cdef int encode(self, object value) except -1:
        """
        Encodes the given value to the internal VECTOR format.
        """
        cdef:
            uint16_t flags = TNS_VECTOR_FLAG_NORM_RESERVED
            uint8_t vector_format, vector_version
            SparseVectorImpl sparse_impl = None
            uint16_t num_sparse_elements, i
            uint32_t* sparse_indices
            uint32_t num_elements

        # determine metadatda about the vector to write
        if isinstance(value, PY_TYPE_SPARSE_VECTOR):
            sparse_impl = value._impl
            num_elements = sparse_impl.num_dimensions
            vector_format = self._get_vector_format(sparse_impl.values)
            vector_version = TNS_VECTOR_VERSION_WITH_SPARSE
            flags |= TNS_VECTOR_FLAG_SPARSE | TNS_VECTOR_FLAG_NORM
        else:
            vector_format = self._get_vector_format(value)
            if vector_format == VECTOR_FORMAT_BINARY:
                num_elements = (<uint32_t> len(value)) * 8
                vector_version = TNS_VECTOR_VERSION_WITH_BINARY
            else:
                num_elements = <uint32_t> len(value)
                vector_version = TNS_VECTOR_VERSION_BASE
                flags |= TNS_VECTOR_FLAG_NORM

        # write header
        self.write_uint8(TNS_VECTOR_MAGIC_BYTE)
        self.write_uint8(vector_version)
        self.write_uint16be(flags)
        self.write_uint8(vector_format)
        self.write_uint32be(num_elements)
        self._reserve_space(8)              # reserve space for norm

        # write data
        if sparse_impl is None:
            self._encode_values(value, num_elements, vector_format)
        else:
            sparse_indices = <uint32_t*> sparse_impl.indices.data.as_voidptr
            num_sparse_elements = len(sparse_impl.indices)
            self.write_uint16be(num_sparse_elements)
            for i in range(num_sparse_elements):
                self.write_uint32be(sparse_indices[i])
            self._encode_values(sparse_impl.values, num_sparse_elements,
                                vector_format)
