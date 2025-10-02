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

# -----------------------------------------------------------------------------
# dataframe_types.py
#
# Shows how to change the schema types and names of a dataframe
# -----------------------------------------------------------------------------

import pyarrow

import oracledb
import sample_env

# determine whether to use python-oracledb thin mode or thick mode
if sample_env.run_in_thick_mode():
    oracledb.init_oracle_client(lib_dir=sample_env.get_oracle_client())

connection = oracledb.connect(
    user=sample_env.get_main_user(),
    password=sample_env.get_main_password(),
    dsn=sample_env.get_connect_string(),
    params=sample_env.get_connect_params(),
)


SQL = "select * from SampleQueryTab where id < 5"

# Default fetch with no type mapping

odf = connection.fetch_df_all(SQL)
tab = pyarrow.table(odf)
print("Default Output:", tab)

# Fetching with an explicit schema

schema = pyarrow.schema(
    [("COL_1", pyarrow.int16()), ("COL_2", pyarrow.string())]
)
odf = connection.fetch_df_all(SQL, requested_schema=schema)
tab = pyarrow.table(odf)
print("\nNew Output:", tab)
