.. _dataframeformat:

************************
Working with Data Frames
************************

Python-oracledb queries can fetch directly to data frames. This can improve
performance and reduce memory requirements when your application uses Python
data frame libraries such as `Apache PyArrow
<https://arrow.apache.org/docs/python/index.html>`__, `Pandas
<https://pandas.pydata.org>`__, `Polars <https://pola.rs/>`__, `NumPy
<https://numpy.org/>`__, `Dask <https://www.dask.org/>`__, `PyTorch
<https://pytorch.org/>`__, or writes files in `Apache Parquet
<https://parquet.apache.org/>`__ format. The :ref:`OracleDataFrame
<oracledataframeobj>` objects fetched expose an Apache Arrow PyCapsule
Interface which, in some cases, allow zero-copy data interchanges to the data
frame objects of other libraries.

.. note::

    The data frame support in python-oracledb 3.3 is a pre-release and may
    change in a future version.

**Fetching Data Frames**

The method :meth:`Connection.fetch_df_all()` fetches all rows from a query.
The method :meth:`Connection.fetch_df_batches()` implements an iterator for
fetching batches of rows. The methods return :ref:`OracleDataFrame
<oracledataframeobj>` objects.

For example, to fetch all rows from a query and print some information about
the results:

.. code-block:: python

    sql = "select * from departments"
    # Adjust arraysize to tune the query fetch performance
    odf = connection.fetch_df_all(statement=sql, arraysize=100)

    print(odf.column_names())
    print(f"{odf.num_columns()} columns")
    print(f"{odf.num_rows()} rows")

With Oracle Database's standard DEPARTMENTS table, this would display::

    ['DEPARTMENT_ID', 'DEPARTMENT_NAME', 'MANAGER_ID', 'LOCATION_ID']
    4 columns
    27 rows

To fetch in batches, use an iterator:

.. code-block:: python

    import pyarrow

    sql = "select * from departments where department_id < 80"
    # Adjust "size" to tune the query fetch performance
    # Here it is small to show iteration
    for odf in connection.fetch_df_batches(statement=sql, size=4):
        df = pyarrow.Table.from_arrays(
            odf.column_arrays(), names=odf.column_names()
        ).to_pandas()
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

**Inserting OracleDataFrames into Oracle Database**

To insert data currently in :ref:`OracleDataFrame <oracledataframeobj>` format
into Oracle Database requires it to be converted.  For example, you could
convert it into a Pandas DataFrame for insert with the Pandas method
``to_sql()``. Or convert into a Python list via the PyArrow
``Table.to_pylist()`` method and then use standard python-oracledb
functionality to execute a SQL INSERT statement.

.. _dftypemapping:

Data Frame Type Mapping
-----------------------

Internally, python-oracledb's :ref:`OracleDataFrame <oracledataframeobj>`
support makes use of `Apache nanoarrow <https://arrow.apache.org/nanoarrow/>`__
libraries to build data frames.

The following data type mapping occurs from Oracle Database types to the Arrow
types used in OracleDataFrame objects. Querying any other data types from
Oracle Database will result in an exception. :ref:`Output type handlers
<outputtypehandlers>` cannot be used to map data types.

.. list-table-with-summary:: Mapping from Oracle Database to Arrow data types
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 1 1
    :width: 100%
    :align: left
    :summary: The first column is the Oracle Database type. The second column is the Arrow data type used in the OracleDataFrame object.

    * - Oracle Database Type
      - Arrow Data Type
    * - DB_TYPE_BINARY_DOUBLE
      - DOUBLE
    * - DB_TYPE_BINARY_FLOAT
      - FLOAT
    * - DB_TYPE_BLOB
      - LARGE_BINARY
    * - DB_TYPE_BOOLEAN
      - BOOLEAN
    * - DB_TYPE_CHAR
      - STRING
    * - DB_TYPE_CLOB
      - LARGE_STRING
    * - DB_TYPE_DATE
      - TIMESTAMP
    * - DB_TYPE_LONG
      - LARGE_STRING
    * - DB_TYPE_LONG_RAW
      - LARGE_BINARY
    * - DB_TYPE_NCHAR
      - STRING
    * - DB_TYPE_NCLOB
      - LARGE_STRING
    * - DB_TYPE_NUMBER
      - DECIMAL128, INT64, or DOUBLE
    * - DB_TYPE_NVARCHAR
      - STRING
    * - DB_TYPE_RAW
      - BINARY
    * - DB_TYPE_TIMESTAMP
      - TIMESTAMP
    * - DB_TYPE_TIMESTAMP_LTZ
      - TIMESTAMP
    * - DB_TYPE_TIMESTAMP_TZ
      - TIMESTAMP
    * - DB_TYPE_VARCHAR
      - STRING
    * - DB_TYPE_VECTOR
      - List or struct with DOUBLE, FLOAT, INT8, or UINT8 values

**Numbers**

When converting Oracle Database NUMBERs:

- If the column has been created without a precision and scale, then the Arrow
  data type will be DOUBLE.

- If :attr:`defaults.fetch_decimals` is set to *True*, then the Arrow data
  type is DECIMAL128.

- If the column has been created with a scale of *0*, and a precision value
  that is less than or equal to *18*, then the Arrow data type is INT64.

- In all other cases, the Arrow data type is DOUBLE.

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
      :summary: The first column is the Oracle Database VECTOR format. The second column is the resulting Arrow data type in the list.

      * - Oracle Database VECTOR format
        - Arrow data type
      * - FLOAT64
        - DOUBLE
      * - FLOAT32
        - FLOAT
      * - INT8
        - INT8
      * - BINARY
        - UINT8

See :ref:`dfvector` for more information.

**LOBs**

When converting Oracle Database CLOBs and BLOBs:

- The LOBs must be no more than 1 GB in length.

**Dates and Timestamps**

When converting Oracle Database DATEs and TIMESTAMPs:

- Arrow TIMESTAMPs will not have timezone data.

- For Oracle Database DATE columns, the Arrow TIMESTAMP will have a time unit
  of "seconds".

- For Oracle Database TIMESTAMP types, the Arrow TIMESTAMP time unit depends on
  the Oracle type's fractional precision as shown in the table below:

  .. list-table-with-summary::
      :header-rows: 1
      :class: wy-table-responsive
      :widths: 1 1
      :align: left
      :summary: The first column is the Oracle Database TIMESTAMP-type fractional second precision. The second column is the resulting Arrow TIMESTAMP time unit.

      * - Oracle Database TIMESTAMP fractional second precision range
        - Arrow TIMESTAMP time unit
      * - 0
        - seconds
      * - 1 - 3
        - milliseconds
      * - 4 - 6
        - microseconds
      * - 7 - 9
        - nanoseconds

.. _convertingodf:

Converting OracleDataFrame to Other Data Frames
-----------------------------------------------

To use data frames in your chosen analysis library, :ref:`OracleDataFrame
objects <oracledataframeobj>` can be converted. Examples for some libraries are
shown in the following sections. Other libraries will have similar methods.

**Conversion Overview**

The guidelines for converting :ref:`OracleDataFrame objects
<oracledataframeobj>` to data frames for other libraries are:

- To convert to a `PyArrow Table <https://arrow.apache.org/docs/python/
  generated/pyarrow.Table.html>`__, use `pyarrow.Table.from_arrays()
  <https://arrow.apache.org/docs/python/generated/pyarrow.Table.html#pyarrow.
  Table.from_arrays>`__ which leverages the Arrow PyCapsule interface.

- To convert to a `Pandas DataFrame <https://pandas.pydata.org/docs/reference/
  api/pandas.DataFrame.html#pandas.DataFrame>`__, use
  `pyarrow.Table.to_pandas() <https://arrow.apache.org/docs/python/generated/
  pyarrow.Table.html#pyarrow.Table.to_pandas>`__.

- If you want to use a library other than Pandas or PyArrow, use the library's
  ``from_arrow()`` method to convert a PyArrow Table to the applicable data
  frame, if your library supports this.  For example, with `Polars
  <https://pola.rs/>`__ use `polars.from_arrow() <https://docs.pola.rs/api/
  python/dev/reference/api/polars.from_arrow.html>`__.

- If your library does not support ``from_arrow()``, then use
  ``from_dataframe()`` if the library supports it. This can be slower,
  depending on the implementation.

Overall, the general recommendation is to use Apache Arrow as much as possible
but if there are no options, then use ``from_dataframe()``.  You should test
and benchmark to find the best option for your applications.

Creating PyArrow Tables
+++++++++++++++++++++++

An example that creates and uses a `PyArrow Table
<https://arrow.apache.org/docs/python/generated/pyarrow.Table.html>`__ is:

.. code-block:: python

    import pyarrow

    # Get an OracleDataFrame
    # Adjust arraysize to tune the query fetch performance
    sql = "select id, name from SampleQueryTab order by id"
    odf = connection.fetch_df_all(statement=sql, arraysize=100)

    # Create a PyArrow table
    pyarrow_table = pyarrow.Table.from_arrays(
        arrays=odf.column_arrays(), names=odf.column_names()
    )

    print("\nNumber of rows and columns:")
    (r, c) = pyarrow_table.shape
    print(f"{r} rows, {c} columns")

This makes use of :meth:`OracleDataFrame.column_arrays()` which returns a list
of :ref:`OracleArrowArray Objects <oraclearrowarrayobj>`.

Internally `pyarrow.Table.from_arrays() <https://arrow.apache.org/docs/python/
generated/pyarrow.Table.html#pyarrow.Table.from_arrays>`__ leverages the Apache
Arrow PyCapsule interface that :ref:`OracleDataFrame <oracledataframeobj>`
exposes.

See `samples/dataframe_pyarrow.py <https://github.com/oracle/python-oracledb/
blob/main/samples/dataframe_pyarrow.py>`__ for a runnable example.

Creating Pandas DataFrames
++++++++++++++++++++++++++

An example that creates and uses a `Pandas DataFrame <https://pandas.pydata.
org/docs/reference/api/pandas.DataFrame.html#pandas.DataFrame>`__ is:

.. code-block:: python

    import pandas
    import pyarrow

    # Get an OracleDataFrame
    # Adjust arraysize to tune the query fetch performance
    sql = "select * from mytable where id = :1"
    myid = 12345  # the bind variable value
    odf = connection.fetch_df_all(statement=sql, parameters=[myid], arraysize=1000)

    # Get a Pandas DataFrame from the data.
    df = pyarrow.Table.from_arrays(
        odf.column_arrays(), names=odf.column_names()
    ).to_pandas()

    # Perform various Pandas operations on the DataFrame
    print(df.T)        # transform
    print(df.tail(3))  # last three rows

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

    # Get an OracleDataFrame
    # Adjust arraysize to tune the query fetch performance
    sql = "select id from SampleQueryTab order by id"
    odf = connection.fetch_df_all(statement=sql, arraysize=100)

    # Convert to a Polars DataFrame
    pyarrow_table = pyarrow.Table.from_arrays(
        odf.column_arrays(), names=odf.column_names()
    )
    df = polars.from_arrow(pyarrow_table)

    # Perform various Polars operations on the DataFrame
    r, c = df.shape
    print(f"{r} rows, {c} columns")
    print(p.sum())

See `samples/dataframe_polars.py <https://github.com/oracle/python-oracledb/
blob/main/samples/dataframe_polars.py>`__ for a runnable example.

Writing Apache Parquet Files
++++++++++++++++++++++++++++

To write output in `Apache Parquet <https://parquet.apache.org/>`__ file
format, you can use data frames as an efficient intermediary. Use the
:meth:`Connection.fetch_df_batches()` iterator and convert to a `PyArrow Table
<https://arrow.apache.org/docs/python/generated/pyarrow.Table.html>`__ that can
be written by the PyArrow library.

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
        pyarrow_table = pyarrow.Table.from_arrays(
            arrays=odf.column_arrays(), names=odf.column_names()
        )

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

    SQL = "select id from SampleQueryTab order by id"

    # Get an OracleDataFrame
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

    SQL = "select id from SampleQueryTab order by id"

    # Get an OracleDataFrame
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

Using VECTOR data with Data Frames
----------------------------------

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
    pyarrow_table = pyarrow.Table.from_arrays(
        odf.column_arrays(), names=odf.column_names()
    )

will result in a PyArrow table containing lists of doubles. The table can be
converted to a data frame of your chosen library using functionality described
earlier in this chapter.  For example, to convert to Pandas:

.. code-block:: python

    pdf = pyarrow_table.to_pandas()
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
    pdf = pyarrow.Table.from_arrays(
        odf.column_arrays(), names=odf.column_names()
    ).to_pandas()

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
    pdf = pyarrow.Table.from_arrays(
        odf.column_arrays(), odf.column_names()
    ).to_pandas()

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
