.. _defaults:

********************
API: Defaults Object
********************

This object contains attributes that can be used to adjust the behavior of the
python-oracledb driver.

All attributes are supported in Thin and Thick modes, subject to noted details.

An example of changing a default value is:

.. code-block:: python

    import oracledb

    oracledb.defaults.fetch_lobs = False  # return LOBs directly as strings or bytes

Defaults Attributes
===================

.. attribute:: defaults.arraysize

    The default value for :attr:`Cursor.arraysize`. This is a query tuning
    attribute, see :ref:`Tuning Fetch Performance <tuningfetch>`.

    This attribute has an initial value of 100.

.. attribute:: defaults.config_dir

    The directory in which optional configuration files such as
    ``tnsnames.ora`` will be read in python-oracledb Thin mode.  This attribute
    takes its initial value from the environment variable ``TNS_ADMIN``.

    This attribute is not used by the python-oracledb Thick mode: the usual
    Oracle Client search path behavior for configuration files is followed, see
    :ref:`optnetfiles`.

.. attribute:: defaults.fetch_decimals

    Identifies whether numbers should be fetched as ``decimal.Decimal`` values.
    This can help avoid issues with converting numbers from Oracle Database's
    decimal format to Python's binary format.

    An output type handler such as previously required in cx_Oracle (see
    `return_numbers_as_decimals.py <https://github.com/oracle/python-cx_Oracle/
    blob/main/samples/return_numbers_as_decimals.py>`__) can alternatively be
    used to adjust the returned type.  If a type handler exists and returns a
    variable (that is, `cursor.var(...)`), then that return variable is used.
    If the type handler returns None, then the value of
    ``oracledb.defaults.fetch_decimals`` is used to determine whether to return
    ``decimal.Decimal`` values.

    This attribute has an initial value of False.

.. attribute:: defaults.fetch_lobs

    When the value of this attribute is True, then queries to LOB columns return
    LOB locators. When the value of this attribute is False, then strings or bytes
    are fetched. If LOBs are larger than 1 GB, then this attribute should be set to
    True and the LOBs should be streamed.  See :ref:`lobdata`.

    An output type handler such as the one previously required in cx_Oracle (see
    `return_lobs_as_strings.py <https://github.com/oracle/python-cx_Oracle/blob/main/samples/
    return_lobs_as_strings.py>`__) can alternatively be used to adjust the returned type.
    If a type handler exists and returns a variable (that is, `cursor.var(...)`), then
    that return variable is used. If the type handler returns None, then the value of
    ``oracledb.defaults.fetch_lobs`` is used.

    This attribute has an initial value of True.

.. attribute:: defaults.prefetchrows

    The default value for :attr:`Cursor.prefetchrows`. This is a query tuning
    attribute, see :ref:`Tuning Fetch Performance <tuningfetch>`.

    This attribute has an initial value of 2.

.. attribute:: defaults.stmtcachesize

    The default value for :attr:`Connection.stmtcachesize` and
    :attr:`ConnectionPool.stmtcachesize`. This is a tuning attribute, see
    :ref:`stmtcache`.

    This attribute has an initial value of 20.
