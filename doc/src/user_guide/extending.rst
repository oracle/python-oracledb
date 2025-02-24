.. _extendingpython-oracledb:

*************************
Extending python-oracledb
*************************

You can extend the capabilities of python-oracledb by using standard Python
functionality for :ref:`subclassing python-oracledb classes <subclassconn>`.
You can also use :ref:`python-oracledb plugins <customplugins>`,
:ref:`connection protocol hooks <protocolhook>`, :ref:`connection password
hooks <passwordhook>`, and :ref:`connection parameter hooks <paramshook>`.

.. _subclassconn:

Subclassing Connections
=======================

Subclassing enables applications to change python-oracledb, for example by
extending connection and statement execution behvior. This can be used to
alter, or log, connection and execution parameters, or to further change
python-oracledb functionality.

The example below demonstrates subclassing a connection to log SQL execution
to a file.  This example also shows how connection credentials can be embedded
in the custom subclass, so application code does not need to supply them.

.. code-block:: python

    class Connection(oracledb.Connection):
        log_file_name = "log.txt"

        def __init__(self):
            connect_string = "hr/hr_password@dbhost.example.com/orclpdb"
            self._log("Connect to the database")
            return super(Connection, self).__init__(connect_string)

        def _log(self, message):
            with open(self.log_file_name, "a") as f:
                print(message, file=f)

        def execute(self, sql, parameters):
            self._log(sql)
            cursor = self.cursor()
            try:
                return cursor.execute(sql, parameters)
            except oracledb.Error as e:
                error_obj, = e.args
                self._log(error_obj.message)
                raise

    connection = Connection()
    connection.execute("""
            select department_name
            from departments
            where department_id = :id""", dict(id=270))

The messages logged in ``log.txt`` are::

    Connect to the database

                select department_name
                from departments
                where department_id = :id

If an error occurs, perhaps due to a missing table, the log file would contain
instead::

    Connect to the database

                select department_name
                from departments
                where department_id = :id
    ORA-00942: table or view does not exist

In production applications, be careful not to log sensitive information.

See `Subclassing.py
<https://github.com/oracle/python-oracledb/blob/main/
samples/subclassing.py>`__ for an example.

.. _plugins:

Python-oracledb Plugins
=======================

Plugins simplify extending python-oracledb functionality, and optionally allow
the distribution of such extensions as modules. The plugin mechanism provides a
loose coupling for python-oracledb, permitting different python-oracledb
configurations.

Examples are the pre-supplied plugins for :ref:`Centralized Configuration
Providers <configurationproviders>`. The loose coupling allows these plugins to
be included with all python-oracledb installations but the large Python SDK
modules used by the plugins are not installed as python-oracledb
dependencies. Only users who want to use a specific configuration provider
plugin need to install its required SDK.

All python-oracledb installations bundle the following plugins:

- ``oci_config_provider`` which allows connection and pool creation calls to
  access connection configuration information stored in OCI Object Storage. See
  :ref:`ociobjstorageprovider`.

- ``azure_config_provider`` which allows connection and pool creation calls to
  access connection configuration information stored using Azure App
  Configuration. See :ref:`azureappstorageprovider`.

- ``oci_tokens`` which uses the `Oracle Cloud Infrastructure (OCI) Software
  Development Kit (SDK) <https://docs.oracle.com/en-us/iaas/Content/API/
  Concepts/sdkconfig.htm>`__ to generate access tokens when authenticating with
  OCI Identity and Access Management (IAM) token-based authentication. See
  :ref:`cloudnativeauthoci`.

- ``azure_tokens`` which uses the `Microsoft Authentication Library (MSAL)
  <https://learn.microsoft.com/en-us/entra/msal/python/?view=msal-py-
  latest>`__ to generate access tokens when authenticating with OAuth 2.0
  token-based authentication. See :ref:`cloudnativeauthoauth`.

To import these python-oracledb plugins in your application, use
``import oracledb.plugins.<name of plugin>``, for example::

    import oracledb.plugins.oci_tokens

Note that the namespace ``oracledb.plugins.ldap_support`` is reserved for
future use by the python-oracledb project.

.. _customplugins:

Building Custom Plugins
-----------------------

If you want to use the :ref:`plugin mechanism <oracledbplugins>` for your own
packages, you can create a `namespace package <https://packaging.python.org/en
/latest/guides/packaging-namespace-packages/#native-namespace-packages>`__. You
can distribute plugin packages either internally within your organization, or
on a package repository such as `PyPI <https://pypi.org/>`__.

The following example creates a plugin that uses a :ref:`connection protocol
hook function <registerprotocolhook>` to do special processing of connection
strings prefixed with "myprefix://".

1. In a terminal or IDE, create a working directory, for example ``myplugin``.
   Inside the working directory create the subdirectory hierarchy
   ``src/oracledb/plugins/``::

    mkdir myplugin
    mkdir -p myplugin/src/oracledb/plugins

2. In the ``myplugin`` directory, create the following files:

   - A ``README`` file::

           My sample connection plugin.

   - A ``pyproject.toml`` file::

           [build-system]
           requires = ["setuptools"]
           build-backend = "setuptools.build_meta"

   - A ``setup.cfg`` file::

           [metadata]
           name = myplugin
           version = 1.0.0
           description = Sample connection plugin for python-oracleb
           long_description = file: README
           long_description_content_type = text/markdown
           author = Your Name
           author_email = youremail@example.com
           license = Apache Software License

           [options]
           zip_safe = False
           package_dir =
               =src

           [options.packages.find]
           where = src

3. Create the plugin code in ``myplugin/src/oracledb/plugins/myplugin.py``:

  .. code-block:: python

        import oracledb

        def myhookfunc(protocol, arg, params):
            print(f"In myhookfunc: protocol={protocol} arg={arg}")
            params.parse_connect_string(arg)

        oracledb.register_protocol("myprefix", myhookfunc)


4. Build the sample package::

        cd myplugin
        python -m pip install build
        python -m build

5. Install the sample package::

        python -m pip install dist/myplugin-1.0.0-py3-none-any.whl

6. To show the plugin being used, create an application file containing:

   .. code-block:: python

        import oracledb
        import oracledb.plugins.myplugin

        cs = 'myprefix://localhost/orclpdb1'

        cp = oracledb.ConnectParams()
        cp.parse_connect_string(cs)

        print(f"host={cp.host}, port={cp.port}, service name={cp.service_name}")

   Running this will print::

        In myhookfunc: protocol=myprefix arg=localhost/orclpdb1
        host=localhost, port=1521, service name=orclpdb1

7. To uninstall the plugin, simply remove the packge::

       python -m pip uninstall myplugin

.. _connectionhooks:

Connection Hooks
================

Connection hooks allow you to modify the connection logic based on your needs.
The hooks supported by python-oracledb are listed in this section.

.. _protocolhook:

Connection Protocol Hooks
-------------------------

The :meth:`oracledb.register_protocol()` method registers a user protocol hook
function that can be called internally by python-oracledb prior to connection
or pool creation.

See :ref:`registerprotocolhook` for usage information.

.. _passwordhook:

Connection Password Hooks
-------------------------

The :meth:`oracledb.register_password_type()` method registers a user password
hook function that will be called internally by python-oracledb prior to
connection or pool creation.

See :ref:`registerpasswordtype` for usage information.

.. _paramshook:

Connection Parameter Hooks
--------------------------

The :meth:`oracledb.register_params_hook()` method registers a user parameter
hook function that will be called internally by python-oracledb prior to
connection or pool creation.

See :ref:`registerparamshook` for usage information.
