# -----------------------------------------------------------------------------
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
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
# load_csv.py
#
# A sample showing how to load CSV data using two methods:
#   - executemany() of data read with Python's CSV module
#   - executemany() of data read into dataframes by PyArrow's CSV module
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

# CSV file. This sample file has both valid rows and some rows with data too
# large to insert.
FILE_NAME = os.path.join("data", "load_csv.csv")

# Adjust the number of rows to be inserted in each iteration to meet your
# memory and performance requirements. Typically this is a large-ish value to
# reduce the number of calls to executemany(). For this demo with a small CSV
# file, a small batch size is used to show the looping behavior of the code.
BATCH_SIZE = 19

connection = oracledb.connect(
    user=sample_env.get_main_user(),
    password=sample_env.get_main_password(),
    dsn=sample_env.get_connect_string(),
    params=sample_env.get_connect_params(),
)

# -----------------------------------------------------------------------------
# Loading using executemany() which uses Oracle Database's "Array DML" support

print("\nLoading with executemany() using Python's CSV module")


def process_batch_em(cursor, batch_number, data):
    print("Processing batch", batch_number + 1)
    cursor.executemany(sql, data, batcherrors=True)
    for error in cursor.getbatcherrors():
        line_num = (batch_number * BATCH_SIZE) + error.offset + 1
        print("Error", error.message, "at line", line_num)


with connection.cursor() as cursor:
    # Clean up the table for demonstration purposes
    cursor.execute("truncate table LoadCsvTab")

    # Predefine the memory areas to match the table definition.
    # This can improve performance by avoiding memory reallocations.
    # Here, one parameter is passed for each of the columns.
    # "None" is used for the ID column, since the size of NUMBER isn't
    # variable.  The "25" matches the maximum expected data size for the
    # NAME column
    cursor.setinputsizes(None, 25)

    # Loop over the data and insert it in batches
    with open(FILE_NAME, "r") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")
        sql = "insert into LoadCsvTab (id, name) values (:1, :2)"
        data = []
        batch_number = 0
        for line in csv_reader:
            data.append((line[0], line[1]))
            if len(data) % BATCH_SIZE == 0:
                process_batch_em(cursor, batch_number, data)
                data = []
                batch_number += 1
        if data:
            process_batch_em(cursor, batch_number, data)

        # In a production system you might choose to fix any invalid rows,
        # re-insert them, and then commit.  Or you could rollback everything.
        # In this sample we simply commit and ignore the invalid rows that
        # couldn't be inserted.
        connection.commit()

    # Show how many rows were inserted
    cursor.execute("select count(*) from LoadCsvTab")
    (r,) = cursor.fetchone()
    print(f"\n{r} valid rows were inserted")

# -----------------------------------------------------------------------------
# Loading with PyArrow's CSV package using executemany()
#
# Using PyArrow to read into a dataframe for insertion can be faster than using
# the Python CSV module.

try:
    import pyarrow.csv
except Exception:
    print("\nTo use pyarrow dataframes, install pyarrow.")
    sys.exit()

print("\nLoading with executemany() using PyArrow's CSV module")

with connection.cursor() as cursor:
    # Clean up the table for demonstration purposes
    cursor.execute("truncate table LoadCsvTab")

    # PyArrow uses a byte size for batching. For this demo, a size is
    # semi-arbitrarily set to give similar behavior to other loading examples
    read_options = pyarrow.csv.ReadOptions(
        column_names=["id", "name"], block_size=BATCH_SIZE * 17
    )

    csv_reader = pyarrow.csv.open_csv(FILE_NAME, read_options=read_options)
    batch_number = 0
    record_start = 0
    for df in csv_reader:
        if df is None:
            break
        batch_number += 1
        print("Processing batch", batch_number)
        cursor.executemany(sql, df, batcherrors=True)
        for error in cursor.getbatcherrors():
            line_num = record_start + error.offset + 1
            print("Error", error.message, "at line", line_num)
        record_start += len(df)

    # Show how many rows were inserted
    cursor.execute("select count(*) from LoadCsvTab")
    (r,) = cursor.fetchone()
    print(f"\n{r} rows were inserted")
