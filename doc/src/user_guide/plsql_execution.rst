.. _plsqlexecution:

.. currentmodule:: oracledb

****************
Executing PL/SQL
****************

PL/SQL is a procedural language used for creating user-defined procedures,
functions, and anonymous blocks. PL/SQL program units are compiled and run
inside Oracle Database, letting them efficiently work on data. Procedures and
functions can be stored in the database, encapsulating business logic for reuse
in other applications.

PL/SQL code can be stored in the database, and executed using python-oracledb.

Examples in this chapter show single invocations using
:meth:`Cursor.callproc()`, :meth:`Cursor.callfunc()`, or
:meth:`Cursor.execute()`. Examples of repeated calls using
:meth:`Cursor.executemany()` are shown in :ref:`batchplsql`.

**User-defined procedures in JavaScript**

You may also be interested in creating user-defined procedures in JavaScript
instead of PL/SQL, see `Introduction to Oracle Database Multilingual Engine for
JavaScript <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-
6AEC4D40-BE51-4DC6-9B8E-22396B5B16DD>`__. These procedures can be invoked in
python-oracledb the same way PL/SQL is.

.. _plsqlproc:

PL/SQL Stored Procedures
------------------------

The :meth:`Cursor.callproc()` method is used to call PL/SQL procedures.

If a procedure with the following definition exists:

.. code-block:: sql

    create or replace procedure myproc (
        a_Value1                            number,
        a_Value2                            out number
    ) as
    begin
        a_Value2 := a_Value1 * 2;
    end;

then the following Python code can be used to call it:

.. code-block:: python

    out_val = cursor.var(int)
    cursor.callproc('myproc', [123, out_val])
    print(out_val.getvalue())        # will print 246

Calling :meth:`Cursor.callproc()` internally generates an :ref:`anonymous PL/SQL
block <anonplsql>` and executes it.  This is equivalent to the application code:

.. code-block:: python

    cursor.execute("begin myproc(:1,:2); end;", [123, out_val])

See :ref:`bind` for information on binding.


.. _plsqlfunc:

PL/SQL Stored Functions
-----------------------

The :meth:`Cursor.callfunc()` method is used to call PL/SQL functions.

The first parameter to :meth:`~Cursor.callfunc()` is the function name. The
second parameter represents the PL/SQL function return value and is expected to
be a Python type, one of the :ref:`oracledb types <types>` or an :ref:`Object
Type <dbobjecttype>`. Any following sequence of values or named parameters are
passed as PL/SQL function arguments.

If a PL/SQL function with the following definition exists:

.. code-block:: sql

    create or replace function myfunc (
        a_StrVal varchar2,
        a_NumVal number,
        a_Date out date
    ) return number as
    begin
        select sysdate into a_Date from dual;
        return length(a_StrVal) + a_NumVal * 2;
    end;

then the following Python code can be used to call it:

.. code-block:: python

    d = cursor.var(oracledb.DB_TYPE_DATE)   # for the a_Date OUT parameter
    return_val = cursor.callfunc("myfunc", int, ["a string", 15, d])
    print(return_val)        # prints 38
    print(d.getvalue())      # like 2024-12-04 22:35:23

A more complex example that returns a spatial (SDO) object can be seen below.
First, the SQL statements necessary to set up the example:

.. code-block:: sql

    create table MyPoints (
        id number(9) not null,
        point sdo_point_type not null
    );

    insert into MyPoints values (1, sdo_point_type(125, 375, 0));

    create or replace function spatial_queryfn (
        a_Id     number
    ) return sdo_point_type is
        t_Result sdo_point_type;
    begin
        select point
        into t_Result
        from MyPoints
        where Id = a_Id;

        return t_Result;
    end;
    /

The Python code that will call this procedure looks as follows:

.. code-block:: python

    obj_type = connection.gettype("SDO_POINT_TYPE")
    cursor = connection.cursor()
    return_val = cursor.callfunc("spatial_queryfn", obj_type, [1])
    print(f"({return_val.X}, {return_val.Y}, {return_val.Z})")
    # will print (125, 375, 0)

See :ref:`bind` for information on binding.


.. _anonplsql:

Anonymous PL/SQL Blocks
-----------------------

An `anonymous PL/SQL block <https://www.oracle.com/pls/topic/lookup?ctx=
dblatest&id=GUID-826B070B-4888-4398-889B-61A3C6B91349>`__ can be called as
shown:

.. code-block:: python

    var = cursor.var(int)
    cursor.execute("""
            begin
                :out_val := length(:in_val);
            end;""", in_val="A sample string", out_val=var)
    print(var.getvalue())        # will print 15

See :ref:`bind` for information on binding.


.. _plsqlnull:

Passing NULL values to PL/SQL
-----------------------------

Oracle Database requires a type, even for null values. When you pass the value
None, then python-oracledb assumes its type is a string. If this is not the
desired type, you can explicitly set it.  For example, to pass a NULL
:ref:`Oracle Spatial SDO_GEOMETRY <spatial>` object to a PL/SQL stored
procedure with the signature::

    procedure myproc(p in sdo_geometry)

You can use:

.. code-block:: python

    type_obj = connection.gettype("SDO_GEOMETRY")
    var = cursor.var(type_obj)
    cursor.callproc("myproc", [var])


Creating Stored Procedures and Packages
---------------------------------------

To create PL/SQL stored procedures and packages, use :meth:`Cursor.execute()`
with a CREATE command. For example:

.. code-block:: python

    cursor.execute("""
            create or replace procedure myprocedure
            (p_in in number, p_out out number) as
            begin
                p_out := p_in * 2;
            end;""")

.. _plsqlwarning:

PL/SQL Compilation Warnings
+++++++++++++++++++++++++++

When creating PL/SQL procedures, functions, or types in python-oracledb, the
statement might succeed without throwing an error but there may be additional
informational messages. These messages are sometimes known in Oracle as
"success with info" messages. If your application needs to show such messages,
they must be explicitly looked for using :attr:`Cursor.warning`. A subsequent
query from a table like ``USER_ERRORS`` will show more details. For example:

.. code-block:: python

    with connection.cursor() as cursor:

        cursor.execute("""
                create or replace procedure badproc as
                begin
                    WRONG WRONG WRONG
                end;""")

        if cursor.warning and cursor.warning.full_code == "DPY-7000":
            print(cursor.warning)

            # Get details
            cursor.execute("""
                    select line, position, text
                    from user_errors
                    where name = 'BADPROC' and type = 'PROCEDURE'
                    order by line, position""")
            for info in cursor:
                print("Error at line {} position {}:\n{}".format(*info))

The output would be::

    DPY-7000: creation succeeded with compilation errors
    Error at line 3 position 23:
    PLS-00103: Encountered the symbol "WRONG" when expecting one of the following:

       := . ( @ % ;


Using the %ROWTYPE Attribute
----------------------------

In PL/SQL, the `%ROWTYPE attribute
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-4E0B9FE2-909D-444A-9B4A-E0243B7FCB99>`__
lets you declare a record that represents either a full or partial row of a
database table or view.

To work with %ROWTYPE in python-oracledb, use :meth:`Connection.gettype()` to
get the relevant attribute type information.

**Getting a %ROWTYPE value from PL/SQL**

Given a PL/SQL function that returns a row of the LOCATIONS table:

.. code-block:: sql

    create or replace function TestFuncOUT return locations%rowtype as
      p locations%rowtype;
    begin
       select * into p from locations where rownum < 2;
       return p;
    end;
    /

You can use :meth:`~Connection.gettype()` to get the type of the PL/SQL
function return value, and specify this as the :meth:`~Cursor.callfunc()`
return type.  For example:

.. code-block:: python

    rt = connection.gettype("LOCATIONS%ROWTYPE")
    r = cursor.callfunc("TESTFUNCOUT", rt)

The variable ``r`` will contain the return value of the PL/SQL function as an
:ref:`Object Type <dbobjecttype>`. You can access its contents using the
methods discussed in :ref:`Fetching Oracle Database Objects and Collections
<fetchobjects>`.  The helper function ``dump_object()`` defined there is a
convenient example:

.. code-block:: python

    dump_object(r)

Output will be::

    {
      LOCATION_ID: 1000
      STREET_ADDRESS: '1297 Via Cola di Rie'
      POSTAL_CODE: '00989'
      CITY: 'Roma'
      STATE_PROVINCE: None
      COUNTRY_ID: 'IT'
    }


**Constructing a %ROWTYPE value in python-oracledb**

You can construct a similar object directly in python-oracledb by using
:meth:`DbObjectType.newobject()` and setting any desired fields.  For example:

.. code-block:: python

    rt = connection.gettype("LOCATIONS%ROWTYPE")
    r = rt.newobject()
    r.CITY = 'Roma'

**Passing a %ROWTYPE value into PL/SQL**

Given the PL/SQL procedure:

.. code-block:: sql

    create or replace procedure TestProcIN(p in locations%rowtype, city out varchar2) as
    begin
        city := p.city;
    end;

you can call :meth:`~Cursor.callproc()` passing the variable ``r`` from the
previous :meth:`~Cursor.callfunc()` or :meth:`~DbObjectType.newobject()`
examples in the appropriate parameter position, for example:

.. code-block:: python

    c = cursor.var(oracledb.DB_TYPE_VARCHAR)
    cursor.callproc("TESTPROCIN", [r, c])
    print(c.getvalue())

This prints::

    Roma


See `plsql_rowtype.py
<https://github.com/oracle/python-oracledb/tree/main/samples/plsql_rowtype.py>`__
for a runnable example.


Using DBMS_OUTPUT
-----------------

The standard way to print output from PL/SQL is with the package `DBMS_OUTPUT
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-C1400094-18D5-4F36-A2C9-D28B0E12FD8C>`__.  Note, PL/SQL code that uses
``DBMS_OUTPUT`` runs to completion before any output is available to the user.
Also, other database connections cannot access the buffer.

To use DBMS_OUTPUT:

* Call the PL/SQL procedure ``DBMS_OUTPUT.ENABLE()`` to enable output to be
  buffered for the connection.
* Execute some PL/SQL that calls ``DBMS_OUTPUT.PUT_LINE()`` to put text in the
  buffer.
* Call ``DBMS_OUTPUT.GET_LINE()`` or ``DBMS_OUTPUT.GET_LINES()`` repeatedly to
  fetch the text from the buffer until there is no more output.


For example:

.. code-block:: python

    # enable DBMS_OUTPUT
    cursor.callproc("dbms_output.enable")

    # execute some PL/SQL that calls DBMS_OUTPUT.PUT_LINE
    cursor.execute("""
            begin
                dbms_output.put_line('This is the python-oracledb manual');
                dbms_output.put_line('Demonstrating how to use DBMS_OUTPUT');
            end;""")

    # tune this size for your application
    chunk_size = 100

    # create variables to hold the output
    lines_var = cursor.arrayvar(str, chunk_size)
    num_lines_var = cursor.var(int)
    num_lines_var.setvalue(0, chunk_size)

    # fetch the text that was added by PL/SQL
    while True:
        cursor.callproc("dbms_output.get_lines", (lines_var, num_lines_var))
        num_lines = num_lines_var.getvalue()
        lines = lines_var.getvalue()[:num_lines]
        for line in lines:
            print(line or "")
        if num_lines < chunk_size:
            break

This will produce the following output::

    This is the python-oracledb manual
    Demonstrating use of DBMS_OUTPUT

An alternative is to call ``DBMS_OUTPUT.GET_LINE()`` once per output line,
which may be much slower:

.. code-block:: python

    text_var = cursor.var(str)
    status_var = cursor.var(int)
    while True:
        cursor.callproc("dbms_output.get_line", (text_var, status_var))
        if status_var.getvalue() != 0:
            break
        print(text_var.getvalue())

.. _implicitresults:

Implicit Results
----------------

Implicit results permit a Python program to consume cursors returned by a
PL/SQL block without the requirement to use OUT :ref:`REF CURSOR <refcur>`
parameters. The method :meth:`Cursor.getimplicitresults()` can be used for this
purpose. It needs Oracle Database 12.1 (or later). For python-oracledb
:ref:`Thick <enablingthick>` mode, Oracle Client 12.1 (or later) is
additionally required.

An example using implicit results is as shown:

.. code-block:: python

    cursor.execute("""
            declare
                cust_cur sys_refcursor;
                sales_cur sys_refcursor;
            begin
                open cust_cur for SELECT * FROM cust_table;
                dbms_sql.return_result(cust_cur);

                open sales_cur for SELECT * FROM sales_table;
                dbms_sql.return_result(sales_cur);
            end;""")

    for implicit_cursor in cursor.getimplicitresults():
        for row in implicit_cursor:
            print(row)

Data from both the result sets are returned::

    (1, 'Tom')
    (2, 'Julia')
    (1000, 1, 'BOOKS')
    (2000, 2, 'FURNITURE')

When using python-oracledb Thick mode, you must leave the parent cursor open
until all of the implicit result sets have been fetched or until your
application no longer requires them. Closing the parent cursor before
fetching all of the implicit result sets will result in the closure of the
implicit result set cursors. If you try to fetch from an implicit result set
after its parent cursor is closed, the following error will be thrown::

    DPI-1039: statement was already closed

Note that the requirement mentioned above is not applicable for
python-oracledb Thin mode. See :ref:`implicitresultsdiff`.

.. _ebr:

Edition-Based Redefinition (EBR)
--------------------------------

Oracle Database's `Edition-Based Redefinition <https://www.oracle.com/pls/topic
/lookup?ctx=dblatest&id=GUID-58DE05A0-5DEF-4791-8FA8-F04D11964906>`__ feature
enables upgrading of the database component of an application while it is in
use, thereby minimizing or eliminating down time. This feature allows multiple
versions of views, synonyms, PL/SQL objects and SQL Translation profiles to be
used concurrently. Different versions of the database objects are associated
with an "edition".

The simplest way to set the edition used by your applications is to pass the
``edition`` parameter to :meth:`oracledb.connect()` or
:meth:`oracledb.create_pool()`:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                   dsn="dbhost.example.com/orclpdb",
                                   edition="newsales")


The edition can also be set by executing the SQL statement:

.. code-block:: sql

    alter session set edition = <edition name>;

You can also set the environment variable ``ORA_EDITION`` to your edition name.

Regardless of which method sets the edition, the value that is in use can be
seen by examining the attribute :attr:`Connection.edition`. If no value has
been set, the value will be None. This corresponds to the database default
edition ``ORA$BASE``.

Consider an example where one version of a PL/SQL function ``Discount`` is
defined in the database default edition ``ORA$BASE`` and the other version of
the same function is defined in a user created edition ``DEMO``.  In your SQL
editor run:

.. code-block:: sql

    connect <username>/<password>

    -- create function using the database default edition
    CREATE OR REPLACE FUNCTION Discount(price IN NUMBER) RETURN NUMBER IS
    BEGIN
        return price * 0.9;
    END;
    /

A new edition named 'DEMO' is created and the user given permission to use
editions. The use of ``FORCE`` is required if the user already contains one or
more objects whose type is editionable and that also have non-editioned
dependent objects.

.. code-block:: sql

    connect system/<password>

    CREATE EDITION demo;
    ALTER USER <username> ENABLE EDITIONS FORCE;
    GRANT USE ON EDITION demo to <username>;

The ``Discount`` function for the demo edition is as follows:

.. code-block:: sql

    connect <username>/<password>

    alter session set edition = demo;

    -- Function for the demo edition
    CREATE OR REPLACE FUNCTION Discount(price IN NUMBER) RETURN NUMBER IS
    BEGIN
        return price * 0.5;
    END;
    /

A Python application can then call the required version of the PL/SQL function
as shown:

.. code-block:: python

    connection = oracledb.connect(user=user, password=password,
                                   dsn="dbhost.example.com/orclpdb")
    print("Edition is:", repr(connection.edition))

    cursor = connection.cursor()
    discounted_price = cursor.callfunc("Discount", int, [100])
    print("Price after discount is:", discounted_price)

    # Use the edition parameter for the connection
    connection = oracledb.connect(user=user, password=password,
                                   dsn="dbhost.example.com/orclpdb",
                                   edition="demo")
    print("Edition is:", repr(connection.edition))

    cursor = connection.cursor()
    discounted_price = cursor.callfunc("Discount", int, [100])
    print("Price after discount is:", discounted_price)

The output of the function call for the default and demo edition is as shown::

    Edition is: None
    Price after discount is:  90
    Edition is: 'DEMO'
    Price after discount is:  50
