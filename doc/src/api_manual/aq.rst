.. _aq:

***************************
API: Advanced Queuing (AQ)
***************************

See :ref:`aqusermanual` for more information about using AQ in python-oracledb.

.. _queue:

Queue Objects
=============

These objects are created using the :meth:`Connection.queue()` method and are
used to enqueue and dequeue messages.

.. dbapiobjectextension::

Queue Methods
-------------

.. method:: Queue.deqmany(max_num_messages)

    Dequeues up to the specified number of messages from the queue and returns
    a list of these messages. Each element of the returned list is a
    :ref:`message property <msgproperties>` object.

    For consistency and compliance with the PEP 8 naming style, the name of
    the method was changed from `deqMany()`. The old name will continue to
    work for a period of time.

.. method:: Queue.deqone()

    Dequeues at most one message from the queue. If a message is dequeued, it
    will be a :ref:`message property <msgproperties>` object; otherwise, it will
    be the value *None*.

    For consistency and compliance with the PEP 8 naming style, the name of
    the method was changed from `deqOne()`. The old name will continue to
    work for a period of time.

.. method:: Queue.enqmany(messages)

    Enqueues multiple messages into the queue. The ``messages`` parameter must
    be a sequence containing :ref:`message property <msgproperties>` objects
    which have all had their payload attribute set to a value that the queue
    supports.

    .. warning::

        In python-oracledb Thick mode using Oracle Client libraries prior to
        21c, calling :meth:`Queue.enqmany()` in parallel on different
        connections acquired from the same connection pool may fail due to
        Oracle bug 29928074. To avoid this, do one of: upgrade the client
        libraries, ensure that :meth:`Queue.enqmany()` is not run in parallel,
        use standalone connections or connections from different pools, or make
        multiple calls to :meth:`Queue.enqone()`. The function
        :meth:`Queue.deqmany()` call is not affected.

    For consistency and compliance with the PEP 8 naming style, the name of
    the method was changed from `enqMany()`. The old name will continue
    to work for a period of time.

.. method:: Queue.enqone(message)

    Enqueues a single message into the queue. The message must be a
    :ref:`message property<msgproperties>` object which has had its payload
    attribute set to a value that the queue supports.

    For consistency and compliance with the PEP 8 naming style, the name of
    the method was changed from `enqOne()`. The old name will continue
    to work for a period of time.

Queue Attributes
----------------

.. attribute:: Queue.connection

    This read-only attribute returns a reference to the connection object on
    which the queue was created.

.. attribute:: Queue.deqoptions

    This read-only attribute returns a reference to the :ref:`options
    <deqoptions>` that will be used when dequeuing messages from the queue.

    For consistency and compliance with the PEP 8 naming style, the name of
    the attribute was changed from ``deqOptions``. The old name will continue
    to work for a period of time.

.. attribute:: Queue.enqoptions

    This read-only attribute returns a reference to the :ref:`options
    <enqoptions>` that will be used when enqueuing messages into the queue.

    For consistency and compliance with the PEP 8 naming style, the name of
    the attribute was changed from ``enqOptions``. The old name will continue
    to work for a period of time.

.. attribute:: Queue.name

    This read-only attribute returns the name of the queue.

.. attribute:: Queue.payload_type

    This read-only attribute returns the object type for payloads that can be
    enqueued and dequeued. If using a JSON queue, this returns the value
    ``"JSON"``. If using a raw queue, this returns the value *None*.

    For consistency and compliance with the PEP 8 naming style, the name of
    the attribute was changed from ``payloadType``. The old name will
    continue to work for a period of time.


.. _deqoptions:

Dequeue Options
===============

These objects are used to configure how messages are dequeued from queues.
An instance of this object is found in the attribute :attr:`Queue.deqOptions`.

.. dbapiobjectextension::

.. attribute:: DeqOptions.condition

    This read-write attribute specifies a boolean expression similar to the where
    clause of a SQL query. The boolean expression can include conditions on message
    properties, user data properties and PL/SQL or SQL functions. The default
    is to have no condition specified.


.. attribute:: DeqOptions.consumername

    This read-write attribute specifies the name of the consumer. Only messages
    matching the consumer name will be accessed. If the queue is not set up for
    multiple consumers this attribute should not be set. The default is to have
    no consumer name specified.


.. attribute:: DeqOptions.correlation

    This read-write attribute specifies the correlation identifier of the message
    to be dequeued. Special pattern-matching characters, such as the percent sign (%)
    and the underscore (_), can be used. If multiple messages satisfy the
    pattern, the order of dequeuing is indeterminate. The default is to have no
    correlation specified.


.. attribute:: DeqOptions.deliverymode

    This write-only attribute specifies what types of messages should be
    dequeued. It should be one of the values :data:`~oracledb.MSG_PERSISTENT`
    (default), :data:`~oracledb.MSG_BUFFERED` or
    :data:`~oracledb.MSG_PERSISTENT_OR_BUFFERED`.


.. attribute:: DeqOptions.mode

    This read-write attribute specifies the locking behaviour associated
    with the dequeue operation. It should be one of the values
    :data:`~oracledb.DEQ_BROWSE`,
    :data:`~oracledb.DEQ_LOCKED`,
    :data:`~oracledb.DEQ_REMOVE` (default), or
    :data:`~oracledb.DEQ_REMOVE_NODATA`.


.. attribute:: DeqOptions.msgid

    This read-write attribute specifies the identifier of the message to be
    dequeued. The default is to have no message identifier specified.


.. attribute:: DeqOptions.navigation

    This read-write attribute specifies the position of the message that
    is retrieved. It should be one of the values :data:`~oracledb.DEQ_FIRST_MSG`,
    :data:`~oracledb.DEQ_NEXT_MSG` (default), or
    :data:`~oracledb.DEQ_NEXT_TRANSACTION`.


.. attribute:: DeqOptions.transformation

    This read-write attribute specifies the name of the transformation that must
    be applied after the message is dequeued from the database but before it is
    returned to the calling application. The transformation must be created
    using dbms_transform. The default is to have no transformation specified.


.. attribute:: DeqOptions.visibility

    This read-write attribute specifies the transactional behavior of the dequeue
    request. It should be one of the values :data:`~oracledb.DEQ_ON_COMMIT` (default)
    or :data:`~oracledb.DEQ_IMMEDIATE`. This attribute is ignored when using
    the :data:`~oracledb.DEQ_BROWSE` mode. Note the value of
    :attr:`~Connection.autocommit` is always ignored.


.. attribute:: DeqOptions.wait

    This read-write attribute specifies the time to wait, in seconds, for a message
    matching the search criteria to become available for dequeuing. One of the
    values :data:`~oracledb.DEQ_NO_WAIT` or
    :data:`~oracledb.DEQ_WAIT_FOREVER` can also be used. The default is
    :data:`~oracledb.DEQ_WAIT_FOREVER`.


.. _enqoptions:

Enqueue Options
===============

These objects are used to configure how messages are enqueued into queues. An
instance of this object is found in the attribute :attr:`Queue.enqOptions`.

.. dbapiobjectextension::

.. attribute:: EnqOptions.deliverymode

    This write-only attribute specifies what type of messages should be
    enqueued. It should be one of the values :data:`~oracledb.MSG_PERSISTENT`
    (default) or :data:`~oracledb.MSG_BUFFERED`.


.. attribute:: EnqOptions.transformation

    This read-write attribute specifies the name of the transformation that
    must be applied before the message is enqueued into the database. The
    transformation must be created using dbms_transform. The default is to have
    no transformation specified.


.. attribute:: EnqOptions.visibility

    This read-write attribute specifies the transactional behavior of the enqueue
    request. It should be one of the values :data:`~oracledb.ENQ_ON_COMMIT` (default)
    or :data:`~oracledb.ENQ_IMMEDIATE`. Note the value of
    :attr:`~Connection.autocommit` is ignored.


.. _msgproperties:

Message Properties
==================

These objects are used to identify the properties of messages that are enqueued
and dequeued in queues. They are created by the method
:meth:`Connection.msgproperties()`.  They are used by the methods
:meth:`Queue.enqone()` and :meth:`Queue.enqmany()` and returned by the methods
:meth:`Queue.deqone()` and :meth:`Queue.deqmany()`.

.. dbapiobjectextension::

.. attribute:: MessageProperties.attempts

    This read-only attribute specifies the number of attempts that have been
    made to dequeue the message.


.. attribute:: MessageProperties.correlation

    This read-write attribute specifies the correlation used when the message
    was enqueued.


.. attribute:: MessageProperties.delay

    This read-write attribute specifies the number of seconds to delay an
    enqueued message. Any integer is acceptable but the constant
    :data:`~oracledb.MSG_NO_DELAY` can also be used indicating that the
    message is available for immediate dequeuing.


.. attribute:: MessageProperties.deliverymode

    This read-only attribute specifies the type of message that was dequeued.
    It will be one of the values :data:`~oracledb.MSG_PERSISTENT` or
    :data:`~oracledb.MSG_BUFFERED`.


.. attribute:: MessageProperties.enqtime

    This read-only attribute specifies the time that the message was enqueued.


.. attribute:: MessageProperties.exceptionq

    This read-write attribute specifies the name of the queue to which the message
    is moved if it cannot be processed successfully. Messages are moved if the
    number of unsuccessful dequeue attempts has exceeded the maximum number of
    retries or if the message has expired. All messages in the exception queue
    are in the :data:`~oracledb.MSG_EXPIRED` state. The default value is the
    name of the exception queue associated with the queue table.


.. attribute:: MessageProperties.expiration

    This read-write attribute specifies, in seconds, how long the message is
    available for dequeuing. This attribute is an offset from the delay attribute.
    Expiration processing requires the queue monitor to be running. Any integer is
    accepted but the constant :data:`~oracledb.MSG_NO_EXPIRATION` can also be
    used indicating that the message never expires.


.. attribute:: MessageProperties.msgid

    This read-only attribute specifies the id of the message in the last queue
    that enqueued or dequeued the message. If the message has never been
    dequeued or enqueued, the value will be *None*.


.. attribute:: MessageProperties.payload

    This read-write attribute identifies the payload that will be enqueued or the
    payload that was dequeued when using a :ref:`queue <queue>`. When enqueuing,
    the value is checked to ensure that it conforms to the type expected by that
    queue. For RAW queues, the value can be a bytes object or a string. If the
    value is a string it will first be converted to bytes in the encoding UTF-8.


.. attribute:: MessageProperties.priority

    This read-write attribute specifies the priority of the message. A smaller
    number indicates a higher priority. The priority can be any integer, including
    negative numbers. The default value is *0*.


.. attribute:: MessageProperties.state

    This read-only attribute specifies the state of the message at the time of
    the dequeue. It will be one of the values :data:`~oracledb.MSG_WAITING`,
    :data:`~oracledb.MSG_READY`, :data:`~oracledb.MSG_PROCESSED` or
    :data:`~oracledb.MSG_EXPIRED`.

.. attribute:: MessageProperties.recipients

    This read-write attribute specifies a list of recipient names that can be
    associated with a message at the time of enqueuing the message. This allows a
    limited set of recipients to dequeue each message. The recipient list associated
    with the message overrides the queue subscriber list, if there is one. The
    recipient names need not be in the subscriber list but can be, if desired.

    To dequeue a message, the consumername attribute can be set to one of
    the recipient names. The original message recipient list is not
    available on dequeued messages. All recipients have to dequeue a
    message before it gets removed from the queue.
