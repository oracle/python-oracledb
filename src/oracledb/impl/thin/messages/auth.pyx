#------------------------------------------------------------------------------
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
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
# auth.pyx
#
# Cython file defining the messages sent to the database and the responses that
# are received by the client for authentication (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

@cython.final
cdef class AuthMessage(Message):
    cdef:
        str encoded_password
        bytes password
        bytes newpassword
        str encoded_newpassword
        str encoded_jdwp_data
        str debug_jdwp
        str session_key
        str speedy_key
        str proxy_user
        str token
        str private_key
        str service_name
        uint8_t purity
        ssize_t user_bytes_len
        bytes user_bytes
        dict session_data
        uint32_t auth_mode
        uint32_t verifier_type
        bint change_password
        str program
        str terminal
        str machine
        str osuser
        str driver_name
        str edition
        list appcontext
        str connect_string

    cdef int _encrypt_passwords(self) except -1:
        """
        Encrypts the passwords using the session key.
        """

        # encrypt password
        salt = secrets.token_bytes(16)
        password_with_salt = salt + self.password
        encrypted_password = encrypt_cbc(self.conn_impl._combo_key,
                                         password_with_salt)
        self.encoded_password = encrypted_password.hex().upper()

        # encrypt new password
        if self.newpassword is not None:
            newpassword_with_salt = salt + self.newpassword
            encrypted_newpassword = encrypt_cbc(self.conn_impl._combo_key,
                                                newpassword_with_salt)
            self.encoded_newpassword = encrypted_newpassword.hex().upper()

    cdef int _generate_verifier(self) except -1:
        """
        Generate the multi-round verifier.
        """
        cdef:
            bytes jdwp_data
            bytearray b
            ssize_t i

        # create password hash
        verifier_data = bytes.fromhex(self.session_data['AUTH_VFR_DATA'])
        if self.verifier_type == TNS_VERIFIER_TYPE_12C:
            keylen = 32
            iterations = int(self.session_data['AUTH_PBKDF2_VGEN_COUNT'])
            salt = verifier_data + b'AUTH_PBKDF2_SPEEDY_KEY'
            password_key = get_derived_key(self.password, salt, 64,
                                           iterations)
            h = hashlib.new("sha512")
            h.update(password_key)
            h.update(verifier_data)
            password_hash = h.digest()[:32]
        else:
            keylen = 24
            h = hashlib.sha1(self.password)
            h.update(verifier_data)
            password_hash = h.digest() + bytes(4)

        # decrypt first half of session key
        encoded_server_key = bytes.fromhex(self.session_data['AUTH_SESSKEY'])
        session_key_part_a = decrypt_cbc(password_hash, encoded_server_key)

        # generate second half of session key
        session_key_part_b = secrets.token_bytes(len(session_key_part_a))
        encoded_client_key = encrypt_cbc(password_hash, session_key_part_b)

        # create session key and combo key
        if len(session_key_part_a) == 48:
            self.session_key = encoded_client_key.hex().upper()[:96]
            b = bytearray(24)
            for i in range(16, 40):
                b[i - 16] = session_key_part_a[i] ^ session_key_part_b[i]
            part1 = hashlib.md5(b[:16]).digest()
            part2 = hashlib.md5(b[16:]).digest()
            combo_key = (part1 + part2)[:keylen]
        else:
            self.session_key = encoded_client_key.hex().upper()[:64]
            salt = bytes.fromhex(self.session_data['AUTH_PBKDF2_CSK_SALT'])
            iterations = int(self.session_data['AUTH_PBKDF2_SDER_COUNT'])
            temp_key = session_key_part_b[:keylen] + session_key_part_a[:keylen]
            combo_key = get_derived_key(temp_key.hex().upper().encode(), salt,
                                        keylen, iterations)

        # retain session key for use by the change password API
        self.conn_impl._combo_key = combo_key

        # generate speedy key for 12c verifiers
        if self.verifier_type == TNS_VERIFIER_TYPE_12C:
            salt = secrets.token_bytes(16)
            speedy_key = encrypt_cbc(combo_key, salt + password_key)
            self.speedy_key = speedy_key[:80].hex().upper()

        # encrypts the passwords
        self._encrypt_passwords()

        # check if debug_jdwp is set. if set, encode the data using the
        # combo session key with zeros padding
        if self.debug_jdwp is not None:
            jdwp_data = self.debug_jdwp.encode()
            encrypted_jdwp_data = encrypt_cbc(combo_key, jdwp_data, zeros=True)
            # Add a "01" at the end of the hex encrypted data to indicate the
            # use of AES encryption
            self.encoded_jdwp_data = encrypted_jdwp_data.hex().upper() + "01"

    cdef str _get_alter_timezone_statement(self):
        """
        Returns the statement required to change the session time zone to match
        the time zone in use by the Python interpreter.
        """
        cdef:
            int tz_hour, tz_minute, timezone
            str sign, tz_repr
        tz_repr = os.environ.get("ORA_SDTZ")
        if tz_repr is None:
            timezone = time.localtime().tm_gmtoff
            tz_hour = timezone // 3600
            tz_minute = (timezone - (tz_hour * 3600)) // 60
            if tz_hour < 0:
                sign = "-"
                tz_hour = -tz_hour
            else:
                sign = "+"
            tz_repr = f"{sign}{tz_hour:02}:{tz_minute:02}"
        return f"ALTER SESSION SET TIME_ZONE='{tz_repr}'\x00"

    cdef tuple _get_version_tuple(self, ReadBuffer buf):
        """
        Return the 5-tuple for the database version. Note that the format
        changed with Oracle Database 18.
        """
        cdef uint32_t full_version_num
        full_version_num = int(self.session_data["AUTH_VERSION_NO"])
        if buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_18_1_EXT_1:
            return ((full_version_num >> 24) & 0xFF,
                    (full_version_num >> 16) & 0xFF,
                    (full_version_num >> 12) & 0x0F,
                    (full_version_num >> 4) & 0xFF,
                    (full_version_num & 0x0F))
        else:
            return ((full_version_num >> 24) & 0xFF,
                    (full_version_num >> 20) & 0x0F,
                    (full_version_num >> 12) & 0x0F,
                    (full_version_num >> 8) & 0x0F,
                    (full_version_num & 0x0F))

    cdef int _initialize_hook(self) except -1:
        """
        Perform initialization.
        """
        self.function_code = TNS_FUNC_AUTH_PHASE_ONE
        self.session_data = {}
        if self.conn_impl.username is not None:
            self.user_bytes = self.conn_impl.username.encode()
            self.user_bytes_len = len(self.user_bytes)
        self.resend = True

    cdef int _process_return_parameters(self, ReadBuffer buf) except -1:
        cdef:
            uint16_t num_params, i
            str key, value
        buf.read_ub2(&num_params)
        for i in range(num_params):
            key = buf.read_str_with_length()
            value = buf.read_str_with_length()
            if value is None:
                value = ""
            if key == "AUTH_VFR_DATA":
                buf.read_ub4(&self.verifier_type)
            else:
                buf.skip_ub4()                  # skip flags
            self.session_data[key] = value
        if self.function_code == TNS_FUNC_AUTH_PHASE_ONE:
            self.function_code = TNS_FUNC_AUTH_PHASE_TWO
        elif not self.change_password:
            self.conn_impl._session_id = \
                    <uint32_t> int(self.session_data["AUTH_SESSION_ID"])
            self.conn_impl._serial_num = \
                    <uint16_t> int(self.session_data["AUTH_SERIAL_NUM"])
            self.conn_impl._db_domain = \
                    self.session_data.get("AUTH_SC_DB_DOMAIN")
            self.conn_impl._db_name = \
                    self.session_data.get("AUTH_SC_DBUNIQUE_NAME")
            self.conn_impl._max_open_cursors = \
                    int(self.session_data.get("AUTH_MAX_OPEN_CURSORS", 0))
            self.conn_impl._service_name = \
                    self.session_data.get("AUTH_SC_SERVICE_NAME")
            self.conn_impl._instance_name = \
                    self.session_data.get("AUTH_INSTANCENAME")
            self.conn_impl._max_identifier_length = \
                    int(self.session_data.get("AUTH_MAX_IDEN_LENGTH", 30))
            self.conn_impl.server_version = self._get_version_tuple(buf)
            self.conn_impl.supports_bool = \
                    buf._caps.ttc_field_version >= TNS_CCAP_FIELD_VERSION_23_1
            self.conn_impl._edition = self.edition

    cdef int _set_params(self, ConnectParamsImpl params,
                         Description description) except -1:
        """
        Sets the parameters to use for the AuthMessage. The user and auth mode
        are retained in order to avoid duplicating this effort for both trips
        to the server.
        """
        self.password = params._get_password()
        self.newpassword = params._get_new_password()
        self.service_name = description.service_name
        self.proxy_user = params.proxy_user
        self.debug_jdwp = params.debug_jdwp
        self.program = params.program
        self.terminal = params.terminal
        self.machine = params.machine
        self.osuser = params.osuser
        self.driver_name = params.driver_name
        if self.driver_name is None:
            self.driver_name = f"{DRIVER_NAME} thn : {DRIVER_VERSION}"
        self.edition = params.edition
        self.appcontext = params.appcontext
        self.connect_string = params._get_connect_string()

        # if drcp is used, use purity = NEW as the default purity for
        # standalone connections and purity = SELF for connections that belong
        # to a pool
        if description.purity == PURITY_DEFAULT \
                and self.conn_impl._drcp_enabled:
            if self.conn_impl._pool is None:
                self.purity = PURITY_NEW
            else:
                self.purity = PURITY_SELF
        else:
            self.purity = description.purity

        # set token parameters; adjust processing so that only phase two is
        # sent
        if params._token is not None \
                or params.access_token_callback is not None:
            self.token = params._get_token()
            if params._private_key is not None:
                self.private_key = params._get_private_key()
            self.function_code = TNS_FUNC_AUTH_PHASE_TWO
            self.resend = False

        # set authentication mode
        if params._new_password is None:
            self.auth_mode = TNS_AUTH_MODE_LOGON
        if params.mode & AUTH_MODE_SYSDBA:
            self.auth_mode |= TNS_AUTH_MODE_SYSDBA
        if params.mode & AUTH_MODE_SYSOPER:
            self.auth_mode |= TNS_AUTH_MODE_SYSOPER
        if params.mode & AUTH_MODE_SYSASM:
            self.auth_mode |= TNS_AUTH_MODE_SYSASM
        if params.mode & AUTH_MODE_SYSBKP:
            self.auth_mode |= TNS_AUTH_MODE_SYSBKP
        if params.mode & AUTH_MODE_SYSDGD:
            self.auth_mode |= TNS_AUTH_MODE_SYSDGD
        if params.mode & AUTH_MODE_SYSKMT:
            self.auth_mode |= TNS_AUTH_MODE_SYSKMT
        if params.mode & AUTH_MODE_SYSRAC:
            self.auth_mode |= TNS_AUTH_MODE_SYSRAC
        if self.private_key is not None:
            self.auth_mode |= TNS_AUTH_MODE_IAM_TOKEN

    cdef int _write_key_value(self, WriteBuffer buf, str key, str value,
                              uint32_t flags=0) except -1:
        cdef:
            bytes key_bytes = key.encode()
            bytes value_bytes = value.encode()
            uint32_t key_len = <uint32_t> len(key_bytes)
            uint32_t value_len = <uint32_t> len(value_bytes)
        buf.write_ub4(key_len)
        buf.write_bytes_with_length(key_bytes)
        buf.write_ub4(value_len)
        if value_len > 0:
            buf.write_bytes_with_length(value_bytes)
        buf.write_ub4(flags)

    cdef int _write_message(self, WriteBuffer buf) except -1:
        cdef:
            uint8_t has_user = 1 if self.user_bytes_len > 0 else 0
            uint32_t num_pairs

        # perform final determination of data to write
        if self.function_code == TNS_FUNC_AUTH_PHASE_ONE:
            num_pairs = 5
        elif self.change_password:
            self._encrypt_passwords()
            num_pairs = 2
        else:
            num_pairs = 4

            # token authentication
            if self.token is not None:
                num_pairs += 1

            # normal user/password authentication
            else:
                num_pairs += 2
                self.auth_mode |= TNS_AUTH_MODE_WITH_PASSWORD
                if self.verifier_type == TNS_VERIFIER_TYPE_12C:
                    num_pairs += 1
                elif self.verifier_type not in (TNS_VERIFIER_TYPE_11G_1,
                                                TNS_VERIFIER_TYPE_11G_2):
                    errors._raise_err(errors.ERR_UNSUPPORTED_VERIFIER_TYPE,
                                      verifier_type=self.verifier_type)
                self._generate_verifier()

            # determine which other key/value pairs to write
            if self.newpassword is not None:
                num_pairs += 1
                self.auth_mode |= TNS_AUTH_MODE_CHANGE_PASSWORD
            if self.proxy_user is not None:
                num_pairs += 1
            if self.conn_impl._cclass is not None:
                num_pairs += 1
            if self.purity != 0:
                num_pairs += 1
            if self.private_key is not None:
                num_pairs += 2
            if self.encoded_jdwp_data is not None:
                num_pairs += 1
            if self.edition is not None:
                num_pairs += 1
            if self.appcontext is not None:
                num_pairs += len(self.appcontext) * 3
            if self.connect_string is not None:
                num_pairs += 1

        # write basic data to packet
        self._write_function_code(buf)
        buf.write_uint8(has_user)           # pointer (authusr)
        buf.write_ub4(self.user_bytes_len)
        buf.write_ub4(self.auth_mode)       # authentication mode
        buf.write_uint8(1)                  # pointer (authivl)
        buf.write_ub4(num_pairs)            # number of key/value pairs
        buf.write_uint8(1)                  # pointer (authovl)
        buf.write_uint8(1)                  # pointer (authovln)
        if has_user:
            buf.write_bytes_with_length(self.user_bytes)

        # write key/value pairs
        if self.function_code == TNS_FUNC_AUTH_PHASE_ONE:
            self._write_key_value(buf, "AUTH_TERMINAL", self.terminal)
            self._write_key_value(buf, "AUTH_PROGRAM_NM", self.program)
            self._write_key_value(buf, "AUTH_MACHINE", self.machine)
            self._write_key_value(buf, "AUTH_PID", _connect_constants.pid)
            self._write_key_value(buf, "AUTH_SID", self.osuser)
        else:
            if self.proxy_user is not None:
                self._write_key_value(buf, "PROXY_CLIENT_NAME",
                                      self.proxy_user)
            if self.token is not None:
                self._write_key_value(buf, "AUTH_TOKEN", self.token)
            elif not self.change_password:
                self._write_key_value(buf, "AUTH_SESSKEY", self.session_key, 1)
                if self.verifier_type == TNS_VERIFIER_TYPE_12C:
                    self._write_key_value(buf, "AUTH_PBKDF2_SPEEDY_KEY",
                                          self.speedy_key)
            if self.encoded_password is not None:
                self._write_key_value(buf, "AUTH_PASSWORD",
                                      self.encoded_password)
            if self.encoded_newpassword is not None:
                self._write_key_value(buf, "AUTH_NEWPASSWORD",
                                      self.encoded_newpassword)
            if not self.change_password:
                self._write_key_value(buf, "SESSION_CLIENT_CHARSET", "873")
                self._write_key_value(buf, "SESSION_CLIENT_DRIVER_NAME",
                                      self.driver_name)
                self._write_key_value(buf, "SESSION_CLIENT_VERSION",
                                    str(_connect_constants.full_version_num))
                self._write_key_value(buf, "AUTH_ALTER_SESSION",
                                      self._get_alter_timezone_statement(), 1)
            if self.conn_impl._cclass is not None:
                self._write_key_value(buf, "AUTH_KPPL_CONN_CLASS",
                                      self.conn_impl._cclass)
            if self.purity != 0:
                self._write_key_value(buf, "AUTH_KPPL_PURITY",
                                      str(self.purity), 1)
            if self.private_key is not None:
                date_format = "%a, %d %b %Y %H:%M:%S GMT"
                now = datetime.datetime.utcnow().strftime(date_format)
                host_info = "%s:%d" % buf._transport.get_host_info()
                header = f"date: {now}\n" + \
                         f"(request-target): {self.service_name}\n" + \
                         f"host: {host_info}"
                signature = get_signature(self.private_key, header)
                self._write_key_value(buf, "AUTH_HEADER", header)
                self._write_key_value(buf, "AUTH_SIGNATURE", signature)
            if self.encoded_jdwp_data is not None:
                self._write_key_value(buf, "AUTH_ORA_DEBUG_JDWP",
                                      self.encoded_jdwp_data)
            if self.edition is not None:
                self._write_key_value(buf, "AUTH_ORA_EDITION", self.edition)
            if self.appcontext is not None:
                # NOTE: these keys require a trailing null character as the
                # server expects it!
                for entry in self.appcontext:
                    self._write_key_value(buf, "AUTH_APPCTX_NSPACE\0", entry[0])
                    self._write_key_value(buf, "AUTH_APPCTX_ATTR\0", entry[1])
                    self._write_key_value(buf, "AUTH_APPCTX_VALUE\0", entry[2])
            if self.connect_string is not None:
                self._write_key_value(buf, "AUTH_CONNECT_STRING",
                                      self.connect_string)
