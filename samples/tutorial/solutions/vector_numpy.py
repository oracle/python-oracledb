# -----------------------------------------------------------------------------
# vector_numpy.py (Section 9.3)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
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
# -----------------------------------------------------------------------------

import array
import numpy
import oracledb
import db_config

con = oracledb.connect(
    user=db_config.user, password=db_config.pw, dsn=db_config.dsn
)
cur = con.cursor()


# Convert from NumPy ndarray type to array type when inserting vectors
def numpy_converter_in(value):
    if value.dtype == numpy.float64:
        dtype = "d"
    elif value.dtype == numpy.float32:
        dtype = "f"
    elif value.dtype == numpy.uint8:
        dtype = "B"
    else:
        dtype = "b"
    return array.array(dtype, value)


def input_type_handler(cur, value, arraysize):
    if isinstance(value, numpy.ndarray):
        return cur.var(
            oracledb.DB_TYPE_VECTOR,
            arraysize=arraysize,
            inconverter=numpy_converter_in,
        )


con.inputtypehandler = input_type_handler


# Convert from array types to NumPy ndarray types when fetching vectors
def numpy_converter_out(value):
    return numpy.array(value, copy=False, dtype=value.typecode)


def output_type_handler(cur, metadata):
    if metadata.type_code is oracledb.DB_TYPE_VECTOR:
        return cur.var(
            metadata.type_code,
            arraysize=cur.arraysize,
            outconverter=numpy_converter_out,
        )


con.outputtypehandler = output_type_handler

# Insert
vector_data_64 = numpy.array([11.25, 11.75, 11.5], dtype=numpy.float64)

cur.execute(
    "insert into vtab (id, v64) values (:1, :2)",
    [202, vector_data_64],
)

# Each vector is represented as a numpy.ndarray type
for (v,) in cur.execute("select v64 from vtab"):
    print(v)
    print(type(v))
