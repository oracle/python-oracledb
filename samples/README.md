## Python-oracledb Examples

This directory contains samples for python-oracledb.

### Basic Examples

1.  The schemas and SQL objects that are referenced in the samples can be
    created by running the Python script [create_schema.py][1]. The script
    requires SYSDBA privileges and will prompt for these credentials as well as
    the names of the schemas and edition that will be created, unless a number
    of environment variables are set as documented in the Python script
    [sample_env.py][2]. Run the script using the following command:

        python create_schema.py

2.  Run a Python script, for example:

        python query.py

3.  After running python-oracledb samples, the schemas and SQL objects can be
    dropped by running the Python script [drop_schema.py][3]. The script
    requires SYSDBA privileges and will prompt for these credentials as well as
    the names of the schemas and edition that will be dropped, unless a number
    of environment variables are set as documented in the Python script
    [sample_env.py][2]. Run the script using the following command:

        python drop_schema.py

### Examples in a Container

The [sample_container](./sample_container) directory has a Dockerfile that will
build a container with the samples and a running Oracle Database.

### Notebooks

The [notebooks](./notebooks) directory has Jupyter notebooks with runnable
examples.

[1]: https://github.com/oracle/python-oracledb/blob/main/samples/create_schema.py
[2]: https://github.com/oracle/python-oracledb/blob/main/samples/sample_env.py
[3]: https://github.com/oracle/python-oracledb/blob/main/samples/drop_schema.py
