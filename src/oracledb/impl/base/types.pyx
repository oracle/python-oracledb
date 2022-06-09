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
# types.pyx
#
# Cython file defining the API types mandated by the Python Database API as
# well as the database types specific to Oracle (embedded in base_impl.pyx).
#------------------------------------------------------------------------------

cdef class ApiType:

    def __init__(self, name, *dbtypes):
        self.name = name
        self.dbtypes = dbtypes

    def __eq__(self, other):
        if isinstance(other, DbType):
            return other in self.dbtypes
        return NotImplemented

    def __hash__(self):
        return hash(self.name)

    def __reduce__(self):
        return self.name

    def __repr__(self):
        return f"<ApiType {self.name}>"


cdef dict db_type_by_num = {}
cdef dict db_type_by_ora_type_num = {}

cdef class DbType:

    def __init__(self, num, name, ora_type_num, default_size=0, csfrm=0,
                 buffer_size_factor=0):
        cdef uint16_t ora_type_key = csfrm * 256 + ora_type_num
        self.num = num
        self.name = name
        self.default_size = default_size
        self._ora_type_num = ora_type_num
        self._csfrm = csfrm
        self._buffer_size_factor = buffer_size_factor
        db_type_by_num[num] = self
        db_type_by_ora_type_num[ora_type_key] = self

    def __reduce__(self):
        return self.name

    def __repr__(self):
        return f"<DbType {self.name}>"

    @staticmethod
    cdef DbType _from_num(uint32_t num):
        try:
            return db_type_by_num[num]
        except KeyError:
            pass
        errors._raise_err(errors.ERR_ORACLE_TYPE_NOT_SUPPORTED, num=num)

    @staticmethod
    cdef DbType _from_ora_type_and_csfrm(uint8_t ora_type_num, uint8_t csfrm):
        cdef uint16_t ora_type_key = csfrm * 256 + ora_type_num
        try:
            return db_type_by_ora_type_num[ora_type_key]
        except KeyError:
            pass
        errors._raise_err(errors.ERR_ORACLE_TYPE_NOT_SUPPORTED,
                          num=ora_type_num)


# database types
DB_TYPE_BFILE = DbType(DB_TYPE_NUM_BFILE, "DB_TYPE_BFILE", 114)
DB_TYPE_BINARY_DOUBLE = DbType(DB_TYPE_NUM_BINARY_DOUBLE,
                               "DB_TYPE_BINARY_DOUBLE", 101,
                               buffer_size_factor=8)
DB_TYPE_BINARY_FLOAT = DbType(DB_TYPE_NUM_BINARY_FLOAT, "DB_TYPE_BINARY_FLOAT",
                              100, buffer_size_factor=4)
DB_TYPE_BINARY_INTEGER = DbType(DB_TYPE_NUM_BINARY_INTEGER,
                                "DB_TYPE_BINARY_INTEGER", 3,
                                buffer_size_factor=22)
DB_TYPE_BLOB = DbType(DB_TYPE_NUM_BLOB, "DB_TYPE_BLOB", 113,
                      buffer_size_factor=112)
DB_TYPE_BOOLEAN = DbType(DB_TYPE_NUM_BOOLEAN, "DB_TYPE_BOOLEAN", 252,
                         buffer_size_factor=4)
DB_TYPE_CHAR = DbType(DB_TYPE_NUM_CHAR, "DB_TYPE_CHAR", 96, 2000, csfrm=1,
                      buffer_size_factor=4)
DB_TYPE_CLOB = DbType(DB_TYPE_NUM_CLOB, "DB_TYPE_CLOB", 112, csfrm=1,
                      buffer_size_factor=112)
DB_TYPE_CURSOR = DbType(DB_TYPE_NUM_CURSOR, "DB_TYPE_CURSOR", 102,
                        buffer_size_factor=4)
DB_TYPE_DATE = DbType(DB_TYPE_NUM_DATE, "DB_TYPE_DATE", 12,
                      buffer_size_factor=7)
DB_TYPE_INTERVAL_DS = DbType(DB_TYPE_NUM_INTERVAL_DS, "DB_TYPE_INTERVAL_DS",
                             183, buffer_size_factor=11)
DB_TYPE_INTERVAL_YM = DbType(DB_TYPE_NUM_INTERVAL_YM, "DB_TYPE_INTERVAL_YM",
                             182)
DB_TYPE_JSON = DbType(DB_TYPE_NUM_JSON, "DB_TYPE_JSON", 119)
DB_TYPE_LONG = DbType(DB_TYPE_NUM_LONG_VARCHAR, "DB_TYPE_LONG", 8, csfrm=1,
                      buffer_size_factor=2147483647)
DB_TYPE_LONG_NVARCHAR = DbType(DB_TYPE_NUM_LONG_NVARCHAR,
                               "DB_TYPE_LONG_NVARCHAR", 8, csfrm=2,
                               buffer_size_factor=2147483647)
DB_TYPE_LONG_RAW = DbType(DB_TYPE_NUM_LONG_RAW, "DB_TYPE_LONG_RAW", 24,
                          buffer_size_factor=2147483647)
DB_TYPE_NCHAR = DbType(DB_TYPE_NUM_NCHAR, "DB_TYPE_NCHAR", 96, 2000, csfrm=2,
                       buffer_size_factor=4)
DB_TYPE_NCLOB = DbType(DB_TYPE_NUM_NCLOB, "DB_TYPE_NCLOB", 112, csfrm=2,
                       buffer_size_factor=112)
DB_TYPE_NUMBER = DbType(DB_TYPE_NUM_NUMBER, "DB_TYPE_NUMBER", 2,
                        buffer_size_factor=22)
DB_TYPE_NVARCHAR = DbType(DB_TYPE_NUM_NVARCHAR, "DB_TYPE_NVARCHAR", 1, 4000,
                          csfrm=2, buffer_size_factor=4)
DB_TYPE_OBJECT = DbType(DB_TYPE_NUM_OBJECT, "DB_TYPE_OBJECT", 109)
DB_TYPE_RAW = DbType(DB_TYPE_NUM_RAW, "DB_TYPE_RAW", 23, 4000,
                     buffer_size_factor=1)
DB_TYPE_ROWID = DbType(DB_TYPE_NUM_ROWID, "DB_TYPE_ROWID", 11,
                       buffer_size_factor=18)
DB_TYPE_TIMESTAMP = DbType(DB_TYPE_NUM_TIMESTAMP, "DB_TYPE_TIMESTAMP", 180,
                           buffer_size_factor=11)
DB_TYPE_TIMESTAMP_LTZ = DbType(DB_TYPE_NUM_TIMESTAMP_LTZ,
                               "DB_TYPE_TIMESTAMP_LTZ", 231,
                               buffer_size_factor=11)
DB_TYPE_TIMESTAMP_TZ = DbType(DB_TYPE_NUM_TIMESTAMP_TZ, "DB_TYPE_TIMESTAMP_TZ",
                              181, buffer_size_factor=13)
DB_TYPE_UROWID = DbType(DB_TYPE_NUM_UROWID, "DB_TYPE_UROWID", 208)
DB_TYPE_VARCHAR = DbType(DB_TYPE_NUM_VARCHAR, "DB_TYPE_VARCHAR", 1, 4000,
                         csfrm=1, buffer_size_factor=4)

# DB API types
BINARY = ApiType("BINARY", DB_TYPE_RAW, DB_TYPE_LONG_RAW)
DATETIME = ApiType("DATETIME", DB_TYPE_DATE, DB_TYPE_TIMESTAMP,
                   DB_TYPE_TIMESTAMP_LTZ, DB_TYPE_TIMESTAMP_TZ)
NUMBER = ApiType("NUMBER", DB_TYPE_NUMBER, DB_TYPE_BINARY_DOUBLE,
                 DB_TYPE_BINARY_FLOAT, DB_TYPE_BINARY_INTEGER)
ROWID = ApiType("ROWID", DB_TYPE_ROWID, DB_TYPE_UROWID)
STRING = ApiType("STRING", DB_TYPE_VARCHAR, DB_TYPE_NVARCHAR, DB_TYPE_CHAR,
                 DB_TYPE_NCHAR, DB_TYPE_LONG)
