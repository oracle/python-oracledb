.. _upgradecomparison:

*****************************************************
Appendix C: The python-oracledb and cx_Oracle Drivers
*****************************************************

The python-oracledb driver is the renamed, major version successor to
`cx_Oracle 8.3 <https://oracle.github.io/python-cx_Oracle/>`__. As a major
release, the python-oracledb driver has :ref:`new features <releasenotes>` and
some :ref:`deprecations`.  Also see :ref:`upgrading83`.

.. _compatibility:

Differences between the python-oracledb and cx_Oracle Drivers
=============================================================

The differences between the cx_Oracle 8.3 and python-oracledb drivers are
listed here.

Mode differences from cx_Oracle
-------------------------------

By default, python-oracledb runs in a 'Thin' mode which connects directly to
Oracle Database.  This mode does not need Oracle Client libraries.  However,
some :ref:`additional functionality <featuresummary>` is available when
python-oracledb uses them.  Python-oracledb is said to be in 'Thick' mode when
Oracle Client libraries are used.  See :ref:`enablingthick`.  Both modes have
comprehensive functionality supporting the Python Database API v2.0
Specification.

cx_Oracle always runs in a Thick mode using Oracle Client libraries.  The
features in python-oracledb Thick mode and cx_Oracle 8.3 are the same, subject
to the :ref:`new features <releasenotes>`, some :ref:`deprecations
<deprecations>`, and to other changes noted in this section.

Oracle Client Library Loading Differences from cx_Oracle
--------------------------------------------------------

Oracle Client libraries are now only loaded if
:func:`oracledb.init_oracle_client()` is called in your application.  This
changes python-oracledb to Thick mode. The ``init_oracle_client()`` method must
be called before any :ref:`standalone connection <standaloneconnection>` or
:ref:`connection pool <connpooling>` is created. If a connection or pool is
created first in the default Thin mode, then Thick mode cannot be enabled.

See :ref:`enablingthick` for more information.

Calling the ``init_oracle_client()`` method immediately loads Oracle Client
libraries.  To emulate the cx_Oracle behavior of deferring library loading
until the creation of the first connection (in the case when
``init_oracle_client()`` is not called), your application will need to defer
calling ``init_oracle_client()`` as appropriate.

In python-oracledb, ``init_oracle_client()`` can now be called multiple times
in the one Python process as long as its arguments are the same each time.

oracledb.clientversion()
++++++++++++++++++++++++

The :func:`oracledb.clientversion()` method shows the version of the Oracle
Client libraries being used.  There is no Oracle Client used in the
python-oracledb Thin mode so this function can only be called in
python-oracledb Thick mode.  If this function is called before
:func:`oracledb.init_oracle_client()`, an exception is thrown.

Connection Differences from cx_Oracle
-------------------------------------

.. _connectdiffs:

oracledb.connect() Differences
++++++++++++++++++++++++++++++

The :func:`oracledb.connect()` function in the python-oracledb driver differs
from cx_Oracle:

- Keyword parameters **must** be used in calls to :func:`oracledb.connect()`. This
  change makes the driver compliant with the Python Database API specification
  PEP 249.  See :ref:`Standalone Connections <standaloneconnection>` and
  :ref:`connerrors`.

- New keyword arguments can be passed to :func:`~oracledb.connect()`.  For
  example you can pass the hostname, port and servicename as separate
  parameters instead of using an Easy Connect connection string.  In
  python-oracledb Thin mode, some of the new arguments replace ``sqlnet.ora``
  settings.

- A new optional parameter ``params`` of type :ref:`ConnectParams <connparam>`
  can be used to encapsulate connection properties. See :ref:`usingconnparams`
  for more information.

- The following parameters are deprecated and ignored:

  - ``encoding`` and ``nencoding``: The encodings in use are always UTF-8.

  - ``threaded``: Threaded Oracle Call Interface (OCI) is now always enabled in
    Thick mode.  This option is not relevant to the Thin mode.

  See :ref:`deprecations` for more information.

The use of the class constructor method ``oracledb.Connection()`` to create
connections is no longer recommended for creating connections.  Use
:func:`~oracledb.connect()` instead.

Connection Object Differences
+++++++++++++++++++++++++++++

The :ref:`Connection object <connobj>` differences between the python-oracledb
and cx_Oracle drivers are:

- The attribute :attr:`Connection.maxBytesPerCharacter` is deprecated. This will
  return a constant value of 4 since encodings are always UTF-8.

- A new boolean attribute, :attr:`Connection.thin` is available. This
  attribute is True if the connection was established in the Thin mode. In
  Thick mode, the value of this attribute is False.

See :ref:`connattrs` for more information.

Pooling Differences from cx_Oracle
----------------------------------

It is recommended to use the new equivalent :ref:`ConnectionPool Object
<connpool>` instead of the SessionPool object, which is deprecated.  To create
a connection pool, use :meth:`oracledb.create_pool()`, which is equivalent to
calling `cx_Oracle.SessionPool()
<https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.SessionPool>`__.

For more information, see :ref:`connpooling`.

oracledb.SessionPool() Differences
++++++++++++++++++++++++++++++++++

The python-oracledb ``oracledb.SessionPool()`` method (which is an alias of
:func:`oracledb.create_pool()`) differs from `cx_Oracle.SessionPool()
<https://cx-oracle.readthedocs.io/en/latest/api_manual/module.html#cx_Oracle.SessionPool>`_
as follows:

- Keyword parameters **must** be used in calls. This change makes the driver
  compliant with the Python Database API specification PEP 249.  See
  :ref:`Connection pooling <connpooling>` and :ref:`connerrors`.

- Passing a value to the ``dsn`` parameter that contains the user name and
  password is now supported in the same way as :func:`oracledb.connect()`. For
  example ``dsn="un/pw@cs"`` can be used.

- New keyword arguments can be passed to :func:`~oracledb.create_pool()`.  For
  example you can pass the hostname, port and servicename as separate
  parameters instead of using an Easy Connect connection string.  In
  python-oracledb Thin mode, some of the new arguments replace ``sqlnet.ora``
  settings.

- The default mode is :data:`~oracledb.POOL_GETMODE_WAIT` instead of
  :data:`~oracledb.POOL_GETMODE_NOWAIT`. If the mode
  :data:`~oracledb.POOL_GETMODE_NOWAIT` is truly desired, modify any pool
  creation code to specify this value instead.  Note the namespace of constant
  has been improved.  Old names like ``SPOOL_ATTRVAL_NOWAIT`` can be used but are
  now deprecated.

- A new optional parameter ``params`` of type :ref:`PoolParams <poolparam>`
  can be used to encapsulate connection properties. See :ref:`usingconnparams`
  for more information.

- The ``encoding`` and ``decoding`` parameters are deprecated and ignored. The
  encodings in use are always UTF-8.

- New keyword arguments that are used internally to create a :ref:`PoolParams
  object <connparam>` before creating the connection.

SessionPool Object Differences
++++++++++++++++++++++++++++++

The SessionPool object (which is an alias for the :ref:`ConnectionPool object
<connpool>`) differences between the python-oracledb and cx_Oracle drivers are:

- A Python type() will show the class as ``oracledb.ConnectionPool`` instead of
  ``cx_Oracle.SessionPool``.

- A new boolean attribute, ``SessionPool.thin`` (see
  :attr:`ConnectionPool.thin`) is available. This attribute is True if the
  connection was established in the Thin mode. In Thick mode, the value of this
  attribute is False.

Cursor Object Differences from cx_Oracle
----------------------------------------

The differences between the :ref:`Cursor object <cursorobj>` in python-oracledb and
cx_Oracle drivers are:

- :meth:`Cursor.fetchmany()`: The name of the size argument of ``fetchmany()``
  is ``size``. This change was done to comply with `PEP 249
  <https://peps.python.org/pep- 0249/>`_. The previous keyword argument name,
  ``numRows`` is deprecated.

- ``Cursor.fetchraw()``: This method was previously deprecated in cx_Oracle 8.2 and has
  been removed in python-oracledb. Instead, use one of the other fetch methods such as
  :meth:`Cursor.fetchmany()`.

- ``Cursor.executemanyprepared()``: This method was previously deprecated in cx_Oracle 6.4
  and has been removed in python-oracledb. Instead, use :meth:`Cursor.executemany()`,
  by passing None for the statement argument and an integer for the parameters argument.

- ``Cursor.bindarraysize``: This attribute is deprecated and removed in python-oracledb. It is
  not needed in the application code.

- :attr:`Cursor.rowcount`: After :meth:`Cursor.execute()` or
  :meth:`Cursor.executemany()` with PL/SQL statements, ``Cursor.rowcount`` will
  return 0. If the cursor or connection are not open, then the value -1 will be
  returned as required by the Python Database API.

Advanced Queuing (AQ) Differences from cx_Oracle
------------------------------------------------

The old Advanced Queuing (AQ) API is not available in python-oracledb since it was
deprecated in cx_Oracle 7.2. Use the :ref:`new Advanced Queuing (AQ) <aqusermanual>`.
Note that AQ is only available in the Thick mode.

Replace:

- :meth:`Connection.deq()` with :meth:`Queue.deqone()` or :meth:`Queue.deqmany()`
- :meth:`Connection.deqoptions()` with attribute :attr:`Queue.deqoptions`
- :meth:`Connection.enq()` with :meth:`Queue.enqone()` or :meth:`Queue.enqmany()`
- :meth:`Connection.deqoptions()` with attribute :attr:`Queue.deqoptions`

The AQ feature in the python-oracledb driver differs from cx_Oracle as follows:

- AQ messages can be enqueued and dequeued as a JSON payload type
- Recipient lists can be enqueued and dequeued
- Enqueue options, dequeue options, and message properties can be set

See :ref:`Oracle Advanced Queuing (AQ) <aqusermanual>`.

.. _errordiff:

Error Handling Differences from cx_Oracle
-----------------------------------------

In python-oracledb Thick mode, error messages generated by the Oracle Client
libraries and the `ODPI-C <https://oracle.github.io/odpi/>`_ layer used by
cx_Oracle and python-oracledb in Thick mode are mostly returned unchanged from
cx_Oracle 8.3 with the exceptions shown below.

Note that the python-oracledb driver error messages can vary between Thin and
Thick modes. See :ref:`errorhandling`.

ConnectionPool.acquire() Message Differences
++++++++++++++++++++++++++++++++++++++++++++

:meth:`ConnectionPool.acquire()` ORA errors will be mapped to DPY errors.  For
example::

    DPY-4005: timed out waiting for the connection pool to return a connection

replaces the cx_Oracle 8.3 error::

    ORA-24459: OCISessionGet() timed out waiting for pool to create new connections

Dead Connection Detection and Timeout Message Differences
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Application code which detects connection failures or statement execution
timeouts will need to check for new errors, DPY-4011 and DPY-4024 respectively.
The error DPY-1001 is returned if an already dead connection is attempted to be
used.

The new Error object attribute :attr:`~oracledb._Error.full_code` may be useful
for checking the error code.

Example error messages are:

* Scenario 1: An already closed or dead connection was attempted to be used.

  python-oracledb Thin Error::

    DPY-1001: not connected to database

  python-oracledb Thick Error::

    DPY-1001: not connected to database

  cx_Oracle Error::

    not connected

* Scenario 2: The database side of the connection was terminated while the
  connection was being used.

  python-oracledb Thin Error::

    DPY-4011: the database or network closed the connection

  python-oracledb Thick Error::

    DPY-4011: the database or network closed the connection
    DPI-1080: connection was closed by ORA-%d

  cx_Oracle Error::

    DPI-1080: connection was closed by ORA-%d

* Scenario 3: Statement execution exceeded the :attr:`connection.call_timeout`
  value.

  python-oracledb Thin Error::

    DPY-4024: call timeout of {timeout} ms exceeded

  python-oracledb Thick Error::

    DPY-4024: call timeout of {timeout} ms exceeded
    DPI-1067: call timeout of %u ms exceeded with ORA-%d

  cx_Oracle Error::

    DPI-1067: call timeout of %u ms exceeded with ORA-%d

.. _upgrading83:

Upgrading from cx_Oracle 8.3 to python-oracledb
===============================================

This section provides the detailed steps needed to upgrade from cx_Oracle 8.3
to python-oracledb.

Things to Know Before the Upgrade
---------------------------------

Below is a list of some useful things to know before upgrading from cx_Oracle
to python-oracledb:

- You can have both cx_Oracle and python-oracledb installed, and can use both
  in the same application.

- If you only want to use the python-oracledb driver in Thin mode, then you do
  not need Oracle Client libraries such as from Oracle Instant Client.  You
  only need to :ref:`install <installation>` the driver itself::

      python -m pip install oracledb

  See :ref:`driverdiff`.

- The python-oracledb Thin and Thick modes have the same level of support for
  the `Python Database API specification <https://peps.python.org/pep-0249/>`_
  and can be used to connect to on-premises databases and Oracle Cloud
  databases. However, the python-oracledb Thin mode does not support some of
  the advanced Oracle Database features such as Application Continuity (AC),
  Advanced Queuing (AQ), Continuous Query Notification (CQN), and Sharding.
  See :ref:`Features Supported <featuresummary>` for details.

- python-oracledb can be used in SQLAlchemy, Django, Pandas, and other
  frameworks and Object-relational Mappers (ORMs). Until they add native
  support, you can override the use of cx_Oracle with a few lines of code. See
  :ref:`frameworks`.

- python-oracledb connection and pool creation calls require keyword arguments
  to conform with the Python Database API specification.  For example you must
  use:

  .. code-block:: python

       oracledb.connect(user="scott", password=pw, dsn="localhost/orclpdb")

  This no longer works:

  .. code-block:: python

       oracledb.connect("scott", pw, "localhost/orclpdb")

- The python-oracledb Thin mode ignores all NLS environment variables.  It also
  ignores ``ORA_SDTZ`` and ``ORA_TZFILE`` environment variables.  Thick mode does use
  these variables.  See :ref:`globalization` for alternatives.

- To use a ``tnsnames.ora`` file in the python-oracledb Thin mode, you must
  explicitly set the environment variable ``TNS_ADMIN`` to the directory
  containing the file, or set :attr:`defaults.config_dir`, or set the
  ``config_dir`` parameter when connecting.

  Only python-oracledb Thick mode will read ``sqlnet.ora`` files.  The Thin
  mode lets equivalent properties be set in the application when connecting.

  Configuration files in a "default" location such as the Instant Client
  ``network/admin/`` subdirectory, in ``$ORACLE_HOME/network/admin/``, or in
  ``$ORACLE_BASE/homes/XYZ/network/admin/`` (in a read-only Oracle Database
  home) is not automatically loaded in Thin mode.  Default locations are
  automatically searched by Thick mode.

- To use the python-oracledb Thin mode in an ORACLE_HOME database installation
  environment, you use an explicit connection string since the ``ORACLE_SID``,
  ``TWO_TASK`` and ``LOCAL`` environment variables are not used.  They are used
  in Thick mode.

- This is a major release so some previously deprecated features are no longer
  available. See :ref:`deprecations`.

.. _commonupgrade:

Steps to Upgrade to python-oracledb
-----------------------------------

If you are creating new applications, follow :ref:`installation` and refer to
other sections of the documentation for usage information.

To upgrade existing code from cx_Oracle to python-oracledb, perform the
following steps:

1. Install the new python-oracledb module::

        python -m pip install oracledb

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
   combined, for example ``un/pw@cs``, is used. This change makes the driver
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

   - ``encoding`` and ``nencoding`` are ignored by python-oracledb. The
     python-oracledb driver uses UTF-8 exclusively.

   - ``threaded`` is ignored in :func:`oracledb.connect()` and
     ``oracledb.Connection()`` by python-oracledb. This parameter was already
     ignored in ``oracledb.SessionPool()`` from cx_Oracle 8.2.

5. Remove all references to :meth:`Cursor.fetchraw()` as this method was
   deprecated in cx_Oracle 8.2 and has been removed in python-oracledb.
   Instead, use one of the other fetch methods such as
   :meth:`Cursor.fetchmany()`.

6. The default value of the ``oracledb.SessionPool()`` parameter
   :attr:`~Connection.getmode` now waits for an available connection.  That is the
   default is now :data:`~oracledb.SPOOL_ATTRVAL_WAIT` instead of
   :data:`~oracledb.SPOOL_ATTRVAL_NOWAIT`.  The new default value improves the
   behavior for most applications.  If the pool is in the middle of growing, the
   new value prevents transient connection creation errors from occurring when
   using the Thin mode, or when using the Thick mode with recent Oracle
   Client libraries.

   If the old default value is required, modify any pool creation code to
   explicitly specify ``getmode=oracledb.POOL_SPOOL_ATTRVAL_NOWAIT``.

   Note a :ref:`ConnectionPool class <connpool>` deprecates the equivalent
   SessionPool class. The method :meth:`oracledb.create_pool()` deprecates the
   use of ``oracledb.SessionPool()``.  New pool parameter constant names such
   as :data:`~oracledb.POOL_GETMODE_NOWAIT` and :data:`~oracledb.PURITY_SELF`
   are now preferred.  The old namespaces still work.

7. Review the following sections to see if your application requirements are
   satisfied by the python-oracledb Thin mode:

   - :ref:`featuresummary`
   - :ref:`driverdiff`

   If your application requirements are not supported by the Thin mode, then
   use the python-oracledb Thick mode.

8. Review :ref:`compatibility`.

   If your code base uses an older cx_Oracle version, review the previous
   :ref:`release notes <releasenotes>` for additional changes to modernize
   the code.

9. Modernize code as needed or desired.  See :ref:`deprecations` for the list
   of deprecations in python-oracledb 1.0.

Additional Upgrade Steps to use python-oracledb Thin Mode
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

To use python-oracledb Thin mode, the following changes need to be made in
addition to the common :ref:`commonupgrade`:

1. Remove calls to :func:`~oracledb.init_oracle_client` since this turns on the
   python-oracledb Thick mode.

2. If the ``config_dir`` parameter of :func:`~oracledb.init_oracle_client` had
   been used, then set the new :attr:`defaults.config_dir` attribute to the
   desired value or set the ``config_dir`` parameter when connecting.  For
   example:

   .. code-block:: python

       oracledb.defaults.config_dir = "/opt/oracle/config"

   Also see :ref:`sqlnetclientconfig`.

3. If the application is connecting using an :ref:`Oracle Net service name
   <netservice>` from a ``tnsnames.ora`` file located in a "default" location
   such as the Instant Client ``network/admin/`` subdirectory, in
   ``$ORACLE_HOME/network/admin/``, or in
   ``$ORACLE_BASE/homes/XYZ/network/admin/`` (in a read-only Oracle Database
   home), then the configuration file directory must now explicitly be set as
   shown above.

4. Remove calls to :func:`oracledb.clientversion()` which is only available in
   the python-oracledb Thick mode.  Oracle Client libraries are not available
   in Thin mode.

5. Ensure that any assumptions about when connections are created in the
   connection pool are eliminated.  The python-oracledb Thin mode creates
   connections in a daemon thread and so the attribute
   :attr:`ConnectionPool.opened` will change over time and will not be equal to
   :attr:`ConnectionPool.min` immediately after the pool is created.  Note that
   this behavior is also similar in recent versions of the Oracle Call
   Interface (OCI) Session Pool used by the Thick mode.  Unless the
   ``oracledb.SessionPool()`` function's parameter ``getmode`` is
   ``SPOOL_ATTRVAL_WAIT`` (or the new equivalent
   :data:`oracledb.POOL_GETMODE_WAIT`), then applications should not call
   :meth:`ConnectionPool.acquire()` until sufficient time has passed for
   connections in the pool to be created.

6. Review error handling improvements. See :ref:`errorhandling`.

7. Review locale and globalization usage. See :ref:`globalization`.

Additional Upgrade Steps to use python-oracledb Thick Mode
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

To use python-oracledb Thick mode, the following changes need to be made in
addition to the common :ref:`commonupgrade`:

1. The function :func:`~oracledb.init_oracle_client()` *must* be called.  It
   can be called anywhere before the first call to :func:`~oracledb.connect()`,
   ``oracledb.Connection()``, and ``oracledb.SessionPool()``.  This enables the
   Thick mode. See :ref:`enablingthick` for more details.

   The requirement to call ``init_oracle_client()`` means that Oracle Client
   library loading is not automatically deferred until the driver is first
   used, such as when a connection is opened. The application must explicitly
   manage this, if deferral is required.  In python-oracledb,
   ``init_oracle_client()`` can be called multiple times in a Python process as
   long as arguments are the same.

   Note that on Linux and related operating systems, the
   ``init_oracle_client()`` parameter ``lib_dir`` should not be
   passed. Instead, set the system library search path with ``ldconfig`` or
   ``LD_LIBRARY_PATH`` prior to running Python.

2. Replace all usages of the deprecated Advanced Queuing API with the new
   :ref:`AQ API <aqusermanual>` originally introduced in cx_Oracle 7.2, see the
   `cx_Oracle Advanced Queuing (AQ) <https://cx-oracle.readthedocs.io
   /en/latest/api_manual/aq.html>`_ documentation.

3. Review error handling improvements. See :ref:`errorhandling`.

Code to Aid the Upgrade to python-oracledb
------------------------------------------

.. _toggling:

Toggling between Drivers
++++++++++++++++++++++++

The sample `oracledb_upgrade.py
<https://github.com/oracle/python-oracledb/tree/main/samples/oracledb_upgrade.py>`__
shows a way to toggle applications between cx_Oracle and the two
python-oracledb modes.  Note this script cannot map some functionality such as
:ref:`obsolete cx_Oracle <compatibility>` features or error message changes.

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
        sql = """SELECT UNIQUE CLIENT_DRIVER
                 FROM V$SESSION_CONNECT_INFO
                 WHERE SID = SYS_CONTEXT('USERENV', 'SID')"""
        for r, in cursor.execute(sql):
            print(r)

You can then choose what mode is in use by setting the environment variable
``ORA_PYTHON_DRIVER_TYPE`` to one of "cx", "thin", or "thick"::

    export ORA_PYTHON_DRIVER_TYPE=thin
    python test.py

Output shows the python-oracledb Thin mode was used::

    python-oracledb thn : 1.0.0

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

Another method that can be used to check which driver is in use is to query
``V$SESSION_CONNECT_INFO``, see :ref:`vsessconinfo`.

.. _frameworks:

Python Frameworks, SQL Generators, and ORMs
-------------------------------------------

The python-oracledb Thin mode features in the python-oracledb cover the needs
of frameworks that depend upon the Python Database API.

Until SQLAlchemy, Django, other frameworks, object-relational mappers (ORMs),
and libraries add native support for python-oracledb, you can add temporary
code like this to use python-oracledb in-place of cx_Oracle:

.. code-block:: python

    import sys
    import oracledb
    oracledb.version = "8.3.0"
    sys.modules["cx_Oracle"] = oracledb
    import cx_Oracle

.. note::

    The import of cx_Oracle occurs last. This code must be run before the
    library code does its own import of cx_Oracle.
