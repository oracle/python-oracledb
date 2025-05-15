# python-oracledb

python-oracledb is a [Python programming language][python] extension module
allowing Python programs to connect to [Oracle Database][oracledb].
Python-oracledb is the new name for Oracle's popular cx_Oracle driver.

The module conforms to the [Python Database API 2.0 specification][pep249] with
a considerable number of additions and a couple of minor exclusions, see the
[feature list][features].

Synchronous and [concurrent][concurrent] coding styles are supported.

## Installation

Run `python -m pip install oracledb`

See [python-oracledb Installation][installation].

## Dependencies and Interoperability

- Python versions 3.9 through 3.13.

  Pre-built packages are available on [PyPI][pypi] and other repositories.

  Source code is also available.

  Previous versions of python-oracledb supported older Python versions.

- Oracle Client libraries are *optional*.

  **Thin mode**: By default python-oracledb runs in a 'Thin' mode which
  connects directly to Oracle Database.

  **Thick mode**: Some advanced Oracle Database functionality is currently only
  available when optional Oracle Client libraries are loaded by
  python-oracledb.  Libraries are available in the free [Oracle Instant
  Client][instantclient] packages. Python-oracledb can use Oracle Client
  libraries 11.2 through 23ai.

- Oracle Database

  **Thin mode**: Oracle Database 12.1 (or later) is required.

  **Thick mode**: Oracle Database 9.2 (or later) is required, depending on the
  Oracle Client library version.  Oracle Database's standard client-server
  version interoperability allows connection to both older and newer
  databases. For example when python-oracledb uses Oracle Client 19c libraries,
  then it can connect to Oracle Database 11.2 or later.

## Documentation

See the [python-oracledb Documentation][documentation] and [Release
Notes][relnotes].

## Samples

Examples can be found in the [/samples][samples] directory and the
[Python and Oracle Database Tutorial][tutorial].

## Help

Questions can be asked in [GitHub Discussions][ghdiscussions].

Problem reports can be raised in [GitHub Issues][ghissues].

## Tests

See [/tests][tests]

## Contributing

This project welcomes contributions from the community. Before submitting a
pull request, please [review our contribution guide](./CONTRIBUTING.md).

## Security

Please consult the [security guide](./SECURITY.md) for our responsible security
vulnerability disclosure process.

## License

See [LICENSE][license], [THIRD_PARTY_LICENSES][tplicense], and
[NOTICE][notice].

[python]: https://www.python.org/
[oracledb]: https://www.oracle.com/database/
[instantclient]: https://www.oracle.com/database/technologies/instant-client.html
[pep249]: https://peps.python.org/pep-0249/
[documentation]: http://python-oracledb.readthedocs.io
[relnotes]: https://python-oracledb.readthedocs.io/en/latest/release_notes.html
[license]: https://github.com/oracle/python-oracledb/blob/main/LICENSE.txt
[tplicense]: https://github.com/oracle/python-oracledb/blob/main/THIRD_PARTY_LICENSES.txt
[notice]: https://github.com/oracle/python-oracledb/blob/main/NOTICE.txt
[tutorial]: https://oracle.github.io/python-oracledb/samples/tutorial/Python-and-Oracle-Database-The-New-Wave-of-Scripting.html
[ghdiscussions]: https://github.com/oracle/python-oracledb/discussions
[ghissues]: https://github.com/oracle/python-oracledb/issues
[tests]: https://github.com/oracle/python-oracledb/tree/main/tests
[samples]: https://github.com/oracle/python-oracledb/tree/main/samples
[installation]: https://python-oracledb.readthedocs.io/en/latest/user_guide/installation.html
[features]: https://oracle.github.io/python-oracledb/#features
[concurrent]: https://python-oracledb.readthedocs.io/en/latest/user_guide/asyncio.html
[pypi]: https://pypi.org/project/oracledb
