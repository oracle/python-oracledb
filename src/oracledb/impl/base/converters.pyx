#------------------------------------------------------------------------------
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
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
# converters.pyx
#
# Cython file defining the low-level methods for converting the intermediate
# form returned by the decoders to an appropriate Python value.
#------------------------------------------------------------------------------

cdef object convert_date_to_python(OracleDataBuffer *buffer):
    """
    Converts a DATE, TIMESTAMP, TIMESTAMP WITH LOCAL TIME ZONE or TIMESTAMP
    WITH TIMEZONE value stored in the buffer to Python datetime.datetime().
    """
    cdef:
        OracleDate *value = &buffer.as_date
        int32_t seconds
    output = cydatetime.datetime_new(value.year, value.month, value.day,
                                     value.hour, value.minute, value.second,
                                     value.fsecond, None)
    if value.tz_hour_offset != 0 or value.tz_minute_offset != 0:
        seconds = value.tz_hour_offset * 3600 + value.tz_minute_offset * 60
        output += cydatetime.timedelta_new(0, seconds, 0)
    return output


cdef object convert_interval_ds_to_python(OracleDataBuffer *buffer):
    """
    Converts an INTERVAL DAYS TO SECONDS value stored in the buffer to Python
    datetime.timedelta().
    """
    cdef:
        OracleIntervalDS *value = &buffer.as_interval_ds
        int32_t total_seconds
    total_seconds = value.hours * 60 * 60 + value.minutes * 60 + value.seconds
    return cydatetime.timedelta_new(value.days, total_seconds,
                                    value.fseconds // 1000)


cdef object convert_interval_ym_to_python(OracleDataBuffer *buffer):
    """
    Converts an INTERVAL YEARS TO MONTHS value stored in the buffer to Python
    oracledb.IntervalYM().
    """
    cdef OracleIntervalYM *value = &buffer.as_interval_ym
    return PY_TYPE_INTERVAL_YM(value.years, value.months)


cdef int convert_number_to_arrow_decimal(OracleArrowArray arrow_array,
                                         OracleDataBuffer *buffer) except -1:
    """
    Converts a NUMBER value stored in the buffer to Arrow DECIMAL128.
    """
    cdef:
        char_type c
        bint has_sign = 0
        char_type digits[39] # 38 digits + sign
        OracleNumber *value = &buffer.as_number
        uint8_t num_chars = 0, decimal_point_index = 0, allowed_max_chars = 0
        int64_t actual_scale = 0

    if value.chars[0] == 45: # minus sign
        has_sign = True

    if value.is_integer:
        if has_sign:
            allowed_max_chars = 39
        else:
            allowed_max_chars = 38
    else: # decimal point
        if has_sign:
            allowed_max_chars = 40
        else:
            allowed_max_chars = 39

    # Arrow Decimal128 can only represent values with 38 decimal digits
    if value.is_max_negative_value or value.num_chars > allowed_max_chars:
        raise ValueError("Value cannot be represented as "
                         "Arrow Decimal128")
    if value.is_integer:
        arrow_array.append_decimal(value.chars, value.num_chars)
    else:
        for i in range(value.num_chars):
            c = value.chars[i]
            # count all characters except the decimal point
            if c != 46:
                digits[num_chars] = c
                num_chars += 1
            else:
                decimal_point_index = i

        # Append any trailing zeros.
        actual_scale = num_chars - decimal_point_index
        for i in range(abs(arrow_array.scale) - actual_scale):
            digits[num_chars] = b'0'
            num_chars += 1
        arrow_array.append_decimal(digits, num_chars)



cdef int convert_number_to_arrow_double(OracleArrowArray arrow_array,
                                        OracleDataBuffer *buffer) except -1:
    """
    Converts a NUMBER value stored in the buffer to Arrow DOUBLE.
    """
    cdef OracleNumber *value = &buffer.as_number
    if value.is_max_negative_value:
        arrow_array.append_double(-1.0e126)
    else:
        arrow_array.append_double(atof(value.chars[:value.num_chars]))


cdef int convert_number_to_arrow_int64(OracleArrowArray arrow_array,
                                       OracleDataBuffer *buffer) except -1:
    """
    Converts a NUMBER value stored in the buffer to Arrow INT64.
    """
    cdef OracleNumber *value = &buffer.as_number
    arrow_array.append_int64(atoi(value.chars[:value.num_chars]))


cdef object convert_number_to_python_decimal(OracleDataBuffer *buffer):
    """
    Converts a NUMBER value stored in the buffer to Python decimal.Decimal().
    """
    cdef OracleNumber *value = &buffer.as_number
    if value.is_max_negative_value:
        return PY_TYPE_DECIMAL("-1e126")
    return PY_TYPE_DECIMAL(value.chars[:value.num_chars].decode())


cdef object convert_number_to_python_float(OracleDataBuffer *buffer):
    """
    Converts a NUMBER value stored in the buffer to Python float.
    """
    cdef OracleNumber *value = &buffer.as_number
    if value.is_max_negative_value:
        return -1.0e126
    return float(value.chars[:value.num_chars])


cdef object convert_number_to_python_int(OracleDataBuffer *buffer):
    """
    Converts a NUMBER value stored in the buffer to Python integer, if
    possible. If the value is not an integer, a float is returned instead.
    """
    cdef OracleNumber *value = &buffer.as_number
    if value.is_max_negative_value:
        return -10 ** 126
    elif value.is_integer:
        return int(value.chars[:value.num_chars])
    return float(value.chars[:value.num_chars])


cdef object convert_number_to_python_str(OracleDataBuffer *buffer):
    """
    Converts a NUMBER value stored in the buffer to Python string.
    """
    cdef OracleNumber *value = &buffer.as_number
    if value.is_max_negative_value:
        return "-1e126"
    return value.chars[:value.num_chars].decode()


cdef object convert_raw_to_python(OracleDataBuffer *buffer):
    """
    Converts a RAW or LONG RAW value stored in the buffer to Python bytes.
    """
    cdef OracleRawBytes *rb = &buffer.as_raw_bytes
    return rb.ptr[:rb.num_bytes]


cdef object convert_str_to_python(OracleDataBuffer *buffer, uint8_t csfrm,
                                  const char* encoding_errors):
    """
    Converts a CHAR, NCHAR, LONG, VARCHAR, or NVARCHAR value stored in the
    buffer to Python string.
    """
    cdef OracleRawBytes *rb = &buffer.as_raw_bytes
    if csfrm == CS_FORM_IMPLICIT:
        return rb.ptr[:rb.num_bytes].decode(ENCODING_UTF8, encoding_errors)
    return rb.ptr[:rb.num_bytes].decode(ENCODING_UTF16, encoding_errors)


cdef int convert_oracle_data_to_arrow(OracleMetadata from_metadata,
                                      OracleMetadata to_metadata,
                                      OracleData* data,
                                      OracleArrowArray arrow_array) except -1:
    """
    Converts the value stored in OracleData to Arrow format.
    """
    cdef:
        ArrowType arrow_type
        uint32_t db_type_num
        OracleRawBytes* rb
        int64_t ts

    # NULL values
    if data.is_null:
        return arrow_array.append_null()

    arrow_type = to_metadata._arrow_type
    db_type_num = from_metadata.dbtype.num
    if arrow_type == NANOARROW_TYPE_INT64:
        convert_number_to_arrow_int64(arrow_array, &data.buffer)
    elif arrow_type == NANOARROW_TYPE_DOUBLE:
        if db_type_num == DB_TYPE_NUM_NUMBER:
            convert_number_to_arrow_double(arrow_array, &data.buffer)
        else:
            arrow_array.append_double(data.buffer.as_double)
    elif arrow_type == NANOARROW_TYPE_FLOAT:
        arrow_array.append_float(data.buffer.as_float)
    elif arrow_type == NANOARROW_TYPE_BOOL:
        arrow_array.append_int64(data.buffer.as_bool)
    elif arrow_type in (
            NANOARROW_TYPE_BINARY,
            NANOARROW_TYPE_STRING,
            NANOARROW_TYPE_LARGE_BINARY,
            NANOARROW_TYPE_LARGE_STRING
    ):
        rb = &data.buffer.as_raw_bytes
        arrow_array.append_bytes(<void*> rb.ptr, rb.num_bytes)
    elif arrow_type == NANOARROW_TYPE_TIMESTAMP:
        ts = int(convert_date_to_python(&data.buffer).timestamp() *
                 arrow_array.factor)
        arrow_array.append_int64(ts)
    elif arrow_type == NANOARROW_TYPE_DECIMAL128:
        convert_number_to_arrow_decimal(arrow_array, &data.buffer)


cdef object convert_oracle_data_to_python(OracleMetadata from_metadata,
                                          OracleMetadata to_metadata,
                                          OracleData* data,
                                          const char* encoding_errors,
                                          bint from_dbobject):
    """
    Converts the value stored in OracleData to a Python object.
    """
    cdef:
        uint8_t py_type_num, ora_type_num, csfrm

    # NULL values
    if data.is_null:
        return None

    # reduce typing
    ora_type_num = from_metadata.dbtype._ora_type_num
    csfrm = from_metadata.dbtype._csfrm
    py_type_num = to_metadata._py_type_num

    # Python bytes
    if py_type_num == PY_TYPE_NUM_BYTES:

        # Oracle RAW, LONG RAW
        # Oracle CHAR, LONG and VARCHAR (bypass decode)
        if ora_type_num in (
            ORA_TYPE_NUM_CHAR,
            ORA_TYPE_NUM_LONG,
            ORA_TYPE_NUM_LONG_RAW,
            ORA_TYPE_NUM_RAW,
            ORA_TYPE_NUM_VARCHAR
        ):
            return convert_raw_to_python(&data.buffer)

    # Python string
    elif py_type_num == PY_TYPE_NUM_STR:

        # Oracle CHAR, LONG and VARCHAR
        if ora_type_num in (
            ORA_TYPE_NUM_CHAR,
            ORA_TYPE_NUM_LONG,
            ORA_TYPE_NUM_VARCHAR
        ):
            return convert_str_to_python(&data.buffer, csfrm, encoding_errors)

        # Oracle NUMBER
        elif ora_type_num == ORA_TYPE_NUM_NUMBER:
            return convert_number_to_python_str(&data.buffer)

        # Oracle BINARY_DOUBLE
        elif ora_type_num == ORA_TYPE_NUM_BINARY_DOUBLE:
            return str(data.buffer.as_double)

        # Oracle BINARY_FLOAT
        elif ora_type_num == ORA_TYPE_NUM_BINARY_FLOAT:
            return str(data.buffer.as_float)

        # Oracle DATE, TIMESTAMP (WITH (LOCAL) TIME ZONE)
        elif ora_type_num in (
            ORA_TYPE_NUM_DATE,
            ORA_TYPE_NUM_TIMESTAMP,
            ORA_TYPE_NUM_TIMESTAMP_LTZ,
            ORA_TYPE_NUM_TIMESTAMP_TZ
        ):
            return str(convert_date_to_python(&data.buffer))

        # Oracle INTERVAL DAY TO SECOND
        elif ora_type_num == ORA_TYPE_NUM_INTERVAL_DS:
            return str(convert_interval_ds_to_python(&data.buffer))

        # Oracle INTERVAL YEAR TO MONTH
        elif ora_type_num == ORA_TYPE_NUM_INTERVAL_DS:
            return str(convert_interval_ym_to_python(&data.buffer))

    # Python integer (or float if data is not an integer)
    elif py_type_num == PY_TYPE_NUM_INT:

        # Oracle BINARY_INTEGER within a DbObject
        if from_dbobject and ora_type_num == ORA_TYPE_NUM_BINARY_INTEGER:
            return data.buffer.as_integer

        # Oracle NUMBER, BINARY_INTEGER
        elif ora_type_num in (ORA_TYPE_NUM_NUMBER,
                              ORA_TYPE_NUM_BINARY_INTEGER):
            if to_metadata.dbtype._ora_type_num != ORA_TYPE_NUM_BINARY_INTEGER:
                return convert_number_to_python_int(&data.buffer)
            value = convert_number_to_python_str(&data.buffer)
            return int(PY_TYPE_DECIMAL(value))

        # Oracle CHAR, LONG, VARCHAR
        elif ora_type_num in (
            ORA_TYPE_NUM_CHAR,
            ORA_TYPE_NUM_LONG,
            ORA_TYPE_NUM_VARCHAR
        ):
            value = convert_str_to_python(&data.buffer, csfrm, encoding_errors)
            return int(PY_TYPE_DECIMAL(value))

        # Oracle BINARY_DOUBLE
        elif ora_type_num == ORA_TYPE_NUM_BINARY_DOUBLE:
            return int(PY_TYPE_DECIMAL(data.buffer.as_double))

        # Oracle BINARY_FLOAT
        elif ora_type_num == ORA_TYPE_NUM_BINARY_FLOAT:
            return int(PY_TYPE_DECIMAL(data.buffer.as_float))

    # Python decimal.Decimal
    elif py_type_num == PY_TYPE_NUM_DECIMAL:

        # Oracle NUMBER
        if ora_type_num == ORA_TYPE_NUM_NUMBER:
            return convert_number_to_python_decimal(&data.buffer)

    # Python float
    elif py_type_num == PY_TYPE_NUM_FLOAT:

        # Oracle NUMBER
        if ora_type_num == ORA_TYPE_NUM_NUMBER:
            return convert_number_to_python_float(&data.buffer)

        # Oracle BINARY_DOUBLE
        elif ora_type_num == ORA_TYPE_NUM_BINARY_DOUBLE:
            return data.buffer.as_double

        # Oracle BINARY_FLOAT
        elif ora_type_num == ORA_TYPE_NUM_BINARY_FLOAT:
            return data.buffer.as_float

        # Oracle CHAR, LONG, VARCHAR
        elif ora_type_num in (
            ORA_TYPE_NUM_CHAR,
            ORA_TYPE_NUM_LONG,
            ORA_TYPE_NUM_VARCHAR
        ):
            rb = &data.buffer.as_raw_bytes
            return float(rb.ptr[:rb.num_bytes])

    # Python datetime.datetime
    elif py_type_num == PY_TYPE_NUM_DATETIME:

        # Oracle DATE, TIMESTAMP, TIMESTAMP WITH LOCAL TIMEZONE,
        # TIMESTAMP WITH TIMEZONE
        if ora_type_num in (
            ORA_TYPE_NUM_DATE,
            ORA_TYPE_NUM_TIMESTAMP,
            ORA_TYPE_NUM_TIMESTAMP_LTZ,
            ORA_TYPE_NUM_TIMESTAMP_TZ
        ):
            return convert_date_to_python(&data.buffer)

    # Python datetime.timedelta
    elif py_type_num == PY_TYPE_NUM_TIMEDELTA:

        # Oracle INTERVAL DAY TO SECOND
        if ora_type_num == ORA_TYPE_NUM_INTERVAL_DS:
            return convert_interval_ds_to_python(&data.buffer)

    # Python oracledb.OracleIntervalYM
    elif py_type_num == PY_TYPE_NUM_ORACLE_INTERVAL_YM:

        # Oracle INTERVAL YEAR TO MONTH
        if ora_type_num == ORA_TYPE_NUM_INTERVAL_YM:
            return convert_interval_ym_to_python(&data.buffer)

    # Python boolean
    elif py_type_num == PY_TYPE_NUM_BOOL:

        # Oracle BOOLEAN
        if ora_type_num == ORA_TYPE_NUM_BOOLEAN:
            return data.buffer.as_bool

    errors._raise_err(errors.ERR_INCONSISTENT_DATATYPES,
                      input_type=from_metadata.dbtype.name,
                      output_type=to_metadata.dbtype.name)
