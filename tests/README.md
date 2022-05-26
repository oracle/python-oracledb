This directory contains the test suite for python-oracledb.

1.  The schemas and SQL objects that are referenced in the test suite can be
    created by running the Python script [create_schema.py][1]. The script
    requires administrative privileges and will prompt for these credentials as
    well as the names of the schemas that will be created, unless a number of
    environment variables are set as documented in the Python script
    [test_env.py][2]. Run the script using the following command:

        python create_schema.py

2.  Run the test suite by issuing the following command in the top-level
    directory of your oracledb installation:

        tox

    This will build the module in an independent environment and run the test
    suite using the module that was just built in that environment.
    Alternatively, you can use the currently installed build of oracledb and
    run the following command instead:

        python -m unittest discover -v -s tests

    You may also run each of the test scripts independently, as in:

        python test_1000_module.py

3.  After running the test suite, the schemas can be dropped by running the
    Python script [drop_schema.py][3]. The script requires administrative
    privileges and will prompt for these credentials as well as the names of
    the schemas that will be dropped, unless a number of environment variables
    are set as documented in the Python script [test_env.py][2]. Run the
    script using the following command:

        python drop_schema.py

[1]: https://github.com/oracle/python-oracledb/blob/main/tests/create_schema.py
[2]: https://github.com/oracle/python-oracledb/blob/main/tests/test_env.py
[3]: https://github.com/oracle/python-oracledb/blob/main/tests/drop_schema.py
