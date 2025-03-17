.. _asyncaq:

********************************
API: Async Advanced Queuing (AQ)
********************************

See :ref:`aqusermanual` for more information about using AQ in python-oracledb.

.. versionadded:: 3.1.0

.. note::

    AsyncQueue objects are only supported in python-oracledb Thin mode.

.. _asyncqueue:

AsyncQueue Objects
==================

These objects are created using the :meth:`AsyncConnection.queue()` method and
are used to enqueue and dequeue messages.

AsyncQueue Methods
------------------

.. method:: AsyncQueue.deqmany(max_num_messages)

    Dequeues up to the specified number of messages from the queue and returns
    a list of these messages. Each element of the returned list is a
    :ref:`message property <msgproperties>` object.

.. method:: AsyncQueue.deqone()

    Dequeues at most one message from the queue. If a message is dequeued, it
    will be a :ref:`message property <asyncmsgproperties>` object; otherwise,
    the value *None* will be returned.

.. method:: AsyncQueue.enqmany(messages)

    Enqueues multiple messages into the queue. The ``messages`` parameter must
    be a sequence containing :ref:`message property <msgproperties>` objects
    which have all had their payload attribute set to a value that the queue
    supports.

.. method:: AsyncQueue.enqone(message)

    Enqueues a single message into the queue. The message must be a
    :ref:`message property <asyncmsgproperties>` object which has had its
    payload attribute set to a value that the queue supports.

AsyncQueue Attributes
---------------------

.. attribute:: AsyncQueue.connection

    This read-only attribute returns a reference to the connection object on
    which the queue was created.

.. attribute:: AsyncQueue.deqoptions

    This read-only attribute returns a reference to the :ref:`options
    <asyncdeqoptions>` that will be used when dequeuing messages from the queue.

.. attribute:: AsyncQueue.enqoptions

    This read-only attribute returns a reference to the :ref:`options
    <asyncenqoptions>` that will be used when enqueuing messages into the queue.

.. attribute:: AsyncQueue.name

    This read-only attribute returns the name of the queue.

.. attribute:: AsyncQueue.payload_type

    This read-only attribute returns the object type for payloads that can be
    enqueued and dequeued. If using a JSON queue, this returns the value
    ``"JSON"``. If using a raw queue, this returns the value *None*.

.. _asyncdeqoptions:

Dequeue Options
===============

.. note::

    These objects are used to configure how messages are dequeued from queues.
    An instance of this object is found in the attribute
    :attr:`AsyncQueue.deqoptions`.

See :ref:`deqoptions` for information on the supported attributes.

.. _asyncenqoptions:

Enqueue Options
===============

.. note::

    These objects are used to configure how messages are enqueued into queues.
    An instance of this object is found in the attribute
    :attr:`AsyncQueue.enqoptions`.

See :ref:`enqoptions` for information on the supported attributes.

.. _asyncmsgproperties:

Message Properties
==================

.. note::

    These objects are used to identify the properties of messages that are
    enqueued and dequeued in queues. They are created by the method
    :meth:`AsyncConnection.msgproperties()`.  They are used by the method
    :meth:`AsyncQueue.enqone()` and returned by the method
    :meth:`AsyncQueue.deqone()`.

See :ref:`msgproperties` for information on the supported attributes.
