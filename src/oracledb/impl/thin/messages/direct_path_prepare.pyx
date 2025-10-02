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
# direct_path_prepare.pyx
#
# Cython file defining the messages that are sent to the database and the
# responses that are received by the client for preparing a direct path cursor
# for execution (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

@cython.final
cdef class DirectPathPrepareMessage(Message):
    cdef:
        str schema_name
        str table_name
        list column_names
        list column_metadata
        uint32_t in_values[TNS_DPP_IN_MAX_PARAMS]
        uint16_t in_values_length
        uint32_t *out_values
        uint16_t out_values_length
        uint16_t cursor_id

    def __dealloc__(self):
        if self.out_values != NULL:
            cpython.PyMem_Free(self.out_values)

    cdef int _initialize_hook(self) except -1:
        """
        Perform initialization.
        """
        self.function_code = TNS_FUNC_DIRECT_PATH_PREPARE
        memset(self.in_values, 0, sizeof(self.in_values))
        self.in_values[TNS_DPP_KW_INDEX_NFOBJ_OID_POS] = 0xffff
        self.in_values[TNS_DPP_KW_INDEX_NFOBJ_SID_POS] = 0xffff
        self.in_values[TNS_DPP_KW_INDEX_NFOBJ_VARRAY_INDEX] = 0xffff

    cdef OracleMetadata _process_metadata(self, ReadBuffer buf):
        """
        Process metadata returned by the database. CLOB and BLOB are always
        treated as strings and bytes when using direct path.
        """
        cdef OracleMetadata metadata
        metadata = Message._process_metadata(self, buf)
        if metadata.dbtype._ora_type_num == ORA_TYPE_NUM_CLOB:
            metadata.dbtype = DbType._from_ora_type_and_csfrm(
                ORA_TYPE_NUM_LONG, CS_FORM_NCHAR
            )
        elif metadata.dbtype._ora_type_num == ORA_TYPE_NUM_BLOB:
            metadata.dbtype = DbType._from_ora_type_and_csfrm(
                ORA_TYPE_NUM_LONG_RAW, 0
            )
        return metadata

    cdef int _process_return_parameters(self, ReadBuffer buf) except -1:
        """
        Process the return parameters sent by the database.
        """
        cdef:
            uint32_t i, num_columns
            uint16_t num_params
            ssize_t num_bytes
        buf.read_ub4(&num_columns)
        self.column_metadata = [
            self._process_metadata(buf) for i in range(num_columns)
        ]
        buf.read_ub2(&num_params)
        if num_params > 0:
            raise Exception("FIX ME!")
        buf.read_ub2(&self.out_values_length)
        num_bytes = sizeof(uint32_t) * self.out_values_length
        self.out_values = <uint32_t*> cpython.PyMem_Malloc(num_bytes)
        for i in range(self.out_values_length):
            buf.read_ub4(&self.out_values[i])
        self.cursor_id = self.out_values[TNS_DPP_OUT_INDEX_CURSOR]

    cdef void _set_in_value(self, uint32_t key, uint32_t value):
        """
        Sets the value in the input array and the maximum value set.
        """
        self.in_values[key] = value
        self.in_values_length = max(self.in_values_length, key + 1)

    cdef int _write_keyword_param(self, WriteBuffer buf, uint32_t index,
                                  str value) except -1:
        """
        Writes a keyword parameter to the buffer.
        """
        cdef bytes value_bytes = value.encode()
        buf.write_ub2(0)                    # text length
        buf.write_ub2(len(value_bytes))
        buf.write_bytes_with_length(value_bytes)
        buf.write_ub2(index)

    cdef int _write_message(self, WriteBuffer buf) except -1:
        """
        Writes the message to the database.
        """
        cdef:
            uint32_t i, keyword_parameters_length
            str name

        # initialize input array
        self._set_in_value(TNS_DPP_IN_INDEX_INTERFACE_VERSION,
                           TNS_DP_INTERFACE_VERSION)
        self._set_in_value(TNS_DPP_IN_INDEX_STREAM_VERSION,
                           TNS_DP_STREAM_VERSION)
        self._set_in_value(TNS_DPP_IN_INDEX_LOCK_WAIT, 1)

        # write message
        self._write_function_code(buf)
        keyword_parameters_length = len(self.column_names) + 2
        buf.write_ub4(TNS_DPP_OP_CODE_LOAD)
        buf.write_uint8(1)                  # keyword parameters (pointer)
        buf.write_ub4(keyword_parameters_length)
        buf.write_uint8(1)                  # input array (pointer)
        buf.write_ub2(self.in_values_length)
        buf.write_uint8(1)                  # metadata (pointer)
        buf.write_uint8(1)                  # metadata length (pointer)
        buf.write_uint8(1)                  # parameters (pointer)
        buf.write_uint8(1)                  # parameters length (pointer)
        buf.write_uint8(1)                  # output array (pointer)
        buf.write_uint8(1)                  # output array length (pointer)
        self._write_keyword_param(buf, TNS_DPP_KW_INDEX_SCHEMA_NAME,
                                  self.schema_name)
        self._write_keyword_param(buf, TNS_DPP_KW_INDEX_OBJECT_NAME,
                                  self.table_name)
        for name in self.column_names:
            self._write_keyword_param(buf, TNS_DPP_KW_INDEX_COLUMN_NAME, name)
        for i in range(self.in_values_length):
            buf.write_ub4(self.in_values[i])
