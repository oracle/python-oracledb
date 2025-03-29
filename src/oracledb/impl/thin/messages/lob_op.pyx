#------------------------------------------------------------------------------
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
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
# lob_op.pyx
#
# Cython file defining the messages that are sent to the database and the
# responses that are received by the client for performing LOB operations
# (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

@cython.final
cdef class LobOpMessage(Message):
    cdef:
        uint32_t operation
        BaseThinLobImpl source_lob_impl
        uint64_t source_offset
        uint64_t dest_offset
        uint32_t dest_length
        int64_t amount
        bint send_amount
        bint bool_flag
        object data

    cdef int _initialize_hook(self) except -1:
        """
        Perform initialization.
        """
        self.function_code = TNS_FUNC_LOB_OP

    cdef int _process_message(self, ReadBuffer buf,
                              uint8_t message_type) except -1:
        cdef:
            const char* encoding
            const char_type *ptr
            ssize_t num_bytes
        if message_type == TNS_MSG_TYPE_LOB_DATA:
            buf.read_raw_bytes_and_length(&ptr, &num_bytes)
            if self.source_lob_impl.dbtype._ora_type_num in \
                    (ORA_TYPE_NUM_BLOB, ORA_TYPE_NUM_BFILE):
                self.data = ptr[:num_bytes]
            else:
                encoding = self.source_lob_impl._get_encoding()
                self.data = ptr[:num_bytes].decode(encoding)
        else:
            Message._process_message(self, buf, message_type)

    cdef int _process_return_parameters(self, ReadBuffer buf) except -1:
        cdef:
            cdef const char_type *ptr
            ssize_t num_bytes
            uint8_t temp8
        if self.source_lob_impl is not None:
            num_bytes = len(self.source_lob_impl._locator)
            ptr = buf.read_raw_bytes(num_bytes)
            self.source_lob_impl._locator = ptr[:num_bytes]
        if self.operation == TNS_LOB_OP_CREATE_TEMP:
            buf.skip_ub2()                  # skip character set
            buf.skip_ub1()                  # skip trailing flags
        elif self.send_amount:
            buf.read_sb8(&self.amount)
        if self.operation in (TNS_LOB_OP_IS_OPEN,
                              TNS_LOB_OP_FILE_EXISTS,
                              TNS_LOB_OP_FILE_ISOPEN):
            buf.read_ub1(&temp8)
            self.bool_flag = temp8 > 0

    cdef int _write_message(self, WriteBuffer buf) except -1:
        cdef int i
        self._write_function_code(buf)
        if self.source_lob_impl is None:
            buf.write_uint8(0)              # source pointer
            buf.write_ub4(0)                # source length
        else:
            buf.write_uint8(1)              # source pointer
            buf.write_ub4(len(self.source_lob_impl._locator))
        buf.write_uint8(0)                  # dest pointer
        buf.write_ub4(self.dest_length)
        buf.write_ub4(0)                    # short source offset
        buf.write_ub4(0)                    # short dest offset
        if self.operation == TNS_LOB_OP_CREATE_TEMP:
            buf.write_uint8(1)              # pointer (character set)
        else:
            buf.write_uint8(0)              # pointer (character set)
        buf.write_uint8(0)                  # pointer (short amount)
        if self.operation in (TNS_LOB_OP_CREATE_TEMP,
                              TNS_LOB_OP_IS_OPEN,
                              TNS_LOB_OP_FILE_EXISTS,
                              TNS_LOB_OP_FILE_ISOPEN):
            buf.write_uint8(1)              # pointer (NULL LOB)
        else:
            buf.write_uint8(0)              # pointer (NULL LOB)
        buf.write_ub4(self.operation)
        buf.write_uint8(0)                  # pointer (SCN array)
        buf.write_uint8(0)                  # SCN array length
        buf.write_ub8(self.source_offset)
        buf.write_ub8(self.dest_offset)
        if self.send_amount:
            buf.write_uint8(1)              # pointer (amount)
        else:
            buf.write_uint8(0)              # pointer (amount)
        for i in range(3):                  # array LOB (not used)
            buf.write_uint16be(0)
        if self.source_lob_impl is not None:
            buf.write_bytes(self.source_lob_impl._locator)
        if self.operation == TNS_LOB_OP_CREATE_TEMP:
            if self.source_lob_impl.dbtype._csfrm == CS_FORM_NCHAR:
                buf._caps._check_ncharset_id()
                buf.write_ub4(TNS_CHARSET_UTF16)
            else:
                buf.write_ub4(TNS_CHARSET_UTF8)
        if self.data is not None:
            buf.write_uint8(TNS_MSG_TYPE_LOB_DATA)
            buf.write_bytes_with_length(self.data)
        if self.send_amount:
            buf.write_ub8(self.amount)      # LOB amount
