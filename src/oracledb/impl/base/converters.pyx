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

cdef object convert_arrow_to_oracle_data(OracleMetadata metadata,
                                         OracleData* data,
                                         ArrowArrayImpl array_impl,
                                         ssize_t array_index):
    """
    Converts the value stored in Arrow format to an OracleData structure.
    """
    cdef:
        int64_t int_value, days, seconds, useconds
        SparseVectorImpl sparse_impl
        uint32_t db_type_num
        ArrowType arrow_type
        uint64_t uint_value
        OracleRawBytes* rb
        tuple sparse_info
        bytes temp_bytes
        ssize_t buf_len
        char buf[21]

    arrow_type = metadata._schema_impl.arrow_type
    db_type_num = metadata.dbtype.num
    if arrow_type in (
        NANOARROW_TYPE_INT8,
        NANOARROW_TYPE_INT16,
        NANOARROW_TYPE_INT32,
        NANOARROW_TYPE_INT64,
    ):
        array_impl.get_int(arrow_type, array_index, &data.is_null, &int_value)
        if not data.is_null:
            buf_len = PyOS_snprintf(buf, sizeof(buf), "%lld", int_value)
            temp_bytes = buf[:buf_len]
            convert_bytes_to_oracle_data(&data.buffer, temp_bytes)
            return temp_bytes
    elif arrow_type in (
        NANOARROW_TYPE_UINT8,
        NANOARROW_TYPE_UINT16,
        NANOARROW_TYPE_UINT32,
        NANOARROW_TYPE_UINT64,
    ):
        array_impl.get_uint(arrow_type, array_index, &data.is_null, &uint_value)
        if not data.is_null:
            buf_len = PyOS_snprintf(buf, sizeof(buf), "%llu", uint_value)
            temp_bytes = buf[:buf_len]
            convert_bytes_to_oracle_data(&data.buffer, temp_bytes)
            return temp_bytes
    elif arrow_type == NANOARROW_TYPE_DOUBLE:
        array_impl.get_double(array_index, &data.is_null,
                              &data.buffer.as_double)
        if db_type_num == DB_TYPE_NUM_NUMBER:
            temp_bytes = str(data.buffer.as_double).encode()
            convert_bytes_to_oracle_data(&data.buffer, temp_bytes)
            return temp_bytes
        elif db_type_num == DB_TYPE_NUM_BINARY_FLOAT:
            data.buffer.as_float = <float> data.buffer.as_double
    elif arrow_type == NANOARROW_TYPE_FLOAT:
        array_impl.get_float(array_index, &data.is_null, &data.buffer.as_float)
        if db_type_num == DB_TYPE_NUM_NUMBER:
            temp_bytes = str(data.buffer.as_float).encode()
            convert_bytes_to_oracle_data(&data.buffer, temp_bytes)
            return temp_bytes
        elif db_type_num == DB_TYPE_NUM_BINARY_DOUBLE:
            data.buffer.as_double = <double> data.buffer.as_float
    elif arrow_type == NANOARROW_TYPE_BOOL:
        array_impl.get_bool(array_index, &data.is_null, &data.buffer.as_bool)
    elif arrow_type in (
            NANOARROW_TYPE_BINARY,
            NANOARROW_TYPE_STRING,
            NANOARROW_TYPE_FIXED_SIZE_BINARY,
            NANOARROW_TYPE_LARGE_BINARY,
            NANOARROW_TYPE_LARGE_STRING
    ):
        rb = &data.buffer.as_raw_bytes
        array_impl.get_bytes(array_index, &data.is_null, <char**> &rb.ptr,
                             &rb.num_bytes)
        if rb.num_bytes == 0:
            data.is_null = True
        elif db_type_num == DB_TYPE_NUM_LONG_NVARCHAR:
            temp_bytes = rb.ptr[:rb.num_bytes].decode().encode(ENCODING_UTF16)
            convert_bytes_to_oracle_data(&data.buffer, temp_bytes)
            return temp_bytes
    elif arrow_type in (NANOARROW_TYPE_TIMESTAMP, NANOARROW_TYPE_DATE64):
        array_impl.get_int(arrow_type, array_index, &data.is_null, &int_value)
        if not data.is_null:
            seconds = int_value // array_impl.schema_impl.time_factor
            useconds = int_value % array_impl.schema_impl.time_factor
            days = seconds // (24 * 60 * 60)
            seconds = seconds % (24 * 60 * 60)
            if array_impl.schema_impl.time_factor == 1_000:
                useconds *= 1_000
            elif array_impl.schema_impl.time_factor == 1_000_000_000:
                useconds //= 1_000
            return EPOCH_DATE + \
                    cydatetime.timedelta_new(days, seconds, useconds)
    elif arrow_type == NANOARROW_TYPE_DATE32:
        array_impl.get_int(arrow_type, array_index, &data.is_null, &int_value)
        if not data.is_null:
            return EPOCH_DATE + cydatetime.timedelta_new(int_value, 0, 0)
    elif arrow_type == NANOARROW_TYPE_DECIMAL128:
        temp_bytes = array_impl.get_decimal(array_index, &data.is_null)
        if not data.is_null:
            convert_bytes_to_oracle_data(&data.buffer, temp_bytes)
            return temp_bytes
    elif arrow_type in (NANOARROW_TYPE_LIST, NANOARROW_TYPE_FIXED_SIZE_LIST):
        return array_impl.get_vector(array_index, &data.is_null)
    elif arrow_type == NANOARROW_TYPE_STRUCT:
        sparse_info = array_impl.get_sparse_vector(array_index, &data.is_null)
        if sparse_info is not None:
            sparse_impl = SparseVectorImpl.__new__(SparseVectorImpl)
            sparse_impl.num_dimensions = sparse_info[0]
            sparse_impl.indices = sparse_info[1]
            sparse_impl.values = sparse_info[2]
            return PY_TYPE_SPARSE_VECTOR._from_impl(sparse_impl)


cdef cydatetime.datetime convert_date_to_python(OracleDataBuffer *buffer):
    """
    Converts a DATE, TIMESTAMP, TIMESTAMP WITH LOCAL TIME ZONE or TIMESTAMP
    WITH TIMEZONE value stored in the buffer to Python datetime.datetime().
    """
    cdef:
        OracleDate *value = &buffer.as_date
        cydatetime.datetime output
        int32_t seconds
    output = cydatetime.datetime_new(value.year, value.month, value.day,
                                     value.hour, value.minute, value.second,
                                     value.fsecond, None)
    if value.tz_hour_offset != 0 or value.tz_minute_offset != 0:
        seconds = value.tz_hour_offset * 3600 + value.tz_minute_offset * 60
        output += cydatetime.timedelta_new(0, seconds, 0)
    return output


cdef int convert_date_to_arrow_date32(ArrowArrayImpl array_impl,
                                      OracleDataBuffer *buffer) except -1:
    """
    Converts a DATE, TIMESTAMP, TIMESTAMP WITH LOCAL TIME ZONE or TIMESTMP
    WITH TIMEZONE value stored in the buffer to Arrow date32.
    """
    cdef:
        cydatetime.timedelta td
        cydatetime.datetime dt
        int32_t days
    dt = convert_date_to_python(buffer)
    td = dt - EPOCH_DATE
    days = td.days
    array_impl.append_int(days)


cdef int convert_date_to_arrow_timestamp(ArrowArrayImpl array_impl,
                                         OracleDataBuffer *buffer) except -1:
    """
    Converts a DATE, TIMESTAMP, TIMESTAMP WITH LOCAL TIME ZONE or TIMESTAMP
    WITH TIMEZONE value stored in the buffer to Arrow timestamp.
    """
    cdef:
        cydatetime.timedelta td
        cydatetime.datetime dt
        int64_t ts, us
    dt = convert_date_to_python(buffer)
    td = dt - EPOCH_DATE
    ts = (<int64_t> cydatetime.timedelta_days(td)) * (24 * 60 * 60) + \
            cydatetime.timedelta_seconds(td)
    ts *= array_impl.schema_impl.time_factor
    us = cydatetime.timedelta_microseconds(td)
    if array_impl.schema_impl.time_factor == 1_000:
        ts += us // 1_000
    elif array_impl.schema_impl.time_factor == 1_000_000:
        ts += us
    elif array_impl.schema_impl.time_factor != 1:
        ts += us * 1_000
    array_impl.append_int(ts)


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


cdef int convert_number_to_arrow_decimal(ArrowArrayImpl array_impl,
                                         OracleDataBuffer *buffer) except -1:
    """
    Converts a NUMBER value stored in the buffer to Arrow DECIMAL128.
    """
    cdef:
        OracleNumber *value = &buffer.as_number
        uint8_t num_digits, allowed_max_chars
        char_type digits[40]
        uint8_t actual_scale

    # determine if the number can be represented as an Arrow decimal128 value
    # only 38 decimal digits are permitted (excluding the sign and decimal
    # point)
    allowed_max_chars = 38
    if value.chars[0] == b'-':
        allowed_max_chars += 1
    if not value.is_integer:
        allowed_max_chars += 1
    if value.is_max_negative_value or value.num_chars > allowed_max_chars:
        raise ValueError("Value cannot be represented as Arrow Decimal128")

    # integers can be handled directly
    if value.is_integer and array_impl.schema_impl.scale == 0:
        return array_impl.append_decimal(value.chars, value.num_chars)

    # Arrow expects a string of digits without the decimal point; if the number
    # does not contain at least the number of digits after the decimal point
    # required by the scale of the Arrow array, zeros are appended
    if value.is_integer:
        actual_scale = 0
        num_digits = value.num_chars
    else:
        actual_scale = 0
        while True:
            num_digits = value.num_chars - actual_scale - 1
            if value.chars[num_digits] == b'.':
                break
            actual_scale += 1
    memcpy(digits, value.chars, num_digits)
    if actual_scale > 0:
        memcpy(&digits[num_digits], &value.chars[num_digits + 1], actual_scale)
        num_digits += actual_scale
    while actual_scale < array_impl.schema_impl.scale:
        digits[num_digits] = b'0'
        num_digits += 1
        actual_scale += 1
    array_impl.append_decimal(digits, num_digits)


cdef int convert_number_to_arrow_double(ArrowArrayImpl array_impl,
                                        OracleDataBuffer *buffer) except -1:
    """
    Converts a NUMBER value stored in the buffer to Arrow DOUBLE.
    """
    cdef:
        OracleNumber *value = &buffer.as_number
        double double_value
    if value.is_max_negative_value:
        array_impl.append_double(-1.0e126)
    else:
        errno.errno = 0
        double_value = strtod((<const char*> value.chars), NULL)
        if errno.errno != 0:
            errors._raise_err(errors.ERR_CANNOT_CONVERT_TO_ARROW_DOUBLE,
                              value=value.chars[:value.num_chars].decode())
        array_impl.append_double(double_value)


cdef int convert_number_to_arrow_float(ArrowArrayImpl array_impl,
                                       OracleDataBuffer *buffer) except -1:
    """
    Converts a NUMBER value stored in the buffer to Arrow float
    """
    cdef:
        OracleNumber *value = &buffer.as_number
        float float_value
    if value.is_max_negative_value:
        array_impl.append_float(-1.0e126)
    else:
        errno.errno = 0
        float_value = strtof((<const char*> value.chars), NULL)
        if errno.errno != 0:
            errors._raise_err(errors.ERR_CANNOT_CONVERT_TO_ARROW_FLOAT,
                              value=value.chars[:value.num_chars].decode())
        array_impl.append_float(float_value)


cdef int convert_number_to_arrow_int(ArrowArrayImpl array_impl,
                                     OracleDataBuffer *buffer) except -1:
    """
    Converts a NUMBER value stored in the buffer to an Arrow integer.
    """
    cdef:
        OracleNumber *value = &buffer.as_number
        int64_t int64_value
    errno.errno = 0
    int64_value = strtoll((<const char*> value.chars), NULL, 0)
    if errno.errno != 0:
        errors._raise_err(errors.ERR_CANNOT_CONVERT_TO_ARROW_INTEGER,
                          value=value.chars[:value.num_chars].decode())
    array_impl.append_int(int64_value)


cdef int convert_number_to_arrow_uint(ArrowArrayImpl array_impl,
                                      OracleDataBuffer *buffer) except -1:
    """
    Converts a NUMBER value stored in the buffer to an Arrow unsigned integer.
    """
    cdef:
        OracleNumber *value = &buffer.as_number
        uint64_t uint64_value
    errno.errno = 0
    uint64_value = strtoull((<const char*> value.chars), NULL, 0)
    if errno.errno != 0:
        errors._raise_err(errors.ERR_CANNOT_CONVERT_TO_ARROW_INTEGER,
                          value=value.chars[:value.num_chars].decode())
    array_impl.append_uint(uint64_value)


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


cdef int convert_bytes_to_oracle_data(OracleDataBuffer *buffer,
                                      bytes value) except -1:
    """
    Converts Python bytes to the format required by the OracleDataBuffer.
    """
    cdef OracleRawBytes *rb = &buffer.as_raw_bytes
    cpython.PyBytes_AsStringAndSize(value, <char**> &rb.ptr, &rb.num_bytes)


cdef int convert_str_to_arrow(ArrowArrayImpl array_impl,
                              OracleDataBuffer *buffer) except -1:
    """
    Converts a CHAR, NCHAR, LONG, VARCHAR, or NVARCHAR value stored in the
    buffer to an Arrow string.
    """
    cdef OracleRawBytes *rb = &buffer.as_raw_bytes
    array_impl.append_bytes(<void*> rb.ptr, rb.num_bytes)


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
                                      ArrowArrayImpl array_impl) except -1:
    """
    Converts the value stored in OracleData to Arrow format.
    """
    cdef:
        ArrowType arrow_type
        uint32_t db_type_num

    # NULL values
    if data.is_null:
        return array_impl.append_null()

    arrow_type = to_metadata._schema_impl.arrow_type
    db_type_num = from_metadata.dbtype.num
    if arrow_type in (
        NANOARROW_TYPE_INT8,
        NANOARROW_TYPE_INT16,
        NANOARROW_TYPE_INT32,
        NANOARROW_TYPE_INT64,
    ):
        convert_number_to_arrow_int(array_impl, &data.buffer)
    elif arrow_type in (
        NANOARROW_TYPE_UINT8,
        NANOARROW_TYPE_UINT16,
        NANOARROW_TYPE_UINT32,
        NANOARROW_TYPE_UINT64,
    ):
        convert_number_to_arrow_uint(array_impl, &data.buffer)
    elif arrow_type == NANOARROW_TYPE_DOUBLE:
        if db_type_num == DB_TYPE_NUM_NUMBER:
            convert_number_to_arrow_double(array_impl, &data.buffer)
        elif db_type_num == DB_TYPE_NUM_BINARY_FLOAT:
            array_impl.append_float(data.buffer.as_float)
        else:
            array_impl.append_double(data.buffer.as_double)
    elif arrow_type == NANOARROW_TYPE_FLOAT:
        if db_type_num == DB_TYPE_NUM_NUMBER:
            convert_number_to_arrow_float(array_impl, &data.buffer)
        elif db_type_num == DB_TYPE_NUM_BINARY_DOUBLE:
            array_impl.append_double(data.buffer.as_double)
        else:
            array_impl.append_float(data.buffer.as_float)
    elif arrow_type == NANOARROW_TYPE_BOOL:
        array_impl.append_int(data.buffer.as_bool)
    elif arrow_type in (
        NANOARROW_TYPE_BINARY,
        NANOARROW_TYPE_STRING,
        NANOARROW_TYPE_FIXED_SIZE_BINARY,
        NANOARROW_TYPE_LARGE_BINARY,
        NANOARROW_TYPE_LARGE_STRING
    ):
        convert_str_to_arrow(array_impl, &data.buffer)
    elif arrow_type in (
        NANOARROW_TYPE_DATE64,
        NANOARROW_TYPE_TIMESTAMP
    ):
        convert_date_to_arrow_timestamp(array_impl, &data.buffer)
    elif arrow_type == NANOARROW_TYPE_DATE32:
        convert_date_to_arrow_date32(array_impl, &data.buffer)
    elif arrow_type == NANOARROW_TYPE_DECIMAL128:
        convert_number_to_arrow_decimal(array_impl, &data.buffer)


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


cdef object convert_python_to_oracle_data(OracleMetadata metadata,
                                          OracleData* data,
                                          object value):
    """
    Converts a Python value to the OracleData structure. The object returned is
    any temporary object that is required to be retained (if any).
    """
    cdef:
        uint8_t ora_type_num = metadata.dbtype._ora_type_num
        bytes temp_bytes
    data.is_null = value is None
    if data.is_null:
        return None
    elif ora_type_num in (ORA_TYPE_NUM_VARCHAR,
                          ORA_TYPE_NUM_CHAR,
                          ORA_TYPE_NUM_LONG):
        if metadata.dbtype._csfrm == CS_FORM_IMPLICIT:
            temp_bytes = (<str> value).encode()
        else:
            temp_bytes = (<str> value).encode(ENCODING_UTF16)
        convert_bytes_to_oracle_data(&data.buffer, temp_bytes)
        if data.buffer.as_raw_bytes.num_bytes == 0:
            data.is_null = True
        return temp_bytes
    elif ora_type_num in (ORA_TYPE_NUM_RAW, ORA_TYPE_NUM_LONG_RAW):
        convert_bytes_to_oracle_data(&data.buffer, value)
    elif ora_type_num in (ORA_TYPE_NUM_NUMBER, ORA_TYPE_NUM_BINARY_INTEGER):
        if isinstance(value, bool):
            return b'1' if value is True else b'0'
        return (<str> cpython.PyObject_Str(value)).encode()
    elif ora_type_num == ORA_TYPE_NUM_BINARY_FLOAT:
        data.buffer.as_float = value
    elif ora_type_num == ORA_TYPE_NUM_BINARY_DOUBLE:
        data.buffer.as_double = value
    elif ora_type_num == ORA_TYPE_NUM_BOOLEAN:
        data.buffer.as_bool = value
    return value


cdef int convert_vector_to_arrow(ArrowArrayImpl array_impl,
                                 object vector) except -1:
    """
    Converts the vector to the format required by the Arrow array.
    """
    if vector is None:
        array_impl.append_null()
    elif isinstance(vector, PY_TYPE_SPARSE_VECTOR):
        array_impl.append_sparse_vector(vector.num_dimensions,
                                         <array.array> vector.indices,
                                         <array.array> vector.values)
    else:
        array_impl.append_vector(<array.array> vector)
