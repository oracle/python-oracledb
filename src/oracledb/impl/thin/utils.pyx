#------------------------------------------------------------------------------
# Copyright (c) 2020, 2023, Oracle and/or its affiliates.
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
# utils.pyx
#
# Cython file defining utility classes and methods (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

class OutOfPackets(Exception):
    pass

class ConnectConstants:

    def __init__(self):
        self.program_name = sys.executable
        self.machine_name = socket.gethostname()
        self.pid = str(os.getpid())
        try:
            self.user_name = getpass.getuser()
        except:
            self.user_name = ""
        self.terminal_name = "unknown"
        self.sanitized_program_name = self._sanitize(self.program_name)
        self.sanitized_machine_name = self._sanitize(self.machine_name)
        self.sanitized_user_name = self._sanitize(self.user_name)
        pattern = r"(?P<major_num>\d+)\.(?P<minor_num>\d+)\.(?P<patch_num>\d+)"
        match_dict = re.match(pattern, VERSION)
        major_num = int(match_dict["major_num"])
        minor_num = int(match_dict["minor_num"])
        patch_num = int(match_dict["patch_num"])
        self.full_version_num = \
                major_num << 24 | minor_num << 20 | patch_num << 12

    def _sanitize(self, value):
        """
        Sanitize the value by replacing all the "(", ")" and "=" characters
        with "?". These are invalid characters within connect data.
        """
        return value.replace("(", "?").replace(")", "?").replace("=", "?")

_connect_constants = ConnectConstants()

cdef int _convert_base64(char_type *buf, long value, int size, int offset):
    """
    Converts every 6 bits into a character, from left to right. This is
    similar to ordinary base64 encoding with a few differences and written
    here for performance.
    """
    cdef int i
    for i in range(size):
        buf[offset + size - i - 1] = TNS_BASE64_ALPHABET_ARRAY[value & 0x3f]
        value = value >> 6
    return offset + size


cdef object _encode_rowid(Rowid *rowid):
    """
    Converts the rowid structure into an encoded string, if the rowid structure
    contains valid data; otherwise, it returns None.
    """
    cdef:
        char_type buf[TNS_MAX_ROWID_LENGTH]
        int offset = 0
    if rowid.rba != 0 or rowid.partition_id != 0 or rowid.block_num != 0 \
            or rowid.slot_num != 0:
        offset = _convert_base64(buf, rowid.rba, 6, offset)
        offset = _convert_base64(buf, rowid.partition_id, 3, offset)
        offset = _convert_base64(buf, rowid.block_num, 6, offset)
        offset = _convert_base64(buf, rowid.slot_num, 3, offset)
        return buf[:TNS_MAX_ROWID_LENGTH].decode()


cdef str _get_connect_data(Description description, str connection_id):
    """
    Return the connect data required by the listener in order to connect.
    """
    constants = _connect_constants
    cid = f"(PROGRAM={constants.sanitized_program_name})" + \
          f"(HOST={constants.sanitized_machine_name})" + \
          f"(USER={constants.sanitized_user_name})"
    if description.connection_id_prefix:
        description.connection_id = description.connection_id_prefix + \
                connection_id
    else:
        description.connection_id = connection_id
    return description.build_connect_string(cid)


def init_thin_impl(package):
    """
    Initializes globals after the package has been completely initialized. This
    is to avoid circular imports and eliminate the need for global lookups.
    """
    global PY_TYPE_DB_OBJECT, PY_TYPE_LOB, PY_TYPE_ASYNC_LOB
    global PY_TYPE_INTERVAL_YM
    PY_TYPE_DB_OBJECT = package.DbObject
    PY_TYPE_LOB = package.LOB
    PY_TYPE_ASYNC_LOB = package.AsyncLOB
    PY_TYPE_INTERVAL_YM = package.IntervalYM
