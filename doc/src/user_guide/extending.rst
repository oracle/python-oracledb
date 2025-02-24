.. _extendingpython-oracledb:

*************************
Extending python-oracledb
*************************

You can extend the capabilities of python-oracledb by
:ref:`subclassing python-oracledb classes <subclassconn>` and also by using
:ref:`plugins <customplugins>`.

.. _subclassconn:

Subclassing Connections
=======================

Subclassing enables applications to add "hooks" for connection and statement
execution.  This can be used to alter or log connection and execution
parameters, and to extend python-oracledb functionality.

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

Plugins simplify extending python-oracledb functionality and the distribution
of modules. The plugin mechanism lets these plugins use large Python modules
without requiring python-oracledb users to install these modules. You can use
plugins to extend python-oracledb with your own `namespace package
<https://packaging.python.org/en/latest/guides/
packaging-namespace-packages/#native-namespace-packages>`__. Python-oracledb
provides two plugins ``oracledb.plugins.oci_config_provider`` and
``oracledb.plugins.azure_config_provider`` which allow you to access the
configuration information stored in OCI Object Storage and Azure App
Configuration respectively, and connect to Oracle Database. See
:ref:`ociobjstorageprovider` and :ref:`azureappstorageprovider` for more
information. Note that the namespace ``oracledb.plugins.ldap_support`` is
reserved for future use by the python-oracledb project.

.. _customplugins:

Building Custom Plugins
-----------------------

If you want to use the :ref:`plugin mechanism <oracledbplugins>` for your own
packages, you can create a `namespace package <https://packaging.python.org/en
/latest/guides/packaging-namespace-packages/#native-namespace-packages>`__.

The following example creates a plugin that uses a :ref:`connection hook
function <connectionhook>` to do special processing of connection strings
prefixed with "myprefix://".

The example uses the following files:

- A ``README`` file which contains::

        My sample connection plugin

- A ``pyproject.toml`` file which contains::

        [build-system]
        requires = ["setuptools"]
        build-backend = "setuptools.build_meta"

- A ``setup.cfg`` file which contains::

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

- The plugin code file ``src/oracledb/plugins/myplugin.py`` which contains:

  .. code-block:: python

        import oracledb

        def myhookfunc(protocol, arg, params):
            print(f"In myhookfunc: protocol={protocol} arg={arg}")
            params.parse_connect_string(arg)

        oracledb.register_protocol("myprefix", myhookfunc)

To use the plugin, perform the following steps:

1. Build the sample package::

        python -m pip install build
        python -m build

2. Install the sample package::

        python -m pip install dist/myplugin-1.0.0-py3-none-any.whl

3. To show the plugin being used, create an application file containing:

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

You can distribute the created package either internally or on a package
repository.
