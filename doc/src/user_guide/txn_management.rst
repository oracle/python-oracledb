.. _txnmgmnt:

*********************
Managing Transactions
*********************

A database transaction is a grouping of SQL statements that make a logical data
change to the database. When statements like :meth:`Cursor.execute()` or
:meth:`Cursor.executemany()` execute SQL statements like INSERT or UPDATE, a
transaction is started or continued. By default, python-oracledb does not
commit this transaction to the database.  You can explictly commit or roll it
back using the methods :meth:`Connection.commit()` and
:meth:`Connection.rollback()`. For example to commit a new row:

.. code-block:: python

    cursor = connection.cursor()
    cursor.execute("insert into mytab (name) values ('John')")
    connection.commit()

Transactions are handled at the connection level, meaning changes performed by
all cursors obtained from a connection will be committed or rolled back
together.

When a database connection is closed, such as with :meth:`Connection.close()`,
or when variables referencing the connection go out of scope, any uncommitted
transaction will be rolled back.

When `Data Definition Language (DDL) <https://www.oracle.com/pls/topic/lookup?
ctx=dblatest&id=GUID-FD9A8CB4-6B9A-44E5-B114-EFB8DA76FC88>`__ statements such
as CREATE are executed, Oracle Database will always perform a commit.


Autocommitting
==============

An alternative way to commit is to set the attribute
:attr:`Connection.autocommit` of the connection to ``True``.  This ensures all
:ref:`DML <dml>` statements (INSERT, UPDATE, and so on) are committed as they
are executed.  Unlike :meth:`Connection.commit()`, this does not require an
additional :ref:`round-trip <roundtrips>` to the database so it is more
efficient when used appropriately.

When executing multiple DML statements that constitute a single transaction, it
is recommended to use autocommit mode only for the last DML statement in the
sequence of operations.

.. warning::

    Overuse of the mode can impact database performance. It can also destroy
    relational data consistency when related changes made to multiple tables
    are committed independently, causing table data to be out of sync.

Note that irrespective of the autocommit value, Oracle Database will always
commit an open transaction when a DDL statement is executed.

The example below shows a new customer being added to the table ``CUST_TABLE``.
The corresponding ``SALES`` table is updated with a purchase of 3000 pens from
the customer.  The final insert uses autocommit mode to commit both new
records:

.. code-block:: python

    # Add a new customer
    id_var = cursor.var(int)
    connection.autocommit = False  # make sure any previous value is off
    cursor.execute("""
            INSERT INTO cust_table (name) VALUES ('John')
            RETURNING id INTO :bvid""", bvid=id_var)

    # Add sales data for the new customer and commit all new values
    id_val = id_var.getvalue()[0]
    connection.autocommit = True
    cursor.execute("INSERT INTO sales_table VALUES (:bvid, 'pens', 3000)",
            bvid=id_val)


Explicit Transactions
=====================

The method :meth:`Connection.begin()` can be used to explicitly start a local
or global transaction.

Without parameters, this explicitly begins a local transaction; otherwise, this
explicitly begins a distributed (global) transaction with the given parameters.
See the Oracle documentation for more details.

Note that in order to make use of global (distributed) transactions, the
attributes :attr:`Connection.internal_name` and
:attr:`Connection.external_name` attributes must be set.

Distributed Transactions
========================

For information on distributed transactions, see the chapter :ref:`tpc`.
