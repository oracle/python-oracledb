.. _initialization:

.. currentmodule:: oracledb

****************************
Initializing python-oracledb
****************************

By default, python-oracledb runs in a 'Thin' mode which connects directly to
Oracle Database.  This mode does not need Oracle Client libraries.  However,
some :ref:`additional functionality <featuresummary>` is available when
python-oracledb uses them.  Python-oracledb is said to be in 'Thick' mode when
Oracle Client libraries are used.  Both modes have comprehensive functionality
supporting the Python Database API v2.0 Specification.

Most applications can use python-oracledb Thin mode. The common reasons to use
Thick mode are:

- Your Oracle Database is version 11, or older
- Your database connections require :ref:`Native Network Encryption (NNE) or
  checksumming <nne>`
- You desire to use :ref:`Application Continuity (AC) or Transparent
  Application Continuity (TAC) <appcont>`

All connections in an application use the same mode.  See :ref:`vsessconinfo`
to verify which mode is in use.

If you are upgrading from the obsolete cx_Oracle driver to python-oracledb,
then refer to :ref:`upgrading83` for changes that may be needed.

.. _enablingthick:

Enabling python-oracledb Thick mode
===================================

To change from the default python-oracledb Thin mode to Thick mode:

1. Oracle Client libraries must be available to handle communication to your
   database.  These need to be installed separately, see :ref:`installation`.

   Oracle Client libraries from one of the following can be used:

  - An `Oracle Instant Client
    <https://www.oracle.com/database/technologies/instant-client.html>`__ Basic
    or Basic Light package. This is generally the easiest if you do not already
    have Oracle software installed.

  - A full Oracle Client installation (installed by running the Oracle
    Universal installer ``runInstaller``)

  - An Oracle Database installation, if Python is running on the same machine
    as the database

  The Client library version does not always have to match the Oracle Database
  version.

2. Your application *must* call the function
   :meth:`oracledb.init_oracle_client()` to load the client libraries. For
   example, if the Oracle Instant Client libraries are in
   ``C:\oracle\instantclient_23_5`` on Windows or
   ``$HOME/Downloads/instantclient_23_3`` on macOS, then you can use:

   .. code-block:: python

      import os
      import platform

      import oracledb

      d = None                               # On Linux, no directory should be passed
      if platform.system() == "Darwin":      # macOS
        d = os.environ.get("HOME")+("/Downloads/instantclient_23_3")
      elif platform.system() == "Windows":   # Windows
        d = r"C:\oracle\instantclient_23_5"
      oracledb.init_oracle_client(lib_dir=d)

  The use of a ‘raw’ string ``r"..."`` on Windows means that backslashes are
  treated as directory separators.  On Linux, the libraries must be in the
  system library search path *before* the Python process starts, preferably
  configured with ``ldconfig``.

More details and options are shown in the later sections:

- :ref:`wininit`

- :ref:`macinit`

- :ref:`linuxinit`

**Notes on calling init_oracle_client()**

- The :meth:`~oracledb.init_oracle_client()` function must be called before
  any :ref:`standalone connection <standaloneconnection>` or
  :ref:`connection pool <connpooling>` is created. If a connection or pool
  is first created, then the Thick mode cannot be enabled.

- If you call :meth:`~oracledb.init_oracle_client()` with a ``lib_dir``
  parameter, the Oracle Client libraries are loaded immediately from that
  directory. If you call :meth:`~oracledb.init_oracle_client()` but do *not*
  set the ``lib_dir`` parameter, the Oracle Client libraries are loaded
  immediately using the search heuristics discussed in later sections. Note if
  you set ``lib_dir`` on Linux and related platforms, you must still have
  configured the system library search path to include that directory *before*
  starting Python.

- Once the Thick mode is enabled, you cannot go back to the Thin mode except by
  removing calls to :meth:`~oracledb.init_oracle_client()` and restarting the
  application.

- If Oracle Client libraries cannot be loaded then
  :meth:`~oracledb.init_oracle_client()` will raise an error ``DPI-1047:
  Oracle Client library cannot be loaded``.  To resolve this, review the
  platform-specific instructions below or see :ref:`DPI-1047 <dpi1047>`.
  Alternatively, remove the call to :meth:`~oracledb.init_oracle_client()` and
  use Thin mode. The features supported by Thin mode can be found in
  :ref:`featuresummary`.

- On any operating system, if you set the ``lib_dir`` parameter to the library
  directory of a full database or full client installation (such as from
  running ``runInstaller``), you will need to have previously set the Oracle
  environment, for example by setting the ``ORACLE_HOME`` environment
  variable. Otherwise you will get errors like ``ORA-1804``. You should set
  this variable, and other Oracle environment variables, before starting
  Python, as shown in :ref:`Oracle Environment Variables <envset>`.

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

      oracledb.init_oracle_client(lib_dir=r"C:\instantclient_23_5")

  On Windows, when the path contains backslashes, use a 'raw' string like
  ``r"C:\instantclient_23_5"``.

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

      oracledb.init_oracle_client(lib_dir="/Users/your_username/Downloads/instantclient_23_3")

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

      CLIENT_DIR=~/Downloads/instantclient_23_3
      DPY_DIR=~/.pyenv/versions/3.9.6/lib/python3.9/site-packages/oracledb
      ln -s $CLIENT_DIR/libclntsh.dylib $DPY_DIR

  This can be automated in Python with:

  .. code-block:: python

      CLIENT_DIR = "~/Downloads/instantclient_23_3"
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
``LD_LIBRARY_PATH``.  This must be configured *prior* to running the Python
process. Web servers and other daemons commonly reset environment variables so
using ``ldconfig`` is generally preferred instead.  On some UNIX platforms an
OS specific equivalent, such as ``LIBPATH`` or ``SHLIB_PATH``, is used instead
of ``LD_LIBRARY_PATH``.

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

Tracing Oracle Client Library Loading
-------------------------------------

To trace the loading of Oracle Client libraries, the environment variable
``DPI_DEBUG_LEVEL`` can be set to 64 before starting Python.  At a Windows
command prompt, this could be done with::

    set DPI_DEBUG_LEVEL=64

On Linux and macOS, you might use::

    export DPI_DEBUG_LEVEL=64

When your python-oracledb application is run, logging output is shown on the
terminal.

.. _enablingthin:

Explicitly Enabling python-oracledb Thin Mode
=============================================

Python-oracledb defaults to Thin mode but can be changed to use Thick mode. In
one special case, you may wish to explicitly enable Thin mode by calling
:meth:`oracledb.enable_thin_mode()` which will prevent Thick mode from ever
being used. Most applications will not need to call this method.

To allow application portability, the driver's internal logic allows
applications to initially attempt :ref:`standalone connection
<standaloneconnection>` creation in Thin mode, but then lets them :ref:`enable
Thick mode <enablingthick>` if that connection is unsuccessful.  An example is
when trying to connect to an Oracle Database that turns out to be an old
version that requires Thick mode.  This heuristic means Thin mode is not
enforced until the initial connection is successful.  Since all connections
must be the same mode, any second and subsequent concurrent Thin mode
connection attempt will wait for the initial standalone connection to succeed,
meaning the driver mode is no longer potentially changeable to Thick mode, thus
letting those additional connections be established in Thin mode.

If you have multiple threads concurrently creating standalone Thin mode
connections, you may wish to call :meth:`oracledb.enable_thin_mode()` as part
of your application initialization. This is not required but avoids the mode
determination delay.

The mode determination delay does not affect the following cases, so calling
:meth:`~oracledb.enable_thin_mode()` is not needed for them:

- Single-threaded applications using :ref:`standalone connections
  <standaloneconnection>`.
- Single or multi-threaded applications using
  :ref:`connection pools <connpooling>` (even with ``min`` of 0).

The delay also does not affect applications that have already called
:func:`oracledb.init_oracle_client()` to enable Thick mode.

To explicitly enable Thin mode, call :meth:`~oracledb.enable_thin_mode()`, for
example:

.. code-block:: python

    import oracledb

    oracledb.enable_thin_mode()

Once this method is called, then python-oracledb Thick mode cannot be enabled.
If you call :func:`oracledb.init_oracle_client()`, you will get the following
error::

    DPY-2019: python-oracledb thick mode cannot be used because thin mode has
    already been enabled or a thin mode connection has already been created

If you have already enabled Thick mode by calling
:func:`oracledb.init_oracle_client()` and then call
:meth:`oracledb.enable_thin_mode()`, you will get the following error::

    DPY-2053: python-oracledb thin mode cannot be used because thick mode has
    already been enabled

.. _optconfigfiles:

Optional Oracle Configuration Files
===================================

.. _optnetfiles:

Optional Oracle Net Configuration Files
---------------------------------------

Optional Oracle Net configuration files may be read when connecting or creating
connection pools. These files affect connection behavior. The common files are:

* ``tnsnames.ora``: A configuration file that defines databases aliases and
  their related connection configuration information used for establishing
  connections. See :ref:`TNS Aliases for Connection Strings <netservice>`.

* ``sqlnet.ora``: A configuration file that contains settings for features such
  as connection failover, network encryption, logging, and tracing. The
  ``sqlnet.ora`` file is only used in python-oracledb Thick mode. See
  :ref:`enablingthick`. In python-oracledb Thin mode, many of the equivalent
  settings can be defined as connection time parameters.

See :ref:`usingconfigfiles` to understand how python-oracledb locates the
files.

.. _optclientfiles:

Optional Oracle Client Configuration File
-----------------------------------------

When python-oracledb Thick mode uses Oracle Client libraries version 12.1 or
later, an optional client parameter file called ``oraaccess.xml`` can be used
to configure some behaviors of those libraries, such as statement caching and
prefetching.  This can be useful to change application behavior if the
application code cannot be altered.

A sample ``oraaccess.xml`` file that sets the Oracle client ':ref:`prefetch
<tuningfetch>`' value to 1000 rows for every query in the application is::

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
file.

For another way to set some python-oracledb behaviors without changing
application code, see :ref:`pyoparams`.

.. _usingconfigfiles:

Using Optional Oracle Configuration Files
-----------------------------------------

If you use optional Oracle configuration files such as ``tnsnames.ora``,
``sqlnet.ora``, or ``oraaccess.xml`` to configure your connections, then put
the files in a directory accessible to python-oracledb and follow steps shown
below.

Note that the :ref:`Easy Connect syntax <easyconnect>` can set many common
configuration options without needing ``tnsnames.ora``, ``sqlnet.ora``, or
``oraaccess.xml`` files.

**Locating tnsnames.ora in python-oracledb Thin mode**

Python-oracledb will read a ``tnsnames.ora`` file when a :ref:`TNS Alias
<netservice>` is used for the ``dsn`` parameter of :meth:`oracledb.connect()`,
:meth:`oracledb.create_pool()`, :meth:`oracledb.connect_async()`, or
:meth:`oracledb.create_pool_async()`. Only one ``tnsnames.ora`` file is
read. If the TNS Alias is not found in that file, then connection will fail.
Thin mode does not read other configuration files such as ``sqlnet.ora`` or
``oraaccess.xml``.

In python-oracledb Thin mode, you should explicitly specify the directory
because some traditional "default" locations such as
``$ORACLE_BASE/homes/XYZ/network/admin/`` (in a read-only Oracle Database home)
or the Windows registry are not automatically used.

The directory used to locate ``tnsnames.ora`` is determined as follows (first
one wins):

- the value of the method parameter ``config_dir``

  .. code-block:: python

      connection = oracledb.connect(user="hr", password=userpwd, dsn="orclpdb",
                                    config_dir="/opt/oracle/config")

- the value in the ``config_dir`` attribute of the method parameter ``params``

  .. code-block:: python

      params = oracledb.ConnectParams(config_dir="/opt/oracle/config")
      connection = oracledb.connect(user="hr", password=userpwd, dsn="orclpdb", params=params)

- the value of :attr:`oracledb.defaults.config_dir <Defaults.config_dir>`,
  which may have been set explicitly to a directory, or internally set during
  initialization to ``$TNS_ADMIN`` or ``$ORACLE_HOME/network/admin``.

  .. code-block:: python

      oracledb.defaults.config_dir = "/opt/oracle/config"
      connection = oracledb.connect(user="hr", password=userpwd, dsn="orclpdb")

This order also applies to python-oracledb Thick mode when
:attr:`oracledb.defaults.thick_mode_dsn_passthrough` is *False*.

**Locating tnsnames.ora, sqlnet.ora or oraaccess.xml in python-oracledb Thick mode**

In python-oracledb Thick mode, the directory containing the optional Oracle
Client configuration files such as ``tnsnames.ora``, ``sqlnet.ora``, and
``oraaccess.xml`` can be explicitly specified, otherwise the Oracle Client
libraries will use a heuristic to locate the directory.

If :attr:`oracledb.defaults.thick_mode_dsn_passthrough` is *False*, then the
following applies to all files except ``tnsnames.ora``.

The configuration file directory is determined as follows:

- From the ``config_dir`` parameter in the
  :meth:`oracledb.init_oracle_client()` call:

  .. code-block:: python

        oracledb.init_oracle_client(config_dir="/opt/oracle/config")

  On Windows, when the path contains backslashes, use a 'raw' string like
  ``r"C:\instantclient_23_5"``.

- If :meth:`~oracledb.init_oracle_client()` is called to enable Thick mode but
  ``config_dir`` is not specified, then default directories are searched for
  the configuration files. This is platform specific and controlled by Oracle
  Client. Directories include:

  - Your home directory, using ``$HOME/.tnsnames.ora`` and ``$HOME/.sqlnet.ora``

  - The directory ``/var/opt/oracle`` on Solaris, and ``/etc`` on other UNIX
    platforms.

  - The directory specified by the `TNS_ADMIN <https://www.oracle.com/pls/
    topic/lookup?ctx=dblatest&id=GUID-12C94B15-2CE1-4B98-9D0C-8226A9DDF4CB>`__
    environment variable.

  - For Oracle Instant Client ZIP files, the ``network/admin`` subdirectory of
    Instant Client, for example
    ``/opt/oracle/instantclient_23_5/network/admin``.

  - For Oracle Instant Client RPMs, the ``network/admin`` subdirectory of
    Instant Client, for example
    ``/usr/lib/oracle/23.5/client64/lib/network/admin``.

  - When using libraries from a local Oracle Database or full client
    installation, in ``$ORACLE_HOME/network/admin`` or
    ``$ORACLE_BASE_HOME/network/admin``.

On Windows, in a full database install, the Windows registry may be also be
consulted by Oracle Client.

For information about the search path see `Oracle Net Services Reference
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-
19423B71-3F6C-430F-84CC-18145CC2A818>`__ for more information.

The documentation :ref:`Network Configuration <hanetwork>` has additional
information about some specific Oracle Net configuration useful for
applications.

**Setting thick_mode_dsn_passthrough**

When :ref:`oracledb.defaults.thick_mode_dsn_passthrough <defaults>` is *True*,
it is the Oracle Client libraries that locate and read any optional
``tnsnames.ora`` configuration. This was always the behavior of python-oracledb
Thick mode in versions prior to 3.0, and is the default in python-oracledb 3.0
and later.

Setting :ref:`oracledb.defaults.thick_mode_dsn_passthrough <defaults>` to
*False* makes Thick mode use the same heuristics as Thin mode regarding
connection string parameter handling and reading any optional ``tnsnames.ora``
configuration file.

Files such as ``sqlnet.ora`` and ``oraaccess.xml`` are only used by Thick
mode. They are always located and read by Oracle Client libraries regardless of
the :ref:`oracledb.defaults.thick_mode_dsn_passthrough <defaults>` value. The
directory search heuristic is determined by the Oracle Client libraries at the
time :meth:`oracledb.init_oracle_client()` is called, as shown above.

The :ref:`oracledb.defaults.thick_mode_dsn_passthrough <defaults>` value is
ignored in Thin mode.

.. _envset:

Oracle Environment Variables for python-oracledb
================================================

Some common environment variables that influence python-oracledb are shown
below.  The variables that may be needed depend on how Python is installed, how
you connect to the database, and what optional settings are desired.  It is
recommended to set Oracle variables in the environment before calling Python.
However, they may also be set in the application with ``os.putenv()`` before the
first connection is established.

.. note::

    System environment variables such as ``LD_LIBRARY_PATH`` must be set before
    Python starts.

The common environment variables listed below are supported in python-oracledb.

.. list-table-with-summary:: Common Oracle environment variables supported by python-oracledb
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 20 40 10
    :name: _oracle_environment_variables
    :summary: The first column displays the Oracle Environment Variable. The second column, Purpose, describes what the environment variableis used for. The third column displays whether the environment variable can be used in python-oracledb Thin mode, Thick mode or both.

    * - Oracle Environment Variable
      - Purpose
      - Python-oracledb Mode
    * - LD_LIBRARY_PATH
      - The library search path for platforms like Linux should include the Oracle libraries, for example ``$ORACLE_HOME/lib`` or ``/opt/instantclient_23_5``.

        This variable is not needed if the libraries are located by an alternative method, such as with ``ldconfig``. On other UNIX platforms, you may need to set an OS specific equivalent such as ``LIBPATH`` or ``SHLIB_PATH``.
      - Thick
    * - NLS_DATE_FORMAT, NLS_TIMESTAMP_FORMAT
      - Often set in Python applications to force a consistent date format independent of the locale.

        These variables are ignored if the environment variable ``NLS_LANG`` is not set.
      - Thick
    * - NLS_LANG
      - Determines the 'national language support' globalization options for python-oracledb.

        Note that the character set component is ignored and only the language and territory components of ``NLS_LANG`` are used. The character set can instead be specified during connection or connection pool creation. See :ref:`globalization`.
      - Thick
    * - ORA_SDTZ
      - The default session time zone.
      - Both
    * - ORA_TZFILE
      - The name of the Oracle time zone file to use. See :ref:`timezonefiles`.
      - Thick
    * - ORACLE_HOME
      - The directory containing the Oracle Database software.

        The directory and various configuration files must be readable by the Python process.  This variable should not be set if you are using Oracle Instant Client.
      - Thick
    * - PATH
      - The library search path for Windows should include the location where ``OCI.DLL`` is found.

        This variable is not needed if you set ``lib_dir`` in a call to :meth:`oracledb.init_oracle_client()`.
      - Thick
    * - TNS_ADMIN
      - The directory of optional Oracle Client configuration files such as ``tnsnames.ora`` and ``sqlnet.ora``.

        Generally not needed if the configuration files are in a default location, or if ``config_dir`` was not used in :meth:`oracledb.init_oracle_client()`.  See :ref:`optnetfiles`.
      - Both

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
shown in Oracle Database views like V$SESSION_CONNECT_INFO.  If this parameter
is not specified, then the value specified in the
:attr:`oracledb.defaults.driver_name <defaults.driver_name>` attribute is used.
If the value of this attribute is None, then a value like
``python-oracledb thk : 3.0.0`` is shown, see :ref:`vsessconinfo`.

The ``error_url`` string will be shown in the exception raised if
``init_oracle_client()`` cannot load the Oracle Client libraries.  This allows
applications that use python-oracledb in Thick mode to refer users to
application-specific installation instructions.  If this value is not
specified, then the :ref:`installation` URL is used.

.. _thicktothin:

Migrating from python-oracledb Thick Mode to python-oracledb Thin Mode
======================================================================

Changing an application that currently uses :ref:`Thick mode <enablingthick>`
to use Thin mode requires the removal of calls to
:func:`oracledb.init_oracle_client()` and an application restart.  Other small
changes may be required:

1. Remove *all* calls to :func:`oracledb.init_oracle_client` from the
   application.

2. Review :ref:`featuresummary` and :ref:`driverdiff` for code changes that
   may be needed.

3. Restart your application.

4. Test and validate your application behavior.

When you are satisfied, you can optionally remove Oracle Client libraries. For
example, delete your Oracle Instant Client directory.

You can validate the python-oracledb mode by checking :attr:`Connection.thin`,
:attr:`ConnectionPool.thin`, or by querying the CLIENT_DRIVER column of
V$SESSION_CONNECT_INFO and verifying if the value of the column begins with the
text ``python-oracledb thn``. See :ref:`vsessconinfo`.

Note all connections in a python-oracledb application must use the same mode.

.. _settingdefaults:

Changing python-oracledb Default Settings
=========================================

Python-oracledb has a singleton :ref:`Defaults <defaults>` object with
attributes that set default behaviors of the driver. The object is accessed
using the :data:`defaults` attribute of the imported driver.

For example, to return queried LOB columns directly as strings or bytes:

.. code-block:: python

    import oracledb

    oracledb.defaults.fetch_lobs = False


See :ref:`defaultsattributes` for the attributes that can be set.
