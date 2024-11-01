.. _startup:

*************************************
Starting and Stopping Oracle Database
*************************************

This chapter covers how to start up and shut down Oracle Database using
python-oracledb.

.. note::

    Database start up and shut down functionality is only supported in the
    python-oracledb Thick mode.  See :ref:`enablingthick`.

===========================
Starting Oracle Database Up
===========================

Python-oracledb can start up a database instance. A privileged connection is
required. This example shows a script that could be run as the 'oracle'
operating system user who administers a local database installation on Linux.
It assumes that the environment variable ``ORACLE_SID`` has been set to the SID
of the database that should be started:

.. code-block:: python

    # the connection must be in PRELIM_AUTH mode to perform startup
    connection = oracledb.connect(mode=oracledb.SYSDBA | oracledb.PRELIM_AUTH)
    connection.startup()

    # the following statements must be issued in normal SYSDBA mode
    connection = oracledb.connect(mode=oracledb.SYSDBA)
    cursor = connection.cursor()
    cursor.execute("alter database mount")
    cursor.execute("alter database open")

To start up a remote database, you may need to configure the Oracle Net
listener to use `static service registration
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-0203C8FA-A4BE-44A5-9A25-3D1E578E879F>`_
by adding a ``SID_LIST_LISTENER`` entry to the database `listener.ora` file.


=============================
Shutting Oracle Database Down
=============================

Python-oracledb has the ability to shut down the database using a privileged
connection. This example also assumes that the environment variable
``ORACLE_SID`` has been set:

.. code-block:: python

    # need to connect as SYSDBA or SYSOPER
    connection = oracledb.connect(mode=oracledb.SYSDBA)

    # first shutdown() call must specify the mode, if DBSHUTDOWN_ABORT is used,
    # there is no need for any of the other steps
    connection.shutdown(mode=oracledb.DBSHUTDOWN_IMMEDIATE)

    # now close and dismount the database
    cursor = connection.cursor()
    cursor.execute("alter database close normal")
    cursor.execute("alter database dismount")

    # perform the final shutdown call
    connection.shutdown(mode=oracledb.DBSHUTDOWN_FINAL)
