#------------------------------------------------------------------------------
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
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
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# parsers.pyx
#
# Cython file defining the classes used for parsing connect strings and
# statements (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

# a set of alternative parameter names that are used in connect descriptors
# the key is the parameter name used in connect descriptors and the value is
# the key used in argument dictionaries (and stored in the parameter objects)
ALTERNATIVE_PARAM_NAMES = {
    "pool_connection_class": "cclass",
    "pool_purity": "purity",
    "server": "server_type",
    "transport_connect_timeout": "tcp_connect_timeout",
    "my_wallet_directory": "wallet_location"
}

# a set of parameter names used as containers for storing additional parameters
CONTAINER_PARAM_NAMES = set([
    "address",
    "address_list",
    "connect_data",
    "description",
    "description_list",
    "security",
])

# DESCRIPTION parameter names that are supported by the driver; all other
# key/value pairs are passed unchanged to the database
DESCRIPTION_PARAM_NAMES = set([
    "address",
    "address_list",
    "connect_data",
    "expire_time",
    "failover",
    "load_balance",
    "source_route",
    "retry_count",
    "retry_delay",
    "sdu",
    "tcp_connect_timeout",
    "use_sni",
    "security",
])

# extra DESCRIPTION parameter names that are passed through when detected in an
# easy connect string
EXTRA_DESCRIPTION_PARAM_NAMES = set([
    "enable",
    "recv_buf_size",
    "send_buf_size"
])

# CONNECT_DATA parameter names that are supported by the driver; all other
# key/value pairs are passed unchanged to the database
CONNECT_DATA_PARAM_NAMES = set([
    "cclass",
    "connection_id_prefix",
    "instance_name",
    "pool_boundary",
    "purity",
    "server_type",
    "service_name",
    "sid",
    "use_tcp_fast_open",
])

# SECURITY parameter names that are supported by the driver; all other
# key/value pairs are passed unchanged to the database
SECURITY_PARAM_NAMES = set([
    "ssl_server_cert_dn",
    "ssl_server_dn_match",
    "ssl_version",
    "wallet_location",
])

# a set of parameter names supported by the driver in EasyConnect strings that
# are common to all drivers
COMMON_PARAM_NAMES = set([
    "expire_time",
    "failover",
    "https_proxy",
    "https_proxy_port",
    "load_balance",
    "pool_boundary",
    "pool_connection_class",
    "pool_purity",
    "retry_count",
    "retry_delay",
    "sdu",
    "source_route",
    "ssl_server_cert_dn",
    "ssl_server_dn_match",
    "transport_connect_timeout",
    "use_sni",
    "wallet_location",
])

# extended parameter prefix
EXTENDED_PARAM_PREFIX = "pyo."

# a set of parameter names that can be specified in EasyConnect strings using
# the extended parameter prefix; these are specific to python-oracledb
EXTENDED_PARAM_NAMES = set([

    # ConnectParams
    "connection_id_prefix",
    "disable_oob",
    "driver_name",
    "edition",
    "events",
    "externalauth",
    "machine",
    "mode",
    "osuser",
    "program",
    "stmtcachesize",
    "terminal",
    "use_tcp_fast_open",

    # PoolParams
    "getmode",
    "homogeneous",
    "increment",
    "max",
    "max_lifetime_session",
    "max_sessions_per_shard",
    "min",
    "ping_interval",
    "ping_timeout",
    "soda_metadata_cache",
    "timeout",
    "wait_timeout",

])

# this cache stores the configurations acquired from one of the configuration
# stores
cdef dict cached_configs = {}

# add all of the common parameters to the extended parameters using the
# python-oracledb specific name
for name in COMMON_PARAM_NAMES:
    EXTENDED_PARAM_NAMES.add(ALTERNATIVE_PARAM_NAMES.get(name, name))


cdef class BaseParser:

    cdef Py_UCS4 get_current_char(self):
        """
        Returns the current character in the data being parsed. This method
        assumes that the end of the stream has not been encountered.
        """
        return cpython.PyUnicode_READ(self.data_kind, self.data, self.temp_pos)

    cdef int initialize(self, str data_to_parse) except -1:
        """
        Initializes the parser with the data to parse.
        """
        self.pos = 0
        self.temp_pos = 0
        self.data_as_str = data_to_parse
        self.num_chars = cpython.PyUnicode_GET_LENGTH(data_to_parse)
        self.data = cpython.PyUnicode_DATA(data_to_parse)
        self.data_kind = cpython.PyUnicode_KIND(data_to_parse)

    cdef int parse_keyword(self) except -1:
        """
        Parse a keyword from the data to parse.
        """
        cdef Py_UCS4 ch
        while self.temp_pos < self.num_chars:
            ch = self.get_current_char()
            if not cpython.Py_UNICODE_ISALPHA(ch) \
                    and not cpython.Py_UNICODE_ISDIGIT(ch) \
                    and ch != '_' and ch != '.':
                break
            self.temp_pos += 1

    cdef int parse_quoted_string(self, Py_UCS4 quote_type) except -1:
        """
        Parses a quoted string with the given quote type. All characters until
        the quote type is detected are discarded.
        """
        cdef Py_UCS4 ch
        while self.temp_pos < self.num_chars:
            ch = self.get_current_char()
            self.temp_pos += 1
            if ch == quote_type:
                self.pos = self.temp_pos
                return 0
        if quote_type == "'":
            errors._raise_err(errors.ERR_MISSING_ENDING_SINGLE_QUOTE)
        else:
            errors._raise_err(errors.ERR_MISSING_ENDING_DOUBLE_QUOTE)

    cdef int skip_spaces(self) except -1:
        """
        Skip any spaces that are present in the string.
        """
        cdef Py_UCS4 ch
        while self.temp_pos < self.num_chars:
            ch = self.get_current_char()
            if not cpython.Py_UNICODE_ISSPACE(ch):
                break
            self.temp_pos += 1


cdef int update_config_cache(str config_cache_key, dict config) except -1:
    """
    Updates the cache with the specified configuration.
    """
    cdef:
        double current_time, soft_expiry_time, hard_expiry_time
        uint32_t time_to_live, time_to_live_grace_period
        object setting

    # the config can include config_time_to_live; the default value is 86400
    # (24 hours); an explicit value of 0 disables caching
    setting = config.get("config_time_to_live")
    if setting is None:
        time_to_live = 86400
    else:
        time_to_live = int(setting)
    if time_to_live == 0:
        return 0

    # the config settings can also include config_time_to_live_grace_period;
    # the default value is 1800 (30 minutes)
    setting = config.get("config_time_to_live_grace_period")
    if setting is None:
        time_to_live_grace_period = 1800
    else:
        time_to_live_grace_period = int(setting)

    # calculate soft and hard expiry times and keep them with the config
    current_time = time.monotonic()
    soft_expiry_time = current_time + time_to_live
    hard_expiry_time = soft_expiry_time + time_to_live_grace_period
    config = copy.deepcopy(config)
    config["config_cache_soft_expiry_time"] = soft_expiry_time
    config["config_cache_hard_expiry_time"] = hard_expiry_time
    cached_configs[config_cache_key] = config


cdef class ConnectStringParser(BaseParser):

    cdef:
        DescriptionList description_list
        Description template_description
        ConnectParamsImpl params_impl
        Address template_address
        Description description
        dict parameters

    cdef int _call_protocol_hook(self, str protocol, str arg,
                                 object fn) except -1:
        """
        Check if the config cache has an entry; if an extry exists and it has
        not expired, use it; otherwise, call the protocol hook function.
        """
        cdef:
            double current_time = 0, expiry_time = 0
            dict config

        # check to see if the cache has a value and that it has not reached the
        # soft expiry time
        config = cached_configs.get(self.data_as_str)
        if config is not None:
            current_time = time.monotonic()
            expiry_time = config["config_cache_soft_expiry_time"]
            if current_time <= expiry_time:
                self.params_impl.set_from_config(config, update_cache=False)
                return 0

        # call the protocol hook function; the cache key is set on the
        # parameters instance so that calls by the hook function to
        # set_from_config() will update the cache
        params = self.params_impl._get_public_instance()
        self.params_impl._config_cache_key = self.data_as_str
        try:
            fn(protocol, arg, params)
        except Exception as e:

            # if the hook fails but a config exists in the cache and the hard
            # expiry time has not been reached the existing config is used
            if config is not None:
                expiry_time = config["config_cache_hard_expiry_time"]
                if current_time <= expiry_time:
                    self.params_impl.set_from_config(config, update_cache=False)
                    return 0
                del cached_configs[self.params_impl._config_cache_key]
            errors._raise_err(errors.ERR_PROTOCOL_HANDLER_FAILED,
                              protocol=protocol, arg=arg, cause=e)
        finally:
            self.params_impl._config_cache_key = None

    cdef bint _is_host_or_service_name_char(self, Py_UCS4 ch):
        """
        Returns whether or not the given character is allowed to be used inside
        a host name or service name.
        """
        return cpython.Py_UNICODE_ISALPHA(ch) \
                or cpython.Py_UNICODE_ISDIGIT(ch) \
                or ch in ('-', '_', '.')

    cdef int _parse_descriptor(self) except -1:
        """
        Parses a connect descriptor.
        """
        cdef:
            AddressList address_list
            Description description
            Address address
            dict args = {}
        self._parse_descriptor_key_value_pair(args)
        self.description_list = DescriptionList()
        list_args = args.get("description_list")
        if list_args is not None:
            self.description_list.set_from_args(list_args)
        else:
            list_args = args
        descriptions = list_args.get("description", list_args)
        if not isinstance(descriptions, list):
            descriptions = [descriptions]
        for desc_args in descriptions:
            description = self.template_description.copy()
            description.set_from_description_args(desc_args)
            self.description_list.children.append(description)
            sub_args = desc_args.get("connect_data")
            if sub_args is not None:
                description.set_from_connect_data_args(sub_args)
            sub_args = desc_args.get("security")
            if sub_args is not None:
                description.set_from_security_args(sub_args)
            address_lists = desc_args.get("address_list", desc_args)
            if not isinstance(address_lists, list):
                address_lists = [address_lists]
            for list_args in address_lists:
                address_list = AddressList()
                address_list.set_from_args(list_args)
                description.children.append(address_list)
                addresses = list_args.get("address", [])
                if not isinstance(addresses, list):
                    addresses = [addresses]
                for addr_args in addresses:
                    address = self.template_address.copy()
                    address.set_from_args(addr_args)
                    address_list.children.append(address)
        if not self.description_list.get_addresses():
            errors._raise_err(errors.ERR_MISSING_ADDRESS,
                              connect_string=self.data_as_str)

    cdef int _parse_descriptor_key_value_pair(self, dict args) except -1:
        """
        Parses a key-value pair from the connect string. At this point it is
        assumed that the character previously read was an opening parenthesis.
        """
        cdef:
            bint is_simple_value = False
            object value = None
            ssize_t start_pos
            Py_UCS4 ch = 0
            str name

        # parse keyword
        self.skip_spaces()
        start_pos = self.temp_pos
        self.parse_keyword()
        if self.temp_pos == start_pos:
            errors._raise_err(errors.ERR_INVALID_CONNECT_DESCRIPTOR,
                              data=self.data_as_str)
        name = self.data_as_str[start_pos:self.temp_pos].lower()
        name = ALTERNATIVE_PARAM_NAMES.get(name, name)

        # look for equals sign
        self.skip_spaces()
        if self.temp_pos < self.num_chars:
            ch = self.get_current_char()
        if ch != '=':
            errors._raise_err(errors.ERR_INVALID_CONNECT_DESCRIPTOR,
                              data=self.data_as_str)
        self.temp_pos += 1
        self.skip_spaces()

        # parse value
        while self.temp_pos < self.num_chars:
            ch = self.get_current_char()
            if ch == '"':
                if is_simple_value:
                    errors._raise_err(errors.ERR_INVALID_CONNECT_DESCRIPTOR,
                                      data=self.data_as_str)
                self.temp_pos += 1
                start_pos = self.temp_pos
                self.parse_quoted_string(ch)
                if self.temp_pos > start_pos + 1:
                    value = self.data_as_str[start_pos:self.temp_pos - 1]
                break
            elif ch == '(':
                if is_simple_value:
                    errors._raise_err(errors.ERR_INVALID_CONNECT_DESCRIPTOR,
                                      data=self.data_as_str)
                self.temp_pos += 1
                if value is None:
                    value = {}
                self._parse_descriptor_key_value_pair(value)
                continue
            elif ch == ')':
                break
            elif not is_simple_value and not cpython.Py_UNICODE_ISSPACE(ch):
                if value is not None or name in CONTAINER_PARAM_NAMES:
                    errors._raise_err(errors.ERR_INVALID_CONNECT_DESCRIPTOR,
                                      data=self.data_as_str)
                start_pos = self.temp_pos
                is_simple_value = True
            self.temp_pos += 1
        if is_simple_value:
            value = self.data_as_str[start_pos:self.temp_pos].strip()
        self.skip_spaces()
        if self.temp_pos < self.num_chars:
            ch = self.get_current_char()
            if ch != ')':
                errors._raise_err(errors.ERR_INVALID_CONNECT_DESCRIPTOR,
                                  data=self.data_as_str)
            self.temp_pos += 1
        self.skip_spaces()
        self.pos = self.temp_pos

        # store value in dictionary
        if value is not None:
            self._set_descriptor_arg(args, name, value)

    cdef int _parse_easy_connect(self) except -1:
        """
        Parses an easy connect string.
        """
        cdef:
            object fn
            str protocol, arg
        protocol = self._parse_easy_connect_protocol()
        if protocol is not None:
            fn = REGISTERED_PROTOCOLS.get(protocol)
            if fn is not None:
                arg = self.data_as_str[self.temp_pos:]
                self._call_protocol_hook(protocol, arg, fn)
                self.description_list = self.params_impl.description_list
                self.pos = self.num_chars
                return 0
            elif protocol != self.template_address.protocol:
                self.template_address = self.template_address.copy()
                self.template_address.set_protocol(protocol)
        self._parse_easy_connect_hosts()
        self._parse_easy_connect_service_name()
        self._parse_easy_connect_instance_name()
        if self.description_list is not None:
            self._parse_easy_connect_parameters()

    cdef int _parse_easy_connect_host(self, Address address) except -1:
        """
        Parses a host name from the easy connect string.
        """
        cdef:
            bint found_bracket = False, found_host = False
            ssize_t start_pos = self.temp_pos
            Py_UCS4 ch
        while self.temp_pos < self.num_chars:
            ch = self.get_current_char()
            if not found_bracket and not found_host and ch == '[':
                found_bracket = True
                start_pos = self.temp_pos + 1
            elif found_bracket and ch == ']':
                address.host = self.data_as_str[start_pos:self.temp_pos]
                self.temp_pos = self.temp_pos + 1
                self.pos = self.temp_pos
                break
            elif found_bracket or self._is_host_or_service_name_char(ch):
                self.temp_pos += 1
                found_host = True
            else:
                if found_host:
                    address.host = self.data_as_str[start_pos:self.temp_pos]
                    self.pos = self.temp_pos
                break

    cdef int _parse_easy_connect_hosts(self) except -1:
        """
        Parses the list of hosts from an easy connect string. This should be a
        series of host names separated by commas or semicolons.
        """
        cdef:
            Address temp_address, address = None
            ssize_t i, port_index = 0
            AddressList address_list
            Py_UCS4 ch
        self.description = self.template_description.copy()
        address_list = AddressList()
        self.description.children.append(address_list)
        self.temp_pos = self.pos
        while True:
            address = self.template_address.copy()
            self._parse_easy_connect_host(address)
            if self.temp_pos != self.pos or self.pos >= self.num_chars:
                break
            self.pos = self.temp_pos
            address_list.children.append(address)
            ch = self.get_current_char()
            if ch == ':':
                self.temp_pos += 1
                self._parse_easy_connect_port(address)
                self.pos = self.temp_pos
                if self.pos >= self.num_chars:
                    break
                for i in range(port_index, len(address_list.children) - 1):
                    temp_address = address_list.children[i]
                    temp_address.port = address.port
                port_index = len(address_list.children)
                ch = self.get_current_char()
            if ch == ';':
                address_list = AddressList()
                self.description.children.append(address_list)
                port_index = 0
            elif ch != ',':
                break
            self.temp_pos += 1

    cdef int _parse_easy_connect_parameter(self) except -1:
        """
        Parses a single parameter from the easy connect string. This is
        expected to be a keyword followed by a value seprated by an equals
        sign.
        """
        cdef:
            ssize_t start_pos, end_pos = 0
            str name, value
            Py_UCS4 ch = 0
            bint keep

        # get parameter name
        self.skip_spaces()
        start_pos = self.temp_pos
        self.parse_keyword()
        if self.temp_pos == start_pos or self.temp_pos >= self.num_chars:
            return 0
        name = self.data_as_str[start_pos:self.temp_pos].lower()
        if name.startswith(EXTENDED_PARAM_PREFIX):
            name = name[len(EXTENDED_PARAM_PREFIX):]
            keep = name in EXTENDED_PARAM_NAMES
        else:
            keep = name in COMMON_PARAM_NAMES \
                    or name in EXTRA_DESCRIPTION_PARAM_NAMES
            name = ALTERNATIVE_PARAM_NAMES.get(name, name)

        # look for the equals sign
        self.skip_spaces()
        if self.temp_pos >= self.num_chars:
            return 0
        ch = self.get_current_char()
        if ch != '=':
            return 0
        self.temp_pos += 1

        # get the parameter value
        found_value = False
        self.skip_spaces()
        start_pos = self.temp_pos
        while self.temp_pos < self.num_chars:
            ch = self.get_current_char()
            if ch == '"':
                # if the quote is not the first character in the value, this is
                # not a valid easy connect parameter
                if self.temp_pos > start_pos:
                    return 0
                self.temp_pos += 1
                start_pos = self.temp_pos
                self.parse_quoted_string(ch)
                end_pos = self.temp_pos - 1
                break
            elif ch == '&':
                end_pos = self.temp_pos
                break
            self.temp_pos += 1
            end_pos = self.temp_pos
        if end_pos > start_pos and keep:
            if self.parameters is None:
                self.parameters = {}
            value = self.data_as_str[start_pos:end_pos]
            if name in EXTRA_DESCRIPTION_PARAM_NAMES:
                self.parameters.setdefault("extra_args", {})[name] = value
            else:
                self.parameters[name] = value
        self.skip_spaces()
        self.pos = self.temp_pos

    cdef int _parse_easy_connect_parameters(self) except -1:
        """
        Parses the parameters from the easy connect string. This is expected to
        be a question mark followed by a series of key-value pairs separated by
        ampersands.
        """
        cdef:
            Py_UCS4 ch, expected_sep
            Address address
        expected_sep = '?'
        self.temp_pos = self.pos
        while self.temp_pos < self.num_chars:
            ch = self.get_current_char()
            if ch != expected_sep:
                break
            expected_sep = '&'
            self.temp_pos += 1
            self._parse_easy_connect_parameter()

    cdef int _parse_easy_connect_port(self, Address address) except -1:
        """
        Parses a port number from the easy connect string. This consists of one
        or more digits.
        """
        cdef:
            ssize_t pos = self.temp_pos
            bint found_port = False
            Py_UCS4 ch
        while self.temp_pos < self.num_chars:
            ch = self.get_current_char()
            if not cpython.Py_UNICODE_ISDIGIT(ch):
                break
            found_port = True
            self.temp_pos += 1
        if found_port:
            address.port = int(self.data_as_str[pos:self.temp_pos])

    cdef str _parse_easy_connect_protocol(self):
        """
        Parses the protocol from an easy connect string. This should be a
        series of alphabetic characters or dashes, followed by a colon and two
        slashes. If such a string is found, it is saved on the template address
        associated with the parser; otherwise, the default protocol of "tcp" is
        saved on the template address associated with the parser. If no
        protocol is found, the separator (two slashes) may still be found and
        will be disarded.
        """
        cdef:
            ssize_t start_sep_pos = self.pos
            int num_sep_chars = 0
            str protocol = None
            Py_UCS4 ch
        self.temp_pos = self.pos
        while self.temp_pos < self.num_chars:
            ch = self.get_current_char()
            if ch == ':':
                protocol = self.data_as_str[self.pos:self.temp_pos].lower()
                start_sep_pos = self.temp_pos + 1
            elif ch == '/' and self.temp_pos - start_sep_pos == num_sep_chars:
                num_sep_chars += 1
                if num_sep_chars == 2:
                    self.temp_pos += 1
                    self.pos = self.temp_pos
                    break
            elif not cpython.Py_UNICODE_ISALPHA(ch) and ch not in ('-', '_'):
                break
            self.temp_pos += 1
        if protocol is not None and num_sep_chars == 2:
            return protocol

    cdef str _parse_easy_connect_service_name(self):
        """
        Parses the service name from an easy connect string. This is expected
        to be a slash followed by a series of alphanumeric characters. If such
        a string is found, it is returned.
        """
        cdef:
            bint found_service_name = False, found_server_type = False
            bint found_slash = False, found_colon = False
            ssize_t service_name_end_pos = 0
            Py_UCS4 ch
            str value
        self.temp_pos = self.pos
        while self.temp_pos < self.num_chars:
            ch = self.get_current_char()
            if not found_slash and ch == '/':
                found_slash = True
            elif found_service_name and not found_colon and ch == ':':
                found_colon = True
            elif found_slash and not found_colon \
                    and self._is_host_or_service_name_char(ch):
                found_service_name = True
                service_name_end_pos = self.temp_pos + 1
            elif found_colon and cpython.Py_UNICODE_ISALPHA(ch):
                found_server_type = True
            else:
                break
            self.temp_pos += 1
        if found_service_name:
            self.description.service_name = \
                    self.data_as_str[self.pos + 1:service_name_end_pos]
        if found_slash:
            self.pos = self.temp_pos
            self.description_list = DescriptionList()
            self.description_list.children.append(self.description)
        if found_server_type:
            value = self.data_as_str[service_name_end_pos + 1:self.temp_pos]
            self.description.set_server_type(value)

    cdef str _parse_easy_connect_instance_name(self):
        """
        Parses the instance name from an easy connect string. This is expected
        to be a slash followed by a series of alphanumeric characters. If such
        a string is found, it is returned.
        """
        cdef:
            ssize_t instance_name_end_pos = 0
            bint found_instance_name = False
            bint found_slash = False
            Py_UCS4 ch
            str value
        self.temp_pos = self.pos
        while self.temp_pos < self.num_chars:
            ch = self.get_current_char()
            if not found_slash and ch == '/':
                found_slash = True
            elif found_slash and self._is_host_or_service_name_char(ch):
                found_instance_name = True
                instance_name_end_pos = self.temp_pos + 1
            else:
                break
            self.temp_pos += 1
        if found_instance_name:
            self.description.instance_name = \
                    self.data_as_str[self.pos + 1:instance_name_end_pos]
            self.pos = self.temp_pos

    cdef dict _process_args_with_extras(self, dict args, set allowed_names,
                                        str extras_name):
        """
        Processes arguments which contain a set of known attributes and any
        number of unknown attributes. The known attributes are left untouched
        whereas the unknown ones are put in a separate dictionary with the
        given name.
        """
        cdef:
            dict extras, result = {}
            object value
            str key
        for key, value in args.items():
            if key in allowed_names:
                result[key] = value
            else:
                extras = result.setdefault(extras_name, {})
                extras[key] = value
        return result

    cdef int _set_descriptor_arg(
        self, dict args, str name, object value
    ) except -1:
        """
        Sets the arg in the dictionary. If the value is already present,
        however, a list is created and both values stored. In addition, if an
        address is being added but an address list already exists, it is simply
        added to that address list instead. Similarly, if an address list is
        being added and addresses already exist, those addresses are first
        added to the address list before the new value is added.
        """
        # process unrecognized parameters, if applicable
        if name == "description":
            value = self._process_args_with_extras(
                value, DESCRIPTION_PARAM_NAMES, "extra_args"
            )
        elif name == "connect_data":
            value = self._process_args_with_extras(
                value, CONNECT_DATA_PARAM_NAMES, "extra_connect_data_args"
            )
        elif name == "security":
            value = self._process_args_with_extras(
                value, SECURITY_PARAM_NAMES, "extra_security_args"
            )

        # add value to arguments, creating a list if encountered multiple times
        orig_value = args.get(name)
        if orig_value is None:
            if name == "address" and "address_list" in args:
                return self._set_descriptor_arg(args, "address_list",
                                                dict(address=value))
            elif name == "address_list" and "address" in args:
                addresses = args.pop("address")
                if not isinstance(addresses, list):
                    addresses = [addresses]
                value = [dict(address=a) for a in addresses] + [value]
            args[name] = value
        elif isinstance(orig_value, list):
            args[name].append(value)
        else:
            args[name] = [orig_value, value]

    cdef int parse(self, str connect_string) except -1:
        """
        Parses a connect string. If the first character is an opening
        parenthesis, the connect string is assumed to be a connect descriptor
        and any failures to parse the string as a connect descriptor will
        result in an exception. If the connect string contains key elements
        identifying it as an easy connect string, any failures to parse the
        connect string as an easy connect string will result in an exception.
        If the connect string doesn't seem to be either option, the value None
        is returned.
        """
        cdef Py_UCS4 ch
        self.initialize(connect_string)
        ch = self.get_current_char()
        if ch == '(':
            self.temp_pos += 1
            self._parse_descriptor()
        else:
            self._parse_easy_connect()
        if self.description_list is not None and self.pos != self.num_chars:
            if self.pos > 0:
                errors._raise_err(errors.ERR_CANNOT_PARSE_CONNECT_STRING,
                                  data=connect_string)
            self.description_list = None


cdef class TnsnamesFileParser(BaseParser):

    cdef int _skip_to_end_of_line(self) except -1:
        """
        Skips all characters until the next line break is found and then
        discards all whitespace after that.
        """
        cdef Py_UCS4 ch
        while self.temp_pos < self.num_chars:
            ch = self.get_current_char()
            self.temp_pos += 1
            if cpython.Py_UNICODE_ISLINEBREAK(ch):
                break
        self.pos = self.temp_pos
        self.skip_spaces()

    cdef str _parse_key(self):
        """
        Parses a key from the file and returns it. This consists of any number
        of non-whitespace characters until an equals sign is found. Any
        comments are discarded. If no characters are found before the equals
        sign, the line is discarded. Similarly, if an opening or closing
        parenthesis is discovered, the line is discarded.
        """
        cdef:
            bint found_key = False
            ssize_t start_pos = 0
            Py_UCS4 ch
        self.skip_spaces()
        while self.temp_pos < self.num_chars:
            ch = self.get_current_char()
            if ch in ('(', ')', '#'):
                self._skip_to_end_of_line()
                found_key = False
                continue
            elif ch == '=':
                if not found_key:
                    self._skip_to_end_of_line()
                    continue
                self.temp_pos += 1
                self.pos = self.temp_pos
                return self.data_as_str[start_pos:self.temp_pos - 1].strip()
            elif not found_key:
                found_key = True
                start_pos = self.temp_pos
            self.temp_pos += 1

    cdef str _parse_value_part(self, ssize_t* num_parens):
        """
        Parses part of a value. This consists of all characters from the first
        non-whitespace character to the end of the value or the first comment.
        The number of parentheses are updated.
        """
        cdef:
            ssize_t start_pos = 0, end_pos = 0
            bint found_part = False
            Py_UCS4 ch
        self.skip_spaces()
        while self.temp_pos < self.num_chars:
            ch = self.get_current_char()
            if ch == '#':
                end_pos = self.temp_pos
                self._skip_to_end_of_line()
                if found_part:
                    break
                continue
            if found_part and num_parens[0] == 0:
                if cpython.Py_UNICODE_ISLINEBREAK(ch):
                    end_pos = self.temp_pos
                    break
            elif ch == '(':
                num_parens[0] += 1
            elif ch == ')' and num_parens[0] > 0:
                num_parens[0] -= 1
            if not found_part:
                found_part = True
                start_pos = self.temp_pos
            self.temp_pos += 1
            end_pos = self.temp_pos
        if found_part:
            return self.data_as_str[start_pos:end_pos].strip()

    cdef str _parse_value(self):
        """
        Parses a value from the file and returns it. This consists of all data
        after the first non-whitespace character until the end of the line on
        which it is found, or if the first non-whitespace character is an
        opening parenthesis, then all data until the number of opening and
        closing parentheses are equal.
        """
        cdef:
            ssize_t num_parens = 0
            list parts = []
            str part
        while self.temp_pos < self.num_chars:
            part = self._parse_value_part(&num_parens)
            if part is not None:
                parts.append(part)
            if num_parens == 0:
                break
        if parts:
            return "\n".join(parts)

    cdef int parse(self, str file_contents, object on_add_entry) except -1:
        """
        Parses the contents of a tnsnames.ora file. This consists of a series
        of key-value pairs where the keys can consist of comma-separated alias
        names and the values can be descriptors or easy connect strings. The
        method "on_add_entry" is called for each key-value pair that is
        discovered. No errors are thrown for improperly formatted files in
        order to be consistent with other drivers.
        """
        cdef str key, value
        self.initialize(file_contents)
        while self.temp_pos < self.num_chars:
            key = self._parse_key()
            value = self._parse_value()
            if key and value:
                on_add_entry(key.upper(), value.strip())
