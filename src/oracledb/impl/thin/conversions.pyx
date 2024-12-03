#------------------------------------------------------------------------------
# Copyright (c) 2021, 2023, Oracle and/or its affiliates.
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
# conversions.pyx
#
# Cython file defining the conversions between data types that are supported by
# the thin client (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

cdef converter_dict = {
    (ORA_TYPE_NUM_CHAR, ORA_TYPE_NUM_NUMBER): float,
    (ORA_TYPE_NUM_VARCHAR, ORA_TYPE_NUM_NUMBER): float,
    (ORA_TYPE_NUM_LONG, ORA_TYPE_NUM_NUMBER): float,
    (ORA_TYPE_NUM_BINARY_INTEGER, ORA_TYPE_NUM_NUMBER):float,
    (ORA_TYPE_NUM_CHAR, ORA_TYPE_NUM_BINARY_INTEGER):_to_binary_int,
    (ORA_TYPE_NUM_VARCHAR, ORA_TYPE_NUM_BINARY_INTEGER): _to_binary_int,
    (ORA_TYPE_NUM_LONG, ORA_TYPE_NUM_BINARY_INTEGER): _to_binary_int,
    (ORA_TYPE_NUM_NUMBER, ORA_TYPE_NUM_BINARY_INTEGER): _to_binary_int,
    (ORA_TYPE_NUM_BINARY_FLOAT, ORA_TYPE_NUM_BINARY_INTEGER): _to_binary_int,
    (ORA_TYPE_NUM_BINARY_DOUBLE, ORA_TYPE_NUM_BINARY_INTEGER): _to_binary_int,
    (ORA_TYPE_NUM_DATE, ORA_TYPE_NUM_CHAR): str,
    (ORA_TYPE_NUM_DATE, ORA_TYPE_NUM_VARCHAR): str,
    (ORA_TYPE_NUM_DATE, ORA_TYPE_NUM_LONG): str,
    (ORA_TYPE_NUM_NUMBER, ORA_TYPE_NUM_VARCHAR): PY_TYPE_NUM_STR,
    (ORA_TYPE_NUM_NUMBER, ORA_TYPE_NUM_CHAR): PY_TYPE_NUM_STR,
    (ORA_TYPE_NUM_NUMBER, ORA_TYPE_NUM_LONG): PY_TYPE_NUM_STR,
    (ORA_TYPE_NUM_BINARY_DOUBLE, ORA_TYPE_NUM_VARCHAR): str,
    (ORA_TYPE_NUM_BINARY_FLOAT, ORA_TYPE_NUM_VARCHAR): str,
    (ORA_TYPE_NUM_BINARY_DOUBLE, ORA_TYPE_NUM_CHAR): str,
    (ORA_TYPE_NUM_BINARY_FLOAT, ORA_TYPE_NUM_CHAR): str,
    (ORA_TYPE_NUM_BINARY_DOUBLE, ORA_TYPE_NUM_LONG): str,
    (ORA_TYPE_NUM_BINARY_FLOAT, ORA_TYPE_NUM_LONG): str,
    (ORA_TYPE_NUM_TIMESTAMP, ORA_TYPE_NUM_VARCHAR): str,
    (ORA_TYPE_NUM_TIMESTAMP, ORA_TYPE_NUM_CHAR): str,
    (ORA_TYPE_NUM_TIMESTAMP, ORA_TYPE_NUM_LONG): str,
    (ORA_TYPE_NUM_TIMESTAMP_TZ, ORA_TYPE_NUM_VARCHAR): str,
    (ORA_TYPE_NUM_TIMESTAMP_TZ, ORA_TYPE_NUM_CHAR): str,
    (ORA_TYPE_NUM_TIMESTAMP_TZ, ORA_TYPE_NUM_LONG): str,
    (ORA_TYPE_NUM_TIMESTAMP_LTZ, ORA_TYPE_NUM_VARCHAR): str,
    (ORA_TYPE_NUM_TIMESTAMP_LTZ, ORA_TYPE_NUM_CHAR): str,
    (ORA_TYPE_NUM_TIMESTAMP_LTZ, ORA_TYPE_NUM_LONG): str,
    (ORA_TYPE_NUM_ROWID, ORA_TYPE_NUM_VARCHAR): str,
    (ORA_TYPE_NUM_ROWID, ORA_TYPE_NUM_CHAR): str,
    (ORA_TYPE_NUM_ROWID, ORA_TYPE_NUM_LONG): str,
    (ORA_TYPE_NUM_INTERVAL_DS, ORA_TYPE_NUM_VARCHAR): str,
    (ORA_TYPE_NUM_INTERVAL_DS, ORA_TYPE_NUM_CHAR): str,
    (ORA_TYPE_NUM_INTERVAL_DS, ORA_TYPE_NUM_LONG): str,
    (ORA_TYPE_NUM_BINARY_INTEGER, ORA_TYPE_NUM_VARCHAR): str,
    (ORA_TYPE_NUM_BINARY_INTEGER, ORA_TYPE_NUM_CHAR): str,
    (ORA_TYPE_NUM_BINARY_INTEGER, ORA_TYPE_NUM_LONG): str,
    (ORA_TYPE_NUM_TIMESTAMP, ORA_TYPE_NUM_DATE): _tstamp_to_date,
    (ORA_TYPE_NUM_TIMESTAMP_TZ, ORA_TYPE_NUM_DATE): _tstamp_to_date,
    (ORA_TYPE_NUM_TIMESTAMP_LTZ, ORA_TYPE_NUM_DATE): _tstamp_to_date,
    (ORA_TYPE_NUM_NUMBER, ORA_TYPE_NUM_BINARY_DOUBLE): PY_TYPE_NUM_FLOAT,
    (ORA_TYPE_NUM_BINARY_FLOAT, ORA_TYPE_NUM_BINARY_DOUBLE): float,
    (ORA_TYPE_NUM_CHAR, ORA_TYPE_NUM_BINARY_DOUBLE): float,
    (ORA_TYPE_NUM_VARCHAR, ORA_TYPE_NUM_BINARY_DOUBLE): float,
    (ORA_TYPE_NUM_LONG, ORA_TYPE_NUM_BINARY_DOUBLE): float,
    (ORA_TYPE_NUM_NUMBER, ORA_TYPE_NUM_BINARY_FLOAT): PY_TYPE_NUM_FLOAT,
    (ORA_TYPE_NUM_BINARY_DOUBLE, ORA_TYPE_NUM_BINARY_FLOAT): float,
    (ORA_TYPE_NUM_CHAR, ORA_TYPE_NUM_BINARY_FLOAT): float,
    (ORA_TYPE_NUM_VARCHAR, ORA_TYPE_NUM_BINARY_FLOAT): float,
    (ORA_TYPE_NUM_LONG, ORA_TYPE_NUM_BINARY_FLOAT): float,
    (ORA_TYPE_NUM_BINARY_FLOAT, ORA_TYPE_NUM_NUMBER): float,
    (ORA_TYPE_NUM_BINARY_DOUBLE, ORA_TYPE_NUM_NUMBER): float,
    (ORA_TYPE_NUM_BLOB, ORA_TYPE_NUM_LONG_RAW): ORA_TYPE_NUM_LONG_RAW,
    (ORA_TYPE_NUM_BLOB, ORA_TYPE_NUM_RAW): ORA_TYPE_NUM_LONG_RAW,
    (ORA_TYPE_NUM_CLOB, ORA_TYPE_NUM_CHAR): ORA_TYPE_NUM_LONG,
    (ORA_TYPE_NUM_CLOB, ORA_TYPE_NUM_VARCHAR): ORA_TYPE_NUM_LONG,
    (ORA_TYPE_NUM_CLOB, ORA_TYPE_NUM_LONG): ORA_TYPE_NUM_LONG,
    (ORA_TYPE_NUM_JSON, ORA_TYPE_NUM_VARCHAR): ORA_TYPE_NUM_LONG,
    (ORA_TYPE_NUM_JSON, ORA_TYPE_NUM_CHAR): ORA_TYPE_NUM_LONG,
    (ORA_TYPE_NUM_JSON, ORA_TYPE_NUM_RAW): ORA_TYPE_NUM_LONG_RAW,
    (ORA_TYPE_NUM_TIMESTAMP_TZ, ORA_TYPE_NUM_TIMESTAMP_LTZ): None,
    (ORA_TYPE_NUM_TIMESTAMP_TZ, ORA_TYPE_NUM_TIMESTAMP): None,
    (ORA_TYPE_NUM_TIMESTAMP_LTZ, ORA_TYPE_NUM_TIMESTAMP_TZ): None,
    (ORA_TYPE_NUM_TIMESTAMP_LTZ, ORA_TYPE_NUM_TIMESTAMP): None,
    (ORA_TYPE_NUM_TIMESTAMP, ORA_TYPE_NUM_TIMESTAMP_LTZ): None,
    (ORA_TYPE_NUM_TIMESTAMP, ORA_TYPE_NUM_TIMESTAMP_TZ): None,
    (ORA_TYPE_NUM_DATE, ORA_TYPE_NUM_TIMESTAMP_LTZ): None,
    (ORA_TYPE_NUM_DATE, ORA_TYPE_NUM_TIMESTAMP): None,
    (ORA_TYPE_NUM_DATE, ORA_TYPE_NUM_TIMESTAMP_TZ): None,
    (ORA_TYPE_NUM_CHAR, ORA_TYPE_NUM_VARCHAR): None,
    (ORA_TYPE_NUM_VARCHAR, ORA_TYPE_NUM_CHAR): None,
    (ORA_TYPE_NUM_LONG, ORA_TYPE_NUM_VARCHAR): None,
    (ORA_TYPE_NUM_LONG, ORA_TYPE_NUM_CHAR): None,
    (ORA_TYPE_NUM_VARCHAR, ORA_TYPE_NUM_LONG): None,
    (ORA_TYPE_NUM_CHAR, ORA_TYPE_NUM_LONG): None,
    (ORA_TYPE_NUM_VECTOR, ORA_TYPE_NUM_CLOB): ORA_TYPE_NUM_CLOB,
    (ORA_TYPE_NUM_VECTOR, ORA_TYPE_NUM_VARCHAR): ORA_TYPE_NUM_LONG,
    (ORA_TYPE_NUM_VECTOR, ORA_TYPE_NUM_CHAR): ORA_TYPE_NUM_LONG,
    (ORA_TYPE_NUM_VECTOR, ORA_TYPE_NUM_LONG): ORA_TYPE_NUM_LONG,
}

cdef object _to_binary_int(object fetch_value):
    return int(PY_TYPE_DECIMAL(fetch_value))

cdef object _tstamp_to_date(object fetch_value):
    return fetch_value.replace(microsecond=0)

cdef int conversion_helper(ThinVarImpl output_var,
                           OracleMetadata metadata) except -1:
    cdef:
        uint8_t fetch_ora_type_num, output_ora_type_num, csfrm
        object key, value

    fetch_ora_type_num = metadata.dbtype._ora_type_num
    output_ora_type_num = output_var.metadata.dbtype._ora_type_num
    if fetch_ora_type_num == output_ora_type_num:
        return 0

    key = (fetch_ora_type_num, output_ora_type_num)
    try:
        value = converter_dict[key]
        if isinstance(value, int):
            if fetch_ora_type_num == ORA_TYPE_NUM_NUMBER:
                output_var.metadata._py_type_num = value
            else:
                csfrm = output_var.metadata.dbtype._csfrm
                metadata.dbtype = DbType._from_ora_type_and_csfrm(value, csfrm)
        else:
            output_var._conv_func = value
    except:
        errors._raise_err(errors.ERR_INCONSISTENT_DATATYPES,
                          input_type=metadata.dbtype.name,
                          output_type=output_var.metadata.dbtype.name)
