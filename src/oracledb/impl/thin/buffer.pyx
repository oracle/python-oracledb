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
# buffer.pyx
#
# Cython file defining the low-level network buffer read and write classes and
# methods for reading and writing low-level data from those buffers (embedded
# in thin_impl.pyx).
#------------------------------------------------------------------------------

DEF PACKET_HEADER_SIZE = 8
DEF NUMBER_AS_TEXT_CHARS = 172
DEF NUMBER_MAX_DIGITS = 40
DEF BUFFER_CHUNK_SIZE = 65536
DEF CHUNKED_BYTES_CHUNK_SIZE = 65536

DEF BYTE_ORDER_LSB = 1
DEF BYTE_ORDER_MSB = 2

cdef int MACHINE_BYTE_ORDER = BYTE_ORDER_MSB \
        if sys.byteorder == "big" else BYTE_ORDER_LSB

cdef struct BytesChunk:
    char_type *ptr
    uint32_t length
    uint32_t allocated_length

cdef struct Rowid:
    uint32_t rba
    uint16_t partition_id
    uint32_t block_num
    uint16_t slot_num


cdef inline uint16_t bswap16(uint16_t value):
    """
    Swap the order of bytes for a 16-bit integer.
    """
    return ((value << 8) & 0xff00) | ((value >> 8) & 0x00ff)


cdef inline uint32_t bswap32(uint32_t value):
    """
    Swap the order of bytes for a 32-bit integer.
    """
    return (
            ((value << 24) & (<uint32_t> 0xff000000)) |
            ((value << 8) & 0x00ff0000) |
            ((value >> 8) & 0x0000ff00) |
            ((value >> 24) & 0x000000ff)
    )


cdef inline uint64_t bswap64(uint64_t value):
    """
    Swap the order of bytes for a 64-bit integer.
    """
    return (
        ((value << 56) & (<uint64_t> 0xff00000000000000ULL)) |
        ((value << 40) & 0x00ff000000000000ULL) |
        ((value << 24) & 0x0000ff0000000000ULL) |
        ((value << 8) & 0x000000ff00000000ULL) |
        ((value >> 8) & 0x00000000ff000000ULL) |
        ((value >> 24) & 0x0000000000ff0000ULL) |
        ((value >> 40) & 0x000000000000ff00ULL) |
        ((value >> 56) & 0x00000000000000ffULL)
    )


cdef inline void pack_uint16(char_type *buf, uint16_t x, int order):
    """
    Pack a 16-bit integer into the buffer using the specified type order.
    """
    if order != MACHINE_BYTE_ORDER:
        x = bswap16(x)
    memcpy(buf, &x, sizeof(x))


cdef inline void pack_uint32(char_type *buf, uint32_t x, int order):
    """
    Pack a 32-bit integer into the buffer using the specified type order.
    """
    if order != MACHINE_BYTE_ORDER:
        x = bswap32(x)
    memcpy(buf, &x, sizeof(x))


cdef inline void pack_uint64(char_type *buf, uint64_t x, int order):
    """
    Pack a 64-bit integer into the buffer using the specified type order.
    """
    if order != MACHINE_BYTE_ORDER:
        x = bswap64(x)
    memcpy(buf, &x, sizeof(x))


cdef inline uint16_t unpack_uint16(const char_type *buf, int order):
    """
    Unpacks a 16-bit integer from the buffer using the specified byte order.
    """
    cdef uint16_t raw_value
    memcpy(&raw_value, buf, sizeof(raw_value))
    return raw_value if order == MACHINE_BYTE_ORDER else bswap16(raw_value)


cdef inline uint32_t unpack_uint32(const char_type *buf, int order):
    """
    Unpacks a 32-bit integer from the buffer using the specified byte order.
    """
    cdef uint32_t raw_value
    memcpy(&raw_value, buf, sizeof(raw_value))
    return raw_value if order == MACHINE_BYTE_ORDER else bswap32(raw_value)


@cython.final
cdef class ChunkedBytesBuffer:

    cdef:
        uint32_t _num_chunks
        uint32_t _allocated_chunks
        BytesChunk *_chunks

    def __dealloc__(self):
        cdef uint32_t i
        for i in range(self._allocated_chunks):
            if self._chunks[i].ptr is not NULL:
                cpython.PyMem_Free(self._chunks[i].ptr)
                self._chunks[i].ptr = NULL
        if self._chunks is not NULL:
            cpython.PyMem_Free(self._chunks)
            self._chunks = NULL

    cdef int _allocate_chunks(self) except -1:
        """
        Allocates a new set of chunks and copies data from the original set of
        chunks if needed.
        """
        cdef:
            BytesChunk *chunks
            uint32_t allocated_chunks
        allocated_chunks = self._allocated_chunks + 8
        chunks = <BytesChunk*> \
                cpython.PyMem_Malloc(sizeof(BytesChunk) * allocated_chunks)
        memset(chunks, 0, sizeof(BytesChunk) * allocated_chunks)
        if self._num_chunks > 0:
            memcpy(chunks, self._chunks, sizeof(BytesChunk) * self._num_chunks)
            cpython.PyMem_Free(self._chunks)
        self._chunks = chunks
        self._allocated_chunks = allocated_chunks

    cdef BytesChunk* _get_chunk(self, uint32_t num_bytes) except NULL:
        """
        Return the chunk that can be used to write the number of bytes
        requested.
        """
        cdef:
            uint32_t num_allocated_bytes
            BytesChunk *chunk
        if self._num_chunks > 0:
            chunk = &self._chunks[self._num_chunks - 1]
            if chunk.allocated_length >= chunk.length + num_bytes:
                return chunk
        if self._num_chunks >= self._allocated_chunks:
            self._allocate_chunks()
        self._num_chunks += 1
        chunk = &self._chunks[self._num_chunks - 1]
        chunk.length = 0
        if chunk.allocated_length < num_bytes:
            num_allocated_bytes = self._get_chunk_size(num_bytes)
            if chunk.ptr:
                cpython.PyMem_Free(chunk.ptr)
            chunk.ptr = <char_type*> cpython.PyMem_Malloc(num_allocated_bytes)
            chunk.allocated_length = num_allocated_bytes
        return chunk

    cdef inline uint32_t _get_chunk_size(self, uint32_t size):
        """
        Returns the size to allocate aligned on a 64K boundary.
        """
        return (size + CHUNKED_BYTES_CHUNK_SIZE - 1) & \
               ~(CHUNKED_BYTES_CHUNK_SIZE - 1)

    cdef char_type* end_chunked_read(self) except NULL:
        """
        Called when a chunked read has ended. Since a chunked read is never
        started until at least some bytes are being read, it is assumed that at
        least one chunk is in use. If one chunk is in use, those bytes are
        returned directly, but if more than one chunk is in use, the first
        chunk is resized to include all of the bytes in a contiguous section of
        memory first.
        """
        cdef:
            uint32_t i, num_allocated_bytes, total_num_bytes = 0, pos = 0
            char_type *ptr
        if self._num_chunks > 1:
            for i in range(self._num_chunks):
                total_num_bytes += self._chunks[i].length
            num_allocated_bytes = self._get_chunk_size(total_num_bytes)
            ptr = <char_type*> cpython.PyMem_Malloc(num_allocated_bytes)
            for i in range(self._num_chunks):
                memcpy(&ptr[pos], self._chunks[i].ptr, self._chunks[i].length)
                pos += self._chunks[i].length
                cpython.PyMem_Free(self._chunks[i].ptr)
                self._chunks[i].ptr = NULL
                self._chunks[i].allocated_length = 0
                self._chunks[i].length = 0
            self._num_chunks = 1
            self._chunks[0].ptr = ptr
            self._chunks[0].length = total_num_bytes
            self._chunks[0].allocated_length = num_allocated_bytes
        return self._chunks[0].ptr

    cdef char_type* get_chunk_ptr(self, uint32_t size_required) except NULL:
        """
        Called when memory is required for a chunked read.
        """
        cdef:
            BytesChunk *chunk
            char_type *ptr
        chunk = self._get_chunk(size_required)
        ptr = &chunk.ptr[chunk.length]
        chunk.length += size_required
        return ptr

    cdef inline void start_chunked_read(self):
        """
        Called when a chunked read is started and simply indicates that no
        chunks are in use. The memory is retained in order to reduce the
        overhead in freeing and reallocating memory for each chunked read.
        """
        self._num_chunks = 0


@cython.final
cdef class ReadBuffer:

    cdef:
        ssize_t _max_packet_size, _max_size, _size, _offset, _bytes_to_process
        ChunkedBytesBuffer _chunked_bytes_buf
        const char_type _split_data[255]
        ssize_t _packet_start_offset
        const char_type *_data
        bytearray _data_obj
        char_type[:] _data_view
        Capabilities _caps
        object _socket
        bint _session_needs_to_be_closed

    def __cinit__(self, object sock, ssize_t max_packet_size,
                  Capabilities caps):
        self._socket = sock
        self._caps = caps
        self._max_size = max_packet_size * 2
        self._max_packet_size = max_packet_size
        self._data_obj = bytearray(self._max_size)
        self._data_view = self._data_obj
        self._data = <char_type*> self._data_obj
        self._chunked_bytes_buf = ChunkedBytesBuffer()

    cdef inline int _get_data_from_socket(self, object obj,
                                          ssize_t bytes_requested,
                                          ssize_t *bytes_read) except -1:
        """
        Simple inline function that performs a socket read while verifying that
        the server has not reset the connection. If it has, the dead connection
        error is returned instead.
        """
        try:
            bytes_read[0] = self._socket.recv_into(obj, bytes_requested)
        except ConnectionResetError as e:
            errors._raise_err(errors.ERR_CONNECTION_CLOSED, str(e))

    cdef int _get_int_length_and_sign(self, uint8_t *length,
                                      bint *is_negative,
                                      uint8_t max_length) except -1:
        """
        Returns the length of an integer sent on the wire. A check is also made
        to ensure the integer does not exceed the maximum length. If the
        is_negative pointer is NULL, negative integers will result in an
        exception being raised.
        """
        cdef const char_type *ptr = self._get_raw(1)
        if ptr[0] & 0x80:
            if is_negative == NULL:
                errors._raise_err(errors.ERR_UNEXPECTED_NEGATIVE_INTEGER)
            is_negative[0] = True
            length[0] = ptr[0] & 0x7f
        else:
            if is_negative != NULL:
                is_negative[0] = False
            length[0] = ptr[0]
        if length[0] > max_length:
            errors._raise_err(errors.ERR_INTEGER_TOO_LARGE, length=length[0],
                              max_length=max_length)

    cdef const char_type* _get_raw(self, ssize_t num_bytes,
                                   bint in_chunked_read=False) except NULL:
        """
        Returns a pointer to a buffer containing the requested number of bytes.
        This may be split across multiple packets in which case a chunked bytes
        buffer is used.
        """
        cdef:
            ssize_t num_bytes_left, num_bytes_split, max_split_data
            uint8_t packet_type, packet_flags
            const char_type *source_ptr
            char_type *dest_ptr

        # if no bytes are left in the buffer, a new packet needs to be fetched
        # before anything else can take place
        if self._offset == self._size:
            self.receive_packet(&packet_type, &packet_flags)
            self.skip_raw_bytes(2)          # skip data flags

        # if there is enough room in the buffer to satisfy the number of bytes
        # requested, return a pointer to the current location and advance the
        # offset the required number of bytes
        source_ptr = &self._data[self._offset]
        num_bytes_left = self._size - self._offset
        if num_bytes <= num_bytes_left:
            if in_chunked_read:
                dest_ptr = self._chunked_bytes_buf.get_chunk_ptr(num_bytes)
                memcpy(dest_ptr, source_ptr, num_bytes)
            self._offset += num_bytes
            return source_ptr

        # the requested bytes are split across multiple packets; if a chunked
        # read is in progress, a chunk is acquired that will accommodate the
        # remainder of the bytes in the current packet; otherwise, the split
        # buffer will be used instead (after first checking to see if there is
        # sufficient room available within it)
        if in_chunked_read:
            dest_ptr = self._chunked_bytes_buf.get_chunk_ptr(num_bytes_left)
        else:
            max_split_data = sizeof(self._split_data)
            if max_split_data < num_bytes:
                errors._raise_err(errors.ERR_BUFFER_LENGTH_INSUFFICIENT,
                                  actual_buffer_len=max_split_data,
                                  required_buffer_len=num_bytes)
            dest_ptr = <char_type*> self._split_data
        memcpy(dest_ptr, source_ptr, num_bytes_left)

        # acquire packets until the requested number of bytes is satisfied
        num_bytes -= num_bytes_left
        while num_bytes > 0:

            # acquire new packet
            self.receive_packet(&packet_type, &packet_flags)
            self.skip_raw_bytes(2)          # skip data flags

            # copy data into the chunked buffer or split buffer, as appropriate
            source_ptr = &self._data[self._offset]
            num_bytes_split = min(num_bytes, self._size - self._offset)
            if in_chunked_read:
                dest_ptr = \
                        self._chunked_bytes_buf.get_chunk_ptr(num_bytes_split)
            else:
                dest_ptr = <char_type*> &self._split_data[num_bytes_left]
            memcpy(dest_ptr, source_ptr, num_bytes_split)
            self._offset += num_bytes_split
            num_bytes -= num_bytes_split

        # return the split buffer unconditionally; if performing a chunked read
        # the return value is ignored anyway
        return self._split_data

    cdef int _process_control_packet(self) except -1:
        """
        Process a control packed received in between data packets.
        """
        cdef uint16_t control_type, error_num
        self.read_uint16(&control_type)
        if control_type == TNS_CONTROL_TYPE_RESET_OOB:
            self._caps.supports_oob = False
        elif control_type == TNS_CONTROL_TYPE_INBAND_NOTIFICATION:
            self.skip_raw_bytes(6)           # skip flags
            self.read_uint16(&error_num)
            self.skip_raw_bytes(4)
            if error_num == TNS_ERR_SESSION_SHUTDOWN \
                    or error_num == TNS_ERR_INBAND_MESSAGE:
                self._session_needs_to_be_closed = True
            else:
                errors._raise_err(errors.ERR_UNSUPPORTED_INBAND_NOTIFICATION,
                                  err_num=error_num)

    cdef int _receive_packet_helper(self, uint8_t *packet_type,
                                    uint8_t *packet_flags) except -1:
        """
        Receives a packet and updates the pointers appropriately. Note that
        multiple packets may be received if they are small enough or a portion
        of a second packet may be received so the buffer needs to be adjusted
        as needed. This is also why room is available in the buffer for up to
        two complete packets.
        """
        cdef:
            ssize_t offset, bytes_to_read, bytes_read = 0
            uint32_t packet_size
            uint16_t temp16

        # if no bytes are left over from a previous read, perform a read of the
        # maximum packet size and reset the offset to 0
        if self._bytes_to_process == 0:
            self._packet_start_offset = 0
            self._offset = 0
            self._get_data_from_socket(self._data_obj, self._max_packet_size,
                                       &bytes_read)

        # otherwise, set the offset to the end of the previous packet and
        # ensure that there are at least enough bytes available to cover the
        # contents of the packet header
        else:
            self._packet_start_offset = self._size
            self._offset = self._size
            if self._bytes_to_process < PACKET_HEADER_SIZE:
                offset = self._size + self._bytes_to_process
                bytes_to_read = PACKET_HEADER_SIZE - self._bytes_to_process
                self._get_data_from_socket(self._data_view[offset:],
                                           bytes_to_read, &bytes_read)

        # if no bytes were read this means the server closed the connection
        if self._bytes_to_process < PACKET_HEADER_SIZE:
            if bytes_read == 0:
                if self._socket is not None:
                    try:
                        self._socket.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                    self._socket.close()
                    self._socket = None
                errors._raise_err(errors.ERR_CONNECTION_CLOSED)
            self._bytes_to_process += bytes_read

        # determine the packet length and ensure that all of the bytes for the
        # packet are available; note that as of version 12.2 the packet size is
        # 32 bits in size instead of 16 bits, but this doesn't take effect
        # until it is known that the server is capable of that as well
        if self._caps.protocol_version >= TNS_VERSION_MIN_LARGE_SDU:
            self._size += 4
            self.read_uint32(&packet_size)
        else:
            self._size += 2
            self.read_uint16(&temp16)
            packet_size = temp16
        while self._bytes_to_process < packet_size:
            offset = self._packet_start_offset + self._bytes_to_process
            bytes_to_read = packet_size - self._bytes_to_process
            self._get_data_from_socket(self._data_view[offset:], bytes_to_read,
                                       &bytes_read)
            self._bytes_to_process += bytes_read

        # process remainder of packet header and set size to the new packet
        self._size = self._packet_start_offset + packet_size
        self._bytes_to_process -= packet_size
        if self._caps.protocol_version < TNS_VERSION_MIN_LARGE_SDU:
            self.skip_raw_bytes(2)      # skip packet checksum
        self.read_ub1(packet_type)
        self.read_ub1(packet_flags)
        self.skip_raw_bytes(2)          # header checksum

        # display packet if requested
        if DEBUG_PACKETS:
            offset = self._packet_start_offset
            _print_packet("Receiving packet:", self._socket.fileno(),
                          self._data_view[offset:self._size])

    cdef int _skip_int(self, uint8_t max_length, bint *is_negative) except -1:
        """
        Skips reading an integer of the specified maximum length from the
        buffer.
        """
        cdef uint8_t length
        self._get_int_length_and_sign(&length, is_negative, max_length)
        self.skip_raw_bytes(length)

    cdef uint64_t _unpack_int(self, const char_type *ptr, uint8_t length):
        """
        Unpacks an integer received in the buffer into its native format.
        """
        if length == 1:
            return ptr[0]
        elif length == 2:
            return (ptr[0] << 8) | ptr[1]
        elif length == 3:
            return (ptr[0] << 16) | (ptr[1] << 8) | ptr[2]
        elif length == 4:
            return (ptr[0] << 24) | (ptr[1] << 16) | (ptr[2] << 8) | ptr[3]
        elif length == 5:
            return ((<uint64_t> ptr[0]) << 32) | (ptr[1] << 24) | \
                    (ptr[2] << 16) | (ptr[3] << 8) | ptr[4]
        elif length == 6:
            return ((<uint64_t> ptr[0]) << 40) | \
                   ((<uint64_t> ptr[1]) << 32) | (ptr[2] << 24) | \
                   (ptr[3] << 16) | (ptr[4] << 8) | ptr[5]
        elif length == 7:
            return ((<uint64_t> ptr[0]) << 48) | \
                   ((<uint64_t> ptr[1]) << 40) | \
                   ((<uint64_t> ptr[2]) << 32) | \
                   (ptr[3] << 24) | (ptr[4] << 16) | (ptr[5] << 8) | ptr[6]
        elif length == 8:
            return ((<uint64_t> ptr[0]) << 46) | \
                   ((<uint64_t> ptr[1]) << 48) | \
                   ((<uint64_t> ptr[2]) << 40) | \
                   ((<uint64_t> ptr[3]) << 32) | \
                   (ptr[4] << 24) | (ptr[5] << 16) | (ptr[6] << 8) | ptr[7]

    cdef inline ssize_t bytes_left(self):
        """
        Return the number of bytes remaining in the buffer.
        """
        return self._size - self._offset

    cdef object read_binary_double(self):
        """
        Read a binary double value from the buffer and return the corresponding
        Python object representing that value.
        """
        cdef:
            uint8_t b0, b1, b2, b3, b4, b5, b6, b7, num_bytes
            uint64_t high_bits, low_bits, all_bits
            const uint8_t *ptr
            double *double_ptr
        self.read_ub1(&num_bytes)
        if _is_null_length(num_bytes):
            return None
        ptr = <uint8_t*> self._get_raw(num_bytes)
        b0 = ptr[0]
        b1 = ptr[1]
        b2 = ptr[2]
        b3 = ptr[3]
        b4 = ptr[4]
        b5 = ptr[5]
        b6 = ptr[6]
        b7 = ptr[7]
        if b0 & 0x80:
            b0 = b0 & 0x7f
        else:
            b0 = ~b0
            b1 = ~b1
            b2 = ~b2
            b3 = ~b3
            b4 = ~b4
            b5 = ~b5
            b6 = ~b6
            b7 = ~b7
        high_bits = b0 << 24 | b1 << 16 | b2 << 8 | b3
        low_bits = b4 << 24 | b5 << 16 | b6 << 8 | b7
        all_bits = high_bits << 32 | (low_bits & <uint64_t> 0xffffffff)
        double_ptr = <double*> &all_bits
        return double_ptr[0]

    cdef object read_binary_float(self):
        """
        Read a binary float value from the buffer and return the corresponding
        Python object representing that value.
        """
        cdef:
            uint8_t b0, b1, b2, b3, num_bytes
            const uint8_t *ptr
            uint64_t all_bits
            float *float_ptr
        self.read_ub1(&num_bytes)
        if _is_null_length(num_bytes):
            return None
        ptr = <uint8_t*> self._get_raw(num_bytes)
        b0 = ptr[0]
        b1 = ptr[1]
        b2 = ptr[2]
        b3 = ptr[3]
        if b0 & 0x80:
            b0 = b0 & 0x7f
        else:
            b0 = ~b0
            b1 = ~b1
            b2 = ~b2
            b3 = ~b3
        all_bits = (b0 << 24) | (b1 << 16) | (b2 << 8) | b3
        float_ptr = <float*> &all_bits
        return float_ptr[0]

    cdef object read_bool(self):
        """
        Read a boolean from the buffer and return True, False or None.
        """
        cdef:
            const char_type *ptr
            ssize_t num_bytes
        self.read_raw_bytes_chunked(&ptr, &num_bytes)
        if ptr != NULL:
            return ptr[0] == 1

    cdef object read_bytes(self):
        """
        Read bytes from the buffer and return the corresponding Python object
        representing that value.
        """
        cdef:
            const char_type *ptr
            ssize_t num_bytes
        self.read_raw_bytes_chunked(&ptr, &num_bytes)
        if ptr != NULL:
            return ptr[:num_bytes]

    cdef object read_date(self):
        """
        Read a date from the buffer and return the corresponding Python object
        representing that value.
        """
        cdef:
            int8_t tz_hour = 0, tz_minute = 0
            uint32_t fsecond = 0
            const char_type *ptr
            uint8_t num_bytes
            int32_t seconds
            uint16_t year
        self.read_ub1(&num_bytes)
        if _is_null_length(num_bytes):
            return None
        ptr = self._get_raw(num_bytes)
        year = (<uint8_t> ptr[0] - 100) * 100 + <uint8_t> ptr[1] - 100
        if num_bytes >= 11:
            fsecond = unpack_uint32(&ptr[7], BYTE_ORDER_MSB) // 1000
        value = cydatetime.datetime_new(year, ptr[2], ptr[3], ptr[4] - 1,
                                        ptr[5] - 1, ptr[6] - 1, fsecond, None)
        if num_bytes > 11 and ptr[11] != 0 and ptr[12] != 0:
            tz_hour = ptr[11] - TZ_HOUR_OFFSET
            tz_minute = ptr[12] - TZ_MINUTE_OFFSET
            if tz_hour != 0 or tz_minute != 0:
                seconds = tz_hour * 3600 + tz_minute * 60
                value += cydatetime.timedelta_new(0, seconds, 0)
        return value

    cdef object read_interval_ds(self):
        """
        Read an interval day to second value from the buffer and return the
        corresponding Python object representing that value.
        """
        cdef:
            int32_t days, hours, minutes, seconds, total_seconds, fseconds
            uint8_t duration_offset = TNS_DURATION_OFFSET
            uint32_t duration_mid = TNS_DURATION_MID
            const char_type *ptr
            uint8_t num_bytes
        self.read_ub1(&num_bytes)
        if _is_null_length(num_bytes):
            return None
        ptr = self._get_raw(num_bytes)
        days = unpack_uint32(ptr, BYTE_ORDER_MSB) - duration_mid
        fseconds = unpack_uint32(&ptr[7], BYTE_ORDER_MSB) - duration_mid
        hours = ptr[4] - duration_offset
        minutes = ptr[5] - duration_offset
        seconds = ptr[6] - duration_offset
        total_seconds = hours * 60 * 60 + minutes * 60 + seconds
        return cydatetime.timedelta_new(days, total_seconds, fseconds // 1000)

    cdef object read_lob(self, ThinConnImpl conn_impl, DbType dbtype):
        """
        Read a LOB locator from the buffer and return a LOB object containing
        it.
        """
        cdef:
            ThinLobImpl lob_impl
            uint8_t num_bytes
        self.read_ub1(&num_bytes)
        if _is_null_length(num_bytes):
            return None
        self.skip_ub1()
        lob_impl = ThinLobImpl._create(conn_impl, dbtype, self.read_bytes())
        return LOB._from_impl(lob_impl)

    cdef object read_oracle_number(self, int preferred_num_type):
        """
        Read an Oracle number from the buffer and return the corresponding
        Python object representing that value. The preferred numeric type
        (int, float, decimal.Decimal and str) is used, if possible.
        """
        cdef:
            uint8_t num_digits, byte, digit, num_bytes
            char_type buf[NUMBER_AS_TEXT_CHARS]
            uint8_t digits[NUMBER_MAX_DIGITS]
            bint is_positive, is_integer
            int16_t decimal_point_index
            const char_type *ptr
            int8_t exponent
            str text

        # read the number of bytes in the number; if the value is 0 or the null
        # length indicator, return None
        self.read_ub1(&num_bytes)
        if _is_null_length(num_bytes):
            return None

        # the first byte is the exponent; positive numbers have the highest
        # order bit set, whereas negative numbers have the highest order bit
        # cleared and the bits inverted
        self.read_sb1(&exponent)
        is_positive = (exponent & 0x80)
        if not is_positive:
            exponent = ~exponent
        exponent -= 193
        decimal_point_index = exponent * 2 + 2

        # a mantissa length of 0 implies a value of 0 (if positive) or a value
        # of -1e126 (if negative)
        if num_bytes == 1:
            if is_positive:
                if preferred_num_type == NUM_TYPE_INT:
                    return 0
                elif preferred_num_type == NUM_TYPE_DECIMAL:
                    return decimal.Decimal(0)
                elif preferred_num_type == NUM_TYPE_STR:
                    return "0"
                return 0.0
            if preferred_num_type == NUM_TYPE_INT:
                return -10 ** 126
            elif preferred_num_type == NUM_TYPE_DECIMAL:
                return decimal.Decimal("-1e126")
            elif preferred_num_type == NUM_TYPE_STR:
                return "-1e126"
            return -1.0e126

        # check for the trailing 102 byte for negative numbers and, if present,
        # reduce the number of mantissa digits
        ptr = self._get_raw(num_bytes - 1)
        if not is_positive and ptr[num_bytes - 2] == 102:
            num_bytes -= 1

        # process the mantissa bytes which are the remaining bytes; each
        # mantissa byte is a base-100 digit
        num_digits = 0
        for i in range(num_bytes - 1):

            # positive numbers have 1 added to them; negative numbers are
            # subtracted from the value 101
            byte = ptr[i]
            if is_positive:
                byte -= 1
            else:
                byte = 101 - byte

            # process the first digit; leading zeroes are ignored
            digit = <uint8_t> byte // 10
            if digit == 0 and i == 0:
                decimal_point_index -= 1
            elif digit == 10:
                digits[num_digits] = 1
                digits[num_digits + 1] = 0
                num_digits += 2
                decimal_point_index += 1
            elif digit != 0 or i > 0:
                digits[num_digits] = digit
                num_digits += 1

            # process the second digit; trailing zeroes are ignored
            digit = byte % 10
            if digit != 0 or i < num_bytes - 2:
                digits[num_digits] = digit
                num_digits += 1

        # create string of digits for transformation to Python value
        is_integer = 1
        num_bytes = 0

        # if negative, include the sign
        if not is_positive:
            buf[num_bytes] = 45         # minus sign
            num_bytes += 1

        # if the decimal point index is 0 or less, add the decimal point and
        # any leading zeroes that are needed
        if decimal_point_index <= 0:
            buf[num_bytes] = 48         # zero
            buf[num_bytes + 1] = 46     # decimal point
            num_bytes += 2
            is_integer = 0
            for i in range(decimal_point_index, 0):
                buf[num_bytes] = 48     # zero
                num_bytes += 1

        # add each of the digits
        for i in range(num_digits):
            if i > 0 and i == decimal_point_index:
                buf[num_bytes] = 46     # decimal point
                is_integer = 0
                num_bytes += 1
            buf[num_bytes] = 48 + digits[i]
            num_bytes += 1

        # if the decimal point index exceeds the number of digits, add any
        # trailing zeroes that are needed
        if decimal_point_index > num_digits:
            for i in range(num_digits, decimal_point_index):
                buf[num_bytes] = 48     # zero
                num_bytes += 1

        # convert result to an integer or a decimal number
        if preferred_num_type == NUM_TYPE_INT and is_integer:
            return int(buf[:num_bytes])
        elif preferred_num_type == NUM_TYPE_DECIMAL:
            return decimal.Decimal(buf[:num_bytes].decode())
        elif preferred_num_type == NUM_TYPE_STR:
            return buf[:num_bytes].decode()
        return float(buf[:num_bytes])

    cdef inline const char_type* read_raw_bytes(self,
                                                ssize_t num_bytes) except NULL:
        """
        Returns a pointer to a contiguous buffer containing the specified
        number of bytes found in the buffer.
        """
        return self._get_raw(num_bytes)

    cdef int read_raw_bytes_chunked(self, const char_type **ptr,
                                    ssize_t *num_bytes) except -1:
        """
        Reads bytes from the buffer into a contiguous buffer. The first byte
        read is the number of bytes to read, unless it is
        TNS_LONG_LENGTH_INDICATOR, in which case a chunked read is performed.
        """
        cdef:
            uint32_t temp_num_bytes
            uint8_t length
        self.read_ub1(&length)
        if _is_null_length(length):
            ptr[0] = NULL
            num_bytes[0] = 0
        elif length != TNS_LONG_LENGTH_INDICATOR:
            ptr[0] = self._get_raw(length)
            num_bytes[0] = length
        else:
            self._chunked_bytes_buf.start_chunked_read()
            num_bytes[0] = 0
            while True:
                self.read_ub4(&temp_num_bytes)
                if temp_num_bytes == 0:
                    break
                num_bytes[0] += temp_num_bytes
                self._get_raw(temp_num_bytes, in_chunked_read=True)
            ptr[0] = self._chunked_bytes_buf.end_chunked_read()

    cdef int read_rowid(self, Rowid *rowid) except -1:
        """
        Reads a rowid from the buffer and populates the rowid structure.
        """
        self.read_ub4(&rowid.rba)
        self.read_ub2(&rowid.partition_id)
        self.skip_ub1()
        self.read_ub4(&rowid.block_num)
        self.read_ub2(&rowid.slot_num)

    cdef int read_sb1(self, int8_t *value) except -1:
        """
        Reads a signed 8-bit integer from the buffer.
        """
        cdef const char_type *ptr = self._get_raw(1)
        value[0] = <int8_t> ptr[0]

    cdef int read_sb2(self, int16_t *value) except -1:
        """
        Reads a signed 16-bit integer from the buffer.
        """
        cdef:
            const char_type *ptr
            bint is_negative
            uint8_t length
        self._get_int_length_and_sign(&length, &is_negative, 2)
        if length == 0:
            value[0] = 0
        else:
            ptr = self._get_raw(length)
            value[0] = <int16_t> self._unpack_int(ptr, length)
            if is_negative:
                value[0] = -value[0]

    cdef int read_sb4(self, int32_t *value) except -1:
        """
        Reads a signed 32-bit integer from the buffer.
        """
        cdef:
            const char_type *ptr
            bint is_negative
            uint8_t length
        self._get_int_length_and_sign(&length, &is_negative, 4)
        if length == 0:
            value[0] = 0
        else:
            ptr = self._get_raw(length)
            value[0] = <int32_t> self._unpack_int(ptr, length)
            if is_negative:
                value[0] = -value[0]

    cdef int read_sb8(self, int64_t *value) except -1:
        """
        Reads a signed 64-bit integer from the buffer.
        """
        cdef:
            const char_type *ptr
            bint is_negative
            uint8_t length
        self._get_int_length_and_sign(&length, &is_negative, 8)
        if length == 0:
            value[0] = 0
        else:
            ptr = self._get_raw(length)
            value[0] = self._unpack_int(ptr, length)
            if is_negative:
                value[0] = -value[0]

    cdef object read_str(self, int csfrm):
        """
        Reads a string from the buffer.
        """
        cdef:
            const char_type *ptr
            ssize_t num_bytes
        self.read_raw_bytes_chunked(&ptr, &num_bytes)
        if ptr != NULL:
            if csfrm == TNS_CS_IMPLICIT:
                return ptr[:num_bytes].decode()
            return ptr[:num_bytes].decode(TNS_ENCODING_UTF16)

    cdef int read_ub1(self, uint8_t *value) except -1:
        """
        Reads an unsigned 8-bit integer from the buffer.
        """
        cdef const char_type *ptr = self._get_raw(1)
        value[0] = ptr[0]

    cdef int read_ub2(self, uint16_t *value) except -1:
        """
        Reads an unsigned 16-bit integer from the buffer.
        """
        cdef:
            const char_type *ptr
            uint8_t length
        self._get_int_length_and_sign(&length, NULL, 2)
        if length == 0:
            value[0] = 0
        else:
            ptr = self._get_raw(length)
            value[0] = <uint16_t> self._unpack_int(ptr, length)

    cdef int read_ub4(self, uint32_t *value) except -1:
        """
        Reads an unsigned 32-bit integer from the buffer.
        """
        cdef:
            const char_type *ptr
            uint8_t length
        self._get_int_length_and_sign(&length, NULL, 4)
        if length == 0:
            value[0] = 0
        else:
            ptr = self._get_raw(length)
            value[0] = <uint32_t> self._unpack_int(ptr, length)

    cdef int read_ub8(self, uint64_t *value) except -1:
        """
        Reads an unsigned 64-bit integer from the buffer.
        """
        cdef:
            const char_type *ptr
            uint8_t length
        self._get_int_length_and_sign(&length, NULL, 8)
        if length == 0:
            value[0] = 0
        else:
            ptr = self._get_raw(length)
            value[0] = self._unpack_int(ptr, length)

    cdef int read_uint16(self, uint16_t *value,
                         int byte_order=BYTE_ORDER_MSB) except -1:
        """
        Read a 16-bit integer from the buffer in the specified byte order.
        """
        cdef const char_type *ptr = self._get_raw(2)
        value[0] = unpack_uint16(ptr, byte_order)

    cdef int read_uint32(self, uint32_t *value,
                         int byte_order=BYTE_ORDER_MSB) except -1:
        """
        Read a 32-bit integer from the buffer in the specified byte order.
        """
        cdef const char_type *ptr = self._get_raw(4)
        value[0] = unpack_uint32(ptr, byte_order)

    cdef object read_urowid(self):
        """
        Read a universal rowid from the buffer and return the Python object
        representing its value.
        """
        cdef:
            ssize_t output_len, input_len, remainder, pos
            int input_offset = 1, output_offset = 0
            const char_type *input_ptr
            bytearray output_value
            uint32_t num_bytes
            Rowid rowid

        # check for null
        self.read_ub4(&num_bytes)
        if num_bytes == 0:
            return None

        # handle physical rowid
        self.read_raw_bytes_chunked(&input_ptr, &input_len)
        if input_ptr[0] == 1:
            rowid.rba = unpack_uint32(&input_ptr[1], BYTE_ORDER_MSB)
            rowid.partition_id = unpack_uint16(&input_ptr[5], BYTE_ORDER_MSB)
            rowid.block_num = unpack_uint32(&input_ptr[7], BYTE_ORDER_MSB)
            rowid.slot_num = unpack_uint16(&input_ptr[11], BYTE_ORDER_MSB)
            return _encode_rowid(&rowid)

        # handle logical rowid
        output_len = (input_len // 3) * 4
        remainder = input_len % 3
        if remainder == 1:
            output_len += 1
        elif remainder == 2:
            output_len += 3
        output_value = bytearray(output_len)
        input_len -= 1
        output_value[0] = 42            # '*'
        output_offset += 1
        while input_len > 0:

            # produce first byte of quadruple
            pos = input_ptr[input_offset] >> 2
            output_value[output_offset] = TNS_BASE64_ALPHABET_ARRAY[pos]
            output_offset += 1

            # produce second byte of quadruple, but if only one byte is left,
            # produce that one byte and exit
            pos = (input_ptr[input_offset] & 0x3) << 4
            if input_len == 1:
                output_value[output_offset] = TNS_BASE64_ALPHABET_ARRAY[pos]
                break
            input_offset += 1
            pos |= ((input_ptr[input_offset] & 0xf0) >> 4)
            output_value[output_offset] = TNS_BASE64_ALPHABET_ARRAY[pos]
            output_offset += 1

            # produce third byte of quadruple, but if only two bytes are left,
            # produce that one byte and exit
            pos = (input_ptr[input_offset] & 0xf) << 2
            if input_len == 2:
                output_value[output_offset] = TNS_BASE64_ALPHABET_ARRAY[pos]
                break
            input_offset += 1
            pos |= ((input_ptr[input_offset] & 0xc0) >> 6)
            output_value[output_offset] = TNS_BASE64_ALPHABET_ARRAY[pos]
            output_offset += 1

            # produce final byte of quadruple
            pos = input_ptr[input_offset] & 0x3f
            output_value[output_offset] = TNS_BASE64_ALPHABET_ARRAY[pos]
            output_offset += 1
            input_offset += 1
            input_len -= 3

        return bytes(output_value).decode()

    cdef int receive_packet(self, uint8_t *packet_type,
                            uint8_t *packet_flags) except -1:
        """
        Calls _receive_packet_helper() and checks the packet type. If a
        control packet is received, it is processed and the next packet is
        received.
        """
        while True:
            self._receive_packet_helper(packet_type, packet_flags)
            if packet_type[0] == TNS_PACKET_TYPE_CONTROL:
                self._process_control_packet()
                continue
            break

    cdef int skip_raw_bytes(self, ssize_t num_bytes) except -1:
        """
        Skip the specified number of bytes in the buffer. In order to avoid
        copying data, the number of bytes left in the packet is determined and
        only that amount is requested.
        """
        cdef ssize_t num_bytes_this_time
        while num_bytes > 0:
            num_bytes_this_time = min(num_bytes, self.bytes_left())
            self._get_raw(num_bytes_this_time)
            num_bytes -= num_bytes_this_time

    cdef int skip_raw_bytes_chunked(self) except -1:
        """
        Skip a number of bytes that may or may not be chunked in the buffer.
        The first byte gives the length. If the length is
        TNS_LONG_LENGTH_INDICATOR, however, chunks are read and discarded.
        """
        cdef:
            uint32_t temp_num_bytes
            uint8_t length
        self.read_ub1(&length)
        if length != TNS_LONG_LENGTH_INDICATOR:
            self.skip_raw_bytes(length)
        else:
            while True:
                self.read_ub4(&temp_num_bytes)
                if temp_num_bytes == 0:
                    break
                self.skip_raw_bytes(temp_num_bytes)

    cdef inline int skip_sb4(self) except -1:
        """
        Skips a signed 32-bit integer in the buffer.
        """
        cdef bint is_negative
        return self._skip_int(4, &is_negative)

    cdef inline int skip_ub1(self) except -1:
        """
        Skips an unsigned 8-bit integer in the buffer.
        """
        self._get_raw(1)

    cdef inline int skip_ub2(self) except -1:
        """
        Skips an unsigned 16-bit integer in the buffer.
        """
        return self._skip_int(2, NULL)

    cdef inline int skip_ub4(self) except -1:
        """
        Skips an unsigned 32-bit integer in the buffer.
        """
        return self._skip_int(4, NULL)


@cython.final
cdef class WriteBuffer:

    cdef:
        ssize_t _max_size, _actual_size
        uint8_t _packet_type
        bytearray _data_obj
        char_type[:] _data_view
        char_type *_data
        Capabilities _caps
        object _socket
        uint8_t _seq_num
        bint _packet_sent

    def __cinit__(self, object sock, ssize_t max_size, Capabilities caps):
        self._socket = sock
        self._caps = caps
        self._data_obj = bytearray(max_size)
        self._data_view = self._data_obj
        self._data = <char_type*> self._data_obj
        self._max_size = max_size

    cdef int _send_packet(self, bint final_packet) except -1:
        """
        Write the packet header and then send the packet. Once sent, reset the
        pointers back to an empty packet.
        """
        cdef ssize_t size = self._actual_size
        self._actual_size = 0
        if self._caps.protocol_version >= TNS_VERSION_MIN_LARGE_SDU:
            self.write_uint32(size)
        else:
            self.write_uint16(size)
            self.write_uint16(0)
        self.write_uint8(self._packet_type)
        self.write_uint8(0)
        self.write_uint16(0)
        self._actual_size = size
        if DEBUG_PACKETS:
            _print_packet("Sending packet:", self._socket.fileno(),
                          self._data_view[:self._actual_size])
        try:
            self._socket.send(self._data_view[:self._actual_size])
        except OSError as e:
            errors._raise_err(errors.ERR_CONNECTION_CLOSED, str(e))
        self._packet_sent = True
        self._actual_size = PACKET_HEADER_SIZE
        if not final_packet:
            self.write_uint16(0)            # add data flags for next packet

    cdef inline ssize_t bytes_left(self):
        """
        Return the number of bytes that can still be added to the packet before
        it is full and must be sent to the server.
        """
        return self._max_size - self._actual_size

    cdef int end_request(self) except -1:
        """
        Indicates that the request from the client is completing and will send
        any packet remaining, if necessary.
        """
        if self._actual_size > PACKET_HEADER_SIZE:
            self._send_packet(final_packet=True)

    cdef inline ssize_t max_payload_bytes(self):
        """
        Return the maximum number of bytes that can be sent in a packet. This
        is the maximum size of the entire packet, less the bytes in the header
        and 2 bytes for the data flags.
        """
        return self._max_size - PACKET_HEADER_SIZE - 2

    cdef void start_request(self, uint8_t packet_type, uint16_t data_flags=0):
        """
        Indicates that a request from the client is starting. The packet type
        is retained just in case a request spans multiple packets. The packet
        header (8 bytes in length) is written when a packet is actually being
        sent and so is skipped at this point.
        """
        self._packet_sent = False
        self._packet_type = packet_type
        self._actual_size = PACKET_HEADER_SIZE
        if packet_type == TNS_PACKET_TYPE_DATA:
            self.write_uint16(data_flags)

    cdef int write_binary_double(self, double value) except -1:
        cdef:
            uint8_t b0, b1, b2, b3, b4, b5, b6, b7
            uint64_t all_bits
            char_type buf[8]
            uint64_t *ptr
        ptr = <uint64_t*> &value
        all_bits = ptr[0]
        b7 = all_bits & 0xff
        b6 = (all_bits >> 8) & 0xff
        b5 = (all_bits >> 16) & 0xff
        b4 = (all_bits >> 24) & 0xff
        b3 = (all_bits >> 32) & 0xff
        b2 = (all_bits >> 40) & 0xff
        b1 = (all_bits >> 48) & 0xff
        b0 = (all_bits >> 56) & 0xff
        if b0 & 0x80 == 0:
            b0 = b0 | 0x80
        else:
            b0 = ~b0
            b1 = ~b1
            b2 = ~b2
            b3 = ~b3
            b4 = ~b4
            b5 = ~b5
            b6 = ~b6
            b7 = ~b7
        buf[0] = b0
        buf[1] = b1
        buf[2] = b2
        buf[3] = b3
        buf[4] = b4
        buf[5] = b5
        buf[6] = b6
        buf[7] = b7
        self.write_uint8(8)
        self.write_raw(buf, 8)

    cdef int write_binary_float(self, float value) except -1:
        cdef:
            uint8_t b0, b1, b2, b3
            uint32_t all_bits
            char_type buf[4]
            uint32_t *ptr
        ptr = <uint32_t*> &value
        all_bits = ptr[0]
        b3 = all_bits & 0xff
        b2 = (all_bits >> 8) & 0xff
        b1 = (all_bits >> 16) & 0xff
        b0 = (all_bits >> 24) & 0xff
        if b0 & 0x80 == 0:
            b0 = b0 | 0x80
        else:
            b0 = ~b0
            b1 = ~b1
            b2 = ~b2
            b3 = ~b3
        buf[0] = b0
        buf[1] = b1
        buf[2] = b2
        buf[3] = b3
        self.write_uint8(4)
        self.write_raw(buf, 4)

    cdef int write_bytes(self, bytes value) except -1:
        cdef:
            ssize_t value_len
            char_type *ptr
        cpython.PyBytes_AsStringAndSize(value, <char**> &ptr, &value_len)
        self.write_raw(ptr, value_len)

    cdef int write_bytes_chunked(self, bytes value) except -1:
        cdef:
            ssize_t value_len, bytes_left, chunk_len
            char_type *ptr
        cpython.PyBytes_AsStringAndSize(value, <char**> &ptr, &value_len)
        if value_len <= TNS_MAX_SHORT_LENGTH:
            self.write_uint8(<uint8_t> value_len)
            self.write_raw(ptr, value_len)
        else:
            self.write_uint8(TNS_LONG_LENGTH_INDICATOR)
            bytes_left = self.bytes_left()
            while value_len > 0:
                chunk_len = min(value_len, TNS_CHUNK_SIZE)
                self.write_ub4(chunk_len)
                value_len -= chunk_len
                while True:
                    if bytes_left >= chunk_len:
                        self.write_raw(ptr, chunk_len)
                        ptr += chunk_len
                        break
                    self.write_raw(ptr, bytes_left)
                    chunk_len -= bytes_left
                    ptr += bytes_left
                    bytes_left = self.max_payload_bytes()
            self.write_ub4(0)

    cdef int write_interval_ds(self, object value) except -1:
        cdef:
            int32_t days, seconds, fseconds
            char_type buf[11]
        days = cydatetime.timedelta_days(value)
        pack_uint32(buf, days + TNS_DURATION_MID, BYTE_ORDER_MSB)
        seconds = cydatetime.timedelta_seconds(value)
        buf[4] = (seconds // 3600) + TNS_DURATION_OFFSET
        seconds = seconds % 3600
        buf[5] = (seconds // 60) + TNS_DURATION_OFFSET
        buf[6] = (seconds % 60) + TNS_DURATION_OFFSET
        fseconds = cydatetime.timedelta_microseconds(value) * 1000
        pack_uint32(&buf[7], fseconds + TNS_DURATION_MID, BYTE_ORDER_MSB)
        self.write_uint8(sizeof(buf))
        self.write_raw(buf, sizeof(buf))

    cdef int write_oracle_date(self, object value, uint8_t length) except -1:
        cdef:
            unsigned int year
            char_type buf[13]
            uint32_t fsecond
        year = cydatetime.PyDateTime_GET_YEAR(value)
        buf[0] = <uint8_t> ((year // 100) + 100)
        buf[1] = <uint8_t> ((year % 100) + 100)
        buf[2] = <uint8_t> cydatetime.PyDateTime_GET_MONTH(value)
        buf[3] = <uint8_t> cydatetime.PyDateTime_GET_DAY(value)
        buf[4] = <uint8_t> cydatetime.PyDateTime_DATE_GET_HOUR(value) + 1
        buf[5] = <uint8_t> cydatetime.PyDateTime_DATE_GET_MINUTE(value) + 1
        buf[6] = <uint8_t> cydatetime.PyDateTime_DATE_GET_SECOND(value) + 1
        if length > 7:
            fsecond = <uint32_t> \
                    cydatetime.PyDateTime_DATE_GET_MICROSECOND(value) * 1000
            if fsecond == 0:
                length = 7
            else:
                pack_uint32(&buf[7], fsecond, BYTE_ORDER_MSB)
        if length > 11:
            buf[11] = TZ_HOUR_OFFSET
            buf[12] = TZ_MINUTE_OFFSET
        self.write_uint8(length)
        self.write_raw(buf, length)

    cdef int write_oracle_number(self, bytes num_bytes) except -1:
        cdef:
            uint8_t num_digits = 0, digit, num_pairs, pair_num, digits_pos
            bint exponent_is_negative = False, append_sentinel = False
            ssize_t num_bytes_length, exponent_pos, pos = 0
            bint is_negative = False, prepend_zero = False
            uint8_t digits[NUMBER_AS_TEXT_CHARS]
            int16_t decimal_point_index
            int8_t exponent_on_wire
            const char_type *ptr
            int16_t exponent

        # zero length string cannot be converted
        num_bytes_length = len(num_bytes)
        if num_bytes_length == 0:
            errors._raise_err(errors.ERR_NUMBER_STRING_OF_ZERO_LENGTH)
        elif num_bytes_length > NUMBER_AS_TEXT_CHARS:
            errors._raise_err(errors.ERR_NUMBER_STRING_TOO_LONG)

        # check to see if number is negative (first character is '-')
        ptr = num_bytes
        if ptr[0] == b'-':
            is_negative = True
            pos += 1

        # scan for digits until the decimal point or exponent indicator found
        while pos < num_bytes_length:
            if ptr[pos] == b'.' or ptr[pos] == b'e' or ptr[pos] == b'E':
                break
            if ptr[pos] < b'0' or ptr[pos] > b'9':
                errors._raise_err(errors.ERR_INVALID_NUMBER)
            digit = ptr[pos] - <uint8_t> b'0'
            pos += 1
            if digit == 0 and num_digits == 0:
                continue
            digits[num_digits] = digit
            num_digits += 1
        decimal_point_index = num_digits

        # scan for digits following the decimal point, if applicable
        if pos < num_bytes_length and ptr[pos] == b'.':
            pos += 1
            while pos < num_bytes_length:
                if ptr[pos] == b'e' or ptr[pos] == b'E':
                    break
                digit = ptr[pos] - <uint8_t> b'0'
                pos += 1
                if digit == 0 and num_digits == 0:
                    decimal_point_index -= 1
                    continue
                digits[num_digits] = digit
                num_digits += 1

        # handle exponent, if applicable
        if pos < num_bytes_length and (ptr[pos] == b'e' or ptr[pos] == b'E'):
            pos += 1
            if pos < num_bytes_length:
                if ptr[pos] == b'-':
                    exponent_is_negative = True
                    pos += 1
                elif ptr[pos] == b'+':
                    pos += 1
            exponent_pos = pos
            while pos < num_bytes_length:
                if ptr[pos] < b'0' or ptr[pos] > b'9':
                    errors._raise_err(errors.ERR_NUMBER_WITH_INVALID_EXPONENT)
                pos += 1
            if exponent_pos == pos:
                errors._raise_err(errors.ERR_NUMBER_WITH_EMPTY_EXPONENT)
            exponent = <int16_t> int(ptr[exponent_pos:pos])
            if exponent_is_negative:
                exponent = -exponent
            decimal_point_index += exponent

        # if there is anything left in the string, that indicates an invalid
        # number as well
        if pos < num_bytes_length:
            errors._raise_err(errors.ERR_CONTENT_INVALID_AFTER_NUMBER)

        # skip trailing zeros
        while num_digits > 0 and digits[num_digits - 1] == 0:
            num_digits -= 1

        # value must be less than 1e126 and greater than 1e-129; the number of
        # digits also cannot exceed the maximum precision of Oracle numbers
        if num_digits > NUMBER_MAX_DIGITS or decimal_point_index > 126 \
                or decimal_point_index < -129:
            errors._raise_err(errors.ERR_ORACLE_NUMBER_NO_REPR)

        # if the exponent is odd, prepend a zero
        if decimal_point_index % 2 == 1:
            prepend_zero = True
            if num_digits > 0:
                digits[num_digits] = 0
                num_digits += 1
                decimal_point_index += 1

        # determine the number of digit pairs; if the number of digits is odd,
        # append a zero to make the number of digits even
        if num_digits % 2 == 1:
            digits[num_digits] = 0
            num_digits += 1
        num_pairs = num_digits // 2

        # append a sentinel 102 byte for negative numbers if there is room
        if is_negative and num_digits > 0 and num_digits < NUMBER_MAX_DIGITS:
            append_sentinel = True

        # write length of number
        self.write_uint8(num_pairs + 1 + append_sentinel)

        # if the number of digits is zero, the value is itself zero since all
        # leading and trailing zeros are removed from the digits string; this
        # is a special case
        if num_digits == 0:
            self.write_uint8(128)
            return 0

        # write the exponent
        exponent_on_wire = <int8_t> (decimal_point_index / 2) + 192
        if is_negative:
            exponent_on_wire = ~exponent_on_wire
        self.write_uint8(exponent_on_wire)

        # write the mantissa bytes
        digits_pos = 0
        for pair_num in range(num_pairs):
            if pair_num == 0 and prepend_zero:
                digit = digits[digits_pos]
                digits_pos += 1
            else:
                digit = digits[digits_pos] * 10 + digits[digits_pos + 1]
                digits_pos += 2
            if is_negative:
                digit = 101 - digit
            else:
                digit += 1
            self.write_uint8(digit)

        # append 102 byte for negative numbers if the number of digits is less
        # than the maximum allowable
        if append_sentinel:
            self.write_uint8(102)

    cdef int write_raw(self, const char_type *data, ssize_t length) except -1:
        cdef ssize_t bytes_to_write
        while True:
            bytes_to_write = min(self._max_size - self._actual_size, length)
            if bytes_to_write > 0:
                memcpy(self._data + self._actual_size, <void*> data,
                       bytes_to_write)
                self._actual_size += bytes_to_write
            if bytes_to_write == length:
                break
            self._send_packet(final_packet=False)
            length -= bytes_to_write
            data += bytes_to_write

    cdef int write_seq_num(self) except -1:
        self._seq_num += 1
        if self._seq_num == 0:
            self._seq_num = 1
        self.write_uint8(self._seq_num)

    cdef int write_str(self, str value) except -1:
        self.write_bytes(value.encode())

    cdef int write_uint8(self, uint8_t value) except -1:
        if self._actual_size + 1 > self._max_size:
            self._send_packet(final_packet=False)
        self._data[self._actual_size] = value
        self._actual_size += 1

    cdef int write_uint16(self, uint16_t value,
                          int byte_order=BYTE_ORDER_MSB) except -1:
        if self._actual_size + 2 > self._max_size:
            self._send_packet(final_packet=False)
        pack_uint16(&self._data[self._actual_size], value, byte_order)
        self._actual_size += 2

    cdef int write_uint32(self, uint32_t value,
                          int byte_order=BYTE_ORDER_MSB) except -1:
        if self._actual_size + 4 > self._max_size:
            self._send_packet(final_packet=False)
        pack_uint32(&self._data[self._actual_size], value, byte_order)
        self._actual_size += 4

    cdef int write_uint64(self, uint64_t value,
                          byte_order=BYTE_ORDER_MSB) except -1:
        if self._actual_size + 8 > self._max_size:
            self._send_packet(final_packet=False)
        pack_uint64(&self._data[self._actual_size], value, byte_order)
        self._actual_size += 8

    cdef int write_ub4(self, uint32_t value) except -1:
        if value == 0:
            self.write_uint8(0)
        elif value <= UINT8_MAX:
            self.write_uint8(1)
            self.write_uint8(<uint8_t> value)
        elif value <= UINT16_MAX:
            self.write_uint8(2)
            self.write_uint16(<uint16_t> value)
        else:
            self.write_uint8(4)
            self.write_uint32(value)

    cdef int write_ub8(self, uint64_t value) except -1:
        if value == 0:
            self.write_uint8(0)
        elif value <= UINT8_MAX:
            self.write_uint8(1)
            self.write_uint8(<uint8_t> value)
        elif value <= UINT16_MAX:
            self.write_uint8(2)
            self.write_uint16(<uint16_t> value)
        elif value <= UINT32_MAX:
            self.write_uint8(4)
            self.write_uint32(value)
        else:
            self.write_uint8(8)
            self.write_uint64(value)
