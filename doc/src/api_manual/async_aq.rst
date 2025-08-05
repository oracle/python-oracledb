.. _asyncaq:

********************************
API: Async Advanced Queuing (AQ)
********************************

.. currentmodule:: oracledb

See :ref:`aqusermanual` for more information about using AQ in python-oracledb.

.. versionadded:: 3.1.0

.. note::

    AsyncQueue objects are only supported in python-oracledb Thin mode.

.. _asyncqueue:

AsyncQueue Class
================

.. autoclass:: AsyncQueue

    An AsyncQueue object should be created using
    :meth:`AsyncConnection.queue()` and is used to enqueue and dequeue
    messages.

AsyncQueue Methods
------------------

.. automethod:: AsyncQueue.deqmany

.. automethod:: AsyncQueue.deqone

.. automethod:: AsyncQueue.enqmany

.. automethod:: AsyncQueue.enqone

AsyncQueue Attributes
---------------------

.. autoproperty:: AsyncQueue.connection

.. autoproperty:: AsyncQueue.deqoptions

.. autoproperty:: AsyncQueue.enqoptions

.. autoproperty:: AsyncQueue.name

.. autoproperty:: AsyncQueue.payload_type

.. _asyncdeqoptions:

DeqOptions Class
================

A DeqOptions object is used to configure how messages are dequeued from
queues. An instance of this object is found in the attribute
:attr:`AsyncQueue.deqoptions`.

See :ref:`deqoptions` for information on the supported attributes.

.. _asyncenqoptions:

EnqOptions Class
================

An EnqOptions object is used to configure how messages are enqueued into
queues. An instance of this object is found in the attribute
:attr:`AsyncQueue.enqoptions`.

See :ref:`enqoptions` for information on the supported attributes.

.. _asyncmsgproperties:

MessageProperties Class
=======================

A MessageProperties object is used to identify the properties of messages
that are enqueued and dequeued in queues. They are created by the method
:meth:`AsyncConnection.msgproperties()`. They are used by the method
:meth:`AsyncQueue.enqone()` and returned by the method
:meth:`AsyncQueue.deqone()`.

See :ref:`msgproperties` for information on the supported attributes.
