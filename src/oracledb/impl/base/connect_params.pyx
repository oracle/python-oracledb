#------------------------------------------------------------------------------
# Copyright (c) 2022, Oracle and/or its affiliates.
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
# connect_params.pyx
#
# Cython file defining the base ConnectParams implementation class (embedded in
# base_impl.pyx).
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

# a set of parameter names in connect descriptors that are treated as
# containers (values are always lists)
CONTAINER_PARAM_NAMES = set((
    "address_list",
    "description",
    "address"
))

# regular expression used for determining if a connect string refers to an Easy
# Connect string or not
EASY_CONNECT_PATTERN = \
        "((?P<protocol>\w+)://)?(?P<host>[^:/]+)(:(?P<port>\d+)?)?/" \
        "(?P<service_name>[^:?]*)(:(?P<server_type>\w+))?"

# dictionary of tnsnames.ora files, indexed by the directory in which the file
# is found; the results are cached in order to avoid parsing a file multiple
# times; the modification time of the file is checked each time, though, to
# ensure that no changes were made since the last time that the file was read
# and parsed.
_tnsnames_files = {}

# internal default values
cdef str DEFAULT_PROTOCOL = "tcp"
cdef uint32_t DEFAULT_PORT = 1521
cdef double DEFAULT_TCP_CONNECT_TIMEOUT = 60


cdef dict _parse_connect_descriptor(str data, dict args):
    """
    Internal method which parses a connect descriptor containing name-value
    pairs in the form (KEY = VALUE), where the value can itself be another
    set of nested name-value pairs. A dictionary is returned containing
    these key value pairs.
    """
    if data[0] != "(" or data[-1] != ")":
        errors._raise_err(errors.ERR_INVALID_CONNECT_DESCRIPTOR, data=data)
    data = data[1:-1]
    pos = data.find("=")
    if pos < 0:
        errors._raise_err(errors.ERR_INVALID_CONNECT_DESCRIPTOR, data=data)
    name = data[:pos].strip().lower()
    data = data[pos + 1:].strip()
    if not data or not data.startswith("("):
        value = data
        if value and value[0] == '"' and value[-1] == '"':
            value = value[1:-1]
    else:
        value = {}
        while data:
            search_pos = 1
            num_opening_parens = 1
            num_closing_parens = 0
            while num_closing_parens < num_opening_parens:
                end_pos = data.find(")", search_pos)
                if end_pos < 0:
                    errors._raise_err(errors.ERR_INVALID_CONNECT_DESCRIPTOR,
                                      data=data)
                num_closing_parens += 1
                num_opening_parens += data.count("(", search_pos, end_pos)
                search_pos = end_pos + 1
            _parse_connect_descriptor(data[:end_pos + 1].strip(), value)
            data = data[end_pos + 1:].strip()
    name = ALTERNATIVE_PARAM_NAMES.get(name, name)
    if name in CONTAINER_PARAM_NAMES:
        args.setdefault(name, []).append(value)
    else:
        args[name] = value
    return args


cdef class ConnectParamsImpl:

    def __init__(self):
        cdef AddressList address_list
        self.stmtcachesize = defaults.stmtcachesize
        self.config_dir = defaults.config_dir
        self._default_description = Description()
        self._default_address = Address()
        self.description_list = DescriptionList()
        self.description_list.descriptions.append(self._default_description)
        self.debug_jdwp = os.getenv("ORA_DEBUG_JDWP")
        address_list = AddressList()
        address_list.addresses.append(self._default_address)
        self._default_description.address_lists.append(address_list)

    def set(self, dict args):
        """
        Sets the property values based on the supplied arguments. All values
        not supplied will be left unchanged.
        """
        self._external_handle = args.get("handle", 0)
        _set_str_param(args, "user", self)
        _set_str_param(args, "proxy_user", self)
        if self.proxy_user is None and self.user is not None:
            self.parse_user(self.user)
        self._set_password(args.get("password"))
        self._set_new_password(args.get("newpassword"))
        self._set_wallet_password(args.get("wallet_password"))
        _set_bool_param(args, "events", &self.events)
        _set_uint_param(args, "mode", &self.mode)
        _set_str_param(args, "edition", self)
        _set_str_param(args, "tag", self)
        _set_bool_param(args, "matchanytag", &self.matchanytag)
        _set_uint_param(args, "stmtcachesize", &self.stmtcachesize)
        _set_bool_param(args, "disable_oob", &self.disable_oob)
        _set_str_param(args, "debug_jdwp", self)
        _set_str_param(args, "config_dir", self)
        self.appcontext = args.get("appcontext")
        self.shardingkey = args.get("shardingkey")
        self.supershardingkey = args.get("supershardingkey")
        self._default_description.set_from_connect_data_args(args)
        self._default_description.set_from_description_args(args)
        self._default_description.set_from_security_args(args)
        self._default_address.set_from_args(args)

    cdef int _copy(self, ConnectParamsImpl other_params) except -1:
        """
        Internal method for copying attributes from another set of parameters.
        """
        self.config_dir = other_params.config_dir
        self.user = other_params.user
        self.proxy_user = other_params.proxy_user
        self.events = other_params.events
        self.mode = other_params.mode
        self.edition = other_params.edition
        self.appcontext = other_params.appcontext
        self.tag = other_params.tag
        self.matchanytag = other_params.matchanytag
        self.shardingkey = other_params.shardingkey
        self.supershardingkey = other_params.supershardingkey
        self.stmtcachesize = other_params.stmtcachesize
        self.disable_oob = other_params.disable_oob
        self.debug_jdwp = other_params.debug_jdwp
        self.description_list = other_params.description_list
        self._external_handle = other_params._external_handle
        self._default_description = other_params._default_description
        self._default_address = other_params._default_address
        self._password = other_params._password
        self._password_obfuscator = other_params._password_obfuscator
        self._new_password = other_params._new_password
        self._new_password_obfuscator = other_params._new_password_obfuscator
        self._wallet_password = other_params._wallet_password
        self._wallet_password_obfuscator = \
                other_params._wallet_password_obfuscator

    cdef bytes _get_new_password(self):
        """
        Returns the new password, after removing the obfuscation.
        """
        if self._new_password is not None:
            return bytes(self._xor_bytes(self._new_password,
                                         self._new_password_obfuscator))

    cdef bytearray _get_obfuscator(self, str password):
        """
        Return a byte array suitable for obfuscating the specified password.
        """
        return bytearray(secrets.token_bytes(len(password.encode())))

    cdef bytes _get_password(self):
        """
        Returns the password, after removing the obfuscation.
        """
        if self._password is not None:
            return bytes(self._xor_bytes(self._password,
                                         self._password_obfuscator))

    cdef TnsnamesFile _get_tnsnames_file(self):
        """
        Return a tnsnames file, if one is present, or None if one is not. If
        the file was previously loaded, the modification time is checked and,
        if unchanged, the previous file is returned.
        """
        cdef TnsnamesFile tnsnames_file
        if self.config_dir is None:
            errors._raise_err(errors.ERR_NO_CONFIG_DIR)
        file_name = os.path.join(self.config_dir, "tnsnames.ora")
        tnsnames_file = _tnsnames_files.get(self.config_dir)
        try:
            stat_info = os.stat(file_name)
        except:
            if tnsnames_file is not None:
                del _tnsnames_files[self.config_dir]
            errors._raise_err(errors.ERR_TNS_NAMES_FILE_MISSING,
                              config_dir=self.config_dir)
        if tnsnames_file is not None \
                and tnsnames_file.mtime == stat_info.st_mtime:
            return tnsnames_file
        tnsnames_file = TnsnamesFile(file_name, stat_info.st_mtime)
        tnsnames_file.read()
        _tnsnames_files[self.config_dir] = tnsnames_file
        return tnsnames_file

    cdef str _get_wallet_password(self):
        """
        Returns the wallet password, after removing the obfuscation.
        """
        if self._wallet_password is not None:
            return self._xor_bytes(self._wallet_password,
                                   self._wallet_password_obfuscator).decode()

    cdef int _parse_connect_string(self, str connect_string) except -1:
        """
        Internal method for parsing a connect string.
        """
        cdef:
            TnsnamesFile tnsnames_file
            Description description
            Address address
            dict args = {}
            str name

        # if a connect string starts with an opening parenthesis it is assumed
        # to be a full connect descriptor
        if connect_string.startswith("("):
            _parse_connect_descriptor(connect_string, args)
            return self._process_connect_descriptor(args)

        # otherwise, see if the connect string is an EasyConnect string
        m = re.search(EASY_CONNECT_PATTERN, connect_string)
        if m is not None:

            # build up arguments
            args = m.groupdict()
            connect_string = connect_string[m.end():]
            params_pos = connect_string.find("?")
            if params_pos >= 0:
                params = connect_string[params_pos + 1:]
                for part in params.split("&"):
                    name, value = [s.strip() for s in part.split("=", 1)]
                    name = name.lower()
                    name = ALTERNATIVE_PARAM_NAMES.get(name, name)
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    args[name] = value

            # create description list
            address = self._default_address.copy()
            address.set_from_args(args)
            description = self._default_description.copy()
            description.set_from_connect_data_args(args)
            description.set_from_description_args(args)
            description.set_from_security_args(args)
            description.address_lists = [AddressList()]
            description.address_lists[0].addresses.append(address)
            self.description_list = DescriptionList()
            self.description_list.descriptions.append(description)

        # otherwise, see if the name is a connect alias in a tnsnames.ora
        # configuration file
        else:
            tnsnames_file = self._get_tnsnames_file()
            name = connect_string
            connect_string = tnsnames_file.entries.get(name.upper())
            if connect_string is None:
                errors._raise_err(errors.ERR_TNS_ENTRY_NOT_FOUND, name=name,
                                  file_name=tnsnames_file.file_name)
            _parse_connect_descriptor(connect_string, args)
            self._process_connect_descriptor(args)

    cdef int _process_connect_descriptor(self, dict args) except -1:
        """
        Internal method used for processing the parsed connect descriptor into
        the set of DescriptionList, Description, AddressList and Address
        container objects.
        """
        cdef:
            AddressList address_list
            Description description
            Address address
        self.description_list = DescriptionList()
        list_args = args.get("description_list")
        if list_args is not None:
            self.description_list.set_from_args(list_args)
        else:
            list_args = args
        for desc_args in list_args.get("description", [list_args]):
            description = self._default_description.copy()
            description.set_from_description_args(desc_args)
            self.description_list.descriptions.append(description)
            sub_args = desc_args.get("connect_data")
            if sub_args is not None:
                description.set_from_connect_data_args(sub_args)
            sub_args = desc_args.get("security")
            if sub_args is not None:
                description.set_from_security_args(sub_args)
            for list_args in desc_args.get("address_list", [desc_args]):
                address_list = AddressList()
                address_list.set_from_args(list_args)
                description.address_lists.append(address_list)
                for addr_args in list_args.get("address", []):
                    address = self._default_address.copy()
                    address.set_from_args(addr_args)
                    address_list.addresses.append(address)

    cdef int _set_new_password(self, str password) except -1:
        """
        Sets the new password on the instance after first obfuscating it.
        """
        if password is not None:
            self._new_password_obfuscator = self._get_obfuscator(password)
            self._new_password = self._xor_bytes(bytearray(password.encode()),
                                                self._new_password_obfuscator)

    cdef int _set_password(self, str password) except -1:
        """
        Sets the password on the instance after first obfuscating it.
        """
        if password is not None:
            self._password_obfuscator = self._get_obfuscator(password)
            self._password = self._xor_bytes(bytearray(password.encode()),
                                             self._password_obfuscator)

    cdef int _set_wallet_password(self, str password) except -1:
        """
        Sets the wallet password on the instance after first obfuscating it.
        """
        if password is not None:
            self._wallet_password_obfuscator = self._get_obfuscator(password)
            self._wallet_password = \
                    self._xor_bytes(bytearray(password.encode()),
                                    self._wallet_password_obfuscator)

    cdef bytearray _xor_bytes(self, bytearray a, bytearray b):
        """
        Perform an XOR of two byte arrays as a means of obfuscating a password
        that is stored on the class. It is assumed that the byte arrays are of
        the same length.
        """
        cdef:
            ssize_t length, i
            bytearray result
        length = len(a)
        result = bytearray(length)
        for i in range(length):
            result[i] = a[i] ^ b[i]
        return result

    def copy(self):
        """
        Creates a copy of the connection parameters and returns it.
        """
        cdef ConnectParamsImpl new_params
        new_params = ConnectParamsImpl.__new__(ConnectParamsImpl)
        new_params._copy(self)
        return new_params

    def _get_addresses(self):
        """
        Return a list of the stored addresses.
        """
        cdef:
            AddressList addr_list
            Description desc
            Address addr
        return [addr for desc in self.description_list.descriptions \
                for addr_list in desc.address_lists \
                for addr in addr_list.addresses]

    def get_connect_string(self):
        """
        Internal method for getting the connect string. This will either be the
        connect string supplied to parse_connect_string() or parse_dsn(), or it
        will be a connect string built up from the components supplied when the
        object was built.
        """
        if self._default_address.host is not None:
            return self.description_list.build_connect_string()

    def get_full_user(self):
        """
        Internal method used for getting the full user (including any proxy
        user) which is used in thick mode exlusively and which is used in
        the repr() methods for Connection and ConnectionPool.
        """
        if self.proxy_user is not None:
            return f"{self.user}[{self.proxy_user}]"
        return self.user

    def parse_connect_string(self, str connect_string):
        """
        Internal method for parsing the connect string.
        """
        connect_string = connect_string.strip()
        try:
            self._parse_connect_string(connect_string)
        except exceptions.Error:
            raise
        except Exception as e:
            errors._raise_err(errors.ERR_CANNOT_PARSE_CONNECT_STRING, cause=e,
                              data=connect_string)

    def parse_dsn(self, str dsn, bint parse_connect_string):
        """
        Parse a dsn (data source name) string supplied by the user. This can be
        in the form user/password@connect_string or it can be a simple connect
        string. The connect string is returned and the user, proxy_user and
        password values are retained.
        """
        connect_string = dsn
        pos = dsn.rfind("@")
        if pos >= 0:
            credentials = dsn[:pos]
            connect_string = dsn[pos + 1:]
            pos = credentials.find("/")
            if pos >= 0:
                user = credentials[:pos]
                self._set_password(credentials[pos + 1:])
            else:
                user = credentials
            self.parse_user(user)
        if parse_connect_string:
            self.parse_connect_string(connect_string)
        return connect_string

    def parse_user(self, str user):
        """
        Parses a user string into its component parts, if applicable. The user
        string may be in the form user[proxy_user] or it may simply be a simple
        user string.
        """
        start_pos = user.find("[")
        if start_pos > 0 and user.endswith("]"):
            self.proxy_user = user[start_pos + 1:-1]
            self.user = user[:start_pos]
        else:
            self.user = user


cdef class Address:
    """
    Internal class used to hold parameters for an address used to create a
    connection to the database.
    """

    def __init__(self):
        self.protocol = DEFAULT_PROTOCOL
        self.port = DEFAULT_PORT

    cdef str build_connect_string(self):
        """
        Build a connect string from the components.
        """
        parts = [f"(PROTOCOL={self.protocol})",
                 f"(HOST={self.host})",
                 f"(PORT={self.port})"]
        if self.https_proxy is not None:
            parts.append(f"(HTTPS_PROXY={self.https_proxy})")
        if self.https_proxy_port != 0:
            parts.append(f"(HTTPS_PROXY_PORT={self.https_proxy_port})")
        return f'(ADDRESS={"".join(parts)})'

    def copy(self):
        """
        Creates a copy of the address and returns it.
        """
        cdef Address address = Address.__new__(Address)
        address.host = self.host
        address.port = self.port
        address.protocol = self.protocol
        address.https_proxy = self.https_proxy
        address.https_proxy_port = self.https_proxy_port
        return address

    @classmethod
    def from_args(cls, dict args):
        """
        Creates an address and sets the arguments before returning it. This is
        used within connect descriptors containing address lists.
        """
        address = cls()
        address.set_from_args(args)
        return address

    def set_from_args(self, dict args):
        """
        Sets parameter values from an argument dictionary or an (ADDRESS) node
        in a connect descriptor.
        """
        _set_str_param(args, "host", self)
        _set_uint_param(args, "port", &self.port)
        _set_protocol_param(args, "protocol", self)
        _set_str_param(args, "https_proxy", self)
        _set_uint_param(args, "https_proxy_port", &self.https_proxy_port)


cdef class AddressList:
    """
    Internal class used to hold address list parameters and a list of addresses
    used to create connections to the database.
    """

    def __init__(self):
        self.addresses = []

    cdef str build_connect_string(self):
        """
        Build a connect string from the components.
        """
        cdef Address a
        parts = [a.build_connect_string() for a in self.addresses]
        return f'(ADDRESS_LIST={"".join(parts)})'

    def set_from_args(self, dict args):
        """
        Set paramter values from an argument dictionary or an (ADDRESS_LIST)
        node in a connect descriptor.
        """
        _set_bool_param(args, "load_balance", &self.load_balance)


cdef class Description:
    """
    Internal class used to hold description parameters.
    """

    def __init__(self):
        self.address_lists = []
        self.tcp_connect_timeout = DEFAULT_TCP_CONNECT_TIMEOUT
        self.ssl_server_dn_match = True

    cdef str _build_duration_str(self, double value):
        """
        Build up the value to display for a duration in the connect string.
        This must be an integer with the units following it.
        """
        cdef int value_int, value_minutes
        value_int = <int> value
        if value != value_int:
            return f"{int(value * 1000)}ms"
        value_minutes = (value_int // 60)
        if value_minutes * 60 == value_int:
            return f"{value_minutes}min"
        return f"{value_int}"

    cdef str build_connect_string(self):
        """
        Build a connect string from the components.
        """
        cdef:
            str connect_data, security, temp
            list parts, address_lists
            AddressList a

        # build connect data segment
        parts = []
        if self.service_name is not None:
            parts.append(f"(SERVICE_NAME={self.service_name})")
        elif self.sid is not None:
            parts.append(f"(SID={self.sid})")
        if self.server_type is not None:
            parts.append(f"(SERVER={self.server_type})")
        if self.cclass is not None:
            parts.append(f"(POOL_CONNECTION_CLASS={self.cclass})")
        if self.purity != 0:
            parts.append(f"(POOL_PURITY={self.purity})")
        connect_data = f'(CONNECT_DATA={"".join(parts)})'

        # build security segment, if applicable
        parts = [f"(SSL_SERVER_DN_MATCH={self.ssl_server_dn_match})"]
        if self.ssl_server_cert_dn is not None:
            parts.append(f"(SSL_SERVER_CERT_DN={self.ssl_server_cert_dn})")
        if self.wallet_location is not None:
            parts.append(f"(MY_WALLET_DIRECTORY={self.wallet_location})")
        security = f'(SECURITY={"".join(parts)})'

        # build connect string
        parts = []
        if self.load_balance:
            parts.append("(LOAD_BALANCE=ON)")
        if self.retry_count != 0:
            parts.append(f"(RETRY_COUNT={self.retry_count})")
        if self.retry_delay != 0:
            parts.append(f"(RETRY_DELAY={self.retry_delay})")
        if self.expire_time != 0:
            parts.append(f"(EXPIRE_TIME={self.expire_time})")
        if self.tcp_connect_timeout != DEFAULT_TCP_CONNECT_TIMEOUT:
            temp = self._build_duration_str(self.tcp_connect_timeout)
            parts.append(f"(TRANSPORT_CONNECT_TIMEOUT={temp})")
        address_lists = [a.build_connect_string() for a in self.address_lists]
        parts.extend(address_lists)
        parts.append(connect_data)
        parts.append(security)
        return f'(DESCRIPTION={"".join(parts)})'

    def copy(self):
        """
        Creates a copy of the description (except for the address lists) and
        returns it.
        """
        cdef Description description = Description.__new__(Description)
        description.address_lists = []
        description.service_name = self.service_name
        description.sid = self.sid
        description.server_type = self.server_type
        description.cclass = self.cclass
        description.purity = self.purity
        description.expire_time = self.expire_time
        description.load_balance = self.load_balance
        description.retry_count = self.retry_count
        description.retry_delay = self.retry_delay
        description.tcp_connect_timeout = self.tcp_connect_timeout
        description.ssl_server_dn_match = self.ssl_server_dn_match
        description.ssl_server_cert_dn = self.ssl_server_cert_dn
        description.wallet_location = self.wallet_location
        return description

    def set_from_connect_data_args(self, dict args):
        """
        Set parameter values from an argument dictionary or a (CONNECT_DATA)
        node in a connect descriptor.
        """
        _set_str_param(args, "service_name", self)
        _set_str_param(args, "sid", self)
        _set_server_type_param(args, "server_type", self)
        _set_str_param(args, "cclass", self)
        _set_purity_param(args, "purity", &self.purity)

    def set_from_description_args(self, dict args):
        """
        Set parameter values from an argument dictionary or a (DESCRIPTION)
        node in a connect descriptor.
        """
        cdef Address address
        _set_uint_param(args, "expire_time", &self.expire_time)
        _set_bool_param(args, "load_balance", &self.load_balance)
        _set_uint_param(args, "retry_count", &self.retry_count)
        _set_uint_param(args, "retry_delay", &self.retry_delay)
        _set_duration_param(args, "tcp_connect_timeout",
                            &self.tcp_connect_timeout)

    def set_from_security_args(self, dict args):
        """
        Set parameter values from an argument dictionary or a (SECURITY)
        node in a connect descriptor.
        """
        _set_bool_param(args, "ssl_server_dn_match", &self.ssl_server_dn_match)
        _set_str_param(args, "ssl_server_cert_dn", self)
        _set_str_param(args, "wallet_location", self)


cdef class DescriptionList:
    """
    Internal class used to hold description list parameters and a list of
    descriptions.
    """

    def __init__(self):
        self.descriptions = []

    cdef str build_connect_string(self):
        """
        Build a connect string from the components.
        """
        cdef:
            Description d
            list parts
        parts = [d.build_connect_string() for d in self.descriptions]
        if len(parts) == 1:
            return parts[0]
        return f'(DESCIPTION_LIST={"".join(parts)})'

    def set_from_args(self, dict args):
        """
        Set paramter values from an argument dictionary or a (DESCRIPTION_LIST)
        node in a connect descriptor.
        """
        _set_bool_param(args, "load_balance", &self.load_balance)


cdef class TnsnamesFile:
    """
    Internal class used to parse and retain connect descriptor entries found in
    a tnsnames.ora file.
    """

    def __init__(self, str file_name, int mtime):
        self.file_name = file_name
        self.mtime = mtime
        self.entries = {}

    def read(self):
        """
        Read and parse the file and retain the connect descriptors found inside
        the file.
        """
        with open(self.file_name) as f:
            entry_names = None
            for line in f:
                line = line.strip()
                pos = line.find("#")
                if pos >= 0:
                    line = line[:pos]
                if not line:
                    continue
                if entry_names is None:
                    pos = line.find("=")
                    if pos < 0:
                        continue
                    entry_names = [s.strip() for s in line[:pos].split(",")]
                    entry_lines = []
                    num_parens = 0
                    line = line[pos+1:].strip()
                if line:
                    num_parens += line.count("(") - line.count(")")
                    entry_lines.append(line)
                if entry_lines and num_parens <= 0:
                    descriptor = "".join(entry_lines)
                    for name in entry_names:
                        self.entries[name.upper()] = descriptor
                    entry_names = None
