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
# utils.pyx
#
# Cython file defining utility classes and methods (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

class OutOfPackets(Exception):
    pass

class MarkerDetected(Exception):
    pass

class ConnectConstants:

    def __init__(self):
        self.pid = str(os.getpid())
        pattern = r"(?P<major_num>\d+)\.(?P<minor_num>\d+)\.(?P<patch_num>\d+)"
        match_dict = re.match(pattern, DRIVER_VERSION)
        major_num = int(match_dict["major_num"])
        minor_num = int(match_dict["minor_num"])
        patch_num = int(match_dict["patch_num"])
        self.full_version_num = \
                major_num << 24 | minor_num << 20 | patch_num << 12


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


cdef str _get_connect_data(Description description, str connection_id, ConnectParamsImpl params):
    """
    Return the connect data required by the listener in order to connect.
    """
    cid = f"(PROGRAM={params.program})" + \
          f"(HOST={params.machine})" + \
          f"(USER={params.osuser})"
    if description.connection_id_prefix:
        description.connection_id = description.connection_id_prefix + \
                connection_id
    else:
        description.connection_id = connection_id
    return description.build_connect_string(cid)


cdef int _check_cryptography() except -1:
    """
    Checks to see that the cryptography package was imported successfully.
    """
    if CRYPTOGRAPHY_IMPORT_ERROR is not None:
        errors._raise_err(errors.ERR_NO_CRYPTOGRAPHY_PACKAGE,
                          str(CRYPTOGRAPHY_IMPORT_ERROR))

# Mapping of Oracle character set IDs to Python encoding names. Used by
# direct path loading to encode character data in the database character set.
# For normal SQL execution the server performs the conversion, but for direct
# path loading the data is written directly to disk.
cdef dict ORACLE_CHARSET_TO_PYTHON_ENCODING = {

    # ASCII
    1: "ascii",              # US7ASCII

    # ISO 8859 series
    31: "iso-8859-1",        # WE8ISO8859P1
    32: "iso-8859-2",        # EE8ISO8859P2
    33: "iso-8859-3",        # SE8ISO8859P3
    34: "iso-8859-4",        # NEE8ISO8859P4
    35: "iso-8859-5",        # CL8ISO8859P5
    36: "iso-8859-6",        # AR8ISO8859P6
    37: "iso-8859-7",        # EL8ISO8859P7
    38: "iso-8859-8",        # IW8ISO8859P8
    39: "iso-8859-9",        # WE8ISO8859P9
    40: "iso-8859-10",       # NE8ISO8859P10
    41: "tis-620",           # TH8TISASCII
    46: "iso-8859-15",       # WE8ISO8859P15
    47: "iso-8859-13",       # BLT8ISO8859P13

    # Windows code pages
    170: "cp1250",           # EE8MSWIN1250
    171: "cp1251",           # CL8MSWIN1251
    172: "cp1253",           # EL8MSWIN1253
    173: "cp1254",           # TR8MSWIN1254
    174: "cp1255",           # IW8MSWIN1255
    175: "cp1256",           # AR8MSWIN1256
    176: "cp1257",           # BLT8MSWIN1257
    177: "cp1258",           # VN8MSWIN1258
    178: "cp1252",           # WE8MSWIN1252

    # DOS / PC code pages
    351: "cp850",            # WE8PC850
    354: "cp437",            # US8PC437
    368: "cp866",            # RU8PC866
    382: "cp852",            # EE8PC852

    # East Asian multi-byte
    829: "big5",             # ZHT16BIG5
    830: "euc_kr",           # KO16KSC5601
    831: "euc_jp",           # JA16EUC
    832: "cp932",            # JA16SJIS
    833: "cp932",            # JA16SJISTILDE
    834: "euc_jp",           # JA16EUCTILDE
    846: "gbk",              # ZHS16GBK
    850: "big5hkscs",        # ZHT16HKSCS
    852: "euc_kr",           # KO16MSWIN949
    854: "big5",             # ZHT16MSWIN950
    870: "gb18030",          # ZHS32GB18030

    # Unicode
    871: "utf-8",            # UTF8 (CESU-8)
    873: "utf-8",            # AL32UTF8
    2000: "utf-16-be",       # AL16UTF16
}


# Single-byte Oracle character set IDs. Oracle stores CLOB data as
# AL16UTF16 for multi-byte database character sets but in the database
# character set for single-byte character sets. This distinction matters
# for direct path loading which writes data directly to disk.
cdef set SINGLE_BYTE_CHARSET_IDS = {
    1,                                              # US7ASCII
    31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41,    # ISO 8859 series
    46, 47,                                         # ISO 8859 series (contd)
    170, 171, 172, 173, 174, 175, 176, 177, 178,    # Windows code pages
    351, 354, 368, 382,                             # DOS / PC code pages
}


cdef bint _is_single_byte_charset(uint16_t charset_id):
    """
    Returns True if the given Oracle character set ID is a single-byte
    character set.
    """
    return charset_id in SINGLE_BYTE_CHARSET_IDS


cdef str _get_db_charset_encoding(uint16_t charset_id):
    """
    Returns the Python encoding name for the given Oracle character set ID,
    or None if the character set is UTF-8 (no conversion needed).
    """
    cdef str encoding
    if charset_id == TNS_CHARSET_UTF8:
        return None
    encoding = ORACLE_CHARSET_TO_PYTHON_ENCODING.get(charset_id)
    if encoding is None:
        errors._raise_err(errors.ERR_DB_CS_NOT_SUPPORTED,
                          charset_id=charset_id)
    if encoding == "utf-8":
        return None
    return encoding


def init_thin_impl(package):
    """
    Initializes globals after the package has been completely initialized. This
    is to avoid circular imports and eliminate the need for global lookups.
    """
    global _connect_constants, errors, exceptions
    _connect_constants = ConnectConstants()
    errors = package.errors
    exceptions = package.exceptions
