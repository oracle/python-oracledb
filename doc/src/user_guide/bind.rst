.. _bind:

********************
Using Bind Variables
********************

SQL and PL/SQL statements that pass data to and from Oracle Database should use
placeholders in SQL and PL/SQL statements that mark where data is supplied or
returned.  A bind variable placeholder is a colon-prefixed identifier or
numeral. For example, ``:dept_id`` and ``:dept_name`` are the two bind variable
placeholders in this SQL statement:

.. code-block:: python

    sql = """insert into departments (department_id, department_name)
             values (:dept_id, :dept_name)"""
    cursor.execute(sql, [280, "Facility"])

As part of execution, the supplied bind variable values ``280`` and
``"Facility"`` are substituted for the placeholders by the database.  This is
called binding.

Using bind variables is important for scalability and security.  They help avoid
SQL Injection security problems because data is never treated as part of an
executable statement when it is parsed.

Bind variables reduce parsing and execution costs when statements are executed
more than once with different data values.  If you do not use bind variables,
Oracle must reparse and cache multiple statements.  When using bind variables,
Oracle Database may be able to reuse the statement execution plan and context.

.. warning::

    Never concatenate or interpolate user data into SQL statements:

    .. code-block:: python

        did = 280
        dnm = "Facility"

        # !! Never do this !!
        sql = f"""insert into departments (department_id, department_name)
                  values ({did}, '{dnm}')"""
        cursor.execute(sql)

    This is a security risk and can impact performance and scalability.

Bind variables can be used to substitute data, but cannot be used to substitute
the text of the statement.  You cannot, for example, use a bind variable
placeholder where a column name or a table name is required.  Bind variable
placeholders also cannot be used in Data Definition Language (DDL) statements,
such as CREATE TABLE or ALTER statements.

Binding by Name or Position
===========================

Binding can be done "by name" or "by position".

.. _bindbyname:

Bind by Name
------------

A named bind is performed when the bind variables in the Python statement use
the names of placeholders in the SQL or PL/SQL statement. For example:

.. code-block:: python

    cursor.execute("""
            insert into departments (department_id, department_name)
            values (:dept_id, :dept_name)""",
            dept_id=280, dept_name="Facility")

Alternatively, the parameters can be passed as a dictionary instead of as
keyword parameters:

.. code-block:: python

    data = dict(dept_id=280, dept_name="Facility")
    cursor.execute("""
            insert into departments (department_id, department_name)
            values (:dept_id, :dept_name)""", data)

In the above examples, the keyword parameter names or the keys of the
dictionary must match the bind variable placeholder names.

The advantages of named binding are that the order of the bind values in the
``execute()`` parameter is not important, the names can be meaningful, and the
placeholder names can be repeated while still only supplying the value once in
the application.

An example of reusing a bind variable placeholder is:

.. code-block:: python

    cursor.execute("""
            update departments set department_id = :dept_id + 10
            where department_id = :dept_id""",
            dept_id=280)

.. _bindbyposition:

Bind by Position
----------------

Positional binding occurs when a list or tuple of bind values is passed to the
``execute()`` call. For example:

.. code-block:: python

    cursor.execute("""
            insert into departments (department_id, department_name)
            values (:1, :2)""", [280, "Facility"])

The following example (which changes the order of the bind placeholder names)
has exactly the same behavior.  The value used to substitute the placeholder
":2" will be the first element of the list and ":1" will be replaced by the
second element.  Bind by position works from left to right and pays no
attention to the name of the bind variable:

.. code-block:: python

    cursor.execute("""
            insert into departments (department_id, department_name)
            values (:2, :1)""", [280, "Facility"])

The following example is also bind by position despite the bind placeholders
having alphabetic names.  The actual process of binding uses the list positions
of the input data to associate the data with the placeholder locations:

.. code-block:: python

    cursor.execute("""
            insert into departments (department_id, department_name)
            values (:dept_id, :dept_name)""", [280, "Facility"])


Python tuples can also be used for binding by position:

.. code-block:: python

    cursor.execute("""
            insert into departments (department_id, department_name)
            values (:1, :2)""", (280, "Facility"))

If only a single bind placeholder is used in the SQL or PL/SQL statement, the
data can be a list like ``[280]`` or a single element tuple like ``(280,)``.

When using bind by position for SQL statements, the order of the bind values
must exactly match the order of each bind variable and duplicated names must
have their values repeated. For PL/SQL statements, however, the order of the
bind values must exactly match the order of each **unique** bind variable found
in the PL/SQL block and values should not be repeated. In order to avoid this
difference, binding by name is recommended when bind variable names are
repeated.


Bind Direction
==============

The caller can supply data to the database (IN), the database can return data
to the caller (OUT) or the caller can supply initial data to the database and
the database can supply the modified data back to the caller (IN/OUT). This is
known as the bind direction.

The examples shown above have all supplied data to the database and are
therefore classified as IN bind variables. In order to have the database return
data to the caller, a variable must be created. This is done by calling the
method :func:`Cursor.var()`, which identifies the type of data that will be
found in that bind variable and its maximum size among other things.

Here is an example showing how to use OUT binds. It calculates the sum of the
integers 8 and 7 and stores the result in an OUT bind variable of type integer:

.. code-block:: python

    out_val = cursor.var(int)
    cursor.execute("""
            begin
                :out_val := :in_bind_var1 + :in_bind_var2;
            end;""",
            out_val=out_val, in_bind_var1=8, in_bind_var2=7)
    print(out_val.getvalue())        # will print 15

If instead of simply getting data back you wish to supply an initial value to
the database, you can set the variable's initial value. This example is the
same as the previous one but it sets the initial value first:

.. code-block:: python

    in_out_var = cursor.var(int)
    in_out_var.setvalue(0, 25)
    cursor.execute("""
            begin
                :in_out_bind_var := :in_out_bind_var + :in_bind_var1 +
                        :in_bind_var2;
            end;""",
            in_out_bind_var=in_out_var, in_bind_var1=8, in_bind_var2=7)
    print(in_out_var.getvalue())        # will print 40

When binding data to parameters of PL/SQL procedures that are declared as OUT
parameters, it is worth noting that any value that is set in the bind variable
will be ignored. In addition, any parameters declared as IN/OUT that do not
have a value set will start out with a value of ``null``.


Binding Null Values
===================

To insert a NULL into a character column you can bind the Python singleton
``None``. For example, with the table::

    create table tab (id number, val varchar2(50));

You can use:

.. code-block:: python

    cursor.execute("insert into tab (id, val) values (:i, :v)", i=280, v=None)

Python-oracledb assumes the value will be a string (equivalent to a VARCHAR2
column). If you need to use a different Oracle Database data type you will need
to make a call to :func:`Cursor.setinputsizes()` or create a bind variable with
the correct type by calling :func:`Cursor.var()`.

For example, if the table had been created using an :ref:`Oracle Spatial
SDO_GEOMETRY <spatial>` object column::

    create table tab (id number, val sdo_geometry);

Then the previous code would fail with::

    ORA-00932: expression is of data type CHAR, which is incompatible with expected data type MDSYS.SDO_GEOMETRY

To insert a NULL into the new table, use:

.. code-block:: python

    type_obj = connection.gettype("SDO_GEOMETRY")
    var = cursor.var(type_obj)
    cursor.execute("insert into tab (id, val) values (:i, :v)", i=280, v=var)

Alternatively use:

.. code-block:: python

    type_obj = connection.gettype("SDO_GEOMETRY")
    cursor.setinputsizes(i=None, v=type_obj)
    cursor.execute("insert into tab (id, val) values (:i, :v)", i=280, v=None)


Binding ROWID Values
====================

The pseudo-column ROWID uniquely identifies a row in a table.  In
python-oracledb, ROWID values are represented as strings. The example below shows
fetching a row and then updating that row by binding its rowid:

.. code-block:: python

    # fetch the row
    cursor.execute("""
            select rowid, manager_id
            from departments
            where department_id = :dept_id""", dept_id=280)
    rowid, manager_id = cursor.fetchone()

    # update the row by binding ROWID
    cursor.execute("""
            update departments set
                manager_id = :manager_id
            where rowid = :rid""", manager_id=205, rid=rowid)


Binding UROWID Values
=====================

Universal rowids (UROWID) are used to uniquely identify rows in index
organized tables. In python-oracledb, UROWID values are represented as strings.
The example below shows fetching a row from index organized table
``universal_rowids`` and then updating that row by binding its urowid:

.. code-block:: sql

    CREATE TABLE universal_rowids (
        int_col number(9) not null,
        str_col varchar2(250) not null,
        date_col date not null,
        CONSTRAINT universal_rowids_pk PRIMARY KEY(int_col, str_col, date_col)
    ) ORGANIZATION INDEX


.. code-block:: python

    ridvar = cursor.var(oracledb.DB_TYPE_UROWID)

    # fetch the row
    cursor.execute("""
            begin
                select rowid into :rid from universal_rowids
                where int_col = 3;
            end;""", rid=ridvar)

    # update the row by binding UROWID
    cursor.execute("""
            update universal_rowids set
                str_col = :str_val
            where rowid = :rowid_val""",
            str_val="String #33", rowid_val=ridvar)

Note that the type :attr:`oracledb.DB_TYPE_UROWID` is only supported in
python-oracledb Thin mode. For python-oracledb Thick mode, the database type
UROWID can be bound with type :attr:`oracledb.DB_TYPE_ROWID`.
See :ref:`querymetadatadiff`.


.. _dml-returning-bind:

DML RETURNING Bind Variables
============================

When a RETURNING clause is used with a DML statement like UPDATE,
INSERT, or DELETE, the values are returned to the application through
the use of OUT bind variables. Consider the following example:

.. code-block:: python

    # The RETURNING INTO bind variable is a string
    dept_name = cursor.var(str)

    cursor.execute("""
            update departments set
                location_id = :loc_id
            where department_id = :dept_id
            returning department_name into :dept_name""",
            loc_id=1700, dept_id=50, dept_name=dept_name)
    print(dept_name.getvalue())     # will print ['Shipping']

In the above example, since the WHERE clause matches only one row, the output
contains a single item in the list. If the WHERE clause matched multiple rows,
the output would contain as many items as there were rows that were updated.

The same bind variable placeholder name cannot be used both before and after
the RETURNING clause. For example, if the ``:dept_name`` bind variable is used
both before and after the RETURNING clause:

.. code-block:: python

    # a variable cannot be used for both input and output in a DML returning
    # statement
    dept_name_var = cursor.var(str)
    dept_name_var.setvalue(0, 'Input Department')
    cursor.execute("""
            update departments set
                department_name = :dept_name || ' EXTRA TEXT'
            returning department_name into :dept_name""",
            dept_name=dept_name_var)

The above example will not update the bind variable as expected, but no error
will be raised if you are using python-oracledb Thick mode. With
python-oracledb Thin mode, the above example returns the following error::

    DPY-2048: the bind variable placeholder ":dept_name" cannot be used
    both before and after the RETURNING clause in a DML RETURNING statement


LOB Bind Variables
==================

Database CLOBs, NCLOBS, BLOBs, and BFILEs can be bound with types
:attr:`oracledb.DB_TYPE_CLOB`, :attr:`oracledb.DB_TYPE_NCLOB`,
:attr:`oracledb.DB_TYPE_BLOB` and :attr:`oracledb.DB_TYPE_BFILE`
respectively. LOBs fetched from the database or created with
:meth:`Connection.createlob()` can also be bound.

LOBs may represent Oracle Database persistent LOBs (those stored in tables) or
temporary LOBs (such as those created with :meth:`Connection.createlob()` or
returned by some SQL and PL/SQL operations).

LOBs can be used as IN, OUT, or IN/OUT bind variables.

See :ref:`lobdata` for examples.

.. _refcur:

REF CURSOR Bind Variables
=========================

Python-oracledb provides the ability to bind and define PL/SQL REF cursors.  As an
example, consider the PL/SQL procedure:

.. code-block:: sql

    CREATE OR REPLACE PROCEDURE find_employees (
        p_query IN VARCHAR2,
        p_results OUT SYS_REFCURSOR
    ) AS
    BEGIN
        OPEN p_results FOR
            SELECT employee_id, first_name, last_name
            FROM employees
            WHERE UPPER(first_name || ' ' || last_name || ' ' || email)
                LIKE '%' || UPPER(p_query) || '%';
    END;
    /

A newly opened cursor can be bound to the REF CURSOR parameter as shown in the
following Python code. After the PL/SQL procedure has been called with
:meth:`Cursor.callproc()`, the cursor can then be fetched just like any other
cursor which had executed a SQL query:

.. code-block:: python

    ref_cursor = connection.cursor()
    cursor.callproc("find_employees", ['Smith', ref_cursor])
    for row in ref_cursor:
        print(row)

With Oracle's `sample HR schema
<https://github.com/oracle/db-sample-schemas>`__ there are two
employees with the last name 'Smith' so the result is::

    (159, 'Lindsey', 'Smith')
    (171, 'William', 'Smith')

To return a REF CURSOR from a PL/SQL function, use ``oracledb.DB_TYPE_CURSOR`` for the
return type of :meth:`Cursor.callfunc()`:

.. code-block:: python

    ref_cursor = cursor.callfunc('example_package.f_get_cursor',
                                 oracledb.DB_TYPE_CURSOR)
    for row in ref_cursor:
        print(row)

See :ref:`tuning` for information on how to tune REF CURSORS.

Also see :ref:`Implicit Results <implicitresults>` which provides an
alternative way to return query results from PL/SQL procedures.

Binding PL/SQL Collections
==========================

PL/SQL Collections like Associative Arrays can be bound as IN, OUT, and IN/OUT
variables.  When binding IN values, an array can be passed directly as shown in
this example, which sums up the lengths of all of the strings in the provided
array. First the PL/SQL package definition:

.. code-block:: sql

    create or replace package mypkg as

        type udt_StringList is table of varchar2(100) index by binary_integer;

        function DemoCollectionIn (
            a_Values            udt_StringList
        ) return number;

    end;
    /

    create or replace package body mypkg as

        function DemoCollectionIn (
            a_Values            udt_StringList
        ) return number is
            t_ReturnValue       number := 0;
        begin
            for i in 1..a_Values.count loop
                t_ReturnValue := t_ReturnValue + length(a_Values(i));
            end loop;
            return t_ReturnValue;
        end;

    end;
    /

Then the Python code:

.. code-block:: python

    values = ["String One", "String Two", "String Three"]
    return_val = cursor.callfunc("mypkg.DemoCollectionIn", int, [values])
    print(return_val)        # will print 32

In order get values back from the database, a bind variable must be created
using :meth:`Cursor.arrayvar()`. The first parameter to this method is a Python
type that python-oracledb knows how to handle or one of the oracledb :ref:`types`.
The second parameter is the maximum number of elements that the array can hold
or an array providing the value (and indirectly the maximum length). The final
parameter is optional and only used for strings and bytes. It identifies the
maximum length of the strings and bytes that can be stored in the array. If not
specified, the length defaults to 4000 bytes.

Consider the following PL/SQL package:

.. code-block:: sql

    create or replace package mypkg as

        type udt_StringList is table of varchar2(100) index by binary_integer;

        procedure DemoCollectionOut (
            a_NumElements       number,
            a_Values            out nocopy udt_StringList
        );

        procedure DemoCollectionInOut (
            a_Values            in out nocopy udt_StringList
        );

    end;
    /

    create or replace package body mypkg as

        procedure DemoCollectionOut (
            a_NumElements       number,
            a_Values            out nocopy udt_StringList
        ) is
        begin
            for i in 1..a_NumElements loop
                a_Values(i) := 'Demo out element #' || to_char(i);
            end loop;
        end;

        procedure DemoCollectionInOut (
            a_Values            in out nocopy udt_StringList
        ) is
        begin
            for i in 1..a_Values.count loop
                a_Values(i) := 'Converted element #' || to_char(i) ||
                        ' originally had length ' || length(a_Values(i));
            end loop;
        end;

    end;
    /

The Python code to process an OUT collection will be as follows. Note the
call to :meth:`Cursor.arrayvar()` which creates space for an array of strings.
Each string permits up to 100 bytes and only 10 strings are permitted. If the
PL/SQL block exceeds the maximum number of strings allowed the error
``ORA-06513: PL/SQL: index for PL/SQL table out of range for host
language array`` will be raised.

.. code-block:: python

    out_array_var = cursor.arrayvar(str, 10, 100)
    cursor.callproc("mypkg.DemoCollectionOut", [5, out_array_var])
    for val in out_array_var.getvalue():
        print(val)

This would produce the following output::

    Demo out element #1
    Demo out element #2
    Demo out element #3
    Demo out element #4
    Demo out element #5

The Python code to process IN/OUT collections is similar. Note the different
call to :meth:`Cursor.arrayvar()` which creates space for an array of strings,
but uses an array to determine both the maximum length of the array and its
initial value.

.. code-block:: python

    in_values = ["String One", "String Two", "String Three", "String Four"]
    in_out_array_var = cursor.arrayvar(str, in_values)
    cursor.callproc("mypkg.DemoCollectionInOut", [in_out_array_var])
    for val in in_out_array_var.getvalue():
        print(val)

This will produce the following output::

    Converted element #1 originally had length 10
    Converted element #2 originally had length 10
    Converted element #3 originally had length 12
    Converted element #4 originally had length 11

If an array variable needs to have an initial value but also needs to allow
for more elements than the initial value contains, the following code can be
used instead:

.. code-block:: python

    in_out_array_var = cursor.arrayvar(str, 10, 100)
    in_out_array_var.setvalue(0, ["String One", "String Two"])

All of the collections that have been bound in preceding examples have used
contiguous array elements. If an associative array with sparse array elements
is needed, a different approach is required. Consider the following PL/SQL
code:

.. code-block:: sql

    create or replace package mypkg as

        type udt_StringList is table of varchar2(100) index by binary_integer;

        procedure DemoCollectionOut (
            a_Value                         out nocopy udt_StringList
        );

    end;
    /

    create or replace package body mypkg as

        procedure DemoCollectionOut (
            a_Value                         out nocopy udt_StringList
        ) is
        begin
            a_Value(-1048576) := 'First element';
            a_Value(-576) := 'Second element';
            a_Value(284) := 'Third element';
            a_Value(8388608) := 'Fourth element';
        end;

    end;
    /

Note that the collection element indices are separated by large values. The
technique used above would fail with the exception ``ORA-06513: PL/SQL: index
for PL/SQL table out of range for host language array``. The code required to
process this collection looks like this instead:

.. code-block:: python

    collection_type = connection.gettype("MYPKG.UDT_STRINGLIST")
    collection = collection_type.newobject()
    cursor.callproc("mypkg.DemoCollectionOut", [collection])
    print(collection.aslist())

This produces the output::

    ['First element', 'Second element', 'Third element', 'Fourth element']

Note the use of :meth:`Object.aslist()` which returns the collection element
values in index order as a simple Python list. The indices themselves are lost
in this approach. The associative array can be turned into a Python dictionary
using :meth:`Object.asdict()`. If that value was printed in the previous
example instead, the output would be::

    {-1048576: 'First element', -576: 'Second element', 284: 'Third element', 8388608: 'Fourth element'}

If the elements need to be traversed in index order, the methods
:meth:`Object.first()` and :meth:`Object.next()` can be used. The method
:meth:`Object.getelement()` can be used to acquire the element at a particular
index. This is shown in the following code:

.. code-block:: python

    ix = collection.first()
    while ix is not None:
        print(ix, "->", collection.getelement(ix))
        ix = collection.next(ix)

This produces the output::

    -1048576 -> First element
    -576 -> Second element
    284 -> Third element
    8388608 -> Fourth element

Similarly, the elements can be traversed in reverse index order using the
methods :meth:`Object.last()` and :meth:`Object.prev()` as shown in the
following code:

.. code-block:: python

    ix = collection.last()
    while ix is not None:
        print(ix, "->", collection.getelement(ix))
        ix = collection.prev(ix)

This produces the output::

    8388608 -> Fourth element
    284 -> Third element
    -576 -> Second element
    -1048576 -> First element


Binding PL/SQL Records
======================

PL/SQL record type objects can also be bound for IN, OUT, and IN/OUT
bind variables.  For example:

.. code-block:: sql

    create or replace package mypkg as

        type udt_DemoRecord is record (
            NumberValue                     number,
            StringValue                     varchar2(30),
            DateValue                       date,
            BooleanValue                    boolean
        );

        procedure DemoRecordsInOut (
            a_Value                         in out nocopy udt_DemoRecord
        );

    end;
    /

    create or replace package body mypkg as

        procedure DemoRecordsInOut (
            a_Value                         in out nocopy udt_DemoRecord
        ) is
        begin
            a_Value.NumberValue := a_Value.NumberValue * 2;
            a_Value.StringValue := a_Value.StringValue || ' (Modified)';
            a_Value.DateValue := a_Value.DateValue + 5;
            a_Value.BooleanValue := not a_Value.BooleanValue;
        end;

    end;
    /

Then this Python code can be used to call the stored procedure which will
update the record:

.. code-block:: python

    # create and populate a record
    record_type = connection.gettype("MYPKG.UDT_DEMORECORD")
    record = record_type.newobject()
    record.NUMBERVALUE = 6
    record.STRINGVALUE = "Test String"
    record.DATEVALUE = datetime.datetime(2016, 5, 28)
    record.BOOLEANVALUE = False

    # show the original values
    print("NUMBERVALUE ->", record.NUMBERVALUE)
    print("STRINGVALUE ->", record.STRINGVALUE)
    print("DATEVALUE ->", record.DATEVALUE)
    print("BOOLEANVALUE ->", record.BOOLEANVALUE)
    print()

    # call the stored procedure which will modify the record
    cursor.callproc("mypkg.DemoRecordsInOut", [record])

    # show the modified values
    print("NUMBERVALUE ->", record.NUMBERVALUE)
    print("STRINGVALUE ->", record.STRINGVALUE)
    print("DATEVALUE ->", record.DATEVALUE)
    print("BOOLEANVALUE ->", record.BOOLEANVALUE)

This will produce the following output::

    NUMBERVALUE -> 6
    STRINGVALUE -> Test String
    DATEVALUE -> 2016-05-28 00:00:00
    BOOLEANVALUE -> False

    NUMBERVALUE -> 12
    STRINGVALUE -> Test String (Modified)
    DATEVALUE -> 2016-06-02 00:00:00
    BOOLEANVALUE -> True

Note that when manipulating records, all of the attributes must be set by the
Python program in order to avoid an Oracle Client bug which will result in
unexpected values or the Python application segfaulting.

.. _spatial:

Binding Spatial Data Types
==========================

Oracle Spatial data types objects can be represented by Python objects and their
attribute values can be read and updated. The objects can further be bound and
committed to database. This is similar to the examples above.

An example of fetching SDO_GEOMETRY is in :ref:`Oracle Database Objects and
Collections <fetchobjects>`.

.. _sqlversioncount:

Reducing the SQL Version Count
==============================

When repeated calls to :meth:`Cursor.execute()` or :meth:`Cursor.executemany()`
bind different string data lengths, then using :meth:`Cursor.setinputsizes()`
can help reduce Oracle Database's SQL "`version count
<https://support.oracle.com/knowledge/Oracle%20Cloud/296377_1.html>`__" for the
statement. The version count is the number of child cursors used for the same
statement text. The database will have a parent cursor representing the text of
a statement, and a number of child cursors for differing executions of the
statement, for example when different bind variable types or lengths are used.

For example, with a table created as::

    create table mytab (c1 varchar2(25), c2 varchar2(100), c3 number);

You can use :meth:`~Cursor.setinputsizes()` to help reduce the number of child
cursors:

.. code-block:: python

    sql = "insert into mytab (c1, c2) values (:1, :2)"

    cursor.setinputsizes(25, 15)

    s1 = "abc"
    s2 = "def"
    cursor.execute(sql, [s1, s2])

    s1 = "aaaaaaaaaaaaaaaaaaaaaaaaa"
    s2 = "z"
    cursor.execute(sql, [s1, s2])

The :meth:`~Cursor.setinputsizes()` call indicates that the first value bound
will be a Python string of no more than 25 characters and the second value
bound will be a string of no more than 15 characters.  If the data string
lengths exceed the :meth:`~Cursor.setinputsizes()` values, then python-oracledb
will accept them but there will be no processing benefit.

It is not uncommon for SQL statements to have low hundreds of
versions. Sometimes this is expected and not a result of any issue. To
determine the reason, find the SQL identifier of the statement and then query
the Oracle Database view `V$SQL_SHARED_CURSOR <https://docs.oracle.com/en/
database/oracle/oracle-database/23/refrn/V-SQL_SHARED_CURSOR.html>`__.

The SQL identifier of a statement can be found in Oracle Database views like
`V$SQLAREA <https://docs.oracle.com/en/database/oracle/oracle-database/23/
refrn/V-SQLAREA.html>`__ after you have run a statement, or you can find it
*before* you execute the statement by using the `DBMS_SQL_TRANSLATOR.SQL_ID()
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-DFFB611B-853A-
434E-808D-D713671C3AA4>`__ function. Make sure to pass in exactly the same SQL
text, including the same whitespace:

.. code-block:: python

    sql = "insert into mytab (c1, c2) values (:1, :2)"  # statement to examine

    cursor.execute("select dbms_sql_translator.sql_id(:1) from dual", [sql])
    (sqlid,) = cursor.fetchone();
    print(sqlid)

This might print a value like::

    6h6gj3ztw2wd8

Then, to find the SQL versions, run a query to see the child cursors. For
example:

.. code-block:: python

    cursor.execute("""select child_number, reason
                      from v$sql_shared_cursor
                      where sql_id = :1 order by 1""", [sqlid])
    col_names = [c.name for c in cursor.description]
    for row in cursor.fetchall():
        r = [dict(zip(col_names, row))]
        print(r)

With the earlier code that used :meth:`~Cursor.setinputsizes()` and inserted
different data lengths you might see::

    [{'CHILD_NUMBER': 0, 'REASON': ' '}]

However if :meth:`~Cursor.setinputsizes()` had not been used, you would see two
rows and REASON would include the text "Bind mismatch", for example::

    [{'CHILD_NUMBER': 0, 'REASON': '<ChildNode><ChildNumber>0</ChildNumber><ID>39</ID><reason>Bind mismatch(22)</reason><size>4x8</size><bind_position>0</bind_position><original_oacflg>1</original_oacflg><original_oacmxl>32</original_oacmxl><upgradeable_new_oacmxl>128</upgradeable_new_oacmxl></ChildNode> '}]
    [{'CHILD_NUMBER': 1, 'REASON': '<ChildNode><ChildNumber>1</ChildNumber><ID>39</ID><reason>Bind mismatch(22)</reason><size>4x8</size><bind_position>0</bind_position><original_oacflg>1</original_oacflg><original_oacmxl>128</original_oacmxl><upgradeable_new_oacmxl>32</upgradeable_new_oacmxl></ChildNode> '}]


.. _inputtypehandlers:

Changing Bind Data Types using an Input Type Handler
====================================================

Input Type Handlers allow applications to change how data is bound to
statements, or even to enable new types to be bound directly.

An input type handler is enabled by setting the attribute
:attr:`Cursor.inputtypehandler` or :attr:`Connection.inputtypehandler`.

**Inserting NaN values as NULL in NUMBER columns**

To insert NaN values as NULLs in a NUMBER column, use an input type handler
with an inconverter:

.. code-block:: python

    def input_type_handler(cursor, value, arraysize):
      if isinstance(value, float):
          return cursor.var(oracledb.DB_TYPE_NUMBER, arraysize=arraysize,
                            inconverter=lambda x: None if math.isnan(x) else x)

    connection.inputtypehandler = input_type_handler

Note that this is not needed for BINARY_FLOAT or BINARY_DOUBLE columns.

**Binding Python Objects**

Input type handlers can be combined with variable converters to bind Python
objects seamlessly:

.. code-block:: python

    # A standard Python object
    class Building:

        def __init__(self, build_id, description, num_floors, date_built):
            self.building_id = build_id
            self.description = description
            self.num_floors = num_floors
            self.date_built = date_built

    building = Building(1, "Skyscraper 1", 5, datetime.date(2001, 5, 24))

    # Get Python representation of the Oracle user defined type UDT_BUILDING
    obj_type = con.gettype("UDT_BUILDING")

    # convert a Python Building object to the Oracle user defined type
    # UDT_BUILDING
    def building_in_converter(value):
        obj = obj_type.newobject()
        obj.BUILDINGID = value.building_id
        obj.DESCRIPTION = value.description
        obj.NUMFLOORS = value.num_floors
        obj.DATEBUILT = value.date_built
        return obj

    def input_type_handler(cursor, value, num_elements):
        if isinstance(value, Building):
            return cursor.var(obj_type, arraysize=num_elements,
                              inconverter=building_in_converter)


    # With the input type handler, the bound Python object is converted
    # to the required Oracle object before being inserted
    cur.inputtypehandler = input_type_handler
    cur.execute("insert into myTable values (:1, :2)", (1, building))


Binding Multiple Values to a SQL WHERE IN Clause
================================================

To use a SQL IN list with multiple values, use one bind variable placeholder
per value. You cannot directly bind a Python list or dictionary to a single
bind variable. For example, to use two values in an IN clause your code should
be like:

.. code-block:: python

    items = ["Smith", "Taylor"]
    cursor.execute("""
        select employee_id, first_name, last_name
        from employees
        where last_name in (:1, :2)""",
        items)
    for row in cursor:
        print(row)

This gives the output::

    (159, 'Lindsey', 'Smith')
    (171, 'William', 'Smith')
    (176, 'Jonathon', 'Taylor')
    (180, 'Winston', 'Taylor')

If the query is executed multiple times with differing numbers of values, a
bind variable placeholder should be included in the SQL statement for each of
the maximum possible number of values. If the statement is executed with a
lesser number of data values, then bind ``None`` for missing values. For
example, if a query is used for up to five values, but only two values are used
in a particular execution, the code could be:

.. code-block:: python

    items = ["Smith", "Taylor", None, None, None]
    cursor.execute("""
        select employee_id, first_name, last_name
        from employees
        where last_name in (:1, :2, :3, :4, :5)""",
        items)
    for row in cursor:
        print(row)

This will produce the same output as the original example.

Reusing the same SQL statement like this for a variable number of values,
instead of constructing a unique statement per set of values, allows best reuse
of Oracle Database resources. Additionally, if a statement with a large number
of bind variable placeholders is executed many times with varying string
lengths for each execution, then consider using :func:`Cursor.setinputsizes()`
to reduce Oracle Database's SQL ":ref:`version count <sqlversioncount>`" for
the statement. For example, if the columns are VARCHAR2(25), then add this
before the :meth:`Cursor.execute()` call:

.. code-block:: python

    cursor.setinputsizes(25,25,25,25,25)

If other bind variables are required in the statement, adjust the bind variable
placeholder numbers appropriately:

.. code-block:: python

    binds = [120]                                   # employee id
    binds += ["Smith", "Taylor", None, None, None]  # IN list
    cursor.execute("""
        select employee_id, first_name, last_name
        from employees
        where employee_id > :1
        and last_name in (:2, :3, :4, :5, :6)""",
        binds)
    for row in cursor:
        print(row)

If a statement containing WHERE IN is not going to be re-executed, or the
number of values is only going to be known at runtime, then a SQL statement can
be dynamically built:

.. code-block:: python

    bind_values = ["Gates", "Marvin", "Fay"]
    bind_names = ",".join(":" + str(i + 1) for i in range(len(bind_values)))
    sql = f"select first_name, last_name from employees where last_name in ({bind_names})"
    cursor.execute(sql, bind_values)
    for row in cursor:
        print(row)

Binding a Large Number of Items in an IN List
---------------------------------------------

The number of items in an IN list is limited to 65535 in Oracle Database 23ai,
and to 1000 in earlier versions. If you exceed the limit, the database will
return an error like ``ORA-01795: maximum number of expressions in a list is
65535``.

To use more values in the IN clause list, you can add OR clauses like:

.. code-block:: python

    sql = """select . . .
             where key in (:0,:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,...)
                or key in (:50,:51,:52,:53,:54,:55,:56,:57,:58,:59,...)
                or key in (:100,:101,:102,:103,:104,:105,:106,:107,:108,:109,...)"""

A more general solution for a larger number of values is to construct a SQL
statement like::

    SELECT ... WHERE col IN ( <something that returns a list of values> )

The best way to do the '<something that returns a list of values>' depends on
how the data is initially represented and the number of items. For example you
might look at using a global temporary table.

One method for large IN lists is to use an Oracle Database collection with the
``TABLE()`` clause. For example, if the following type was created::

    SQL> CREATE OR REPLACE TYPE name_array AS TABLE OF VARCHAR2(25);
      2  /

then the application could do:

.. code-block:: python

    type_obj = connection.gettype("NAME_ARRAY")
    obj = type_obj.newobject()
    obj.extend(["Smith", "Taylor"])
    cursor.execute("""select employee_id, first_name, last_name
                      from employees
                      where last_name in (select * from table(:1))""",
                   [obj])
    for row in cursor:
        print(row)

When using this technique, it is important to review the database optimizer
plan to ensure it is efficient.

Since this ``TABLE()`` solution uses an object type, there is a performance
impact because of the extra :ref:`round-trips <roundtrips>` required to get the
type information. Unless you have a large number of binds you may prefer one of
the previous solutions. For efficiency, retain the return value of
:meth:`Connection.gettype()` for reuse where possible instead of making
repeated calls to it.

Some users employ the types SYS.ODCINUMBERLIST, SYS.ODCIVARCHAR2LIST, or
SYS.ODCIDATELIST instead of creating their own type, but this should be used
with the understanding that the database may remove these in a future version,
and that their size is 32K - 1.

Binding Column and Table Names
==============================

Table names cannot be bound in SQL queries.  You can concatenate text to build
up a SQL statement, but ensure that you use an Allow List or other means to
validate the data in order to avoid SQL Injection security issues:

.. code-block:: python

    table_allow_list = ['employees', 'departments']
    table_name = get_table_name() #  get the table name from user input
    if table_name.lower() not in table_allow_list:
        raise Exception('Invalid table name')
    sql = f'select * from {table_name}'

Binding column names can be done either by using a similar method, or by using
a CASE statement.  The example below demonstrates binding a column name in an
ORDER BY clause:

.. code-block:: python

    sql = """
        select *
        from departments
        order by
            case :bindvar
                when 'DEPARTMENT_ID' then
                    department_id
                else
                    manager_id
            end"""

    col_name = get_column_name() # Obtain a column name from the user
    cursor.execute(sql, [col_name])

Depending on the name provided by the user, the query results will be
ordered either by the column DEPARTMENT_ID or the column MANAGER_ID.
