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
# load_csv_direct_path.py
#
# A sample showing how to load CSV data using two methods:
#   - Direct Path Load of data read with Python's CSV module
#   - Direct Path Load of data from PyArrow dataframes
#
# This is related to load_csv.py but the CSV data file for Direct Path Load can
# only contain valid data.
#
# Direct Path Loads can be faster for very large data sets than the
# executemany() code shown in load_csv.py.
#
# To run the second example, install pyarrow:
#   python -m pip install pyarrow --upgrade
# -----------------------------------------------------------------------------

import csv
import os
import sys

import oracledb
import sample_env

# determine whether to use python-oracledb thin mode or thick mode
if sample_env.run_in_thick_mode():
    oracledb.init_oracle_client(lib_dir=sample_env.get_oracle_client())

# CSV file. This sample file has both valid rows
FILE_NAME = os.path.join("data", "load_csv_direct_path.csv")

# Adjust the number of rows to be inserted in each iteration to meet your
# memory and performance requirements. Typically this is a large-ish value to
# reduce the number of calls to executemany() or direct_path_load(). For this
# demo with a small CSV file, a small batch size is used to show the looping
# behavior of the code.
BATCH_SIZE = 19

connection = oracledb.connect(
    user=sample_env.get_main_user(),
    password=sample_env.get_main_password(),
    dsn=sample_env.get_connect_string(),
    params=sample_env.get_connect_params(),
)

# -----------------------------------------------------------------------------
# Loading with Python's CSV package using Direct Path Loads

print("\nDirect Path Load using Python's CSV module")


def process_batch_dpl(connection, batch_number, data):
    print("Processing batch", batch_number + 1)
    connection.direct_path_load(
        schema_name=sample_env.get_main_user(),
        table_name="LoadCsvTab",
        column_names=["id", "name"],
        data=data,
    )


with connection.cursor() as cursor:
    # Clean up the table for demonstration purposes
    cursor.execute("truncate table LoadCsvTab")

# Loop over the data and insert it in batches
with open(FILE_NAME, "r") as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=",")
    data = []
    batch_number = 0
    for line in csv_reader:
        data.append((float(line[0]), line[1]))
        if len(data) % BATCH_SIZE == 0:
            process_batch_dpl(connection, batch_number, data)
            data = []
            batch_number += 1
    if data:
        process_batch_dpl(connection, batch_number, data)

# Show how many rows were inserted
with connection.cursor() as cursor:
    cursor.execute("select count(*) from LoadCsvTab")
    (r,) = cursor.fetchone()
    print(f"\n{r} rows were inserted")

# -----------------------------------------------------------------------------
# Loading with PyArrow's CSV package using Direct Path Loads
#
# Using Direct Path Load in conjunction with PyArrow's CSV package can be the
# fastest way to load huge datasets.

try:
    import pyarrow.csv
except Exception:
    print("\nTo use pyarrow dataframes, install pyarrow.")
    sys.exit()

print("\nDirect Path Load using PyArrow's CSV module")

with connection.cursor() as cursor:
    # Clean up the table for demonstration purposes
    cursor.execute("truncate table LoadCsvTab")

# PyArrow uses a byte size for batching. For this demo, a size is
# semi-arbitrarily set to give similar behavior to other loading examples
read_options = pyarrow.csv.ReadOptions(
    column_names=["id", "name"], block_size=BATCH_SIZE * 18
)

csv_reader = pyarrow.csv.open_csv(FILE_NAME, read_options=read_options)
batch_number = 0
for df in csv_reader:
    if df is None:
        break
    batch_number += 1
    print("Processing batch", batch_number)
    connection.direct_path_load(
        schema_name=sample_env.get_main_user(),
        table_name="LoadCsvTab",
        column_names=["id", "name"],
        data=df,
    )

with connection.cursor() as cursor:

    # Show how many rows were inserted
    cursor.execute("select count(*) from LoadCsvTab")
    (r,) = cursor.fetchone()
    print(f"\n{r} rows were inserted")

    # Direct Path Load always commits so clean up the table for demonstration
    # purposes
    cursor.execute("truncate table LoadCsvTab")
