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
# direct_path_load_stream.pyx
#
# Cython file defining the messages that are sent to the database and the
# responses that are received by the client for sending direct path data to the
# database (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

@cython.final
cdef class DirectPathPiece:
    cdef:
        bint is_fast
        bint is_first
        bint is_last
        bint is_split_with_prev
        bint is_split_with_next
        uint8_t flags
        uint8_t num_segments
        ssize_t length
        bytes data

    cdef int finalize(self, PieceBuffer buf) except -1:
        """
        Finalizes the piece in preparation for writing to the message.
        """
        self.length = buf._pos
        self.data = buf._data[:buf._pos]
        buf._pos = 0
        if self.is_first:
            self.flags |= TNS_DPLS_ROW_HEADER_FIRST
        elif self.is_split_with_prev:
            self.flags |= TNS_DPLS_ROW_HEADER_SPLIT_WITH_PREV
        if self.is_last:
            self.flags |= TNS_DPLS_ROW_HEADER_LAST
        elif self.is_split_with_next:
            self.flags |= TNS_DPLS_ROW_HEADER_SPLIT_WITH_NEXT
        if self.is_fast_row():
            self.flags |= TNS_DPLS_ROW_HEADER_FAST_ROW
            self.flags |= TNS_DPLS_ROW_HEADER_FAST_PIECE

    cdef uint8_t header_length(self):
        """
        Returns the length of the piece header.
        """
        cdef uint8_t length = 2
        if self.is_fast_row():
            length += 2
        return length

    cdef bint is_fast_row(self):
        """
        Returns true if the piece contains all of the data for a row and all of
        the segments are fast segments.
        """
        return self.is_first and self.is_last and self.is_fast

    cdef int write_to_message(self, WriteBuffer buf) except -1:
        """
        Writes the piece to the message.
        """
        buf.write_uint8(self.flags)
        if self.is_fast_row():
            buf.write_uint16be(self.length + self.header_length())
        buf.write_uint8(self.num_segments)
        buf.write_raw(self.data, self.length)


@cython.final
cdef class PieceBuffer(Buffer):
    cdef:
        DirectPathPiece current_piece
        uint32_t total_piece_length
        list pieces

    cdef int _finalize_piece(self) except -1:
        """
        Finalizes the piece by adding the data in the buffer and calculating
        the piece length, then resetting the buffer.
        """
        cdef uint64_t new_length
        self.current_piece.finalize(self)
        self.pieces.append(self.current_piece)
        new_length = (<uint64_t> self.total_piece_length) + \
                self.current_piece.length + self.current_piece.header_length()
        if new_length > TNS_DPLS_MAX_MESSAGE_SIZE:
            errors._raise_err(errors.ERR_DPL_TOO_MUCH_DATA)
        self.total_piece_length = <uint32_t> new_length

    cdef int _write_more_data(self, ssize_t num_bytes_available,
                              ssize_t num_bytes_wanted) except -1:
        """
        Called when the amount of buffer available is less than the amount of
        data requested. This finalizes the current piece and creates a new one
        to write to.
        """
        self._finalize_piece()
        self.current_piece = DirectPathPiece.__new__(DirectPathPiece)

    cdef int _write_raw_bytes_and_length(self, const char_type *ptr,
                                         ssize_t num_bytes) except -1:
        """
        Helper function that writes the length in the format required before
        writing the bytes. It also splits the pieces as needed.
        """
        cdef:
            ssize_t bytes_left = self._max_size - self._pos
            ssize_t bytes_to_write
        if num_bytes <= TNS_DPLS_MAX_SHORT_LENGTH:
            if num_bytes + 1 > bytes_left:
                self._finalize_piece()
                self.current_piece = DirectPathPiece.__new__(DirectPathPiece)
            self.write_uint8(<uint8_t> num_bytes)
            self.write_raw(ptr, num_bytes)
            self.current_piece.num_segments += 1
        else:
            while num_bytes + 3 > bytes_left:
                bytes_to_write = bytes_left - 3
                self.write_uint8(TNS_LONG_LENGTH_INDICATOR)
                self.write_uint16be(bytes_to_write)
                self.write_raw(ptr, bytes_to_write)
                num_bytes -= bytes_to_write
                bytes_left = self._max_size
                ptr += bytes_to_write
                self.current_piece.is_split_with_next = True
                self.current_piece.num_segments += 1
                self._finalize_piece()
                self.current_piece = DirectPathPiece.__new__(DirectPathPiece)
                self.current_piece.is_split_with_prev = num_bytes > 0
            if num_bytes > 0:
                self.current_piece.num_segments += 1
                self.write_uint8(TNS_LONG_LENGTH_INDICATOR)
                self.write_uint16be(<uint16_t> num_bytes)
                self.write_raw(ptr, num_bytes)

    cdef int add_column_value(
        self,
        BaseConnImpl conn_impl,
        OracleMetadata metadata,
        OracleData *data,
        object value,
        uint64_t row_num
    ):
        """
        Adds column data to the piece (or pieces, if the column value cannot
        fit inside the current piece).
        """
        cdef uint8_t ora_type_num

        # check that the number of segments hasn't already reached the maximum
        # allowable; if it has finalize the current piece and create a new one
        if self.current_piece.num_segments == 255:
            self._finalize_piece()
            self.current_piece = DirectPathPiece.__new__(DirectPathPiece)

        # clear the is_fast flag if the current data type is not one of the
        # fast types
        if not metadata.dbtype._is_fast:
            self.current_piece.is_fast = False

        # write data to the buffer; retain current buffer length in case buffer
        # needs to be split across pieces
        ora_type_num = metadata.dbtype._ora_type_num
        if data.is_null:
            if not metadata.nulls_allowed:
                errors._raise_err(errors.ERR_NULLS_NOT_ALLOWED,
                                  column_name=metadata.name, row_num=row_num)
            self.write_uint8(TNS_NULL_LENGTH_INDICATOR)
            self.current_piece.num_segments += 1
        elif ora_type_num in (ORA_TYPE_NUM_VARCHAR,
                              ORA_TYPE_NUM_CHAR,
                              ORA_TYPE_NUM_LONG,
                              ORA_TYPE_NUM_RAW,
                              ORA_TYPE_NUM_LONG_RAW):
            if metadata.max_size > 0 \
                    and data.buffer.as_raw_bytes.num_bytes > metadata.max_size:
                errors._raise_err(
                    errors.ERR_VALUE_TOO_LARGE,
                    max_size=metadata.max_size,
                    actual_size=data.buffer.as_raw_bytes.num_bytes,
                    row_num=row_num,
                    column_name=metadata.name
                )
            self._write_raw_bytes_and_length(
                data.buffer.as_raw_bytes.ptr,
                data.buffer.as_raw_bytes.num_bytes
            )
        elif ora_type_num == ORA_TYPE_NUM_NUMBER:
            self.write_oracle_number(value)
        elif ora_type_num == ORA_TYPE_NUM_BINARY_DOUBLE:
            self.write_binary_double(data.buffer.as_double)
        elif ora_type_num == ORA_TYPE_NUM_BINARY_FLOAT:
            self.write_binary_float(data.buffer.as_float)
        elif ora_type_num in (ORA_TYPE_NUM_DATE,
                              ORA_TYPE_NUM_TIMESTAMP,
                              ORA_TYPE_NUM_TIMESTAMP_TZ,
                              ORA_TYPE_NUM_TIMESTAMP_LTZ):
            self.write_oracle_date(value, metadata.dbtype._buffer_size_factor)
        elif ora_type_num == ORA_TYPE_NUM_INTERVAL_DS:
            self.write_interval_ds(value)
        elif ora_type_num == ORA_TYPE_NUM_INTERVAL_YM:
            self.write_interval_ym(value)
        elif ora_type_num == ORA_TYPE_NUM_BOOLEAN:
            self.write_bool(data.buffer.as_bool)
        elif ora_type_num == ORA_TYPE_NUM_JSON:
            self.write_oson(value, conn_impl._oson_max_fname_size)
        elif ora_type_num == ORA_TYPE_NUM_VECTOR:
            self.write_vector(value)
        else:
            errors._raise_err(errors.ERR_DB_TYPE_NOT_SUPPORTED,
                              name=metadata.dbtype.name)

    cdef int finish_row(self) except -1:
        """
        Called when the row is finished. The current piece is finalized.
        """
        self.current_piece.is_last = True
        self._finalize_piece()
        self.current_piece = None

    cdef int initialize(self) except -1:
        """
        Initializes the piece buffer to the maximum size allowed. A list of
        pieces is maintained and populated as data is written to the buffer.
        """
        self._initialize(TNS_DPLS_MAX_PIECE_SIZE)
        self.pieces = []

    cdef int start_row(self) except -1:
        """
        Called when a row is being started. A new piece is created.
        """
        self.current_piece = DirectPathPiece.__new__(DirectPathPiece)
        self.current_piece.is_first = True
        self.current_piece.is_fast = True


@cython.final
cdef class DirectPathLoadStreamMessage(Message):
    cdef:
        uint64_t current_row_num
        uint32_t total_piece_length
        uint16_t cursor_id
        list row_pieces

    cdef int _calculate_pieces(
        self,
        BatchLoadManager manager,
        list column_metadata
    ) except -1:
        """
        Calculates the list of pieces that will be sent to the server. Due to
        the nature of the protocol, this must be calculated in advance.
        """
        cdef:
            object row = None, col = None
            ArrowArrayImpl array_impl
            uint64_t overall_row_num
            OracleMetadata metadata
            list all_rows, arrays
            uint32_t row_num
            PieceBuffer buf
            OracleData data
            ssize_t col_num

        # create buffer used for writing column data
        buf = PieceBuffer.__new__(PieceBuffer)
        buf.initialize()

        # acquire information from the manager
        all_rows = manager._get_all_rows()
        arrays = manager._get_arrow_arrays()

        # calculate pieces
        for row_num in range(manager.num_rows):
            overall_row_num = manager.offset + row_num
            if all_rows is not None:
                row = all_rows[overall_row_num]
            self.current_row_num += 1
            buf.start_row()
            for col_num, metadata in enumerate(column_metadata):
                if all_rows is not None:
                    col = self.conn_impl._check_value(metadata, row[col_num],
                                                      NULL)
                    col = convert_python_to_oracle_data(metadata, &data, col)
                else:
                    array_impl = arrays[col_num]
                    col = convert_arrow_to_oracle_data(
                        metadata, &data, array_impl, <int64_t> overall_row_num
                    )
                buf.add_column_value(self.conn_impl, metadata, &data, col,
                                     self.current_row_num)
            buf.finish_row()

        # retain pieces for writing to message
        self.total_piece_length = buf.total_piece_length
        self.row_pieces = buf.pieces

    cdef int _initialize_hook(self) except -1:
        """
        Perform initialization.
        """
        self.function_code = TNS_FUNC_DIRECT_PATH_LOAD_STREAM

    cdef int _process_return_parameters(self, ReadBuffer buf) except -1:
        """
        Process the return parameters sent by the database.
        """
        cdef uint16_t num_out_values, i
        buf.read_ub2(&num_out_values)
        for i in range(num_out_values):
            buf.skip_ub4()

    cdef int _write_message(self, WriteBuffer buf) except -1:
        """
        Writes the message to the database.
        """
        cdef DirectPathPiece piece

        # write header and initial data
        self._write_function_code(buf)
        buf.write_ub2(self.cursor_id)
        buf.write_uint8(1)                  # pointer (buffer)
        buf.write_ub4(self.total_piece_length)
        buf.write_ub4(TNS_DP_STREAM_VERSION)
        buf.write_uint8(0)                  # pointer (input values)
        buf.write_ub4(0)                    # number of input values
        buf.write_uint8(1)                  # pointer (output values)
        buf.write_uint8(1)                  # pointer (output values length)

        # write all pieces
        for piece in self.row_pieces:
            piece.write_to_message(buf)

    cdef int prepare(self,
        uint16_t cursor_id,
        BatchLoadManager manager,
        list column_metadata
    ):
        """
        Prepares the values for writing to the message.
        """
        self.cursor_id = cursor_id
        self._calculate_pieces(manager, column_metadata)
