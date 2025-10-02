This directory contains the extended test suite for python-oracledb. These
tests either require specialized configuration or are timing dependent.
Configuration for these extended tests can be found in the file pointed to by
the environment variable `PYO_TEST_EXT_CONFIG_FILE` or, if the environment
variable is not specified, then the file `config.ini` found in this directory.
Configuration required to run the extended test is documented in each test
file.

All of the tests can be run by executing this command:

    pytest tests/ext

Or each file can be run independently.

A sample configuration file is found in `sample_config.ini`.
