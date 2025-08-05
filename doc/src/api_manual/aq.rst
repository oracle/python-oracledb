.. _aq:

**************************
API: Advanced Queuing (AQ)
**************************

.. currentmodule:: oracledb

See :ref:`aqusermanual` for more information about using AQ in python-oracledb.

.. _queue:

Queue Class
===========

.. autoclass:: Queue

    A Queue object should be created using :meth:`Connection.queue()` and is
    used to enqueue and dequeue messages.

    .. dbapiobjectextension::

Queue Methods
-------------

.. automethod:: Queue.deqmany

    For consistency and compliance with the PEP 8 naming style, the name of
    the method was changed from `deqMany()`. The old name will continue to
    work for a period of time.

.. automethod:: Queue.deqone

    For consistency and compliance with the PEP 8 naming style, the name of
    the method was changed from `deqOne()`. The old name will continue to
    work for a period of time.

.. automethod:: Queue.enqmany

    For consistency and compliance with the PEP 8 naming style, the name of
    the method was changed from `enqMany()`. The old name will continue
    to work for a period of time.

.. automethod:: Queue.enqone

    For consistency and compliance with the PEP 8 naming style, the name of
    the method was changed from `enqOne()`. The old name will continue
    to work for a period of time.

Queue Attributes
----------------

.. autoproperty:: Queue.connection

.. autoproperty:: Queue.deqoptions

    For consistency and compliance with the PEP 8 naming style, the name of
    the attribute was changed from ``deqOptions``. The old name will continue
    to work for a period of time.

.. autoproperty:: Queue.enqoptions

    For consistency and compliance with the PEP 8 naming style, the name of
    the attribute was changed from ``enqOptions``. The old name will continue
    to work for a period of time.

.. autoproperty:: Queue.name

.. autoproperty:: Queue.payload_type

    For consistency and compliance with the PEP 8 naming style, the name of
    the attribute was changed from ``payloadType``. The old name will
    continue to work for a period of time.

.. _deqoptions:

DeqOptions Class
================

.. autoclass:: DeqOptions

    A DeqOptions object is used to configure how messages are dequeued
    from queues. An instance of this object is found in the attribute
    :attr:`Queue.deqoptions`.

    .. dbapiobjectextension::

DeqOptions Attributes
---------------------

.. autoproperty:: DeqOptions.condition

.. autoproperty:: DeqOptions.consumername

.. autoproperty:: DeqOptions.correlation

.. autoproperty:: DeqOptions.deliverymode

.. autoproperty:: DeqOptions.mode

.. autoproperty:: DeqOptions.msgid

.. autoproperty:: DeqOptions.navigation

.. autoproperty:: DeqOptions.transformation

.. autoproperty:: DeqOptions.visibility

.. autoproperty:: DeqOptions.wait

.. _enqoptions:

EnqOptions Class
================

.. autoclass:: EnqOptions

    An EnqOptions object is used to configure how messages are enqueued into
    queues. An instance of this object is found in the attribute
    :attr:`Queue.enqoptions`.

    .. dbapiobjectextension::

EnqOptions Attributes
---------------------

.. autoproperty:: EnqOptions.deliverymode

.. autoproperty:: EnqOptions.transformation

.. autoproperty:: EnqOptions.visibility

.. _msgproperties:

MessageProperties Class
=======================

.. autoclass:: MessageProperties

    A MessageProperties object is used to identify the properties of messages
    that are enqueued and dequeued in queues. They are created by the method
    :meth:`Connection.msgproperties()`.  They are used by the methods
    :meth:`Queue.enqone()` and :meth:`Queue.enqmany()` and returned by the
    methods :meth:`Queue.deqone()` and :meth:`Queue.deqmany()`.

    .. dbapiobjectextension::

MessageProperties Attributes
----------------------------

.. autoproperty:: MessageProperties.attempts

.. autoproperty:: MessageProperties.correlation

.. autoproperty:: MessageProperties.delay

.. autoproperty:: MessageProperties.deliverymode

.. autoproperty:: MessageProperties.enqtime

.. autoproperty:: MessageProperties.exceptionq

.. autoproperty:: MessageProperties.expiration

.. autoproperty:: MessageProperties.msgid

.. autoproperty:: MessageProperties.payload

.. autoproperty:: MessageProperties.priority

.. autoproperty:: MessageProperties.recipients

.. autoproperty:: MessageProperties.state
