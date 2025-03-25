.. _lobdata:

***************************************
Using CLOB, BLOB, NCLOB, and BFILE Data
***************************************

Oracle Database uses :ref:`LOB objects <lobobj>` to store large data such as
text, images, videos, and other multimedia formats.  The maximum size of a LOB
(large object) is limited to the size of the tablespace storing it.

There are `four types of LOBs <https://www.oracle.com/pls/topic/lookup?ctx=
dblatest&id=GUID-0A692C1B-1C95-4121-8F95-25BE465B87F6>`__:

    * CLOB - Character Large Object, used for storing strings in the database
      character set format. python-oracledb uses the type
      :attr:`oracledb.DB_TYPE_CLOB`.
    * BLOB - Binary Large Object, used for storing binary data. python-oracledb
      uses the type :attr:`oracledb.DB_TYPE_BLOB`.
    * NCLOB - National Character Large Object, used for storing strings in the
      national character set format. python-oracledb uses the type
      :attr:`oracledb.DB_TYPE_NCLOB`.
    * BFILE - External Binary File, used for referencing a file stored on the
      host operating system outside of the database. python-oracledb uses the
      type :attr:`oracledb.DB_TYPE_BFILE`.

LOBs can be permanent or temporary. They can be inserted into, and fetched
from, Oracle Database in chunks, as mecessary.

LOBs up to 1 GB in length can be also be handled directly as strings or bytes
in python-oracledb.  This makes LOBs easy to work with, and has significant
performance benefits over streaming.  However, it requires the entire LOB
data to be present in Python memory, which may not be possible.

See `GitHub <https://github.com/oracle/python-oracledb/tree/main/samples>`__
for LOB examples.

Simple Insertion of LOBs
========================

Consider a table with CLOB and BLOB columns:

.. code-block:: sql

    CREATE TABLE lob_tbl (
        id NUMBER,
        c CLOB,
        b BLOB
    );

With python-oracledb, LOB data can be inserted in the table by binding strings
or bytes as needed:

.. code-block:: python

    with open('example.txt', 'r') as f:
        text_data = f.read()

    with open('image.png', 'rb') as f:
        img_data = f.read()

    cursor.execute("""
            insert into lob_tbl (id, c, b)
            values (:lobid, :clobdata, :blobdata)""",
            lobid=10, clobdata=text_data, blobdata=img_data)

Note that with this approach, LOB data is limited to 1 GB in size.

.. _directlobs:

Fetching LOBs as Strings and Bytes
==================================

CLOBs and BLOBs smaller than 1 GB can queried from the database directly as
strings and bytes.  This can be much faster than streaming a :ref:`LOB Object
<lobobj>`.  Support is enabled by setting the :ref:`Defaults Object
<defaults>`.

.. code-block:: python

    import oracledb

    # returns strings or bytes instead of a locator
    oracledb.defaults.fetch_lobs = False

    . . .

    id_val = 1
    text_data = "The quick brown fox jumps over the lazy dog"
    binary_data = b"Some binary data"
    cursor.execute("insert into lob_tbl (id, c, b) values (:1, :2, :3)",
                   [id_val, text_data, binary_data])

    cursor.execute("select c, b from lob_tbl where id = :1", [id_val])
    clob_data, blob_data = cursor.fetchone()
    print("CLOB length:", len(clob_data))
    print("CLOB data:", clob_data)
    print("BLOB length:", len(blob_data))
    print("BLOB data:", blob_data)

This displays::

    CLOB length: 43
    CLOB data: The quick brown fox jumps over the lazy dog
    BLOB length: 16
    BLOB data: b'Some binary data'

An older alternative to using ``oracledb.defaults.fetch_lobs`` is to use a type
handler:

.. code-block:: python

    def output_type_handler(cursor, metadata):
        if metadata.type_code is oracledb.DB_TYPE_CLOB:
            return cursor.var(oracledb.DB_TYPE_LONG, arraysize=cursor.arraysize)
        if metadata.type_code is oracledb.DB_TYPE_BLOB:
            return cursor.var(oracledb.DB_TYPE_LONG_RAW, arraysize=cursor.arraysize)
        if metadata.type_code is oracledb.DB_TYPE_NCLOB:
            return cursor.var(oracledb.DB_TYPE_LONG_NVARCHAR, arraysize=cursor.arraysize)

    connection.outputtypehandler = output_type_handler

Streaming LOBs (Read)
=====================

Without setting ``oracledb.defaults.fetch_lobs`` to False, or without using an
output type handler, the CLOB and BLOB values are fetched as :ref:`LOB
objects<lobobj>`. The size of the LOB object can be obtained by calling
:meth:`LOB.size()` and the data can be read by calling :meth:`LOB.read()`:

.. code-block:: python

    id_val = 1
    text_data = "The quick brown fox jumps over the lazy dog"
    binary_data = b"Some binary data"
    cursor.execute("insert into lob_tbl (id, c, b) values (:1, :2, :3)",
                   [id_val, text_data, binary_data])

    cursor.execute("select b, c from lob_tbl where id = :1", [id_val])
    b, c = cursor.fetchone()
    print("CLOB length:", c.size())
    print("CLOB data:", c.read())
    print("BLOB length:", b.size())
    print("BLOB data:", b.read())

This approach produces the same results as the previous example but it will
perform more slowly because it requires more :ref:`round-trips <roundtrips>` to
Oracle Database and has higher overhead. It is needed, however, if the LOB data
cannot be fetched as one block of data from the server.

To stream the BLOB column, the :meth:`LOB.read()` method can be called
repeatedly until all of the data has been read, as shown below:

.. code-block:: python

    cursor.execute("select b from lob_tbl where id = :1", [10])
    blob, = cursor.fetchone()
    offset = 1
    num_bytes_in_chunk = 65536
    with open("image.png", "wb") as f:
        while True:
            data = blob.read(offset, num_bytes_in_chunk)
            if data:
                f.write(data)
            if len(data) < num_bytes_in_chunk:
                break
            offset += len(data)


Streaming LOBs (Write)
======================

If a row containing a LOB is being inserted or updated, and the quantity of
data that is to be inserted or updated cannot fit in a single block of data,
the data can be streamed using the method :meth:`LOB.write()` instead as shown
in the following code:

.. code-block:: python

    id_val = 9
    lob_var = cursor.var(oracledb.DB_TYPE_BLOB)
    cursor.execute("""
            insert into lob_tbl (id, b)
            values (:1, empty_blob())
            returning b into :2""", [id_val, lob_var])
    blob, = lobVar.getvalue()
    offset = 1
    num_bytes_in_chunk = 65536
    with open("image.png", "rb") as f:
        while True:
            data = f.read(num_bytes_in_chunk)
            if data:
                blob.write(data, offset)
            if len(data) < num_bytes_in_chunk:
                break
            offset += len(data)
    connection.commit()

Temporary LOBs
==============

All of the examples shown thus far have made use of permanent LOBs. These are
LOBs that are stored in the database. Oracle also supports temporary LOBs that
are not stored in the database but can be used to pass large quantities of
data. These LOBs use space in the temporary tablespace until all variables
referencing them go out of scope or the connection in which they are created is
explicitly closed.

When calling PL/SQL procedures with data that exceeds 32,767 bytes in length,
python-oracledb automatically creates a temporary LOB internally and passes
that value through to the procedure. If the data that is to be passed to the
procedure exceeds that which can fit in a single block of data, however, you
can use the method :meth:`Connection.createlob()` to create a temporary LOB.
This LOB can then be read and written just like in the examples shown above for
persistent LOBs.

.. _bfiles:

Using BFILEs
============

`BFILEs <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-D4642C92
-F343-4700-9F1F-486F82249FB8>`__ are objects stored in a directory in the
Oracle Database server file system, not in the database. The database column of
type BFILE stores a reference to this external binary file. Each BFILE column
can reference a single external file. BFILEs are read-only data types and
hence you cannot modify the file from within your application.

Before using the BFILE data type, you must:

- Create a `DIRECTORY <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-
  F7440C27-C7F0-4874-8C3C-F3BC1534CBE0>`__ object which is an alias for the
  full path to the directory containing BFILE data in the database server file
  system. For example, you can create a DIRECTORY object by using:

  .. code-block:: sql

        create or replace directory my_bfile_dir as '/demo/bfiles'

  In the above example, "my_bfile_dir" is the directory alias.
  "/demo/bfiles" is the physical directory in the database server file
  system that contains the files. It is a string containing the full path name
  of the directory and follows the operating system rules.

  To allow non-privileged users to access this directory, you can grant access
  using:

  .. code-block:: sql

    grant read on directory my_bfile_dir to hr;

  Ensure that the Oracle Server processes have read access to the directory.

- Store the physical binary file in the directory in the database server file
  system. For example, the binary file "my_bfile.txt" is stored in the
  directory "/demo/bfiles".

Consider the file, "/demo/bfiles/my_bfile.txt", exists on the server and
contains the text, "This is my BFILE data". You can access the "my_bfile.txt"
file as detailed below.

The following table will be used in the subsequent examples.

.. code-block:: sql

    create table bfile_tbl(
        id number,
        bfile_data bfile
    );

**Inserting BFILEs**

You must use the `BFILENAME <https://www.oracle.com/pls/topic/lookup?ctx=
dblatest&id=GUID-1F767077-7C26-4962-9833-1433F1749621>`__ function in an INSERT
statement to associate a file and a BFILE column. The ``BFILENAME`` function
takes two arguments, the directory alias and the file name. To insert a BFILE
reference, for example:

.. code-block:: python

    cursor.execute("""
        insert into bfile_tbl (id, bfile_data) values
        (:id, bfilename(:bfiledir, :bfilename))""",
        id=102, bfiledir="my_bfile_dir", bfilename="my_bfile.txt")

    connection.commit()

This inserts a reference to the file "my_bfile.txt" located in the directory
referenced by the alias "my_bfile_dir" into the bfile_tbl table.

**Fetching BFILEs**

To query the bfile_tbl table and fetch the BFILE LOB locator, you can use
the `BFILENAME <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-
1F767077-7C26-4962-9833-1433F1749621>`__ function as shown below:

.. code-block:: python

    cursor.execute("select bfilename(:bfiledir, :bfilename) from bfile_tbl where id = :id",
        id=102, bfiledir="my_bfile_dir", bfilename="my_bfile.txt")
    bfile, = cursor.fetchone()
    print(bfile.read())

This will display::

    This is my BFILE data

This fetched LOB can use :meth:`LOB.fileexists()` to check if the file
referenced by the BFILE type LOB exists.

You can get the directory alias and file name of this fetched LOB by using
:meth:`LOB.getfilename()`. Also, you can set the directory alias and file name
for this fetched LOB by using :meth:`LOB.setfilename()`.
