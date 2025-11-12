.. _authenticationmethods:

.. currentmodule:: oracledb

**********************
Authentication Options
**********************

Authentication allows only authorized users to access Oracle Database after
successful verification of their identity. This section details the various
Oracle Database authentication options supported in python-oracledb.

The Oracle Client libraries used by python-oracledb Thick mode may support
additional authentication options that are configured independently of the
driver.

.. _dbauthentication:

Database Authentication
=======================

Database Authentication is the most basic authentication method that allows
users to connect to Oracle Database by using a valid database username and
their associated password. Oracle Database verifies the username and
password specified in the python-oracledb connection method with the
information stored in the database. See `Database Authentication of Users
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-1F783131-CD1C-
4EA0-9300-C132651B0700>`__ for more information.

:ref:`Standalone connections <standaloneconnection>` and
:ref:`pooled connections <connpooling>` can be created in python-oracledb Thin
and Thick modes using database authentication. This can be done by specifying
the database username and the associated password in the ``user`` and
``password`` parameters of :meth:`oracledb.connect()`,
:meth:`oracledb.create_pool()`, :meth:`oracledb.connect_async()`, or
:meth:`oracledb.create_pool_async()`. An example is:

.. code-block:: python

    import oracledb
    import getpass

    userpwd = getpass.getpass("Enter password: ")

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb")

.. _proxyauth:

Proxy Authentication
====================

Proxy authentication allows a user (the "session user") to connect to Oracle
Database using the credentials of a "proxy user".  Statements will run as the
session user.  Proxy authentication is generally used in three-tier
applications where one user owns the schema while multiple end-users access
the data. For more information about proxy authentication, see the `Oracle
documentation <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-
D77D0D4A-7483-423A-9767-CBB5854A15CC>`__.

An alternative to using proxy users is to set
:attr:`Connection.client_identifier` after connecting and use its value in
statements and in the database, for example for :ref:`monitoring
<endtoendtracing>`.

The following proxy examples use these schemas. The ``mysessionuser`` schema
is granted access to use the password of ``myproxyuser``:

.. code-block:: sql

    CREATE USER myproxyuser IDENTIFIED BY myproxyuserpw;
    GRANT CREATE SESSION TO myproxyuser;

    CREATE USER mysessionuser IDENTIFIED BY itdoesntmatter;
    GRANT CREATE SESSION TO mysessionuser;

    ALTER USER mysessionuser GRANT CONNECT THROUGH myproxyuser;

After connecting to the database, the following query can be used to show the
session and proxy users:

.. code-block:: sql

    SELECT SYS_CONTEXT('USERENV', 'PROXY_USER'),
           SYS_CONTEXT('USERENV', 'SESSION_USER')
    FROM DUAL;

Standalone connection examples:

.. code-block:: python

    # Basic Authentication without a proxy
    connection = oracledb.connect(user="myproxyuser", password="myproxyuserpw",
                                  dsn="dbhost.example.com/orclpdb")
    # PROXY_USER:   None
    # SESSION_USER: MYPROXYUSER

    # Basic Authentication with a proxy
    connection = oracledb.connect(user="myproxyuser[mysessionuser]", password="myproxyuserpw",
                                  dsn="dbhost.example.com/orclpdb")
    # PROXY_USER:   MYPROXYUSER
    # SESSION_USER: MYSESSIONUSER

Pooled connection examples:

.. code-block:: python

    # Basic Authentication without a proxy
    pool = oracledb.create_pool(user="myproxyuser", password="myproxyuserpw",
                                dsn="dbhost.example.com/orclpdb")
    connection = pool.acquire()
    # PROXY_USER:   None
    # SESSION_USER: MYPROXYUSER

    # Basic Authentication with proxy
    pool = oracledb.create_pool(user="myproxyuser[mysessionuser]", password="myproxyuserpw",
                                dsn="dbhost.example.com/orclpdb",
                                homogeneous=False)

    connection = pool.acquire()
    # PROXY_USER:   MYPROXYUSER
    # SESSION_USER: MYSESSIONUSER

Note the use of a :ref:`heterogeneous <connpooltypes>` pool in the example
above.  This is required in this scenario.

.. _extauth:

External Authentication
=======================

Instead of storing the database username and password in Python scripts or
environment variables, database access can be authenticated by an outside
system.  External Authentication allows applications to validate user access
with an external password store (such as an
:ref:`Oracle Wallet <extauthwithwallet>`), with the
:ref:`operating system <opsysauth>`, or with an external authentication
service.

.. note::

    Connecting to Oracle Database using external authentication is only
    supported in python-oracledb Thick mode. See :ref:`enablingthick`.

.. _extauthwithwallet:

Using an Oracle Wallet for External Authentication
--------------------------------------------------

The following steps give an overview of using an Oracle Wallet.  Wallets should
be kept securely.  Wallets can be managed with `Oracle Wallet Manager
<https://www.oracle.com/pls/topic/lookup?ctx=db21&id=GUID-E3E16C82-E174-4814-
98D5-EADF1BCB3C37>`__.

In this example the wallet is created for the ``myuser`` schema in the
directory ``/home/oracle/wallet_dir``.  The ``mkstore`` command is available
from a full Oracle Client or Oracle Database installation.  If you have been
given wallet by your DBA, skip to step 3.

1.  First create a new wallet as the ``oracle`` user::

        mkstore -wrl "/home/oracle/wallet_dir" -create

    This will prompt for a new password for the wallet.

2.  Create the entry for the database user name and password that are currently
    hardcoded in your Python scripts.  Use either of the methods shown below.
    They will prompt for the wallet password that was set in the first step.

    **Method 1 - Using an Easy Connect string**::

        mkstore -wrl "/home/oracle/wallet_dir" -createCredential dbhost.example.com/orclpdb myuser myuserpw

    **Method 2 - Using a connect name identifier**::

        mkstore -wrl "/home/oracle/wallet_dir" -createCredential mynetalias myuser myuserpw

    The alias key ``mynetalias`` immediately following the
    ``-createCredential`` option will be the connect name to be used in Python
    scripts.  If your application connects with multiple different database
    users, you could create a wallet entry with different connect names for
    each.

    You can see the newly created credential with::

        mkstore -wrl "/home/oracle/wallet_dir" -listCredential

3.  Skip this step if the wallet was created using an Easy Connect String.
    Otherwise, add an entry in :ref:`tnsnames.ora <optnetfiles>` for the
    connect name as follows::

        mynetalias =
            (DESCRIPTION =
                (ADDRESS = (PROTOCOL = TCP)(HOST = dbhost.example.com)(PORT = 1521))
                (CONNECT_DATA =
                    (SERVER = DEDICATED)
                    (SERVICE_NAME = orclpdb)
                )
            )

    The file uses the description for your existing database and sets the
    connect name alias to ``mynetalias``, which is the identifier used when
    adding the wallet entry.

4.  Add the following wallet location entry in the :ref:`sqlnet.ora
    <optnetfiles>` file, using the ``DIRECTORY`` you created the wallet in::

        WALLET_LOCATION =
            (SOURCE =
                (METHOD = FILE)
                (METHOD_DATA =
                    (DIRECTORY = /home/oracle/wallet_dir)
                )
            )
        SQLNET.WALLET_OVERRIDE = TRUE

    Examine the Oracle documentation for full settings and values.

5.  Ensure the configuration files are in a default location or TNS_ADMIN is
    set to the directory containing them.  See :ref:`optnetfiles`.

With an Oracle wallet configured, and readable by you, your scripts
can connect to Oracle Database with:

- Standalone connections by setting the ``externalauth`` parameter to *True*
  in :meth:`oracledb.connect()`:

  .. code-block:: python

    connection = oracledb.connect(externalauth=True, dsn="mynetalias")

- Or pooled connections by setting the ``externalauth`` parameter to *True*
  in :meth:`oracledb.create_pool()`.  Additionally in python-oracledb Thick
  mode, you must set the ``homogeneous`` parameter to *False* as shown below
  since heterogeneous pools can only be used with external authentication:

  .. code-block:: python

    pool = oracledb.create_pool(externalauth=True, homogeneous=False,
                                dsn="mynetalias")
    pool.acquire()

The ``dsn`` used in :meth:`oracledb.connect()` and
:meth:`oracledb.create_pool()` must match the one used in the wallet.

After connecting, the query::

    SELECT SYS_CONTEXT('USERENV', 'SESSION_USER') FROM DUAL;

will show::

    MYUSER

.. note::

    Wallets are also used to configure Transport Layer Security (TLS) connections.
    If you are using a wallet like this, you may need a database username and password
    in :meth:`oracledb.connect()` and :meth:`oracledb.create_pool()` calls.

**External Authentication and Proxy Authentication**

The following examples show external wallet authentication combined with
:ref:`proxy authentication <proxyauth>`.  These examples use the wallet
configuration from above, with the addition of a grant to another user::

    ALTER USER mysessionuser GRANT CONNECT THROUGH myuser;

After connection, you can check who the session user is with:

.. code-block:: sql

    SELECT SYS_CONTEXT('USERENV', 'PROXY_USER'),
           SYS_CONTEXT('USERENV', 'SESSION_USER')
    FROM DUAL;

Standalone connection example:

.. code-block:: python

    # External Authentication with proxy
    connection = oracledb.connect(user="[mysessionuser]", dsn="mynetalias")
    # PROXY_USER:   MYUSER
    # SESSION_USER: MYSESSIONUSER

You can also set the ``externalauth`` parameter to *True* in standalone
connections:

.. code-block:: python

    # External Authentication with proxy when externalauth is set to True
    connection = oracledb.connect(user="[mysessionuser]", dsn="mynetalias",
                                  externalauth=True)
    # PROXY_USER:   MYUSER
    # SESSION_USER: MYSESSIONUSER

A connection pool example is:

.. code-block:: python

    # External Authentication with proxy
    pool = oracledb.create_pool(externalauth=True, homogeneous=False,
                                dsn="mynetalias")
    pool.acquire(user="[mysessionuser]")
    # PROXY_USER:   MYUSER
    # SESSION_USER: MYSESSIONUSER

The following usage is not supported:

.. code-block:: python

    pool = oracledb.create_pool(user="[mysessionuser]", externalauth=True,
                                homogeneous=False, dsn="mynetalias")
    pool.acquire()

.. _opsysauth:

Operating System Authentication
-------------------------------

With `Operating System <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-37BECE32-58D5-43BF-A098-97936D66968F>`__ authentication, Oracle allows
user authentication to be performed by the operating system.  The following
steps give an overview of how to implement OS Authentication on Linux.

1.  Log in to your computer. The commands used in these steps assume the
    operating system user name is "oracle".

2.  Log in to SQL*Plus as the SYSTEM user and verify the value for the
    ``OS_AUTHENT_PREFIX`` parameter::

        SQL> SHOW PARAMETER os_authent_prefix

        NAME                                 TYPE        VALUE
        ------------------------------------ ----------- ------------------------------
        os_authent_prefix                    string      ops$

3.  Create an Oracle Database user using the ``os_authent_prefix`` determined
    in step 2, and the operating system user name:

   .. code-block:: sql

        CREATE USER ops$oracle IDENTIFIED EXTERNALLY;
        GRANT CONNECT, RESOURCE TO ops$oracle;

In Python, connect using the following code:

.. code-block:: python

       connection = oracledb.connect(dsn="mynetalias")

Your session user will be ``OPS$ORACLE``.

If your database is not on the same computer as Python, you can perform testing
by setting the database configuration parameter ``remote_os_authent=true``.
Beware of security concerns because this is insecure.

See `Oracle AI Database Security Guide
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-37BECE32-58D5-43BF-A098-97936D66968F>`__ for more information about
Operating System Authentication.

.. _tokenauth:

Token-Based Authentication
==========================

Token-Based Authentication allows users to connect to a database by using an
encrypted authentication token without having to enter a database username and
password.  The authentication token must be valid and not expired for the
connection to be successful.  Users already connected will be able to continue
work after their token has expired but they will not be able to reconnect
without getting a new token.

The two authentication methods supported by python-oracledb are
:ref:`Open Authorization (OAuth 2.0) <oauth2>` and :ref:`Oracle
Cloud Infrastructure (OCI) Identity and Access Management (IAM) <iamauth>`.
These authentication methods can use Cloud Native Authentication with the
support of the Azure SDK or OCI SDK to generate access tokens and connect to
Oracle Database. Alternatively, these methods can use a Python script that
contains a class to generate access tokens to connect to Oracle Database.

.. _iamauth:

OCI IAM Token-Based Authentication
----------------------------------

Oracle Cloud Infrastructure (OCI) Identity and Access Management (IAM) provides
its users with a centralized database authentication and authorization system.
Using this authentication method, users can use the database access token
issued by OCI IAM to authenticate to the Oracle Autonomous Database. Both Thin
and Thick modes of the python-oracledb driver support OCI IAM token-based
authentication.

When using python-oracledb in Thick mode, Oracle Client libraries 19.14 (or
later), or 21.5 (or later) are needed.

Standalone connections and pooled connections can be created in python-oracledb
Thick and Thin modes using OCI IAM token-based authentication. This can be done
by using a class like the sample :ref:`TokenHandlerIAM class <iamhandler>` or
by using python-oracledb's :ref:`OCI Cloud Native Authentication Plugin
(oci_tokens) <cloudnativeauthoci>`. Tokens can be specified using the
connection parameter introduced in python-oracledb 1.1. Users of earlier
python-oracledb versions can alternatively use :ref:`OCI IAM Token-Based
Authentication Connection Strings <iamauthconnstr>`.

OCI IAM Token Generation and Extraction
+++++++++++++++++++++++++++++++++++++++

Authentication tokens can be generated using python-oracledb's
:ref:`oci_tokens <ocicloudnativeauthplugin>` plugin.

Alternatively, authentication tokens can be generated through execution of an
Oracle Cloud Infrastructure command line interface (OCI-CLI) command ::

    oci iam db-token get

On Linux, a folder ``.oci/db-token`` will be created in your home directory.
It will contain the token and private key files needed by python-oracledb.

.. _iamhandler:

**Example of Generating an IAM Token**

Here, as an example, we are using a Python script to automate the process of
generating and reading OCI IAM tokens.

.. code:: python

    import os

    import oracledb

    class TokenHandlerIAM:

        def __init__(self,
                     dir_name="dir_name",
                     command="oci iam db-token get"):
            self.dir_name = dir_name
            self.command = command
            self.token = None
            self.private_key = None

        def __call__(self, refresh):
            if refresh:
                if os.system(self.command) != 0:
                    raise Exception("token command failed!")
            if self.token is None or refresh:
                self.read_token_info()
            return (self.token, self.private_key)

        def read_token_info(self):
            token_file_name = os.path.join(self.dir_name, "token")
            pkey_file_name = os.path.join(self.dir_name, "oci_db_key.pem")
            with open(token_file_name) as f:
                self.token = f.read().strip()
            with open(pkey_file_name) as f:
                if oracledb.is_thin_mode():
                    self.private_key = f.read().strip()
                else:
                    lines = [s for s in f.read().strip().split("\n")
                             if s not in ('-----BEGIN PRIVATE KEY-----',
                                          '-----END PRIVATE KEY-----')]
                    self.private_key = "".join(lines)

The TokenHandlerIAM class uses a callable to generate and read OCI IAM tokens.
When the callable in the TokenHandlerIAM class is invoked for the first time
to create a standalone connection or pool, the ``refresh`` parameter is
*False* which allows the callable to return a cached token, if desired. The
expiry date is then extracted from this token and compared with the current
date. If the token has not expired, then it will be used directly. If the token
has expired, the callable is invoked the second time with the ``refresh``
parameter set to *True*.

The TokenHandlerIAM class defined here is used in the examples shown in
:ref:`conncreationociiam`.

.. _conncreationociiam:

Connection Creation with OCI IAM Access Tokens
++++++++++++++++++++++++++++++++++++++++++++++

For OCI IAM Token-Based Authentication with a class such as the sample
:ref:`TokenHandlerIAM class <iamhandler>`, the ``access_token`` connection
parameter must be specified. This parameter should be a 2-tuple (or a callable
that returns a 2-tuple) containing the token and private key. In the examples
used below, the ``access_token`` parameter is set to a callable.

The examples used in the subsequent sections use the
:ref:`TokenHandlerIAM class <iamhandler>` to generate OCI IAM tokens to connect
to Oracle Autonomous Database with mutual TLS (mTLS). See :ref:`autonomousdb`.

**Standalone Connections in Thin Mode Using OCI IAM Tokens**

When using a class such as the :ref:`TokenHandlerIAM class <iamhandler>` to
generate OCI IAM tokens to connect to Oracle Autonomous Database in Thin mode,
you need to explicitly set the ``access_token`` parameter of
:func:`~oracledb.connect`, and also any desired ``config_dir``,
``wallet_location``, and ``wallet_password`` parameters. For example:

.. code:: python

    connection = oracledb.connect(
        access_token=TokenHandlerIAM(),
        dsn=mydb_low,
        config_dir="path_to_unzipped_wallet",
        wallet_location="location_of_pem_file",
        wallet_password=wp)

**Connection Pools in Thin Mode Using OCI IAM Tokens**

When using a class such as :ref:`TokenHandlerIAM class <iamhandler>` to
generate OCI IAM tokens to connect to Oracle Autonomous Database in Thin mode,
you need to explicitly set the ``access_token`` parameter of
:func:`~oracledb.create_pool`, and also any desired ``config_dir``,
``wallet_location``, and ``wallet_password`` parameters. The ``homogeneous``
parameter must be *True* (its default value). For example:

.. code:: python

    connection = oracledb.create_pool(
        access_token=TokenHandlerIAM(),
        homogeneous=True, # must always be True for connection pools
        dsn=mydb_low,
        config_dir="path_to_unzipped_wallet",
        wallet_location="location_of_pem_file",
        wallet_password=wp
        min=1, max=5, increment=2)

Note that the ``access_token`` parameter should be set to a callable. This is
useful when the connection pool needs to expand and create new connections but
the current token has expired. In such a case, the callable should return a
string specifying the new, valid access token.

**Standalone Connections in Thick Mode Using OCI IAM Tokens**

When using a class such as :ref:`TokenHandlerIAM class <iamhandler>` to
generate OCI IAM tokens to connect to Oracle Autonomous Database in Thick mode,
you need to explicitly set the ``access_token`` and ``externalAuth`` parameters
of :func:`~oracledb.connect`. For example:

.. code:: python

    connection = oracledb.connect(
        access_token=TokenHandlerIAM(),
        externalauth=True, # must always be True in Thick mode
        dsn=mydb_low)

**Connection Pools in Thick Mode Using OCI IAM Tokens**

When using a class such as :ref:`TokenHandlerIAM class <iamhandler>` to
generate OCI IAM tokens to connect to Oracle Autonomous Database in Thick mode,
you need to explicitly set the ``access_token`` and ``externalauth`` parameters
of :func:`oracledb.create_pool`. The ``homogeneous`` parameter must be *True*
(its default value). For example:

.. code:: python

    pool = oracledb.create_pool(
        access_token=TokenHandlerIAM(),
        externalauth=True, # must always be True in Thick mode
        homogeneous=True,  # must always be True for connection pools
        dsn=mydb_low, min=1, max=5, increment=2)

Note that the ``access_token`` parameter should be set to a callable. This is
useful when the connection pool needs to expand and create new connections but
the current token has expired. In such a case, the callable should return a
string specifying the new, valid access token.

.. _iamauthconnstr:

OCI IAM Token-Based Authentication Connection Strings
+++++++++++++++++++++++++++++++++++++++++++++++++++++

The connection string used by python-oracledb can specify the directory where
the token and private key files are located. This syntax is usable with older
versions of python-oracledb. However, it is recommended to use connection
parameters introduced in python-oracledb 1.1 instead. See
:ref:`OCI IAM Token-Based Authentication<iamauth>`.

.. note::

    OCI IAM Token-Based Authentication Connection Strings is only supported in
    python-oracledb Thick mode. See :ref:`enablingthick`.

The Oracle Cloud Infrastructure command line interface (OCI-CLI) can be used
externally to get tokens and private keys from OCI IAM, for example with the
OCI-CLI ``oci iam db-token get`` command.

The Oracle Net parameter ``TOKEN_AUTH`` must be set when you are using the
connection string syntax. Also, the ``PROTOCOL`` parameter must be ``tcps``
and ``SSL_SERVER_DN_MATCH`` should be ``ON``.

You can set ``TOKEN_AUTH=OCI_TOKEN`` in a ``sqlnet.ora`` file.  Alternatively,
you can specify it in a :ref:`Connect Descriptor <conndescriptor>`, for example
when using a :ref:`tnsnames.ora <optnetfiles>` file::

    db_alias =
        (DESCRIPTION =
            (ADDRESS=(PROTOCOL=TCPS)(PORT=1522)(HOST=xxx.oraclecloud.com))
            (CONNECT_DATA=(SERVICE_NAME=xxx.adb.oraclecloud.com))
            (SECURITY =
                (SSL_SERVER_CERT_DN="CN=xxx.oraclecloud.com, \
                 O=Oracle Corporation,L=Redwood City,ST=California,C=US")
                (TOKEN_AUTH=OCI_TOKEN)
            )
        )

The default location for the token and private key is the same default location
that the OCI-CLI tool writes to. For example ``~/.oci/db-token/`` on Linux.

If the token and private key files are not in the default location then their
directory must be specified with the ``TOKEN_LOCATION`` parameter in a
:ref:`sqlnet.ora <optnetfiles>` file or in a :ref:`Connect Descriptor
<conndescriptor>`, for example when using a :ref:`tnsnames.ora <optnetfiles>`
file::

    db_alias =
        (DESCRIPTION =
            (ADDRESS=(PROTOCOL=TCPS)(PORT=1522)(HOST=xxx.oraclecloud.com))
            (CONNECT_DATA=(SERVICE_NAME=xxx.adb.oraclecloud.com))
            (SECURITY =
                (SSL_SERVER_CERT_DN="CN=xxx.oraclecloud.com, \
                 O=Oracle Corporation,L=Redwood City,ST=California,C=US")
                (TOKEN_AUTH=OCI_TOKEN)
                (TOKEN_LOCATION="/path/to/token/folder")
            )
        )

The ``TOKEN_AUTH`` and ``TOKEN_LOCATION`` values in a connection string take
precedence over the ``sqlnet.ora`` settings.

Standalone connection example:

.. code-block:: python

    connection = oracledb.connect(dsn=db_alias, externalauth=True)

Connection pool example:

.. code-block:: python

    pool = oracledb.create_pool(dsn=db_alias, externalauth=True,
                                homogeneous=False, min=1, max=2, increment=1)

    connection = pool.acquire()

.. _cloudnativeauthoci:

OCI Cloud Native Authentication with the oci_tokens Plugin
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

With Cloud Native Authentication, python-oracledb's :ref:`oci_tokens
<ocicloudnativeauthplugin>` plugin can automatically generate and refresh OCI
IAM tokens when required with the support of the `Oracle Cloud Infrastructure
(OCI) Software Development Kit (SDK)
<https://docs.oracle.com/en-us/iaas/tools/python/latest/index.html>`__.

The :ref:`oci_tokens <ocicloudnativeauthplugin>` plugin can be imported
like:

.. code-block:: python

    import oracledb.plugins.oci_tokens

The plugin has a Python package dependency which needs to be installed
separately before the plugin can be used, see :ref:`ocitokenmodules`.

The ``oci_tokens`` plugin defines and registers a :ref:`parameter hook
<registerparamshook>` function which uses the connection parameter
``extra_auth_params`` passed to :meth:`oracledb.connect()`,
:meth:`oracledb.create_pool()`, :meth:`oracledb.connect_async()`, or
:meth:`oracledb.create_pool_async()`. Using this parameter's values, the hook
function sets the ``access_token`` parameter of a :ref:`ConnectParams object
<connparam>` to a callable which generates an OCI IAM token. Python-oracledb
then acquires and uses a token to transparently complete connection or pool
creation calls.

For OCI Cloud Native Authentication connection and pool creation, the
``extra_auth_params`` parameter should be a dictionary with keys as shown in
the following table.

.. list-table-with-summary:: OCI Cloud Native Authentication Configuration Keys
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 10 25 15
    :name: _oci_configuration_parameters
    :summary: The first column displays the name of the dictionary key. The second column displays its description. The third column displays whether the attribute is required or optional.

    * - Key
      - Description
      - Required or Optional
    * - ``auth_type``
      - The authentication type. The value should be the string "ConfigFileAuthentication", "InstancePrincipal", "SecurityToken", "SecurityTokenSimple" or "SimpleAuthentication".

        With Configuration File Authentication, the location of a configuration file containing the necessary information must be provided. By default, this file is located at */home/username/.oci/config*, unless a custom location is specified during OCI IAM setup.

        With Instance Principal Authentication, OCI compute instances can be authorized to access services on Oracle Cloud such as Oracle Autonomous Database. Python-oracledb applications running on such a compute instance are automatically authenticated, eliminating the need to provide database user credentials. This authentication method will only work on compute instances where internal network endpoints are reachable. See :ref:`instanceprincipalauth`.

        With Security Token authentication or Session Token-based authentication, the authentication happens using *security_token_file* parameter present in the configuration file. By default, this file is located at */home/username/.oci/config*, unless a custom location is specified during OCI IAM setup. You also need to specify the *profile* which contains the *security_token_file* parameter.

        With Security Token Simple authentication or Session Token-based Simple authentication, the authentication happens using *security_token_file* parameter. The individual configuration parameters can be provided at runtime.

        With Simple Authentication, the individual configuration parameters can be provided at runtime.

        See `OCI SDK Authentication Methods <https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_authentication_methods.htm>`__ for more information.
      - Required
    * - ``user``
      - The Oracle Cloud Identifier (OCID) of the user invoking the API. For example, *ocid1.user.oc1..<unique_ID>*.

        This parameter can be specified when the value of the ``auth_type`` key is "SimpleAuthentication". This is not required when ``auth_type`` is "SecurityToken" or "SecurityTokenSimple"
      - Required
    * - ``key_file``
      - The full path and filename of the private key.

        This parameter can be specified when the value of the ``auth_type`` key is "SimpleAuthentication".
      - Required
    * - ``fingerprint``
      - The fingerprint associated with the public key that has been added to this user.

        This parameter can be specified when the value of the ``auth_type`` key is "SimpleAuthentication".
      - Required
    * - ``tenancy``
      - The OCID of your tenancy. For example, *ocid1.tenancy.oc1..<unique_ID>*.

        This parameter can be specified when the value of the ``auth_type`` key is "SimpleAuthentication".
      - Required
    * - ``region``
      - The Oracle Cloud Infrastructure region. For example, *ap-mumbai-1*.

        This parameter can be specified when the value of the ``auth_type`` key is "SimpleAuthentication".
      - Required
    * - ``profile``
      - The configuration profile name to load.

        Multiple profiles can be created, each with distinct values for necessary parameters. If not specified, the DEFAULT profile is used.

        This parameter can be specified when the value of the ``auth_type`` key is "SimpleAuthentication" or "ConfigFileAuthentication". If it is not specified when using "ConfigFileAuthentication", the default value is taken.
      - Required
    * - ``file_location``
      - The configuration file location. The default value is *~/.oci/config*.

        This parameter can be specified when the value of the ``auth_type`` key is "ConfigFileAuthentication".
      - Optional
    * - ``scope``
      - This parameter identifies all databases in the cloud tenancy of the authenticated user. The default value is *urn:oracle:db::id::**.

        A scope that authorizes access to all databases within a compartment has the format *urn:oracle:db::id::<compartment-ocid>*, for example, urn:oracle:db::id::ocid1.compartment.oc1..xxxxxxxx.

        A scope that authorizes access to a single database within a compartment has the format *urn:oracle:db::id::<compartment-ocid>::<database-ocid>*, for example, urn:oracle:db::id::ocid1.compartment.oc1..xxxxxx::ocid1.autonomousdatabase.oc1.phx.xxxxxx.

        This parameter can be specified when the value of the ``auth_type`` key is "SimpleAuthentication", "ConfigFileAuthentication", or "InstancePrincipal".
      - Optional

All keys and values other than ``auth_type`` are used by the `OCI SDK
<https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm>`__ API
calls in the plugin.  The plugin implementation can be seen in
`plugins/oci_tokens.py
<https://github.com/oracle/python-oracledb/blob/main/src/oracledb/plugins/oci_tokens.py>`__.

For information on the OCI specific configuration parameters, see `OCI SDK
<https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm>`__.

The examples in the subsequent sections use the :ref:`oci_tokens
<ocicloudnativeauthplugin>` plugin to generate OCI IAM tokens to connect to
Oracle Autonomous Database with mutual TLS (mTLS). See :ref:`autonomousdb`.

**Standalone Connections in Thin Mode Using OCI IAM Tokens**

When using the :ref:`oci_tokens <ocicloudnativeauthplugin>` plugin to generate
OCI IAM tokens to connect to Oracle Autonomous Database in Thin mode, you need
to explicitly set the ``extra_auth_params`` parameter of
:func:`~oracledb.connect`, and also any desired ``config_dir``,
``wallet_location``, and ``wallet_password`` parameters. For example:

.. code:: python

    import oracledb.plugins.oci_tokens

    token_based_auth = {                             # OCI specific configuration
        "auth_type": "ConfigFileAuthentication",     # parameters to be set when using
        "profile": <profile>,                        # the oci_tokens plugin with
        "file_location": <filelocation>,             # configuration file authentication
    }

    connection = oracledb.connect(
        dsn=mydb_low,
        config_dir="path_to_unzipped_wallet",
        wallet_location="location_of_pem_file",
        wallet_password=wp,
        extra_auth_params=token_based_auth)

**Connection Pools in Thin Mode Using OCI IAM Tokens**

When using the :ref:`oci_tokens <ocicloudnativeauthplugin>` plugin to generate
OCI IAM tokens to connect to Oracle Autonomous Database in Thin mode, you need
to explicitly set the ``extra_auth_params`` parameter of
:func:`~oracledb.create_pool`, and also any desired ``config_dir``,
``wallet_location``, and ``wallet_password`` parameters. The ``homogeneous``
parameter must be *True* (its default value). For example:

.. code:: python

    import oracledb.plugins.oci_tokens

    token_based_auth = {
        "auth_type": "SimpleAuthentication", # OCI specific configuration
        "user": <user>,                      # parameters to be set when using
        "key_file": <key_file>,              # the oci_tokens plugin with
        "fingerprint": <fingerprint>,        # simple authentication
        "tenancy": <tenancy>,
        "region": <region>,
        "profile": <profile>
    }

    connection = oracledb.create_pool(
        dsn=mydb_low,
        config_dir="path_to_unzipped_wallet",
        homogeneous=true,           # must always be True for connection pools
        wallet_location="location_of_pem_file",
        wallet_password=wp,
        extra_auth_params=token_based_auth)

**Standalone Connections in Thick Mode Using OCI IAM Tokens**

When using the :ref:`oci_tokens <ocicloudnativeauthplugin>` plugin to generate
OCI IAM tokens to connect to Oracle Autonomous Database in Thick mode, you need
to explicitly set the ``externalauth`` and ``extra_auth_params`` parameters of
:func:`oracledb.connect`. For example:

.. code:: python

    import oracledb.plugins.oci_tokens

    token_based_auth = {
        "auth_type": "SimpleAuthentication", # OCI specific configuration
        "user": <user>,                      # parameters to be set when using
        "key_file": <key_file>,              # the oci_tokens plugin with
        "fingerprint": <fingerprint>,        # simple authentication
        "tenancy": <tenancy>,
        "region": <region>,
        "profile": <profile>
    }
    connection = oracledb.connect(
        externalauth=True,
        dsn=mydb_low,
        extra_auth_params=token_based_auth)

**Connection Pools in Thick Mode Using OCI IAM Tokens**

When using the :ref:`oci_tokens <ocicloudnativeauthplugin>` plugin to generate
OCI IAM tokens to connect to Oracle Autonomous Database in Thick mode, you need
to explicitly set the ``extra_auth_params`` and ``externalauth`` parameters of
:func:`~oracledb.create_pool`. The ``homogeneous`` parameter must be *True*
(its default value). For example:

.. code:: python

    import oracledb.plugins.oci_tokens

    token_based_auth = {                             # OCI specific configuration
        "auth_type": "ConfigFileAuthentication",     # parameters to be set when using
        "profile": <profile>,                        # the oci_tokens plugin with
        "file_location": <filelocation>,             # configuration file authentication
    }

    connection = oracledb.create_pool(
        externalauth=True, # must always be True in Thick mode
        homogeneous=True,  # must always be True for connection pools
        dsn=mydb_low,
        extra_auth_params=token_based_auth)

.. _oauth2:

OAuth 2.0 Token-Based Authentication
------------------------------------

Oracle Cloud Infrastructure (OCI) users can be centrally managed in a Microsoft
Entra ID (formerly Microsoft Azure Active Directory) service. Open
Authorization (OAuth 2.0) token-based authentication allows users to
authenticate to Oracle Database using Entra ID OAuth2 tokens. Ensure that
you have a Microsoft Azure account and your Oracle Database is registered
with Microsoft Entra ID. See `Configuring the Oracle Database for Microsoft
Entra ID Integration <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
GUID-0A60F22D-56A3-408D-8EC8-852C38C159C0>`_ for more information. Both Thin
and Thick modes of the python-oracledb driver support OAuth 2.0 token-based
authentication.

When using python-oracledb in Thick mode, Oracle Client libraries 19.15 (or
later), or 21.7 (or later) are needed.

Standalone connections and pooled connections can be created in python-oracledb
Thick and Thin modes using OAuth 2.0 token-based authentication. This can be
done or by using a class such as the example :ref:`TokenHandlerOAuth Class
<oauthhandler>` or by using python-oracledb's :ref:`Azure Cloud Native
Authentication Plugin (azure_tokens) <cloudnativeauthoauth>`. Tokens can be
specified using the connection parameter introduced in python-oracledb 1.1.
Users of earlier python-oracledb versions can alternatively use :ref:`OAuth 2.0
Token-Based Authentication Connection Strings <oauth2connstr>`.

OAuth2 Token Generation And Extraction
++++++++++++++++++++++++++++++++++++++

There are different ways to retrieve Entra ID OAuth2 tokens. You can use
python-oracledb's :ref:`azure_tokens <cloudnativeauthoauth>` plugin to generate
tokens. Some of the other ways to retrieve OAuth2 tokens are detailed in
`Examples of Retrieving Entra ID OAuth2 Tokens <https://www.oracle.com/pls/
topic/lookup?ctx=dblatest&id=GUID-3128BDA4-A233-48D8-A2B1-C8380DBDBDCF>`_. You
can also retrieve Entra ID OAuth2 tokens by using `Azure Identity client
library for Python <https://docs.microsoft.com/en-us/python/api/overview/azure/
identity-readme?view=azure-python>`_.

.. _oauthhandler:

**Example of Generating an OAuth2 Token**

An example of automating the process of generating and reading Entra ID OAuth2
tokens is:

.. code:: python

    import json
    import os

    import oracledb
    import requests

    class TokenHandlerOAuth:

        def __init__(self,
                     file_name="cached_token_file_name",
                     api_key="api_key",
                     client_id="client_id",
                     client_secret="client_secret"):
            self.token = None
            self.file_name = file_name
            self.url = \
                f"https://login.microsoftonline.com/{api_key}/oauth2/v2.0/token"
            self.scope = \
                f"https://oracledevelopment.onmicrosoft.com/{client_id}/.default"
            if os.path.exists(file_name):
                with open(file_name) as f:
                    self.token = f.read().strip()
            self.api_key = api_key
            self.client_id = client_id
            self.client_secret = client_secret

        def __call__(self, refresh):
            if self.token is None or refresh:
                post_data = dict(client_id=self.client_id,
                                 grant_type="client_credentials",
                                 scope=self.scope,
                                 client_secret=self.client_secret)
                r = requests.post(url=self.url, data=post_data)
                result = json.loads(r.text)
                self.token = result["access_token"]
                with open(self.file_name, "w") as f:
                    f.write(self.token)
            return self.token

The TokenHandlerOAuth class uses a callable to generate and read OAuth2
tokens. When the callable in the TokenHandlerOAuth class is invoked for the
first time to create a standalone connection or pool, the ``refresh`` parameter
is *False* which allows the callable to return a cached token, if desired. The
expiry date is then extracted from this token and compared with the current
date. If the token has not expired, then it will be used directly. If the token
has expired, the callable is invoked the second time with the ``refresh``
parameter set to *True*.

The TokenHandlerOAuth class defined here is used in the examples shown in
:ref:`conncreationoauth2`.

**Example of Using a Curl Command**

See using a :ref:`curl <curl>` command for an alternative way to generate the
tokens.

.. _conncreationoauth2:

Connection Creation with OAuth2 Access Tokens
+++++++++++++++++++++++++++++++++++++++++++++

For OAuth 2.0 Token-Based Authentication using a class such as the sample
:ref:`TokenHandlerOAuth class <oauthhandler>`, the ``access_token`` connection
parameter must be specified. This parameter should be a string (or a callable
that returns a string) specifying an Entra ID OAuth2 token. In the examples
used below, the ``access_token`` parameter is set to a callable.

The examples used in the subsequent sections use the
:ref:`TokenHandlerOAuth class <oauthhandler>` to generate OAuth2 tokens to
connect to Oracle Autonomous Database with mutual TLS (mTLS). See
:ref:`autonomousdb`.

**Standalone Connections in Thin Mode Using OAuth2 Tokens**

When using a class such as the :ref:`TokenHandlerOAuth class <oauthhandler>` to
generate OAuth2 tokens to connect to Oracle Autonomous Database in Thin mode,
you need to explicitly set the ``access_token``, and also any desired
``config_dir``, ``wallet_location``, and ``wallet_password`` parameters of
:func:`~oracledb.connect`. For example:

.. code:: python

    connection = oracledb.connect(
        access_token=TokenHandlerOAuth(),
        dsn=mydb_low,
        config_dir="path_to_unzipped_wallet",
        wallet_location="location_of_pem_file",
        wallet_password=wp)

**Connection Pools in Thin Mode Using OAuth2 Tokens**

When using a class such as the :ref:`TokenHandlerOAuth class <oauthhandler>` to
generate OAuth2 tokens to connect to Oracle Autonomous Database in Thin mode,
you need to explicitly set the ``access_token`` parameter of
:func:`~oracledb.create_pool`, and also any desired ``config_dir``,
``wallet_location``, and ``wallet_password`` parameters. The ``homogeneous``
parameter must be *True* (its default value). For example:

.. code:: python

    connection = oracledb.create_pool(
        access_token=TokenHandlerOAuth(),
        homogeneous=True, # must always be True for connection pools
        dsn=mydb_low,
        config_dir="path_to_unzipped_wallet",
        wallet_location="location_of_pem_file",
        wallet_password=wp
        min=1, max=5, increment=2)

Note that the ``access_token`` parameter should be set to a callable. This is
useful when the connection pool needs to expand and create new connections but
the current token has expired. In such a case, the callable should return a
string specifying the new, valid Entra ID OAuth2 token.

**Standalone Connections Thick Mode Using OAuth2 Tokens**

When using a class such as the :ref:`TokenHandlerOAuth class <oauthhandler>`
to generate OAuth2 tokens to connect to Oracle Autonomous Database in Thick
mode, you need to explicitly set the ``access_token`` and ``externalAuth``
parameters of :func:`~oracledb.connect`. For example:

.. code:: python

    connection = oracledb.connect(
        access_token=TokenHandlerOAuth(),
        externalauth=True, # must always be True in Thick mode
        dsn=mydb_low)

**Connection Pools in Thick Mode Using OAuth2 Tokens**

When using a class such as the :ref:`TokenHandlerOAuth class <oauthhandler>` to
generate OAuth2 tokens to connect to Oracle Autonomous Database in Thick mode,
you need to explicitly set the ``access_token`` and ``externalauth`` parameters
of :func:`~oracledb.create_pool`. The ``homogeneous`` parameter must be *True*
(which is its default value). For example:

.. code:: python

    pool = oracledb.create_pool(
        access_token=TokenHandlerOAuth(),
        externalauth=True, # must always be True in Thick mode
        homogeneous=True,  # must always be True for connection pools
        dsn=mydb_low, min=1, max=5, increment=2)

Note that the ``access_token`` parameter should be set to a callable. This is
useful when the connection pool needs to expand and create new connections but
the current token has expired. In such a case, the callable should return a
string specifying the new, valid Entra ID OAuth2 token.

.. _oauth2connstr:

OAuth 2.0 Token-Based Authentication Connection Strings
+++++++++++++++++++++++++++++++++++++++++++++++++++++++

The connection string used by python-oracledb can specify the directory where
the token file is located. This syntax is usable with older versions of
python-oracledb. However, it is recommended to use connection parameters
introduced in python-oracledb 1.1 instead. See
:ref:`OAuth 2.0 Token-Based Authentication<oauth2>`.

.. note::

    OAuth 2.0 Token-Based Authentication Connection Strings is only supported
    in python-oracledb Thick mode. See :ref:`enablingthick`.

There are different ways to retrieve Entra ID OAuth2 tokens. Some of the ways to
retrieve OAuth2 tokens are detailed in `Examples of Retrieving Entra ID OAuth2
Tokens <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
GUID-3128BDA4-A233-48D8-A2B1-C8380DBDBDCF>`_. You can also retrieve Entra ID OAuth2
tokens by using `Azure Identity client library for Python
<https://docs.microsoft.com/en-us/python/api/overview/azure/identity-readme?view=
azure-python>`_.

.. _curl:

**Example of Using a Curl Command**

Here, as an example, we are using Curl with a Resource Owner
Password Credential (ROPC) Flow, that is, a ``curl`` command is used against
the Entra ID API to get the Entra ID OAuth2 token::

    curl -X POST -H 'Content-Type: application/x-www-form-urlencoded'
    https://login.microsoftonline.com/your_tenant_id/oauth2/v2.0/token
    -d 'client_id=your_client_id'
    -d 'grant_type=client_credentials'
    -d 'scope=https://oracledevelopment.onmicrosoft.com/your_client_id/.default'
    -d 'client_secret=your_client_secret'

This command generates a JSON response with token type, expiration, and access
token values. The JSON response needs to be parsed so that only the access
token is written and stored in a file. You can save the value of
``access_token`` generated to a file and set ``TOKEN_LOCATION`` to the location
of token file. See :ref:`TokenHandlerOAuth class <oauthhandler>` for an example
of generating tokens.

The Oracle Net parameters ``TOKEN_AUTH`` and ``TOKEN_LOCATION`` must be set when
you are using the connection string syntax. Also, the ``PROTOCOL``
parameter must be ``tcps`` and ``SSL_SERVER_DN_MATCH`` should be ``ON``.

You can set ``TOKEN_AUTH=OAUTH``. There is no default location set in this
case, so you must set ``TOKEN_LOCATION`` to either of the following:

*  A directory, in which case, you must create a file named ``token`` which
   contains the token value
*  A fully qualified file name, in which case, you must specify the entire path
   of the file which contains the token value

You can either set ``TOKEN_AUTH`` and ``TOKEN_LOCATION`` in a :ref:`sqlnet.ora
<optnetfiles>` file or alternatively, you can specify it inside a :ref:`Connect
Descriptor <conndescriptor>`, for example when using a :ref:`tnsnames.ora
<optnetfiles>` file::

    db_alias =
        (DESCRIPTION =
            (ADDRESS=(PROTOCOL=TCPS)(PORT=1522)(HOST=xxx.oraclecloud.com))
            (CONNECT_DATA=(SERVICE_NAME=xxx.adb.oraclecloud.com))
            (SECURITY =
                (SSL_SERVER_CERT_DN="CN=xxx.oraclecloud.com, \
                 O=Oracle Corporation,L=Redwood City,ST=California,C=US")
                (TOKEN_AUTH=OAUTH)
                (TOKEN_LOCATION="/home/user1/mytokens/oauthtoken")
            )
        )

The ``TOKEN_AUTH`` and ``TOKEN_LOCATION`` values in a connection string take
precedence over the ``sqlnet.ora`` settings.

Standalone connection example:

.. code-block:: python

    connection = oracledb.connect(dsn=db_alias, externalauth=True)

Connection pool example:

.. code-block:: python

    pool = oracledb.create_pool(dsn=db_alias, externalauth=True,
                                homogeneous=False, min=1, max=2, increment=1)

    connection = pool.acquire()

.. _cloudnativeauthoauth:

Azure Cloud Native Authentication with the azure_tokens Plugin
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

With Cloud Native Authentication, python-oracledb's :ref:`azure_tokens
<azurecloudnativeauthplugin>` plugin can automatically generate and refresh
OAuth2 tokens when required with the support of the `Microsoft Authentication
Library (MSAL) <https://learn.microsoft.com/en-us/
entra/msal/python/?view=msal-py-latest>`__.

The :ref:`azure_tokens <azurecloudnativeauthplugin>` plugin can be imported
like:

.. code-block:: python

    import oracledb.plugins.azure_tokens

The plugin has a Python package dependency which needs to be installed
separately before the plugin can be used, see :ref:`azuretokenmodules`.

The ``azure_tokens`` plugin defines and registers a :ref:`parameter hook
<registerparamshook>` function which uses the connection parameter
``extra_auth_params`` passed to :meth:`oracledb.connect()`,
:meth:`oracledb.create_pool()`, :meth:`oracledb.connect_async()`, or
:meth:`oracledb.create_pool_async()`. Using this parameter's values, the hook
function sets the ``access_token`` parameter of a :ref:`ConnectParams object
<connparam>` to a callable which generates an OAuth2 token. Python-oracledb
then acquires and uses a token to transparently complete connection or pool
creation calls.

For OAuth 2.0 Token-Based Authentication connection and pool creation, the
``extra_auth_params`` parameter should be a dictionary with keys as shown in
the following table.

.. list-table-with-summary:: Azure Cloud Native Authentication Configuration Keys
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 10 30 10
    :name: _azure_configuration_parameters
    :summary: The first column displays the dictionary key. The second column displays the description of the key. The third column displays whether the parameter is required or optional.

    * - Key
      - Description
      - Required or Optional
    * - ``auth_type``
      - The authentication type.

        This must be the string "AzureServicePrincipal". This type makes the plugin acquire Azure service principal access tokens through a client credential flow.
      - Required
    * - ``authority``
      - This parameter must be set as a string in the URI format with the tenant ID, for example ``https://{identity provider instance}/{tenantId}``.

        The tenantId is the directory tenant against which the application operates, in either GUID or domain-name format.
      - Required
    * - ``client_id``
      - The application ID that is assigned to your application.

        This information can be found in the portal where the application was registered.
      - Required
    * - ``client_credential``
      - The client secret that was generated for your application in the application registration portal.
      - Required
    * - ``scopes``
      - This parameter represents the value of the scope for the request.

        It should be the resource identifier (application ID URI) of the desired resource, with the suffix ".default". For example, ``https://{uri}/clientID/.default``.
      - Required

All keys and values other than ``auth_type`` are used by the `Microsoft
Authentication Library (MSAL) <https://learn.microsoft.com/en-us/
entra/msal/python/?view=msal-py-latest>`__ API calls in the plugin.  The plugin
implementation can be seen in `plugins/azure_tokens.py
<https://github.com/oracle/python-oracledb/blob/main/src/oracledb/plugins/azure_tokens.py>`__.

For information on the Azure specific configuration parameters, see `MSAL
<https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-client
-creds-grant-flow>`__.

The examples in the subsequent sections use the :ref:`azure_tokens
<azurecloudnativeauthplugin>` plugin to generate OAuth2 tokens to connect to
Oracle Autonomous Database with mutual TLS (mTLS). See :ref:`autonomousdb`.

**Standalone Connections in Thin Mode Using OAuth2 Tokens**

When using the :ref:`azure_tokens <azurecloudnativeauthplugin>` plugin to
generate OAuth2 tokens to connect to Oracle Autonomous Database in Thin mode,
you need to explicitly set the ``extra_auth_params`` parameter, and also any
required ``config_dir``, ``wallet_location``, and ``wallet_password``
parameters of :func:`~oracledb.connect`. For example:

.. code:: python

    import oracledb.plugins.azure_tokens

    token_based_auth = {
        "auth_type": "AzureServicePrincipal", # Azure specific configuration
        "authority": <authority>,             # parameters to be set when using
        "client_id": <client_id>,             # the azure_tokens plugin
        "client_credential": <client_credential>,
        "scopes": <scopes>
    }

    connection = oracledb.connect(
        dsn=mydb_low,
        config_dir="path_to_unzipped_wallet",
        wallet_location="location_of_pem_file",
        wallet_password=wp,
        extra_auth_params=token_based_auth)

**Connection Pools in Thin Mode Using OAuth2 Tokens**

When using the :ref:`azure_tokens <azurecloudnativeauthplugin>` plugin to
generate OAuth2 tokens to connect to Oracle Autonomous Database in Thin mode,
you need to explicitly set the ``extra_auth_params`` parameter of
:func:`~oracledb.create_pool`, and also any desired ``config_dir``,
``wallet_location``, and ``wallet_password`` parameters. The ``homogeneous``
parameter must be *True* (its default value). For example:

.. code:: python

    import oracledb.plugins.azure_tokens

    token_based_auth = {
        "auth_type": "AzureServicePrincipal", # Azure specific configuration
        "authority": <authority>,             # parameters to be set when using
        "client_id": <client_id>,             # the azure_tokens plugin
        "client_credential": <client_credential>,
        "scopes": <scopes>
    }

    connection = oracledb.create_pool(
        dsn=mydb_low,
        config_dir="path_to_unzipped_wallet",
        homogeneous=true,          # must always be True for connection pools
        wallet_location="location_of_pem_file",
        wallet_password=wp,
        extra_auth_params=token_based_auth)

**Standalone Connections Thick Mode Using OAuth2 Tokens**

When using the :ref:`azure_tokens <azurecloudnativeauthplugin>` plugin to
generate OAuth2 tokens to connect to Oracle Autonomous Database in Thick mode,
you need to explicitly set the ``extra_auth_params`` and ``externalauth``
parameters of :func:`~oracledb.connect`. For example:

.. code:: python

    import oracledb.plugins.azure_tokens

    token_based_auth = {
        "auth_type": "AzureServicePrincipal", # Azure specific configuration
        "authority": <authority>,             # parameters to be set when using
        "client_id": <client_id>,             # the azure_tokens plugin
        "client_credential": <client_credential>,
        "scopes": <scopes>
    }

    connection = oracledb.connect(
        externalauth=True,  # must always be True in Thick mode
        dsn=mydb_low,
        extra_auth_params=token_based_auth)

**Connection Pools in Thick Mode Using OAuth2 Tokens**

When using the :ref:`azure_tokens <azurecloudnativeauthplugin>` plugin to
generate OAuth2 tokens to connect to Oracle Autonomous Database in Thick mode,
you need to explicitly set the ``extra_auth_params`` and ``externalauth``
parameters of :func:`~oracledb.create_pool`. The ``homogeneous`` parameter must
be *True* (its default value). For example:

.. code:: python

    import oracledb.plugins.azure_tokens

    token_based_auth = {
        "auth_type": "AzureServicePrincipal", # Azure specific configuration
        "authority": <authority>,             # parameters to be set when using
        "client_id": <client_id>,             # the azure_tokens plugin
        "client_credential": <client_credential>,
        "scopes": <scopes>
    }

    connection = oracledb.create_pool(
        externalauth=True, # must always be True in Thick mode
        homogeneous=True,  # must always be True for connection pools
        dsn=mydb_low,
        extra_auth_params=token_based_auth)

.. _instanceprincipalauth:

Instance Principal Authentication
=================================

With Instance Principal Authentication, Oracle Cloud Infrastructure (OCI)
compute instances can be authorized to access services on Oracle Cloud such as
Oracle Autonomous Database. Python-oracledb applications running on such a
compute instance do not need to provide database user credentials.

Each compute instance behaves as a distinct type of Identity and Access
Management (IAM) Principal, that is, each compute instance has a unique
identity in the form of a digital certificate which is managed by OCI. When
using Instance Principal Authentication, a compute instance authenticates with
OCI IAM using this identity and obtains a short-lived token. This token is
then used to access Oracle Cloud services without storing or managing any
secrets in your application.

The example below demonstrates how to connect to Oracle Autonomous
Database using Instance Principal authentication. To enable this, use
python-oracledb's :ref:`oci_tokens <ocicloudnativeauthplugin>` plugin which
is pre-installed with the ``oracledb`` module.

**Step 1: Create an OCI Compute Instance**

An `OCI compute instance <https://docs.oracle.com/en-us/iaas/compute-cloud-at-
customer/topics/compute/compute-instances.htm>`__ is a virtual machine running
within OCI that provides compute resources for your application. This compute
instance will be used to authenticate access to Oracle Cloud services when
using Instance Principal Authentication.

To create an OCI compute instance, see the steps in `Creating an Instance
<https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/
launchinginstance.htm>`__ section of the Oracle Cloud Infrastructure
documentation.

For more information on OCI compute instances, see `Calling Services from a
Compute Instance <https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/
callingservicesfrominstances.htm>`__.

**Step 2: Install the OCI CLI on your compute instance**

The `OCI Command Line Interface (CLI) <https://docs.oracle.com/en-us/iaas/
Content/API/Concepts/cliconcepts.htm>`__ that can be used on its own or with
the Oracle Cloud console to complete OCI tasks.

To install the OCI CLI on your compute instance, see the installation
instructions in the `Installing the CLI <https://docs.oracle.com/en-us/iaas/
Content/API/SDKDocs/cliinstall.htm>`__ section of Oracle Cloud Infrastructure
documentation.

**Step 3: Create a Dynamic Group**

A Dynamic Group is used to define rules to group the compute instances that
require access.

To create a dynamic group using the Oracle Cloud console, see the steps in the
`To create a dynamic group <https://docs.oracle.com/en-us/iaas/Content/
Identity/Tasks/managingdynamicgroups.htm#>`__ section of the Oracle Cloud
Infrastructure documentation.

**Step 4: Create an IAM Policy**

An IAM Policy is used to grant a dynamic group permission to access the
required OCI services such as Oracle Autonomous Database. If the scope is not
set, the policy should be for the specified tenancy.

To create an IAM policy using Oracle Cloud console, see the steps in the
`Create an IAM Policy <https://docs.oracle.com/en-us/iaas/application-
integration/doc/creating-iam-policy.html>`__ section of the Oracle Cloud
Infrastructure documentation.

**Step 5: Map an Instance Principal to an Oracle Database User**

You must map the Instance Principal to an Oracle Database user. For more
information, see `Accessing the Database Using an Instance Principal
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-1B648FB0-BE86-
4BCE-91D0-239D287C638B>`__.

Also, make sure that external authentication is enabled on Oracle ADB and
Oracle Database parameter ``IDENTITY_PROVIDER_TYPE`` is set to *OCI_IAM*.
For the steps, see `Enable IAM Authentication on ADB <https://docs.oracle.com/
en/cloud/paas/autonomous-database/serverless/adbsb/enable-iam-authentication
.html>`__.

**Step 6: Deploy your application on the Compute Instance**

To use Instance Principal authentication, set ``extra_auth_params`` when
creating a standalone connection or a connection pool. The defined IAM policy
must allow access according to the specified scope. For information on the
keys of the ``extra_auth_params`` parameter, see
:ref:`_oci_configuration_parameters`.

An example of connecting using Instance Principal:

.. code-block:: python

    import oracledb
    import oracledb.plugins.oci_tokens

    token_based_auth = {
      "auth_type": "InstancePrincipal"
    }

    connection = oracledb.connect(
        dsn=mydb_low,
        extra_auth_params=token_based_auth
    )

.. _configproviderauthmethods:

Authentication Methods for Centralized Configuration Providers
==============================================================

You may need to provide authentication methods to access a centralized
configuration provider. The authentication methods for the following
centralized configuration providers are detailed in this section:

- :ref:`OCI Object Storage Centralized Configuration Provider
  <ociobjectstorageauthmethods>`

- :ref:`Azure App Centralized Configuration Provider <azureappauthmethods>`

.. _ociobjectstorageauthmethods:

OCI Object Storage Configuration Provider Authentication Methods
----------------------------------------------------------------

An Oracle Cloud Infrastructure (OCI) authentication method can be used to
access the OCI Object Storage centralized configuration provider. The
authentication methood can be set in the ``<option>=<value>`` parameter of
an :ref:`OCI Object Storage connection string <connstringoci>`. Depending on
the specified authentication method, you must also set the corresponding
authentication parameters in the connection string.

You can specify one of the authentication methods listed below.

**API Key-based Authentication**

The authentication to OCI is done using API key-related values. This is the
default authentication method. Note that this method is used when no
authentication value is set or by setting the option value to *OCI_DEFAULT*.

The optional authentication parameters that can be set for this method are
*OCI_PROFILE*, *OCI_TENANCY*, *OCI_USER*, *OCI_FINGERPRINT*, *OCI_KEY_FILE*,
and *OCI_PASS_PHRASE*. These authentication parameters can also be set in an
OCI Authentication Configuration file which can be stored in a default
location *~/.oci/config*, or in location *~/.oraclebmc/config*, or in the
location specified by the OCI_CONFIG_FILE environment variable. See
`Authentication Parameters for Oracle Cloud Infrastructure (OCI) Object
Storage <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-EB94F084
-0F3F-47B5-AD77-D111070F7E8D>`__.

**Instance Principal Authentication**

The authentication to OCI is done using VM instance credentials running on
OCI. To use this method, set the option value to *OCI_INSTANCE_PRINCIPAL*.
There are no optional authentication parameters that can be set for this
method.

**Resource Principal Authentication**

The authentication to OCI is done using OCI resource principals. To use this
method, you must set the option value to OCI_RESOURCE_PRINCIPAL. There are no
optional authentication parameters that can be set for this method.

For more information on these authentication methods, see `OCI Authentication
Methods <https://docs.oracle.com/en-us/iaas/Content/API/Concepts/
sdk_authentication_methods.htm>`__.

.. _azureappauthmethods:

Azure App Configuration Provider Authentication Methods
-------------------------------------------------------

A Microsoft Azure authentication method can be used to access the Azure App
centralized configuration provider. The authentication methood can be set in
the ``<option>=<value>`` parameter of an :ref:`Azure App connection string
<connstringazure>`. Depending on the specified authentication method, you must
also set the corresponding authentication parameters in the connection string.

**Default Azure Credential**

The authentication to Azure App Configuration is done as a service principal
(using either a client secret or client certificate) or as a managed identity
depending on which parameters are set. This authentication method also
supports reading the parameters as environment variables. This is the default
authentication method. This method is used when no authentication value is set
or by setting the option value to *AZURE_DEFAULT*.

The optional parameters that can be set for this option include
*AZURE_CLIENT_ID*, *AZURE_CLIENT_SECRET*, *AZURE_CLIENT_CERTIFICATE_PATH*,
*AZURE_TENANT_ID*, and *AZURE_MANAGED_IDENTITY_CLIENT_ID*. For more
information on these parameters, see `Authentication Parameters for Azure App
Configuration Store <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
GUID-1EECAD82-6CE5-4F4F-A844-C75C7AA1F907>`__.

**Service Principal with Client Secret**

The authentication to Azure App Configuration is done using the client secret.
To use this method, you must set the option value to
*AZURE_SERVICE_PRINCIPAL*. The required parameters that must be set for this
option include *AZURE_SERVICE_PRINCIPAL*, *AZURE_CLIENT_ID*,
*AZURE_CLIENT_SECRET*, and *AZURE_TENANT_ID*. For more
information on these parameters, see `Authentication Parameters for Azure App
Configuration Store <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
GUID-1EECAD82-6CE5-4F4F-A844-C75C7AA1F907>`__.

**Service Principal with Client Certificate**

The authentication to Azure App Configuration is done using the client
certificate. To use this method, you must set the option value to
*AZURE_SERVICE_PRINCIPAL*. The required parameters that must be set for this
option are *AZURE_SERVICE_PRINCIPAL*, *AZURE_CLIENT_ID*,
*AZURE_CLIENT_CERTIFICATE_PATH*, and *AZURE_TENANT_ID*. For more information
on these parameters, see `Authentication Parameters for Azure App
Configuration Store <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
GUID-1EECAD82-6CE5-4F4F-A844-C75C7AA1F907>`__.

Note that the Service Principal with Client Certificate authentication method
overrides Service Principal with Client Secret authentication method.

**Managed Identity**

The authentication to Azure App Configuration is done using managed identity
or managed user identity credentials. To use this method, you must set the
option value to *AZURE_MANAGED_IDENTITY*. If you want to use a user-assigned
managed identity for authentication, then you must specify the required
parameter *AZURE_MANAGED_IDENTITY_CLIENT_ID*. For more information on these
parameters, see `Authentication Parameters for Azure App Configuration Store
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-1EECAD82-6CE5-
4F4F-A844-C75C7AA1F907>`__.
