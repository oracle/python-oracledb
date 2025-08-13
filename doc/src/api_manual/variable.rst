.. _varobj:

*********************
API: Variable Objects
*********************

.. currentmodule:: oracledb

Variable Class
==============

.. autoclass:: Var

    A Var object should be created with :meth:`Cursor.var()` or
    :meth:`Cursor.arrayvar()`.

    .. dbapiobjectextension::

Variable Methods
=================

.. automethod:: Var.getvalue

.. automethod:: Var.setvalue

Variable Attributes
===================

.. autoproperty:: Var.actual_elements

    For consistency and compliance with the PEP 8 naming style, the
    attribute ``actualElements`` was renamed to ``actual_elements``. The old
    name will continue to work for a period of time.

.. autoproperty:: Var.buffer_size

    For consistency and compliance with the PEP 8 naming style, the
    attribute ``bufferSize`` was renamed to ``buffer_size``. The old
    name will continue to work for a period of time.

.. autoproperty:: Var.convert_nulls

   .. versionadded:: 1.4.0

.. autoproperty:: Var.inconverter

.. autoproperty:: Var.num_elements

    For consistency and compliance with the PEP 8 naming style, the
    attribute ``numElements`` was renamed to ``num_elements``. The old name
    will continue to work for a period of time.

.. autoproperty:: Var.outconverter

.. autoproperty:: Var.size

.. autoproperty:: Var.type

.. autoproperty:: Var.values
