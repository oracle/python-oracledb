# Deep Data Security Samples

The samples in this directory and its subdirectories use Microsoft Entra ID
OAUTH tokens for overall authentication.

## Prerequisites

- The database must support Deep Data Security (23.26.2 or higher).
- Install the third-party Python library `msal` (used for Microsoft Entra token
  flows).
```bash
python -m pip install msal
```
- Requires Microsoft Entra ID account

## 1) Set environment variables

Before running the samples, configure the required environment variables for
Azure authentication and database connectivity. Replace all placeholder values
with values from your own Azure and Oracle Database environment.

The sample scripts use two sources of configuration:

1. **Azure authentication variables** are read directly from environment
   variables by the token-acquisition scripts.
2. **Database connection variables** are loaded through
   `python-oracledb/samples/sample_env.py`. These variables usually use the
   `PYO_SAMPLES_*` prefix.

### Azure authentication variables

Set the following variables for Azure user token and DB token acquisition:

```bash
# User token acquisition
export AZURE_USER_CLIENT_ID="user app client id"
export AZURE_USER_AUTHORITY="azure user authority"
export AZURE_USER_SCOPES="azure user scope"

# Database token acquisition
export AZURE_DB_CLIENT_ID="db app client id"
export AZURE_DB_CLIENT_CREDENTIAL="client secret"
export AZURE_DB_AUTHORITY="azure db authority"
export AZURE_DB_SCOPES="azure db scope"

# Microsoft Azure user credentials
export AZURE_USERNAME="your azure username"
```

### Application roles and usernames

Configure these environment variables to match your Azure application's role
names and user login emails.

```bash
# Azure role name for employees
export DEMO_EMPLOYEES_AZURE_ROLE="AZURE_EMPLOYEES"
# Azure role name for managers
export DEMO_MANAGERS_AZURE_ROLE="AZURE_MANAGERS"
# Username (email address) for employee
export DEMO_EMPLOYEE_USERNAME="employee@example.com"
# Username (email address) for manager
export DEMO_MANAGER_USERNAME="manager@example.com"
```

```bash
export DB_TENANT_ID="your tenant id"
export DB_APP_ID="your app id"
export DB_APP_ID_URI="your app id uri"
```

These values are used by `setup_schema.py` when configuring database external
authentication.

### Database connection variables

The following variables are read through
`python-oracledb/samples/sample_env.py`. Replace the example values with values
from your Oracle Database environment:

```bash
export PYO_SAMPLES_CONNECT_STRING="myhost.example.com/myservice"
export PYO_SAMPLES_MAIN_USER="app_user"
export PYO_SAMPLES_MAIN_PASSWORD="change_me"
export PYO_SAMPLES_WALLET_LOCATION="/path/to/wallet"
export PYO_SAMPLES_WALLET_PASSWORD="wallet_password"
```


## 2) Ensure main sample schema has already been created. If not, run this:

```bash
python ../../create_schema.py
```

The main sample `create_schema.py` script creates the application user and
base sample schema objects used by all python-oracledb samples. It must be run
first because these samples depend on that application user already existing.


## 3) Run required SQL setup script

```bash
python setup_schema.py
```

The `setup_schema.py` script then configures the objects specific to
these samples, including the HR sample data, Deep Data Security policy setup,
and the Microsoft Entra external-authentication values read from the
environment.


## 4) Set end-user identity (required for both samples)

`end_user_identity` is the end-user access token fetched by the script using
the Python `msal` library.
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


## 5) Run the Deep Data Security sample Python program

Run either sample to observe the same Deep Data Security behavior before and
after setting context:

```bash
python deep_data_security_standalone.py
# or
python deep_data_security_pool.py
```

### What these sample programs do

- Connect to Oracle Database using settings from `sample_env`
- Use Azure values (`AZURE_USER_CLIENT_ID`, `AZURE_USER_AUTHORITY`,
  `AZURE_USER_SCOPES`, `AZURE_USERNAME`, `AZURE_DB_CLIENT_ID`,
  `AZURE_DB_CLIENT_CREDENTIAL`, `AZURE_DB_AUTHORITY`, `AZURE_DB_SCOPES`) for
  end-user and DB security parameters
- Print context and data-query results **before** setting end-user identity
- Call `provider.set_end_user_identity(END_USER_IDENTITY)`
- Reconnect/acquire a new connection and print context + `hr.employees` results
  **after** identity is set


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

## Note

**Note:** For official python-oracledb Deep Data Security details, see:
> https://python-oracledb.readthedocs.io/en/latest/user_guide/connection_handling.html#deep-data-security

For a Django demo for Deep Data Security, refer to:
`python-oracledb/samples/deep_data_security/azure/django/hr_demo`
