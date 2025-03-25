.. _introduction:

*****************************************************
Introduction to the Python Driver for Oracle Database
*****************************************************

The python-oracledb driver is a Python module that enables access to Oracle
Database. It conforms to the `Python Database API v2.0 Specification
<https://www.python.org/dev/peps/pep-0249/>`__ with a considerable number of
additions and a couple of exclusions. Synchronous and :ref:`concurrent
<asyncio>` coding styles are supported.  It is distributed under an open-source
:ref:`license <license>`.

The module is available from standard package repositories including `PyPI
<https://pypi.org/project/oracledb/>`__, `conda-forge
<https://anaconda.org/conda-forge/oracledb>`__, and `yum.oracle.com
<https://yum.oracle.com/oracle-linux-python.html>`__.  The source code is
hosted at `github.com/oracle/python-oracledb
<https://github.com/oracle/python-oracledb>`__.

This module is currently tested with Python 3.9, 3.10, 3.11, 3.12, and 3.13
against Oracle Database 23ai, 21c, 19c, 18c, 12c, and 11gR2. Previous versions
of python-oracledb supported older Python versions.

Changes in python-oracledb
releases can be found in the :ref:`release notes <releasenotes>`.

The python-oracledb driver is the renamed, major version successor to cx_Oracle
8.3.  For upgrade information, see :ref:`upgrading83`. The cx_Oracle driver is
obsolete and should not be used for new development.

Getting Started
===============

See :ref:`quickstart`.

Runnable examples are in the `GitHub samples directory
<https://github.com/oracle/python-oracledb/tree/main/samples>`__.
A tutorial `Python and Oracle Database Tutorial: The New Wave of Scripting
<https://oracle.github.io/python-oracledb
/samples/tutorial/Python-and-Oracle-Database-The-New-Wave-of-Scripting.html>`__
is also available.

Architecture
============

Python-oracledb is a 'Thin' driver with an optional 'Thick' mode enabled by an
application setting.

python-oracledb Thin Mode Architecture
--------------------------------------

By default, python-oracledb allows connecting directly to Oracle Database 12.1
or later.  This Thin mode does not need Oracle Client libraries.

.. _thinarchfig:
.. figure:: /images/python-oracledb-thin-arch.png
   :alt: architecture of the python-oracledb driver in Thin mode

   Architecture of the python-oracledb driver in Thin mode

The figure shows the architecture of python-oracledb.  Users interact with a
Python application, for example by making web requests. The application program
makes calls to python-oracledb functions. The connection from python-oracledb
Thin mode to the Oracle Database is established directly.  The database can be
on the same machine as Python, or it can be remote.

The Oracle Net behavior can optionally be configured by using a
``tnsnames.ora`` file and with application settings. See :ref:`optnetfiles`.

python-oracledb Thick Mode Architecture
---------------------------------------

Python-oracledb is said to be in 'Thick' mode when it links with Oracle Client
libraries.  An application script runtime option enables this mode by loading
the libraries, see :ref:`enablingthick`.  This gives you some :ref:`additional
functionality <featuresummary>`. Depending on the version of the Oracle Client
libraries, this mode of python-oracledb can connect to Oracle Database 9.2 or
later.

.. _thickarchfig:
.. figure:: /images/python-oracledb-thick-arch.png
   :alt: architecture of the python-oracledb driver in Thick mode

   Architecture of the python-oracledb driver in Thick mode

The figure shows the architecture of the python-oracledb Thick mode.  Users
interact with a Python application, for example by making web requests. The
application program makes calls to python-oracledb functions. Internally,
python-oracledb dynamically loads Oracle Client libraries.  Connections from
python-oracledb Thick mode to Oracle Database are established using the Oracle
Client libraries.  The database can be on the same machine as Python, or it can
be remote.

To use python-oracledb Thick mode, the Oracle Client libraries must be
installed separately, see :ref:`installation`.  The libraries can be from an
installation of `Oracle Instant Client
<https://www.oracle.com/database/technologies/instant-client.html>`__, from a
full Oracle Client installation (such as installed by Oracle's GUI installer),
or even from an Oracle Database installation (if Python is running on the same
machine as the database). Oracle's standard client-server version
interoperability allows connection to both older and newer databases from
different Oracle Client library versions.

Some behaviors of the Oracle Client libraries can optionally be configured with
an ``oraaccess.xml`` file, for example to enable auto-tuning of a statement
cache.  See :ref:`optclientfiles`.

The Oracle Net behavior can optionally be configured with files such as
``tnsnames.ora`` and ``sqlnet.ora``, for example to enable :ref:`network
encryption <netencrypt>`. See :ref:`optnetfiles`.

Oracle environment variables that are set before python-oracledb first creates
a database connection may affect python-oracledb Thick mode behavior.  See
:ref:`envset`.


Feature Highlights of python-oracledb
======================================

The python-oracledb feature highlights are:

    *   Easy installation from PyPI and other repositories
    *   Support for multiple Oracle Database versions
    *   Supports the `Python Database API v2.0 Specification <https://www.
        python.org/dev/peps/pep-0249/>`__ with a considerable number of
        additions and a couple of exclusions
    *   Works with common frameworks and ORMs
    *   Execution of SQL and PL/SQL statements
    *   Extensive Oracle data type support, including JSON, VECTOR, large
        objects (``CLOB`` and ``BLOB``) and binding of SQL objects
    *   Connection management, including connection pooling
    *   Oracle Database High Availability features
    *   Full use of Oracle Network Service infrastructure, including encrypted
        network traffic

See :ref:`featuresummary` for more information.
