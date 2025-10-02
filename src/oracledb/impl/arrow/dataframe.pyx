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
# dataframe.pyx
#
# Cython implementation of the DataFrameImpl class.
#------------------------------------------------------------------------------

cdef class DataFrameImpl:

    @classmethod
    def from_arrow_stream(cls, obj):
        """
        Extract Arrow arrays from an object implementing the PyCapsule arrow
        stream interface.
        """
        cdef:
            ArrowArrayStream *arrow_stream
            ArrowSchemaImpl schema_impl
            ArrowArrayImpl array_impl
            ArrowSchema arrow_schema
            ArrowArray arrow_array
            DataFrameImpl df_impl
            ssize_t i

        # initialization
        df_impl = DataFrameImpl.__new__(DataFrameImpl)
        df_impl.schema_impls = []
        df_impl.arrays = []
        capsule = obj.__arrow_c_stream__()
        arrow_stream = <ArrowArrayStream*> cpython.PyCapsule_GetPointer(
            capsule, "arrow_array_stream"
        )

        # populate list of schemas
        _check_nanoarrow(arrow_stream.get_schema(arrow_stream, &arrow_schema))
        for i in range(arrow_schema.n_children):
            schema_impl = ArrowSchemaImpl.__new__(ArrowSchemaImpl)
            schema_impl.populate_from_schema(arrow_schema.children[i])
            df_impl.schema_impls.append(schema_impl)

        # populate list of arrays
        while True:
            _check_nanoarrow(arrow_stream.get_next(arrow_stream, &arrow_array))
            if arrow_array.release == NULL:
                break
            for i in range(arrow_schema.n_children):
                array_impl = ArrowArrayImpl.__new__(ArrowArrayImpl)
                array_impl.populate_from_array(df_impl.schema_impls[i],
                                               arrow_array.children[i])
                df_impl.arrays.append(array_impl)

        ArrowArrayStreamRelease(arrow_stream)
        return df_impl

    def get_arrays(self):
        """
        Internal method for getting the list of arrays associated with the data
        frame.
        """
        return self.arrays

    def get_stream_capsule(self):
        """
        Internal method for getting a PyCapsule pointer to a stream that
        encapsulates the arrays found in the data frame.
        """
        cdef:
            ArrowSchemaImpl schema_impl
            ArrowArrayImpl array_impl
            ArrowArrayStream *stream
            int64_t i, num_arrays
            ArrowSchema schema
            ArrowArray array

        # initialization
        stream = NULL
        array.release = NULL
        schema.release = NULL
        num_arrays = <int64_t> len(self.arrays)

        try:

            # create schema/array encompassing all of the arrays
            _check_nanoarrow(
                ArrowSchemaInitFromType(&schema, NANOARROW_TYPE_STRUCT)
            )
            _check_nanoarrow(ArrowSchemaAllocateChildren(&schema, num_arrays))
            _check_nanoarrow(
                ArrowArrayInitFromType(&array, NANOARROW_TYPE_STRUCT)
            )
            _check_nanoarrow(ArrowArrayAllocateChildren(&array, num_arrays))
            for i, schema_impl in enumerate(self.schema_impls):
                array_impl = self.arrays[i]
                array.length = array_impl.arrow_array.length
                copy_arrow_array(
                    array_impl, array_impl.arrow_array, array.children[i]
                )
                _check_nanoarrow(
                    ArrowSchemaDeepCopy(
                        schema_impl.arrow_schema, schema.children[i]
                    )
                )

            # create stream and populate it
            stream = <ArrowArrayStream*> \
                    cpython.PyMem_Calloc(1, sizeof(ArrowArrayStream))
            _check_nanoarrow(
                ArrowBasicArrayStreamInit(stream, &schema, num_arrays)
            )
            ArrowBasicArrayStreamSetArray(stream, 0, &array)

        except:
            if schema.release:
                ArrowSchemaRelease(&schema)
            if array.release:
                ArrowArrayRelease(&array)
            if stream != NULL:
                if stream.release:
                    ArrowArrayStreamRelease(stream)
                cpython.PyMem_Free(stream)
            raise

        # create and return capsule
        return cpython.PyCapsule_New(
            stream,
            "arrow_array_stream",
            &pycapsule_array_stream_deleter
        )


cdef void pycapsule_array_stream_deleter(object stream_capsule) noexcept:
    """
    Called when the PyCapsule pointer is no longer required and performs the
    necessary cleanup.
    """
    cdef ArrowArrayStream* stream
    stream = <ArrowArrayStream*> cpython.PyCapsule_GetPointer(
        stream_capsule, 'arrow_array_stream'
    )
    if stream.release != NULL:
        ArrowArrayStreamRelease(stream)
    cpython.PyMem_Free(stream)
