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
# schema.pyx
#
# Cython implementation of the ArrowSchemaImpl class.
#------------------------------------------------------------------------------

cdef class ArrowSchemaImpl:

    def __cinit__(self):
        self.arrow_schema = \
                <ArrowSchema*> cpython.PyMem_Calloc(1, sizeof(ArrowSchema))

    def __dealloc__(self):
        if self.arrow_schema != NULL:
            if self.arrow_schema.release != NULL:
                ArrowSchemaRelease(self.arrow_schema)
            cpython.PyMem_Free(self.arrow_schema)

    cdef bint _is_sparse_vector(self) except*:
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

    @classmethod
    def from_arrow_schema(cls, obj):
        cdef:
            ArrowSchema* arrow_schema
            ArrowSchemaImpl schema_impl
        schema_capsule = obj.__arrow_c_schema__()
        arrow_schema = <ArrowSchema*> cpython.PyCapsule_GetPointer(
            schema_capsule, "arrow_schema"
        )
        schema_impl = ArrowSchemaImpl.__new__(ArrowSchemaImpl)
        schema_impl.populate_from_schema(arrow_schema)
        return schema_impl

    cdef str get_type_name(self):
        """
        Returns a string representation of the Arrow type.
        """
        return ArrowTypeString(self.arrow_type).decode()

    cdef int populate_from_schema(self, ArrowSchema* schema) except -1:
        """
        Populate the schema from another schema.
        """
        cdef:
            ArrowSchemaView schema_view
            ArrowSchemaImpl schema_impl
            int64_t i
        ArrowSchemaMove(schema, self.arrow_schema)
        memset(&schema_view, 0, sizeof(ArrowSchemaView))
        _check_nanoarrow(
            ArrowSchemaViewInit(&schema_view, self.arrow_schema, NULL)
        )
        self.arrow_type = schema_view.type
        self.name = schema.name.decode()
        self.precision = schema_view.decimal_precision
        self.scale = schema_view.decimal_scale
        self.fixed_size = schema_view.fixed_size
        if schema_view.type == NANOARROW_TYPE_STRUCT:

            # struct may refer to a sparse vector
            if self._is_sparse_vector():
                _check_nanoarrow(
                    ArrowSchemaViewInit(&schema_view,
                                        schema.children[2].children[0], NULL)
                )
                self._set_child_arrow_type(schema_view.type)

            # otherwise, it is treated as a list of columns such as those used
            # for a requested schema
            else:
                self.child_schemas = []
                for i in range(schema.n_children):
                    schema_impl = ArrowSchemaImpl.__new__(ArrowSchemaImpl)
                    schema_impl.populate_from_schema(schema.children[i])
                    self.child_schemas.append(schema_impl)
        elif schema_view.type == NANOARROW_TYPE_TIMESTAMP:
            self._set_time_unit(schema_view.time_unit)
        elif schema_view.type == NANOARROW_TYPE_DATE64:
            self._set_time_unit(NANOARROW_TIME_UNIT_MILLI)
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
            NANOARROW_TYPE_DATE32,
            NANOARROW_TYPE_DATE64,
            NANOARROW_TYPE_DECIMAL128,
            NANOARROW_TYPE_DOUBLE,
            NANOARROW_TYPE_FIXED_SIZE_BINARY,
            NANOARROW_TYPE_FLOAT,
            NANOARROW_TYPE_INT8,
            NANOARROW_TYPE_INT16,
            NANOARROW_TYPE_INT32,
            NANOARROW_TYPE_INT64,
            NANOARROW_TYPE_LARGE_BINARY,
            NANOARROW_TYPE_LARGE_STRING,
            NANOARROW_TYPE_STRING,
            NANOARROW_TYPE_UINT8,
            NANOARROW_TYPE_UINT16,
            NANOARROW_TYPE_UINT32,
            NANOARROW_TYPE_UINT64,
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
        Populate the schema from the supplied metadata.
        """
        cdef ArrowType storage_type = arrow_type
        self.arrow_type = arrow_type
        self._set_time_unit(time_unit)
        self._set_child_arrow_type(child_arrow_type)
        self.name = name
        if arrow_type == NANOARROW_TYPE_TIMESTAMP:
            storage_type = NANOARROW_TYPE_INT64

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
        _check_nanoarrow(ArrowSchemaSetName(self.arrow_schema, name.encode()))

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
