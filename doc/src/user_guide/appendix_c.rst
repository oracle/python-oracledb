.. currentmodule:: oracledb

*****************************************************
Appendix C: The python-oracledb and cx_Oracle Drivers
*****************************************************

The python-oracledb driver is the renamed, successor to cx_Oracle. The
python-oracledb driver has many :ref:`new features <releasenotes>` and some
:ref:`deprecations` compared with cx_Oracle. The cx_Oracle driver is obsolete
and should not be used for new development.

.. _upgrading83:

Upgrading from cx_Oracle 8.3 to python-oracledb
===============================================

Below is a list of some useful things to know before upgrading from cx_Oracle
to python-oracledb:

- You can have both cx_Oracle and python-oracledb installed, and can use both
  in the same application.  Install python-oracledb like::

      python -m pip install oracledb --upgrade

  See :ref:`installation` for details.

- By default, python-oracledb runs in a 'Thin' mode which connects directly to
  Oracle Database.  This mode does not need Oracle Client libraries.
  However, some :ref:`additional functionality <featuresummary>` is available
  when python-oracledb uses them.  Python-oracledb is said to be in 'Thick'
  mode when Oracle Client libraries are used.  See :ref:`enablingthick`.  Both
  modes have comprehensive functionality supporting the Python Database API
  v2.0 Specification. The Thick mode is equivalent to cx_Oracle.

  cx_Oracle always runs in a Thick mode using Oracle Client libraries.  The
  features in python-oracledb Thick mode and cx_Oracle 8.3 are the same,
  subject to the :ref:`new features <releasenotes>`, some :ref:`deprecations
  <deprecations>`, and to other changes noted in the documentation.

- python-oracledb Thin and Thick modes have the same level of support for the
  `Python Database API specification <https://peps.python.org/pep-0249/>`_ and
  can be used to connect to on-premises databases and Oracle Cloud
  databases. See :ref:`driverdiff`.

  Examples can be found in the `GitHub samples directory
  <https://github.com/oracle/python-oracledb/tree/main/samples>`__. A basic
  example is:

  .. code-block:: python

      import oracledb
      import getpass

      pw = getpass.getpass(f"Enter password for hr@localhost/orclpdb: ")

      with oracledb.connect(user="hr", password=userpwd, dsn="localhost/orclpdb") as connection:
          with connection.cursor() as cursor:
              for r in cursor.execute("select sysdate from dual"):
                  print(r)

- python-oracledb can be used in SQLAlchemy, Django, Pandas, Superset and other
  frameworks and Object-relational Mappers (ORMs). See :ref:`frameworks`.

- python-oracledb connection and pool creation calls require keyword arguments
  to conform with the Python Database API specification.  For example you must
  use:

  .. code-block:: python

       connection = oracledb.connect(user="scott", password=pw, dsn="localhost/orclpdb")

  This no longer works:

  .. code-block:: python

       connection = oracledb.connect("scott", pw, "localhost/orclpdb")

- New optional keyword arguments can be passed to connection and pool creation
  functions. For example you can pass the hostname, port and servicename as
  separate parameters instead of using an Easy Connect connection string. In
  python-oracledb Thin mode, some of the new arguments replace :ref:`sqlnet.ora
  <optnetfiles>` settings.

- Some previously deprecated features are no longer available. See
  :ref:`deprecations`.

- There are many new features, see the :ref:`release notes <releasenotes>`.

.. _commonupgrade:

Steps to Upgrade to python-oracledb
-----------------------------------

If you are creating new applications, follow :ref:`installation` and refer to
other sections of the documentation for usage information.

To upgrade existing code from cx_Oracle to python-oracledb, perform the
following steps:

1. Install the new python-oracledb module::

        python -m pip install oracledb --upgrade

   See :ref:`installation` for more details.

2. Import the new interface module. This can be done in two ways. You can change:

   .. code-block:: python

        import cx_Oracle

   to:

   .. code-block:: python

        import oracledb as cx_Oracle

   Alternatively, you can replace all references to the module ``cx_Oracle``
   with ``oracledb``.  For example, change:

   .. code-block:: python

        import cx_Oracle
        c = cx_Oracle.connect(...)

   to:

   .. code-block:: python

        import oracledb
        c = oracledb.connect(...)

   Any new code being introduced during the upgrade should aim to use the
   latter syntax.

3. Use keyword parameters in calls to :func:`oracledb.connect()`,
   ``oracledb.Connection()``, and ``oracledb.SessionPool()``.

   You **must** replace positional parameters with keyword parameters, unless
   only one parameter is being passed. Python-oracledb uses keyword parameters
   exclusively unless a DSN containing the user, password, and connect string
   combined, for example ``"un/pw@cs"``, is used. This change makes the driver
   compliant with the Python Database API specification `PEP 249
   <https://peps.python.org/pep-0249/>`_.

   For example, the following code will fail:

   .. code-block:: python

       c = oracledb.connect("un", "pw", "cs")

   and needs to be changed to:

   .. code-block:: python

       c = oracledb.connect(user="un", password="pw", dsn="cs")

   The following example will continue to work without change:

   .. code-block:: python

       c = oracledb.connect("un/pw@cs")

4. Review obsolete encoding parameters in calls to :func:`oracledb.connect()`,
   ``oracledb.Connection()``, and ``oracledb.SessionPool()``:

   - ``encoding`` and ``nencoding`` are desupported in python-oracledb and must
     be removed. The python-oracledb driver uses UTF-8 exclusively.

   - ``threaded`` is desupported in :func:`oracledb.connect()` and
     ``oracledb.Connection()`` by python-oracledb and must be removed. This
     parameter was already ignored in ``oracledb.SessionPool()`` from cx_Oracle
     8.2.

5. Remove all references to ``Cursor.fetchraw()`` as this method was deprecated
   in cx_Oracle 8.2 and has been removed in python-oracledb.  Instead, use one
   of the other fetch methods such as :meth:`Cursor.fetchmany()`.

6. The default value of the ``oracledb.SessionPool()`` parameter ``getmode``
   now waits for an available connection.  That is, the default is now
   :data:`~oracledb.POOL_GETMODE_WAIT` instead of
   :data:`~oracledb.POOL_GETMODE_NOWAIT`.  The new default value improves the
   behavior for most applications.  If the pool is in the middle of growing,
   the new value prevents transient connection creation errors from occurring
   when using python-oracledb Thin mode, or when using Thick mode with recent
   Oracle Client libraries.

   If the old default value is required, modify any pool creation code to
   explicitly specify ``getmode=oracledb.POOL_GETMODE_NOWAIT``.

   Note a :ref:`ConnectionPool class <connpool>` deprecates the equivalent
   SessionPool class. The method :meth:`oracledb.create_pool()` deprecates the
   use of ``oracledb.SessionPool()``.  New pool parameter constant names such
   as :data:`~oracledb.POOL_GETMODE_NOWAIT` and :data:`~oracledb.PURITY_SELF`
   are now preferred.  The old namespaces still work.

7. A Python `type() <https://docs.python.org/3/library/functions.html#type>`__
   will show the class of a connection pool as ``oracledb.ConnectionPool``
   instead of ``cx_Oracle.SessionPool``. Update code as needed.

8. Use the new :ref:`Advanced Queuing (AQ) <aqusermanual>` API instead of the
   older API which was deprecated in cx_Oracle 7.2 and is not available in
   python-oracledb.

   Replace:

   - ``Connection.deq()`` with :meth:`Queue.deqone()` or :meth:`Queue.deqmany()`
   - ``Connection.deqoptions()`` with attribute :attr:`Queue.deqoptions`
   - ``Connection.enq()`` with :meth:`Queue.enqone()` or :meth:`Queue.enqmany()`
   - ``Connection.enqoptions()`` with attribute :attr:`Queue.enqoptions`

   See :ref:`aqusermanual`.

9. Remove calls to ``Cursor.executemanyprepared()``. This method was previously
   deprecated in cx_Oracle 6.4 and has been removed in
   python-oracledb. Instead, use :meth:`Cursor.executemany()` by passing *None*
   for the statement argument and an integer for the ``parameters`` argument.

10. Remove the use of the ``Cursor.bindarraysize``. It is desupported and not
    needed in the application code.

11. In python-oracledb, VARCHAR2 and LOB columns that have the ``IS JSON``
    constraint enabled are fetched by default as Python objects. These columns
    are fetched in the same way that :ref:`JSON type columns <json21fetch>` are
    fetched when using Oracle Database 21c (or later). The returned value
    varies depending on the JSON data. If the JSON data is an object, then a
    dictionary is returned.  If it is an array, then a list is returned. If it
    is a scalar value, then that particular scalar value is returned.

    In cx_Oracle, VARCHAR2 and LOB columns that have the ``IS JSON`` constraint
    enabled are fetched by default as strings and LOB objects respectively. To
    enable this same fetch behavior in python-oracledb, you can use an
    :ref:`output type handler <outputtypehandlers>` as shown below.

    .. code-block:: python

        def type_handler(cursor, fetch_info):
            if fetch_info.is_json:
                return cursor.var(fetch_info.type_code, cursor.arraysize)

12. Review uses of :attr:`Cursor.rowcount`. After :meth:`Cursor.execute()` or
    :meth:`Cursor.executemany()` with PL/SQL statements, :attr:`Cursor.rowcount`
    will return *0*. If the cursor or connection are not open, then the value
    *-1* will be returned as required by the Python Database API.

13. In python-oracledb Thick mode, error messages generated by the Oracle
    Client libraries and the `ODPI-C <https://oracle.github.io/odpi/>`_ layer
    used by cx_Oracle and python-oracledb in Thick mode are mostly returned
    unchanged from cx_Oracle 8.3. Some exceptions shown below.

    Note that the python-oracledb driver error messages can also vary between
    Thin and Thick modes. See :ref:`errorhandling`.

    **ConnectionPool.acquire() Message Differences**

    :meth:`ConnectionPool.acquire()` ORA errors will be mapped to DPY errors.
    For example::

        DPY-4005: timed out waiting for the connection pool to return a connection

    replaces the cx_Oracle 8.3 error::

        ORA-24459: OCISessionGet() timed out waiting for pool to create new connections

    **Dead Connection Detection and Timeout Message Differences**

    Application code which detects connection failures or statement execution
    timeouts will need to check for new errors, ``DPY-4011`` and ``DPY-4024``
    respectively. The error ``DPY-1001`` is returned if an already dead connection
    is attempted to be used.

    The new Error object attribute :attr:`~oracledb._Error.full_code` may be
    useful for checking the error code.

    Example error messages are:

    * Scenario 1: An already closed or dead connection was attempted to be used.

      python-oracledb Thin mode Error::

        DPY-1001: not connected to database

      python-oracledb Thick mode Error::

        DPY-1001: not connected to database

      cx_Oracle Error::

        not connected

    * Scenario 2: The database side of the connection was terminated while the
      connection was being used.

      python-oracledb Thin mode Error::

        DPY-4011: the database or network closed the connection

      python-oracledb Thick mode Error::

        DPY-4011: the database or network closed the connection
        DPI-1080: connection was closed by ORA-%d

      cx_Oracle Error::

        DPI-1080: connection was closed by ORA-%d

    * Scenario 3: Statement execution exceeded the :attr:`connection.call_timeout`
      value.

      python-oracledb Thin mode Error::

        DPY-4024: call timeout of {timeout} ms exceeded

      python-oracledb Thick mode Error::

        DPY-4024: call timeout of {timeout} ms exceeded
        DPI-1067: call timeout of %u ms exceeded with ORA-%d

      cx_Oracle Error::

        DPI-1067: call timeout of %u ms exceeded with ORA-%d

14. If your code base uses an older cx_Oracle version, review
    :ref:`deprecations` for additional changes that may be necessary.

15. Modernize code to take advantage of new features, if desired. See the
    :ref:`release notes <releasenotes>`.

16. Review the following sections to see if your application requirements are
    satisfied by python-oracledb Thin mode:

    - :ref:`featuresummary`
    - :ref:`driverdiff`

    If so, then follow :ref:`upgradethin`.

    If your application requirements are not supported by python-oracledb Thin
    mode, then use Thick mode, see :ref:`upgradethick`.

.. _upgradethin:

Additional Upgrade Steps to use python-oracledb Thin Mode
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

To upgrade from cx_Oracle to python-oracledb Thin mode, the following changes
need to be made in addition to the common :ref:`commonupgrade`:

1. Remove calls to :func:`~oracledb.init_oracle_client` since this turns on
   python-oracledb Thick mode.

2. If the ``config_dir`` parameter of :func:`~oracledb.init_oracle_client` had
   been used, then set the new
   :attr:`oracledb.defaults.config_dir <Defaults.config_dir>` attribute to the
   desired value or set the ``config_dir`` parameter in your connection or pool
   creation method call.  For example:

   .. code-block:: python

       oracledb.defaults.config_dir = "/opt/oracle/config"

   or

   .. code-block:: python

       connection = oracledb.connect(user="hr", password=userpwd, dsn="orclpdb",
                                     config_dir="/opt/oracle/config")


   Also, see :ref:`sqlnetclientconfig`.

3. If the ``driver_name`` parameter of :func:`~oracledb.init_oracle_client` had
   been used, then set the new
   :attr:`oracledb.defaults.driver_name <Defaults.driver_name>` attribute to
   the desired value or set the ``driver_name`` parameter when connecting.  The
   convention for this parameter is to separate the product name from the
   product version by a colon and single blank characters. For example:

   .. code-block:: python

       oracledb.defaults.driver_name = "python-oracledb : 1.2.0"

   See :ref:`otherinit`.

4. Remove calls to :func:`oracledb.clientversion()`.

   The :func:`oracledb.clientversion()` function shows the version of the
   Oracle Client libraries being used. Since Oracle Client libraries are not
   used in python-oracledb Thin mode, this function cannot be called. If it is
   called before calling :func:`oracledb.init_oracle_client()`, an exception is
   thrown.

5. To connect using a :ref:`TNS Alias <netservice>` from a ``tnsnames.ora``
   file (see :ref:`optnetfiles`) in python-oracledb Thin mode, you should
   explicitly set the environment variable ``TNS_ADMIN`` to the directory
   containing the file, or set
   :attr:`oracledb.defaults.config_dir <Defaults.config_dir>`, or set the
   ``config_dir`` parameter when connecting.

   A ``tnsnames.ora`` file in a "default" location such as the Instant Client
   ``network/admin/`` subdirectory may not be automatically loaded in Thin mode
   on some platforms. A ``tnsnames.ora`` file identified by the Windows
   registry, or in ``$ORACLE_BASE/homes/XYZ/network/admin/`` (in a read-only
   Oracle Database home) will never be automatically located by
   python-oracledb Thin mode.

   Only python-oracledb Thick mode will read :ref:`sqlnet.ora <optnetfiles>`
   and :ref:`oraaccess.xml <optclientfiles>` files.  The Thin mode lets
   equivalent properties be set in the application when connecting.

6. To use python-oracledb Thin mode in an ``ORACLE_HOME`` database installation
   environment, you must use an explicit connection string since the
   ``ORACLE_SID``, ``TWO_TASK``, and ``LOCAL`` environment variables are not
   used.  They are used in Thick mode.

7. Ensure that any assumptions about when connections are created in the
   connection pool are eliminated.  Python-oracledb Thin mode creates
   connections in a daemon thread and so the attribute
   :attr:`ConnectionPool.opened` will change over time and will not be equal
   to :attr:`ConnectionPool.min` immediately after the pool is created.  Note
   that this behavior is also similar in recent versions of the Oracle Call
   Interface (OCI) Session Pool used by the Thick mode.  Unless the
   ``oracledb.SessionPool()`` function's parameter ``getmode`` is
   :data:`oracledb.POOL_GETMODE_WAIT`, then applications should not call
   :meth:`ConnectionPool.acquire()` until sufficient time has passed for
   connections in the pool to be created.

8. Review locale and globalization usage. Python-oracledb Thin mode ignores
   all NLS environment variables.  It also ignores the ``ORA_TZFILE``
   environment variable.  Thick mode does use these variables.  See
   :ref:`globalization`.

9. If SQL statements contain repeated bind variable placeholder names, and you
   are :ref:`binding by position <bindbyposition>`, then make sure that a value
   is passed for each use of the placeholder, see :ref:`dupbindplaceholders`.

.. _upgradethick:

Additional Upgrade Steps to use python-oracledb Thick Mode
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

To upgrade from cx_Oracle to python-oracledb Thick mode, in addition to the
common :ref:`commonupgrade`, the function :func:`oracledb.init_oracle_client()`
*must* be called to enable the Thick mode.  It can be called anywhere before
the first call to :func:`oracledb.connect()`, ``oracledb.Connection()``, or
``oracledb.SessionPool()``. If a connection or pool is created first in the
default Thin mode, then Thick mode cannot be enabled. See
:ref:`enablingthick` for more details.

The requirement to call :func:`~oracledb.init_oracle_client()` means that
Oracle Client library loading is not automatically deferred until the driver
is first used, such as when a connection is opened. To emulate the cx_Oracle
behavior of deferring library loading until the creation of the first
connection (in the case when :func:`~oracledb.init_oracle_client()` is not
called), your application will need to explicitly defer calling
:func:`~oracledb.init_oracle_client()` as appropriate.

In python-oracledb, :func:`~oracledb.init_oracle_client()` can be called
multiple times in a Python process as long as the arguments are the same.

Note that on Linux and related operating systems, the
:func:`~oracledb.init_oracle_client()` parameter ``lib_dir`` should not be
passed. Instead, set the system library search path with ``ldconfig`` or
``LD_LIBRARY_PATH`` prior to running Python.

Modernizing Code
----------------

Many significant new features have been added to python-oracledb. You may want
to take advantage of them when upgrading from cx_Oracle.  See the rest of the
documentation, the :ref:`release notes <releasenotes>`, and
:ref:`featuresummary`.

The following points summarize some of the smaller changes that you may find
interesting:

- The :meth:`oracledb.makedsn()` method for creating the ``dsn`` value has been
  deprecated.  New code should use keyword arguments when creating connections
  or connection pools, or make use of a ``params`` object described below.

- A new optional parameter ``params`` of type :ref:`ConnectParams <connparam>`
  can be used to encapsulate connection properties.  Similarly a new optional
  parameter ``params`` of type :ref:`PoolParams <poolparam>` can be used to
  encapsulate pool creation properties. See :ref:`usingconnparams` for more
  information.

- The use of the class constructor method ``oracledb.Connection()`` to create
  connections is no longer recommended for creating connections.  Use
  :func:`~oracledb.connect()` instead.

- The new method signature of :attr:`Connection.outputtypehandler` is
  ``handler(cursor, metadata)``. The old signature ``handler(cursor, name,
  default_type, length, precision, scale)`` was deprecated in python-oracledb
  1.4 but will still work and will be removed in a future version.

- The attribute :attr:`Connection.maxBytesPerCharacter` is deprecated. This
  will return a constant value of *4* since encodings are always UTF-8.

- In python-oracledb, the name of the size argument of
  :meth:`Cursor.fetchmany()` is ``size``. This change was done to comply with
  `PEP 249 <https://peps.python.org/pep- 0249/>`_. The previous keyword
  argument name, ``numRows`` is deprecated.

Code to Aid the Upgrade to python-oracledb
------------------------------------------

.. _toggling:

Toggling between Drivers
++++++++++++++++++++++++

The sample `oracledb_upgrade.py <https://github.com/oracle/python-oracledb/
tree/main/samples/oracledb_upgrade.py>`__ shows a way to toggle applications
between cx_Oracle and the two python-oracledb modes.  Note this script cannot
map some functionality such as obsolete cx_Oracle features or error message
changes.

An example application showing this module in use is:

.. code-block:: python

    # test.py

    import oracledb_upgrade as cx_Oracle
    import os

    un = os.environ.get("PYTHON_USERNAME")
    pw = os.environ.get("PYTHON_PASSWORD")
    cs = os.environ.get("PYTHON_CONNECTSTRING")

    connection = cx_Oracle.connect(user=un, password=pw, dsn=cs)
    with connection.cursor() as cursor:
        sql = """select unique client_driver
                 from v$session_connect_info
                 where sid = sys_context('userenv', 'sid')"""
        for r, in cursor.execute(sql):
            print(r)

You can then choose what mode is in use by setting the environment variable
``ORA_PYTHON_DRIVER_TYPE`` to one of "cx", "thin", or "thick"::

    export ORA_PYTHON_DRIVER_TYPE=thin
    python test.py

Output shows that python-oracledb Thin mode was used::

    python-oracledb thn : 3.0.0

You can customize ``oracledb_upgrade.py`` to your needs.  For example, if your
connection and pool creation calls always use keyword parameters, you can
remove the shims that map from positional arguments to keyword arguments.

The simplest form is shown in :ref:`frameworks`.

Testing Which Driver is in Use
++++++++++++++++++++++++++++++

To know whether the driver is cx_Oracle or python-oracledb, you can use code
similar to:

.. code-block:: python

    import oracledb as cx_Oracle
    # or:
    # import cx_Oracle

    if cx_Oracle.__name__ == 'cx_Oracle':
           print('cx_Oracle')
    else:
           print('oracledb')

Another method that can be used to check which driver is in use is to query the
view V$SESSION_CONNECT_INFO, see :ref:`vsessconinfo`.
