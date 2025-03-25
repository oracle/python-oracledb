.. _subscrobj:

*************************
API: Subscription Objects
*************************

.. dbapiobjectextension::

Subscription Methods
====================

.. method:: Subscription.registerquery(statement, [args])

    Registers the query for subsequent notification when tables referenced by
    the query are changed. This behaves similarly to :meth:`Cursor.execute()`
    but only queries are permitted and the ``args`` parameter must be a
    sequence or dictionary.  If the ``qos`` parameter included the flag
    :data:`oracledb.SUBSCR_QOS_QUERY` when the subscription was created, then
    the ID for the registered query is returned; otherwise, *None* is returned.

Subscription Attributes
=======================

.. attribute:: Subscription.callback

    This read-only attribute returns the callback that was registered when the
    subscription was created.


.. attribute:: Subscription.connection

    This read-only attribute returns the connection that was used to register
    the subscription when it was created.


.. attribute:: Subscription.id

    This read-only attribute returns the value of the REGID column found in the
    database view USER_CHANGE_NOTIFICATION_REGS or the value of the REG_ID
    column found in the database view USER_SUBSCR_REGISTRATIONS. For AQ
    subscriptions, the value is *0*.


.. attribute:: Subscription.ip_address

    This read-only attribute returns the IP address used for callback
    notifications from the database server. If not set during construction,
    this value is *None*.

    For consistency and compliance with the PEP 8 naming style, the
    attribute ``ipAddress`` was renamed to ``ip_address``. The old name will
    continue to work for a period of time.


.. attribute:: Subscription.name

    This read-only attribute returns the name used to register the subscription
    when it was created.


.. attribute:: Subscription.namespace

    This read-only attribute returns the namespace used to register the
    subscription when it was created.


.. attribute:: Subscription.operations

    This read-only attribute returns the operations that will send
    notifications for each table or query that is registered using this
    subscription.


.. attribute:: Subscription.port

    This read-only attribute returns the port used for callback notifications
    from the database server. If not set during construction, this value is
    *0*.


.. attribute:: Subscription.protocol

    This read-only attribute returns the protocol used to register the
    subscription when it was created.


.. attribute:: Subscription.qos

    This read-only attribute returns the quality of service flags used to
    register the subscription when it was created.


.. attribute:: Subscription.timeout

    This read-only attribute returns the timeout (in seconds) that was
    specified when the subscription was created. A value of *0* indicates that
    there is no timeout.


.. _msgobjects:

Message Objects
---------------

Message objects are created when a notification is received. They are passed to
the callback procedure specified when a subscription is created.

.. attribute:: Message.consumer_name

    This read-only attribute returns the name of the consumer which generated
    the notification. It will be populated if the subscription was created with
    the namespace :data:`oracledb.SUBSCR_NAMESPACE_AQ` and the queue is a
    multiple consumer queue.

    For consistency and compliance with the PEP 8 naming style, the
    attribute ``consumerName`` was renamed to ``consumer_name``. The old name
    will continue to work for a period of time.


.. attribute:: Message.dbname

    This read-only attribute returns the name of the database that generated
    the notification.

.. attribute:: Message.msgid

    This read-only attribute returns the message id of the AQ message which
    generated the notification. It will only be populated if the subscription
    was created with the namespace :data:`oracledb.SUBSCR_NAMESPACE_AQ`.

.. attribute:: Message.queries

    This read-only attribute returns a list of message query objects that give
    information about query result sets changed for this notification. This
    attribute will be an empty list if the ``qos`` parameter did not include
    the flag :data:`~oracledb.SUBSCR_QOS_QUERY` when the subscription was
    created.


.. attribute:: Message.queue_name

    This read-only attribute returns the name of the queue which generated the
    notification. It will only be populated if the subscription was created
    with the namespace :data:`oracledb.SUBSCR_NAMESPACE_AQ`.

    For consistency and compliance with the PEP 8 naming style, the
    attribute ``queueName`` was renamed to ``queue_name``. The old name will
    continue to work for a period of time.


.. attribute:: Message.registered

    This read-only attribute returns whether the subscription which generated
    this notification is still registered with the database. The subscription
    is automatically deregistered with the database when the subscription
    timeout value is reached or when the first notification is sent (when the
    quality of service flag :data:`oracledb.SUBSCR_QOS_DEREG_NFY` is used).


.. attribute:: Message.subscription

    This read-only attribute returns the subscription object for which this
    notification was generated.


.. attribute:: Message.tables

    This read-only attribute returns a list of message table objects that give
    information about the tables changed for this notification. This
    attribute will be an empty list if the ``qos`` parameter included the flag
    :data:`~oracledb.SUBSCR_QOS_QUERY` when the subscription was created.


.. attribute:: Message.txid

    This read-only attribute returns the id of the transaction that generated
    the notification.


.. attribute:: Message.type

    This read-only attribute returns the type of message that has been sent.
    See the constants section on event types for additional information.


MessageTable Objects
--------------------

MessageTable objects are created when a notification is received for each table
change. They are accessed in the tables attribute of message objects, and the
tables attribute of message query objects.


.. attribute:: MessageTable.name

    This read-only attribute returns the name of the table that was changed.


.. attribute:: MessageTable.operation

    This read-only attribute returns the operation that took place on the table
    that was changed.


.. attribute:: MessageTable.rows

    This read-only attribute returns a list of message row objects that give
    information about the rows changed on the table. This value is only filled
    in if the ``qos`` parameter to the :meth:`Connection.subscribe()` method
    included the flag :data:`~oracledb.SUBSCR_QOS_ROWIDS`.


MessageRow Objects
------------------

MessageRow objects are created when a notification is received for each row
changed in a table. They are found in the rows attribute of message table
objects.


.. attribute:: MessageRow.operation

    This read-only attribute returns the operation that took place on the row
    that was changed.


.. attribute:: MessageRow.rowid

    This read-only attribute returns the rowid of the row that was changed.


MessageQuery Objects
--------------------

A MessageQuery object is created when a notification is received for a query
result set change. This object is found in the queries attribute of message
objects.


.. attribute:: MessageQuery.id

    This read-only attribute returns the query id of the query for which the
    result set changed. The value will match the value returned by
    :meth:`Subscription.registerquery()` when the related query was registered.


.. attribute:: MessageQuery.operation

    This read-only attribute returns the operation that took place on the query
    result set that was changed. Valid values for this attribute are
    :data:`~oracledb.EVENT_DEREG` and :data:`~oracledb.EVENT_QUERYCHANGE`.


.. attribute:: MessageQuery.tables

    This read-only attribute returns a list of message table objects that give
    information about the table changes that caused the query result set to
    change for this notification.
