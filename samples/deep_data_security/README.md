# Deep Data Security Sample: Run Flow

Use this flow in:

```bash
cd python-oracledb/samples/deep_data_security/
```

## Prerequisites

- The database version must support Deep Data Security.
- Install the third-party Python library `msal` (used for Microsoft Entra token
  flows).

## 1) Run required SQL setup scripts

Run these scripts in the target database, in this order:

1. `create_hr_schema.sql`
   - Reference: https://github.com/paulparkinson/oracle-ai-for-sustainable-dev/blob/main/security/deepdatasecurity/sql-entraid/00_create_hr_sample_objects.sql
2. `database_entra_external_auth.sql`
   - Reference: https://github.com/paulparkinson/oracle-ai-for-sustainable-dev/blob/main/security/deepdatasecurity/sql-entraid/01_enable_database_free_entra_external_authentication.sql
3. `setup_dds_demo.sql`
   - Reference: https://github.com/paulparkinson/oracle-ai-for-sustainable-dev/blob/main/security/deepdatasecurity/sql-entraid/setup_entraid_dds_demo.sql

## 2) Set environment variables

Set these environment variables (replace placeholder values with your own):

```bash
# User token acquisition
export AZURE_USER_CLIENT_ID="user app client id"
export AZURE_USER_AUTHORITY="azure user authority"
export AZURE_USER_SCOPES="azure user scope"

# DB token acquisition
export AZURE_DB_CLIENT_ID="db app client id"
export AZURE_DB_CLIENT_CREDENTIAL="client secret"
export AZURE_DB_AUTHORITY="azure db authority"
export AZURE_DB_SCOPES="azure db scope"

# ROPC username
export AZURE_USERNAME="your azure username"
```

Also `python-oracledb/samples/sample_env.py` must be configured.

- `end_user_identity` is the end-user access token fetched by the script using
  the Python `msal` library.

## 3) Set end-user identity (required for both samples)

Both sample programs require setting the end-user identity before the query
steps:

- `deep_data_security_standalone.py`
- `deep_data_security_pool.py`

Each sample uses:

```python
provider.set_end_user_identity(end_user_identity)
```

This is the key step that activates Deep Data Security. After this identity is
set, the next connection/acquire call runs with end-user context, and Deep Data
Security policies (row filtering and column masking) are enforced for that
user.


## 4) Run the Deep Data Security sample Python program

Run either sample to observe the same Deep Data Security behavior before and
after setting context:

```bash
python deep_data_security_standalone.py
# or
python deep_data_security_pool.py
```

### What these sample programs do

- Connect to Oracle Database using settings from `sample_env`
- Use Azure values (`AZURE_USER_CLIENT_ID`, `AZURE_USER_AUTHORITY`, `AZURE_USER_SCOPES`, `AZURE_USERNAME`, `AZURE_DB_CLIENT_ID`, `AZURE_DB_CLIENT_CREDENTIAL`, `AZURE_DB_AUTHORITY`, `AZURE_DB_SCOPES`) for end-user and DB security parameters
- Print context and data-query results **before** setting end-user identity
- Call `provider.set_end_user_identity(END_USER_IDENTITY)`
- Reconnect/acquire a new connection and print context + `hr.employees` results **after** identity is set


---

## Sample output

### Employee login behavior

```text

xxxxxxxxxxxxxxxxxxxx Before setting the context xxxxxxxxxxxxxxxxxxxx

xs$session username is None
(None,)
ORA_END_USER_CONTEXT username is None
(None,)
ORA_END_USER_CONTEXT user token iss = None

-- Read contexts through DB query
Current user sys_context('userenv', 'current_user') = DB_USR
XS session user xs_sys_context('xs$session', 'username') = None

-- Sample DB query on table hr.employees
ORA-00942: table or view does not exist
Help: https://docs.oracle.com/error-help/db/ora-00942/
press enter to set the context

xxxxxxxxxxxxxxxxxxxx After setting the context xxxxxxxxxxxxxxxxxxxx

xs$session username is sks1@example.onmicrosoft.com
ORA_END_USER_CONTEXT username is sks1@example.onmicrosoft.com
ORA_END_USER_CONTEXT user token iss = https://sts.windows.net/xxxxxxxx/

-- Read contexts through DB query
Current user sys_context('userenv', 'current_user') = XS$NULL
XS session user xs_sys_context('xs$session', 'username') = sks1@example.onmicrosoft.com

-- Sample DB query on table hr.employees
Count of records in hr.employees = 1

Dept ID: 60, First Name: Suraj, SSN: 000-00-0101
```

### Output interpretation

The output shows that before the Deep Data Security context is applied, no
end-user identity is set (`xs$session` is `None`) and the sample `hr.employees`
query fails. After the context is applied, the end-user identity is established
and the employee can see only the row they are authorized to access (`Count of
records in hr.employees = 1`). This demonstrates employee-scoped data
visibility enforced by Deep Data Security policies.

### Manager login behavior (after context is set)

When a manager logs in, the context can show the manager identity while still
enforcing masking rules on sensitive columns.

```text
xxxxxxxxxxxxxxxxxxxx After setting the context xxxxxxxxxxxxxxxxxxxx

xs$session username is bks1@example.onmicrosoft.com
ORA_END_USER_CONTEXT username is bks1@example.onmicrosoft.com
ORA_END_USER_CONTEXT user token iss = https://sts.windows.net/xxxxxxxx/

-- Read contexts through DB query
Current user sys_context('userenv', 'current_user') = XS$NULL
XS session user xs_sys_context('xs$session', 'username') = bks1@example.onmicrosoft.com

-- Sample DB query on table hr.employees
Count of records in hr.employees = 4

Dept ID: 90, First Name: Bob, SSN: 000-00-0100
Dept ID: 60, First Name: Suraj, SSN: None
Dept ID: 60, First Name: Riley, SSN: None
Dept ID: 60, First Name: Jordan, SSN: None

```

Interpretation: for manager login, once the Deep Data Security context is set,
the manager can view all relevant employee rows (`Count of records in
hr.employees = 4`). At the same time, sensitive SSN data is still
policy-protected: SSN is shown for the manager's own record and masked (set as
`None`) for reportees. This demonstrates broader manager-level row visibility
with column-level protection still enforced.
