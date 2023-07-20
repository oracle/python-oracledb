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

cdef enum:
    PACKET_HEADER_SIZE = 8
    CHUNKED_BYTES_CHUNK_SIZE = 65536

cdef struct BytesChunk:
    char_type *ptr
    uint32_t length
    uint32_t allocated_length

cdef struct Rowid:
    uint32_t rba
    uint16_t partition_id
    uint32_t block_num
    uint16_t slot_num

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
cdef class ReadBuffer(Buffer):

    cdef:
        ssize_t _max_packet_size, _bytes_to_process
        ChunkedBytesBuffer _chunked_bytes_buf
        bint _session_needs_to_be_closed
        const char_type _split_data[255]
        ssize_t _packet_start_offset
        Capabilities _caps
        object _socket

    def __cinit__(self, object sock, ssize_t max_packet_size,
                  Capabilities caps):
        self._socket = sock
        self._caps = caps
        self._max_packet_size = max_packet_size
        self._initialize(max_packet_size * 2)
        self._chunked_bytes_buf = ChunkedBytesBuffer()

    cdef inline int _get_data_from_socket(self, object obj,
                                          ssize_t bytes_requested,
                                          ssize_t *bytes_read) except -1:
        """
        Simple function that performs a socket read while verifying that the
        server has not reset the connection. If it has, the dead connection
        error is returned instead.
        """
        try:
            bytes_read[0] = self._socket.recv_into(obj, bytes_requested)
        except ConnectionResetError as e:
            errors._raise_err(errors.ERR_CONNECTION_CLOSED, str(e), cause=e)
        if bytes_read[0] == 0:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self._socket.close()
            self._socket = None
            errors._raise_err(errors.ERR_CONNECTION_CLOSED)

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
        if self._pos == self._size:
            self.receive_packet(&packet_type, &packet_flags)
            self.skip_raw_bytes(2)          # skip data flags

        # if there is enough room in the buffer to satisfy the number of bytes
        # requested, return a pointer to the current location and advance the
        # offset the required number of bytes
        source_ptr = &self._data[self._pos]
        num_bytes_left = self._size - self._pos
        if num_bytes <= num_bytes_left:
            if in_chunked_read:
                dest_ptr = self._chunked_bytes_buf.get_chunk_ptr(num_bytes)
                memcpy(dest_ptr, source_ptr, num_bytes)
            self._pos += num_bytes
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
            source_ptr = &self._data[self._pos]
            num_bytes_split = min(num_bytes, self._size - self._pos)
            if in_chunked_read:
                dest_ptr = \
                        self._chunked_bytes_buf.get_chunk_ptr(num_bytes_split)
            else:
                dest_ptr = <char_type*> &self._split_data[num_bytes_left]
            memcpy(dest_ptr, source_ptr, num_bytes_split)
            self._pos += num_bytes_split
            num_bytes -= num_bytes_split

        # return the split buffer unconditionally; if performing a chunked read
        # the return value is ignored anyway
        return self._split_data

    cdef int _read_raw_bytes_and_length(self, const char_type **ptr,
                                        ssize_t *num_bytes) except -1:
        """
        Helper function that processes the length. If the length is defined as
        TNS_LONG_LENGTH_INDICATOR, a chunked read is performed.
        """
        cdef uint32_t temp_num_bytes
        if num_bytes[0] != TNS_LONG_LENGTH_INDICATOR:
            return Buffer._read_raw_bytes_and_length(self, ptr, num_bytes)
        self._chunked_bytes_buf.start_chunked_read()
        num_bytes[0] = 0
        while True:
            self.read_ub4(&temp_num_bytes)
            if temp_num_bytes == 0:
                break
            num_bytes[0] += temp_num_bytes
            self._get_raw(temp_num_bytes, in_chunked_read=True)
        ptr[0] = self._chunked_bytes_buf.end_chunked_read()

    cdef int _process_control_packet(self) except -1:
        """
        Process a control packed received in between data packets.
        """
        cdef:
            uint16_t control_type
            uint32_t error_num
        self.read_uint16(&control_type)
        if control_type == TNS_CONTROL_TYPE_RESET_OOB:
            self._caps.supports_oob = False
        elif control_type == TNS_CONTROL_TYPE_INBAND_NOTIFICATION:
            self.skip_raw_bytes(4)           # skip first integer
            self.read_uint32(&error_num)
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
            ssize_t offset, bytes_to_read, bytes_read
            uint32_t packet_size
            uint16_t temp16

        # if no bytes are left over from a previous read, perform a read of the
        # maximum packet size and reset the offset to 0
        if self._bytes_to_process == 0:
            self._packet_start_offset = 0
            self._pos = 0
            self._get_data_from_socket(self._data_obj, self._max_packet_size,
                                       &self._bytes_to_process)

        # otherwise, set the offset to the end of the previous packet and
        # ensure that there are at least enough bytes available to cover the
        # contents of the packet header
        else:
            self._packet_start_offset = self._size
            self._pos = self._size
            if self._bytes_to_process < PACKET_HEADER_SIZE:
                offset = self._size + self._bytes_to_process
                bytes_to_read = PACKET_HEADER_SIZE - self._bytes_to_process
                self._get_data_from_socket(self._data_view[offset:],
                                           bytes_to_read, &bytes_read)
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

    cdef object read_oson(self):
        """
        Read an OSON value from the buffer and return the converted value. OSON
        is sent as a LOB value with all of the data prefetched. Since the LOB
        locator is not required it is simply discarded.
        it.
        """
        cdef:
            OsonDecoder decoder
            uint32_t num_bytes
            bytes data
        self.read_ub4(&num_bytes)
        if num_bytes > 0:
            self.skip_ub8()             # size (unused)
            self.skip_ub4()             # chunk size (unused)
            data = self.read_bytes()
            self.read_bytes()           # LOB locator (unused)
            decoder = OsonDecoder.__new__(OsonDecoder)
            return decoder.decode(data)

    cdef object read_lob_with_length(self, ThinConnImpl conn_impl,
                                     DbType dbtype):
        """
        Read a LOB locator from the buffer and return a LOB object containing
        it.
        """
        cdef:
            uint32_t chunk_size, num_bytes
            ThinLobImpl lob_impl
            uint64_t size
            bytes locator
        self.read_ub4(&num_bytes)
        if num_bytes > 0:
            self.read_ub8(&size)
            self.read_ub4(&chunk_size)
            locator = self.read_bytes()
            lob_impl = ThinLobImpl._create(conn_impl, dbtype, locator)
            lob_impl._size = size
            lob_impl._chunk_size = chunk_size
            lob_impl._has_metadata = True
            return PY_TYPE_LOB._from_impl(lob_impl)

    cdef int read_rowid(self, Rowid *rowid) except -1:
        """
        Reads a rowid from the buffer and populates the rowid structure.
        """
        self.read_ub4(&rowid.rba)
        self.read_ub2(&rowid.partition_id)
        self.skip_ub1()
        self.read_ub4(&rowid.block_num)
        self.read_ub2(&rowid.slot_num)

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
            uint8_t length
            Rowid rowid

        # get data (first buffer contains the length, which can be ignored)
        self.read_raw_bytes_and_length(&input_ptr, &input_len)
        if input_ptr == NULL:
            return None
        self.read_raw_bytes_and_length(&input_ptr, &input_len)

        # handle physical rowid
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

    cdef int check_control_packet(self) except -1:
        """
        Checks for a control packet or final close packet from the server.
        """
        cdef:
            uint8_t packet_type, packet_flags
            uint16_t data_flags
        self._receive_packet_helper(&packet_type, &packet_flags)
        if packet_type == TNS_PACKET_TYPE_CONTROL:
            self._process_control_packet()
        elif packet_type == TNS_PACKET_TYPE_DATA:
            self.read_uint16(&data_flags)
            if data_flags == TNS_DATA_FLAGS_EOF:
                self._session_needs_to_be_closed = True

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


@cython.final
cdef class WriteBuffer(Buffer):

    cdef:
        uint8_t _packet_type
        uint8_t _packet_flags
        Capabilities _caps
        object _socket
        uint8_t _seq_num
        bint _packet_sent

    def __cinit__(self, object sock, ssize_t max_size, Capabilities caps):
        self._socket = sock
        self._caps = caps
        self._initialize(max_size)

    cdef int _send_packet(self, bint final_packet) except -1:
        """
        Write the packet header and then send the packet. Once sent, reset the
        pointers back to an empty packet.
        """
        cdef ssize_t size = self._pos
        self._pos = 0
        if self._caps.protocol_version >= TNS_VERSION_MIN_LARGE_SDU:
            self.write_uint32(size)
        else:
            self.write_uint16(size)
            self.write_uint16(0)
        self.write_uint8(self._packet_type)
        self.write_uint8(self._packet_flags)
        self.write_uint16(0)
        self._pos = size
        if DEBUG_PACKETS:
            _print_packet("Sending packet:", self._socket.fileno(),
                          self._data_view[:self._pos])
        try:
            self._socket.send(self._data_view[:self._pos])
        except OSError as e:
            errors._raise_err(errors.ERR_CONNECTION_CLOSED, str(e))
        self._packet_sent = True
        self._pos = PACKET_HEADER_SIZE
        if not final_packet:
            self.write_uint16(0)            # add data flags for next packet

    cdef int _write_more_data(self, ssize_t num_bytes_available,
                              ssize_t num_bytes_wanted) except -1:
        """
        Called when the amount of buffer available is less than the amount of
        data requested. This sends the packet to the server and then resets the
        buffer for further writing.
        """
        self._send_packet(final_packet=False)

    cdef int end_request(self) except -1:
        """
        Indicates that the request from the client is completing and will send
        any packet remaining, if necessary.
        """
        if self._pos > PACKET_HEADER_SIZE:
            self._send_packet(final_packet=True)

    cdef inline ssize_t max_payload_bytes(self):
        """
        Return the maximum number of bytes that can be sent in a packet. This
        is the maximum size of the entire packet, less the bytes in the header
        and 2 bytes for the data flags.
        """
        return self._max_size - PACKET_HEADER_SIZE - 2

    cdef void start_request(self, uint8_t packet_type, uint8_t packet_flags=0,
                            uint16_t data_flags=0):
        """
        Indicates that a request from the client is starting. The packet type
        is retained just in case a request spans multiple packets. The packet
        header (8 bytes in length) is written when a packet is actually being
        sent and so is skipped at this point.
        """
        self._packet_sent = False
        self._packet_type = packet_type
        self._packet_flags = packet_flags
        self._pos = PACKET_HEADER_SIZE
        if packet_type == TNS_PACKET_TYPE_DATA:
            self.write_uint16(data_flags)

    cdef int write_lob_with_length(self, ThinLobImpl lob_impl) except -1:
        """
        Writes a LOB locator to the buffer.
        """
        self.write_ub4(len(lob_impl._locator))
        return self.write_lob(lob_impl)

    cdef object write_oson(self, value):
        """
        Encodes the given value to OSON and then writes that to the buffer.
        it.
        """
        cdef OsonEncoder encoder = OsonEncoder.__new__(OsonEncoder)
        encoder.encode(value)
        self.write_qlocator(encoder._pos)
        self._write_raw_bytes_and_length(encoder._data, encoder._pos)

    cdef int write_seq_num(self) except -1:
        self._seq_num += 1
        if self._seq_num == 0:
            self._seq_num = 1
        self.write_uint8(self._seq_num)
