# -----------------------------------------------------------------------------
# Copyright (c) 2026, Oracle and/or its affiliates.
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
# setup_schema.py
#
# Command-line utility for setting up the schema required by the demo.
# -----------------------------------------------------------------------------

import json
import pathlib
import sys

path = pathlib.Path(__file__)
sys.path.insert(0, str(path.parent.parent.parent))

import sample_env  # noqa

DEMO_USER = "hr"

DB_TENANT_ID = sample_env.get_value("DB_TENANT_ID", "Database tenant id")
DB_APP_ID = sample_env.get_value("DB_APP_ID", "Database app id")
DB_APP_ID_URI = sample_env.get_value("DB_APP_ID_URI", "Database app id URI")
DEMO_EMPLOYEES_AZURE_ROLE = sample_env.get_value(
    "DEMO_EMPLOYEES_AZURE_ROLE",
    "Employees Azure Role",
    default_value="EMPLOYEES",
)
DEMO_MANAGERS_AZURE_ROLE = sample_env.get_value(
    "DEMO_MANAGERS_AZURE_ROLE", "Managers Azure Role", default_value="MANAGERS"
)
DEMO_EMPLOYEE_USERNAME = sample_env.get_value(
    "DEMO_EMPLOYEE_USERNAME", "Employee User Name"
)
DEMO_MANAGER_USERNAME = sample_env.get_value(
    "DEMO_MANAGER_USERNAME", "Manager User Name"
)

# validate database credentials and database server version
conn = sample_env.get_admin_connection()
version = tuple(int(s) for s in conn.version.split(".")[:3])
if version < (23, 26, 2):
    raise Exception(
        f"Database is at version {conn.version} but 23.26.2 or higher is needed"
    )
cursor = conn.cursor()

# create schema
cursor.execute(f"drop user if exists {DEMO_USER} cascade")
cursor.execute(f"create user {DEMO_USER} no authentication")
cursor.execute(f"grant update any end user context to {DEMO_USER}")
cursor.execute(f"grant select any end user context to {DEMO_USER}")

# ensure schema has unlimited quota on the default tablespace
cursor.execute(
    """
    select default_tablespace
    from dba_users
    where username = :1
    """,
    [DEMO_USER.upper()],
)
(tablespace_name,) = cursor.fetchone()
cursor.execute(f"alter user {DEMO_USER} quota unlimited on {tablespace_name}")

# create employees table
cursor.execute(f"""
    create table {DEMO_USER}.employees (
        employee_id   NUMBER(10)    CONSTRAINT employees_pk PRIMARY KEY,
        first_name    VARCHAR2(50)  NOT NULL,
        last_name     VARCHAR2(50)  NOT NULL,
        user_name     VARCHAR2(128) NOT NULL,
        manager_id    NUMBER(10),
        ssn           VARCHAR2(11),
        salary        NUMBER(10,2),
        department_id NUMBER(10),
        phone_number  VARCHAR2(30)
    )
    """)
cursor.execute(f"""
    alter table {DEMO_USER}.employees add constraint employees_manager_fk
    foreign key (manager_id) references {DEMO_USER}.employees (employee_id)
    """)
cursor.execute(f"""
    create unique index {DEMO_USER}.employees_user_name_uk
    on {DEMO_USER}.employees (user_name)
    """)
cursor.execute(f"""
    create index {DEMO_USER}.employees_manager_ix
    on {DEMO_USER}.employees (manager_id)
    """)

# populate employees table with some data
employee_data = [
    (
        100,
        "Maya",
        "Manager",
        DEMO_MANAGER_USERNAME,
        None,
        "000-00-0100",
        175000,
        90,
        "555.0100",
    ),
    (
        101,
        "Avery",
        "Stone",
        "avery.stone@example.com",
        100,
        "000-00-0101",
        125000,
        60,
        "555.0101",
    ),
    (
        102,
        "Riley",
        "Chen",
        "riley.chen@example.com",
        100,
        "000-00-0102",
        118000,
        60,
        "555.0102",
    ),
    (
        103,
        "Jordan",
        "Patel",
        DEMO_EMPLOYEE_USERNAME,
        100,
        "000-00-0103",
        116000,
        60,
        "555.0103",
    ),
]
cursor.executemany(
    f"""
    insert into {DEMO_USER}.employees
    (employee_id, first_name, last_name, user_name, manager_id, ssn, salary,
     department_id, phone_number)
    values (:1, :2, :3, :4, :5, :6, :7, :8, :9)
    """,
    employee_data,
)
conn.commit()

# ensure application user has the necessary privileges
app_user = sample_env.get_main_user()
cursor.execute(f"grant create end user security context to {app_user}")
cursor.execute(f"grant update any end user context to {app_user}")

# enable external authentication; this is done differently on cloud databases
# than on local databases
cursor.execute("select sys_context('userenv', 'cloud_service')")
(cloud_service,) = cursor.fetchone()
if cloud_service is None:
    cursor.execute(
        "alter system set identity_provider_type = AZURE_AD scope=both"
    )
    cursor.execute(f"""
        alter system set identity_provider_config = '{{
            "application_id_uri": "{DB_APP_ID_URI}",
            "tenant_id": "{DB_TENANT_ID}",
            "app_id": "{DB_APP_ID}"
        }}' scope=both
        """)
else:
    params_dict = dict(
        tenant_id=DB_TENANT_ID,
        application_id=DB_APP_ID,
        application_id_uri=DB_APP_ID_URI,
    )
    cursor.callproc(
        "dbms_cloud_admin.enable_external_authentication",
        ["AZURE_AD", True, json.dumps(params_dict)],
    )

# create context and admin package
cursor.execute(f"""
    create or replace end user context {DEMO_USER}.emp_ctx using json schema '{{
      "type": "object",
      "properties": {{
        "ID": {{
          "type": "integer",
          "o:onFirstRead": "{DEMO_USER}.ctx_pkg.init_user_context"
        }}
      }}
    }}'
    """)
cursor.execute(f"""
    create or replace package {DEMO_USER}.ctx_pkg as
        procedure init_user_context;
    end;
    """)
cursor.execute(f"""
    create or replace package body {DEMO_USER}.ctx_pkg as
      procedure init_user_context is
        sql_stmt varchar2(4000);
      begin
        sql_stmt := '
          update end_user_context t
          set t.context.ID = (
             select e.employee_id
             from {DEMO_USER}.employees e
             where upper(e.user_name) = upper(ora_end_user_context.username)
           )
          where owner = ''{DEMO_USER.upper()}''
            and name = ''EMP_CTX'';
        ';
        execute immediate sql_stmt;
      end;
    end;
    """)

# create roles
cursor.execute(f"""
    create or replace data role hrapp_employees
    mapped to 'AZURE_ROLE={DEMO_EMPLOYEES_AZURE_ROLE}'
    """)
cursor.execute(f"""
    create or replace data role hrapp_managers
    mapped to 'AZURE_ROLE={DEMO_MANAGERS_AZURE_ROLE}'
    """)
cursor.execute("create role if not exists employee_context_admin")
cursor.execute(f"""
    grant execute on {DEMO_USER}.ctx_pkg
    to employee_context_admin
    """)
cursor.execute("grant employee_context_admin to hrapp_employees")
cursor.execute("grant employee_context_admin to hrapp_managers")
cursor.execute(f"""
    create or replace data grant {DEMO_USER}.employee_context_grant
        as select
        on sys.end_user_context
        where owner = '{DEMO_USER.upper()}'
          and name = 'EMP_CTX'
        to hrapp_employees, hrapp_managers
    """)
cursor.execute(f"""
    create or replace data grant {DEMO_USER}.hrapp_employees_access
        as select, update(phone_number, first_name)
        on {DEMO_USER}.employees
        where upper(user_name) = upper(ora_end_user_context.username)
        to hrapp_employees
    """)
cursor.execute(f"""
    create or replace data grant {DEMO_USER}.hrapp_manager_access
        as select (all columns except ssn),
            update (salary, department_id, first_name)
        on {DEMO_USER}.employees
        where manager_id = ora_end_user_context.{DEMO_USER}.emp_ctx.ID
        to hrapp_managers
    """)
print("Schema setup completed.")
