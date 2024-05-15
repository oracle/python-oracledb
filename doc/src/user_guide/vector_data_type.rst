.. _vectors:

*****************
Using Vector Data
*****************

Oracle Database 23ai introduced a new data type VECTOR for artificial
intelligence and machine learning search operations. The vector data type
is a homogeneous array of 8-bit signed integers, 32-bit floating-point
numbers, or 64-bit floating-point numbers. With the vector data type, you
can define the number of dimensions for the data and the storage format
for each dimension value in the vector.

To create a table with three columns for vector data, for example:

.. code-block:: sql

    CREATE TABLE vector_table (
        v32 vector(3, float32),
        v64 vector(3, float64),
        v8  vector(3, int8)
    )

In this example, each column can store vector data of three dimensions where
each dimension value is of the specified storage format. This example is used
in subsequent sections.

.. _insertvector:

Inserting Vectors
=================

With python-oracledb, vector data can be inserted using Python arrays
(``array.array()``). To use Python arrays, import the ``array`` module in your
code.

Python arrays (``array.array()``) of float (32-bit), double (64-bit), or
int8_t (8-bit signed integer) are used as bind values when inserting vector
columns. For example:

.. code-block:: python

    vector_data_32 = array.array("f", [1.625, 1.5, 1.0]) # 32-bit float
    vector_data_64 = array.array("d", [11.25, 11.75, 11.5]) # 64-bit float
    vector_data_8 = array.array("b", [1, 2, 3]) # 8-bit signed integer

    cursor.execute(
        "insert into vector_table (v32, v64, v8) values (:1, :2, :3)",
        [vector_data_32, vector_data_64, vector_data_8],
    )

See `vector.py <https://github.com/oracle/python-oracledb/tree/main/
samples/vector.py>`__ for a runnable example.

If you are using python-oracledb Thick mode with older versions of Oracle
Client libraries than 23ai, see this
:ref:`section <vector_thick_mode_old_client>`.

.. _fetchvector:

Fetching Vectors
================

With python-oracledb, vector columns are fetched as Python arrays
(``array.array()``). For example:

.. code-block:: python

    cursor.execute("select * from vector_table")
        for row in cursor:
            print(row)

This prints an output such as::

    (array("f", [1.625, 1.5, 1.0]), array("d", [11.25, 11.75, 11.5]), array("b", [1, 2, 3]))

The :ref:`FetchInfo <fetchinfoobj>` object that is returned as part of the
fetched metadata contains attributes :attr:`FetchInfo.vector_dimensions` and
:attr:`FetchInfo.vector_format` which return the number of dimensions of the
vector column and the storage format of each dimension value in the vector
column respectively.

You can convert the vector data fetched from a connection to a Python list by
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
representation of each row's value.

If you are using python-oracledb Thick mode with older versions of Oracle
Client libraries than 23ai, see :ref:`below <vector_thick_mode_old_client>`.

.. _vector_thick_mode_old_client:

Using python-oracledb Thick Mode with Older Versions of Oracle Client Libraries
===============================================================================

If you are using python-oracledb Thick mode with older versions of Oracle
Client libraries than 23ai, then you must use strings when inserting vectors.
For example:

.. code-block:: python

    vector_data_32 = "[1.625, 1.5, 1.0]"
    vector_data_64 = "[11.25, 11.75, 11.5]"
    vector_data_8 = "[1, 2, 3]"

    cursor.execute(
        "insert into vector_table (v32, v64, v8) values (:1, :2, :3)",
        [vector_data_32, vector_data_64, vector_data_8],
    )

The vector columns are fetched as Python lists. For example:

.. code-block:: python

    cursor.execute("select * from vector_table")
    for row in cursor:
        print(row)

See `vector_string.py <https://github.com/oracle/python-oracledb/tree/main/
samples/vector_string.py>`__ for a runnable example.

.. _numpyvectors:

Using NumPy
===========

Vector data can be used with Python's `NumPy <https://numpy.org>`__ package
types. To use NumPy's ndarray type, install NumPy, for example with
``pip install numpy``, and import the module in your code.

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

    connection.inputtypehandler = input_type_handler

    cursor.execute(
        "insert into vector_table (v32, v64, v8) values (:1, :2, :3)",
        [vector_data_32, vector_data_64, vector_data_8],
    )

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

Using it in a query:

.. code-block:: python

    connection.outputtypehandler = output_type_handler

    cursor.execute("select * from vector_table")
        for row in cursor:
            print(row)

This prints an output such as::

    (array([1.625, 1.5, 1.0], dtype=float32), array([11.25, 11.75, 11.5], dtype=float64), array([1, 2, 3], dtype=int8))

See `vector_numpy.py <https://github.com/oracle/python-oracledb/tree/main/
samples/vector_numpy.py>`__ for a runnable example.
