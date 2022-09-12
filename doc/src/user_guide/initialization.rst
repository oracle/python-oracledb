.. _initialization:

****************************
Initializing python-oracledb
****************************

By default, python-oracledb runs in a 'Thin' mode which connects directly to
Oracle Database.  This mode does not need Oracle Client libraries.  However,
some :ref:`additional functionality <featuresummary>` is available when
python-oracledb uses them.  Python-oracledb is said to be in 'Thick' mode when
Oracle Client libraries are used.  Both modes have comprehensive functionality
supporting the Python Database API v2.0 Specification.

.. _enablingthick:

Enabling python-oracledb Thick mode
===================================

Changing from the default Thin mode to the Thick mode requires the addition of
a call to :func:`oracledb.init_oracle_client()` as shown in sections below.
Other small code updates may also be required, see :ref:`driverdiff` .  If you are
upgrading a cx_Oracle application to python-oracledb, then refer to
:ref:`upgrading83` for changes that may be needed.

.. note::

    To use python-oracledb in Thick mode you *must* call
    :func:`~oracledb.init_oracle_client()` in the application.  It must be
    called before any :ref:`standalone connection <standaloneconnection>` or
    :ref:`connection pool <connpooling>` is created.  If a connection or pool
    is first created, then the Thick mode cannot be enabled.

    All connections in an application use the same mode.

    Once the Thick mode is enabled, you cannot go back to Thin mode.

Enabling the python-oracledb Thick mode loads Oracle Client libraries which
handle communication to your database.  The Oracle Client libraries need to be
installed separately.  See :ref:`installation`.

.. figure:: /images/python-oracledb-thick-arch.png
   :alt: architecture of the python-oracledb driver in Thick mode

   Architecture of the python-oracledb driver in Thick mode

You can validate the python-oracledb mode by querying the ``CLIENT_DRIVER``
column of ``V$SESSION_CONNECT_INFO`` and verifying the value of the column
begins with ``python-oracledb thk``. See :ref:`vsessconinfo`.


.. _libinit:

Setting the Oracle Client Library Directory
-------------------------------------------

When :meth:`~oracledb.init_oracle_client()` is called, python-oracledb
dynamically loads Oracle Client libraries using a search heuristic.  Only the
first set of libraries found are loaded.  The libraries can be:

- in an installation of Oracle Instant Client
- or in a full Oracle Client installation
- or in an Oracle Database installation (if Python is running on the same
  machine as the database).

The versions of Oracle Client and Oracle Database do not have
to be the same.  For certified configurations see Oracle Support's `Doc ID
207303.1
<https://support.oracle.com/epmos/faces/DocumentDisplay?id=207303.1>`__.

See :ref:`installation` for information about installing Oracle Client
libraries.

.. _wininit:

Setting the Oracle Client Directory on Windows
++++++++++++++++++++++++++++++++++++++++++++++

On Windows, python-oracledb Thick mode can be enabled as follows:

- By passing the ``lib_dir`` parameter in a call to
  :meth:`~oracledb.init_oracle_client()`, for example:

  .. code-block:: python

      import oracledb

      oracledb.init_oracle_client(lib_dir=r"C:\instantclient_19_14")

  This directory should contain the libraries from an unzipped Instant
  Client 'Basic' or 'Basic Light' package.  If you pass the library
  directory from a full client or database installation, such as Oracle
  Database "XE" Express Edition, then you will need to have previously set
  your environment to use that same software installation. Otherwise, files
  such as message files will not be located and you may have library
  version clashes.  On Windows, when the path contains backslashes, use a
  'raw' string like ``r"C:\instantclient_19_14"``.

  If the Oracle Client libraries cannot be loaded from ``lib_dir``, then an
  exception is raised.

- By calling :meth:`~oracledb.init_oracle_client()` without passing a
  ``lib_dir`` parameter:

  .. code-block:: python

      import oracledb

      oracledb.init_oracle_client()

  In this case, Oracle Client libraries are first looked for in the
  directory where the python-oracledb binary module is installed.  This
  directory should contain the libraries from an unzipped Instant Client
  'Basic' or 'Basic Light' package.

  If the libraries are not found there, the search looks at the directories
  on the system library search path, for example, the ``PATH`` environment
  variable.

  If the Oracle Client libraries cannot be loaded, then an exception is
  raised.

.. _macinit:

Setting the Oracle Client Directory on macOS
++++++++++++++++++++++++++++++++++++++++++++

On macOS, python-oracledb Thick mode can be enabled as follows:

- By passing the ``lib_dir`` parameter in a call to
  :meth:`~oracledb.init_oracle_client()`, for example:

  .. code-block:: python

      import oracledb

      oracledb.init_oracle_client(lib_dir="/Users/your_username/Downloads/instantclient_19_8")

  This directory should contain the libraries from an unzipped Instant
  Client 'Basic' or 'Basic Light' package.  If the Oracle Client libraries
  cannot be loaded from ``lib_dir``, then an exception is raised.

- By calling :meth:`~oracledb.init_oracle_client()` without passing a
  ``lib_dir`` parameter:

    .. code-block:: python

        import oracledb

        oracledb.init_oracle_client()

  In this case, the Oracle Client libraries are first looked for in the
  directory where the python-oracledb Thick mode binary module is installed.
  This directory should contain the libraries from an unzipped Instant Client
  'Basic' or 'Basic Light' package, or a symbolic link to the main Oracle
  Client library if Instant Client is in a different directory.

  You can find the directory containing the Thick mode binary module by
  calling the python CLI without specifying a Python script, executing
  ``import oracledb``, and then typing ``oracledb`` at the prompt.  For
  example if
  ``/Users/yourname/Library/3.9.6/lib/python3.9/site-packages/oracledb-1.0.0-py3.9-macosx-11.5-x86_64.egg/oracledb``
  contains ``thick_impl.cpython-39-darwin.so``, then you could run ``ln -s
  ~/Downloads/instantclient_19_8/libclntsh.dylib
  ~/Library/3.9.6/lib/python3.9/site-packages/oracledb-1.0.0-py3.9-macosx-11.5-x86_64.egg/oracledb/``.

  If python-oracledb does not find the Oracle Client library in that
  directory, the directories on the system library search path may be used,
  for example, ``~/lib/`` and ``/usr/local/lib``, or in ``$DYLD_LIBRARY_PATH``.
  These paths will vary with macOS version and Python version.  Any value
  in ``DYLD_LIBRARY_PATH`` will not propagate to a sub-shell.

  If the Oracle Client libraries cannot be loaded, then an exception is
  raised.

.. _linuxinit:

Setting the Oracle Client Directory on Linux and Related Platforms
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

On Linux and related platforms, python-oracledb Thick mode can be enabled as
follows:

- By calling :meth:`~oracledb.init_oracle_client()` without passing a
  ``lib_dir`` parameter:

  .. code-block:: python

      import oracledb

      oracledb.init_oracle_client()

  Oracle Client libraries are looked for in the operating system library
  search path, such as configured with ``ldconfig`` or set in the environment
  variable ``LD_LIBRARY_PATH``.  On some UNIX platforms an OS specific
  equivalent, such as ``LIBPATH`` or ``SHLIB_PATH`` is used instead of
  ``LD_LIBRARY_PATH``.

  If libraries are not found in the system library search path, then
  ``$ORACLE_HOME/lib`` will be used.  Note that the environment variable
  ``ORACLE_HOME`` should only ever be set when you have a full database
  installation or full client installation (such as installed with the Oracle
  GUI installer).  It should not be set if you are using Oracle Instant
  Client.  The ``ORACLE_HOME`` variable, and other necessary variables, should
  be set before starting Python.  See :ref:`envset`.

  If the Oracle Client libraries cannot be loaded, then an exception is
  raised.

Ensure that the Python process has directory and file access permissions for
the Oracle Client libraries.  On Linux ensure a ``libclntsh.so`` file exists.
On macOS ensure a ``libclntsh.dylib`` file exists.  python-oracledb Thick will
not directly load ``libclntsh.*.XX.1`` files in ``lib_dir`` or from the directory
where the python-oracledb binary module is available.  Note that other libraries
used by ``libclntsh*`` are also required.

.. _usinginitoracleclient:

Calling oracledb.init_oracle_client() to Set the Oracle Client Directory
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Oracle Client Libraries are loaded when :meth:`oracledb.init_oracle_client()`
is called.  In some environments, applications can use the ``lib_dir``
parameter to specify the directory containing the Oracle Client libraries.
Otherwise, the system library search path should contain the relevant library
directory before Python is invoked.

For example, if the Oracle Instant Client Libraries are in
``C:\oracle\instantclient_19_9`` on Windows or
``$HOME/Downloads/instantclient_19_8`` on macOS (Intel x86), then you can use:

.. code-block:: python

    import oracledb
    import os
    import platform

    d = None  # default suitable for Linux
    if platform.system() == "Darwin" and platform.machine() == "x86_64":
        d = os.environ.get("HOME")+"/Downloads/instantclient_19_8")
    elif platform.system() == "Windows":
        d = r"C:\oracle\instantclient_19_14"
    oracledb.init_oracle_client(lib_dir=d)

Note the use of a 'raw' string ``r"..."`` on Windows so that backslashes are
treated as directory separators.

**Note that if you set** ``lib_dir`` **on Linux and related platforms, you must
still have configured the system library search path to include that directory
before starting Python**.

On any operating system, if you set ``lib_dir`` to the library directory of a
full database or full client installation, you will need to have previously set
the Oracle environment, for example by setting the ``ORACLE_HOME`` environment
variable.  Otherwise, you will get errors like ``ORA-1804``.  You should set this
along with other Oracle environment variables before starting Python as
shown in :ref:`envset`.

**Tracing Oracle Client Libraries Loading**

To trace the loading of Oracle Client libraries, the environment variable
``DPI_DEBUG_LEVEL`` can be set to 64 before starting Python.  For example, on
Linux, you might use::

    $ export DPI_DEBUG_LEVEL=64
    $ python myapp.py 2> log.txt


.. _optnetfiles:

Optional Oracle Net Configuration Files
=======================================

Optional Oracle Net configuration files may be read by python-oracledb.  These
files affect connections and applications.  The common files are:

* ``tnsnames.ora``: A configuration file that defines databases addresses
  for establishing connections. See :ref:`Net Service Name for Connection
  Strings <netservice>`.

* ``sqlnet.ora``: A profile configuration file that may contain information on
  features such as connection failover, network encryption, logging, and
  tracing.  The files should be in a directory accessible to Python, not on the
  database server host.  See `Oracle Net Services Reference
  <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
  id=GUID-19423B71-3F6C-430F-84CC-18145CC2A818>`__ for more information.

  .. note::

      The ``sqlnet.ora`` file is only supported in the python-oracledb Thick
      mode. See :ref:`enablingthick`.

      In the python-oracledb Thin mode, many of the equivalent settings can be
      defined as connection time parameters, for example by using the
      :ref:`ConnectParams Class <connparam>`.

**python-oracledb Thin mode**

In python-oracledb Thin mode applications, you specify the directory that
contains the ``tnsnames.ora`` file by:

- setting the `TNS_ADMIN
  <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-12C94B15-2CE1-4B98-9D0C-8226A9DDF4CB>`__
  environment variable to the directory containing the file

- setting :attr:`defaults.config_dir` to the directory containing the file

- setting the ``config_dir`` parameter to the directory containing the file
  when :func:`connecting <oracledb.connect()>` or creating a
  :func:`connection pool <oracledb.create_pool()>`.

For example:

.. code-block:: python

    import oracledb

    oracledb.defaults.config_dir = "/opt/oracle/config"

.. note::

    In Thin mode, you must explicitly set the directory because traditional
    "default" locations such as the Instant Client ``network/admin/``
    subdirectory, or ``$ORACLE_HOME/network/admin/``, or
    ``$ORACLE_BASE/homes/XYZ/network/admin/`` (in a read-only Oracle Database
    home) are not automatically looked in.

**python-oracledb Thick mode**

In python-oracledb Thick mode, the files are loaded from default locations
(shown below), from the directory also specified in the ``$TNS_ADMIN``
environment variable, or from the directory specified as a parameter in the
:meth:`oracledb.init_oracle_client()` call.  For example, if the file
``/opt/oracle/config/tnsnames.ora`` should be used, you can call:

.. code-block:: python

    import oracledb
    import sys

    try:
        oracledb.init_oracle_client(config_dir="/opt/oracle/config")
    except Exception as err:
        print("Whoops!")
        print(err)
        sys.exit(1)

.. note::

    In python-oracledb Thick mode, once an application has created its first
    connection, trying to change the configuration directory will not have any
    effect.

If :meth:`~oracledb.init_oracle_client()` is called to enable Thick mode but
``config_dir`` is not specified, then default directories are searched for the
configuration files.  They include:

- ``$TNS_ADMIN``

- ``/opt/oracle/instantclient_19_14/network/admin`` if Instant Client is in
  ``/opt/oracle/instantclient_19_14``.

- ``/usr/lib/oracle/19.14/client64/lib/network/admin`` if Oracle 19.6 Instant
  Client RPMs are used on Linux.

- ``$ORACLE_HOME/network/admin`` if python-oracledb Thick is using libraries
  from a database installation.

Note that the :ref:`easyconnect` can set many common configuration options
without needing ``tnsnames.ora`` or ``sqlnet.ora`` files.

The section :ref:`Network Configuration <hanetwork>` has additional information
about Oracle Net configuration.

.. _optclientfiles:

Optional Oracle Client Configuration File
=========================================

When python-oracledb uses Oracle Client libraries version 12.1 or later, an
optional client parameter file called ``oraaccess.xml`` can be used to
configure some behaviors of those libraries, such as statement caching and
prefetching.  This can be useful if the application cannot be altered.  The
file is read from the same directory as the `Optional Oracle Net Configuration
Files`_.

.. note::

  The ``oraaccess.xml`` file is only supported in the python-oracledb Thick
  mode.  See :ref:`enablingthick`.

A sample ``oraaccess.xml`` file that sets the Oracle client 'prefetch' value to
1000 rows.  This value affects every SQL query in the application::

    <?xml version="1.0"?>
     <oraaccess xmlns="http://xmlns.oracle.com/oci/oraaccess"
      xmlns:oci="http://xmlns.oracle.com/oci/oraaccess"
      schemaLocation="http://xmlns.oracle.com/oci/oraaccess
      http://xmlns.oracle.com/oci/oraaccess.xsd">
      <default_parameters>
        <prefetch>
          <rows>1000</rows>
        </prefetch>
      </default_parameters>
    </oraaccess>

Prefetching is the number of additional rows that the underlying Oracle Client
library fetches whenever python-oracledb Thick requests query data from the database.
Prefetching is a tuning option to maximize data transfer efficiency and minimize
:ref:`round-trips <roundtrips>` to the database.  The prefetch size does not
affect when or how many rows are returned by the Thick mode to the application.
The cache management is transparently handled by the Oracle Client libraries.
Note that standard Thick mode fetch tuning is done using :attr:`Cursor.arraysize`, but
changing the prefetch value can be useful in some cases such as when modifying
the application is not feasible.

The `oraaccess.xml` file has other uses including:

- Changing the value of Fast Application Notification :ref:`FAN <fan>` events which affects notifications and Runtime Load Balancing (RLB).
- Configuring `Client Result Caching <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-D2FA7B29-301B-4AB8-8294-2B1B015899F9>`__ parameters
- Turning on `Client Statement Cache Auto-tuning <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-75169FE4-DE2C-431F-BBA7-3691C7C33360>`__

Refer to the documentation on `oraaccess.xml
<https://www.oracle.com/pls/topic/lookup?
ctx=dblatest&id=GUID-9D12F489-EC02-46BE-8CD4-5AECED0E2BA2>`__
for more details.

.. _envset:

Oracle Environment Variables for python-oracledb Thick Mode
===========================================================

Some common environment variables that influence python-oracledb are shown
below.  The variables that may be needed depend on how Python is installed, how
you connect to the database, and what optional settings are desired.  It is
recommended to set Oracle variables in the environment before calling Python.
However, they may also be set in the application with ``os.putenv()`` before the
first connection is established.  System environment variables like
``LD_LIBRARY_PATH`` must be set before Python starts.

.. note::

  These variables, with the exception of ``TNS_ADMIN``, are only supported in
  the python-oracledb Thick mode.  See :ref:`enablingthick`.

.. list-table-with-summary:: Common Oracle environment variables
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 1 2
    :summary: The first column displays the Oracle Environment Variable. The second column, Purpose, describes what the environment variableis used for.
    :align: left

    * - Oracle Environment Variables
      - Purpose
    * - LD_LIBRARY_PATH
      - The library search path for platforms like Linux should include the
        Oracle libraries, for example ``$ORACLE_HOME/lib`` or
        ``/opt/instantclient_19_3``. This variable is not needed if the
        libraries are located by an alternative method, such as with
        ``ldconfig``. On other UNIX platforms, you may need to set an OS
        specific equivalent such as ``LIBPATH`` or ``SHLIB_PATH``.
    * - PATH
      - The library search path for Windows should include the location where
        ``OCI.DLL`` is found.  Not needed if you set ``lib_dir`` in a call to
        :meth:`oracledb.init_oracle_client()`
    * - TNS_ADMIN
      - The directory of optional Oracle Client configuration files such as
        ``tnsnames.ora`` and ``sqlnet.ora``. Not needed if the configuration
        files are in a default location or if ``config_dir`` was not used in
        :meth:`oracledb.init_oracle_client()`.  See :ref:`optnetfiles`.
    * - ORA_SDTZ
      - The default session time zone.
    * - ORA_TZFILE
      - The name of the Oracle time zone file to use.  See below.
    * - ORACLE_HOME
      - The directory containing the Oracle Database software. The directory
        and various configuration files must be readable by the Python process.
        This variable should not be set if you are using Oracle Instant Client.
    * - NLS_LANG
      - Determines the 'national language support' globalization options for
        python-oracledb. Note that from cx_Oracle 8, the character set component is
        ignored and only the language and territory components of ``NLS_LANG``
        are used. The character set can instead be specified during connection
        or connection pool creation. See :ref:`globalization`.
    * - NLS_DATE_FORMAT, NLS_TIMESTAMP_FORMAT
      - Often set in Python applications to force a consistent date format
        independent of the locale. The variables are ignored if the environment
        variable ``NLS_LANG`` is not set.

Oracle Instant Client includes a small and big time zone file, for example
``timezone_32.dat`` and ``timezlrg_32.dat``.  The versions can be shown by running
the utility ``genezi -v`` located in the Instant Client directory.  The small file
contains only the most commonly used time zones.  By default, the larger
``timezlrg_n.dat`` file is used.  If you want to use the smaller ``timezone_n.dat``
file, then set the ``ORA_TZFILE`` environment variable to the name of the file
without any directory prefix. For example ``export ORA_TZFILE=timezone_32.dat``.
With Oracle Instant Client 12.2 or later, you can also use an external time zone
file.  Create a subdirectory ``oracore/zoneinfo`` under the Instant Client
directory, and move the file into it.  Then set ``ORA_TZFILE`` to the file name,
without any directory prefix.  The ``genezi -v`` utility will show the time zone
file in use.

If python-oracledb Thick mode is using Oracle Client libraries from an Oracle
Database or full Oracle Client software installation (such as installed with
Oracle's GUI installer), and you want to use a non-default time zone file, then
set ``ORA_TZFILE`` to the file name with a directory prefix. For example:
``export ORA_TZFILE=/opt/oracle/myconfig/timezone_31.dat``.

The Oracle Database documentation contains more information about time zone
files, see `Choosing a Time Zone File
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-805AB986-DE12-4FEA-AF56-5AABCD2132DF>`__.

.. _otherinit:

Other python-oracledb Thick Mode Initialization
===============================================

The :meth:`oracledb.init_oracle_client()` function allows ``driver_name`` and
``error_url`` parameters to be set.  These are useful for applications whose
end-users are not aware that python-oracledb is being used.  An example of setting
the parameters is:

.. code-block:: python

    import oracledb
    import sys

    try:
        oracledb.init_oracle_client(driver_name="My Great App : 3.1.4",
                                    error_url="https://example.com/MyInstallInstructions.html")
    except Exception as err:
        print("Whoops!")
        print(err)
        sys.exit(1)

The convention for ``driver_name`` is to separate the product name from the
product version by a colon and single blank characters.  The value will be
shown in Oracle Database views like ``V$SESSION_CONNECT_INFO``.  If this
parameter is not specified, then a value like "python-oracledb thk : 1.0.0" is
shown, see :ref:`vsessconinfo`.

The ``error_url`` string will be shown in the exception raised if
``init_oracle_client()`` cannot load the Oracle Client libraries.  This allows
applications that use python-oracledb in Thick mode to refer users to
application-specific installation instructions.  If this value is not
specified, then the :ref:`installation` URL is used.


Changing from python-oracledb Thick Mode to python-oracledb Thin Mode
=====================================================================

Changing an application that currently uses Thin mode requires the removal of
calls to :func:`oracledb.init_oracle_client()` and an application restart.
Other small changes may be required.

All connections in a python-oracledb application must use the same mode.

If you have been using python-oracledb in Thick mode, you can use Thin mode by:

1. Reviewing :ref:`featuresummary` and :ref:`driverdiff` for code changes that
   may be needed.  Also read :ref:`toggling`.

2. Removing all calls to :func:`oracledb.init_oracle_client` from the
   application.

3. Make other necessary changes identified in step 1.

4. When you are satisfied, you can optionally remove Oracle Client
   libraries. For example, delete your Oracle Instant Client directory.

You can validate the python-oracledb mode by querying the ``CLIENT_DRIVER``
column of ``V$SESSION_CONNECT_INFO`` and verifying if the value of the column
begins with ``python-oracledb thn``. See :ref:`vsessconinfo`.
