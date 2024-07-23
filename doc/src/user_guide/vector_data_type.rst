.. _vectors:

*****************
Using VECTOR Data
*****************

Oracle Database 23ai introduced a new data type `VECTOR <https://docs.oracle.
com/en/database/oracle/oracle-database/23/vecse/overview-ai-vector-search.
html>`__ for artificial intelligence and machine learning search operations.
The VECTOR data type is a homogeneous array of 8-bit signed integers, 8-bit
unsigned integers, 32-bit floating-point numbers, or 64-bit floating-point
numbers.

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

.. _outputtypehandlerlist:

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

If you are using python-oracledb Thick mode with older versions of Oracle
Client libraries than 23ai, see this
:ref:`section <vector_thick_mode_old_client>`.

See `vector.py <https://github.com/oracle/python-oracledb/tree/main/
samples/vector.py>`__ for a runnable example.

.. _binaryformat:

Using BINARY Vectors
====================

In addition to Int8, Float32, and Float64 formats, you can also use a
Binary format to define vectors. The binary format represents each dimension
value as a binary value (0 or 1). Binary vectors require less memory storage.
For example, a 16 dimensional vector with binary format requires only 2 bytes
of storage while a 16 dimensional vector with int8 format requires 16 bytes of
storage.

Binary vectors are represented as 8-bit unsigned integers. For the binary
format, you must define the number of dimensions as a multiple of 8.

To create a table with one column for vector data:

.. code-block:: sql

    CREATE TABLE vector_binary_table (
        vb vector(24, binary)
    )

In this example, the ``vb`` column can store vector data of 24 dimensions
where each dimension value is represented as a single bit. Note that the
number of dimensions 24 is a multiple of 8.

If you specify a vector dimension that is not a multiple of 8, then you will
get ``ORA-51813``.

.. _insertbinaryvector:

Inserting BINARY Vectors
------------------------

Python arrays of type uint8_t (8-bit unsigned integer) are used as bind values
when inserting vector columns. The length of unit8_t arrays must be equal to
the number of dimensions divided by 8. For example, if the number of
dimensions for a vector column is 24, then the length of the array must be 3.
The values in unint8_t arrays can range from 0 to 255. For example:

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
using this :ref:`output type handler <outputtypehandlerlist>`. For each vector
column, the database will now return a Python list representation of each
row's value.

If you are using python-oracledb Thick mode with older versions of Oracle
Client libraries than 23ai, see this
:ref:`section <vector_thick_mode_old_client>`.

.. _vector_thick_mode_old_client:

Using python-oracledb Thick Mode with Older Versions of Oracle Client Libraries
===============================================================================

If you are using python-oracledb Thick mode with versions of Oracle Client
libraries older than 23ai, then you must use strings when inserting vectors.
The vector columns are fetched as Python lists.

Inserting Vectors with Older Oracle Client Versions
---------------------------------------------------

To insert vectors of int8, float32, float64, and unit8 format when using Oracle
Client versions older than 23ai, you must use strings as shown below:

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

With Oracle Client versions older than 23ai, the vector columns are fetched as
Python lists. For example:

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

    vector_data_32 = numpy.array([1.625, 1.5, 1.0])
    vector_data_64 = numpy.array([11.25, 11.75, 11.5])
    vector_data_8 = numpy.array([1, 2, 3])
    vector_data_vb = numpy.array([180, 150, 100])

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
        if value.typecode == "b":
            dtype = numpy.int8
        elif value.typecode == "f":
            dtype = numpy.float32
        elif value.typecode == "B":
            dtype = numpy.uint8
        else:
            dtype = numpy.float64
        return numpy.array(value, copy=False, dtype=dtype)

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
