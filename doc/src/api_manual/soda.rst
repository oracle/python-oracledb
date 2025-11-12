.. _soda:

**********
API: SODA
**********

.. currentmodule:: oracledb

`Oracle Database Simple Oracle Document Access (SODA)
<https://docs.oracle.com/en/database/oracle/simple-oracle-document-access>`__
allows documents to be inserted, queried, and retrieved from Oracle Database
using a set of NoSQL-style python-oracledb methods. By default, documents are
JSON strings. See the :ref:`user manual <sodausermanual>` for examples.

.. note::

    SODA is only supported in python-oracledb Thick mode.  See
    :ref:`enablingthick`.

.. _sodarequirements:

SODA Requirements
=================

To use SODA, the role SODA_APP must be granted to the user.  To create
collections, users need the CREATE TABLE privilege.  These can be granted by a
DBA:

.. code-block:: sql

    SQL> grant soda_app, create table to myuser;

Advanced users who are using Oracle sequences for keys will also need the
CREATE SEQUENCE privilege.

SODA requires Oracle Client 18.3 or higher and Oracle Database 18.1 and higher.

.. note::

    SODA APIs are only supported in python-oracledb Thick mode. See
    :ref:`enablingthick`.

If you are using Oracle Database 21c (or later) and create new collections
you need to do one of the following:

- Use Oracle Client libraries 21c (or later)

- Or explicitly use collection metadata when creating collections and set
  the data storage type to BLOB, for example::

    {
        "keyColumn": {
            "name":"ID"
        },
        "contentColumn": {
            "name": "JSON_DOCUMENT",
            "sqlType": "BLOB"
        },
        "versionColumn": {
            "name": "VERSION",
            "method": "UUID"
        },
        "lastModifiedColumn": {
            "name": "LAST_MODIFIED"
        },
        "creationTimeColumn": {
            "name": "CREATED_ON"
        }
    }

- Or set the database initialization parameter `compatible
  <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
  id=GUID-A2E90F08-BC9F-4688-A9D0-4A948DD3F7A9>`__ to 19.0.0 or lower

Otherwise, you may get errors such as ``ORA-40842: unsupported value JSON in
the metadata for the field sqlType`` or ``ORA-40659: Data type does not match
the specification in the collection metadata``.

.. _sodadb:

SodaDatabase Class
==================

.. autoclass:: SodaDatabase

    A SodaDatabase object is returned by :meth:`Connection.getSodaDatabase()`.

    .. dbapiobjectextension::

SodaDatabase Methods
--------------------

.. automethod:: SodaDatabase.createCollection

    .. seealso::

        :ref:`SODA collection object <sodacoll>` and `Oracle Database SODA
        Collection Metadata Reference <https://www.oracle.com/pls/topic/lookup
        ?ctx=dblatest&id=GUID-49EFF3D3-9FAB-4DA6-BDE2-2650383566A3>`__

.. automethod:: SodaDatabase.createDocument

.. automethod:: SodaDatabase.getCollectionNames

.. automethod:: SodaDatabase.openCollection

.. _sodacoll:

SodaCollection Class
====================

.. autoclass:: SodaCollection

    A SODA Collection object is used to represent SODA collections and is
    created by :meth:`SodaDatabase.createCollection()` and
    :meth:`SodaDatabase.openCollection()`.

    .. dbapiobjectextension::

SodaCollection Methods
----------------------

.. automethod:: SodaCollection.createIndex

    .. seealso::

        `Overview of SODA Indexing <https://www.oracle.com/pls/topic/lookup?
        ctx=dblatest&id=GUID-4848E6A0-58A7-44FD-8D6D-A033D0CCF9CB>`__

.. automethod:: SodaCollection.drop

.. automethod:: SodaCollection.dropIndex

    .. seealso::

        `DROP INDEX statement <https://www.oracle.com/pls/topic/lookup?ctx=
        dblatest&id=GUID-F60F75DF-2866-4F93-BB7F-8FCE64BF67B6>`__

.. automethod:: SodaCollection.find

    .. seealso::

        :ref:`SodaOperation object <sodaop>`

.. automethod:: SodaCollection.getDataGuide

    .. seealso::

        :ref:`SODA document object <sodadoc>`

.. automethod:: SodaCollection.insertMany

    .. seealso::

        :ref:`SODA document object <sodadoc>`.

.. automethod:: SodaCollection.insertManyAndGet

    .. seealso::

        :ref:`SODA Document objects <sodadoc>`, `MONITOR and NO_MONITOR Hints
        <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-19E0F73C
        -A959-41E4-A168-91E436DEE1F1>`__, and `Monitoring Database Operations
        <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-C941CE9D
        -97E1-42F8-91ED-4949B2B710BF>`__

.. automethod:: SodaCollection.insertOne

    .. seealso::

        :ref:`SODA document object <sodadoc>`

.. automethod:: SodaCollection.insertOneAndGet

    .. seealso::

        :ref:`SODA Document object <sodadoc>`, `MONITOR and NO_MONITOR Hints
        <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-19E0F73C
        -A959-41E4-A168-91E436DEE1F1>`__, and `Monitoring Database Operations
        <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-C941CE9D
        -97E1-42F8-91ED-4949B2B710BF>`__

.. automethod:: SodaCollection.listIndexes

    .. versionadded:: 1.4.0

.. automethod:: SodaCollection.save

.. automethod:: SodaCollection.saveAndGet

    .. seealso::

        `MONITOR and NO_MONITOR Hints <https://www.oracle.com/pls/topic/lookup?
        ctx=dblatest&id=GUID-19E0F73C-A959-41E4-A168-91E436DEE1F1>`__ and
        `Monitoring Database Operations <https://www.oracle.com/pls/topic/
        lookup?ctx=dblatest&id=GUID-C941CE9D-97E1-42F8-91ED-4949B2B710BF>`__

.. automethod:: SodaCollection.truncate

SodaCollection Attributes
-------------------------

.. autoproperty:: SodaCollection.metadata

    .. seealso::

        `Oracle Database SODA Collection Metadata Reference <https://www.oracle
        .com/pls/topic/lookup?ctx=dblatest&id=GUID-49EFF3D3-9FAB-4DA6-BDE2-
        2650383566A3>`__

.. autoproperty:: SodaCollection.name

.. _sodadoc:

SodaDocument Class
==================

.. autoclass:: SodaDocument

    A SODA Document object is returned by
    :meth:`SodaDatabase.createDocument()`,
    :meth:`SodaOperation.getDocuments()`, and
    :meth:`SodaOperation.getOne()` as well as by iterating over
    :ref:`SODA document cursors <sodadoccur>`.

    .. dbapiobjectextension::

SodaDocument Methods
--------------------

.. automethod:: SodaDocument.getContent

.. automethod:: SodaDocument.getContentAsBytes

.. automethod:: SodaDocument.getContentAsString

SodaDocument Attributes
-----------------------

.. autoproperty:: SodaDocument.createdOn

    .. seealso::

        `ISO 8601 <https://www.iso.org/iso-8601-date-and-time-format.html>`__

.. autoproperty:: SodaDocument.key

.. autoproperty:: SodaDocument.lastModified

    .. seealso::

        `ISO 8601 <https://www.iso.org/iso-8601-date-and-time-format.html>`__

.. autoproperty:: SodaDocument.mediaType

.. autoproperty:: SodaDocument.version

.. _sodadoccur:

SodaDocCursor Class
===================

.. autoclass:: SodaDocCursor

    A SodaDocCursor object is returned by :meth:`SodaOperation.getCursor()`
    and implements the iterator protocol. Each iteration will return a
    :ref:`SODA document object <sodadoc>`.

    .. dbapiobjectextension::

SodaDocCursor Methods
---------------------

.. automethod:: SodaDocCursor.close

.. _sodaop:

SodaOperation Class
===================

.. autoclass:: SodaOperation

    A SODA Operation object represents an operation that will be performed on
    all or some of the documents in a SODA collection. This object is created
    by :meth:`SodaCollection.find()`.

    .. dbapiobjectextension::

SodaOperation Methods
---------------------

.. automethod:: SodaOperation.count

.. automethod:: SodaOperation.fetchArraySize

.. automethod:: SodaOperation.filter

    .. seealso::

        `Overview of SODA filter specifications <https://www.oracle.com/pls/
        topic/lookup?ctx=dblatest&id=GUID-CB09C4E3-BBB1-40DC-88A8-
        8417821B0FBE>`__

.. automethod:: SodaOperation.getCursor

    .. seealso::

        :ref:`SODA Document Cursor object <sodadoccur>`

.. automethod:: SodaOperation.getDocuments

    .. seealso::

        :ref:`SODA Document objects <sodadoc>`

.. automethod:: SodaOperation.getOne

    .. seealso::

        :ref:`SODA Document object <sodadoc>`

.. automethod:: SodaOperation.hint

    .. seealso::

        Oracle AI Database SQL Tuning Guide documentation `MONITOR and
        NO_MONITOR Hints <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
        id=GUID-19E0F73C-A959-41E4-A168-91E436DEE1F1>`__ and `Monitoring Database
        Operations <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
        GUID-C941CE9D-97E1-42F8-91ED-4949B2B710BF>`__

.. automethod:: SodaOperation.key

.. automethod:: SodaOperation.keys

.. automethod:: SodaOperation.limit

.. automethod:: SodaOperation.lock

    .. versionadded:: 1.4.0

.. automethod:: SodaOperation.remove

.. automethod:: SodaOperation.replaceOne

    .. seealso::

        :ref:`SODA document object <sodadoc>`

.. automethod:: SodaOperation.replaceOneAndGet

    .. seealso::

        :ref:`SODA document object <sodadoc>`

.. automethod:: SodaOperation.skip

.. automethod:: SodaOperation.version
