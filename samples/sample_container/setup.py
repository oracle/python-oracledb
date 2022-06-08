#! /usr/bin/env python3.9
#
# NAME
#
#   setup.py
#
# PURPOSE
#
#   Creates the python-oracledb sample schema after waiting for the database to
#   open.
#
# USAGE
#
#   ./setup.py

import oracledb
import os
import time

pw = os.environ.get("ORACLE_PASSWORD")
os.environ["PYO_SAMPLES_ADMIN_PASSWORD"] = pw

c = None

for i in range(30):
    try:
        c = oracledb.connect(user="system",
                             password=pw,
                             dsn="localhost/xepdb1",
                             tcp_connect_timeout=5)
        break
    except (OSError, oracledb.Error) as e:
        print("Waiting for database to open")
        time.sleep(5)

if c:
    print("PDB is open")
else:
    print("PDB did not open in allocated time")
    print("Try again in a few minutes")
    exit()

# Connect to the CDB to start DRCP because enable_per_pdb_drcp is FALSE by
# default
print("Starting DRCP pool")
with oracledb.connect(user="sys",
                      password=pw,
                      dsn="localhost/XE",
                      mode=oracledb.AUTH_MODE_SYSDBA) as connection:
    with connection.cursor() as cursor:
        cursor.callproc("dbms_connection_pool.start_pool")

# create_schema.py will be appended here by the Dockerfile
