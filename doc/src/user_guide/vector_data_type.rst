.. _vectors:

.. currentmodule:: oracledb

*****************
Using VECTOR Data
*****************

Oracle AI Database 26ai introduced a new data type `VECTOR <https://www.oracle.
com/pls/topic/lookup?ctx=dblatest&id=GUID-746EAA47-9ADA-4A77-82BB-
64E8EF5309BE>`__ for artificial intelligence and machine learning search
operations. The VECTOR data type is a homogeneous array of 8-bit signed
integers, 8-bit unsigned integers, 32-bit floating-point numbers, or 64-bit
floating-point numbers. For more information about using vectors in Oracle
Database, see the `Oracle AI Vector Search User's Guide
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=VECSE>`__.

With the VECTOR data type, you can define the number of dimensions for the
data and the storage format for each dimension value in the vector. The
possible storage formats include:

- **int8** for 8-bit signed integers
- **binary** for 8-bit unsigned integers
- **float32** for 32-bit floating-point numbers
- **float64** for 64-bit floating point numbers

Vectors can also be defined with an arbitrary number of dimensions and
formats. This allows you to specify vectors of different dimensions with the
various storage formats mentioned above. For example:

.. code-block:: sql

    CREATE TABLE vector_table (
        vec_data vector
    )

If you are interested in using VECTOR data with data frames, see
:ref:`dfvector`.

.. _intfloatformat:

Using FLOAT32, FLOAT64, and INT8 Vectors
========================================

To create a table with three columns for vector data:

.. code-block:: sql

    CREATE TABLE vector_table (
        v32 vector(3, float32),
        v64 vector(3, float64),
        v8  vector(3, int8)
    )

In this example, each column can store vector data of three dimensions where
each dimension value is of the specified format.

.. _insertintfloatformat:

Inserting FLOAT32, FLOAT64, and INT8 Vectors
--------------------------------------------

With python-oracledb, vector data can be inserted using
`Python array.array() <https://docs.python.org/3/library/array.html>`__
objects. Python arrays of type float (32-bit), double (64-bit), or
int8_t (8-bit signed integer) are used as bind values when inserting vector
columns. For example:

.. code-block:: python

    import array

    vector_data_32 = array.array("f", [1.625, 1.5, 1.0]) # 32-bit float
    vector_data_64 = array.array("d", [11.25, 11.75, 11.5]) # 64-bit float
    vector_data_8 = array.array("b", [1, 2, 3]) # 8-bit signed integer

    cursor.execute(
        "insert into vector_table (v32, v64, v8) values (:1, :2, :3)",
        [vector_data_32, vector_data_64, vector_data_8]
    )

.. _fetchintfloatformat:

Fetching FLOAT32, FLOAT64, and INT8 Vectors
-------------------------------------------

With python-oracledb, vector columns of int8, float32, and float64 format are
fetched as Python array.array() types. For example:

.. code-block:: python

    cursor.execute("select * from vector_table")
        for row in cursor:
            print(row)

This prints an output such as::

    (array("f", [1.625, 1.5, 1.0]), array("d", [11.25, 11.75, 11.5]), array("b", [1, 2, 3]))

The :ref:`FetchInfo <fetchinfoobj>` object that is returned as part of the
fetched metadata contains attributes :attr:`FetchInfo.vector_dimensions` and
:attr:`FetchInfo.vector_format` which return the number of dimensions of the
vector column and the format of each dimension value in the vector column
respectively.

.. _vecoutputtypehandlerlist:

You can convert the vector data fetched from array.array() to a Python list by
using the following :ref:`output type handler <outputtypehandlers>`:

.. code-block:: python

    def output_type_handler(cursor, metadata):
        if metadata.type_code is oracledb.DB_TYPE_VECTOR:
            return cursor.var(metadata.type_code, arraysize=cursor.arraysize,
                              outconverter=list)

    connection.outputtypehandler = output_type_handler

    cursor.execute("select * from vector_table")
    for row in cursor:
        print(row)

For each vector column, the database will now return a Python list
representation of each row's value as shown below::

    ([1.625, 1.5, 1.0], [11.25, 11.75, 11.5], [1, 2, 3])

See :ref:`insertvecwithnumpy` for an example of using an input type handler.

If you are using python-oracledb Thick mode with Oracle Client 21c or earlier,
see this :ref:`section <vector_thick_mode_old_client>`.

See `vector.py <https://github.com/oracle/python-oracledb/tree/main/
samples/vector.py>`__ for a runnable example.

.. _binaryformat:

Using BINARY Vectors
====================

A Binary vector format represents each dimension value as a binary value (0 or
1). Binary vectors require less memory storage.  For example, a 16
dimensional vector with binary format requires only 2 bytes of storage while a
16 dimensional vector with int8 format requires 16 bytes of storage.

Binary vectors are represented as 8-bit unsigned integers. For the binary
format, you must define the number of dimensions as a multiple of 8.

To create a table with one column for vector data:

.. code-block:: sql

    CREATE TABLE vector_binary_table (
        vb vector(24, binary)
    )

In this example, the VB column can store vector data of 24 dimensions
where each dimension value is represented as a single bit. Note that the
number of dimensions 24 is a multiple of 8.

If you specify a vector dimension that is not a multiple of 8, then you will
get ``ORA-51813``.

.. _insertbinaryvector:

Inserting BINARY Vectors
------------------------

Python arrays of type uint8_t (8-bit unsigned integer) are used as bind values
when inserting vector columns. The length of uint8_t arrays must be equal to
the number of dimensions divided by 8. For example, if the number of
dimensions for a vector column is 24, then the length of the array must be 3.
The values in uint8_t arrays can range from 0 to 255. For example:

.. code-block:: python

    import array

    vector_data_vb = array.array("B", [180, 150, 100]) # 8-bit unsigned integer

    cursor.execute(
        "insert into vector_binary_table values (:1)",
        [vector_data_vb]
    )

.. _fetchbinaryvector:

Fetching BINARY Vectors
-----------------------

With python-oracledb, vector columns of binary format are fetched as Python
array.array() types. For example:

.. code-block:: python

    cursor.execute("select * from vector_binary_table")
        for row in cursor:
            print(row)

This prints an output such as::

    (array("B", [180, 150, 100]))

The :ref:`FetchInfo <fetchinfoobj>` object that is returned as part of the
fetched metadata contains attributes :attr:`FetchInfo.vector_dimensions` and
:attr:`FetchInfo.vector_format` which return the number of dimensions of the
vector column and the format of each dimension value in the vector column
respectively.

You can convert the vector data fetched from a connection to a Python list by
using this :ref:`output type handler <vecoutputtypehandlerlist>`. For each vector
column, the database will now return a Python list representation of each
row's value.

If you are using python-oracledb Thick mode with Oracle Client 21c or earlier,
see this :ref:`section <vector_thick_mode_old_client>`.

.. _sparsevectors:

Using SPARSE Vectors
====================

A Sparse vector is a vector which has zero value for most of its dimensions.
This vector only physically stores the non-zero values. For more information
on sparse vectors, see the `Oracle AI Vector search User's Guide <https://
www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-6015566C-3277-4A3C-8DD0-
08B346A05478>`__.

Sparse vectors are represented by the total number of vector dimensions, an
array of indices, and an array of values where each value's location in the
vector is indicated by the corresponding indices array position. All other
vector values are treated as zero.  The storage formats that can be used with
sparse vectors are float32, float64, and int8. Note that the binary storage
format cannot be used with sparse vectors.

For example, a string representation could be::

    [25, [5, 8, 11], [25.25, 6.125, 8.25]]

In this example, the sparse vector has 25 dimensions. Only indices 5, 8, and 11
have values which are 25.25, 6.125, and 8.25 respectively. All of the other
values are zero.

In Oracle AI Database, you can define a column for a sparse vector using the
following format::

    VECTOR(number_of_dimensions, dimension_storage_format, sparse)

For example, to create a table with three columns for sparse vectors:

.. code-block:: sql

    CREATE TABLE vector_sparse_table (
        float32sparsecol vector(25, float32, sparse),
        float64sparsecol vector(30, float64, sparse),
        int8sparsecol vector(35, int8, sparse)
    )

In this example:

- The float32sparsecol column can store sparse vector data of 25 dimensions
  where each dimension value is a 32-bit floating-point number.

- The float64sparsecol column can store sparse vector data of 30 dimensions
  where each dimension value is a 64-bit floating-point number.

- The int8sparsecol column can store sparse vector data of 35 dimensions where
  each dimension value is a 8-bit signed integer.

.. _insertsparsevectors:

Inserting SPARSE Vectors
------------------------

With python-oracledb, sparse vector data can be inserted using
:ref:`SparseVector objects <sparsevectorsobj>`.  The SparseVector objects are
used when fetching vectors, and as bind values when inserting sparse vector
columns. For example to insert data:

.. code-block:: python

    import array

    # 32-bit float sparse vector
    float32_val = oracledb.SparseVector(
        25, [6, 10, 18], array.array('f', [26.25, 129.625, 579.875])
    )

    # 64-bit float sparse vector
    float64_val = oracledb.SparseVector(
        30, [9, 16, 24], array.array('d', [19.125, 78.5, 977.375])
    )

    # 8-bit signed integer sparse vector
    int8_val = oracledb.SparseVector(
        35, [10, 20, 30], array.array('b', [26, 125, -37])
    )

    cursor.execute(
        "insert into vector_sparse_table values (:1, :2, :3)",
        [float32_val, float64_val, int8_val]
    )

.. _fetchsparsevectors:

Fetching Sparse Vectors
-----------------------

With python-oracledb, sparse vector columns are fetched as :ref:`SparseVector
objects <sparsevectorsobj>`:

.. code-block:: python

    cursor.execute("select * from vector_sparse_table")
    for row in cursor:
       print(row)


This prints::

    (oracledb.SparseVector(25, array('I', [6, 10, 18]), array('f', [26.25, 129.625, 579.875])),
     oracledb.SparseVector(30, array('I', [9, 16, 24]), array('d', [19.125, 78.5, 977.375])),
     oracledb.SparseVector(35, array('I', [10, 20, 30]), array('b', [26, 125, -37])))

Depending on context, the SparseVector type will be treated as a string:

.. code-block:: python

    cursor.execute("select * from vector_sparse_table")
    for float32_val, float64_val, int8_val in cursor:
        print("float32:", float32_val)
        print("float64:", float64_val)
        print("int8:", int8_val)

This prints::

    float32: [25, [6, 10, 18], [26.25, 129.625, 579.875]]
    float64: [30, [9, 16, 24], [19.125, 78.5, 977.375]]
    int8: [35, [10, 20, 30], [26, 125, -37]]

Values can also be explicitly passed to `str()
<https://docs.python.org/3/library/stdtypes.html#str>`__, if needed.

VECTOR Metadata
===============

The :ref:`FetchInfo <fetchinfoobj>` object that is returned as part of the
query metadata contains attributes :attr:`FetchInfo.vector_dimensions`,
:attr:`FetchInfo.vector_format`, and :attr:`FetchInfo.vector_is_sparse` which
return the number of dimensions of the vector column, the format of each
dimension value in the vector column, and a boolean which determines whether
the vector is sparse or not.

For example:

.. code-block:: python

    cursor.execute("select float64sparsecol from vector_sparse_table")
    desc = cursor.description[0]
    print(desc.vector_format, desc.vector_dimensions, desc.vector_is_sparse)

might print::

    VectorFormat.FLOAT64 30 True

.. _vector_thick_mode_old_client:

Using python-oracledb Thick Mode with Older Versions of Oracle Client Libraries
===============================================================================

If you are using python-oracledb Thick mode with Oracle Client 21c or earlier,
then you must use strings when inserting vectors.  The vector columns are
fetched as Python lists.

Inserting Vectors with Older Oracle Client Versions
---------------------------------------------------

To insert vectors of int8, float32, float64, and unit8 format when using Oracle
Client 21c or earlier, you must use strings as shown below:

.. code-block:: python

    vector_data_32 = "[1.625, 1.5, 1.0]"
    vector_data_64 = "[11.25, 11.75, 11.5]"
    vector_data_8 = "[1, 2, 3]"
    vector_data_vb = "[180, 150, 100]"

    cursor.execute(
        "insert into vector_table (v32, v64, v8, vb) values (:1, :2, :3, :4)",
        [vector_data_32, vector_data_64, vector_data_8, vector_data_vb]
    )

Fetching Vectors with Older Oracle Client Versions
--------------------------------------------------

With Oracle Client 21c or earlier, the vector columns are fetched as Python
lists. For example:

.. code-block:: python

    cursor.execute("select * from vector_table")
    for row in cursor:
        print(row)

This prints an output such as::

    ([1.625, 1.5, 1.0], [11.25, 11.75, 11.5], [1, 2, 3], [180, 150, 100])

See `vector_string.py <https://github.com/oracle/python-oracledb/tree/main/
samples/vector_string.py>`__ for a runnable example.

.. _numpyvectors:

Using NumPy
===========

Vector data can be used with Python's `NumPy <https://numpy.org>`__ package
types. To use NumPy's ndarray type, install NumPy, for example with
``pip install numpy``, and import the module in your code.

.. _insertvecwithnumpy:

Inserting Vectors with NumPy
----------------------------

To insert vectors, you must convert NumPy ndarray types to array types. This
conversion can be done by using an input type handler. For example:

.. code-block:: python

    def numpy_converter_in(value):
        if value.dtype == numpy.float64:
            dtype = "d"
        elif value.dtype == numpy.float32:
            dtype = "f"
        elif value.dtype == numpy.uint8:
            dtype = "B"
        else:
            dtype = "b"
        return array.array(dtype, value)

    def input_type_handler(cursor, value, arraysize):
        if isinstance(value, numpy.ndarray):
            return cursor.var(
                oracledb.DB_TYPE_VECTOR,
                arraysize=arraysize,
                inconverter=numpy_converter_in,
            )

Using it in an ``INSERT`` statement:

.. code-block:: python

    vector_data_32 = numpy.array([1.625, 1.5, 1.0], dtype=numpy.float32)
    vector_data_64 = numpy.array([11.25, 11.75, 11.5], dtype=numpy.float64)
    vector_data_8 = numpy.array([1, 2, 3], dtype=numpy.int8)
    vector_data_vb = numpy.array([180, 150, 100], dtype=numpy.uint8)

    connection.inputtypehandler = input_type_handler

    cursor.execute(
        "insert into vector_table (v32, v64, v8, vb) values (:1, :2, :3, :4)",
        [vector_data_32, vector_data_64, vector_data_8, vector_data_vb],
    )

.. _fetchvecwithnumpy:

Fetching Vectors with NumPy
---------------------------

To fetch vector data as an ndarray type, you can convert the array type to
an ndarray type by using an output type handler. For example:

.. code-block:: python

    def numpy_converter_out(value):
        return numpy.array(value, copy=False, dtype=value.typecode)

    def output_type_handler(cursor, metadata):
        if metadata.type_code is oracledb.DB_TYPE_VECTOR:
            return cursor.var(
                metadata.type_code,
                arraysize=cursor.arraysize,
                outconverter=numpy_converter_out,
            )

Using it to query the columns:

.. code-block:: python

    connection.outputtypehandler = output_type_handler

    cursor.execute("select * from vector_table")
        for row in cursor:
            print(row)

This prints an output such as::

    (array([1.625, 1.5, 1.0], dtype=float32), array([11.25, 11.75, 11.5], dtype=float64), array([1, 2, 3], dtype=int8), array([180, 150, 100], dtype=uint8))

See `vector_numpy.py <https://github.com/oracle/python-oracledb/tree/main/
samples/vector_numpy.py>`__ for a runnable example.
