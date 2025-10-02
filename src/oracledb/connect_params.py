# -----------------------------------------------------------------------------
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl and Apache License
# 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose
# either license.
#
# If you elect to accept the software under the Apache License, Version 2.0,
# the following applies:
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# connect_params.py
#
# Contains the ConnectParams class used for managing the parameters required to
# establish a connection to the database.
#
# *** NOTICE *** This file is generated from a template and should not be
# modified directly. See build_from_template.py in the utils subdirectory for
# more information.
# -----------------------------------------------------------------------------

import functools
import ssl
from typing import Union, Callable, Any, Optional

import oracledb

from .base import BaseMetaClass
from . import base_impl, utils


class ConnectParams(metaclass=BaseMetaClass):
    """
    Contains all parameters used for establishing a connection to the
    database.
    """

    __slots__ = ["_impl"]
    _impl_class = base_impl.ConnectParamsImpl

    @utils.params_initer
    def __init__(
        self,
        *,
        user: Optional[str] = None,
        proxy_user: Optional[str] = None,
        password: Optional[str] = None,
        newpassword: Optional[str] = None,
        wallet_password: Optional[str] = None,
        access_token: Optional[Union[str, tuple, Callable]] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        protocol: Optional[str] = None,
        https_proxy: Optional[str] = None,
        https_proxy_port: Optional[int] = None,
        service_name: Optional[str] = None,
        instance_name: Optional[str] = None,
        sid: Optional[str] = None,
        server_type: Optional[str] = None,
        cclass: Optional[str] = None,
        purity: Optional[oracledb.Purity] = None,
        expire_time: Optional[int] = None,
        retry_count: Optional[int] = None,
        retry_delay: Optional[int] = None,
        tcp_connect_timeout: Optional[float] = None,
        ssl_server_dn_match: Optional[bool] = None,
        ssl_server_cert_dn: Optional[str] = None,
        wallet_location: Optional[str] = None,
        events: Optional[bool] = None,
        externalauth: Optional[bool] = None,
        mode: Optional[oracledb.AuthMode] = None,
        disable_oob: Optional[bool] = None,
        stmtcachesize: Optional[int] = None,
        edition: Optional[str] = None,
        tag: Optional[str] = None,
        matchanytag: Optional[bool] = None,
        config_dir: Optional[str] = None,
        appcontext: Optional[list] = None,
        shardingkey: Optional[list] = None,
        supershardingkey: Optional[list] = None,
        debug_jdwp: Optional[str] = None,
        connection_id_prefix: Optional[str] = None,
        ssl_context: Optional[Any] = None,
        sdu: Optional[int] = None,
        pool_boundary: Optional[str] = None,
        use_tcp_fast_open: Optional[bool] = None,
        ssl_version: Optional[ssl.TLSVersion] = None,
        program: Optional[str] = None,
        machine: Optional[str] = None,
        terminal: Optional[str] = None,
        osuser: Optional[str] = None,
        driver_name: Optional[str] = None,
        use_sni: Optional[bool] = None,
        thick_mode_dsn_passthrough: Optional[bool] = None,
        extra_auth_params: Optional[dict] = None,
        pool_name: Optional[str] = None,
        handle: Optional[int] = None,
    ):
        """
        All parameters are optional. A brief description of each parameter
        follows:

        - ``user``: the name of the database user to connect to
          (default: None)

        - ``proxy_user``: the name of the proxy user to connect to. If this
          value is not specified, it will be parsed out of user if user is in
          the form "user[proxy_user]"
          (default: None)

        - ``password``: the password for the database user
          (default: None)

        - ``newpassword``: a new password for the database user. The new
          password will take effect immediately upon a successful connection to
          the database
          (default: None)

        - ``wallet_password``: the password to use to decrypt the wallet, if it
          is encrypted. This is not the database password. For Oracle
          Autonomous Database this is the password created when downloading the
          wallet. This value is only used in python-oracledb Thin mode.
          (default: None)

        - ``access_token``: a string, or a 2-tuple, or a callable. If it is a
          string, it specifies an Entra ID OAuth2 token used for Open
          Authorization (OAuth 2.0) token based authentication. If it is a
          2-tuple, it specifies the token and private key strings used for
          Oracle Cloud Infrastructure (OCI) Identity and Access Management
          (IAM) token based authentication. If it is a callable, it returns
          either a string or a 2-tuple used for OAuth 2.0 or OCI IAM token
          based authentication and is useful when the pool needs to expand and
          create new connections but the current authentication token has
          expired
          (default: None)

        - ``host``: the hostname or IP address of the machine hosting the
          database or the database listener
          (default: None)

        - ``port``: the port number on which the database listener is listening
          (default: 1521)

        - ``protocol``: one of the strings "tcp" or "tcps" indicating whether
          to use unencrypted network traffic or encrypted network traffic (TLS)
          (default: "tcp")

        - ``https_proxy``: the hostname or IP address of a proxy host to use
          for tunneling secure connections
          (default: None)

        - ``https_proxy_port``: the port on which to communicate with the proxy
          host
          (default: 0)

        - ``service_name``: the service name of the database
          (default: None)

        - ``instance_name``: the instance name of the database
          (default: None)

        - ``sid``: the system identifier (SID) of the database. Note using a
          service_name instead is recommended
          (default: None)

        - ``server_type``: the type of server connection that should be
          established. If specified, it should be one of strings "dedicated",
          "shared" or "pooled"
          (default: None)

        - ``cclass``: the connection class to use for Database Resident
          Connection Pooling (DRCP)
          (default: None)

        - ``purity``: the connection purity to use for Database Resident
          Connection Pooling (DRCP)
          (default: :attr:`oracledb.PURITY_DEFAULT`)

        - ``expire_time``: the number of minutes between the sending of
          keepalive probes. If this parameter is set to a value greater than
          zero it enables keepalive
          (default: 0)

        - ``retry_count``: the number of times that initial connection
          establishment should be retried before the connection attempt is
          terminated
          (default: 0)

        - ``retry_delay``: the number of seconds to wait before retrying to
          establish a connection
          (default: 1)

        - ``tcp_connect_timeout``: a float indicating the maximum number of
          seconds to wait when establishing a connection to the database host
          (default: 20.0)

        - ``ssl_server_dn_match``: a boolean indicating whether the server
          certificate distinguished name (DN) should be matched in addition to
          the regular certificate verification that is performed. Note that if
          the ssl_server_cert_dn parameter is not privided, host name matching
          is performed instead
          (default: True)

        - ``ssl_server_cert_dn``: the distinguished name (DN) which should be
          matched with the server. This value is ignored if the
          ssl_server_dn_match parameter is not set to the value True. If
          specified this value is used for any verfication. Otherwise the
          hostname will be used
          (default: None)

        - ``wallet_location``: the directory where the wallet can be found. In
          python-oracledb Thin mode this must be the directory containing the
          PEM-encoded wallet file ewallet.pem. In python-oracledb Thick mode
          this must be the directory containing the file cwallet.sso
          (default: None)

        - ``events``: a boolean specifying whether events mode should be
          enabled. This value is only used in python-oracledb Thick mode and is
          needed for continuous query notification and high availability event
          notifications
          (default: False)

        - ``externalauth``: a boolean indicating whether to use external
          authentication
          (default: False)

        - ``mode``: the authorization mode to use. One of the constants
          :data:`oracledb.AUTH_MODE_DEFAULT`,
          :data:`oracledb.AUTH_MODE_PRELIM`, :data:`oracledb.AUTH_MODE_SYSASM`,
          :data:`oracledb.AUTH_MODE_SYSBKP`, :data:`oracledb.AUTH_MODE_SYSDBA`,
          :data:`oracledb.AUTH_MODE_SYSDGD`, :data:`oracledb.AUTH_MODE_SYSKMT`,
          :data:`oracledb.AUTH_MODE_SYSOPER`, or
          :data:`oracledb.AUTH_MODE_SYSRAC`
          (default: :attr:`oracledb.AUTH_MODE_DEFAULT`)

        - ``disable_oob``: a boolean indicating whether out-of-band breaks
          should be disabled. This value is only used in python-oracledb Thin
          mode. It has no effect on Windows which does not support this
          functionality
          (default: False)

        - ``stmtcachesize``: the size of the statement cache
          (default: :attr:`oracledb.defaults.stmtcachesize
          <Defaults.stmtcachesize>`)

        - ``edition``: edition to use for the connection. This parameter cannot
          be used simultaneously with the cclass parameter
          (default: None)

        - ``tag``: identifies the type of connection that should be returned
          from a pool. This value is only used in python-oracledb Thick mode
          (default: None)

        - ``matchanytag``: a boolean specifying whether any tag can be used
          when acquiring a connection from the pool. This value is only used in
          python-oracledb Thick mode
          (default: False)

        - ``config_dir``: a directory in which the optional tnsnames.ora
          configuration file is located. This value is only used in python-
          oracledb Thin mode. For python-oracledb Thick mode, it is used if
          :attr:`oracledb.defaults.thick_mode_dsn_passthrough
          <Defaults.thick_mode_dsn_passthrough>` is *False*. Otherwise in Thick
          mode use the ``config_dir`` parameter of
          :meth:`oracledb.init_oracle_client()`
          (default: :attr:`oracledb.defaults.config_dir
          <Defaults.config_dir>`)

        - ``appcontext``: application context used by the connection. It should
          be a list of 3-tuples (namespace, name, value) and each entry in the
          tuple should be a string
          (default: None)

        - ``shardingkey``: a list of strings, numbers, bytes or dates that
          identify the database shard to connect to. This value is only used in
          python-oracledb Thick mode
          (default: None)

        - ``supershardingkey``: a list of strings, numbers, bytes or dates that
          identify the database shard to connect to. This value is only used in
          python-oracledb Thick mode
          (default: None)

        - ``debug_jdwp``: a string with the format "host=<host>;port=<port>"
          that specifies the host and port of the PL/SQL debugger. This value
          is only used in python-oracledb Thin mode.  For python-oracledb Thick
          mode set the ORA_DEBUG_JDWP environment variable
          (default: None)

        - ``connection_id_prefix``: an application specific prefix that is
          added to the connection identifier used for tracing
          (default: None)

        - ``ssl_context``: an SSLContext object used for connecting to the
          database using TLS.  This SSL context will be modified to include the
          private key or any certificates found in a separately supplied
          wallet. This parameter should only be specified if the default
          SSLContext object cannot be used
          (default: None)

        - ``sdu``: the requested size of the Session Data Unit (SDU), in bytes.
          The value tunes internal buffers used for communication to the
          database. Bigger values can increase throughput for large queries or
          bulk data loads, but at the cost of higher memory use. The SDU size
          that will actually be used is negotiated down to the lower of this
          value and the database network SDU configuration value
          (default: 8192)

        - ``pool_boundary``: one of the values "statement" or "transaction"
          indicating when pooled DRCP connections can be returned to the pool.
          This requires the use of DRCP with Oracle Database 23.4 or higher
          (default: None)

        - ``use_tcp_fast_open``: a boolean indicating whether to use TCP fast
          open. This is an Oracle Autonomous Database Serverless (ADB-S)
          specific property for clients connecting from within OCI Cloud
          network. Please refer to the ADB-S documentation for more information
          (default: False)

        - ``ssl_version``: one of the values ssl.TLSVersion.TLSv1_2 or
          ssl.TLSVersion.TLSv1_3 indicating which TLS version to use
          (default: None)

        - ``program``: a string recorded by Oracle Database as the program from
          which the connection originates
          (default: :attr:`oracledb.defaults.program
          <Defaults.program>`)

        - ``machine``: a string recorded by Oracle Database as the name of the
          machine from which the connection originates
          (default: :attr:`oracledb.defaults.machine
          <Defaults.machine>`)

        - ``terminal``: a string recorded by Oracle Database as the terminal
          identifier from which the connection originates
          (default: :attr:`oracledb.defaults.terminal
          <Defaults.terminal>`)

        - ``osuser``: a string recorded by Oracle Database as the operating
          system user who originated the connection
          (default: :attr:`oracledb.defaults.osuser
          <Defaults.osuser>`)

        - ``driver_name``: a string recorded by Oracle Database as the name of
          the driver which originated the connection
          (default: :attr:`oracledb.defaults.driver_name
          <Defaults.driver_name>`)

        - ``use_sni``: a boolean indicating whether to use the TLS SNI
          extension to bypass the second TLS neogiation that would otherwise be
          required
          (default: False)

        - ``thick_mode_dsn_passthrough``: a boolean indicating whether to pass
          the connect string to the Oracle Client libraries unchanged without
          parsing by the driver. Setting this to False makes python-oracledb
          Thick and Thin mode applications behave similarly regarding
          connection string parameter handling and locating any optional
          tnsnames.ora configuration file
          (default: :attr:`oracledb.defaults.thick_mode_dsn_passthrough
          <Defaults.thick_mode_dsn_passthrough>`)

        - ``extra_auth_params``: a dictionary containing configuration
          parameters necessary for Oracle Database authentication using
          plugins, such as the Azure and OCI cloud-native authentication
          plugins
          (default: None)

        - ``pool_name``: the name of the DRCP pool when using multi-pool DRCP
          with Oracle Database 23.4, or higher
          (default: None)

        - ``handle``: an integer representing a pointer to a valid service
          context handle. This value is only used in python-oracledb Thick
          mode. It should be used with extreme caution
          (default: 0)
        """
        pass

    def __repr__(self):
        return (
            self.__class__.__qualname__ + "("
            f"user={self.user!r}, "
            f"proxy_user={self.proxy_user!r}, "
            f"host={self.host!r}, "
            f"port={self.port!r}, "
            f"protocol={self.protocol!r}, "
            f"https_proxy={self.https_proxy!r}, "
            f"https_proxy_port={self.https_proxy_port!r}, "
            f"service_name={self.service_name!r}, "
            f"instance_name={self.instance_name!r}, "
            f"sid={self.sid!r}, "
            f"server_type={self.server_type!r}, "
            f"cclass={self.cclass!r}, "
            f"purity={self.purity!r}, "
            f"expire_time={self.expire_time!r}, "
            f"retry_count={self.retry_count!r}, "
            f"retry_delay={self.retry_delay!r}, "
            f"tcp_connect_timeout={self.tcp_connect_timeout!r}, "
            f"ssl_server_dn_match={self.ssl_server_dn_match!r}, "
            f"ssl_server_cert_dn={self.ssl_server_cert_dn!r}, "
            f"wallet_location={self.wallet_location!r}, "
            f"events={self.events!r}, "
            f"externalauth={self.externalauth!r}, "
            f"mode={self.mode!r}, "
            f"disable_oob={self.disable_oob!r}, "
            f"stmtcachesize={self.stmtcachesize!r}, "
            f"edition={self.edition!r}, "
            f"tag={self.tag!r}, "
            f"matchanytag={self.matchanytag!r}, "
            f"config_dir={self.config_dir!r}, "
            f"appcontext={self.appcontext!r}, "
            f"shardingkey={self.shardingkey!r}, "
            f"supershardingkey={self.supershardingkey!r}, "
            f"debug_jdwp={self.debug_jdwp!r}, "
            f"connection_id_prefix={self.connection_id_prefix!r}, "
            f"ssl_context={self.ssl_context!r}, "
            f"sdu={self.sdu!r}, "
            f"pool_boundary={self.pool_boundary!r}, "
            f"use_tcp_fast_open={self.use_tcp_fast_open!r}, "
            f"ssl_version={self.ssl_version!r}, "
            f"program={self.program!r}, "
            f"machine={self.machine!r}, "
            f"terminal={self.terminal!r}, "
            f"osuser={self.osuser!r}, "
            f"driver_name={self.driver_name!r}, "
            f"use_sni={self.use_sni!r}, "
            f"thick_mode_dsn_passthrough={self.thick_mode_dsn_passthrough!r}, "
            f"extra_auth_params={self.extra_auth_params!r}, "
            f"pool_name={self.pool_name!r}"
            ")"
        )

    def _flatten_value(f):
        """
        Helper function used to flatten arrays of values if they only contain a
        single item.
        """

        @functools.wraps(f)
        def wrapped(self):
            values = f(self)
            return values if len(values) > 1 else values[0]

        return wrapped

    @property
    def appcontext(self) -> list:
        """
        Application context used by the connection. It should be a list of
        3-tuples (namespace, name, value) and each entry in the tuple should be
        a string.
        """
        return self._impl.appcontext

    @property
    @_flatten_value
    def cclass(self) -> Union[list, str]:
        """
        The connection class to use for Database Resident Connection Pooling
        (DRCP).
        """
        return [d.cclass for d in self._impl.description_list.children]

    @property
    def config_dir(self) -> str:
        """
        A directory in which the optional tnsnames.ora configuration file is
        located. This value is only used in python-oracledb Thin mode. For
        python-oracledb Thick mode, it is used if
        :attr:`oracledb.defaults.thick_mode_dsn_passthrough
        <Defaults.thick_mode_dsn_passthrough>` is *False*. Otherwise in Thick
        mode use the ``config_dir`` parameter of
        :meth:`oracledb.init_oracle_client()`.
        """
        return self._impl.config_dir

    @property
    @_flatten_value
    def connection_id_prefix(self) -> Union[list, str]:
        """
        An application specific prefix that is added to the connection
        identifier used for tracing.
        """
        return [
            d.connection_id_prefix
            for d in self._impl.description_list.children
        ]

    @property
    def debug_jdwp(self) -> str:
        """
        A string with the format "host=<host>;port=<port>" that specifies the
        host and port of the PL/SQL debugger. This value is only used in
        python-oracledb Thin mode.  For python-oracledb Thick mode set the
        ORA_DEBUG_JDWP environment variable.
        """
        return self._impl.debug_jdwp

    @property
    def disable_oob(self) -> bool:
        """
        A boolean indicating whether out-of-band breaks should be disabled.
        This value is only used in python-oracledb Thin mode. It has no effect
        on Windows which does not support this functionality.
        """
        return self._impl.disable_oob

    @property
    def driver_name(self) -> str:
        """
        A string recorded by Oracle Database as the name of the driver which
        originated the connection.
        """
        return self._impl.driver_name

    @property
    def edition(self) -> str:
        """
        Edition to use for the connection. This parameter cannot be used
        simultaneously with the cclass parameter.
        """
        return self._impl.edition

    @property
    def events(self) -> bool:
        """
        A boolean specifying whether events mode should be enabled. This value
        is only used in python-oracledb Thick mode and is needed for continuous
        query notification and high availability event notifications.
        """
        return self._impl.events

    @property
    @_flatten_value
    def expire_time(self) -> Union[list, int]:
        """
        The number of minutes between the sending of keepalive probes. If this
        parameter is set to a value greater than zero it enables keepalive.
        """
        return [d.expire_time for d in self._impl.description_list.children]

    @property
    def externalauth(self) -> bool:
        """
        A boolean indicating whether to use external authentication.
        """
        return self._impl.externalauth

    @property
    def extra_auth_params(self) -> dict:
        """
        A dictionary containing configuration parameters necessary for Oracle
        Database authentication using plugins, such as the Azure and OCI cloud-
        native authentication plugins.
        """
        return self._impl.extra_auth_params

    @property
    @_flatten_value
    def host(self) -> Union[list, str]:
        """
        The hostname or IP address of the machine hosting the database or the
        database listener.
        """
        return [a.host for a in self._impl._get_addresses()]

    @property
    @_flatten_value
    def https_proxy(self) -> Union[list, str]:
        """
        The hostname or IP address of a proxy host to use for tunneling secure
        connections.
        """
        return [a.https_proxy for a in self._impl._get_addresses()]

    @property
    @_flatten_value
    def https_proxy_port(self) -> Union[list, int]:
        """
        The port on which to communicate with the proxy host.
        """
        return [a.https_proxy_port for a in self._impl._get_addresses()]

    @property
    @_flatten_value
    def instance_name(self) -> Union[list, str]:
        """
        The instance name of the database.
        """
        return [d.instance_name for d in self._impl.description_list.children]

    @property
    def machine(self) -> str:
        """
        A string recorded by Oracle Database as the name of the machine from
        which the connection originates.
        """
        return self._impl.machine

    @property
    def matchanytag(self) -> bool:
        """
        A boolean specifying whether any tag can be used when acquiring a
        connection from the pool. This value is only used in python-oracledb
        Thick mode.
        """
        return self._impl.matchanytag

    @property
    def mode(self) -> oracledb.AuthMode:
        """
        The authorization mode to use. One of the constants
        :data:`oracledb.AUTH_MODE_DEFAULT`, :data:`oracledb.AUTH_MODE_PRELIM`,
        :data:`oracledb.AUTH_MODE_SYSASM`, :data:`oracledb.AUTH_MODE_SYSBKP`,
        :data:`oracledb.AUTH_MODE_SYSDBA`, :data:`oracledb.AUTH_MODE_SYSDGD`,
        :data:`oracledb.AUTH_MODE_SYSKMT`, :data:`oracledb.AUTH_MODE_SYSOPER`,
        or :data:`oracledb.AUTH_MODE_SYSRAC`.
        """
        return oracledb.AuthMode(self._impl.mode)

    @property
    def osuser(self) -> str:
        """
        A string recorded by Oracle Database as the operating system user who
        originated the connection.
        """
        return self._impl.osuser

    @property
    @_flatten_value
    def pool_boundary(self) -> Union[list, str]:
        """
        One of the values "statement" or "transaction" indicating when pooled
        DRCP connections can be returned to the pool. This requires the use of
        DRCP with Oracle Database 23.4 or higher.
        """
        return [d.pool_boundary for d in self._impl.description_list.children]

    @property
    @_flatten_value
    def pool_name(self) -> Union[list, str]:
        """
        The name of the DRCP pool when using multi-pool DRCP with Oracle
        Database 23.4, or higher.
        """
        return [d.pool_name for d in self._impl.description_list.children]

    @property
    @_flatten_value
    def port(self) -> Union[list, int]:
        """
        The port number on which the database listener is listening.
        """
        return [a.port for a in self._impl._get_addresses()]

    @property
    def program(self) -> str:
        """
        A string recorded by Oracle Database as the program from which the
        connection originates.
        """
        return self._impl.program

    @property
    @_flatten_value
    def protocol(self) -> Union[list, str]:
        """
        One of the strings "tcp" or "tcps" indicating whether to use
        unencrypted network traffic or encrypted network traffic (TLS).
        """
        return [a.protocol for a in self._impl._get_addresses()]

    @property
    def proxy_user(self) -> str:
        """
        The name of the proxy user to connect to. If this value is not
        specified, it will be parsed out of user if user is in the form
        "user[proxy_user]".
        """
        return self._impl.proxy_user

    @property
    @_flatten_value
    def purity(self) -> Union[list, oracledb.Purity]:
        """
        The connection purity to use for Database Resident Connection Pooling
        (DRCP).
        """
        return [
            oracledb.Purity(d.purity)
            for d in self._impl.description_list.children
        ]

    @property
    @_flatten_value
    def retry_count(self) -> Union[list, int]:
        """
        The number of times that initial connection establishment should be
        retried before the connection attempt is terminated.
        """
        return [d.retry_count for d in self._impl.description_list.children]

    @property
    @_flatten_value
    def retry_delay(self) -> Union[list, int]:
        """
        The number of seconds to wait before retrying to establish a
        connection.
        """
        return [d.retry_delay for d in self._impl.description_list.children]

    @property
    @_flatten_value
    def sdu(self) -> Union[list, int]:
        """
        The requested size of the Session Data Unit (SDU), in bytes. The value
        tunes internal buffers used for communication to the database. Bigger
        values can increase throughput for large queries or bulk data loads,
        but at the cost of higher memory use. The SDU size that will actually
        be used is negotiated down to the lower of this value and the database
        network SDU configuration value.
        """
        return [d.sdu for d in self._impl.description_list.children]

    @property
    @_flatten_value
    def server_type(self) -> Union[list, str]:
        """
        The type of server connection that should be established. If specified,
        it should be one of strings "dedicated", "shared" or "pooled".
        """
        return [d.server_type for d in self._impl.description_list.children]

    @property
    @_flatten_value
    def service_name(self) -> Union[list, str]:
        """
        The service name of the database.
        """
        return [d.service_name for d in self._impl.description_list.children]

    @property
    def shardingkey(self) -> list:
        """
        A list of strings, numbers, bytes or dates that identify the database
        shard to connect to. This value is only used in python-oracledb Thick
        mode.
        """
        return self._impl.shardingkey

    @property
    @_flatten_value
    def sid(self) -> Union[list, str]:
        """
        The system identifier (SID) of the database. Note using a service_name
        instead is recommended.
        """
        return [d.sid for d in self._impl.description_list.children]

    @property
    def ssl_context(self) -> Any:
        """
        An SSLContext object used for connecting to the database using TLS.
        This SSL context will be modified to include the private key or any
        certificates found in a separately supplied wallet. This parameter
        should only be specified if the default SSLContext object cannot be
        used.
        """
        return self._impl.ssl_context

    @property
    @_flatten_value
    def ssl_server_cert_dn(self) -> Union[list, str]:
        """
        The distinguished name (DN) which should be matched with the server.
        This value is ignored if the ssl_server_dn_match parameter is not set
        to the value True. If specified this value is used for any verfication.
        Otherwise the hostname will be used.
        """
        return [
            d.ssl_server_cert_dn for d in self._impl.description_list.children
        ]

    @property
    @_flatten_value
    def ssl_server_dn_match(self) -> Union[list, bool]:
        """
        A boolean indicating whether the server certificate distinguished name
        (DN) should be matched in addition to the regular certificate
        verification that is performed. Note that if the ssl_server_cert_dn
        parameter is not privided, host name matching is performed instead.
        """
        return [
            d.ssl_server_dn_match for d in self._impl.description_list.children
        ]

    @property
    @_flatten_value
    def ssl_version(self) -> Union[list, ssl.TLSVersion]:
        """
        One of the values ssl.TLSVersion.TLSv1_2 or ssl.TLSVersion.TLSv1_3
        indicating which TLS version to use.
        """
        return [d.ssl_version for d in self._impl.description_list.children]

    @property
    def stmtcachesize(self) -> int:
        """
        The size of the statement cache.
        """
        return self._impl.stmtcachesize

    @property
    def supershardingkey(self) -> list:
        """
        A list of strings, numbers, bytes or dates that identify the database
        shard to connect to. This value is only used in python-oracledb Thick
        mode.
        """
        return self._impl.supershardingkey

    @property
    def tag(self) -> str:
        """
        Identifies the type of connection that should be returned from a pool.
        This value is only used in python-oracledb Thick mode.
        """
        return self._impl.tag

    @property
    @_flatten_value
    def tcp_connect_timeout(self) -> Union[list, float]:
        """
        A float indicating the maximum number of seconds to wait when
        establishing a connection to the database host.
        """
        return [
            d.tcp_connect_timeout for d in self._impl.description_list.children
        ]

    @property
    def terminal(self) -> str:
        """
        A string recorded by Oracle Database as the terminal identifier from
        which the connection originates.
        """
        return self._impl.terminal

    @property
    def thick_mode_dsn_passthrough(self) -> bool:
        """
        A boolean indicating whether to pass the connect string to the Oracle
        Client libraries unchanged without parsing by the driver. Setting this
        to False makes python-oracledb Thick and Thin mode applications behave
        similarly regarding connection string parameter handling and locating
        any optional tnsnames.ora configuration file.
        """
        return self._impl.thick_mode_dsn_passthrough

    @property
    def user(self) -> str:
        """
        The name of the database user to connect to.
        """
        return self._impl.user

    @property
    @_flatten_value
    def use_sni(self) -> Union[list, bool]:
        """
        A boolean indicating whether to use the TLS SNI extension to bypass the
        second TLS neogiation that would otherwise be required.
        """
        return [d.use_sni for d in self._impl.description_list.children]

    @property
    @_flatten_value
    def use_tcp_fast_open(self) -> Union[list, bool]:
        """
        A boolean indicating whether to use TCP fast open. This is an Oracle
        Autonomous Database Serverless (ADB-S) specific property for clients
        connecting from within OCI Cloud network. Please refer to the ADB-S
        documentation for more information.
        """
        return [
            d.use_tcp_fast_open for d in self._impl.description_list.children
        ]

    @property
    @_flatten_value
    def wallet_location(self) -> Union[list, str]:
        """
        The directory where the wallet can be found. In python-oracledb Thin
        mode this must be the directory containing the PEM-encoded wallet file
        ewallet.pem. In python-oracledb Thick mode this must be the directory
        containing the file cwallet.sso.
        """
        return [
            d.wallet_location for d in self._impl.description_list.children
        ]

    def copy(self) -> "ConnectParams":
        """
        Creates a copy of the ConnectParams instance and returns it.
        """
        params = ConnectParams.__new__(ConnectParams)
        params._impl = self._impl.copy()
        return params

    def get_connect_string(self) -> str:
        """
        Returns the connection string associated with the instance.
        """
        return self._impl.get_connect_string()

    def get_network_service_names(self) -> list:
        """
        Returns a list of the network service names found in the
        :ref:`tnsnames.ora <optnetfiles>` file which is inside the directory
        that can be identified by the attribute
        :attr:`~ConnectParams.config_dir`.  If a tnsnames.ora file does not
        exist, then an exception is raised.
        """
        return self._impl.get_network_service_names()

    def parse_connect_string(self, connect_string: str) -> None:
        """
        Parses the connect string into its components and stores the
        parameters.

        The ``connect string`` parameter can be an Easy Connect string,
        name-value pairs, or a simple alias which is looked up in
        ``tnsnames.ora``. Parameters that are found in the connect string
        override any currently stored values.
        """
        self._impl.parse_connect_string(connect_string)

    def parse_dsn_with_credentials(self, dsn: str) -> tuple:
        """
        Parses a DSN in the form <user>/<password>@<connect_string> or in the
        form <user>/<password> and returns a 3-tuple containing the parsed
        user, password and connect string. Empty strings are returned as the
        value *None*.
        """
        return self._impl.parse_dsn_with_credentials(dsn)

    @utils.params_setter
    def set(
        self,
        *,
        user: Optional[str] = None,
        proxy_user: Optional[str] = None,
        password: Optional[str] = None,
        newpassword: Optional[str] = None,
        wallet_password: Optional[str] = None,
        access_token: Optional[Union[str, tuple, Callable]] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        protocol: Optional[str] = None,
        https_proxy: Optional[str] = None,
        https_proxy_port: Optional[int] = None,
        service_name: Optional[str] = None,
        instance_name: Optional[str] = None,
        sid: Optional[str] = None,
        server_type: Optional[str] = None,
        cclass: Optional[str] = None,
        purity: Optional[oracledb.Purity] = None,
        expire_time: Optional[int] = None,
        retry_count: Optional[int] = None,
        retry_delay: Optional[int] = None,
        tcp_connect_timeout: Optional[float] = None,
        ssl_server_dn_match: Optional[bool] = None,
        ssl_server_cert_dn: Optional[str] = None,
        wallet_location: Optional[str] = None,
        events: Optional[bool] = None,
        externalauth: Optional[bool] = None,
        mode: Optional[oracledb.AuthMode] = None,
        disable_oob: Optional[bool] = None,
        stmtcachesize: Optional[int] = None,
        edition: Optional[str] = None,
        tag: Optional[str] = None,
        matchanytag: Optional[bool] = None,
        config_dir: Optional[str] = None,
        appcontext: Optional[list] = None,
        shardingkey: Optional[list] = None,
        supershardingkey: Optional[list] = None,
        debug_jdwp: Optional[str] = None,
        connection_id_prefix: Optional[str] = None,
        ssl_context: Optional[Any] = None,
        sdu: Optional[int] = None,
        pool_boundary: Optional[str] = None,
        use_tcp_fast_open: Optional[bool] = None,
        ssl_version: Optional[ssl.TLSVersion] = None,
        program: Optional[str] = None,
        machine: Optional[str] = None,
        terminal: Optional[str] = None,
        osuser: Optional[str] = None,
        driver_name: Optional[str] = None,
        use_sni: Optional[bool] = None,
        thick_mode_dsn_passthrough: Optional[bool] = None,
        extra_auth_params: Optional[dict] = None,
        pool_name: Optional[str] = None,
        handle: Optional[int] = None,
    ):
        """
        Sets the values for one or more of the parameters of a ConnectParams
        object.  All parameters are optional. A brief description of each
        parameter follows:

        - ``user``: the name of the database user to connect to

        - ``proxy_user``: the name of the proxy user to connect to. If this
          value is not specified, it will be parsed out of user if user is in
          the form "user[proxy_user]"

        - ``password``: the password for the database user

        - ``newpassword``: a new password for the database user. The new
          password will take effect immediately upon a successful connection to
          the database

        - ``wallet_password``: the password to use to decrypt the wallet, if it
          is encrypted. This is not the database password. For Oracle
          Autonomous Database this is the password created when downloading the
          wallet. This value is only used in python-oracledb Thin mode.

        - ``access_token``: a string, or a 2-tuple, or a callable. If it is a
          string, it specifies an Entra ID OAuth2 token used for Open
          Authorization (OAuth 2.0) token based authentication. If it is a
          2-tuple, it specifies the token and private key strings used for
          Oracle Cloud Infrastructure (OCI) Identity and Access Management
          (IAM) token based authentication. If it is a callable, it returns
          either a string or a 2-tuple used for OAuth 2.0 or OCI IAM token
          based authentication and is useful when the pool needs to expand and
          create new connections but the current authentication token has
          expired

        - ``host``: the hostname or IP address of the machine hosting the
          database or the database listener

        - ``port``: the port number on which the database listener is listening

        - ``protocol``: one of the strings "tcp" or "tcps" indicating whether
          to use unencrypted network traffic or encrypted network traffic (TLS)

        - ``https_proxy``: the hostname or IP address of a proxy host to use
          for tunneling secure connections

        - ``https_proxy_port``: the port on which to communicate with the proxy
          host

        - ``service_name``: the service name of the database

        - ``instance_name``: the instance name of the database

        - ``sid``: the system identifier (SID) of the database. Note using a
          service_name instead is recommended

        - ``server_type``: the type of server connection that should be
          established. If specified, it should be one of strings "dedicated",
          "shared" or "pooled"

        - ``cclass``: the connection class to use for Database Resident
          Connection Pooling (DRCP)

        - ``purity``: the connection purity to use for Database Resident
          Connection Pooling (DRCP)

        - ``expire_time``: the number of minutes between the sending of
          keepalive probes. If this parameter is set to a value greater than
          zero it enables keepalive

        - ``retry_count``: the number of times that initial connection
          establishment should be retried before the connection attempt is
          terminated

        - ``retry_delay``: the number of seconds to wait before retrying to
          establish a connection

        - ``tcp_connect_timeout``: a float indicating the maximum number of
          seconds to wait when establishing a connection to the database host

        - ``ssl_server_dn_match``: a boolean indicating whether the server
          certificate distinguished name (DN) should be matched in addition to
          the regular certificate verification that is performed. Note that if
          the ssl_server_cert_dn parameter is not privided, host name matching
          is performed instead

        - ``ssl_server_cert_dn``: the distinguished name (DN) which should be
          matched with the server. This value is ignored if the
          ssl_server_dn_match parameter is not set to the value True. If
          specified this value is used for any verfication. Otherwise the
          hostname will be used

        - ``wallet_location``: the directory where the wallet can be found. In
          python-oracledb Thin mode this must be the directory containing the
          PEM-encoded wallet file ewallet.pem. In python-oracledb Thick mode
          this must be the directory containing the file cwallet.sso

        - ``events``: a boolean specifying whether events mode should be
          enabled. This value is only used in python-oracledb Thick mode and is
          needed for continuous query notification and high availability event
          notifications

        - ``externalauth``: a boolean indicating whether to use external
          authentication

        - ``mode``: the authorization mode to use. One of the constants
          :data:`oracledb.AUTH_MODE_DEFAULT`,
          :data:`oracledb.AUTH_MODE_PRELIM`, :data:`oracledb.AUTH_MODE_SYSASM`,
          :data:`oracledb.AUTH_MODE_SYSBKP`, :data:`oracledb.AUTH_MODE_SYSDBA`,
          :data:`oracledb.AUTH_MODE_SYSDGD`, :data:`oracledb.AUTH_MODE_SYSKMT`,
          :data:`oracledb.AUTH_MODE_SYSOPER`, or
          :data:`oracledb.AUTH_MODE_SYSRAC`

        - ``disable_oob``: a boolean indicating whether out-of-band breaks
          should be disabled. This value is only used in python-oracledb Thin
          mode. It has no effect on Windows which does not support this
          functionality

        - ``stmtcachesize``: the size of the statement cache

        - ``edition``: edition to use for the connection. This parameter cannot
          be used simultaneously with the cclass parameter

        - ``tag``: identifies the type of connection that should be returned
          from a pool. This value is only used in python-oracledb Thick mode

        - ``matchanytag``: a boolean specifying whether any tag can be used
          when acquiring a connection from the pool. This value is only used in
          python-oracledb Thick mode

        - ``config_dir``: a directory in which the optional tnsnames.ora
          configuration file is located. This value is only used in python-
          oracledb Thin mode. For python-oracledb Thick mode, it is used if
          :attr:`oracledb.defaults.thick_mode_dsn_passthrough
          <Defaults.thick_mode_dsn_passthrough>` is *False*. Otherwise in Thick
          mode use the ``config_dir`` parameter of
          :meth:`oracledb.init_oracle_client()`

        - ``appcontext``: application context used by the connection. It should
          be a list of 3-tuples (namespace, name, value) and each entry in the
          tuple should be a string

        - ``shardingkey``: a list of strings, numbers, bytes or dates that
          identify the database shard to connect to. This value is only used in
          python-oracledb Thick mode

        - ``supershardingkey``: a list of strings, numbers, bytes or dates that
          identify the database shard to connect to. This value is only used in
          python-oracledb Thick mode

        - ``debug_jdwp``: a string with the format "host=<host>;port=<port>"
          that specifies the host and port of the PL/SQL debugger. This value
          is only used in python-oracledb Thin mode.  For python-oracledb Thick
          mode set the ORA_DEBUG_JDWP environment variable

        - ``connection_id_prefix``: an application specific prefix that is
          added to the connection identifier used for tracing

        - ``ssl_context``: an SSLContext object used for connecting to the
          database using TLS.  This SSL context will be modified to include the
          private key or any certificates found in a separately supplied
          wallet. This parameter should only be specified if the default
          SSLContext object cannot be used

        - ``sdu``: the requested size of the Session Data Unit (SDU), in bytes.
          The value tunes internal buffers used for communication to the
          database. Bigger values can increase throughput for large queries or
          bulk data loads, but at the cost of higher memory use. The SDU size
          that will actually be used is negotiated down to the lower of this
          value and the database network SDU configuration value

        - ``pool_boundary``: one of the values "statement" or "transaction"
          indicating when pooled DRCP connections can be returned to the pool.
          This requires the use of DRCP with Oracle Database 23.4 or higher

        - ``use_tcp_fast_open``: a boolean indicating whether to use TCP fast
          open. This is an Oracle Autonomous Database Serverless (ADB-S)
          specific property for clients connecting from within OCI Cloud
          network. Please refer to the ADB-S documentation for more information

        - ``ssl_version``: one of the values ssl.TLSVersion.TLSv1_2 or
          ssl.TLSVersion.TLSv1_3 indicating which TLS version to use

        - ``program``: a string recorded by Oracle Database as the program from
          which the connection originates

        - ``machine``: a string recorded by Oracle Database as the name of the
          machine from which the connection originates

        - ``terminal``: a string recorded by Oracle Database as the terminal
          identifier from which the connection originates

        - ``osuser``: a string recorded by Oracle Database as the operating
          system user who originated the connection

        - ``driver_name``: a string recorded by Oracle Database as the name of
          the driver which originated the connection

        - ``use_sni``: a boolean indicating whether to use the TLS SNI
          extension to bypass the second TLS neogiation that would otherwise be
          required

        - ``thick_mode_dsn_passthrough``: a boolean indicating whether to pass
          the connect string to the Oracle Client libraries unchanged without
          parsing by the driver. Setting this to False makes python-oracledb
          Thick and Thin mode applications behave similarly regarding
          connection string parameter handling and locating any optional
          tnsnames.ora configuration file

        - ``extra_auth_params``: a dictionary containing configuration
          parameters necessary for Oracle Database authentication using
          plugins, such as the Azure and OCI cloud-native authentication
          plugins

        - ``pool_name``: the name of the DRCP pool when using multi-pool DRCP
          with Oracle Database 23.4, or higher

        - ``handle``: an integer representing a pointer to a valid service
          context handle. This value is only used in python-oracledb Thick
          mode. It should be used with extreme caution
        """
        pass

    def set_from_config(self, config: dict) -> None:
        """
        Sets the property values based on the specified configuration. This
        method is intended for use with Centralized Configuration Providers.

        The ``config`` parameter is a dictionary which consists of the
        following optional keys: "connect_descriptor", "user", "password", and
        "pyo".

        If the key "connect_descriptor" is specified, it is expected to be a
        string, which will be parsed and the properties found within it are
        stored in the ConnectParams instance.

        If the keys "user" or "password" are specified, and the parameters do
        not already have a user or password set, these values will be stored;
        otherwise, they will be ignored. The key "user" is expected to be a
        string. The "key" password may be a string or it may be a dictionary
        which will be examined by a :ref:`registered password type handler
        <registerpasswordtype>` to determine the actual password.

        If the key "pyo" is specified, it is expected to be a dictionary
        containing keys corresponding to property names. Any property names
        accepted by the ConnectParams class will be stored in the ConnectParams
        instance; all other values will be ignored.
        """
        self._impl.set_from_config(config)
