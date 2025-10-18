# python-oracledb

The python-oracledb driver is the widely used, open-source [Python][python]
extension module allowing Python programs to connect directly to [Oracle
Database][oracledb] with no extra libraries needed. The module is built with
Cython for safety and speed. It is lightweight and high-performance. It is
stable, well tested, and has comprehensive [documentation][documentation]. The
module is maintained by Oracle.

The module conforms to the [Python Database API 2.0 specification][pep249] with
a considerable number of additions and a couple of minor exclusions, see the
[feature list][features]. It is used by many Python frameworks, SQL generators,
ORMs, and libraries.

Python-oracledb has a rich feature set which is easy to use. It gives you
control over SQL and PL/SQL statement execution; for working with data frames;
for fast data ingestion; for calling NoSQL-style document APIs; for message
queueing; for receiving database notifications; and for starting and stopping
the database. It also has high availability and security features. Synchronous
and [concurrent][concurrent] coding styles are supported. Database operations
can optionally be [pipelined][pipelining].

Python-oracledb is the successor to the now obsolete cx_Oracle driver.

## Python-oracledb Installation

Run:

```
python -m pip install oracledb --upgrade
```

See [Installing python-oracledb][installation] for details.

## Samples

Examples can be found in the [/samples][samples] directory and the
[Python and Oracle Database Tutorial][tutorial].

A basic example:

```
import oracledb
import getpass

un = "scott"                  # Sample database username
cs = "localhost/orclpdb"      # Sample database connection string
# cs = "localhost/freepdb1"   # For Oracle Database Free users
# cs = "localhost/orclpdb1"   # Some databases may have this service
pw = getpass.getpass(f"Enter password for {un}@{cs}: ")

with oracledb.connect(user=un, password=pw, dsn=cs) as connection:
    with connection.cursor() as cursor:
        sql = "select sysdate from dual"
        for r in cursor.execute(sql):
            print(r)
```

## Dependencies and Interoperability

- Python versions 3.9 through 3.14.

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
  libraries versions 11.2 through 23, inclusive.

- Oracle Database

  **Thin mode**: Oracle Database 12.1 (or later) is required.

  **Thick mode**: Oracle Database 9.2 (or later) is required, depending on the
  Oracle Client library version.  Oracle Database's standard client-server
  version interoperability allows connection to both older and newer
  databases. For example when python-oracledb uses Oracle Client 19 libraries,
  then it can connect to Oracle Database 11.2 or later.

## Documentation

See the [python-oracledb Documentation][documentation] and [Release
Notes][relnotes].

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
[pipelining]: https://python-oracledb.readthedocs.io/en/latest/user_guide/asyncio.html#pipelining-database-operations
[pypi]: https://pypi.org/project/oracledb
