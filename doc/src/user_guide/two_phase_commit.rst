.. _tpc:

.. currentmodule:: oracledb

*****************************
Using Two-Phase Commits (TPC)
*****************************

The python-oracledb functions :meth:`~Connection.tpc_begin()` and
:meth:`~Connection.tpc_end()` support distributed transactions. See `Two-Phase
Commit Mechanism <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
GUID-8152084F-4760-4B89-A91C-9A84F81C23D1>`_ in the Oracle Database
documentation.

The method :meth:`Connection.tpc_begin()` can be used to start a TPC
transaction.

Distributed transaction protocols attempt to keep multiple data sources
consistent with one another by ensuring updates to the data sources
participating in a distributed transaction are all performed, or none of
them performed. These data sources, also called participants or resource
managers, may be traditional database systems, messaging systems, and
other systems that store state such as caches. A common class of
distributed transaction protocols are referred to as two-phase commit
protocols. These protocols split the commitment of a distributed
transaction into two distinct, separate phases.

During the first phase, the participants (data sources) are polled or
asked to vote on the outcome of the distributed transaction. This phase,
called the prepare phase, ensures agreement or consensus on the ability
for each participant to commit their portion of the transaction. When
asked to prepare, the participants respond positively if they can commit
their portion of the distributed transaction when requested or respond
that there were no changes, so they have no need to be committed. Once
all participants have responded to the first phase, the second phase of
the protocol can begin. The method :meth:`Connection.tpc_prepare()` can
be used to prepare a global transaction for commit.

During the second phase of the protocol, called the commit phase, all of
the participants that indicated they needed to be committed are asked to
either commit their prepared changes or roll them back. If the decision on
the outcome of the distributed transaction was to commit the transaction,
each participant is asked to commit their changes. If the decision was to
abort or rollback the distributed transaction, each participant is asked
to rollback their changes. The methods :meth:`Connection.tpc_commit()` and
:meth:`Connection.tpc_rollback()` can be used to commit or rollback a
transaction respectively.

While applications can coordinate these activities, it takes on additional
responsibilities to ensure the correct outcome of all participants, even in
the face of failures. These failures could be of the application itself, one
of the participants in the transaction, of communication links, etc. In order
to assure the atomic characteristics of a distributed transaction, once the
decision has been made to commit the distributed transaction, this decision
needs to be durably recorded in case of failure. The application, as part of
its steps for recovery from a failure, now needs to check the durable log and
notify the participants of the outcome. Failures may be nested such that not
only might the application fail, one or more participants or connections to
participants might fail. All these scenarios require careful consideration
and remediation to ensure that all participants either committed or rolled
back their local updates.

As a result, most applications rely upon the services provided by a
transaction manager (TM), also called a transaction coordinator. The purpose
of having a transaction manager perform this coordination is to eliminate
having to have each application perform these transaction management functions.
The application asks the transaction manager to start a transaction. As
additional participants or resource managers join the transaction, they register
with the transaction manager as participants. When the original application decides
the transaction is to be committed or rolled back, it asks the transaction manager
to commit or rollback the transaction. If the application asked the transaction to
be rolled back, the transaction coordinator notifies all participants to roll back.
Otherwise, the transaction manager then starts the two-phase commit protocol.

The following example shows how to perform an application level two-phase commit:

.. code-block:: python

    import oracledb

    # connect to first database and begin transaction
    conn1 = oracledb.connect(DSN1)
    xid1 = conn1.xid(1000, "txn1", "branch1")
    conn1.tpc_begin(xid1)
    with conn1.cursor() as cursor:
        cursor.execute("insert into SomeTable values (1, 'Some value')")

    # connect to second database and begin transaction
    conn2 = oracledb.connect(DSN2)
    xid2 = conn1.xid(1000, "txn1", "branch2")
    conn2.tpc_begin(xid2)
    with conn2.cursor() as cursor:
        cursor.execute("insert into SomeOtherTable values (2, 'Some value')")

    # prepare both transactions and commit
    commit_needed1 = conn1.tpc_prepare()
    commit_needed2 = conn2.tpc_prepare()
    if commit_needed1:
        conn1.tpc_commit()
    if commit_needed2:
        conn2.tpc_commit()


The following example shows how to perform recovery.

.. code-block:: python

    import oracledb

    with oracledb.connect(DSN, mode=oracledb.SYSDBA) as conn:
        for xid in conn.tpc_recover():
            print("Recovering xid by rolling it back:", xid)
            conn.tpc_rollback(xid)
