.. _asynclobobj:

*********************
API: AsyncLOB Objects
*********************

An AsyncLOB object can be created with :meth:`AsyncConnection.createlob()`.
Also, this object is returned whenever Oracle :data:`CLOB`, :data:`BLOB` and
:data:`BFILE` columns are fetched.

.. dbapiobjectextension::

See :ref:`lobdata` for more information about using LOBs.

.. note::

    AsyncLOB objects are only supported in the python-oracledb Thin mode.

.. _asynclobmeth:

AsyncLOB Methods
================

.. method:: AsyncLOB.close()

    Closes the LOB. Call this when writing is completed so that the indexes
    associated with the LOB can be updated -- but only if :meth:`~AsyncLOB.open()`
    was called first.

.. method:: AsyncLOB.fileexists()

    Returns a boolean indicating if the file referenced by the BFILE type LOB
    exists.

.. method:: AsyncLOB.getchunksize()

    Returns the chunk size for the internal LOB. Reading and writing to the LOB
    in chunks of multiples of this size will improve performance.

.. method:: AsyncLOB.getfilename()

    Returns a two-tuple consisting of the directory alias and file name for a
    BFILE type LOB.

.. method:: AsyncLOB.isopen()

    Returns a boolean indicating if the LOB has been opened using the method
    :meth:`~AsyncLOB.open()`.

.. method:: AsyncLOB.open()

    Opens the LOB for writing. This will improve performance when writing to a
    LOB in chunks and there are functional or extensible indexes associated
    with the LOB. If this method is not called, each write will perform an open
    internally followed by a close after the write has been completed.

.. method:: AsyncLOB.read([offset=1, [amount]])

    Returns a portion (or all) of the data in the LOB object. Note that the
    amount and offset are in bytes for BLOB and BFILE type LOBs and in UCS-2
    code points for CLOB and NCLOB type LOBs. UCS-2 code points are equivalent
    to characters for all but supplemental characters. If supplemental
    characters are in the LOB, the offset and amount will have to be chosen
    carefully to avoid splitting a character.

.. method:: AsyncLOB.setfilename(dir_alias, name)

    Sets the directory alias and name of the BFILE type LOB.

.. method:: AsyncLOB.size()

    Returns the size of the data in the LOB object. For BLOB and BFILE type
    LOBs, this is the number of bytes. For CLOB and NCLOB type LOBs, this is the
    number of UCS-2 code points. UCS-2 code points are equivalent to characters
    for all but supplemental characters.

.. method:: AsyncLOB.trim(new_size=0)

    Trims the LOB to the new size.

.. method:: AsyncLOB.write(data, offset=1)

    Writes the data to the LOB object at the given offset. The offset is in
    bytes for BLOB type LOBs and in UCS-2 code points for CLOB and NCLOB type
    LOBs. UCS-2 code points are equivalent to characters for all but
    supplemental characters. If supplemental characters are in the LOB, the
    offset will have to be chosen carefully to avoid splitting a character.
    Note that if you want to make the LOB value smaller, you must use the
    :meth:`~AsyncLOB.trim()` function.

.. _asynclobattr:

AsyncLOB Attributes
===================

.. attribute:: AsyncLOB.type

    This read-only attribute returns the type of the LOB as one of the
    :ref:`database type constants <dbtypes>`.
