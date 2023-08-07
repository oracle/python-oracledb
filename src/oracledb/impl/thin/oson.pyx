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
# json.pyx
#
# Cython file defining the classes and methods used for encoding and decoding
# OSON (Oracle's extensions to JSON) (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

@cython.final
cdef class OsonDecoder(Buffer):

    cdef:
        ssize_t field_id_length
        ssize_t tree_seg_pos
        list field_names
        uint16_t flags

    cdef object _decode_container_node(self, uint8_t node_type):
        """
        Parses a container node (object or array) and returns it.
        """
        cdef:
            bint is_shared, is_object = (node_type & 0x40) == 0
            ssize_t field_ids_pos = 0, offsets_pos = 0, pos
            uint32_t i, num_children = 0
            uint32_t offset, temp32
            uint16_t temp16
            uint8_t temp8
            object value
            str name

        # determine the number of children by examining the 4th and 5th most
        # significant bits of the node type; determine the offsets in the tree
        # segment to the field ids array and the value offsets array
        self._get_num_children(node_type, &num_children, &is_shared)
        if is_shared:
            value = {}
            self._get_offset(node_type, &offset)
            offsets_pos = self._pos
            self.skip_to(self.tree_seg_pos + offset)
            self.read_ub1(&temp8)
            self._get_num_children(temp8, &num_children, &is_shared)
            field_ids_pos = self._pos
        elif is_object:
            value = {}
            field_ids_pos = self._pos
            offsets_pos = self._pos + self.field_id_length * num_children
        else:
            value = [None] * num_children
            offsets_pos = self._pos

        # process each of the children
        for i in range(num_children):
            if is_object:
                self.skip_to(field_ids_pos)
                if self.field_id_length == 1:
                    self.read_ub1(&temp8)
                    name = self.field_names[temp8 - 1]
                elif self.field_id_length == 2:
                    self.read_uint16(&temp16)
                    name = self.field_names[temp16 - 1]
                else:
                    self.read_uint32(&temp32)
                    name = self.field_names[temp32 - 1]
                field_ids_pos = self._pos
            self.skip_to(offsets_pos)
            self._get_offset(node_type, &offset)
            offsets_pos = self._pos
            self.skip_to(self.tree_seg_pos + offset)
            if is_object:
                value[name] = self._decode_node()
            else:
                value[i] = self._decode_node()

        return value

    cdef object _decode_node(self):
        """
        Parses a node from the tree segment and returns the Python equivalent.
        """
        cdef:
            uint8_t node_type, temp8
            const char_type* ptr
            uint16_t temp16
            uint32_t temp32

        # if the most significant bit is set the node refers to a container
        self.read_ub1(&node_type)
        if node_type & 0x80:
            return self._decode_container_node(node_type)

        # handle simple scalars
        if node_type == TNS_JSON_TYPE_NULL:
            return None
        elif node_type == TNS_JSON_TYPE_TRUE:
            return True
        elif node_type == TNS_JSON_TYPE_FALSE:
            return False

        # handle fixed length scalars
        elif node_type in (TNS_JSON_TYPE_DATE, TNS_JSON_TYPE_TIMESTAMP7):
            ptr = self._get_raw(7)
            return self.parse_date(ptr, 7)
        elif node_type == TNS_JSON_TYPE_TIMESTAMP:
            ptr = self._get_raw(11)
            return self.parse_date(ptr, 11)
        elif node_type == TNS_JSON_TYPE_TIMESTAMP_TZ:
            ptr = self._get_raw(13)
            return self.parse_date(ptr, 13)
        elif node_type == TNS_JSON_TYPE_BINARY_FLOAT:
            ptr = self._get_raw(4)
            return self.parse_binary_float(ptr)
        elif node_type == TNS_JSON_TYPE_BINARY_DOUBLE:
            ptr = self._get_raw(8)
            return self.parse_binary_double(ptr)
        elif node_type == TNS_JSON_TYPE_INTERVAL_DS:
            ptr = self._get_raw(11)
            return self.parse_interval_ds(ptr)
        elif node_type == TNS_JSON_TYPE_INTERVAL_YM:
            errors._raise_err(errors.ERR_DB_TYPE_NOT_SUPPORTED,
                              name="DB_TYPE_INTERVAL_YM")

        # handle scalars with lengths stored outside the node itself
        elif node_type == TNS_JSON_TYPE_STRING_LENGTH_UINT8:
            self.read_ub1(&temp8)
            ptr = self._get_raw(temp8)
            return ptr[:temp8].decode()
        elif node_type == TNS_JSON_TYPE_STRING_LENGTH_UINT16:
            self.read_uint16(&temp16)
            ptr = self._get_raw(temp16)
            return ptr[:temp16].decode()
        elif node_type == TNS_JSON_TYPE_STRING_LENGTH_UINT32:
            self.read_uint32(&temp32)
            ptr = self._get_raw(temp32)
            return ptr[:temp32].decode()
        elif node_type == TNS_JSON_TYPE_NUMBER_LENGTH_UINT8:
            return self.read_oracle_number(NUM_TYPE_DECIMAL)
        elif node_type == TNS_JSON_TYPE_ID:
            self.read_ub1(&temp8)
            ptr = self._get_raw(temp8)
            return ptr[:temp8]
        elif node_type == TNS_JSON_TYPE_BINARY_LENGTH_UINT16:
            self.read_uint16(&temp16)
            ptr = self._get_raw(temp16)
            return ptr[:temp16]
        elif node_type == TNS_JSON_TYPE_BINARY_LENGTH_UINT32:
            self.read_uint32(&temp32)
            ptr = self._get_raw(temp32)
            return ptr[:temp32]

        # handle number/decimal with length stored inside the node itself
        if (node_type & 0xf0) in (0x20, 0x60):
            temp8 = node_type & 0x0f
            ptr = self._get_raw(temp8 + 1)
            return self.parse_oracle_number(ptr, temp8 + 1, NUM_TYPE_DECIMAL)

        # handle integer with length stored inside the node itself
        elif (node_type & 0xf0) in (0x40, 0x50):
            temp8 = node_type & 0x0f
            ptr = self._get_raw(temp8)
            return self.parse_oracle_number(ptr, temp8, NUM_TYPE_DECIMAL)

        # handle string with length stored inside the node itself
        elif (node_type & 0xe0) == 0:
            if node_type == 0:
                return ''
            ptr = self._get_raw(node_type)
            return ptr[:node_type].decode()

        errors._raise_err(errors.ERR_OSON_NODE_TYPE_NOT_SUPPORTED,
                          node_type=node_type)

    cdef int _get_num_children(self, uint8_t node_type, uint32_t* num_children,
                               bint* is_shared) except -1:
        """
        Return the number of children the container has. This is determined by
        examining the 4th and 5th signficant bits of the node type:

            00 - number of children is uint8_t
            01 - number of children is uint16_t
            10 - number of children is uint32_t
            11 - field ids are shared with another object whose offset follows

        In the latter case the flag is_shared is set and the number of children
        is read by the caller instead as it must examine the offset and then
        retain the location for later use.
        """
        cdef:
            uint8_t temp8, children_bits = (node_type & 0x18)
            uint16_t temp16
        is_shared[0] = (children_bits == 0x18)
        if children_bits == 0:
            self.read_ub1(&temp8)
            num_children[0] = temp8
        elif children_bits == 0x08:
            self.read_uint16(&temp16)
            num_children[0] = temp16
        elif children_bits == 0x10:
            self.read_uint32(num_children)

    cdef int _get_offset(self, uint8_t node_type, uint32_t* offset) except -1:
        """
        Return an offset. The offset will be either a 16-bit or 32-bit value
        depending on the value of the 3rd significant bit of the node type.
        """
        cdef uint16_t temp16
        if node_type & 0x20:
            self.read_uint32(offset)
        else:
            self.read_uint16(&temp16)
            offset[0] = temp16

    cdef object decode(self, bytes data):
        """
        Returns a Python object corresponding to the encoded OSON bytes.
        """
        cdef:
            uint32_t num_field_names, field_names_seg_size, tree_seg_size, i
            ssize_t hash_id_size, field_name_offsets_size
            uint16_t num_tiny_nodes, temp16
            ssize_t field_name_offsets_pos
            uint8_t version, temp8
            const char_type* ptr
            uint32_t offset

        # populate the buffer with the data
        self._populate_from_bytes(data)

        # parse root header
        ptr = self._get_raw(3)
        if ptr[0] != TNS_JSON_MAGIC_BYTE_1 or \
                ptr[1] != TNS_JSON_MAGIC_BYTE_2 or \
                ptr[2] != TNS_JSON_MAGIC_BYTE_3:
            errors._raise_err(errors.ERR_UNEXPECTED_DATA, data=ptr[:3])
        self.read_ub1(&version)
        if version != TNS_JSON_VERSION:
            errors._raise_err(errors.ERR_OSON_VERSION_NOT_SUPPORTED,
                              version=version)
        self.read_uint16(&self.flags)

        # if value is a scalar value, the header is much smaller
        if self.flags & TNS_JSON_FLAG_IS_SCALAR:
            if self.flags & TNS_JSON_FLAG_TREE_SEG_UINT32:
                self.skip_raw_bytes(4)
            else:
                self.skip_raw_bytes(2)
            return self._decode_node()

        # determine the number of field names
        if self.flags & TNS_JSON_FLAG_NUM_FNAMES_UINT32:
            self.read_uint32(&num_field_names)
            self.field_id_length = 4
        elif self.flags & TNS_JSON_FLAG_NUM_FNAMES_UINT16:
            self.read_uint16(&temp16)
            num_field_names = temp16
            self.field_id_length = 2
        else:
            self.read_ub1(&temp8)
            num_field_names = temp8
            self.field_id_length = 1

        # determine the size of the field names segment
        if self.flags & TNS_JSON_FLAG_FNAMES_SEG_UINT32:
            field_name_offsets_size = 4
            self.read_uint32(&field_names_seg_size)
        else:
            field_name_offsets_size = 2
            self.read_uint16(&temp16)
            field_names_seg_size = temp16

        # determine the size of the tree segment
        if self.flags & TNS_JSON_FLAG_TREE_SEG_UINT32:
            self.read_uint32(&tree_seg_size)
        else:
            self.read_uint16(&temp16)
            tree_seg_size = temp16

        # determine the number of "tiny" nodes
        self.read_uint16(&num_tiny_nodes)

        # skip the hash id array
        if self.flags & TNS_JSON_FLAG_HASH_ID_UINT8:
            hash_id_size = 1
        elif self.flags & TNS_JSON_FLAG_HASH_ID_UINT16:
            hash_id_size = 2
        else:
            hash_id_size = 4
        self.skip_raw_bytes(num_field_names * hash_id_size)

        # skip the field name offsets array for now
        field_name_offsets_pos = self._pos
        self.skip_raw_bytes(num_field_names * field_name_offsets_size)
        ptr = self._get_raw(field_names_seg_size)

        # determine the names of the fields
        self.skip_to(field_name_offsets_pos)
        self.field_names = [None] * num_field_names
        for i in range(num_field_names):
            if self.flags & TNS_JSON_FLAG_FNAMES_SEG_UINT32:
                self.read_uint32(&offset)
            else:
                self.read_uint16(&temp16)
                offset = temp16
            temp8 = ptr[offset]
            self.field_names[i] = ptr[offset + 1:offset + temp8 + 1].decode()

        # get tree segment
        self.skip_raw_bytes(field_names_seg_size)
        self.tree_seg_pos = self._pos

        # return root node
        return self._decode_node()


@cython.final
cdef class OsonFieldName:

    cdef:
        str name
        bytes name_bytes
        ssize_t name_bytes_len
        uint32_t hash_id
        uint32_t offset
        uint32_t field_id

    cdef int _calc_hash_id(self) except -1:
        """
        Calculates the hash id to use for the field name. This is based on
        Bernstein's hash function.
        """
        cdef:
            const char_type *ptr = self.name_bytes
            ssize_t i
        self.hash_id = 0x811C9DC5
        for i in range(self.name_bytes_len):
            self.hash_id = (self.hash_id ^ ptr[i]) * 16777619

    @staticmethod
    cdef OsonFieldName create(str name):
        """
        Creates and initializes the field name.
        """
        cdef:
            OsonFieldName field_name
            ssize_t name_bytes_len
        field_name = OsonFieldName.__new__(OsonFieldName)
        field_name.name = name
        field_name.name_bytes = name.encode()
        name_bytes_len = len(field_name.name_bytes)
        if name_bytes_len > 255:
            errors._raise_err(errors.ERR_OSON_FIELD_NAME_LIMITATION)
        field_name.name_bytes_len = <uint8_t> name_bytes_len
        field_name._calc_hash_id()
        return field_name

    def sort_key(self):
        """
        Returns the sort key to use when sorting field names.
        """
        return ((self.hash_id & 0xff), self.name_bytes_len, self.name_bytes)


@cython.final
cdef class OsonFieldNamesSegment(GrowableBuffer):

    cdef:
        uint32_t num_field_names
        dict field_names_dict
        list field_names

    cdef int _examine_node(self, object value) except -1:
        """
        Examines the value. If it is a dictionary, all keys are extracted and
        unique names retained. Elements in lists and tuples and values in
        dictionaries are then examined to determine if they contain
        dictionaries as well.
        """
        cdef OsonFieldName field_name
        if isinstance(value, (list, tuple)):
            for child_value in value:
                self._examine_node(child_value)
        elif isinstance(value, dict):
            for key, child_value in (<dict> value).items():
                if key not in self.field_names_dict:
                    field_name = OsonFieldName.create(key)
                    self.field_names_dict[key] = field_name
                    field_name.offset = self._pos
                    self.write_uint8(field_name.name_bytes_len)
                    self.write_bytes(field_name.name_bytes)
                self._examine_node(child_value)

    cdef int _process_field_names(self) except -1:
        """
        Processes the field names in preparation for encoding within OSON.
        """
        cdef:
            OsonFieldName field_name
            ssize_t i
        self.field_names = sorted(self.field_names_dict.values(),
                                  key=OsonFieldName.sort_key)
        for i, field_name in enumerate(self.field_names):
            field_name.field_id = i + 1
        self.num_field_names = <uint32_t> len(self.field_names)

    @staticmethod
    cdef OsonFieldNamesSegment create(object value):
        """
        Creates and initializes the segment. The value (and all of its
        children) are examined for dictionaries and the keys retained as
        required by OSON.
        """
        cdef OsonFieldNamesSegment seg
        seg = OsonFieldNamesSegment.__new__(OsonFieldNamesSegment)
        seg._initialize(TNS_CHUNK_SIZE)
        seg.field_names_dict = {}
        seg._examine_node(value)
        seg._process_field_names()
        return seg


@cython.final
cdef class OsonTreeSegment(GrowableBuffer):

    cdef int _encode_container(self, uint8_t node_type,
                               ssize_t num_children) except -1:
        """
        Encodes the first part of a container.
        """
        node_type |= 0x20                   # use uint32_t for offsets
        if num_children > 65535:
            node_type |= 0x10               # num children is uint32_t
        elif num_children > 255:
            node_type |= 0x08               # num children is uint16_t
        self.write_uint8(node_type)
        if num_children < 256:
            self.write_uint8(<uint8_t> num_children)
        elif num_children < 65536:
            self.write_uint16(<uint16_t> num_children)
        else:
            self.write_uint32(<uint32_t> num_children)

    cdef int encode_array(self, object value,
                          OsonFieldNamesSegment fnames_seg) except -1:
        """
        Encode an array in the OSON tree segment.
        """
        cdef:
            ssize_t num_children
            uint8_t node_type
            uint32_t offset
        num_children = len(value)
        self._encode_container(TNS_JSON_TYPE_ARRAY, num_children)
        offset = self._pos
        self._reserve_space(num_children * sizeof(uint32_t))
        for element in value:
            pack_uint32(&self._data[offset], self._pos, BYTE_ORDER_MSB)
            offset += sizeof(uint32_t)
            self.encode_node(element, fnames_seg)

    cdef int encode_object(self, dict value,
                           OsonFieldNamesSegment fnames_seg) except -1:
        """
        Encode an object in the OSON tree segment.
        """
        cdef:
            uint32_t field_id_offset, value_offset
            uint8_t node_type, field_id_size
            OsonFieldName field_name
            ssize_t num_children
            object child_value
            str key
        num_children = len(value)
        self._encode_container(TNS_JSON_TYPE_OBJECT, num_children)
        if fnames_seg.num_field_names < 256:
            field_id_size = 1
        elif fnames_seg.num_field_names < 65536:
            field_id_size = 2
        else:
            field_id_size = 4
        field_id_offset = self._pos
        value_offset = self._pos + num_children * field_id_size
        self._reserve_space(num_children * (field_id_size + sizeof(uint32_t)))
        for key, child_value in value.items():
            field_name = fnames_seg.field_names_dict[key]
            if field_id_size == 1:
                self._data[field_id_offset] = <uint8_t> field_name.field_id
            elif field_id_size == 2:
                pack_uint16(&self._data[field_id_offset],
                            <uint16_t> field_name.field_id, BYTE_ORDER_MSB)
            else:
                pack_uint32(&self._data[field_id_offset], field_name.field_id,
                            BYTE_ORDER_MSB)
            pack_uint32(&self._data[value_offset], self._pos, BYTE_ORDER_MSB)
            field_id_offset += field_id_size
            value_offset += sizeof(uint32_t)
            self.encode_node(child_value, fnames_seg)

    cdef int encode_node(self, object value,
                         OsonFieldNamesSegment fnames_seg) except -1:
        """
        Encode a value (node) in the OSON tree segment.
        """
        cdef:
            uint32_t value_len
            bytes value_bytes

        # handle null
        if value is None:
            self.write_uint8(TNS_JSON_TYPE_NULL)

        # handle booleans
        elif isinstance(value, bool):
            if value is True:
                self.write_uint8(TNS_JSON_TYPE_TRUE)
            else:
                self.write_uint8(TNS_JSON_TYPE_FALSE)

        # handle numeric types
        elif isinstance(value, (int, float, PY_TYPE_DECIMAL)):
            value_bytes = (<str> cpython.PyObject_Str(value)).encode()
            self.write_uint8(TNS_JSON_TYPE_NUMBER_LENGTH_UINT8)
            self.write_oracle_number(value_bytes)

        # handle bytes
        elif isinstance(value, bytes):
            value_len = len(<bytes> value)
            if value_len < 65536:
                self.write_uint8(TNS_JSON_TYPE_BINARY_LENGTH_UINT16)
                self.write_uint16(<uint16_t> value_len)
            else:
                self.write_uint8(TNS_JSON_TYPE_BINARY_LENGTH_UINT32)
                self.write_uint32(value_len)
            self.write_bytes(<bytes> value)

        # handle timestamps
        elif isinstance(value, PY_TYPE_DATETIME):
            if cydatetime.PyDateTime_DATE_GET_MICROSECOND(value) == 0:
                self.write_uint8(TNS_JSON_TYPE_TIMESTAMP7)
                self.write_oracle_date(value, 7, write_length=False)
            else:
                self.write_uint8(TNS_JSON_TYPE_TIMESTAMP)
                self.write_oracle_date(value, 11, write_length=False)

        # handle dates
        elif isinstance(value, PY_TYPE_DATE):
            self.write_uint8(TNS_JSON_TYPE_DATE)
            self.write_oracle_date(value, 7, write_length=False)

        # handle timedeltas
        elif isinstance(value, PY_TYPE_TIMEDELTA):
            self.write_uint8(TNS_JSON_TYPE_INTERVAL_DS)
            self.write_interval_ds(value, write_length=False)

        # handle strings
        elif isinstance(value, str):
            value_bytes = (<str> value).encode()
            value_len = len(value_bytes)
            if value_len < 256:
                self.write_uint8(TNS_JSON_TYPE_STRING_LENGTH_UINT8)
                self.write_uint8(<uint8_t> value_len)
            elif value_len < 65536:
                self.write_uint8(TNS_JSON_TYPE_STRING_LENGTH_UINT16)
                self.write_uint16(<uint16_t> value_len)
            else:
                self.write_uint8(TNS_JSON_TYPE_STRING_LENGTH_UINT32)
                self.write_uint32(value_len)
            if value_len > 0:
                self.write_bytes(value_bytes)

        # handle lists/tuples
        elif isinstance(value, (list, tuple)):
            self.encode_array(value, fnames_seg)

        # handle dictionaries
        elif isinstance(value, dict):
            self.encode_object(value, fnames_seg)

        # other types are not supported
        else:
            errors._raise_err(errors.ERR_PYTHON_TYPE_NOT_SUPPORTED,
                              typ=type(value).__name__)


@cython.final
cdef class OsonEncoder(GrowableBuffer):

    cdef int encode(self, object value) except -1:
        """
        Encodes the given value to OSON.
        """
        cdef:
            OsonFieldNamesSegment fnames_seg = None
            OsonFieldName field_name
            OsonTreeSegment tree_seg
            uint16_t flags

        # determine the flags to use
        flags = TNS_JSON_FLAG_INLINE_LEAF
        if isinstance(value, (list, tuple, dict)):
            flags |= TNS_JSON_FLAG_HASH_ID_UINT8 | \
                     TNS_JSON_FLAG_TINY_NODES_STAT
            fnames_seg = OsonFieldNamesSegment.create(value);
            if fnames_seg.num_field_names > 65535:
                flags |= TNS_JSON_FLAG_NUM_FNAMES_UINT32
            elif fnames_seg.num_field_names > 255:
                flags |= TNS_JSON_FLAG_NUM_FNAMES_UINT16
            if fnames_seg._pos > 65535:
                flags |= TNS_JSON_FLAG_FNAMES_SEG_UINT32
        else:
            flags |= TNS_JSON_FLAG_IS_SCALAR

        # encode values into tree segment
        tree_seg = OsonTreeSegment.__new__(OsonTreeSegment)
        tree_seg._initialize(TNS_CHUNK_SIZE)
        tree_seg.encode_node(value, fnames_seg)
        if tree_seg._pos > 65535:
            flags |= TNS_JSON_FLAG_TREE_SEG_UINT32

        # write initial header
        self.write_uint8(TNS_JSON_MAGIC_BYTE_1)
        self.write_uint8(TNS_JSON_MAGIC_BYTE_2)
        self.write_uint8(TNS_JSON_MAGIC_BYTE_3)
        self.write_uint8(TNS_JSON_VERSION)
        self.write_uint16(flags)

        # write extended header (when value is not scalar)
        if fnames_seg is not None:

            # write number of field names
            if fnames_seg.num_field_names < 256:
                self.write_uint8(<uint8_t> fnames_seg.num_field_names)
            elif fnames_seg.num_field_names < 65536:
                self.write_uint16(<uint16_t> fnames_seg.num_field_names)
            else:
                self.write_uint32(fnames_seg.num_field_names)

            # write size of field names segment
            if fnames_seg._pos < 65536:
                self.write_uint16(<uint16_t> fnames_seg._pos)
            else:
                self.write_uint32(fnames_seg._pos)

        # write size of tree segment
        if (tree_seg._pos < 65536):
            self.write_uint16(<uint16_t> tree_seg._pos)
        else:
            self.write_uint32(tree_seg._pos)

        # write remainder of header and any data (when value is not scalar)
        if fnames_seg is not None:

            # write number of "tiny" nodes (always zero)
            self.write_uint16(0)

            # write array of hash ids
            for field_name in fnames_seg.field_names:
                self.write_uint8(field_name.hash_id & 0xff)

            # write array of field name offsets
            for field_name in fnames_seg.field_names:
                if fnames_seg._pos < 65536:
                    self.write_uint16(<uint16_t> field_name.offset)
                else:
                    self.write_uint32(field_name.offset)

            # write field names
            if fnames_seg._pos > 0:
                self.write_raw(fnames_seg._data, fnames_seg._pos)

        # write tree segment data
        self.write_raw(tree_seg._data, tree_seg._pos)
