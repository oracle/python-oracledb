# -----------------------------------------------------------------------------
# setup_tutorial.py (Setup Section)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
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

import oracledb
import db_config
import run_sql_script

# Connect using the tutorial username and password
con = oracledb.connect(
    user=db_config.user, password=db_config.pw, dsn=db_config.dsn
)

# create sample schemas and definitions for the tutorial
print("Setting up the sample tables and other DB objects for the tutorial...")
run_sql_script.run_sql_script(
    con, "setup_tutorial", user=db_config.user, pw=db_config.pw
)
print("Done.")
