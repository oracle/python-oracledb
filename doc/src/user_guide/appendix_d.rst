.. _frameworks:

.. currentmodule:: oracledb

*******************************************************
Appendix D: Python Frameworks, SQL Generators, and ORMs
*******************************************************

Python-oracledb's Thin and :ref:`Thick <enablingthick>` modes cover the feature
needs of frameworks that depend upon the Python Database API.

Using python-oracledb with Data Frame Libraries
===============================================

Python-oracledb can fetch directly to data frames that expose an Apache Arrow
PyCapsule interface. This is an efficient way to work with data using Python
libraries such as `Apache PyArrow
<https://arrow.apache.org/docs/python/index.html>`__, `Pandas
<https://pandas.pydata.org>`__, `Polars <https://pola.rs/>`__, `NumPy
<https://numpy.org/>`__, `PyTorch <https://pytorch.org/>`__, or to write files
in `Apache Parquet <https://parquet.apache.org/>`__ format.

See :ref:`dataframeformat` for more information.

.. _flask:

Connecting with Flask
=====================

The Flask web application framework works well with python-oracledb, either
directly or by using a library such as :ref:`SQLAlchemy <sqlalchemy>`.

Examples using python-oracledb directly are available in `connection_pool.py
<https://github.com/oracle/python-oracledb/tree/main/samples/
connection_pool.py>`__, `drcp_pool.py <https://github.com/oracle/
python-oracledb/tree/main/samples/drcp_pool.py>`__, and `session_callback.py
<https://github.com/oracle/python-oracledb/tree/main/samples/
session_callback.py>`__.

.. _sqlalchemy:

Connecting with SQLAlchemy
==========================

`SQLAlchemy <https://www.sqlalchemy.org/>`__, and libraries such as `Pandas
<https://pandas.pydata.org>`__ that internally use SQLAlchemy, can connect
easily in python-oracledb as shown in this section.

Also, see `SQLAlchemy documentation on connecting <https://docs.sqlalchemy.org/
en/20/dialects/oracle.html#module-sqlalchemy.dialects.oracle.oracledb>`__ and
`SQLAlchemy general documentation about Oracle Database
<https://docs.sqlalchemy.org/en/20/dialects/oracle.html#module-sqlalchemy.
dialects.oracle.base>`__.

Connecting with SQLAlchemy 2
----------------------------

SQLAlchemy 2 supports python-oracledb directly.

Standalone Connections in SQLAlchemy
++++++++++++++++++++++++++++++++++++

An example of creating a standalone connection in SQLAlchemy 2 is:

.. code-block:: python

    # Using python-oracledb in SQLAlchemy 2

    import os
    import getpass
    import oracledb
    from sqlalchemy import create_engine
    from sqlalchemy import text

    # Uncomment to use python-oracledb Thick mode
    # Review the doc for the appropriate parameters
    #oracledb.init_oracle_client(<your parameters>)

    un = os.environ.get("PYTHON_USERNAME")
    cs = os.environ.get("PYTHON_CONNECTSTRING")
    pw = getpass.getpass(f'Enter password for {un}@{cs}: ')

    # Note the first argument is different for SQLAlchemy 1.4 and 2
    engine = create_engine('oracle+oracledb://@',
                           connect_args={
                               # Pass any python-oracledb connect() parameters
                               "user": un,
                               "password": pw,
                               "dsn": cs
                           }
             )

    with engine.connect() as connection:
        print(connection.scalar(text(
               """select unique client_driver
                  from v$session_connect_info
                  where sid = sys_context('userenv', 'sid')""")))


Note that the ``create_engine()`` argument driver declaration uses
``oracle+oracledb://`` for SQLAlchemy 2 but ``oracle://`` for SQLAlchemy 1.4.

The ``connect_args`` dictionary can use any appropriate
:meth:`oracledb.connect()` parameter.

.. _sqlalchemy2conpool:

Pooled Connections in SQLAlchemy
++++++++++++++++++++++++++++++++

Most multi-user applications should use a :ref:`connection pool <connpooling>`.
The python-oracledb pool is preferred because of its high availability
support. Some single-user applications may also benefit from these availability
features.

To use a python-oracledb connection pool in SQLAlchemy:

.. code-block:: python

    # Using python-oracledb in SQLAlchemy 2

    import os, platform
    import getpass
    import oracledb
    from sqlalchemy import create_engine
    from sqlalchemy import text
    from sqlalchemy.pool import NullPool

    # Uncomment to use python-oracledb Thick mode
    # Review the doc for the appropriate parameters
    #oracledb.init_oracle_client(<your parameters>)

    un = os.environ.get("PYTHON_USERNAME")
    cs = os.environ.get("PYTHON_CONNECTSTRING")
    pw = getpass.getpass(f'Enter password for {un}@{cs}: ')

    pool = oracledb.create_pool(user=un, password=pw, dsn=cs,
                                min=4, max=4, increment=0)
    engine = create_engine("oracle+oracledb://", creator=pool.acquire, poolclass=NullPool)

    with engine.connect() as connection:
        print(connection.scalar(text("""select unique client_driver
                                        from v$session_connect_info
                                        where sid = sys_context('userenv', 'sid')""")))


.. _sqlalchemy1:

Connecting with SQLAlchemy 1.4
------------------------------

SQLAlchemy 1.4 can use python-oracledb with the help of the module name mapping
code shown in :ref:`boilerplatemapping`.  An example is:

.. code-block:: python

    # Using python-oracledb in SQLAlchemy 1.4

    import os
    import getpass
    import oracledb
    from sqlalchemy import create_engine
    from sqlalchemy import text

    import sys
    oracledb.version = "8.3.0"
    sys.modules["cx_Oracle"] = oracledb

    # Uncomment to use python-oracledb Thick mode
    # Review the doc for the appropriate parameters
    #oracledb.init_oracle_client(<your parameters>)

    un = os.environ.get("PYTHON_USERNAME")
    cs = os.environ.get("PYTHON_CONNECTSTRING")
    pw = getpass.getpass(f'Enter password for {un}@{cs}: ')

    # Note the first argument is different for SQLAlchemy 1.4 and 2
    engine = create_engine('oracle://@',
                           connect_args={
                               # Pass any python-oracledb connect() parameters
                               "user": un,
                               "password": pw,
                               "dsn": cs
                           }
             )

    with engine.connect() as connection:
        print(connection.scalar(text(
               """select unique client_driver
                  from v$session_connect_info
                  where sid = sys_context('userenv', 'sid')""")))


Note that the ``create_engine()`` argument driver declaration uses
``oracle://`` for SQLAlchemy 1.4 but ``oracle+oracledb://`` for SQLAlchemy 2.

The ``connect_args`` dictionary can use any appropriate
:meth:`oracledb.connect()` parameter.

You can also use python-oracledb connection pooling with SQLAlchemy 1.4.  This
is similar to :ref:`pooled connections in SQLAlchemy 2 <sqlalchemy2conpool>`
but use the appropriate :ref:`name mapping code <boilerplatemapping>` and first
argument to ``create_engine()``.

.. _django:

Connecting with Django
======================

Django 5 supports python-oracledb directly.  Earlier versions should use
:ref:`name mapping code <boilerplatemapping>`.

See `Django 5.2 documentation for Oracle Database
<https://docs.djangoproject.com/en/5.2/ref/databases/#oracle-notes>`__.

Standalone Connections
----------------------

To connect in Django 5, an example settings.py file is:

.. code-block:: python

    DATABASES = {
      "default": {
        "ENGINE": "django.db.backends.oracle",
        "NAME": "example.com:1521/orclpdb",
        "USER": "hr",
        "PASSWORD": "the-hr-password"
      }
    }

Pooled Connections
------------------

Django 5.2 supports python-oracledb :ref:`connection pools <connpooling>`.
Most multi-user applications should use a connection pool. The python-oracledb
pool is preferred because of its high availability support. Some single-user
applications may also benfit from these availability features.

.. _djangoconpool:

To use a connection pool in Django 5.2, an example settings.py file is:

.. code-block:: python

    DATABASES = {
      "default": {
        "ENGINE": "django.db.backends.oracle",
        "NAME": "example.com:1521/orclpdb",
        "USER": "hr",
        "PASSWORD": "the-hr-password"
        "OPTIONS": {
          "pool": {
            "min": 0,
            "max": 4,
            "increment": 1,
            # Additional python-oracledb pool parameters can be added here
          }
        }
      },
    }

.. _boilerplatemapping:

Older Versions of Python Frameworks, SQL Generators, and ORMs
=============================================================

For versions of SQLAlchemy, Django, Superset, other frameworks,
object-relational mappers (ORMs), and libraries that support the obsolete
cx_Oracle driver but do not have native support for python-oracledb, you can
add code like this to use python-oracledb:

.. code-block:: python

    import sys
    import oracledb
    oracledb.version = "8.3.0"
    sys.modules["cx_Oracle"] = oracledb

.. note::

    This must occur before any import of cx_Oracle by your code or the library.

See :ref:`sqlalchemy1` for an example.

To use Thick mode, for example, if you need to connect to Oracle Database
11gR2, add a call to :meth:`oracledb.init_oracle_client()` with the appropriate
parameters for your environment, see :ref:`enablingthick`.

SQLAlchemy 2 and Django 5 have native support for python-oracledb so the above
code snippet is not needed in those versions.  Check your preferred library for
which Oracle Database driver it requires.

For details on using Superset with python-oracledb, refer to the blog post
`Steps to use Apache Superset and Oracle Database
<https://medium.com/p/ae0858b4f134>`__.
