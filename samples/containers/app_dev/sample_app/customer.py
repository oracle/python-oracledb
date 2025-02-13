# -----------------------------------------------------------------------------
# Copyright (c) 2025 Oracle and/or its affiliates.
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
# customer.py
# -----------------------------------------------------------------------------

import os

from flask import Flask, render_template, request, redirect, url_for
import oracledb

app = Flask(__name__, template_folder="templates")
app.config["CONNECTION_POOL"] = None
app.config["CONNECTION_STATUS"] = None
drop_table_23ai = "drop table if exists customer_info"
drop_table = """begin
                  execute immediate 'drop table customer_info';
                exception
                  when others then
                    if sqlcode != -942 then
                      raise;
                    end if;
                end;"""
stmts = [
    """create table customer_info (
       id     number generated always as
                identity(start with 1001 increment by 1),
       name    varchar2(30),
       dob     date,
       city    varchar2(30),
       zipcode number)""",
    """insert into customer_info (name, dob, city, zipcode)
       values ('Allen', '01-Sep-1980', 'Belmont', 56009)""",
    """insert into customer_info (name, dob, city, zipcode)
       values ('Bob', '12-Aug-2009', 'San Jose', 56012)""",
    """insert into customer_info (name, dob, city, zipcode)
       values ('Christina', '30-Jul-1994', 'San Carlos', 56023)""",
]


# init_session(): a 'session callback' to efficiently set any initial state
# that each connection should have.
def init_session(connection, requestedTag_ignored):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            alter session set
                time_zone = 'UTC'
                 nls_date_format = 'DD-MON-YYYY'
            """
        )


def create_pool():
    pool_min = 2
    pool_max = 2
    pool_inc = 0

    tns_admin = os.environ.get("TNS_ADMIN")
    wallet_password = os.environ.get("PYO_SAMPLES_WALLET_PASSWORD")
    wallet_location = os.environ.get("PYO_SAMPLES_WALLET_LOCATION")
    if (
        wallet_password is not None
        and wallet_location is None
        and tns_admin is not None
    ):
        wallet_location = tns_admin

    if wallet_password is not None:
        try:
            db_pool = oracledb.create_pool(
                user=os.environ.get("PYO_SAMPLES_MAIN_USER"),
                password=os.environ.get("PYO_SAMPLES_MAIN_PASSWORD"),
                wallet_password=wallet_password,
                wallet_location=wallet_location,
                config_dir=tns_admin,
                dsn=os.environ.get("PYO_SAMPLES_CONNECT_STRING"),
                min=pool_min,
                max=pool_max,
                increment=pool_inc,
                session_callback=init_session,
            )
            error_msg = "Success!"
        except oracledb.DatabaseError as e:
            db_pool = None
            (error,) = e.args
            error_msg = error.message
    else:
        try:
            db_pool = oracledb.create_pool(
                user=os.environ.get("PYO_SAMPLES_MAIN_USER"),
                password=os.environ.get("PYO_SAMPLES_MAIN_PASSWORD"),
                dsn=os.environ.get("PYO_SAMPLES_CONNECT_STRING"),
                config_dir=tns_admin,
                min=pool_min,
                max=pool_max,
                increment=pool_inc,
                session_callback=init_session,
            )
            error_msg = "Success!"
        except oracledb.DatabaseError as e:
            db_pool = None
            (error,) = e.args
            error_msg = error.message

    return (db_pool, error_msg)


# Create customer details table and populate records
# Note: The customer_info table will be re-created everytime during this
# application startup.
def create_schema():
    pool = app.config["CONNECTION_POOL"]
    dbstatus = app.config["CONNECTION_STATUS"]

    if dbstatus != "Success!":
        return

    try:
        connection = pool.acquire()
    except oracledb.DatabaseError:
        return

    with connection.cursor() as cursor:
        dbversion = connection.version
        dbversion = dbversion.split(".")[0]
        if int(dbversion) >= 23:
            cursor.execute(drop_table_23ai)
        else:
            cursor.execute(drop_table)
        for stmt in stmts:
            cursor.execute(stmt)
        connection.commit()


@app.route("/entry", methods=["POST", "GET"])
def entry():
    stmt = """insert into customer_info (name, dob, city, zipcode) values
             (:1, :2, :3, :4)"""

    if request.method == "GET":
        msg = "Customer details added successfully!"
        return render_template("customer_entry_redirect.html", form_data=msg)

    if request.method == "POST":
        data = [
            request.form["cus_name"],
            request.form["cus_dob"],
            request.form["cus_city"],
            request.form["cus_zipcode"],
        ]

    try:
        pool = app.config["CONNECTION_POOL"]
        with pool.acquire() as connection:
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute(stmt, data)
    except oracledb.DatabaseError as e:
        (error,) = e.args
        dbstatus = error.message
        return render_template("error_handler.html", form_data=dbstatus)

    return redirect(url_for("customer"))


@app.route("/customer", methods=["POST", "GET"])
def customer():
    stmt = "select * from customer_info"
    pool = app.config["CONNECTION_POOL"]
    dbstatus = app.config["CONNECTION_STATUS"]

    if dbstatus != "Success!":
        return render_template("error_handle.html", form_data=dbstatus)

    try:
        connection = pool.acquire()
    except oracledb.DatabaseError as e:
        (error,) = e.args
        dbstatus = error.message
        return render_template("error_handler.html", form_data=dbstatus)

    with connection.cursor() as cursor:
        cursor.execute(stmt)
        data = cursor.fetchall()
        return render_template("customer_list.html", form_data=data)


# MAIN

# Create the connection pool
(
    app.config["CONNECTION_POOL"],
    app.config["CONNECTION_STATUS"],
) = create_pool()

# Warning: the CUSTOMER_INFO table used by this application will be re-created
# during application startup so any previous changes (addition of customers)
# will vanish.

create_schema()
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8443,
    )
