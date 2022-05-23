#------------------------------------------------------------------------------
# Copyright (c) 2020, 2022, Oracle and/or its affiliates.
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

    @staticmethod
    cdef ThinLobImpl _create(ThinConnImpl conn_impl, DbType dbtype,
                             bytes locator=None):
        cdef:
            ThinLobImpl lob_impl = ThinLobImpl.__new__(ThinLobImpl)
            LobOpMessage message
        lob_impl._conn_impl = conn_impl
        lob_impl.dbtype = dbtype
        if locator is not None:
            lob_impl._locator = locator
        else:
            lob_impl._locator = bytes(40)
            message = conn_impl._create_message(LobOpMessage)
            message.operation = TNS_LOB_OP_CREATE_TEMP
            message.amount = TNS_DURATION_SESSION
            message.send_amount = True
            message.source_lob_impl = lob_impl
            message.source_offset = dbtype._csfrm
            message.dest_offset = dbtype._ora_type_num
            conn_impl._protocol._process_single_message(message)
        return lob_impl

    cdef str _get_encoding(self):
        if self.dbtype._csfrm == TNS_CS_NCHAR \
                or self._locator[TNS_LOB_LOCATOR_OFFSET_FLAG_3] & \
                TNS_LOB_LOCATOR_VAR_LENGTH_CHARSET:
            return TNS_ENCODING_UTF16
        return TNS_ENCODING_UTF8

    def close(self):
        """
        Internal method for closing a LOB that was opened earlier.
        """
        cdef LobOpMessage message
        message = self._conn_impl._create_message(LobOpMessage)
        message.operation = TNS_LOB_OP_CLOSE
        message.source_lob_impl = self
        self._conn_impl._protocol._process_single_message(message)

    def free_lob(self):
        """
        Internal method for closing a temp LOB during the next piggyback.
        """
        if self._locator[TNS_LOB_ABSTRACT_POS] & TNS_LOB_ABSTRACT_VALUE \
                or self._locator[TNS_LOB_TEMP_POS] & TNS_LOB_TEMP_VALUE:
            if self._conn_impl._temp_lobs_to_close is None:
                self._conn_impl._temp_lobs_to_close = []
            self._conn_impl._temp_lobs_to_close.append(self._locator)
            self._conn_impl._temp_lobs_total_size += len(self._locator)
            self._conn_impl = None

    def get_is_open(self):
        """
        Internal method for returning whether the LOB is open or not.
        """
        cdef LobOpMessage message
        message = self._conn_impl._create_message(LobOpMessage)
        message.operation = TNS_LOB_OP_IS_OPEN
        message.source_lob_impl = self
        self._conn_impl._protocol._process_single_message(message)
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
        message = self._conn_impl._create_message(LobOpMessage)
        message.operation = TNS_LOB_OP_GET_LENGTH
        message.source_lob_impl = self
        message.send_amount = True
        self._conn_impl._protocol._process_single_message(message)
        return message.amount

    def open(self):
        """
        Internal method for opening a LOB.
        """
        cdef LobOpMessage message
        message = self._conn_impl._create_message(LobOpMessage)
        message.operation = TNS_LOB_OP_OPEN
        message.source_lob_impl = self
        message.amount = TNS_LOB_OPEN_READ_WRITE
        message.send_amount = True
        self._conn_impl._protocol._process_single_message(message)

    def read(self, uint64_t offset, uint64_t amount):
        """
        Internal method for reading a portion (or all) of the data in the LOB.
        """
        cdef LobOpMessage message
        message = self._conn_impl._create_message(LobOpMessage)
        message.operation = TNS_LOB_OP_READ
        message.source_lob_impl = self
        message.source_offset = offset
        message.amount = amount
        message.send_amount = True
        self._conn_impl._protocol._process_single_message(message)
        if message.data is None:
            if self.dbtype._ora_type_num == TNS_DATA_TYPE_BLOB:
                return b""
            return ""
        return message.data

    def trim(self, uint64_t new_size):
        """
        Internal method for trimming the data in the LOB to the new size
        """
        cdef LobOpMessage message
        message = self._conn_impl._create_message(LobOpMessage)
        message.operation = TNS_LOB_OP_TRIM
        message.source_lob_impl = self
        message.amount = new_size
        message.send_amount = True
        self._conn_impl._protocol._process_single_message(message)

    def write(self, object value, uint64_t offset):
        """
        Internal method for writing data to the LOB object.
        """
        cdef LobOpMessage message
        message = self._conn_impl._create_message(LobOpMessage)
        message.operation = TNS_LOB_OP_WRITE
        message.source_lob_impl = self
        message.source_offset = offset
        if self.dbtype._ora_type_num == TNS_DATA_TYPE_BLOB:
            message.data = value
        else:
            message.data = value.encode(self._get_encoding())
        self._conn_impl._protocol._process_single_message(message)
