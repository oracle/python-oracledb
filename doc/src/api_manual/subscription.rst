.. _subscrobj:

*************************
API: Subscription Objects
*************************

.. currentmodule:: oracledb

.. dbapiobjectextension::

Subscription Class
==================

.. autoclass:: Subscription

    A Subscription object should be created using
    :meth:`Connection.subscribe()`. See :ref:`cqn` for more information.

Subscription Methods
--------------------

.. automethod:: Subscription.registerquery

Subscription Attributes
-----------------------

.. autoproperty:: Subscription.callback

.. autoproperty:: Subscription.connection

.. autoproperty:: Subscription.id

.. autoproperty:: Subscription.ip_address

    For consistency and compliance with the PEP 8 naming style, the
    attribute ``ipAddress`` was renamed to ``ip_address``. The old name will
    continue to work for a period of time.

.. autoproperty:: Subscription.name

.. autoproperty:: Subscription.namespace

.. autoproperty:: Subscription.operations

.. autoproperty:: Subscription.port

.. autoproperty:: Subscription.protocol

.. autoproperty:: Subscription.qos

.. autoproperty:: Subscription.timeout

.. _msgobjects:

Message Class
=============

.. autoclass:: Message

    A Message object is created when a notification is received. They are
    passed to the callback procedure specified when a subscription is created.

Message Attributes
------------------

.. autoproperty:: Message.consumer_name

    For consistency and compliance with the PEP 8 naming style, the
    attribute ``consumerName`` was renamed to ``consumer_name``. The old name
    will continue to work for a period of time.

.. autoproperty:: Message.dbname

.. autoproperty:: Message.msgid

.. autoproperty:: Message.queries

.. autoproperty:: Message.queue_name

    For consistency and compliance with the PEP 8 naming style, the
    attribute ``queueName`` was renamed to ``queue_name``. The old name will
    continue to work for a period of time.

.. autoproperty:: Message.registered

.. autoproperty:: Message.subscription

.. autoproperty:: Message.tables

.. autoproperty:: Message.txid

.. autoproperty:: Message.type

    See the constants section on :ref:`eventtypes` for additional information.

MessageTable Class
==================

.. autoclass:: MessageTable

    A MessageTable object is created when a notification is received for each
    table change. They are accessed in the tables attribute of message
    objects, and the tables attribute of message query objects.

.. autoproperty:: MessageTable.name

.. autoproperty:: MessageTable.operation

.. autoproperty:: MessageTable.rows

MessageRow Class
================

.. autoclass:: MessageRow

    A MessageRow object is created when a notification is received for each
    row changed in a table. They are found in the rows attribute of message
    table objects.

MessageRow Attributes
---------------------

.. autoproperty:: MessageRow.operation

.. autoproperty:: MessageRow.rowid

MessageQuery Class
==================

.. autoclass:: MessageQuery

    A MessageQuery object is created when a notification is received for a
    query result set change. This object is found in the queries attribute of
    message objects.

.. autoproperty:: MessageQuery.id

.. autoproperty:: MessageQuery.operation

.. autoproperty:: MessageQuery.tables
