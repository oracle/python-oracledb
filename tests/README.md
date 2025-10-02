This directory contains the test suite for python-oracledb.

1.  Install pytest and tox:

        python -m pip install pytest tox --upgrade

2.  Set the required database credential and related environment variables
    documented in [conftest.py][2].

3.  The schemas and SQL objects that are referenced in the test suite can be
    created by running the Python script [create_schema.py][1]. The script
    requires administrative privileges to complete successfully:

        python -m pytest tests/create_schema.py

4.  Run the test suite by issuing the following command in the top-level
    directory of your oracledb installation:

        python -m tox

    This will build the module in an independent environment and run the test
    suite using the module that was just built in that environment.
    Alternatively, you can use the currently installed build of oracledb and
    run the following command instead:

        python -m pytest

    You may also run each of the test scripts independently, as in:

        python -m pytest tests/test_1000_module.py

    The tests run in thin mode by default. If you wish to run the tests in
    thick mode, use the following command:

        python -m pytest --use-thick-mode

5.  After running the test suite, the schemas can be dropped by running the
    Python script [drop_schema.py][3]. The script requires administrative
    privileges to complete successfully. A set of environment variables should
    be set as documented in the Python script [conftest.py][2]. Run the
    script using the following command:

        python -m pytest tests/drop_schema.py

6.  Enable tests that require extra configuration

    The following test(s) are automatically skipped if their required
    environment variable(s) and setup is not available.

    5.1  test_5000_externalauth.py

         This test aims to test the usage of external authentication.

         - Set the PYO_TEST_EXTERNAL_USER environment variable to the externally
           identified user that will be connected using external authentication.

         - Set up external authentication. See
           [Connecting Using External Authentication][4] for creating an
           Oracle Wallet or enabling OS authentication.

         - Run the following SQL commands as a user with administrative
           privileges (such as SYSTEM or ADMIN) to allow the external user to
           connect to the database and behave as proxy for testing external
           authentication with proxy:

               grant create session to <External User>;

               alter user <Schema Owner> grant connect through <External User>;



[1]: https://github.com/oracle/python-oracledb/blob/main/tests/create_schema.py
[2]: https://github.com/oracle/python-oracledb/blob/main/tests/conftest.py
[3]: https://github.com/oracle/python-oracledb/blob/main/tests/drop_schema.py
[4]: https://python-oracledb.readthedocs.io/en/latest/user_guide/connection_handling.html#connecting-using-external-authentication
