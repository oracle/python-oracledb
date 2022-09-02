.. _aqusermanual:

***********************************
Using Oracle Advanced Queuing (AQ)
***********************************

`Oracle Advanced Queuing
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=ADQUE>`__ is a highly
configurable and scalable messaging feature of Oracle Database.  It has
interfaces in various languages, letting you integrate multiple tools in your
architecture.

.. note::

    Oracle Advanced Queuing is only supported in the python-oracledb Thick
    mode.  See :ref:`enablingthick`.

Python-oracledb uses the updated interface for Oracle Advanced Queuing that
was first introduced in cx_Oracle 7.2.

Starting from Oracle Database 21c, Advanced Queuing also supports the JSON
payload type. To use the JSON payload type, the Oracle Client libraries must
be version 21 or later.

There are Advanced Queuing examples in the `GitHub examples
<https://github.com/oracle/python-oracledb/tree/main/samples>`__ directory.


Creating a Queue
================

Before being used, queues need to be created in the database.

**Using RAW Payloads**

Queues can be created using the RAW payload type, for example in
SQL*Plus:

.. code-block:: sql

    begin
        dbms_aqadm.create_queue_table('MY_QUEUE_TABLE', 'RAW');
        dbms_aqadm.create_queue('DEMO_RAW_QUEUE', 'MY_QUEUE_TABLE');
        dbms_aqadm.start_queue('DEMO_RAW_QUEUE');
    end;
    /

This example creates a RAW queue suitable for sending string or bytes
messages.

**Using JSON Payloads**

Also, queues can be created using the JSON payload type. For example,
in SQL*Plus:

.. code-block:: sql

    begin
        dbms_aqadm.create_queue_table('JSON_QUEUE_TABLE', 'JSON');
        dbms_aqadm.create_queue('DEMO_JSON_QUEUE', 'JSON_QUEUE_TABLE');
        dbms_aqadm.start_queue('DEMO_JSON_QUEUE');
    end;
    /

This example creates a JSON queue suitable for sending JSON data
messages.

Enqueuing Messages
==================

To send messages in Python, you connect and get a :ref:`queue <queue>`. The
queue can be used for enqueuing, dequeuing, or both as needed.

**Using RAW Payloads**

You can connect to the database and get the queue that was created with RAW
payload type by using:

.. code-block:: python

    queue = connection.queue("DEMO_RAW_QUEUE")

Now messages can be queued using :meth:`~Queue.enqone()`.  To send three
messages:

.. code-block:: python

    PAYLOAD_DATA = [
        "The first message",
        "The second message",
        "The third message"
    ]
    for data in PAYLOAD_DATA:
        queue.enqone(connection.msgproperties(payload=data))
    connection.commit()

Since the queue sending the messages is a RAW queue, the strings in this
example will be internally encoded to bytes using ``message.encode()``
before being enqueued.

**Using JSON Payloads**

You can connect to the database and get the queue that was created with JSON
payload type by using:

.. code-block:: python

    queue = connection.queue("DEMO_JSON_QUEUE", "JSON")
    # The second argument (JSON) indicates that the queue is of JSON payload type.

Now the message can be enqueued using :meth:`~Queue.enqone()`.

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

Dequeuing is performed similarly. To dequeue a message call the method
:meth:`~Queue.deqone()` as shown in the examples below.

**Using RAW Payload Type**

.. code-block:: python

    queue = connection.queue("DEMO_RAW_QUEUE")
    message = queue.deqOne()
    connection.commit()
    print(message.payload.decode())

Note that if the message is expected to be a string, the bytes must
be decoded using ``message.payload.decode()``, as shown.

**Using JSON Payload Type**

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

You can queue messages:

.. code-block:: python

    book_type = connection.gettype("UDT_BOOK")
    queue = connection.queue("DEMO_BOOK_QUEUE", book_type)

    book = book_type.newobject()
    book.TITLE = "Quick Brown Fox"
    book.AUTHORS = "The Dog"
    book.PRICE = 123

    queue.enqone(connection.msgproperties(payload=book))
    connection.commit()

Dequeuing is done like this:

.. code-block:: python

    book_type = connection.gettype("UDT_BOOK")
    queue = connection.queue("DEMO_BOOK_QUEUE", book_type)

    message = queue.deqone()
    connection.commit()
    print(message.payload.TITLE)   # will print Quick Brown Fox


Using Recipient Lists
=====================

A list of recipient names can be associated with a message at the time
a message is enqueued. This allows a limited set of recipients to
dequeue each message. The recipient list associated with the message
overrides the queue subscriber list, if there is one. The recipient
names need not be in the subscriber list but can be, if desired.

To dequeue a message, the ``consumername`` attribute can be set to
one of the recipient names. The original message recipient list is
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

Changing Queue and Message Options
==================================

Refer to the :ref:`python-oracledb AQ API <aq>` and
`Oracle Advanced Queuing documentation
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=ADQUE>`__ for details
on all of the enqueue and dequeue options available.

Enqueue options can be set.  For example, to make it so that an explicit
call to :meth:`~Connection.commit()` on the connection is not needed to commit
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

This means that if no dequeue operation occurs within 60 seconds that the
message will be dropped from the queue.


Bulk Enqueue and Dequeue
========================

The :meth:`~Queue.enqmany()` and :meth:`~Queue.deqmany()` methods can be used
for efficient bulk message handling.

:meth:`~Queue.enqmany()` is similar to :meth:`~Queue.enqone()` but accepts an
array of messages:

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

    Calling :meth:`~Queue.enqmany()` in parallel on different connections
    acquired from the same pool may fail due to Oracle bug 29928074.  Ensure
    that this function is not run in parallel, use standalone connections or
    connections from different pools, or make multiple calls to
    :meth:`~Queue.enqone()` instead. The function :meth:`~Queue.deqmany()` call
    is not affected.

To dequeue multiple messages at one time, use :meth:`~Queue.deqmany()`.  This
takes an argument specifying the maximum number of messages to dequeue at one
time:

.. code-block:: python

    for message in queue.deqmany(10):
        print(message.payload.decode())

Depending on the queue properties and the number of messages available to
dequeue, this code will print out from zero to ten messages.
