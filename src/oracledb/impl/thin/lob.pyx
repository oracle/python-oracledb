#------------------------------------------------------------------------------
# Copyright (c) 2020, 2026, Oracle and/or its affiliates.
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
# lob.pyx
#
# Cython file defining the thin Lob implementation class (embedded in
# thin_impl.pyx).
#------------------------------------------------------------------------------

cdef class ThinLobImpl(BaseLobImpl):

    cdef:
        ThinConnImpl _conn_impl
        bytes _locator
        bint _has_metadata
        uint64_t _size
        uint32_t _chunk_size

    cdef const char* _get_encoding(self):
        """
        Return the encoding used by the LOB. NCLOB always uses UTF-16. CLOB
        uses UTF-16 if the "variable length character set" flag is set, but
        uses UTF-16LE if the "little endian" flag is set (this flag is only for
        those CLOBs that were originally created in Oracle Database 9i). In all
        other cases, the encoding UTF-8 is used.
        """
        if self.dbtype._csfrm == CS_FORM_NCHAR:
            return ENCODING_UTF16
        elif self._locator[TNS_LOB_LOC_OFFSET_FLAG_3] & \
                TNS_LOB_LOC_FLAGS_VAR_LENGTH_CHARSET:
            if self._locator[TNS_LOB_LOC_OFFSET_FLAG_4] & \
                    TNS_LOB_LOC_FLAGS_LITTLE_ENDIAN:
                return ENCODING_UTF16LE
            return ENCODING_UTF16
        return ENCODING_UTF8

    def close(self):
        """
        Internal method for closing a LOB that was opened earlier.
        """
        cdef LobOpMessage message
        message = self._conn_impl._create_message(LobOpMessage, "lob_close")
        if self.dbtype._ora_type_num == ORA_TYPE_NUM_BFILE:
            message.operation = TNS_LOB_OP_FILE_CLOSE
        else:
            message.operation = TNS_LOB_OP_CLOSE
        message.source_lob_impl = self
        yield message

    def create_temp(self):
        """
        Internal method for creating a temporary LOB.
        """
        cdef LobOpMessage message
        self._locator = bytes(40)
        message = self._conn_impl._create_message(
            LobOpMessage, "create_temp_lob"
        )
        message.operation = TNS_LOB_OP_CREATE_TEMP
        message.dest_length = TNS_DURATION_SESSION
        message.source_lob_impl = self
        message.source_offset = self.dbtype._csfrm
        message.dest_offset = self.dbtype._ora_type_num
        yield message

    def file_exists(self):
        """
        Internal method for returning whether the file referenced by a BFILE
        exists.
        """
        cdef LobOpMessage message
        message = self._conn_impl._create_message(
            LobOpMessage, "lob_file_exists"
        )
        message.operation = TNS_LOB_OP_FILE_EXISTS
        message.source_lob_impl = self
        yield message
        return message.bool_flag

    def free_lob(self):
        """
        Internal method for closing a temp LOB during the next piggyback.
        """
        cdef:
            uint8_t flags1 = self._locator[TNS_LOB_LOC_OFFSET_FLAG_1]
            uint8_t flags4 = self._locator[TNS_LOB_LOC_OFFSET_FLAG_4]
        if flags1 & TNS_LOB_LOC_FLAGS_ABSTRACT \
                or flags4 & TNS_LOB_LOC_FLAGS_TEMP:
            if self._conn_impl._temp_lobs_to_close is None:
                self._conn_impl._temp_lobs_to_close = []
            self._conn_impl._temp_lobs_to_close.append(self._locator)
            self._conn_impl._temp_lobs_total_size += len(self._locator)
            self._conn_impl = None

    def get_chunk_size(self):
        """
        Internal method for returning the chunk size of the LOB.
        """
        cdef LobOpMessage message
        if self._has_metadata:
            return self._chunk_size
        message = self._conn_impl._create_message(
            LobOpMessage, "get_lob_chunk_size"
        )
        message.operation = TNS_LOB_OP_GET_CHUNK_SIZE
        message.source_lob_impl = self
        message.send_amount = True
        yield message
        return message.amount

    def get_file_name(self):
        """
        Internal method for returning a 2-tuple constaining the directory.
        """
        cdef:
            const char_type *ptr = self._locator
            uint16_t dir_name_offset, file_name_offset
            uint16_t dir_name_len, file_name_len
        dir_name_offset = TNS_LOB_LOC_FIXED_OFFSET + 2
        dir_name_len = decode_uint16be(&ptr[TNS_LOB_LOC_FIXED_OFFSET])
        file_name_offset = dir_name_offset + dir_name_len + 2
        file_name_len = decode_uint16be(&ptr[dir_name_offset + dir_name_len])
        return (
            ptr[dir_name_offset:dir_name_offset + dir_name_len].decode(),
            ptr[file_name_offset:file_name_offset + file_name_len].decode()
        )

    def get_is_open(self):
        """
        Internal method for returning whether the LOB is open or not.
        """
        cdef LobOpMessage message
        message = self._conn_impl._create_message(
            LobOpMessage, "get_lob_is_open"
        )
        if self.dbtype._ora_type_num == ORA_TYPE_NUM_BFILE:
            message.operation = TNS_LOB_OP_FILE_ISOPEN
        else:
            message.operation = TNS_LOB_OP_IS_OPEN
        message.source_lob_impl = self
        yield message
        return message.bool_flag

    def get_max_amount(self):
        """
        Internal method for returning the maximum amount that can be read.
        """
        return 2**32 - 1

    def get_size(self):
        """
        Internal method for returning the size of a LOB.
        """
        cdef LobOpMessage message
        if self._has_metadata:
            return self._size
        message = self._conn_impl._create_message(LobOpMessage, "get_lob_size")
        message.operation = TNS_LOB_OP_GET_LENGTH
        message.source_lob_impl = self
        message.send_amount = True
        yield message
        return message.amount

    def open(self):
        """
        Internal method for opening a LOB.
        """
        cdef LobOpMessage message
        message = self._conn_impl._create_message(LobOpMessage, "lob_open")
        if self.dbtype._ora_type_num == ORA_TYPE_NUM_BFILE:
            message.operation = TNS_LOB_OP_FILE_OPEN
            message.amount = TNS_LOB_OPEN_READ_ONLY
        else:
            message.operation = TNS_LOB_OP_OPEN
            message.amount = TNS_LOB_OPEN_READ_WRITE
        message.source_lob_impl = self
        message.send_amount = True
        yield message

    async def process_async_operation(self, object method_owner, str name,
                                      object args, object kwargs):
        """
        Processes a database operation asynchronously.
        """
        return await self._conn_impl.process_async_operation(
            method_owner, name, args, kwargs
        )

    def process_sync_operation(self,
                               object method_owner, str name, object args,
                               object kwargs):
        """
        Processes a database operation synchronously.
        """
        return self._conn_impl.process_sync_operation(
            method_owner, name, args, kwargs
        )

    def read(self, uint64_t offset, uint64_t amount):
        """
        Internal method for reading a portion (or all) of the data in the LOB.
        """
        cdef:
            bint was_open = True
            LobOpMessage message
        if self.dbtype._ora_type_num == ORA_TYPE_NUM_BFILE:
            was_open = yield from self.get_is_open()
            if not was_open:
                yield from self.open()
        message = self._conn_impl._create_message(LobOpMessage, "lob_read")
        message.operation = TNS_LOB_OP_READ
        message.source_lob_impl = self
        message.source_offset = offset
        message.amount = amount
        message.send_amount = True
        yield message
        if not was_open:
            yield from self.close()
        if message.data is None:
            if self.dbtype._ora_type_num in (ORA_TYPE_NUM_BLOB,
                                             ORA_TYPE_NUM_BFILE):
                return b""
            return ""
        return message.data

    def set_file_name(self, str dir_alias, str name):
        """
        Internal method for setting the directory alias and file name
        associated with a BFILE LOB.
        """
        cdef char_type dir_length[2]
        cdef char_type name_length[2]
        encode_uint16be(dir_length, len(dir_alias))
        encode_uint16be(name_length, len(name))
        self._locator = self._locator[:TNS_LOB_LOC_FIXED_OFFSET] + \
                dir_length[:2] + dir_alias.encode() + name_length[:2] + \
                name.encode()

    def trim(self, uint64_t new_size):
        """
        Internal method for trimming the data in the LOB to the new size.
        """
        cdef LobOpMessage message
        message = self._conn_impl._create_message(LobOpMessage, "lob_trim")
        message.operation = TNS_LOB_OP_TRIM
        message.source_lob_impl = self
        message.amount = new_size
        message.send_amount = True
        yield message
        self._has_metadata = False

    def write(self, object value, uint64_t offset):
        """
        Write data to the LOB object.
        """
        cdef LobOpMessage message
        message = self._conn_impl._create_message(LobOpMessage, "lob_write")
        message.operation = TNS_LOB_OP_WRITE
        message.source_lob_impl = self
        message.source_offset = offset
        if self.dbtype._ora_type_num == ORA_TYPE_NUM_BLOB:
            if not isinstance(value, bytes):
                raise TypeError("only bytes can be written to BLOBs")
            message.data = value
        else:
            if not isinstance(value, str):
                raise TypeError(
                    "only strings can be written to CLOBs and NCLOBS"
                )
            message.data = (<str> value).encode(self._get_encoding())
        yield message
        self._has_metadata = False
