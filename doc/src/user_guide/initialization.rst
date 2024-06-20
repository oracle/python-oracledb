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

If you are upgrading a cx_Oracle application to python-oracledb, then refer to
:ref:`upgrading83` for changes that may be needed.

To change from the default Thin mode to the Thick mode:

- Oracle Client libraries must be available to handle communication to your
  database.  These need to be installed separately, see :ref:`installation`.

  Various versions of Oracle Client libraries can be used. They do not have to
  match the version of Oracle Database.  Python-oracledb can use the Client
  Libraries from:

  - an installation of `Oracle Instant Client
    <https://www.oracle.com/database/technologies/instant-client.html>`__

  - or a full Oracle Client installation (installed by running the Oracle
    Universal installer ``runInstaller``)

  - or an Oracle Database installation, if Python is running on the same
    machine as the database

- Your application *must* call the function
  :meth:`oracledb.init_oracle_client()`. For example, if the Oracle Instant
  Client libraries are in ``C:\oracle\instantclient_19_17`` on Windows or
  ``$HOME/Downloads/instantclient_19_8`` on macOS (Intel x86), then you can
  use:

  .. code-block:: python

      import os
      import platform

      import oracledb

      d = None  # default suitable for Linux
      if platform.system() == "Darwin" and platform.machine() == "x86_64":   # macOS
        d = os.environ.get("HOME")+("/Downloads/instantclient_19_8")
      elif platform.system() == "Windows":
        d = r"C:\oracle\instantclient_19_18"
      oracledb.init_oracle_client(lib_dir=d)

  The use of a ‘raw’ string ``r"..."`` on Windows means that backslashes are
  treated as directory separators.

  More details and options are shown in the later sections
  :ref:`wininit`, :ref:`macinit`, and :ref:`linuxinit`.

All connections in an application use the same mode.

Once the Thick mode is enabled, you cannot go back to the Thin mode except by
removing calls to :meth:`~oracledb.init_oracle_client()` and restarting the
application.

See :ref:`vsessconinfo` to verify which mode is in use.

**Notes on calling init_oracle_client()**

- The :meth:`~oracledb.init_oracle_client()` function must be called before
  any :ref:`standalone connection <standaloneconnection>` or
  :ref:`connection pool <connpooling>` is created. If a connection or pool
  is first created, then the Thick mode cannot be enabled.

- If you call :meth:`~oracledb.init_oracle_client()` with a ``lib_dir`` parameter,
  the Oracle Client libraries are loaded immediately from that directory. If
  you call :meth:`~oracledb.init_oracle_client()` but do *not* set the ``lib_dir``
  parameter, the Oracle Client libraries are loaded immediately using the
  search heuristics discussed in later sections.

- If Oracle Client libraries cannot be loaded then
  :meth:`~oracledb.init_oracle_client()` will raise an error ``DPI-1047:
  Oracle Client library cannot be loaded``.  To resolve this, review the
  platform-specific instructions below or see :ref:`runtimetroubleshooting`.
  Alternatively, remove the call to :meth:`~oracledb.init_oracle_client()` and
  use Thin mode. The features supported by Thin mode can be found in
  :ref:`driverdiff`.

- If you set ``lib_dir`` on Linux and related platforms, you must still have
  configured the system library search path to include that directory before
  starting Python.

- On any operating system, if you set ``lib_dir`` to the library directory of a
  full database or full client installation (such as from running
  ``runInstaller``), you will need to have previously set the Oracle environment,
  for example by setting the ``ORACLE_HOME`` environment variable. Otherwise you
  will get errors like ``ORA-1804``. You should set this variable, and other
  Oracle environment variables, before starting Python, as shown in :ref:`Oracle
  Environment Variables <envset>`.

- The :meth:`~oracledb.init_oracle_client()` function may be called multiple
  times in your application but must always pass the same arguments.

.. _wininit:

Enabling python-oracledb Thick Mode on Windows
----------------------------------------------

On Windows, the alternative ways to enable Thick mode are:

- By passing the ``lib_dir`` parameter in a call to
  :meth:`~oracledb.init_oracle_client()`, for example:

  .. code-block:: python

      import oracledb

      oracledb.init_oracle_client(lib_dir=r"C:\instantclient_19_18")

  On Windows, when the path contains backslashes, use a 'raw' string like
  ``r"C:\instantclient_19_18"``.

  This directory should contain the libraries from an unzipped `Instant Client
  'Basic' or 'Basic Light' <https://www.oracle.com/au/database/technologies/
  instant-client.html>`__ package.  If you pass the library directory from a
  full client or database installation, such as `Oracle Database “XE” Express
  Edition <https://www.oracle.com/database/technologies/appdev/xe.html>`__,
  then you will need to have previously set your environment to use that same
  software installation. Otherwise, files such as message files will not be
  located and you may have library version clashes.

  If the Oracle Client libraries cannot be loaded, then an exception is
  raised.

- Alternatively, you can call :meth:`~oracledb.init_oracle_client()` without
  passing a ``lib_dir`` parameter:

  .. code-block:: python

      import oracledb

      oracledb.init_oracle_client()

  In this case, Oracle Client libraries are first looked for in the directory
  where the python-oracledb binary module is installed.  This directory should
  contain the libraries from an unzipped `Instant Client 'Basic' or 'Basic
  Light' <https://www.oracle.com/au/database/technologies/instant-client
  .html>`__ package.

  If the libraries are not found there, the search looks at the directories
  on the system library search path, for example, the ``PATH`` environment
  variable.

  If the Oracle Client libraries cannot be loaded, then an exception is
  raised.

.. _macinit:

Enabling python-oracledb Thick Mode on macOS
--------------------------------------------

On macOS, the alternative ways to enable Thick mode are:

- By passing the ``lib_dir`` parameter in a call to
  :meth:`~oracledb.init_oracle_client()`, for example:

  .. code-block:: python

      import oracledb

      oracledb.init_oracle_client(lib_dir="/Users/your_username/Downloads/instantclient_19_8")

  This directory should contain the libraries from an unzipped `Instant Client
  'Basic' or 'Basic Light' <https://www.oracle.com/au/database/technologies/
  instant-client.html>`__ package.

- Alternatively, you can call :meth:`~oracledb.init_oracle_client()` without
  passing a ``lib_dir`` parameter:

  .. code-block:: python

      import oracledb

      oracledb.init_oracle_client()

  In this case, the Oracle Client libraries are first looked for in the
  directory where the python-oracledb Thick mode binary module is installed.
  This directory should contain the libraries from an unzipped `Instant Client
  'Basic' or 'Basic Light'
  <https://www.oracle.com/au/database/technologies/instant-client.html>`__
  package, or a symbolic link to the main Oracle Client library if Instant
  Client is in a different directory.

  You can find the directory containing the Thick mode binary module by calling
  the python CLI without specifying a Python script, executing ``import
  oracledb``, and then typing ``oracledb`` at the prompt.  For example this
  might show
  ``/Users/yourname/.pyenv/versions/3.9.6/lib/python3.9/site-packages/oracledb/__init__.py``.
  After checking that
  ``/Users/yourname/.pyenv/versions/3.9.6/lib/python3.9/site-packages/oracledb``
  contains the binary module ``thick_impl.cpython-39-darwin.so`` you could then
  run these commands in a terminal window::

      CLIENT_DIR=~/Downloads/instantclient_19_8
      DPY_DIR=~/.pyenv/versions/3.9.6/lib/python3.9/site-packages/oracledb
      ln -s $CLIENT_DIR/libclntsh.dylib $DPY_DIR

  This can be automated in Python with:

  .. code-block:: python

      CLIENT_DIR = "~/Downloads/instantclient_19_8"
      LIB_NAME = "libclntsh.dylib"

      import os
      import oracledb

      target_dir = oracledb.__path__[0]
      os.symlink(os.path.join(CLIENT_DIR, LIB_NAME),
                 os.path.join(target_dir, LIB_NAME))

  If python-oracledb does not find the Oracle Client library in that directory,
  the directories on the system library search path may be used, for example,
  ``~/lib/`` and ``/usr/local/lib``, or in ``$DYLD_LIBRARY_PATH``.  These paths
  will vary with macOS version and Python version.  Any value in
  ``DYLD_LIBRARY_PATH`` will not propagate to a sub-shell, so do not rely on
  setting it.

  If the Oracle Client libraries cannot be loaded, then an exception is
  raised.

Ensure that the Python process has directory and file access permissions for
the Oracle Client libraries.

.. _linuxinit:

Enabling python-oracledb Thick Mode on Linux and Related Platforms
------------------------------------------------------------------

On Linux and related platforms, enable Thick mode by calling
:meth:`~oracledb.init_oracle_client()` without passing a ``lib_dir``
parameter.

.. code-block:: python

    import oracledb

    oracledb.init_oracle_client()

Oracle Client libraries are looked for in the operating system library search
path, such as configured with ``ldconfig`` or set in the environment variable
``LD_LIBRARY_PATH``.  Web servers and other daemons commonly reset environment
variables so using ``ldconfig`` is generally preferred instead.  On some UNIX
platforms an OS specific equivalent, such as ``LIBPATH`` or ``SHLIB_PATH``, is
used instead of ``LD_LIBRARY_PATH``.

If libraries are not found in the system library search path, then libraries
in ``$ORACLE_HOME/lib`` will be used.  Note that the environment variable
``ORACLE_HOME`` should only ever be set when you have a full database
installation or full client installation (such as installed with the Oracle
GUI installer).  It should not be set if you are using `Oracle Instant Client
<https://www.oracle.com/au/database/technologies/instant-client.html>`__. If
being used, ``ORACLE_HOME`` and other necessary Oracle environment variables
should be set before starting Python.  See :ref:`envset`.

If the Oracle Client libraries cannot be loaded, then an exception is
raised.

On Linux, python-oracledb Thick mode will not automatically load Oracle Client
library files from the directory where the python-oracledb binary module is
located.  One of the above methods should be used instead.

Ensure that the Python process has directory and file access permissions for
the Oracle Client libraries.  OS restrictions may prevent the opening of Oracle
Client libraries installed in unsafe paths, such as from a user directory.  You
may need to install the Oracle Client libraries under a directory like ``/opt``
or ``/usr/local``.

Tracing Oracle Client Libraries Loading
---------------------------------------

To trace the loading of Oracle Client libraries, the environment variable
``DPI_DEBUG_LEVEL`` can be set to 64 before starting Python.  At a Windows
command prompt, this could be done with::

    set DPI_DEBUG_LEVEL=64

On Linux and macOS, you might use::

    export DPI_DEBUG_LEVEL=64

When your python-oracledb application is run, logging output is shown on the
terminal.

.. _optconfigfiles:

Optional Oracle Configuration Files
===================================

.. _optnetfiles:

Optional Oracle Net Configuration Files
---------------------------------------

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

  The ``sqlnet.ora`` file is only used in the python-oracledb Thick mode. See
  :ref:`enablingthick`. In the python-oracledb Thin mode, many of the
  equivalent settings can be defined as connection time parameters, for
  example by using the :ref:`ConnectParams Class <connparam>`.

See :ref:`usingconfigfiles` to understand how python-oracledb locates the
files.

.. _optclientfiles:

Optional Oracle Client Configuration File
-----------------------------------------

When python-oracledb Thick mode uses Oracle Client libraries version 12.1 or
later, an optional client parameter file called ``oraaccess.xml`` can be used
to configure some behaviors of those libraries, such as statement caching and
prefetching.  This can be useful if the application cannot be altered.  The
file is read from the same directory as the `Optional Oracle Net Configuration
Files`_.

.. note::

    The ``oraaccess.xml`` file is only used in the python-oracledb Thick mode.
    See :ref:`enablingthick`.

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

See :ref:`tuningfetch` for information about prefetching.

The ``oraaccess.xml`` file has other uses including:

- Changing the value of Fast Application Notification :ref:`FAN <fan>` events
  which affects notifications and Runtime Load Balancing (RLB).
- Configuring `Client Result Caching <https://www.oracle.com/pls/topic/lookup?
  ctx=dblatest&id=GUID-D2FA7B29-301B-4AB8-8294-2B1B015899F9>`__ parameters.
- Turning on `Client Statement Cache Auto-tuning <https://www.oracle.com/pls/
  topic/lookup?ctx=dblatest&id=GUID-75169FE4-DE2C-431F-BBA7-3691C7C33360>`__.

Refer to the documentation on `oraaccess.xml <https://www.oracle.com/pls/topic
/lookup?ctx=dblatest&id=GUID-9D12F489-EC02-46BE-8CD4-5AECED0E2BA2>`__
for more details.

See :ref:`usingconfigfiles` to understand how python-oracledb locates the
files.

.. _usingconfigfiles:

Using Optional Oracle Configuration Files
-----------------------------------------

If you use optional Oracle configuration files such as ``tnsnames.ora``,
``sqlnet.ora`` or ``oraaccess.xml``, then put the files in an accessible
directory and follow the Thin or Thick mode instructions below.

The files should be in a directory accessible to Python, not on the database
server host.

**For python-oracledb Thin mode**

In python-oracledb Thin mode, you must specify the directory that contains the
``tnsnames.ora`` file by either:

- Setting the `TNS_ADMIN <https://www.oracle.com/pls/topic/lookup?ctx=dblatest
  &id=GUID-12C94B15-2CE1-4B98-9D0C-8226A9DDF4CB>`__ environment variable to the
  directory containing the file

- Or setting :attr:`defaults.config_dir` to the directory containing the file.
  For example:

  .. code-block:: python

        import oracledb

        oracledb.defaults.config_dir = "/opt/oracle/config"

- Or setting the ``config_dir`` parameter to the directory containing the file
  when :func:`connecting <oracledb.connect()>` or creating a
  :func:`connection pool <oracledb.create_pool()>`. For example:

  .. code-block:: python

        connection = oracledb.connect(user="hr", password=userpwd, dsn="orclpdb",
                                  config_dir="/opt/oracle/config")

On Windows, when the path contains backslashes, use a 'raw' string like
``r"C:\instantclient_19_18"``.

.. note::

    In Thin mode, you must explicitly set the directory because traditional
    "default" locations such as the Instant Client ``network/admin/``
    subdirectory, or ``$ORACLE_HOME/network/admin/``, or
    ``$ORACLE_BASE/homes/XYZ/network/admin/`` (in a read-only Oracle Database
    home) are not automatically looked in.

**For python-oracledb Thick mode**

In python-oracledb Thick mode, the directory containing the optional files can
be explicitly specified or a default location will be used. Do one of:

- Set the ``config_dir`` parameter to the directory containing the files
  in the :meth:`oracledb.init_oracle_client()` call:

  .. code-block:: python

        oracledb.init_oracle_client(config_dir="/opt/oracle/config")

  On Windows, when the path contains backslashes, use a 'raw' string like
  ``r"C:\instantclient_19_18"``.

.. note::

    In python-oracledb Thick mode, once an application has created its first
    connection, trying to change the configuration directory will not have any
    effect.

- If :meth:`~oracledb.init_oracle_client()` is called to enable Thick mode but
  ``config_dir`` is not specified, then default directories are searched for the
  configuration files.  They include:

  - The directory specified by the `TNS_ADMIN <https://www.oracle.com/pls/
    topic/lookup?ctx=dblatest&id=GUID-12C94B15-2CE1-4B98-9D0C-8226A9DDF4CB>`__
    environment variable.

  - For Oracle Instant Client ZIP files, the ``network/admin`` subdirectory of
    Instant Client, for example
    ``/opt/oracle/instantclient_19_18/network/admin``.

  - For Oracle Instant RPMs, the ``network/admin`` subdirectory of Instant
    Client, for example ``/usr/lib/oracle/19.18/client64/lib/network/admin``.

  - When using libraries from a local Oracle Database or full client
    installation, in ``$ORACLE_HOME/network/admin`` or
    ``$ORACLE_BASE_HOME/network/admin``.

Note that the :ref:`easyconnect` can set many common configuration options
without needing ``tnsnames.ora`` or ``sqlnet.ora`` files.

The section :ref:`Network Configuration <hanetwork>` has additional information
about Oracle Net configuration.

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

    The variables listed below are only supported in the python-oracledb Thick
    mode, with the exception of ``TNS_ADMIN`` and ``ORA_SDTZ`` which are also
    supported in the python-oracledb Thin mode.

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
        ``/opt/instantclient_19_18``. This variable is not needed if the
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
From Oracle Instant Client 12.2, you can also use an external time zone file.
Create a subdirectory ``oracore/zoneinfo`` under the Instant Client directory,
and move the file into it.  Then set ``ORA_TZFILE`` to the file name, without
any directory prefix.  The ``genezi -v`` utility will show the time zone file
in use. With Oracle Instant Client 19.18 (or later), you can alternatively
place the external time zone file in any directory and then set the
``ORA_TZFILE`` environment variable to the absolute path of the file.

If python-oracledb Thick mode is using Oracle Client libraries from an Oracle
Database or full Oracle Client software installation (such as installed with
Oracle's GUI installer), and you want to use a non-default time zone file, then
set ``ORA_TZFILE`` to the file name with a directory prefix. For example:
``export ORA_TZFILE=/opt/oracle/myconfig/timezone_31.dat``.

The Oracle Database documentation contains more information about time zone
files, see `Choosing a Time Zone File <https://www.oracle.com/pls/topic/
lookup?ctx=dblatest&id=GUID-805AB986-DE12-4FEA-AF56-5AABCD2132DF>`__.

.. _otherinit:

Other python-oracledb Thick Mode Initialization
===============================================

The :meth:`oracledb.init_oracle_client()` function allows ``driver_name`` and
``error_url`` parameters to be set.  These are useful for applications whose
end-users are not aware that python-oracledb is being used.  An example of
setting the parameters is:

.. code-block:: python

    oracledb.init_oracle_client(driver_name="My Great App : 3.1.4",
                                error_url="https://example.com/MyInstallInstructions.html")

The convention for ``driver_name`` is to separate the product name from the
product version by a colon and single blank characters.  The value will be
shown in Oracle Database views like ``V$SESSION_CONNECT_INFO``.  If this
parameter is not specified, then a value like ``python-oracledb thk : 1.2.0``
is shown, see :ref:`vsessconinfo`.

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
begins with the text ``python-oracledb thn``. See :ref:`vsessconinfo`.
