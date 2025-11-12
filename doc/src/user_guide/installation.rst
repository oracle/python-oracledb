.. _installation:

.. currentmodule:: oracledb

***************************
Installing python-oracledb
***************************

The python-oracledb driver allows Python applications to connect to Oracle
Database with no extra libraries needed.

.. figure:: /images/python-oracledb-thin-arch.png
   :alt: architecture of the python-oracledb driver

   Architecture of the python-oracledb driver

By default, python-oracledb runs in a 'Thin' mode which connects directly to
Oracle Database.  This mode does not need Oracle Client libraries.  However,
some :ref:`additional functionality <featuresummary>` is available when
python-oracledb uses them.  Python-oracledb is said to be in 'Thick' mode when
Oracle Client libraries are used.  See :ref:`enablingthick`. Both modes have
comprehensive functionality supporting the Python Database API v2.0
Specification.

.. _quickstart:

Quick Start python-oracledb Installation
========================================

Python-oracledb is typically installed from Python's package repository `PyPI
<https://pypi.org/project/oracledb/>`__ using `pip
<https://pip.pypa.io/en/latest/installation/>`__ or `uv
<https://pypi.org/project/uv/>`__.

1. Install `Python 3 <https://www.python.org/downloads>`__ if it is not already
   available.

   Use any version from Python 3.9 through 3.14.

   Previous versions of python-oracledb supported older Python versions.

2. Install python-oracledb, for example:

  .. code-block:: shell

      python -m pip install oracledb --upgrade --user

  Note the module name is simply ``oracledb``.

  On some platforms the Python binary may be called ``python3`` instead of
  ``python``.

  If you are behind a proxy, use the ``--proxy`` option. For example:

  .. code-block:: shell

      python -m pip install oracledb --upgrade --user --proxy=http://proxy.example.com:80

  By default, python-oracledb connects directly to Oracle Database.  This lets
  it be used immediately without needing any additional installation of Oracle
  Client libraries.

3. Create a file ``test.py`` such as:

  .. code-block:: python

      import oracledb
      import getpass

      un = "scott"
      cs = "localhost/orclpdb"
      # cs = "localhost/freepdb1"   # for Oracle AI Database Free users
      # cs = "localhost/orclpdb1"   # some databases may have this service
      pw = getpass.getpass(f"Enter password for {un}@{cs}: ")

      with oracledb.connect(user=un, password=pw, dsn=cs) as connection:
          with connection.cursor() as cursor:
              sql = "select sysdate from dual"
              for r in cursor.execute(sql):
                  print(r)

4. Edit ``test.py`` and set the ``un`` and ``cs`` variables to your own
   database username and the database connection string, respectively.

   A simple :ref:`connection <connhandling>` to the database requires an Oracle
   Database `user name and password
   <https://www.youtube.com/watch?v=WDJacg0NuLo>`_ and a database
   :ref:`connection string <connstr>`.  For python-oracledb, a common
   connection string format is ``hostname:port/servicename``, using the host
   name where the database is running, the Oracle Database service name of the
   database instance, and the port that the database is using. If the default
   port 1521 is being used, then this component of the connection string is
   often omitted.

   The database can be on-premises or in the :ref:`Cloud <autonomousdb>`.  The
   python-oracledb driver does not include a database.

5. Run the program:

   .. code-block:: shell

      python test.py

   Enter the database password when prompted and the queried date will be shown,
   for example:

   .. code-block:: shell

      Enter password for cj@localhost/orclpdb: xxxxxxxxxx
      (datetime.datetime(2024, 4, 30, 8, 24, 4),)

If you have trouble installing, refer to detailed instructions below, or see
:ref:`troubleshooting`.

You can learn more about python-oracledb from the `python-oracledb
documentation <https://python-oracledb.readthedocs.io/en/latest/index.html>`__
and `samples <https://github.com/oracle/python-oracledb/tree/main/samples>`__.

Supported Oracle Database Versions
==================================

When python-oracledb is used in the default Thin mode, it connects directly to
the Oracle Database and does not require Oracle Client libraries.  Connections
in this mode can be made to Oracle Database 12.1 or later.

To connect to older Oracle Database releases you must have Oracle Client
libraries installed, and enable python-oracledb's :ref:`Thick mode
<enablingthick>`.

In python-oracledb Thick mode, Oracle Database's standard client-server
network interoperability allows connections between different versions of
Oracle Client libraries and Oracle Database.  For current or previously
certified configurations, see Oracle Support's `Doc ID 207303.1
<https://support.oracle.com/knowledge/Oracle%20Database%20Products/207303_1.html>`__.
In summary:

- Oracle Client 23 can connect to Oracle Database 19 or later
- Oracle Client 21 can connect to Oracle Database 12.1 or later
- Oracle Client 19, 18 and 12.2 can connect to Oracle Database 11.2 or later
- Oracle Client 12.1 can connect to Oracle Database 10.2 or later
- Oracle Client 11.2 can connect to Oracle Database 9.2 or later

Any attempt to use Oracle Database features that are not supported by a
particular mode or client library/database combination will result in runtime
errors.  The python-oracledb attribute :attr:`Connection.thin` can be used to
see what mode a connection is in.  In the Thick mode, the function
:func:`oracledb.clientversion()` can be used to determine which Oracle Client
version is in use. The attribute :attr:`Connection.version` can be used to
determine which Oracle Database version a connection is accessing. These
attributes can then be used to adjust the application behavior accordingly.

Note Oracle maintains a list of database versions that problem resolution and
error correction can be obtained for, see `Release Schedule of Current Database
Releases <https://support.oracle.com/epmos/faces/DocumentDisplay?
id=742060.1>`__.

.. _instreq:

Installation Requirements
=========================

To use python-oracledb, you need:

- Python 3.9, 3.10, 3.11, 3.12, 3.13, or 3.14

- The Python cryptography package. This package is automatically installed as a
  dependency of python-oracledb.  It is strongly recommended that you keep the
  cryptography package up to date whenever new versions are released.  If the
  cryptography package is not available, you can still install python-oracledb
  but can only use it in Thick mode, see :ref:`nocrypto`.

- Optionally, Oracle Client libraries can be installed to enable some
  additional advanced functionality. These can be from the free `Oracle Instant
  Client <https://www.oracle.com/database/technologies/instant-client.html>`__
  Basic or Basic Light packages, from a full Oracle Client installation (such
  as installed by Oracle's GUI installer), or from those included in Oracle
  Database if Python is on the same machine as the database.  Oracle Client
  libraries versions 23, 21, 19, 18, 12, and 11.2 can be used where available
  on Linux, Windows, and macOS.  Oracle's standard client-server version
  interoperability allows connection to both older and newer databases.

- An Oracle Database either local or remote, on-premises or in the Cloud.

Installing python-oracledb on Linux
===================================

This section discusses the generic installation methods on Linux.

Install python-oracledb
------------------------

The generic way to install python-oracledb on Linux is to use Python's `pip
<https://pip.pypa.io/en/latest/>`__ package to install from Python's package
repository `PyPI <https://pypi.org/project/oracledb/>`__:

.. code-block:: shell

    python -m pip install oracledb --upgrade

This will download and install a pre-compiled binary from `PyPI
<https://pypi.org/project/oracledb/>`__ if one is available for your
architecture.  Otherwise, the source will be downloaded, compiled, and the
resulting binary installed.  Compiling python-oracledb requires the
``Python.h`` header file.  If you are using the default ``python`` package,
this file is in the ``python-devel`` package or equivalent.

On some platforms the Python binary may be called ``python3`` instead of
``python``.

The installation ``--user`` option is useful when you do not have permission to
write to system directories:

.. code-block:: shell

    python -m pip install oracledb --upgrade --user

If you are behind a proxy, use the ``--proxy`` option. For example:

.. code-block:: shell

    python -m pip install oracledb --upgrade --proxy=http://proxy.example.com:80


Optionally Install Oracle Client
--------------------------------

By default, python-oracledb runs in a Thin mode which connects directly to
Oracle Database so no further installation steps are required.  However, to use
additional features available in :ref:`Thick mode <featuresummary>` you need
Oracle Client libraries installed.  Oracle Client versions 23, 21, 19, 18, 12,
and 11.2 can be used.

- If your database is on a remote computer, then download the free `Oracle
  Instant Client
  <https://www.oracle.com/database/technologies/instant-client.html>`__ "Basic"
  or "Basic Light" package for your operating system architecture.

- Alternatively, use the client libraries already available in a locally
  installed database such as the free `Oracle AI Database Free
  <https://www.oracle.com/database/free/>`__ release.

To use python-oracledb in Thick mode you must call
:meth:`oracledb.init_oracle_client()` in your application, see
:ref:`enablingthick`. For example:

.. code-block:: python

    import oracledb

    oracledb.init_oracle_client()

On Linux, do not pass the ``lib_dir`` parameter to
:meth:`~oracledb.init_oracle_client()`.  The Oracle Client libraries on Linux
must be in the system library search path *before* the Python process starts.


Oracle Instant Client Zip Files
+++++++++++++++++++++++++++++++

To use python-oracledb Thick mode with Oracle Instant Client zip files:

1. Download an Oracle 23, 21, 19, 18, 12, or 11.2 "Basic" or "Basic Light" zip
   file matching your Python 64-bit or 32-bit architecture:

  - `Linux 64-bit (x86-64)
    <https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html>`__
  - `Linux 32-bit (x86)
    <https://www.oracle.com/database/technologies/instant-client/linux-x86-32-downloads.html>`__
  - `Linux Arm 64-bit (aarch64)
    <https://www.oracle.com/database/technologies/instant-client/linux-arm-aarch64-downloads.html>`__

  Oracle Instant Client version 23 will connect to Oracle Database 19 or later.
  Oracle Instant Client version 19 will connect to Oracle Database 11.2 or
  later.

  Oracle Database versions 23 and 19 are Long Term Support Releases. Note
  32-bit clients are not available on any platform for Oracle Database version
  23, however you can use older 32-bit clients to connect to this version of
  the database.

  It is recommended to keep up to date with the latest Oracle Instant Client
  release updates of your desired major version.

2. Unzip the package into a single directory that is accessible to your
   application. For example:

   .. code-block:: shell

       mkdir -p /opt/oracle
       cd /opt/oracle
       unzip instantclient-basic-linux.x64-21.6.0.0.0.zip

   Note OS restrictions may prevent the opening of Oracle Client libraries
   installed in unsafe paths, such as from a user directory.  You may need to
   install under a directory like ``/opt`` or ``/usr/local``.

3. Install the ``libaio`` package with sudo or as the root user. For example:

   .. code-block:: shell

       sudo dnf install libaio

   On some Linux distributions this package is called ``libaio1`` or
   ``libaio1t64`` instead.

   If you have ``libaio1t64`` installed but Instant Client still fails to find
   ``libaio.so.1``, you may need to create a symbolic link from
   ``libaio.so.1t64`` to ``libaio.so.1`` (similar to `the patch here
   <https://git.hadrons.org/cgit/debian/pkgs/libaio.git/commit/?id=
   26cf01e7c7f79e9838932fa7cb6d3203c6d7e6c5>`__).

4. When using Oracle Instant Client 19 on Linux versions such as Oracle Linux
   8, you may need to manually install the ``libnsl`` package to make
   ``libnsl.so`` available:

   .. code-block:: shell

       sudo dnf install libnsl

5. If there is no other Oracle software on the machine that will be
   impacted, permanently add Instant Client to the runtime link
   path. For example, with sudo or as the root user:

   .. code-block:: shell

       sudo sh -c "echo /opt/oracle/instantclient_21_6 > /etc/ld.so.conf.d/oracle-instantclient.conf"
       sudo ldconfig

   Alternatively, set the environment variable ``LD_LIBRARY_PATH`` to
   the appropriate directory for the Instant Client version. For
   example:

   .. code-block:: shell

       export LD_LIBRARY_PATH=/opt/oracle/instantclient_21_6:$LD_LIBRARY_PATH

  Make sure this is set in each shell that invokes Python.  Web servers and
  other daemons commonly reset environment variables so using ``ldconfig`` is
  generally preferred instead.

6. If you use optional Oracle configuration files such as ``tnsnames.ora``,
   ``sqlnet.ora``, or ``oraaccess.xml`` with Instant Client, then put the files
   in an accessible directory, for example in
   ``/opt/oracle/your_config_dir``. Then use:

   .. code-block:: python

       import oracledb

       oracledb.init_oracle_client(config_dir="/home/your_username/oracle/your_config_dir")

   or set the environment variable ``TNS_ADMIN`` to that directory name.

   Alternatively, put the files in the ``network/admin`` subdirectory of Instant
   Client, for example in ``/opt/oracle/instantclient_21_6/network/admin``.
   This is the default Oracle configuration directory for executables linked
   with this Instant Client.

7. Call :meth:`oracledb.init_oracle_client()` in your application, if it is not
   already used.

Oracle Instant Client RPMs
++++++++++++++++++++++++++

To use python-oracledb with Oracle Instant Client RPMs:

1a. Download and install Oracle Instant Client "Basic" or "Basic Light"

    Download and install an Oracle 23, 21, 19, 18, 12, or 11.2 "Basic" or "Basic
    Light" RPM matching your Python architecture from:

    - `Linux 64-bit (x86-64) <https://www.oracle.com/database/technologies/
      instant-client/linux-x86-64-downloads.html>`__
    - `Linux Arm 64-bit (aarch64) <https://www.oracle.com/database/technologies
      /instant-client/linux-arm-aarch64-downloads.html>`__

    Install the downloaded RPM with sudo or as the root user. For example:

    .. code-block:: shell

        sudo dnf install oracle-instantclient-basic-23.9.0.25.07-1.el9.x86_64.rpm

    Dnf will automatically install required dependencies, such as ``libaio``.

    It is recommended to keep up to date with the latest Oracle Instant Client
    release updates of your desired major version.

    Oracle Database versions 23 and 19 are Long Term Support Releases. Oracle
    Instant Client version 23 will connect to Oracle Database 19 or
    later. Oracle Instant Client version 19 will connect to Oracle Database
    version 11.2 or later.

    Note 32-bit clients are not available on any platform for Oracle Database
    version 23, however you can use older 32-bit clients to connect to this
    version of the database.

1b. Alternatively, install Instant Client from Oracle's yum server

    See `Oracle Database Instant Client for Oracle Linux
    <https://yum.oracle.com/oracle-instant-client.html>`__ instructions. The
    repositories are:

    - Instant Client version 23 on Oracle Linux 9

      - `Instant Client 23 for Oracle Linux 9 (x86-64) <https://yum.oracle.com/
        repo/OracleLinux/OL9/oracle/instantclient23/x86_64/index.html>`__

      - `Instant Client 23 for Oracle Linux 9 (aarch64) <https://yum.oracle.com
        /repo/OracleLinux/OL9/oracle/instantclient23/aarch64/index.html>`__

      .. code-block:: shell

          sudo dnf install oracle-instantclient-release-23ai-el9
          sudo dnf install oracle-instantclient-basic

    - Instant Client version 19 on Oracle Linux 9:

      - `Instant Client 19 for Oracle Linux 9 (x86-64) <https://yum.oracle.com/
        repo/OracleLinux/OL9/oracle/instantclient/x86_64/index.html>`__

      - `Instant Client 19 for Oracle Linux 9 (aarch64) <https://yum.oracle.com
        /repo/OracleLinux/OL9/oracle/instantclient/aarch64/index.html>`__

      .. code-block:: shell

          sudo dnf install oracle-instantclient-release-el9
          sudo dnf install oracle-instantclient19.XX-basic

    - Instant Client version 23 on Oracle Linux 8

      - `Instant Client 23 for Oracle Linux 8 (x86-64) <https://yum.oracle.com/
        repo/OracleLinux/OL8/oracle/instantclient23/x86_64/index.html>`__

      - `Instant Client 23 for Oracle Linux 8 (aarch64) <https://yum.oracle.com
        /repo/OracleLinux/OL8/oracle/instantclient23/aarch64/index.html>`__

      .. code-block:: shell

          sudo dnf install oracle-instantclient-release-23ai-el8
          sudo dnf install oracle-instantclient-basic

    - Instant Client version 19 on Oracle Linux 8:

      - `Instant Client 19 for Oracle Linux 8 (x86-64) <https://yum.oracle.com/
        repo/OracleLinux/OL8/oracle/instantclient/x86_64/index.html>`__

      - `Instant Client 19 for Oracle Linux 8 (aarch64) <https://yum.oracle.com
        /repo/OracleLinux/OL8/oracle/instantclient/aarch64/index.html>`__

      .. code-block:: shell

          sudo dnf install -y oracle-release-el8
          sudo dnf install -y oracle-instantclient19.XX-basic

2. When using Oracle Instant Client 19 on Linux versions such as Oracle Linux
   8, you may need to manually install the ``libnsl`` package to make
   ``libnsl.so`` available:

   .. code-block:: shell

       sudo dnf install libnsl

3. For Instant Client 19 or later, the system library search path is
   automatically configured during installation.

   For older versions, if there is no other Oracle software on the machine that
   will be impacted, permanently add Instant Client to the runtime link
   path. For example, with sudo or as the root user:

   .. code-block:: shell

       sudo sh -c "echo /usr/lib/oracle/18.5/client64/lib > /etc/ld.so.conf.d/oracle-instantclient.conf"
       sudo ldconfig

   Alternatively, for version 18 and earlier, every shell running
   Python will need to have the environment variable
   ``LD_LIBRARY_PATH`` set to the appropriate directory for the
   Instant Client version. For example:

   .. code-block:: shell

       export LD_LIBRARY_PATH=/usr/lib/oracle/18.5/client64/lib:$LD_LIBRARY_PATH

  Web servers and other daemons commonly reset environment variables so using
  ``ldconfig`` is generally preferred instead.

4. If you use optional Oracle configuration files such as ``tnsnames.ora``,
   ``sqlnet.ora`` or ``oraaccess.xml`` with Instant Client, then put the files
   in an accessible directory, for example in
   ``/opt/oracle/your_config_dir``. Then your application code can use:

   .. code-block:: python

       import oracledb

       oracledb.init_oracle_client(config_dir="/opt/oracle/your_config_dir")

   or you can set the environment variable ``TNS_ADMIN`` to that directory
   name.

   Alternatively, put the files in the ``network/admin`` subdirectory of Instant
   Client, for example in ``/usr/lib/oracle/21/client64/lib/network/admin``.
   This is the default Oracle configuration directory for executables linked
   with this Instant Client.

5. Call :meth:`oracledb.init_oracle_client()` in your application, if it is not
   already used.

Local Database or Full Oracle Client
++++++++++++++++++++++++++++++++++++

Python-oracledb applications can use Oracle Client 23, 21, 19, 18, 12, or 11.2
libraries from a local Oracle Database or full Oracle Client installation (such
as installed by Oracle's GUI installer).

The libraries must be either 32-bit or 64-bit, matching your Python
architecture. Note 32-bit clients are not available on any platform for Oracle
Database version 23, however you can use older 32-bit clients to connect to
this version of the database.

1. Set required Oracle environment variables, such as ``ORACLE_HOME``, by
   running the Oracle environment script. For example:

   .. code-block:: shell

       source /usr/local/bin/oraenv

   For Oracle Database Express Edition ("XE") 11.2, run:

   .. code-block:: shell

       source /u01/app/oracle/product/11.2.0/xe/bin/oracle_env.sh

2. Optional Oracle configuration files such as ``tnsnames.ora``,
   ``sqlnet.ora``, or ``oraaccess.xml`` can be placed in
   ``$ORACLE_HOME/network/admin``.

   Alternatively, Oracle configuration files can be put in another, accessible
   directory.  Then set the environment variable ``TNS_ADMIN`` to that
   directory name.

3. Call :meth:`oracledb.init_oracle_client()` in your application, if it is not
   already used.


.. _wininstall:

Installing python-oracledb on Windows
=====================================

Install python-oracledb
------------------------

Use Python's `pip <https://pip.pypa.io/en/latest/installation/>`__ package
to install python-oracledb from Python's package repository `PyPI
<https://pypi.org/project/oracledb/>`__:

.. code-block:: shell

    python -m pip install oracledb --upgrade

If you are behind a proxy, use the ``--proxy`` option. For example:

.. code-block:: shell

    python -m pip install oracledb --upgrade --proxy=http://proxy.example.com:80

This will download and install a pre-compiled binary `if one is available
<https://pypi.org/project/oracledb/>`__ for your architecture.  If a
pre-compiled binary is not available, the source will be downloaded, compiled,
and the resulting binary installed.

Optionally Install Oracle Client
--------------------------------

By default, python-oracledb runs in a Thin mode which connects directly to
Oracle Database so no further installation steps are required.  However, to use
additional features available in :ref:`Thick mode <featuresummary>` you need
Oracle Client libraries installed.  Oracle Client versions 21, 19, 18, 12, and
11.2 can be used.

- If your database is on a remote computer, then download the free `Oracle
  Instant Client <https://www.oracle.com/database/technologies/instant-client.
  html>`__ "Basic" or "Basic Light" package for your operating system
  architecture.

- Alternatively, use the client libraries already available in a locally
  installed database such as the free `Oracle Database Express Edition ("XE")
  <https://www.oracle.com/database/technologies/appdev/xe.html>`__ release.

To use python-oracledb in Thick mode you must call
:meth:`oracledb.init_oracle_client()` in your application, see
:ref:`enablingthick`. For example:

.. code-block:: python

    import oracledb

    oracledb.init_oracle_client()

On Windows, you may prefer to pass the ``lib_dir`` parameter in the call as
shown below.

Oracle Instant Client Zip Files
+++++++++++++++++++++++++++++++

To use python-oracledb in Thick mode with Oracle Instant Client zip files:

1. Download an Oracle 21, 19, 18, 12, or 11.2 "Basic" or "Basic Light" zip
   file: `64-bit <https://www.oracle.com/database/technologies/instant-client/
   winx64-64-downloads.html>`__ or `32-bit <https://www.oracle.com/database/
   technologies/instant-client/microsoft-windows-32-downloads.html>`__,
   matching your Python architecture.  Note 32-bit clients are not available on
   any platform for Oracle Database version 23, however you can use older
   32-bit clients to connect to this version of the database.

   The latest version is recommended.  Oracle Instant Client 19 will connect to
   Oracle Database 11.2 or later.

2. Unzip the package into a directory that is accessible to your
   application. For example unzip
   ``instantclient-basic-windows.x64-19.22.0.0.0dbru.zip`` to
   ``C:\oracle\instantclient_19_22``.

3. Oracle Instant Client libraries require a Visual Studio redistributable with
   a 64-bit or 32-bit architecture to match Instant Client's architecture.
   Each Instant Client version requires a different redistributable version:

  - For Instant Client 21, install `VS 2019 <https://docs.microsoft.com/en-US/cpp/windows/latest-supported-vc-redist?view=msvc-170>`__ or later
  - For Instant Client 19, install `VS 2017 <https://docs.microsoft.com/en-US/cpp/windows/latest-supported-vc-redist?view=msvc-170>`__
  - For Instant Client 18 or 12.2, install `VS 2013 <https://docs.microsoft.com/en-US/cpp/windows/latest-supported-vc-redist?view=msvc-170#visual-studio-2013-vc-120>`__
  - For Instant Client 12.1, install `VS 2010 <https://docs.microsoft.com/en-US/cpp/windows/latest-supported-vc-redist?view=msvc-170#visual-studio-2010-vc-100-sp1-no-longer-supported>`__
  - For Instant Client 11.2, install `VS 2005 64-bit <https://docs.microsoft.com/en-US/cpp/windows/latest-supported-vc-redist?view=msvc-170#visual-studio-2005-vc-80-sp1-no-longer-supported>`__

Configure Oracle Instant Client
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. There are several alternative ways to tell python-oracledb where your Oracle
   Client libraries are, see :ref:`initialization`.

  * With Oracle Instant Client you can use
    :meth:`oracledb.init_oracle_client()` in your application, for example:

    .. code-block:: python

        import oracledb

        oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient_19_22")

    Note that a 'raw' string is used because backslashes occur in the path.

  * Alternatively, add the Oracle Instant Client directory to the ``PATH``
    environment variable.  The directory must occur in ``PATH`` before any
    other Oracle directories.  Restart any open command prompt windows.

    Update your application to call ``init_oracle_client()``, which enables
    python-oracledb Thick mode:

    .. code-block:: python

        import oracledb

        oracledb.init_oracle_client()

  * Another way to set ``PATH`` is to use a batch file that sets it before
    Python is executed, for example:

    .. code-block:: shell

        REM mypy.bat
        SET PATH=C:\oracle\instantclient_19_22;%PATH%
        python %*

    Invoke this batch file every time you want to run Python.

    Update your application to call ``init_oracle_client()``, which enables
    python-oracledb Thick mode:

    .. code-block:: python

        import oracledb

        oracledb.init_oracle_client()

2. If you use optional Oracle configuration files such as ``tnsnames.ora``,
   ``sqlnet.ora``, or ``oraaccess.xml`` with Instant Client, then put the files
   in an accessible directory, for example in
   ``C:\oracle\your_config_dir``. Then use:

   .. code-block:: python

       import oracledb

       oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient_19_22",
                                   config_dir=r"C:\oracle\your_config_dir")

   or set the environment variable ``TNS_ADMIN`` to that directory name.

   Alternatively, put the files in a ``network\admin`` subdirectory of Instant
   Client, for example in ``C:\oracle\instantclient_19_22\network\admin``.
   This is the default Oracle configuration directory for executables linked
   with this Instant Client.

Local Database or Full Oracle Client
++++++++++++++++++++++++++++++++++++

Python-oracledb Thick mode applications can use Oracle Client 21, 19, 18, 12,
or 11.2 libraries from a local Oracle Database or full Oracle Client (such as
installed by Oracle's GUI installer).

The Oracle libraries must be either 32-bit or 64-bit, matching your Python
architecture. Note 32-bit clients are not available on any platform for Oracle
Database version 23, however you can use older 32-bit clients to connect to
this version of the database.

1. Set the environment variable ``PATH`` to include the path that contains
   ``OCI.DLL``, if it is not already set.

   Restart any open command prompt windows.

2. Optional Oracle configuration files such as ``tnsnames.ora``,
   ``sqlnet.ora``, or ``oraaccess.xml`` can be placed in the
   ``network\admin`` subdirectory of the Oracle Database software installation.

   Alternatively, pass ``config_dir`` to :meth:`oracledb.init_oracle_client()`
   as shown in the previous section, or set ``TNS_ADMIN`` to the directory
   name.

3. To use python-oracledb in Thick mode you must call
   :meth:`oracledb.init_oracle_client()` in your application, see
   :ref:`enablingthick`.

   .. code-block:: python

       import oracledb

       oracledb.init_oracle_client()

Installing python-oracledb on macOS
===================================

Python-oracledb is available as a Universal binary for Python 3.9, or later, on
Apple macOS Intel x86-64 and Apple macOS ARM64 (M1, M2, M3, M4) architectures.

Install python-oracledb
-----------------------

Use Python's `pip <https://pip.pypa.io/en/latest/installation/>`__ package
to install python-oracledb from Python's package repository `PyPI
<https://pypi.org/project/oracledb/>`__:

.. code-block:: shell

    python -m pip install oracledb --upgrade

The ``--user`` option may be useful if you do not have permission to write to
system directories:

.. code-block:: shell

    python -m pip install oracledb --upgrade --user

If you are behind a proxy, use the ``--proxy`` option. For example:

.. code-block:: shell

    python -m pip install oracledb --upgrade --user --proxy=http://proxy.example.com:80

To install into the system Python, you may need to use ``/usr/bin/python3``
instead of ``python``:

.. code-block:: shell

    /usr/bin/python3 -m pip install oracledb --upgrade --user

Optionally Install Oracle Client
--------------------------------

By default, python-oracledb runs in a Thin mode which connects directly to
Oracle Database so no further installation steps are required.  However, to use
additional features available in :ref:`Thick mode <featuresummary>` you need
Oracle Client libraries installed.

You can get the libraries from either the Oracle Instant Client **Basic** or
**Basic Light** package.  The steps below show installing **Basic**.

Instant Client Scripted Installation on macOS ARM64
+++++++++++++++++++++++++++++++++++++++++++++++++++

Instant Client installation can be scripted. Open a terminal window and run:

.. code-block:: shell

    cd $HOME/Downloads
    curl -O https://download.oracle.com/otn_software/mac/instantclient/233023/instantclient-basic-macos.arm64-23.3.0.23.09.dmg
    hdiutil mount instantclient-basic-macos.arm64-23.3.0.23.09.dmg
    /Volumes/instantclient-basic-macos.arm64-23.3.0.23.09/install_ic.sh
    hdiutil unmount /Volumes/instantclient-basic-macos.arm64-23.3.0.23.09

Note you should use the latest DMG available.

If you have multiple Instant Client DMG packages mounted, you only need to run
``install_ic.sh`` once.  It will copy all mounted Instant Client DMG packages at
the same time.

The Instant Client directory will be like
``$HOME/Downloads/instantclient_23_3``.  Applications may not have access to
the ``Downloads`` directory, so you should move Instant Client somewhere
convenient.

Instant Client Manual Installation on macOS ARM64
+++++++++++++++++++++++++++++++++++++++++++++++++

* Download the latest Instant Client **Basic** ARM64 package DMG from `Oracle
  <https://www.oracle.com/database/technologies/instant-client/macos-arm64-
  downloads.html>`__.

* Using Finder, double-click the DMG to mount it.

* Open a terminal window and run the install script in the mounted package,
  for example if you downloaded version 23.3:

  .. code-block:: shell

    /Volumes/instantclient-basic-macos.arm64-23.3.0.23.09/install_ic.sh

  The Instant Client directory will be like
  ``$HOME/Downloads/instantclient_23_3``.  Applications may not have access to
  the ``Downloads`` directory, so you should move Instant Client somewhere
  convenient.

* Using Finder, eject the mounted Instant Client package.

If you have multiple Instant Client DMG packages mounted, you only need to run
``install_ic.sh`` once.  It will copy all mounted Instant Client DMG packages
at the same time.

Instant Client Scripted Installation on macOS Intel x86-64
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Instant Client installation can be scripted. Open a terminal window and run:

.. code-block:: shell

    cd $HOME/Downloads
    curl -O https://download.oracle.com/otn_software/mac/instantclient/1916000/instantclient-basic-macos.x64-19.16.0.0.0dbru.dmg
    hdiutil mount instantclient-basic-macos.x64-19.16.0.0.0dbru.dmg
    /Volumes/instantclient-basic-macos.x64-19.16.0.0.0dbru/install_ic.sh
    hdiutil unmount /Volumes/instantclient-basic-macos.x64-19.16.0.0.0dbru

Note you should use the latest DMG available.

If you have multiple Instant Client DMG packages mounted, you only need to run
``install_ic.sh`` once.  It will copy all mounted Instant Client DMG packages at
the same time.

The Instant Client directory will be ``$HOME/Downloads/instantclient_19_16``.
Applications may not have access to the ``Downloads`` directory, so you should
move Instant Client somewhere convenient.

Instant Client Manual Installation on macOS Intel x86-64
++++++++++++++++++++++++++++++++++++++++++++++++++++++++

* Download the latest Instant Client **Basic** Intel 64-bit package DMG from
  `Oracle <https://www.oracle.com/database/technologies/instant-client/macos-
  intel-x86-downloads.html>`__.

* Using Finder, double-click the DMG to mount it.

* Open a terminal window and run the install script in the mounted package, for example:

  .. code-block:: shell

    /Volumes/instantclient-basic-macos.x64-19.16.0.0.0dbru/install_ic.sh

  The Instant Client directory will be ``$HOME/Downloads/instantclient_19_16``.
  Applications may not have access to the ``Downloads`` directory, so you
  should move Instant Client somewhere convenient.

* Using Finder, eject the mounted Instant Client package.

If you have multiple Instant Client DMG packages mounted, you only need to run
``install_ic.sh`` once.  It will copy all mounted Instant Client DMG packages at
the same time.

Configure Oracle Instant Client
-------------------------------

Your application must load the installed Oracle Instant Client libraries. It
can optionally indicate external configuration files.

1. Call :meth:`oracledb.init_oracle_client()` in your application:

   .. code-block:: python

        import oracledb

        oracledb.init_oracle_client(lib_dir="/Users/your_username/Downloads/instantclient_23_3")

2. If you use optional Oracle configuration files such as ``tnsnames.ora``,
   ``sqlnet.ora``, or ``oraaccess.xml`` with Oracle Instant Client, then put the
   files in an accessible directory, for example in
   ``/Users/your_username/oracle/your_config_dir``. Then use:

   .. code-block:: python

       import oracledb

       oracledb.init_oracle_client(lib_dir="/Users/your_username/Downloads/instantclient_23_3",
                                   config_dir="/Users/your_username/oracle/your_config_dir")

   Or set the environment variable ``TNS_ADMIN`` to that directory name.

   Alternatively, put the files in the ``network/admin`` subdirectory of Oracle
   Instant Client, for example in
   ``/Users/your_username/Downloads/instantclient_23_3/network/admin``.  This is the
   default Oracle configuration directory for executables linked with this
   Instant Client.

Installing python-oracledb without Internet Access
===================================================

To install python-oracledb on a computer that is not connected to the internet,
download a python-oracledb wheel package from Python's package repository `PyPI
<https://pypi.org/project/oracledb/#files>`__. Use the file appropriate for
your operating system and python version. Transfer this file to the offline
computer and install it with:

.. code-block:: shell

    python -m pip install "<file_name>"

You will also need to use a similar step to install the required cryptography
package and its dependencies.

Then follow the general python-oracledb platform installation instructions to
install Oracle Client libraries. This is only necessary if you intend to use
python-oracledb :ref:`Thick mode <initialization>`.

.. _nocrypto:

Installing python-oracledb without the Cryptography Package
===========================================================

If the Python cryptography package is not available, python-oracledb can still
be installed but can only be used in Thick mode.  Trying to use Thin mode will
give the error ``DPY-3016: python-oracledb thin mode cannot be used because the
cryptography package is not installed``.

To use python-oracledb without the cryptography package:

- Install python-oracledb using pip's ``--no-deps`` option, for example:

  .. code-block:: python

      python -m pip install oracledb --no-deps

- Oracle Client libraries must then be installed.  See previous sections.

- Add a call to :meth:`oracledb.init_oracle_client()` in your application, see
  :ref:`enablingthick`.

.. _installsrc:

Installing from Source Code
===========================

For platforms that do not have pre-built binaries on `PyPI
<https://pypi.org/project/oracledb/>`__, using the normal ``python -m pip
install oracledb`` command will download the python-oracledb source bundle,
build, and install it.

Alternatively, to create your own package files for installation, you can build
and install python-oracledb either :ref:`locally from source code <installgh>`,
or by using a :ref:`presupplied GitHub Action <installghactions>` which builds
packages for all architectures and Python versions.

.. _installgh:

Building a python-oracledb package locally
------------------------------------------

1. Install a C99 compliant C compiler.

2. Download the source code using one of the following options:

   - You can clone the source code from `GitHub
     <https://github.com/oracle/python-oracledb>`__:

     .. code-block:: shell

         git clone --recurse-submodules https://github.com/oracle/python-oracledb.git

   - Alternatively, you can manually download a `source zip
     <https://github.com/oracle/python-oracledb/archive/refs/heads/main.zip>`__
     file from GitHub.

     In this case, you will also need to download an `ODPI-C
     <https://github.com/oracle/odpi>`__ source zip file and put the
     extracted contents inside the ``odpi`` subdirectory, for example in
     ``python-oracledb-main/src/oracledb/impl/thick/odpi``.

   - Alternatively, clone the source from `opensource.oracle.com
     <https://opensource.oracle.com/>`__, which mirrors GitHub:

     .. code-block:: shell

         git clone --recurse-submodules https://opensource.oracle.com/git/oracle/python-oracledb.git
         git checkout main

   - Alternatively, a python-oracledb source package can manually be downloaded
     from PyPI.

     Navigate to the `PyPI python-oracledb download files
     <https://pypi.org/project/oracledb/#files>`__ page, download the source
     package archive, and extract it.

3. With the source code available, build a python-oracledb package by running:

   .. code-block:: shell

       cd python-oracledb               # the name may vary depending on the download
       python -m pip install build --upgrade
       # export PYO_COMPILE_ARGS='-g0'  # optionally set any compilation arguments
       python -m build

   A python-oracledb wheel package is created in the ``dist`` subdirectory.
   For example when using Python 3.12 on macOS you might have the file
   ``dist/oracledb-3.1.0-cp312-cp312-macosx_14_0_arm64.whl``.

4. Install this package:

   .. code-block:: shell

       python -m pip install dist/oracledb-3.1.0-cp312-cp312-macosx_14_0_arm64.whl

   The package can also be installed on any computer which has the same
   architecture and Python version as the build machine.

.. _installghactions:

Building python-oracledb packages using GitHub Actions
------------------------------------------------------

The python-oracledb GitHub repository has a builder Action that uses GitHub
infrastructure to build python-oracledb packages for all architectures and
Python versions.

1. Fork the `python-oracledb repository
   <https://github.com/oracle/python-oracledb/fork>`__.  Additionally fork the
   `ODPI-C repository <https://github.com/oracle/odpi/fork>`__, keeping the
   default name.

2. In your python-oracledb fork, go to the Actions tab
   ``https://github.com/<your name>/python-oracledb/actions/``.  If this is
   your first time using Actions, confirm enabling them.

3. In the "All workflows" list on the left-hand side, select the "Build
   python-oracledb packages" entry.

4. Navigate to the "Run workflow" drop-down, select the branch to build from
   (for example, "main"), and run the workflow.

5. Optionally edit the input field list of package targets and remove targets
   you do not want to build. For example, remove "Linux" if you do not want
   Linux packages.

6. When the build has completed, download the "python-oracledb-wheels"
   artifact, unzip it, and install the one for your architecture and Python
   version.  For example, when using Python 3.12 on macOS, install:

   .. code-block:: shell

       python -m pip install oracledb-3.1.0-cp312-cp312-macosx_10_13_universal2.whl

.. _docker:

Using python-oracledb Containers
================================

Dockerfiles showing installation of Python and python-oracledb on Oracle Linux
are available from
`github.com/oracle/docker-images/tree/main/OracleLinuxDevelopers
<https://github.com/oracle/docker-images/tree/main/OracleLinuxDevelopers>`__.

Containers built from these Dockerfiles can be pulled from the GitHub Container
Registry:

- `oraclelinux9-python <https://github.com/oracle/docker-images/pkgs/container/
  oraclelinux9-python>`__
- `oraclelinux8-python <https://github.com/oracle/docker-images/pkgs/container/
  oraclelinux8-python>`__

For example, you can pull a container for Python 3.12 on Oracle Linux 9 using:

.. code-block:: shell

    docker pull ghcr.io/oracle/oraclelinux9-python:3.12-oracledb

Or use it in a Dockerfile like:

.. code-block:: shell

    FROM ghcr.io/oracle/oraclelinux9-python:3.12-oracledb

**Sample Containers**

There are two python-oracledb containers with samples located in
`/samples/containers
<https://github.com/oracle/python-oracledb/tree/main/samples/containers>`__.

.. _configprovidermodules:

Installing Centralized Configuration Provider Modules for python-oracledb
=========================================================================

To use python-oracledb with a :ref:`centralized configuration provider
<configurationproviders>`, you must install the necessary modules for your
preferred provider as detailed below.

.. _ociccpmodules:

Install Modules for the OCI Object Storage Centralized Configuration Provider
-----------------------------------------------------------------------------

For python-oracledb to use an :ref:`Oracle Cloud Infrastructure (OCI) Object
Storage configuration provider <ociobjstorageprovider>`, you must install the
`OCI <https://pypi.org/project/oci/>`__ package by using the optional
``[oci_config]`` dependency:

  .. code-block:: shell

    python -m pip install oracledb[oci_config]

See :ref:`ociobjstorageprovider` for information on using this configuration
provider with python-oracledb.

.. _azureccpmodules:

Install Modules for the Azure App Centralized Configuration Provider
--------------------------------------------------------------------

For python-oracledb to use an :ref:`Azure App Configuration Provider
<azureappstorageprovider>`, you must install the `Azure App Configuration
<https://pypi.org/project/azure-appconfiguration/>`__, `Azure Identity
<https://pypi.org/project/azure-identity/>`__, and `Azure Key Vault Secrets
<https://pypi.org/project/azure-keyvault-secrets/>`__ packages by using the
optional ``[azure_config]`` dependency:

.. code-block:: shell

    python -m pip install oracledb[azure_config]

See :ref:`azureappstorageprovider` for information on using this configuration
provider with python-oracledb.

.. _cloudnativemodules:

Installing Cloud Native Authentication Modules for python-oracledb
==================================================================

To use a python-oracledb Cloud Native Authentication plugin, you must install
the necessary modules for your preferred plugin, as detailed below.

.. _ocitokenmodules:

Install Modules for the OCI Cloud Native Authentication Plugin
--------------------------------------------------------------

For python-oracledb to use the OCI Cloud Native Authentication Plugin, you must
install the `Python SDK for Oracle Cloud Infrastructure
<https://pypi.org/project/oci/>`__ package by using the ``[oci_auth]``
dependency:

.. code-block:: shell

    python -m pip install oracledb[oci_auth]

Review the `OCI SDK installation instructions
<https://docs.oracle.com/en-us/iaas/tools/python/latest/installation.html>`__
as needed.

See :ref:`cloudnativeauthoci` for more information on using the plugin in
python-oracledb.

.. _azuretokenmodules:

Install Modules for the Azure Cloud Native Authentication Plugin
----------------------------------------------------------------

For python-oracledb to use the Azure Cloud Native Authentication Plugin, you
must install the `Microsoft Authentication Library (MSAL) for Python
<https://pypi.org/project/msal/>`__ package by using the optional
``[azure_auth]`` dependency:

.. code-block:: shell

    python -m pip install oracledb[azure_auth]

Review the `Microsoft MSAL installation instructions
<https://learn.microsoft.com/en-us/entra/msal/python/?view=msal-py-latest#install-the-package>`__
as needed.

See :ref:`cloudnativeauthoauth` for more information on using the plugin in
python-oracledb.
