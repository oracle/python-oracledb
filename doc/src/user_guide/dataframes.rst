.. _dataframeformat:

.. currentmodule:: oracledb

************************
Working with Data Frames
************************

Python-oracledb can query directly to a data frame format, and can also insert
data frames into Oracle Database. This can improve performance and reduce
memory requirements when your application uses Python data frame libraries such
as `Apache PyArrow <https://arrow.apache.org/docs/python/index.html>`__,
`Pandas <https://pandas.pydata.org>`__, `Polars <https://pola.rs/>`__, `NumPy
<https://numpy.org/>`__, `Dask <https://www.dask.org/>`__, `PyTorch
<https://pytorch.org/>`__, or writes files in `Apache Parquet
<https://parquet.apache.org/>`__ format.

Python-oracledb has a :ref:`DataFrame <oracledataframeobj>` object that exposes
an Apache Arrow ArrowArrayStream PyCapsule Interface. This enables zero-copy
data interchanges to the data frame objects of other libraries.

.. _dfquery:

Fetching Data Frames
====================

Data frames can be fetched by using a standard SQL query with :ref:`Connection
<connobj>` or :ref:`AsyncConnection <asyncconnobj>` methods.

Data Frame Queries
------------------

The python-oracledb methods for fetching rows into data frames are:

- :meth:`Connection.fetch_df_all()` fetches all rows from a query
- :meth:`Connection.fetch_df_batches()` implements an iterator for fetching
  batches of rows

These methods can also be called from :ref:`AsyncConnection
<asyncconnobj>`. The methods all return python-oracledb :ref:`DataFrame
<oracledataframeobj>` objects.

For example, to fetch all rows from a query and print some information about
the results:

.. code-block:: python

    sql = "select * from departments where department_id > :1"
    # Adjust arraysize to tune the query fetch performance
    odf = connection.fetch_df_all(statement=sql, parameters=[100], arraysize=100)

    print(odf.column_names())
    print(f"{odf.num_columns()} columns")
    print(f"{odf.num_rows()} rows")

With Oracle Database's standard DEPARTMENTS table, this would display::

    ['DEPARTMENT_ID', 'DEPARTMENT_NAME', 'MANAGER_ID', 'LOCATION_ID']
    4 columns
    17 rows

To fetch in batches, use an iterator:

.. code-block:: python

    import pyarrow

    sql = "select * from departments where department_id < :1"
    # Adjust "size" to tune the query fetch performance
    # Here it is small to show iteration
    for odf in connection.fetch_df_batches(statement=sql, parameters=[80], size=4):
        df = pyarrow.table(odf).to_pandas()
        print(df)

With Oracle Database's standard DEPARTMENTS table, this would display::

       DEPARTMENT_ID  DEPARTMENT_NAME  MANAGER_ID  LOCATION_ID
    0             10   Administration         200         1700
    1             20        Marketing         201         1800
    2             30       Purchasing         114         1700
    3             40  Human Resources         203         2400
       DEPARTMENT_ID   DEPARTMENT_NAME  MANAGER_ID  LOCATION_ID
    0             50          Shipping         121         1500
    1             60                IT         103         1400
    2             70  Public Relations         204         2700

Converting to other data frame formats is :ref:`shown later <convertingodf>` in
this chapter.

**Asynchronous Data Frame Queries**

With :ref:`asynchronous programming <asyncio>`, use the appropriate syntax. For
example, to fetch all rows at once:

.. code-block:: python

    connection = await oracledb.connect_async(...)
    odf = await connection.fetch_df_all(sql="select ...", parameters=..., arraysize=...)

Or to iterate:

.. code-block:: python

    connection = await oracledb.connect_async(...)
    async for odf in connection.fetch_df_batches(sql="select ...", parameters=..., size=...):
        do_something(odf)

.. _dftypemapping:

Data Frame Type Mapping
-----------------------

Default Data Frame Type Mapping
+++++++++++++++++++++++++++++++

Internally, python-oracledb's :ref:`DataFrame <oracledataframeobj>` support
makes use of `Apache nanoarrow <https://arrow.apache.org/nanoarrow/>`__
libraries to build data frames.

When querying, the following default data type mapping occurs from Oracle
Database types to the Arrow types used in python-oracledb DataFrame
objects. Querying any other data types from Oracle Database will result in
an exception. :ref:`Output type handlers <outputtypehandlers>` cannot be used
to map data types.

.. list-table-with-summary:: Mapping from Oracle Database to Apache Arrow data types
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 1 1
    :width: 100%
    :align: left
    :summary: The first column is the Oracle Database type. The second column is the Apache Arrow data type used in the python-oracledb DataFrame object.

    * - Oracle Database Type
      - Apache Arrow Data Type
    * - :attr:`DB_TYPE_BINARY_DOUBLE`
      - DOUBLE
    * - :attr:`DB_TYPE_BINARY_FLOAT`
      - FLOAT
    * - :attr:`DB_TYPE_BLOB`
      - LARGE_BINARY
    * - :attr:`DB_TYPE_BOOLEAN`
      - BOOLEAN
    * - :attr:`DB_TYPE_CHAR`
      - LARGE_STRING
    * - :attr:`DB_TYPE_CLOB`
      - LARGE_STRING
    * - :attr:`DB_TYPE_DATE`
      - TIMESTAMP
    * - :attr:`DB_TYPE_LONG`
      - LARGE_STRING
    * - :attr:`DB_TYPE_LONG_RAW`
      - LARGE_BINARY
    * - :attr:`DB_TYPE_NCHAR`
      - LARGE_STRING
    * - :attr:`DB_TYPE_NCLOB`
      - LARGE_STRING
    * - :attr:`DB_TYPE_NUMBER`
      - DECIMAL128, INT64, or DOUBLE
    * - :attr:`DB_TYPE_NVARCHAR`
      - LARGE_STRING
    * - :attr:`DB_TYPE_RAW`
      - LARGE_BINARY
    * - :attr:`DB_TYPE_TIMESTAMP`
      - TIMESTAMP
    * - :attr:`DB_TYPE_TIMESTAMP_LTZ`
      - TIMESTAMP
    * - :attr:`DB_TYPE_TIMESTAMP_TZ`
      - TIMESTAMP
    * - :attr:`DB_TYPE_VARCHAR`
      - LARGE_STRING
    * - :attr:`DB_TYPE_VECTOR`
      - List or struct with DOUBLE, FLOAT, INT8, or UINT8 values

**Numbers**

When converting Oracle Database NUMBERs:

- If the column has been created without a precision and scale, or you are
  querying an expression that results in a number without precision or scale,
  then the Apache Arrow data type will be DOUBLE.

- If :attr:`oracledb.defaults.fetch_decimals <Defaults.fetch_decimals>` is set
  to *True*, then the Apache Arrow data type is DECIMAL128.

- If the column has been created with a scale of *0*, and a precision value
  that is less than or equal to *18*, then the Apache Arrow data type is INT64.

- In all other cases, the Apache Arrow data type is DOUBLE.

**Strings**

When converting Oracle Database character types:

- If the number of records being fetched by :meth:`Connection.fetch_df_all()`,
  or fetched in each batch by :meth:`Connection.fetch_df_batches()`, can be
  handled by 32-bit offsets, you can use an :ref:`explicit mapping
  <explicitmapping>` to fetch as STRING instead of the default
  LARGE_STRING. This will save 4 bytes per record.

**Vectors**

When converting Oracle Database VECTORs:

- Dense vectors are fetched as lists.

- Sparse vectors are fetched as structs with fields ``num_dimensions``,
  ``indices`` and ``values`` similar to :ref:`SparseVector objects
  <sparsevectorsobj>`.

- Fixed and flexible dimensions are supported for dense VECTOR columns. For
  sparse VECTOR columns, the dimension of each vector must be the same.

- VECTOR columns with flexible formats are not supported. Each vector value
  must have the same storage format data type.

- Vector values are fetched as the following types:

  .. list-table-with-summary::
      :header-rows: 1
      :class: wy-table-responsive
      :widths: 1 1
      :align: left
      :summary: The first column is the Oracle Database VECTOR format. The second column is the resulting Apache Arrow data type in the list.

      * - Oracle Database VECTOR format
        - Apache Arrow data type
      * - FLOAT64
        - DOUBLE
      * - FLOAT32
        - FLOAT
      * - INT8
        - INT8
      * - BINARY
        - UINT8

See :ref:`dfvector` for more information.

**CLOB and NCLOB**

When converting Oracle Database CLOBs and NCLOBs:

- LOBs must be no more than 1 GB in length.

- If the number of records being fetched by :meth:`Connection.fetch_df_all()`,
  or fetched in each batch by :meth:`Connection.fetch_df_batches()`, can be
  handled by 32-bit offsets, you can use an :ref:`explicit mapping
  <explicitmapping>` to fetch CLOBs and NCLOBs as STRING instead of the default
  LARGE_STRING. This will save 4 bytes per record.

**BLOB**

When converting Oracle Database BLOBs:

- LOBs must be no more than 1 GB in length.

- If the number of records being fetched by :meth:`Connection.fetch_df_all()`,
  or fetched in each batch by :meth:`Connection.fetch_df_batches()`, can be
  handled by 32-bit offsets, you can use an :ref:`explicit mapping
  <explicitmapping>` to fetch BLOBs as BINARY instead of the default
  LARGE_BINARY. This will save 4 bytes per record.

**Dates and Timestamps**

When converting Oracle Database DATEs and TIMESTAMPs:

- Apache Arrow TIMESTAMPs will not have timezone data.

- For Oracle Database DATE columns, the Apache Arrow TIMESTAMP will have a time
  unit of "seconds".

- For Oracle Database TIMESTAMP types, the Apache Arrow TIMESTAMP time unit
  depends on the Oracle type's fractional precision as shown in the table
  below:

  .. list-table-with-summary::
      :header-rows: 1
      :class: wy-table-responsive
      :widths: 1 1
      :align: left
      :summary: The first column is the Oracle Database TIMESTAMP-type fractional second precision. The second column is the resulting Apache Arrow TIMESTAMP time unit.

      * - Oracle Database TIMESTAMP fractional second precision range
        - Apache Arrow TIMESTAMP time unit
      * - 0
        - seconds
      * - 1 - 3
        - milliseconds
      * - 4 - 6
        - microseconds
      * - 7 - 9
        - nanoseconds

.. _explicitmapping:

Explicit Data Frame Type Mapping
++++++++++++++++++++++++++++++++

You can explicitly set the data types and names that a :ref:`DataFrame
<oracledataframeobj>` will use for query results. This provides fine-grained
control over the physical data representation of the resulting Arrow arrays. It
allows you to specify a representation that is more efficient for its specific
use case. This can reduce memory consumption and improve processing speed.

The parameter ``requested_schema`` parameter to
:meth:`Connection.fetch_df_all()`, :meth:`Connection.fetch_df_batches()`,
:meth:`AsyncConnection.fetch_df_all()`, or
:meth:`AsyncConnection.fetch_df_batches()` should be an object implementing the
`Arrow PyCapsule schema interface
<https://arrow.apache.org/docs/python/generated/pyarrow.Schema.html>`__.

For example, the ``pyarrow.schema()`` factory function can be used to create a
new schema. This takes a list of field definitions as input. Each field can be
a tuple of ``(name, DataType)``:

.. code-block:: python

    import pyarrow

    # Default fetch

    odf = connection.fetch_df_all(
        "select 123 c1, 'Scott' c2 from dual"
    )
    tab = pyarrow.table(odf)
    print("Default Output:", tab)

    # Fetching with an explicit schema

    schema = pyarrow.schema([
        ("col_1", pyarrow.int16()),
        ("C2", pyarrow.string())
    ])

    odf = connection.fetch_df_all(
        "select 456 c1, 'King' c2 from dual",
        requested_schema=schema
    )
    tab = pyarrow.table(odf)
    print("\nNew Output:", tab)

The schema should have an entry for each queried column.

Running the example shows that the number column with the explicit schema was
fetched into the requested type INT16. Its name has also changed::

    Default Output: pyarrow.Table
    C1: double
    C2: string
    ----
    C1: [[123]]
    C2: [["Scott"]]

    New Output: pyarrow.Table
    col_1: int16
    C2: string
    ----
    col_1: [[456]]
    C2: [["King"]]

**Supported Explicit Type Mapping**

The following table shows the explicit type mappings that are supported. The
Oracle Database types in each row can be converted to any of the Apache Arrow
types in the same row. An error will occur if the database type or the data
cannot be represented in the requested schema type.

  .. list-table-with-summary::
      :header-rows: 1
      :class: wy-table-responsive
      :widths: 1 1
      :align: left
      :summary: The first column is the Oracle Database data types. The second column shows supported Apache Arrow data types.

      * - Oracle Database Types
        - Apache Arrow Data Types
      * - :attr:`DB_TYPE_NUMBER`
        - DECIMAL128(p, s)
          DOUBLE
          FLOAT
          INT8
          INT16
          INT32
          INT64
          UINT8
          UINT16
          UINT32
          UINT64
      * - :attr:`DB_TYPE_BLOB`
          :attr:`DB_TYPE_LONG_RAW`
          :attr:`DB_TYPE_RAW`
        - BINARY
          FIXED SIZE BINARY
          LARGE_BINARY
      * - :attr:`DB_TYPE_BOOLEAN`
        - BOOLEAN
      * - :attr:`DB_TYPE_DATE`
          :attr:`DB_TYPE_TIMESTAMP`
          :attr:`DB_TYPE_TIMESTAMP_LTZ`
          :attr:`DB_TYPE_TIMESTAMP_TZ`
        - DATE32
          DATE64
          TIMESTAMP
      * - :attr:`DB_TYPE_BINARY_DOUBLE`
          :attr:`DB_TYPE_BINARY_FLOAT`
        - DOUBLE
          FLOAT
      * - :attr:`DB_TYPE_CHAR`
          :attr:`DB_TYPE_CLOB`
          :attr:`DB_TYPE_LONG`
          :attr:`DB_TYPE_NCHAR`
          :attr:`DB_TYPE_NCLOB`
          :attr:`DB_TYPE_NVARCHAR`
          :attr:`DB_TYPE_VARCHAR`
        - LARGE_STRING
          STRING

.. _convertingodf:

Converting python-oracledb's DataFrame to Other Data Frames
-----------------------------------------------------------

To use data frames in your chosen analysis library, :ref:`DataFrame objects
<oracledataframeobj>` can be converted. Examples for some libraries are shown
in the following sections. Other libraries will have similar methods.

**Conversion Overview**

Guidelines for converting python-oracledb :ref:`DataFrame objects
<oracledataframeobj>` to data frames for other libraries are:

- To convert to a `PyArrow Table <https://arrow.apache.org/docs/python/
  generated/pyarrow.Table.html>`__, use `pyarrow.table()
  <https://arrow.apache.org/docs/python/generated/pyarrow.table.html
  #pyarrow.table>`__ which leverages the Arrow PyCapsule interface.

- To convert to a `Pandas DataFrame <https://pandas.pydata.org/docs/reference/
  api/pandas.DataFrame.html#pandas.DataFrame>`__, use
  `pyarrow.table().to_pandas() <https://arrow.apache.org/docs/python/generated/
  pyarrow.Table.html#pyarrow.Table.to_pandas>`__.

- If you want to use a library other than Pandas or PyArrow, use the library's
  ``from_arrow()`` method to convert a PyArrow Table to the applicable data
  frame, if your library supports this.  For example, with `Polars
  <https://pola.rs/>`__ use `polars.from_arrow() <https://docs.pola.rs/api/
  python/dev/reference/api/polars.from_arrow.html>`__.

You should test and benchmark to find the best option for your applications.

Creating PyArrow Tables
+++++++++++++++++++++++

An example that creates and uses a `PyArrow Table
<https://arrow.apache.org/docs/python/generated/pyarrow.Table.html>`__ is:

.. code-block:: python

    import pyarrow

    # Get a python-oracledb DataFrame
    # Adjust arraysize to tune the query fetch performance
    sql = "select id, name from mytable order by id"
    odf = connection.fetch_df_all(statement=sql, arraysize=100)

    # Create a PyArrow table
    pyarrow_table = pyarrow.table(odf)

    print("\nNumber of rows and columns:")
    (r, c) = pyarrow_table.shape
    print(f"{r} rows, {c} columns")

Internally `pyarrow.table()
<https://arrow.apache.org/docs/python/generated/
pyarrow.table.html#pyarrow.table>`__
leverages the Apache Arrow PyCapsule interface that python-oracledb
:ref:`DataFrame <oracledataframeobj>` objects expose.

See `samples/dataframe_pyarrow.py <https://github.com/oracle/python-oracledb/
blob/main/samples/dataframe_pyarrow.py>`__ for a runnable example.

.. _pandasdf:

Creating Pandas DataFrames
++++++++++++++++++++++++++

An example that creates and uses a `Pandas DataFrame <https://pandas.pydata.
org/docs/reference/api/pandas.DataFrame.html#pandas.DataFrame>`__ is:

.. code-block:: python

    import pandas
    import pyarrow

    # Get a python-oracledb DataFrame
    # Adjust arraysize to tune the query fetch performance
    sql = "select * from mytable where id = :1"
    myid = 12345  # the bind variable value
    odf = connection.fetch_df_all(statement=sql, parameters=[myid], arraysize=1000)

    # Get a Pandas DataFrame from the data.
    pdf = pyarrow.table(odf).to_pandas()

    # Perform various Pandas operations on the DataFrame
    print(pdf.T)        # transform
    print(pdf.tail(3))  # last three rows

The `to_pandas() <https://arrow.apache.org/docs/python/generated/pyarrow.Table.
html#pyarrow.Table.to_pandas>`__ method supports arguments like
``types_mapper=pandas.ArrowDtype`` and ``deduplicate_objects=False``, which may
be useful for some data sets.

See `samples/dataframe_pandas.py <https://github.com/oracle/python-oracledb/
blob/main/samples/dataframe_pandas.py>`__ for a runnable example.

Creating Polars DataFrames
++++++++++++++++++++++++++

An example that creates and uses a `Polars DataFrame
<https://docs.pola.rs/api/python/stable/reference/dataframe/index.html>`__ is:

.. code-block:: python

    import polars
    import pyarrow

    # Get a python-oracledb DataFrame
    # Adjust arraysize to tune the query fetch performance
    sql = "select id from mytable order by id"
    odf = connection.fetch_df_all(statement=sql, arraysize=100)

    # Convert to a Polars DataFrame
    pdf = polars.from_arrow(odf)

    # Perform various Polars operations on the DataFrame
    r, c = pdf.shape
    print(f"{r} rows, {c} columns")
    print(pdf.sum())

See `samples/dataframe_polars.py <https://github.com/oracle/python-oracledb/
blob/main/samples/dataframe_polars.py>`__ for a runnable example.

Writing Apache Parquet Files
++++++++++++++++++++++++++++

To write output in `Apache Parquet <https://parquet.apache.org/>`__ file
format, you can use data frames as an efficient intermediary. Use the
:meth:`Connection.fetch_df_batches()` iterator and convert to a `PyArrow Table
<https://arrow.apache.org/docs/python/generated/
pyarrow.table.html#pyarrow.table>`__ that can be written by the PyArrow
library.

.. code-block:: python

    import pyarrow
    import pyarrow.parquet as pq

    FILE_NAME = "sample.parquet"

    # Tune the fetch batch size for your query
    BATCH_SIZE = 10000

    sql = "select * from mytable"
    pqwriter = None
    for odf in connection.fetch_df_batches(statement=sql, size=BATCH_SIZE):

        # Get a PyArrow table from the query results
        pyarrow_table = pyarrow.table(odf)

        if not pqwriter:
            pqwriter = pq.ParquetWriter(FILE_NAME, pyarrow_table.schema)

        pqwriter.write_table(pyarrow_table)

    pqwriter.close()

See `samples/dataframe_parquet_write.py <https://github.com/oracle/
python-oracledb/blob/main/samples/dataframe_parquet_write.py>`__
for a runnable example.

The DLPack Protocol
+++++++++++++++++++

The DataFrame format facilitates working with query results as
tensors. Conversion can be done using the standard `DLPack Protocol
<https://arrow.apache.org/docs/python/dlpack.html>`__ implemented by PyArrow.

**Using NumPy Arrays**

For example, to convert to `NumPy <https://numpy.org/>`__ ``ndarray`` format:

.. code-block:: python

    import numpy
    import pyarrow

    SQL = "select id from mytable order by id"

    # Get a python-oracledb DataFrame
    # Adjust arraysize to tune the query fetch performance
    odf = connection.fetch_df_all(statement=SQL, arraysize=100)

    # Convert to an ndarray via the Python DLPack specification
    pyarrow_array = pyarrow.array(odf.get_column_by_name("ID"))
    np = numpy.from_dlpack(pyarrow_array)

    # Perform various numpy operations on the ndarray

    print(numpy.sum(np))
    print(numpy.log10(np))

See `samples/dataframe_numpy.py <https://github.com/oracle/python-oracledb/
blob/main/samples/dataframe_numpy.py>`__ for a runnable example.

Using Torch
+++++++++++

An example of working with data as a `Torch tensor
<https://pytorch.org/docs/stable/tensors.html>`__ is:

.. code-block:: python

    import pyarrow
    import torch

    SQL = "select id from mytable order by id"

    # Get a python-oracledb DataFrame
    # Adjust arraysize to tune the query fetch performance
    odf = connection.fetch_df_all(statement=SQL, arraysize=100)

    # Convert to a Torch tensor via the Python DLPack specification
    pyarrow_array = pyarrow.array(odf.get_column_by_name("ID"))
    tt = torch.from_dlpack(pyarrow_array)

    # Perform various Torch operations on the tensor

    print(torch.sum(tt))
    print(torch.log10(tt))

See `samples/dataframe_torch.py <https://github.com/oracle/python-oracledb/
blob/main/samples/dataframe_torch.py>`__ for a runnable example.

.. _dfvector:

Fetching VECTOR columns to Data Frames
--------------------------------------

Columns of the `VECTOR <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-746EAA47-9ADA-4A77-82BB-64E8EF5309BE>`__ data type can be fetched with
the methods :meth:`Connection.fetch_df_all()` and
:meth:`Connection.fetch_df_batches()`. VECTOR columns can have flexible
dimensions, but flexible storage formats are not supported: each vector value
must have the same format data type. Vectors can be dense or sparse.

See :ref:`dftypemapping` for the type mapping for VECTORs.

**Dense Vectors**

By default, Oracle Database vectors are "dense".  These are fetched in
python-oracledb as Arrow lists. For example, if the table::

    create table myvec (v64 vector(3, float64));

contains these two vectors::

    [4.1, 5.2, 6.3]
    [7.1, 8.2, 9.3]

then the code:

.. code-block:: python

    odf = connection.fetch_df_all("select v64 from myvec")
    pyarrow_table = pyarrow.table(odf)

will result in a PyArrow table containing lists of doubles. The table can be
converted to a data frame of your chosen library.

For example, to convert the PyArrow table to Pandas:

.. code-block:: python

    pdf = pyarrow_table.to_pandas()

Or you can convert the python-oracledb :ref:`DataFrame <oracledataframeobj>`
directly if the library supports it. For example, to fetch to Pandas the syntax
is the same as shown in :ref:`Creating Pandas DataFrames <pandasdf>`:

.. code-block:: python

    odf = connection.fetch_df_all("select v64 from myvec")
    pdf = pyarrow.table(odf).to_pandas()
    print(pdf)

The output will be::

                   V64
    0  [4.1, 5.2, 6.3]
    1  [7.1, 8.2, 9.3]

**Sparse Vectors**

Sparse vectors (where many of the values are 0) are fetched as structs with
fields ``num_dimensions``, ``indices``, and ``values`` similar to
:ref:`SparseVector objects <sparsevectorsobj>` which are discussed in a
non-data frame context in :ref:`sparsevectors`.

If the table::

    create table myvec (v64 vector(3, float64, sparse));

contains these two vectors::

    [3, [1,2], [4.1, 5.2]]
    [3, [0], [9.3]]

then the code to fetch as data frames:

.. code-block:: python

    import pyarrow

    odf = connection.fetch_df_all("select v64 from myvec")
    pdf = pyarrow.table(odf).to_pandas()

    print(pdf)

    print("First row:")

    num_dimensions = pdf.iloc[0].V64['num_dimensions']
    print(f"num_dimensions={num_dimensions}")

    indices = pdf.iloc[0].V64['indices']
    print(f"indices={indices}")

    values = pdf.iloc[0].V64['values']
    print(f"values={values}")

will display::

                                                     V64
    0  {'num_dimensions': 3, 'indices': [1, 2], 'valu...
    1  {'num_dimensions': 3, 'indices': [0], 'values'...

    First row:
    num_dimensions=3
    indices=[1 2]
    values=[4.1 5.2]

You can convert each struct as needed.  One way to convert into `Pandas
dataframes with sparse values
<https://pandas.pydata.org/docs/user_guide/sparse.html>`__ is via a `SciPy
coordinate format matrix <https://docs.scipy.org/doc/scipy/reference/generated/
scipy.sparse.coo_array.html#scipy.sparse.coo_array>`__. The Pandas method
`from_spmatrix() <https://pandas.pydata.org/docs/reference/api/
pandas.DataFrame.sparse.from_spmatrix.html>`__ can then be used to create the
final sparse dataframe:

.. code-block:: python

    import numpy
    import pandas
    import pyarrow
    import scipy

    def convert_to_sparse_array(val):
        dimensions = val["num_dimensions"]
        col_indices = val["indices"]
        row_indices = numpy.zeros(len(col_indices))
        values = val["values"]
        sparse_matrix = scipy.sparse.coo_matrix(
            (values, (col_indices, row_indices)), shape=(dimensions, 1))
        return pandas.arrays.SparseArray.from_spmatrix(sparse_matrix)

    odf = connection.fetch_df_all("select v64 from myvec")
    pdf = pyarrow.table(odf).to_pandas()

    pdf["SPARSE_ARRAY_V64"] = pdf["V64"].apply(convert_to_sparse_array)

    print(pdf.SPARSE_ARRAY_V64)

The code will print::

    0    [0.0, 4.1, 5.2]
    Fill: 0.0
    IntIndex
    Indices: ar...
    1    [9.3, 0.0, 0.0]
    Fill: 0.0
    IntIndex
    Indices: ar...
    Name: SPARSE_ARRAY_V64, dtype: object

.. _dfinsert:

Inserting Data Frames
=====================

Python-oracledb :ref:`DataFrame <oracledataframeobj>` instances, or third-party
DataFrame instances that support the Apache Arrow PyCapsule Interface, can be
inserted into Oracle Database by passing them directly to
:meth:`Cursor.executemany()` or :meth:`AsyncCursor.executemany()`.  They can
also be passed to :meth:`Connection.direct_path_load()` and
:meth:`AsyncConnection.direct_path_load()`.

Inserting Data Frames with executemany()
----------------------------------------

For example, with the table::

    create table t (col1 number, col2 number);

The following code will insert a Pandas DataFrame:

.. code-block:: python

    import pandas

    d = {'A': [1.2, 2.4, 8.9], 'B': [3.333, 4.9, 0.0]}
    pdf = pandas.DataFrame(data=d)

    cursor.executemany("insert into t (col1, col2) values (:1, :2)", pdf)

Inserting to a dense VECTOR column::

    create table SampleVectorTab (v64 vector(3, float64));

Can be done like:

.. code-block:: python

    import pandas

    d = {"v": [[3.3, 1.32, 5.0], [2.2, 2.32, 2.0]]}
    pdf = pandas.DataFrame(data=d)

    cursor.executemany("insert into SampleVectorTab (v64) values (:1)", pdf)

See `dataframe_insert.py <https://github.com/oracle/python-oracledb/tree/main/
samples/dataframe_insert.py>`__ for a runnable example.

For general information about fast data ingestion, and discussion of
:meth:`Cursor.executemany()` and :meth:`AsyncCursor.executemany()` options, see
:ref:`batchstmnt`.

.. _dfppl:

Inserting Data Frames with Direct Path Loads
--------------------------------------------

Very large :ref:`DataFrame <oracledataframeobj>` objects can be efficiently
inserted using Oracle Database Direct Path Loading by passing them to
:meth:`Connection.direct_path_load()`. You can also pass third-party DataFrame
instances that support the Apache Arrow PyCapsule Interface.

See :ref:`directpathloads` for general information about Direct Path Loads.

For example, if the user "HR" has the table::

    create table mytab (
                   id   number(9),
                   name varchar2(100));

The following code will insert a Pandas DataFrame:

.. code-block:: python

    import pandas

    d = [
        (1, "Abigail"),
        (2, "Anna"),
        (3, "Janey"),
        (4, "Jessica"),
    ]
    pdf = pandas.DataFrame(data=d)

    connection.direct_path_load(
        schema_name="hr",
        table_name="mytab",
        column_names=["id", "name"],
        data=pdf
    )

Explicit Conversion to DataFrame or ArrowArray
==============================================

Data frames that support the Apache Arrow PyCapsule Interface can be explicitly
converted to :ref:`DataFrame <oracledataframeobj>` and :ref:`ArrowArray
<oraclearrowarrayobj>` objects by calling :func:`oracledb.from_arrow()`.  The
resulting object depends on what interface is supported by the source object.

For example:

.. code-block:: python

    import pandas

    d = {'A': [1.2, 2.4, 8.9], 'B': [3.333, 4.9, 0.0]}
    pdf = pandas.DataFrame(data=d)
    print(type(pdf))

    odf = oracledb.from_arrow(pdf)
    print(type(odf))

will print::

    <class 'pandas.core.frame.DataFrame'>
    <class 'oracledb.dataframe.DataFrame'>
