#------------------------------------------------------------------------------
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
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
# dbobject.pyx
#
# Cython file defining the thin DbObjectType, DbObjectAttr and DbObject
# implementation classes (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

@cython.final
cdef class DbObjectPickleBuffer(GrowableBuffer):

    cdef int _read_raw_bytes_and_length(self, const char_type **ptr,
                                        ssize_t *num_bytes) except -1:
        """
        Helper function that processes the length (if needed) and then acquires
        the specified number of bytes from the buffer.
        """
        cdef uint32_t extended_num_bytes
        if num_bytes[0] == TNS_LONG_LENGTH_INDICATOR:
            self.read_uint32(&extended_num_bytes)
            num_bytes[0] = <ssize_t> extended_num_bytes
        ptr[0] = self._get_raw(num_bytes[0])

    cdef int _write_raw_bytes_and_length(self, const char_type *ptr,
                                         ssize_t num_bytes) except -1:
        """
        Helper function that writes the length in the format required before
        writing the bytes.
        """
        self.write_length(num_bytes)
        self.write_raw(ptr, <uint32_t> num_bytes)

    cdef int get_is_atomic_null(self, bint* is_null) except -1:
        """
        Reads the next byte and checks to see if the value is atomically null.
        If not, the byte is returned to the buffer for further processing.
        """
        cdef uint8_t value
        self.read_ub1(&value)
        if value in (TNS_OBJ_ATOMIC_NULL, TNS_NULL_LENGTH_INDICATOR):
            is_null[0] = True
        else:
            is_null[0] = False
            self._pos -= 1

    cdef int read_header(self, uint8_t* flags, uint8_t *version) except -1:
        """
        Reads the header of the pickled data.
        """
        cdef:
            uint32_t prefix_seg_length
            uint8_t tmp
        self.read_ub1(flags)
        self.read_ub1(version)
        self.skip_length()
        if flags[0] & TNS_OBJ_NO_PREFIX_SEG:
            return 0
        self.read_length(&prefix_seg_length)
        self.skip_raw_bytes(prefix_seg_length)

    cdef int read_length(self, uint32_t *length) except -1:
        """
        Read the length from the buffer. This will be a single byte, unless the
        value meets or exceeds TNS_LONG_LENGTH_INDICATOR. In that case, the
        value is stored as a 4-byte integer.
        """
        cdef uint8_t short_length
        self.read_ub1(&short_length)
        if short_length == TNS_LONG_LENGTH_INDICATOR:
            self.read_uint32(length)
        else:
            length[0] = short_length

    cdef int skip_length(self) except -1:
        """
        Skips the length instead of reading it from the buffer.
        """
        cdef uint8_t short_length
        self.read_ub1(&short_length)
        if short_length == TNS_LONG_LENGTH_INDICATOR:
            self.skip_raw_bytes(4)

    cdef int write_header(self, ThinDbObjectImpl obj_impl) except -1:
        """
        Writes the header of the pickled data. Since the size is unknown at
        this point, zero is written initially and the actual size is written
        later.
        """
        cdef ThinDbObjectTypeImpl typ_impl = obj_impl.type
        self.write_uint8(obj_impl.image_flags)
        self.write_uint8(obj_impl.image_version)
        self.write_uint8(TNS_LONG_LENGTH_INDICATOR)
        self.write_uint32(0)
        if typ_impl.is_collection:
            self.write_uint8(1)             # length of prefix segment
            self.write_uint8(1)             # prefix segment contents

    cdef int write_length(self, ssize_t length) except -1:
        """
        Writes the length to the buffer.
        """
        if length <= TNS_OBJ_MAX_SHORT_LENGTH:
            self.write_uint8(<uint8_t> length)
        else:
            self.write_uint8(TNS_LONG_LENGTH_INDICATOR)
            self.write_uint32(<uint32_t> length)


@cython.final
cdef class TDSBuffer(Buffer):
    pass


cdef class ThinDbObjectImpl(BaseDbObjectImpl):
    cdef:
        uint8_t image_flags, image_version
        bytes toid, oid, packed_data
        uint32_t num_elements
        dict unpacked_assoc_array
        list unpacked_assoc_keys
        dict unpacked_attrs
        list unpacked_array
        uint16_t flags

    cdef inline int _ensure_assoc_keys(self) except -1:
        """
        Ensure that the keys for the associative array have been calculated.
        PL/SQL associative arrays keep their keys in sorted order so this must
        be calculated when indices are required.
        """
        if self.unpacked_assoc_keys is None:
            self.unpacked_assoc_keys = list(sorted(self.unpacked_assoc_array))

    cdef inline int _ensure_unpacked(self) except -1:
        """
        Ensure that the data has been unpacked.
        """
        if self.packed_data is not None:
            self._unpack_data()

    cdef bytes _get_packed_data(self):
        """
        Returns the packed data for the object. This will either be the value
        retrieved from the database or generated packed data (for new objects
        and those that have had their data unpacked already).
        """
        cdef:
            ThinDbObjectTypeImpl typ_impl = self.type
            DbObjectPickleBuffer buf
            ssize_t size
        if self.packed_data is not None:
            return self.packed_data
        buf = DbObjectPickleBuffer.__new__(DbObjectPickleBuffer)
        buf._initialize(TNS_CHUNK_SIZE)
        buf.write_header(self)
        self._pack_data(buf)
        size = buf._pos
        buf.skip_to(3)
        buf.write_uint32(size)
        return buf._data[:size]

    cdef int _pack_data(self, DbObjectPickleBuffer buf) except -1:
        """
        Packs the data from the object into the buffer.
        """
        cdef:
            ThinDbObjectTypeImpl typ_impl = self.type
            ThinDbObjectAttrImpl attr
            int32_t index
            object value
        if typ_impl.is_collection:
            buf.write_uint8(typ_impl.collection_flags)
            if typ_impl.collection_type == TNS_OBJ_PLSQL_INDEX_TABLE:
                self._ensure_assoc_keys()
                buf.write_length(len(self.unpacked_assoc_keys))
                for index in self.unpacked_assoc_keys:
                    buf.write_uint32(<uint32_t> index)
                    self._pack_value(buf, typ_impl.element_dbtype,
                                     typ_impl.element_objtype,
                                     self.unpacked_assoc_array[index])
            else:
                buf.write_length(len(self.unpacked_array))
                for value in self.unpacked_array:
                    self._pack_value(buf, typ_impl.element_dbtype,
                                    typ_impl.element_objtype, value)
        else:
            for attr in typ_impl.attrs:
                self._pack_value(buf, attr.dbtype, attr.objtype,
                                 self.unpacked_attrs[attr.name])

    cdef int _pack_value(self, DbObjectPickleBuffer buf,
                         DbType dbtype, ThinDbObjectTypeImpl objtype,
                         object value) except -1:
        """
        Packs a value into the buffer. At this point it is assumed that the
        value matches the correct type.
        """
        cdef:
            uint8_t ora_type_num = dbtype._ora_type_num
            ThinDbObjectImpl obj_impl
            bytes temp_bytes
        if value is None:
            if objtype is not None and not objtype.is_collection:
                buf.write_uint8(TNS_OBJ_ATOMIC_NULL)
            else:
                buf.write_uint8(TNS_NULL_LENGTH_INDICATOR)
        elif ora_type_num in (TNS_DATA_TYPE_CHAR, TNS_DATA_TYPE_VARCHAR):
            if dbtype._csfrm == TNS_CS_IMPLICIT:
                temp_bytes = (<str> value).encode()
            else:
                temp_bytes = (<str> value).encode(TNS_ENCODING_UTF16)
            buf.write_bytes_with_length(temp_bytes)
        elif ora_type_num == TNS_DATA_TYPE_NUMBER:
            temp_bytes = (<str> cpython.PyObject_Str(value)).encode()
            buf.write_oracle_number(temp_bytes)
        elif ora_type_num == TNS_DATA_TYPE_BINARY_INTEGER:
            buf.write_uint8(4)
            buf.write_uint32(<uint32_t> value)
        elif ora_type_num == TNS_DATA_TYPE_RAW:
            buf.write_bytes_with_length(value)
        elif ora_type_num == TNS_DATA_TYPE_BINARY_DOUBLE:
            buf.write_binary_double(value)
        elif ora_type_num == TNS_DATA_TYPE_BINARY_FLOAT:
            buf.write_binary_float(value)
        elif ora_type_num == TNS_DATA_TYPE_BOOLEAN:
            buf.write_uint8(4)
            buf.write_uint32(value)
        elif ora_type_num in (TNS_DATA_TYPE_DATE, TNS_DATA_TYPE_TIMESTAMP,
                              TNS_DATA_TYPE_TIMESTAMP_TZ,
                              TNS_DATA_TYPE_TIMESTAMP_LTZ):
            buf.write_oracle_date(value, dbtype._buffer_size_factor)
        elif ora_type_num in (TNS_DATA_TYPE_CLOB, TNS_DATA_TYPE_BLOB):
            buf.write_lob(value._impl)
        elif ora_type_num == TNS_DATA_TYPE_INT_NAMED:
            obj_impl = value._impl
            if self.type.is_collection or obj_impl.type.is_collection:
                temp_bytes = obj_impl._get_packed_data()
                buf.write_bytes_with_length(temp_bytes)
            else:
                obj_impl._pack_data(buf)
        else:
            errors._raise_err(errors.ERR_DB_TYPE_NOT_SUPPORTED,
                              name=dbtype.name)

    cdef int _unpack_data(self) except -1:
        """
        Unpacks the packed data into a dictionary of Python values.
        """
        cdef DbObjectPickleBuffer buf
        buf = DbObjectPickleBuffer.__new__(DbObjectPickleBuffer)
        buf._populate_from_bytes(self.packed_data)
        buf.read_header(&self.image_flags, &self.image_version)
        self._unpack_data_from_buf(buf)
        self.packed_data = None

    cdef int _unpack_data_from_buf(self, DbObjectPickleBuffer buf) except -1:
        """
        Unpacks the data from the buffer into Python values.
        """
        cdef:
            dict unpacked_attrs = {}, unpacked_assoc_array = None
            ThinDbObjectTypeImpl typ_impl = self.type
            list unpacked_array = None
            ThinDbObjectAttrImpl attr
            uint32_t num_elements, i
            int32_t assoc_index
            object value
        if typ_impl.is_collection:
            if typ_impl.collection_type == TNS_OBJ_PLSQL_INDEX_TABLE:
                unpacked_assoc_array = {}
            else:
                unpacked_array = []
            buf.skip_raw_bytes(1)           # collection flags
            buf.read_length(&num_elements)
            for i in range(num_elements):
                if typ_impl.collection_type == TNS_OBJ_PLSQL_INDEX_TABLE:
                    buf.read_int32(&assoc_index)
                value = self._unpack_value(buf, typ_impl.element_dbtype,
                                           typ_impl.element_objtype)
                if typ_impl.collection_type == TNS_OBJ_PLSQL_INDEX_TABLE:
                    unpacked_assoc_array[assoc_index] = value
                else:
                    unpacked_array.append(value)
        else:
            unpacked_attrs = {}
            for attr in typ_impl.attrs:
                value = self._unpack_value(buf, attr.dbtype, attr.objtype)
                unpacked_attrs[attr.name] = value
        self.unpacked_attrs = unpacked_attrs
        self.unpacked_array = unpacked_array
        self.unpacked_assoc_array = unpacked_assoc_array

    cdef object _unpack_value(self, DbObjectPickleBuffer buf,
                              DbType dbtype, ThinDbObjectTypeImpl objtype):
        """
        Unpacks a single value and returns it.
        """
        cdef:
            uint8_t ora_type_num = dbtype._ora_type_num
            uint8_t csfrm = dbtype._csfrm
            ThinDbObjectImpl obj_impl
            ThinConnImpl conn_impl
            bint is_null
        if ora_type_num == TNS_DATA_TYPE_NUMBER:
            return buf.read_oracle_number(NUM_TYPE_FLOAT)
        elif ora_type_num == TNS_DATA_TYPE_BINARY_INTEGER:
            return buf.read_binary_integer()
        elif ora_type_num in (TNS_DATA_TYPE_VARCHAR, TNS_DATA_TYPE_CHAR):
            if csfrm == TNS_CS_NCHAR:
                conn_impl = self.type._conn_impl
                conn_impl._protocol._caps._check_ncharset_id()
            return buf.read_str(csfrm)
        elif ora_type_num == TNS_DATA_TYPE_RAW:
            return buf.read_bytes()
        elif ora_type_num == TNS_DATA_TYPE_BINARY_DOUBLE:
            return buf.read_binary_double()
        elif ora_type_num == TNS_DATA_TYPE_BINARY_FLOAT:
            return buf.read_binary_float()
        elif ora_type_num in (TNS_DATA_TYPE_DATE, TNS_DATA_TYPE_TIMESTAMP,
                              TNS_DATA_TYPE_TIMESTAMP_LTZ,
                              TNS_DATA_TYPE_TIMESTAMP_TZ):
            return buf.read_date()
        elif ora_type_num in (TNS_DATA_TYPE_CLOB, TNS_DATA_TYPE_BLOB):
            conn_impl = self.type._conn_impl
            return buf.read_lob(conn_impl, dbtype)
        elif ora_type_num == TNS_DATA_TYPE_BOOLEAN:
            return buf.read_bool()
        elif ora_type_num == TNS_DATA_TYPE_INT_NAMED:
            buf.get_is_atomic_null(&is_null)
            if is_null:
                return None
            obj_impl = ThinDbObjectImpl.__new__(ThinDbObjectImpl)
            obj_impl.type = objtype
            if objtype.is_collection or self.type.is_collection:
                obj_impl.packed_data = buf.read_bytes()
            else:
                obj_impl._unpack_data_from_buf(buf)
            return PY_TYPE_DB_OBJECT._from_impl(obj_impl)
        errors._raise_err(errors.ERR_DB_TYPE_NOT_SUPPORTED, name=dbtype.name)

    def append_checked(self, object value):
        """
        Internal method for appending a value to a collection object.
        """
        cdef:
            ThinDbObjectTypeImpl typ_impl
            int32_t new_index
        self._ensure_unpacked()
        if self.unpacked_array is not None:
            typ_impl = self.type
            if typ_impl.max_num_elements > 0 \
                    and len(self.unpacked_array) >= typ_impl.max_num_elements:
                errors._raise_err(errors.ERR_INVALID_COLL_INDEX_SET,
                                  index=len(self.unpacked_array),
                                  min_index=0,
                                  max_index=typ_impl.max_num_elements - 1)
            self.unpacked_array.append(value)
        else:
            self._ensure_assoc_keys()
            new_index = self.unpacked_assoc_keys[-1] + 1 \
                    if self.unpacked_assoc_keys else 0
            self.unpacked_assoc_array[new_index] = value
            self.unpacked_assoc_keys.append(new_index)

    def copy(self):
        """
        Internal method for creating a copy of an object.
        """
        cdef ThinDbObjectImpl copied_impl
        copied_impl = ThinDbObjectImpl.__new__(ThinDbObjectImpl)
        copied_impl.type = self.type
        copied_impl.flags = self.flags
        copied_impl.image_flags = self.image_flags
        copied_impl.image_version = self.image_version
        copied_impl.toid = self.toid
        copied_impl.packed_data = self.packed_data
        copied_impl.num_elements = self.num_elements
        if self.unpacked_attrs is not None:
            copied_impl.unpacked_attrs = self.unpacked_attrs.copy()
        if self.unpacked_array is not None:
            copied_impl.unpacked_array = list(self.unpacked_array)
        return copied_impl

    def delete_by_index(self, int32_t index):
        """
        Internal method for deleting an entry from a collection that is indexed
        by integers.
        """
        self._ensure_unpacked()
        if self.unpacked_array is not None:
            del self.unpacked_array[index]
        else:
            self.unpacked_assoc_keys = None
            del self.unpacked_assoc_array[index]

    def exists_by_index(self, int32_t index):
        """
        Internal method for determining if an entry exists in a collection that
        is indexed by integers.
        """
        self._ensure_unpacked()
        if self.unpacked_array is not None:
            return index >= 0 and index < len(self.unpacked_array)
        else:
            return index in self.unpacked_assoc_array

    def get_attr_value(self, ThinDbObjectAttrImpl attr):
        """
        Internal method for getting an attribute value.
        """
        self._ensure_unpacked()
        return self.unpacked_attrs[attr.name]

    def get_element_by_index(self, int32_t index):
        """
        Internal method for getting an entry from a collection that is indexed
        by integers.
        """
        self._ensure_unpacked()
        try:
            if self.unpacked_array is not None:
                return self.unpacked_array[index]
            else:
                return self.unpacked_assoc_array[index]
        except (KeyError, IndexError):
            errors._raise_err(errors.ERR_INVALID_COLL_INDEX_GET, index=index)

    def get_first_index(self):
        """
        Internal method for getting the first index from a collection that is
        indexed by integers.
        """
        self._ensure_unpacked()
        if self.unpacked_array:
            return 0
        elif self.unpacked_assoc_array:
            self._ensure_assoc_keys()
            return self.unpacked_assoc_keys[0]

    def get_last_index(self):
        """
        Internal method for getting the last index from a collection that is
        indexed by integers.
        """
        self._ensure_unpacked()
        if self.unpacked_array:
            return len(self.unpacked_array) - 1
        elif self.unpacked_assoc_array:
            self._ensure_assoc_keys()
            return self.unpacked_assoc_keys[-1]

    def get_next_index(self, int32_t index):
        """
        Internal method for getting the next index from a collection that is
        indexed by integers.
        """
        cdef int32_t i
        self._ensure_unpacked()
        if self.unpacked_array:
            if index + 1 < len(self.unpacked_array):
                return index + 1
        elif self.unpacked_assoc_array:
            self._ensure_assoc_keys()
            for i in self.unpacked_assoc_keys:
                if i > index:
                    return i

    def get_prev_index(self, int32_t index):
        """
        Internal method for getting the next index from a collection that is
        indexed by integers.
        """
        self._ensure_unpacked()
        if self.unpacked_array:
            if index > 0:
                return index - 1
        elif self.unpacked_assoc_array:
            self._ensure_assoc_keys()
            for i in reversed(self.unpacked_assoc_keys):
                if i < index:
                    return i

    def get_size(self):
        """
        Internal method for getting the size of a collection.
        """
        self._ensure_unpacked()
        if self.unpacked_array is not None:
            return len(self.unpacked_array)
        else:
            return len(self.unpacked_assoc_array)

    def set_attr_value_checked(self, ThinDbObjectAttrImpl attr, object value):
        """
        Internal method for setting an attribute value.
        """
        self._ensure_unpacked()
        self.unpacked_attrs[attr.name] = value

    def set_element_by_index_checked(self, int32_t index, object value):
        """
        Internal method for setting an entry in a collection that is indexed by
        integers.
        """
        self._ensure_unpacked()
        if self.unpacked_array is not None:
            try:
                self.unpacked_array[index] = value
            except IndexError:
                max_index = max(len(self.unpacked_array) - 1, 0)
                errors._raise_err(errors.ERR_INVALID_COLL_INDEX_SET,
                                  index=index, min_index=0,
                                  max_index=max_index)
        else:
            if index not in self.unpacked_assoc_array:
                self.unpacked_assoc_keys = None
            self.unpacked_assoc_array[index] = value

    def trim(self, int32_t num_to_trim):
        """
        Internal method for trimming a number of entries from a collection.
        """
        self._ensure_unpacked()
        if num_to_trim > 0:
            self.unpacked_array = self.unpacked_array[:-num_to_trim]


cdef class ThinDbObjectAttrImpl(BaseDbObjectAttrImpl):
    cdef:
        bytes oid


cdef class ThinDbObjectTypeImpl(BaseDbObjectTypeImpl):
    cdef:
        uint8_t collection_type, collection_flags, version
        uint32_t max_num_elements
        bint is_xml_type
        bytes oid

    def create_new_object(self):
        """
        Internal method for creating a new object.
        """
        cdef ThinDbObjectImpl obj_impl
        obj_impl = ThinDbObjectImpl.__new__(ThinDbObjectImpl)
        obj_impl.type = self
        obj_impl.toid = b'\x00\x22' + \
                bytes([TNS_OBJ_NON_NULL_OID, TNS_OBJ_HAS_EXTENT_OID]) + \
                self.oid + TNS_EXTENT_OID
        obj_impl.flags = TNS_OBJ_TOP_LEVEL
        obj_impl.image_flags = TNS_OBJ_IS_VERSION_81
        obj_impl.image_version = TNS_OBJ_IMAGE_VERSION
        obj_impl.unpacked_attrs = {}
        if self.is_collection:
            obj_impl.image_flags |= TNS_OBJ_IS_COLLECTION
            if self.collection_type == TNS_OBJ_PLSQL_INDEX_TABLE:
                obj_impl.unpacked_assoc_array = {}
            else:
                obj_impl.unpacked_array = []
        else:
            obj_impl.image_flags |= TNS_OBJ_NO_PREFIX_SEG
            for attr in self.attrs:
                obj_impl.unpacked_attrs[attr.name] = None
        return obj_impl


cdef class ThinDbObjectTypeSuperCache:
    cdef:
        dict caches
        object lock
        int cache_num

    def __init__(self):
        self.caches = {}
        self.cache_num = 0
        self.lock = threading.Lock()


cdef class ThinDbObjectTypeCache:
    cdef:
        object return_value_var, full_name_var, oid_var, tds_var
        object meta_cursor, attrs_ref_cursor_var, version_var
        object schema_var, package_name_var, name_var
        ThinConnImpl conn_impl
        dict types_by_oid
        dict types_by_name
        list partial_types

    cdef int _clear_meta_cursor(self) except -1:
        """
        Clears the cursor used for searching metadata. This is needed when
        returning a connection to the pool since user-level objects are
        retained.
        """
        if self.meta_cursor is not None:
            self.meta_cursor.close()
            self.meta_cursor = None
            self.return_value_var = None
            self.full_name_var = None
            self.oid_var = None
            self.tds_var = None
            self.attrs_ref_cursor_var = None
            self.version_var = None
            self.schema_var = None
            self.package_name_var = None
            self.name_var = None

    cdef int _determine_element_type_csfrm(self, ThinDbObjectTypeImpl typ_impl,
                                           uint8_t* csfrm) except -1:
        """
        Determine the element type's character set form. This is only needed
        for CLOB and NCLOB where this information is not stored in the TDS.
        """
        cdef:
            object cursor
            str type_name
        cursor = self.meta_cursor.connection.cursor()
        if typ_impl.package_name is not None:
            cursor.execute("""
                    select elem_type_name
                    from all_plsql_coll_types
                    where owner = :owner
                      and package_name = :package_name
                      and type_name = :name""",
                    owner=typ_impl.schema,
                    package_name=typ_impl.package_name,
                    name=typ_impl.name)
        else:
            cursor.execute("""
                    select elem_type_name
                    from all_coll_types
                    where owner = :owner
                      and type_name = :name""",
                    owner=typ_impl.schema,
                    name=typ_impl.name)

        type_name, = cursor.fetchone()
        if type_name == "NCLOB":
            csfrm[0] = TNS_CS_NCHAR
        else:
            csfrm[0] = TNS_CS_IMPLICIT

    cdef int _determine_element_objtype(self,
                                        ThinDbObjectTypeImpl impl) except -1:
        """
        Determine the element type's object type. This is needed when
        processing collections with object as the element type since this
        information is not available in the TDS.
        """
        cdef:
            str schema, name, package_name = None
            object cursor
        cursor = self.meta_cursor.connection.cursor()
        if impl.package_name is not None:
            cursor.execute("""
                    select
                        elem_type_owner,
                        elem_type_package,
                        elem_type_name
                    from all_plsql_coll_types
                    where owner = :owner
                      and package_name = :package_name
                      and type_name = :name""",
                    owner=impl.schema,
                    package_name=impl.package_name,
                    name=impl.name)
            schema, package_name, name = cursor.fetchone()
        else:
            cursor.execute("""
                    select
                        elem_type_owner,
                        elem_type_name
                    from all_coll_types
                    where owner = :owner
                      and type_name = :name""",
                    owner=impl.schema,
                    name=impl.name)
            schema, name = cursor.fetchone()
        impl.element_objtype = self.get_type_for_info(None, schema,
                                                      package_name, name)

    cdef int _initialize(self, ThinConnImpl conn_impl) except -1:
        self.types_by_oid = {}
        self.types_by_name = {}
        self.partial_types = []
        self.conn_impl = conn_impl

    cdef int _init_meta_cursor(self, object conn) except -1:
        """
        Initializes the cursor that fetches the type metadata.
        """
        cursor = conn.cursor()
        self.return_value_var = cursor.var(DB_TYPE_BINARY_INTEGER)
        self.tds_var = cursor.var(bytes)
        self.full_name_var = cursor.var(str)
        self.schema_var = cursor.var(str)
        self.package_name_var = cursor.var(str)
        self.name_var = cursor.var(str)
        self.oid_var = cursor.var(bytes)
        self.version_var = cursor.var(DB_TYPE_BINARY_INTEGER)
        self.attrs_ref_cursor_var = cursor.var(DB_TYPE_CURSOR)
        cursor.setinputsizes(ret_val=self.return_value_var,
                             tds=self.tds_var,
                             full_name=self.full_name_var,
                             oid=self.oid_var,
                             schema=self.schema_var,
                             package_name=self.package_name_var,
                             name=self.name_var,
                             version=self.version_var,
                             attrs_rc=self.attrs_ref_cursor_var)
        cursor.prepare("""
            declare
                t_Instantiable              varchar2(3);
                t_SuperTypeOwner            varchar2(128);
                t_SuperTypeName             varchar2(128);
                t_SubTypeRefCursor          sys_refcursor;
                t_Pos                       pls_integer;
            begin
                :ret_val := dbms_pickler.get_type_shape(:full_name, :oid,
                    :version, :tds, t_Instantiable, t_SuperTypeOwner,
                    t_SuperTypeName, :attrs_rc, t_SubTypeRefCursor);
                :package_name := null;
                if substr(:full_name, length(:full_name) - 7) = '%ROWTYPE' then
                    t_Pos := instr(:full_name, '.');
                    :schema := substr(:full_name, 1, t_Pos - 1);
                    :name := substr(:full_name, t_Pos + 1);
                else
                    begin
                        select owner, type_name
                        into :schema, :name
                        from all_types
                        where type_oid = :oid;
                    exception
                    when no_data_found then
                        begin
                            select owner, package_name, type_name
                            into :schema, :package_name, :name
                            from all_plsql_types
                            where type_oid = :oid;
                        exception
                        when no_data_found then
                            null;
                        end;
                    end;
                end if;
            end;""")
        self.meta_cursor = cursor

    cdef int _parse_element_type(self, ThinDbObjectTypeImpl typ_impl,
                                 TDSBuffer buf) except -1:
        """
        Parses the element type from the TDS buffer.
        """
        cdef uint8_t attr_type, ora_type_num = 0, csfrm = 0
        buf.read_ub1(&attr_type)
        if attr_type in (TNS_OBJ_TDS_TYPE_NUMBER, TNS_OBJ_TDS_TYPE_FLOAT):
            ora_type_num = TNS_DATA_TYPE_NUMBER
        elif attr_type in (TNS_OBJ_TDS_TYPE_VARCHAR, TNS_OBJ_TDS_TYPE_CHAR):
            buf.skip_raw_bytes(2)           # maximum length
            buf.read_ub1(&csfrm)
            csfrm = csfrm & 0x7f
            if attr_type == TNS_OBJ_TDS_TYPE_VARCHAR:
                ora_type_num = TNS_DATA_TYPE_VARCHAR
            else:
                ora_type_num = TNS_DATA_TYPE_CHAR
        elif attr_type == TNS_OBJ_TDS_TYPE_RAW:
            ora_type_num = TNS_DATA_TYPE_RAW
        elif attr_type == TNS_OBJ_TDS_TYPE_BINARY_FLOAT:
            ora_type_num = TNS_DATA_TYPE_BINARY_FLOAT
        elif attr_type == TNS_OBJ_TDS_TYPE_BINARY_DOUBLE:
            ora_type_num = TNS_DATA_TYPE_BINARY_DOUBLE
        elif attr_type == TNS_OBJ_TDS_TYPE_DATE:
            ora_type_num = TNS_DATA_TYPE_DATE
        elif attr_type == TNS_OBJ_TDS_TYPE_TIMESTAMP:
            ora_type_num = TNS_DATA_TYPE_TIMESTAMP
        elif attr_type == TNS_OBJ_TDS_TYPE_TIMESTAMP_LTZ:
            ora_type_num = TNS_DATA_TYPE_TIMESTAMP_LTZ
        elif attr_type == TNS_OBJ_TDS_TYPE_TIMESTAMP_TZ:
            ora_type_num = TNS_DATA_TYPE_TIMESTAMP_TZ
        elif attr_type == TNS_OBJ_TDS_TYPE_BOOLEAN:
            ora_type_num = TNS_DATA_TYPE_BOOLEAN
        elif attr_type == TNS_OBJ_TDS_TYPE_CLOB:
            ora_type_num = TNS_DATA_TYPE_CLOB
            self._determine_element_type_csfrm(typ_impl, &csfrm)
        elif attr_type == TNS_OBJ_TDS_TYPE_BLOB:
            ora_type_num = TNS_DATA_TYPE_BLOB
        elif attr_type == TNS_OBJ_TDS_TYPE_OBJ:
            ora_type_num = TNS_DATA_TYPE_INT_NAMED
            self._determine_element_objtype(typ_impl)
        else:
            errors._raise_err(errors.ERR_TDS_TYPE_NOT_SUPPORTED, num=attr_type)
        typ_impl.element_dbtype = DbType._from_ora_type_and_csfrm(ora_type_num,
                                                                  csfrm)

    cdef int _parse_tds(self, ThinDbObjectTypeImpl typ_impl,
                        bytes tds) except -1:
        """
        Parses the TDS for the type. This is only needed for collection types,
        so if the TDS is determined to be for an object type, the remaining
        information is skipped.
        """
        cdef:
            uint32_t element_pos
            uint16_t num_attrs
            uint8_t attr_type
            TDSBuffer buf

        # parse initial TDS bytes
        buf = TDSBuffer.__new__(TDSBuffer)
        buf._populate_from_bytes(tds)
        buf.skip_raw_bytes(4)               # end offset
        buf.skip_raw_bytes(2)               # version op code and version
        buf.skip_raw_bytes(2)               # unknown

        # if the number of attributes exceeds 1, the type cannot refer to a
        # collection, so nothing further needs to be done
        buf.read_uint16(&num_attrs)
        if num_attrs > 1:
            return 0

        # continue parsing TDS bytes to discover if type refers to a collection
        buf.skip_raw_bytes(1)               # TDS attributes?
        buf.skip_raw_bytes(1)               # start ADT op code
        buf.skip_raw_bytes(2)               # ADT number (always zero)
        buf.skip_raw_bytes(4)               # offset to index table

        # if type of first attribute is not a collection, nothing further needs
        # to be done
        buf.read_ub1(&attr_type)
        if attr_type != TNS_OBJ_TDS_TYPE_COLL:
            return 0
        typ_impl.is_collection = True

        # continue parsing TDS to determine element type
        buf.read_uint32(&element_pos)
        buf.read_uint32(&typ_impl.max_num_elements)
        buf.read_ub1(&typ_impl.collection_type)
        if typ_impl.collection_type == TNS_OBJ_PLSQL_INDEX_TABLE:
            typ_impl.collection_flags = TNS_OBJ_HAS_INDEXES
        buf.skip_to(element_pos)
        self._parse_element_type(typ_impl, buf)

    cdef int _populate_type_info(self, str name,
                                 ThinDbObjectTypeImpl typ_impl) except -1:
        """
        Populate the type information given the name of the type.
        """
        cdef:
            ThinDbObjectAttrImpl attr_impl
            ssize_t pos, name_length
            list name_components
            object attrs_rc
        self.full_name_var.setvalue(0, name)
        self.meta_cursor.execute(None)
        if self.return_value_var.getvalue() != 0:
            errors._raise_err(errors.ERR_INVALID_OBJECT_TYPE_NAME, name=name)
        typ_impl.version = self.version_var.getvalue()
        if typ_impl.oid is None:
            typ_impl.oid = self.oid_var.getvalue()
            self.types_by_oid[typ_impl.oid] = typ_impl
        if typ_impl.schema is None:
            typ_impl.schema = self.schema_var.getvalue()
            typ_impl.package_name = self.package_name_var.getvalue()
            typ_impl.name = self.name_var.getvalue()
            typ_impl.is_xml_type = \
                    (typ_impl.schema == "SYS" and typ_impl.name == "XMLTYPE")
        self._parse_tds(typ_impl, self.tds_var.getvalue())
        typ_impl.attrs = []
        typ_impl.attrs_by_name = {}
        attrs_rc = self.attrs_ref_cursor_var.getvalue()
        for cursor_version, attr_name, attr_num, attr_type_name, \
                attr_type_owner, attr_type_package, attr_type_oid, \
                attr_instantiable, attr_super_type_owner, \
                attr_super_type_name in attrs_rc:
            attr_impl = ThinDbObjectAttrImpl.__new__(ThinDbObjectAttrImpl)
            attr_impl.name = attr_name
            if attr_type_owner is not None:
                attr_impl.dbtype = DB_TYPE_OBJECT
                attr_impl.objtype = self.get_type_for_info(attr_type_oid,
                                                           attr_type_owner,
                                                           attr_type_package,
                                                           attr_type_name)
            else:
                attr_impl.dbtype = DbType._from_ora_name(attr_type_name)
            typ_impl.attrs.append(attr_impl)
            typ_impl.attrs_by_name[attr_name] = attr_impl

    cdef ThinDbObjectTypeImpl get_type(self, object conn, str name):
        """
        Returns the database object type given its name. The cache is first
        searched and if it is not found, the database is searched and the
        result stored in the cache.
        """
        cdef ThinDbObjectTypeImpl typ_impl
        typ_impl = self.types_by_name.get(name)
        if typ_impl is None:
            if self.meta_cursor is None:
                self._init_meta_cursor(conn)
            typ_impl = ThinDbObjectTypeImpl.__new__(ThinDbObjectTypeImpl)
            typ_impl._conn_impl = self.conn_impl
            self._populate_type_info(name, typ_impl)
            self.types_by_oid[typ_impl.oid] = typ_impl
            self.types_by_name[name] = typ_impl
            self.populate_partial_types(conn)
        return typ_impl

    cdef ThinDbObjectTypeImpl get_type_for_info(self, bytes oid, str schema,
                                                str package_name, str name):
        """
        Returns a type for the specified fetch info, if one has already been
        cached. If not, a new type object is created and cached. It is also
        added to the partial_types list which will be fully populated once the
        current execute has completed.
        """
        cdef:
            ThinDbObjectTypeImpl typ_impl
            str full_name
        if package_name is not None:
            full_name = f"{schema}.{package_name}.{name}"
        else:
            full_name = f"{schema}.{name}"
        if oid is not None:
            typ_impl = self.types_by_oid.get(oid)
        else:
            typ_impl = self.types_by_name.get(full_name)
        if typ_impl is None:
            typ_impl = ThinDbObjectTypeImpl.__new__(ThinDbObjectTypeImpl)
            typ_impl._conn_impl = self.conn_impl
            typ_impl.oid = oid
            typ_impl.schema = schema
            typ_impl.package_name = package_name
            typ_impl.name = name
            typ_impl.is_xml_type = (schema == "SYS" and name == "XMLTYPE")
            if oid is not None:
                self.types_by_oid[oid] = typ_impl
            self.types_by_name[full_name] = typ_impl
            self.partial_types.append(typ_impl)
        return typ_impl

    cdef int populate_partial_types(self, object conn) except -1:
        """
        Populate any partial types that were discovered earlier. Since
        populating an object type might result in additional object types being
        discovered, object types are popped from the partial types list until
        the list is empty.
        """
        cdef:
            ThinDbObjectTypeImpl typ_impl
            str full_name, name, suffix
        while self.partial_types:
            typ_impl = self.partial_types.pop()
            if self.meta_cursor is None:
                self._init_meta_cursor(conn)
            suffix = "%ROWTYPE"
            if typ_impl.name.endswith(suffix):
                name = typ_impl.name[:-len(suffix)]
            else:
                name = typ_impl.name
                suffix = ""
            if typ_impl.package_name is not None:
                full_name = f'"{typ_impl.schema}".' + \
                            f'"{typ_impl.package_name}".' + \
                            f'"{name}"{suffix}'
            else:
                full_name = f'"{typ_impl.schema}"."{name}"{suffix}'
            self._populate_type_info(full_name, typ_impl)


# global cache of database object types
# since the database object types require a reference to the connection (in
# order to be able to manage LOBs), storing the cache on the connection would
# involve creating a circular reference
cdef ThinDbObjectTypeSuperCache DB_OBJECT_TYPE_SUPER_CACHE = \
        ThinDbObjectTypeSuperCache()


cdef int create_new_dbobject_type_cache(ThinConnImpl conn_impl) except -1:
    """
    Creates a new database object type cache and returns its identifier.
    """
    cdef:
        ThinDbObjectTypeCache cache
        int cache_num
    with DB_OBJECT_TYPE_SUPER_CACHE.lock:
        DB_OBJECT_TYPE_SUPER_CACHE.cache_num += 1
        cache_num = DB_OBJECT_TYPE_SUPER_CACHE.cache_num
    cache = ThinDbObjectTypeCache.__new__(ThinDbObjectTypeCache)
    cache._initialize(conn_impl)
    DB_OBJECT_TYPE_SUPER_CACHE.caches[cache_num] = cache
    return cache_num


cdef ThinDbObjectTypeCache get_dbobject_type_cache(int cache_num):
    """
    Returns the database object type cache given its identifier.
    """
    return DB_OBJECT_TYPE_SUPER_CACHE.caches[cache_num]


cdef int remove_dbobject_type_cache(int cache_num) except -1:
    """
    Removes the sub cache given its identifier.
    """
    del DB_OBJECT_TYPE_SUPER_CACHE.caches[cache_num]
