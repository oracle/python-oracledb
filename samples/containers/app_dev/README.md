# Oracle python-oracledb environment for Python application developers

This Dockerfile creates a sample Oracle Linux container with the Oracle Python
driver python-oracledb, the Apache web server with WSGI, and (optionally)
Oracle Instant Client.  You need to have access to an existing database.

A sample Flask application can optionally be deployed.

This image can be used for development and deployment of Python applications
for demonstrations and testing.

It has been tested on macOS using podman and docker.

## Build Instructions

- Edit `container_build.env` and set your desired values.

- Build the container image using the `container_build.sh` script:

  ```
  ./container_build.sh
  ```

  By default, Apache has SSL enabled and is listening on port 8443.

## Usage for Application Devlopment

- Run a container:

  ```
  podman run -it -p 8443:8443 --name my_python_dev pyorcldbdev
  ```

  You can now create and run your own Python applications using the `python`
  binary.

  See lower for how to deploy applications such as the sample Flask application
  in the container.

- If you want to use the Apache HTTP server, it is configured with the WSGI
  module. The listening port is set to 8443. (Note port 80 is disabled).

  The Python home for the WSGI module is `/opt/pyorcldb_env`.  Refer to the
  Apache HTTP server configuration file
  `/opt/apache/conf/extra/pyorcldb_wsgi.conf` for more information.

  To start Apache in the container:

  ```
  $ apachectl start
  ```

  To stop Apache:

  ```
  $ apachectl stop
  ```

- An Oracle Database wallet and/or `tnsnames.ora` file can be copied into, or
  mounted in, `/opt/wallet` to connect to Oracle Database or Oracle Autonomous
  Database.

- By default, the Python virtual environment file `/opt/pyorcldb_env` is
  sourced in the bash shell. The virtual environment can be enabled or
  disabled.

  To enable the Python virtual environment:

  ```
  $ source /opt/pyorcldb_env/bin/activate
  ```

  To disable the Python virtual environment:

  ```
  $ deactivate
  ```

## Container Environment

### Default Environment

- Oracle Linux 8
- Python 3.12
- Apache HTTP server 2.4

### Optional packages

- Oracle Instant Client (Basic and SQL*Plus packages)

  By default, Oracle Instant Client is not installed. If you require it, select
  the version in
  `python-oracledb/samples/containers/app_dev/container_build.env` before
  building the container image.

  Supported versions: 23ai, 21c and 19c

  Recommended version: 23ai


### Python modules pre-installed

- Oracle Database driver for Python - oracledb (latest available version)
- Pre-requisites for oracledb - cffi, cryptography, pycparser

### Default Apache HTTP configuration

- Server name         - pyorcldbdemo
- Protocol            - HTTPS
- Port #              - 8443
- WSGI Python home    - `/opt/env/pyorcldb_env`
- SSL certificate     - `/opt/cert/certificate.pem` (For demo and testing purposes)
- SSL certificate key - `/opt/cert/privatekey.pem` (For demo and testing purposes)
- Document root       - `/opt/app`
- Error log           - `/opt/apache/logs/pyorcldb_error.log`
- Custom log          - `/opt/apache/logs/appstack_app_access.log`

### Directories

- Python application home     - `/opt/app`
- Python virtual environment  - `/opt/pyorcldb_env`
- Apache HTTP server home     - `/opt/apache`
- Oracle Database wallet home - `/opt/wallet`
- SSL certificate and key     - `/opt/cert` (For demo and testing purposes)

### The default SSL certificate and key

The SSL certificate and key generated in `/opt/cert` can be used for demo and
testing purposes only.  This is strictly not for production use. Configure or
replace them with your own certificate and key.

## Deploying the Sample Flask Application

The GitHub directory
[samples/containers/app_dev/sample_app](https://github.com/oracle/python-oracledb/tree/main/samples/containers/app_dev/sample_app)
contains a sample Flask web application that queries a small customer
database. This application can be enabled by copying or mounting it into the
container.

The sample application uses database credentials set via environment variables:

1. `PYO_SAMPLES_MAIN_USER` - Oracle Database username
2. `PYO_SAMPLES_MAIN_PASSWORD` -  Oracle Database password
3. `PYO_SAMPLES_CONNECT_STRING` - Oracle Database TNS Alias or Easy Connect
   string
4. `TNS_ADMIN` - The location of the tnsnames.ora file or wallet files
5. `PYO_SAMPLES_WALLET_PASSWORD` - Oracle Database wallet password
6. `PYO_SAMPLES_WALLET_LOCATION` - Oracle Database wallet location. This
   variable is optional and the sample application will use TNS_ADMIN path as
   wallet location when this variable is not set.

Here is an example to deploy the sample application without a database wallet:

```
podman run -it -p 8443:8443 --env DEPLOY_APP="TRUE" --env APP_NAME="customer" \
  --env PYO_SAMPLES_MAIN_USER="user" --env PYO_SAMPLES_MAIN_PASSWORD="passwd" \
  --env PYO_SAMPLES_CONNECT_STRING="myhostname:1521/mydbservicename" \
  -v ./sample_app:/opt/app --name my_app1 pyorcldbdev
```

Here is an example to deploy the sample application with a database wallet, for
example to connect to Oracle Autonomous Database Serverless (ADB-S):

```
podman run -it -p 8443:8443 --env DEPLOY_SAMPLE_APP="TRUE" \
  --env APP_NAME="customer" --env PYO_SAMPLES_MAIN_USER="myuserid" \
  --env PYO_SAMPLES_MAIN_PASSWORD="mypassword" \
  --env PYO_SAMPLES_CONNECT_STRING="mydb1" \
  --env PYO_SAMPLES_WALLET_PASSWORD="mywalletpassword" \
  --env TNS_ADMIN=/opt/wallet -v ./sample_app:/opt/app \
  -v /disk/path/mywallet:/opt/wallet --name my_app1 \
  pyorcldbdev
```

The application will be installed in the container in `/opt/app`.

The deployed sample application can be accessed using the host browser with the
URL:

```
https://localhost:8443/app/customer
```

Because the SSL certificate is self-signed, you may have to accept accessing
the URL in the browser.

Review log files such as `/opt/apache/logs/pyorcldb_error.log` if you have
problems accessing the application.

## Deploying your own Flask Application

Your own Python Flask application can be easily deployed with Apache. The
following setup is required:

- In your application directory, run `pip freeze > requirements.txt` to
  generate a `requirements.txt` file for installing Python libraries required
  for the application.

  Note that the application does not need to bundle the Python virtual
  environment: this container will create one.

- Add a WSGI file `pyorcldb_app.wsgi` in the root directory of the application
  and configure the application. For example:

  ```
  from mymodule1 import app as application

  def func1():
      return application
  ```

  In the above code, `app` is the Flask object created in the Python module
  `mymodule1.py`.  That Flask object is renamed to `application` to comply with
  the naming conventions expected by the WSGI server.

- Set the module name in the environment variable `APP_NAME` and set
  `DEPLOY_APP` to `TRUE` while creating the container.

Here is a sample command to deploy a Flask application while creating the
container:

```
podman run -it -p 8443:8443 --env DEPLOY_APP="TRUE" --env APP_NAME="mymodule1" \
  -v /mydisk/myapplication:/opt/app --name myapp2 pyorcldbdev
```

Pass in any other environment as required by your application, for example the
database connection details.

This command will deploy your application into the container `myapp2` under
directory `/opt/app`. The auto-deployment will start the Apache HTTP server on
port 8443.

The URL of the deployed Flask application or web service will be in this
pattern `https://localhost:8443/app/<API/route name>`. The URL for the above
sample `podman run` command is `https://localhost:8443/app/mymodule1`.
