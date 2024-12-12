#------------------------------------------------------------------------------
# Copyright (c) 2024, Oracle and/or its affiliates.
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
# decoders.pyx
#
# Cython file defining the low-level decoding routines used by the driver.
#------------------------------------------------------------------------------

cdef int decode_binary_double(const uint8_t *ptr, ssize_t num_bytes,
                              OracleDataBuffer *buffer) except -1:
    """
    Decode a binary double from raw bytes.
    """
    cdef:
        uint8_t b0, b1, b2, b3, b4, b5, b6, b7
        uint64_t high_bits, low_bits, all_bits
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
    memcpy(&buffer.as_double, &all_bits, 8)


cdef int decode_binary_float(const uint8_t *ptr, ssize_t num_bytes,
                             OracleDataBuffer *buffer) except -1:
    """
    Decode a binary float from raw bytes.
    """
    cdef:
        uint8_t b0, b1, b2, b3
        uint64_t all_bits
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
    memcpy(&buffer.as_float, &all_bits, 4)


cdef int decode_bool(const uint8_t* ptr, ssize_t num_bytes,
                     OracleDataBuffer *buffer) except -1:
    """
    Decode a boolean value from raw bytes.
    """
    buffer.as_bool = (ptr[num_bytes - 1] == 1)


cdef int decode_date(const uint8_t* ptr, ssize_t num_bytes,
                     OracleDataBuffer *buffer) except -1:
    """
    Decode a date from the raw bytes making up the Oracle Date.
    """
    cdef OracleDate *output = &buffer.as_date
    output.year = (ptr[0] - 100) * 100 + ptr[1] - 100
    output.month = ptr[2]
    output.day = ptr[3]
    output.hour = ptr[4] - 1
    output.minute = ptr[5] - 1
    output.second = ptr[6] - 1
    if num_bytes < 11:
        output.fsecond = 0
    else:
        output.fsecond = decode_uint32be(&ptr[7]) // 1000
    if num_bytes <= 11 or ptr[11] == 0 or ptr[12] == 0:
        output.tz_hour_offset = output.tz_minute_offset = 0
    else:
        if ptr[11] & TNS_HAS_REGION_ID:
            errors._raise_err(errors.ERR_NAMED_TIMEZONE_NOT_SUPPORTED)
        output.tz_hour_offset = ptr[11] - TZ_HOUR_OFFSET
        output.tz_minute_offset = ptr[12] - TZ_MINUTE_OFFSET


cdef uint64_t decode_integer(const uint8_t* ptr, ssize_t num_bytes):
    """
    Decodes an integer from raw bytes.
    """
    if num_bytes == 1:
        return ptr[0]
    elif num_bytes == 2:
        return decode_uint16be(ptr)
    elif num_bytes == 3:
        return decode_uint24be(ptr)
    elif num_bytes == 4:
        return decode_uint32be(ptr)
    elif num_bytes == 5:
        return decode_uint40be(ptr)
    elif num_bytes == 6:
        return decode_uint48be(ptr)
    elif num_bytes == 7:
        return decode_uint56be(ptr)
    elif num_bytes == 8:
        return decode_uint64be(ptr)


cdef int decode_interval_ds(const uint8_t *ptr, ssize_t num_bytes,
                            OracleDataBuffer *buffer) except -1:
    """
    Decode an interval days to seconds from raw bytes.
    """
    cdef OracleIntervalDS *output = &buffer.as_interval_ds
    output.days = decode_uint32be(ptr) - TNS_DURATION_MID
    output.hours = ptr[4] - TNS_DURATION_OFFSET
    output.minutes = ptr[5] - TNS_DURATION_OFFSET
    output.seconds = ptr[6] - TNS_DURATION_OFFSET
    output.fseconds = decode_uint32be(&ptr[7]) - TNS_DURATION_MID


cdef int decode_interval_ym(const uint8_t *ptr, ssize_t num_bytes,
                            OracleDataBuffer *buffer) except -1:
    """
    Decode an interval years to months from raw bytes.
    """
    cdef OracleIntervalYM *output = &buffer.as_interval_ym
    output.years = decode_uint32be(ptr) - TNS_DURATION_MID
    output.months = ptr[4] - TNS_DURATION_OFFSET


cdef int decode_number(const uint8_t* ptr, ssize_t num_bytes,
                       OracleDataBuffer *buffer) except -1:
    """
    Decode a number from the raw bytes making up the Oracle number.
    """
    cdef:
        OracleNumber *output = &buffer.as_number
        uint8_t byte, digit, num_digits
        int16_t decimal_point_index
        uint8_t digits[40]
        bint is_positive
        int8_t exponent

    # the first byte is the exponent; positive numbers have the highest
    # order bit set, whereas negative numbers have the highest order bit
    # cleared and the bits inverted
    exponent = <int8_t> ptr[0]
    is_positive = (exponent & 0x80)
    if not is_positive:
        exponent = ~exponent
    exponent -= 193
    decimal_point_index = exponent * 2 + 2

    # initialize output structure
    output.is_max_negative_value = False
    output.is_integer = True
    output.num_chars = 0

    # a mantissa length of 0 implies a value of 0 (if positive) or a value
    # of -1e126 (if negative)
    if num_bytes == 1:
        if is_positive:
            output.num_chars = 1
            output.chars[0] = 48                    # zero
        else:
            output.is_max_negative_value = True
        return 0

    # check for the trailing 102 byte for negative numbers and, if present,
    # reduce the number of mantissa digits
    if not is_positive and ptr[num_bytes - 1] == 102:
        num_bytes -= 1

    # process the mantissa bytes which are the remaining bytes; each
    # mantissa byte is a base-100 digit
    num_digits = 0
    for i in range(1, num_bytes):

        # positive numbers have 1 added to them; negative numbers are
        # subtracted from the value 101
        byte = ptr[i]
        if is_positive:
            byte -= 1
        else:
            byte = 101 - byte

        # process the first digit; leading zeroes are ignored
        digit = <uint8_t> byte // 10
        if digit == 0 and num_digits == 0:
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
        if digit != 0 or i < num_bytes - 1:
            digits[num_digits] = digit
            num_digits += 1

    # create string of digits for transformation to Python value
    # if negative, include the sign
    if not is_positive:
        output.chars[output.num_chars] = 45         # minus sign
        output.num_chars += 1

    # if the decimal point index is 0 or less, add the decimal point and
    # any leading zeroes that are needed
    if decimal_point_index <= 0:
        output.chars[output.num_chars] = 48         # zero
        output.chars[output.num_chars + 1] = 46     # decimal point
        output.num_chars += 2
        output.is_integer = 0
        for i in range(decimal_point_index, 0):
            output.chars[output.num_chars] = 48     # zero
            output.num_chars += 1

    # add each of the digits
    for i in range(num_digits):
        if i > 0 and i == decimal_point_index:
            output.chars[output.num_chars] = 46     # decimal point
            output.is_integer = 0
            output.num_chars += 1
        output.chars[output.num_chars] = 48 + digits[i]
        output.num_chars += 1

    # if the decimal point index exceeds the number of digits, add any
    # trailing zeroes that are needed
    if decimal_point_index > num_digits:
        for i in range(num_digits, decimal_point_index):
            output.chars[output.num_chars] = 48     # zero
            output.num_chars += 1


cdef inline uint16_t decode_uint16be(const char_type *buf):
    """
    Decodes a 16-bit integer in big endian order (most significant byte first).
    """
    return (
        (<uint16_t> buf[0] << 8) |
        (<uint16_t> buf[1])
    )


cdef inline uint16_t decode_uint16le(const char_type *buf):
    """
    Decodes a 16-bit integer in little endian order (least significant byte
    first).
    """
    return (
        (<uint16_t> buf[1] << 8) |
        (<uint16_t> buf[0])
    )


cdef inline uint32_t decode_uint24be(const char_type *buf):
    """
    Decodes a 24-bit integer in big endian order (most significant byte first).
    """
    return (
        (<uint32_t> buf[0] << 16) |
        (<uint32_t> buf[1] << 8) |
        (<uint32_t> buf[2])
    )


cdef inline uint32_t decode_uint32be(const char_type *buf):
    """
    Decodes a 32-bit integer in big endian order (most significant byte first).
    """
    return (
        (<uint32_t> buf[0] << 24) |
        (<uint32_t> buf[1] << 16) |
        (<uint32_t> buf[2] << 8) |
        (<uint32_t> buf[3])
    )


cdef inline uint64_t decode_uint40be(const char_type *buf):
    """
    Decodes a 40-bit integer in big endian order (most significant byte first).
    """
    return (
        (<uint64_t> buf[0] << 32) |
        (<uint64_t> buf[1] << 24) |
        (<uint64_t> buf[2] << 16) |
        (<uint64_t> buf[3] << 8) |
        (<uint64_t> buf[4])
    )


cdef inline uint64_t decode_uint48be(const char_type *buf):
    """
    Decodes a 48-bit integer in big endian order (most significant byte first).
    """
    return (
        (<uint64_t> buf[0] << 40) |
        (<uint64_t> buf[1] << 32) |
        (<uint64_t> buf[2] << 24) |
        (<uint64_t> buf[3] << 16) |
        (<uint64_t> buf[4] << 8) |
        (<uint64_t> buf[5])
    )


cdef inline uint64_t decode_uint56be(const char_type *buf):
    """
    Decodes a 56-bit integer in big endian order (most significant byte first).
    """
    return (
        (<uint64_t> buf[0] << 48) |
        (<uint64_t> buf[1] << 40) |
        (<uint64_t> buf[2] << 32) |
        (<uint64_t> buf[3] << 24) |
        (<uint64_t> buf[4] << 16) |
        (<uint64_t> buf[5] << 8) |
        (<uint64_t> buf[6])
    )


cdef inline uint64_t decode_uint64be(const char_type *buf):
    """
    Decodes a 64-bit integer in big endian order (most significant byte first).
    """
    return (
        (<uint64_t> buf[0] << 56) |
        (<uint64_t> buf[1] << 48) |
        (<uint64_t> buf[2] << 40) |
        (<uint64_t> buf[3] << 32) |
        (<uint64_t> buf[4] << 24) |
        (<uint64_t> buf[5] << 16) |
        (<uint64_t> buf[6] << 8) |
        (<uint64_t> buf[7])
    )
