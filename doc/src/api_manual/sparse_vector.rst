.. _sparsevectorsobj:

*************************
API: SparseVector Objects
*************************

A SparseVector Object stores information about a sparse vector. This object
can be created with :meth:`oracledb.SparseVector()`.

See :ref:`sparsevectors` for more information.

.. versionadded:: 3.0.0

SparseVector Attributes
=======================

.. attribute:: SparseVector.indices

    This read-only attribute is an array that returns the indices (zero-based)
    of non-zero values in the vector.

.. attribute:: SparseVector.num_dimensions

    This read-only attribute is an integer that returns the number of
    dimensions of the vector.

.. attribute:: SparseVector.values

    This read-only attribute is an array that returns the non-zero values
    stored in the vector.
