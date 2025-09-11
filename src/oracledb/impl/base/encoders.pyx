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
# encoders.pyx
#
# Cython file defining the low-level encoding routines used by the driver.
#------------------------------------------------------------------------------

cdef inline void encode_binary_double(char_type *buf, double value):
    """
    Encodes a double in the format expected by the Oracle Database for
    BINARY_DOUBLE.
    """
    cdef:
        uint8_t b0, b1, b2, b3, b4, b5, b6, b7
        uint64_t all_bits
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


cdef inline void encode_binary_float(char_type *buf, float value):
    """
    Encodes a float in the format expected by the Oracle Database for
    BINARY_FLOAT.
    """
    cdef:
        uint8_t b0, b1, b2, b3
        uint32_t all_bits
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


cdef inline void encode_boolean(char_type *buf, ssize_t *buflen, bint value):
    """
    Encodes a boolean in the format expected by the Oracle Database for
    BOOLEAN.
    """
    if value:
        buflen[0] = 3
        buf[0] = 2
        encode_uint16be(&buf[1], 0x0101)
    else:
        buflen[0] = 2
        encode_uint16be(buf, 0x0100)


cdef inline void encode_date(char_type *buf, object value):
    """
    Encodes a datetime.date or datetime.datetime object in the format exepcted
    by the Oracle Database for DATE.
    """
    cdef unsigned int year
    year = cydatetime.PyDateTime_GET_YEAR(value)
    buf[0] = <uint8_t> ((year // 100) + 100)
    buf[1] = <uint8_t> ((year % 100) + 100)
    buf[2] = <uint8_t> cydatetime.PyDateTime_GET_MONTH(value)
    buf[3] = <uint8_t> cydatetime.PyDateTime_GET_DAY(value)
    buf[4] = <uint8_t> cydatetime.PyDateTime_DATE_GET_HOUR(value) + 1
    buf[5] = <uint8_t> cydatetime.PyDateTime_DATE_GET_MINUTE(value) + 1
    buf[6] = <uint8_t> cydatetime.PyDateTime_DATE_GET_SECOND(value) + 1


cdef inline void encode_interval_ds(char_type *buf, object value):
    """
    Encodes a datetime.timedelta object in the format exepcted by the Oracle
    Database for INTERVAL DAY TO SECOND.
    """
    cdef int32_t days, seconds, fseconds
    days = cydatetime.timedelta_days(value)
    encode_uint32be(buf, days + TNS_DURATION_MID)
    seconds = cydatetime.timedelta_seconds(value)
    buf[4] = (seconds // 3600) + TNS_DURATION_OFFSET
    seconds = seconds % 3600
    buf[5] = (seconds // 60) + TNS_DURATION_OFFSET
    buf[6] = (seconds % 60) + TNS_DURATION_OFFSET
    fseconds = cydatetime.timedelta_microseconds(value) * 1000
    encode_uint32be(&buf[7], fseconds + TNS_DURATION_MID)


cdef int encode_interval_ym(char_type *buf, object value) except -1:
    """
    Encodes a IntervalYM object in the format exepcted by the Oracle Database
    for INTERVAL YEAR TO MONTH.
    """
    cdef int32_t years, months
    years = (<tuple> value)[0]
    months = (<tuple> value)[1]
    encode_uint32be(buf, years + TNS_DURATION_MID)
    buf[4] = months + TNS_DURATION_OFFSET


cdef int encode_number(char_type *buf, ssize_t *buflen, bytes value) except -1:
    """
    Encodes bytes representing numeric data in the format exepcted by the
    Oracle Database for NUMBER.
    """
    cdef:
        uint8_t num_digits = 0, digit, num_pairs, pair_num, digits_pos
        bint is_negative = False, prepend_zero = False
        ssize_t value_length, exponent_pos, pos = 0
        uint8_t digits[NUMBER_AS_TEXT_CHARS]
        bint exponent_is_negative = False
        int16_t decimal_point_index
        int8_t exponent_on_wire
        const char_type *ptr
        int16_t exponent

    # zero length string cannot be converted
    value_length = len(value)
    if value_length == 0:
        errors._raise_err(errors.ERR_NUMBER_STRING_OF_ZERO_LENGTH)
    elif value_length > NUMBER_AS_TEXT_CHARS:
        errors._raise_err(errors.ERR_NUMBER_STRING_TOO_LONG)

    # check to see if number is negative (first character is '-')
    ptr = value
    if ptr[0] == b'-':
        is_negative = True
        pos += 1

    # scan for digits until the decimal point or exponent indicator found
    while pos < value_length:
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
    if pos < value_length and ptr[pos] == b'.':
        pos += 1
        while pos < value_length:
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
    if pos < value_length and (ptr[pos] == b'e' or ptr[pos] == b'E'):
        pos += 1
        if pos < value_length:
            if ptr[pos] == b'-':
                exponent_is_negative = True
                pos += 1
            elif ptr[pos] == b'+':
                pos += 1
        exponent_pos = pos
        while pos < value_length:
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
    if pos < value_length:
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

    # if the number of digits is zero, the value is itself zero since all
    # leading and trailing zeros are removed from the digits string; this
    # is a special case
    if num_digits == 0:
        buf[0] = 128
        buflen[0] = 1
        return 0

    # the total length of the buffer will be the number of pairs (each of which
    # are encoded in a single byte) plus a single byte for the exponent
    buflen[0] = num_pairs + 1

    # encode the exponent
    exponent_on_wire = <int8_t> (decimal_point_index / 2) + 192
    if is_negative:
        exponent_on_wire = ~exponent_on_wire
    buf[0] = exponent_on_wire

    # encode the mantissa bytes
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
        buf[pair_num + 1] = digit

    # append a sentinel 102 byte for negative numbers if the number of digits
    # is less than the maximum allowable
    if is_negative and num_digits < NUMBER_MAX_DIGITS:
        buf[num_pairs + 1] = 102
        buflen[0] += 1


cdef inline void encode_timestamp(char_type *buf, object value):
    """
    Encodes a datetime.date or datetime.datetime object in the format exepcted
    by the Oracle Database for TIMESTAMP (WITH LOCAL TIME ZONE).
    """
    cdef uint32_t fsecond = 0
    encode_date(buf, value)
    if isinstance(value, PY_TYPE_DATETIME):
        fsecond = <uint32_t> \
                cydatetime.PyDateTime_DATE_GET_MICROSECOND(value) * 1000
    encode_uint32be(&buf[7], fsecond)


cdef inline void encode_timestamp_tz(char_type *buf, object value):
    """
    Encodes a datetime.date or datetime.datetime object in the format exepcted
    by the Oracle Database for TIMESTAMP WITH TIME ZONE.
    """
    encode_timestamp(buf, value)
    buf[11] = TZ_HOUR_OFFSET
    buf[12] = TZ_MINUTE_OFFSET


cdef inline void encode_uint16be(char_type *buf, uint16_t value):
    """
    Encodes a 16-bit integer in big endian order (most significant byte first).
    """
    buf[0] = <char_type> ((value >> 8) & 0xff)
    buf[1] = <char_type> (value & 0xff)


cdef inline void encode_uint16le(char_type *buf, uint16_t value):
    """
    Encodes a 16-bit integer in big endian order (most significant byte first).
    """
    buf[1] = <char_type> ((value >> 8) & 0xff)
    buf[0] = <char_type> (value & 0xff)


cdef inline void encode_uint32be(char_type *buf, uint32_t value):
    """
    Encodes a 32-bit integer in big endian order (most significant byte first).
    """
    buf[0] = <char_type> ((value >> 24) & 0xff)
    buf[1] = <char_type> ((value >> 16) & 0xff)
    buf[2] = <char_type> ((value >> 8) & 0xff)
    buf[3] = <char_type> (value & 0xff)


cdef inline void encode_uint64be(char_type *buf, uint64_t value):
    """
    Decodes a 64-bit integer in big endian order (most significant byte first).
    """
    buf[0] = <char_type> ((value >> 56) & 0xff)
    buf[1] = <char_type> ((value >> 48) & 0xff)
    buf[2] = <char_type> ((value >> 40) & 0xff)
    buf[3] = <char_type> ((value >> 32) & 0xff)
    buf[4] = <char_type> ((value >> 24) & 0xff)
    buf[5] = <char_type> ((value >> 16) & 0xff)
    buf[6] = <char_type> ((value >> 8) & 0xff)
    buf[7] = <char_type> (value & 0xff)
