# Python python-oracledb Notebooks

This directory contains Jupyter notebooks showing best practices for using
python-oracledb.  The notebooks cover:

- Connecting
- Queries
- DML
- Transactions
- Data frames
- Data loading and unloading (CSV Files)
- JSON
- PL/SQL
- Vectors
- Objects

Python-oracledb's default 'Thin' mode is used.

Jupyter notebooks let you easily step through, modify, and execute Python code:

![A screenshot of a notebook running in a browser](./images/jupyter-notebook-screenshot.png)

# Setup

An existing Oracle Database is required.  The JSON demo assumes that Oracle
Database 21c or later is being used.  The VECTOR demo assumes that Oracle AI
Database 26ai is being used.

### Install Python

See https://www.python.org/downloads/

### Install Jupyter

See https://jupyter.org/install:

    python -m pip install notebook

### Install the python-oracledb driver

    python -m pip install oracledb

### Install some libraries used by the examples

    python -m pip install numpy matplotlib pyarrow pandas

### Create the python-oracledb sample schema

Clone the python-oracledb repository, for example in a terminal window:

    git clone https://github.com/oracle/python-oracledb.git

    cd python-oracledb/samples

Review README.md and sample_env.py

In the terminal, set desired credentials, for example:

    export PYO_SAMPLES_ADMIN_USER=system
    export PYO_SAMPLES_ADMIN_PASSWORD=oracle
    export PYO_SAMPLES_CONNECT_STRING=localhost/orclpdb
    export PYO_SAMPLES_MAIN_USER=pythondemo
    export PYO_SAMPLES_MAIN_PASSWORD=welcome
    export PYO_SAMPLES_EDITION_USER=pythoneditions
    export PYO_SAMPLES_EDITION_PASSWORD=welcome
    export PYO_SAMPLES_EDITION_NAME=python_e1

Install the schema:

    python create_schema.py

### Start Jupyter

    cd notebooks

    export PYO_SAMPLES_ADMIN_USER=system
    export PYO_SAMPLES_ADMIN_PASSWORD=oracle
    export PYO_SAMPLES_CONNECT_STRING=localhost/orclpdb
    export PYO_SAMPLES_MAIN_USER=pythondemo
    export PYO_SAMPLES_MAIN_PASSWORD=welcome

    jupyter notebook

If Jupyter is not in your path, you may need to find it on your computer and
invoke it with an absolute path, for example on macOS:

    $HOME/Library/Python/3.9/bin/jupyter notebook

Load each notebook *.ipynb file and step through the cells.

The notebooks will use the environment variables above for connection
credentials. However, if these variables are not set in the terminal window
that you start Jupyter in, then edit the credentials and connect string near
the top of each notebook. Set the same values you used when installing the
schema.
