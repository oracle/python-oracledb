.. _aqusermanual:

.. currentmodule:: oracledb

************************************************************
Using Oracle Transactional Event Queues and Advanced Queuing
************************************************************

`Oracle Transactional Event Queues and Advanced Queuing
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=ADQUE>`__ are highly
configurable and scalable messaging features of Oracle Database allowing
data-driven and event-driven applications to stream events and communicate with
each other. They have interfaces in various languages, letting you integrate
multiple tools in your architecture. Both Oracle Transactional Event Queues
(TxEventQ) and Advanced Queuing (AQ) "Classic" queues support sending and
receiving of various payloads, such as RAW values, JSON, JMS, and objects.
Transactional Event Queues use a highly optimized implementation of Advanced
Queuing. They were previously called AQ Sharded Queues.

.. note::

    Transactional Event Queues with JMS payloads are only supported in
    python-oracledb :ref:`Thick mode <enablingthick>`.

Python-oracledb API calls are the same for Transactional Event Queues and
Classic Queues, however there are differences in support for some payload
types which are detailed below.

.. list-table-with-summary:: Payload Differences Between Classic Queues and Transactional Event Queues
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 10 20 20
    :summary: The first column displays the payload type. The second column displays whether the payload type is supported in Classic Queues. The third column displays whether the payload type is supported in Transactional Event Queues.

    * - Payload Type
      - Classic Queues
      - Transactional Event Queues
    * - RAW
      - Supported
      - Supported for single and array message enqueuing and dequeuing when using Oracle Database 19c (or later). In python-oracledb Thick mode, Oracle Client libraries 19c (or later) are needed.
    * - Named Oracle Objects
      - Supported
      - Supported for single and array message enqueuing and dequeuing when using Oracle Database 19c (or later). In python-oracledb Thick mode, Oracle Client libraries 19c (or later) are needed.
    * - JSON
      - Supported when using Oracle Database 21c (or later). In python-oracle Thick mode, Oracle Client libraries 21c (or later) are also needed.

        Buffered messaging using the :data:`~oracledb.MSG_BUFFERED` delivery mode is not supported for JSON payloads.
      - Supported for single and array message enqueuing and dequeuing when using Oracle Database 21c (or later). In python-oracledb Thick mode, Oracle Client libraries 21c (or later) are needed.

        Buffered messaging using the :data:`~oracledb.MSG_BUFFERED` delivery mode is not supported for JSON payloads.
    * - JMS
      - Supported
      - Supported for single and array message enqueuing and dequeuing when using Oracle Client 19 (or later) and Oracle Database version 23 (or later).

**Usage Notes**

For Classic Queues and Transactional Event Queues, the use of
:data:`oracledb.ENQ_IMMEDIATE` with bulk enqueuing, and JMS payloads are only
supported in python-oracledb :ref:`Thick mode <enablingthick>`.

The ``payload_type`` parameter in :meth:`Connection.queue()` must be
specified when the payload is JSON or Named Oracle Objects. This parameter need
not be specified for RAW payloads.

Transactional Event Queues do not support :attr:`EnqOptions.transformation`,
:attr:`DeqOptions.transformation`, or :ref:`Recipient Lists <reciplists>`.

The delivery mode :data:`oracledb.MSG_BUFFERED` is not supported for bulk array
operations in python-oracledb Thick mode.

There are examples of AQ Classic Queues in the `GitHub samples
<https://github.com/oracle/python-oracledb/tree/main/samples>`__ directory.

Creating a Queue
================

Before being used in applications, queues need to be created in the database.

To experiment with queueing, you can grant yourself privileges, for example in
SQL*Plus as a DBA user:

.. code-block:: sql

    grant aq_administrator_role, aq_user_role to &&username;
    grant execute on dbms_aq to &&username;

**Creating RAW Payload Queues**

To use SQL*Plus to create a Classic Queue for the RAW payload which is suitable
for sending string or bytes messages:

.. code-block:: sql

    begin
        dbms_aqadm.create_queue_table('MY_QUEUE_TABLE', 'RAW');
        dbms_aqadm.create_queue('DEMO_RAW_QUEUE', 'MY_QUEUE_TABLE');
        dbms_aqadm.start_queue('DEMO_RAW_QUEUE');
    end;
    /

To create a Transactional Event Queue for RAW payloads:

.. code-block:: sql

    begin
        dbms_aqadm.create_sharded_queue('RAW_SHQ', queue_payload_type=>'RAW');
        dbms_aqadm.start_queue('RAW_SHQ');
    end;
    /

**Creating JSON Payload Queues**

Queues can also be created for JSON payloads. For example, to create a Classic
Queue in SQL*Plus:

.. code-block:: sql

    begin
        dbms_aqadm.create_queue_table('JSON_QUEUE_TABLE', 'JSON');
        dbms_aqadm.create_queue('DEMO_JSON_QUEUE', 'JSON_QUEUE_TABLE');
        dbms_aqadm.start_queue('DEMO_JSON_QUEUE');
    end;
    /

Enqueuing Messages
==================

To send messages in Python, you connect and get a :ref:`queue <queue>`. The
queue can then be used for enqueuing, dequeuing, or for both.

**Enqueuing RAW Payloads**

You can connect to the database and get the queue that was created with RAW
payload type by using :meth:`Connection.queue()` or
:meth:`AsyncConnection.queue()`. For example:

.. code-block:: python

    queue = connection.queue("DEMO_RAW_QUEUE")

Now messages can be queued using :meth:`Queue.enqone()` or
:meth:`AsyncQueue.enqone()`.  For example, to send three messages:

.. code-block:: python

    PAYLOAD_DATA = [
        "The first message",
        "The second message",
        "The third message"
    ]
    for data in PAYLOAD_DATA:
        queue.enqone(connection.msgproperties(payload=data))
    connection.commit()

Since the queue is a RAW queue, strings are internally encoded to bytes using
`encode() <https://docs.python.org/3/library/stdtypes.html#str.encode>`__
before being enqueued.

The use of :meth:`Connection.commit()` or :meth:`AsyncConnection.commit()`
allows messages to be sent only when any database transaction related to them
is committed. This default behavior can be altered, see :ref:`aqoptions`.

**Enqueuing JSON Payloads**

You can connect to the database and get the queue that was created with JSON
payload type by using :meth:`Connection.queue()` or
:meth:`AsyncConnection.queue()`. For example:

.. code-block:: python

    # The argument "JSON" indicates the queue is of JSON payload type
    queue = connection.queue("DEMO_JSON_QUEUE", "JSON")

Now the message can be enqueued using :meth:`Queue.enqone()` or
:meth:`AsyncQueue.enqone()`, for example:

.. code-block:: python

    json_data = [
        [
            2.75,
            True,
            'Ocean Beach',
            b'Some bytes',
            {'keyA': 1.0, 'KeyB': 'Melbourne'},
            datetime.datetime(2022, 8, 1, 0, 0)
        ],
        dict(name="John", age=30, city="New York")
    ]
    for data in json_data:
        queue.enqone(connection.msgproperties(payload=data))
    connection.commit()

Dequeuing Messages
==================

Dequeuing is performed similarly as shown in the examples below. This returns a
:ref:`MessageProperties <msgproperties>` object containing the message payload
and related attributes.

**Dequeuing RAW Payloads**

To dequeue a message, call the method :meth:`Queue.deqone()` or
:meth:`AsyncQueue.deqone()`. For example:

.. code-block:: python

    queue = connection.queue("DEMO_RAW_QUEUE")
    message = queue.deqOne()
    connection.commit()
    print(message.payload.decode())

Note that if the message is expected to be a string, the bytes must be decoded
by the application using `decode()
<https://docs.python.org/3/library/stdtypes.html#bytes.decode>`__, as shown.

If there are no messages in the queue, :meth:`Queue.deqone()` or
:meth:`AsyncQueue.deqone()` will wait for one to be enqueued.  This default
behavior can be altered, see :ref:`aqoptions`.

Various :ref:`message properties <msgproperties>` can be accessed.  For example
to show the :attr:`~MessageProperties.msgid` of a dequeued message:

.. code-block:: python

    print(message.msgid.hex())

**Dequeuing JSON Payloads**

To dequeue a message, call the method :meth:`Queue.deqone()` or
:meth:`AsyncQueue.deqone()`, for example:

.. code-block:: python

    queue = connection.queue("DEMO_JSON_QUEUE", "JSON")
    message = queue.deqOne()
    connection.commit()

Using Object Queues
===================

Named Oracle objects can be enqueued and dequeued as well.  Given an object
type called ``UDT_BOOK``:

.. code-block:: sql

    CREATE OR REPLACE TYPE udt_book AS OBJECT (
        Title   VARCHAR2(100),
        Authors VARCHAR2(100),
        Price   NUMBER(5,2)
    );
    /

And a queue that accepts this type:

.. code-block:: sql

    begin
        dbms_aqadm.create_queue_table('BOOK_QUEUE_TAB', 'UDT_BOOK');
        dbms_aqadm.create_queue('DEMO_BOOK_QUEUE', 'BOOK_QUEUE_TAB');
        dbms_aqadm.start_queue('DEMO_BOOK_QUEUE');
    end;
    /

You can enqueue messages using :meth:`Queue.enqone()` or
:meth:`AsyncQueue.enqone()`, for example:

.. code-block:: python

    book_type = connection.gettype("UDT_BOOK")
    queue = connection.queue("DEMO_BOOK_QUEUE", book_type)

    book = book_type.newobject()
    book.TITLE = "Quick Brown Fox"
    book.AUTHORS = "The Dog"
    book.PRICE = 123

    queue.enqone(connection.msgproperties(payload=book))
    connection.commit()

Dequeuing can be done with :meth:`Queue.deqone()` or
:meth:`AsyncQueue.deqone()`, for example:

.. code-block:: python

    book_type = connection.gettype("UDT_BOOK")
    queue = connection.queue("DEMO_BOOK_QUEUE", book_type)

    message = queue.deqone()
    connection.commit()
    print(message.payload.TITLE)   # will print Quick Brown Fox

.. _reciplists:

Using Recipient Lists
=====================

Classic Queues support Recipient Lists.  A list of recipient names can be
associated with a message at the time a message is enqueued. This allows a
limited set of recipients to dequeue each message. The recipient list
associated with the message overrides the queue subscriber list, if there is
one. The recipient names need not be in the subscriber list but can be, if
desired.  Transactional Event Queues do not support Recipient Lists.

To dequeue a message, the :attr:`~DeqOptions.consumername` attribute can be
set to one of the recipient names. The original message recipient list is
not available on dequeued messages. All recipients have to dequeue
a message before it gets removed from the queue.

Subscribing to a queue is like subscribing to a magazine: each
subscriber can dequeue all the messages placed into a specific queue,
just as each magazine subscriber has access to all its articles.
However, being a recipient is like getting a letter: each recipient
is a designated target of a particular message.

For example::

    props = self.connection.msgproperties(payload=book,recipients=["sub2", "sub3"])
    queue.enqone(props)

Later, when dequeuing messages, a specific recipient can be set to get the
messages intended for that recipient using the ``consumername`` attribute::

    queue.deqoptions.consumername = "sub3"
    m = queue.deqone()

.. _aqoptions:

Changing Queue and Message Options
==================================

Refer to the :ref:`python-oracledb AQ API <aq>` and
`Oracle Advanced Queuing documentation
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=ADQUE>`__ for details
on all of the enqueue and dequeue options available.

Enqueue options can be set.  For example, to make it so that an explicit call
to :meth:`~Connection.commit()` on the connection is not needed to send
messages:

.. code-block:: python

    queue = connection.queue("DEMO_RAW_QUEUE")
    queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE

Dequeue options can also be set.  For example, to specify not to block on
dequeuing if no messages are available:

.. code-block:: python

    queue = connection.queue("DEMO_RAW_QUEUE")
    queue.deqoptions.wait = oracledb.DEQ_NO_WAIT

Message properties can be set when enqueuing.  For example, to set an
expiration of 60 seconds on a message:

.. code-block:: python

    queue.enqone(connection.msgproperties(payload="Message", expiration=60))

This means that if no dequeue operation occurs within 60 seconds then the
message will be dropped from the queue.

.. _bulkenqdeq:

Bulk Enqueue and Dequeue
========================

The :meth:`Queue.enqmany()`, :meth:`Queue.deqmany()`,
:meth:`AsyncQueue.enqmany()`, and :meth:`AsyncQueue.deqmany()` methods can be
used for efficient bulk message handling.

The bulk enqmany methods are similar to single message enqueue methods but
accept an array of messages, for example:

.. code-block:: python

    messages = [
        "The first message",
        "The second message",
        "The third message",
    ]
    queue = connection.queue("DEMO_RAW_QUEUE")
    queue.enqmany(connection.msgproperties(payload=m) for m in messages)
    connection.commit()

.. warning::

    In python-oracledb Thick mode using Oracle Client libraries prior to 21c,
    calling :meth:`Queue.enqmany()` in parallel on different connections
    acquired from the same connection pool may fail due to Oracle
    bug 29928074. To avoid this, do one of: upgrade the client libraries,
    ensure that :meth:`Queue.enqmany()` is not run in parallel, use standalone
    connections or connections from different pools, or make multiple calls to
    :meth:`Queue.enqone()`. The function :meth:`Queue.deqmany()` call is not
    affected.

To dequeue multiple messages at one time, use :meth:`Queue.deqmany()` or
:meth:`AsyncQueue.deqmany()`.  These take an argument specifying the maximum
number of messages to dequeue at one time, for example:

.. code-block:: python

    for message in queue.deqmany(10):
        print(message.payload.decode())

Depending on the queue properties and the number of messages available to
dequeue, this code will print out from zero to ten messages.
