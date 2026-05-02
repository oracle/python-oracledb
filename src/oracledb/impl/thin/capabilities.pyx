#------------------------------------------------------------------------------
# Copyright (c) 2021, 2026, Oracle and/or its affiliates.
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
# capabilities.pyx
#
# Cython file defining the capabilities (neogiated at connect time) that both
# the database server and the client are capable of (embedded in
# thin_impl.pyx).
#------------------------------------------------------------------------------

# defines the mapping between Oracle Database character set and IANA encoding
# names used by Python
cdef dict ORACLE_CHARSET_TO_PYTHON_ENCODING = {
    # ASCII
    1: "ascii",                         # US7ASCII

    # ISO 8859 series
    31: "iso_8859_1",                   # WE8ISO8859P1
    32: "iso_8859_2",                   # EE8ISO8859P2
    33: "iso_8859_3",                   # SE8ISO8859P3
    34: "iso_8859_4",                   # NEE8ISO8859P4
    35: "iso_8859_5",                   # CL8ISO8859P5
    36: "iso_8859_6",                   # AR8ISO8859P6
    37: "iso_8859_7",                   # EL8ISO8859P7
    38: "iso_8859_8",                   # IW8ISO8859P8
    39: "iso_8859_9",                   # WE8ISO8859P9
    40: "iso_8859_10",                  # NE8ISO8859P10
    41: "tis_620",                      # TH8TISASCII
    46: "iso_8859_15",                  # WE8ISO8859P15
    47: "iso_8859_13",                  # BLT8ISO8859P13

    # Windows code pages
    170: "cp1250",                      # EE8MSWIN1250
    171: "cp1251",                      # CL8MSWIN1251
    172: "cp1253",                      # EL8MSWIN1253
    173: "cp1254",                      # TR8MSWIN1254
    174: "cp1255",                      # IW8MSWIN1255
    175: "cp1256",                      # AR8MSWIN1256
    176: "cp1257",                      # BLT8MSWIN1257
    177: "cp1258",                      # VN8MSWIN1258
    178: "cp1252",                      # WE8MSWIN1252

    # DOS / PC code pages
    351: "cp850",                       # WE8PC850
    354: "cp437",                       # US8PC437
    368: "cp866",                       # RU8PC866
    382: "cp852",                       # EE8PC852

    # East Asian multi-byte
    829: "big5",                        # ZHT16BIG5
    830: "euc_kr",                      # KO16KSC5601
    831: "euc_jp",                      # JA16EUC
    832: "cp932",                       # JA16SJIS
    833: "cp932",                       # JA16SJISTILDE
    834: "euc_jp",                      # JA16EUCTILDE
    846: "gbk",                         # ZHS16GBK
    850: "big5hkscs",                   # ZHT16HKSCS
    852: "euc_kr",                      # KO16MSWIN949
    854: "big5",                        # ZHT16MSWIN950
    870: "gb18030",                     # ZHS32GB18030

    # universal encodings
    873: "utf_8",                       # AL32UTF8
    2000: "utf_16_be",                  # AL16UTF16
}

cdef class Capabilities:
    cdef:
        uint16_t protocol_version
        uint8_t ttc_field_version
        uint16_t charset_id
        const char* encoding
        uint16_t ncharset_id
        const char* nencoding
        bytearray compile_caps
        bytearray runtime_caps
        uint32_t max_string_size
        bint supports_fast_auth
        bint supports_oob
        bint supports_oob_check
        bint supports_end_of_response
        bint supports_end_user_security_context
        bint supports_pipelining
        bint supports_request_boundaries
        uint32_t sdu

    def __init__(self):
        self._init_compile_caps()
        self._init_runtime_caps()
        self.sdu = 8192                 # initial value to use

    cdef void _adjust_for_protocol(self, uint16_t protocol_version,
                                   uint16_t protocol_options, uint32_t flags):
        """
        Adjust the capabilities of the protocol based on the server's response
        to the initial connection request.
        """
        self.protocol_version = protocol_version
        self.supports_oob = protocol_options & TNS_GSO_CAN_RECV_ATTENTION
        if flags & TNS_ACCEPT_FLAG_FAST_AUTH:
            self.supports_fast_auth = True
        if flags & TNS_ACCEPT_FLAG_CHECK_OOB:
            self.supports_oob_check = True
        if protocol_version >= TNS_VERSION_MIN_END_OF_RESPONSE:
            if flags & TNS_ACCEPT_FLAG_HAS_END_OF_RESPONSE:
                self.compile_caps[TNS_CCAP_TTC4] |= TNS_CCAP_END_OF_RESPONSE
                self.supports_end_of_response = True
                self.supports_pipelining = True

    @cython.boundscheck(False)
    cdef void _adjust_for_server_compile_caps(self, bytearray server_caps):
        if server_caps[TNS_CCAP_FIELD_VERSION] < self.ttc_field_version:
            self.ttc_field_version = server_caps[TNS_CCAP_FIELD_VERSION]
            self.compile_caps[TNS_CCAP_FIELD_VERSION] = self.ttc_field_version
        if server_caps[TNS_CCAP_TTC4] & TNS_CCAP_EXPLICIT_BOUNDARY:
            self.supports_request_boundaries = True
        if len(server_caps) > TNS_CCAP_FEATURE_BACKPORT2 \
                and (server_caps[TNS_CCAP_FEATURE_BACKPORT2] \
                    & TNS_CCAP_END_USER_SEC_CTX_PIGGYBACK):
            self.supports_end_user_security_context = True

    @cython.boundscheck(False)
    cdef void _adjust_for_server_runtime_caps(self, bytearray server_caps):
        if server_caps[TNS_RCAP_TTC] & TNS_RCAP_TTC_32K:
            self.max_string_size = 32767
        else:
            self.max_string_size = 4000
        if not (server_caps[TNS_RCAP_TTC] & TNS_RCAP_TTC_SESSION_STATE_OPS):
            self.supports_request_boundaries = False

    cdef const char* _get_encoding(self) except NULL:
        """
        Returns the encoding to use for encoding or decoding data that is
        stored in the database character set. If no encoding is found, an
        exception is raised. This is only required for direct path load and for
        strings found within Oracle database objects.
        """
        cdef str encoding
        if self.encoding != NULL:
            return self.encoding
        encoding = ORACLE_CHARSET_TO_PYTHON_ENCODING.get(self.charset_id)
        if encoding is None:
            errors._raise_err(errors.ERR_DB_CS_NOT_SUPPORTED,
                              charset_id=self.charset_id)
        return encoding.encode()

    cdef const char* _get_nencoding(self) except NULL:
        """
        Returns the encoding to use for encoding or decoding data that is
        stored in the database national character set. If no encoding is found,
        an exception is raised. This is required for handling NCHAR data.
        """
        cdef str encoding
        if self.nencoding != NULL:
            return self.nencoding
        encoding = ORACLE_CHARSET_TO_PYTHON_ENCODING.get(self.ncharset_id)
        if encoding is None:
            errors._raise_err(errors.ERR_NCHAR_CS_NOT_SUPPORTED,
                              charset_id=self.ncharset_id)
        return encoding.encode()

    @cython.boundscheck(False)
    cdef void _init_compile_caps(self):
        self.ttc_field_version = TNS_CCAP_FIELD_VERSION_MAX
        self.compile_caps = bytearray(TNS_CCAP_MAX)
        self.compile_caps[TNS_CCAP_SQL_VERSION] = TNS_CCAP_SQL_VERSION_MAX
        self.compile_caps[TNS_CCAP_LOGON_TYPES] = \
                TNS_CCAP_O5LOGON | TNS_CCAP_O5LOGON_NP | \
                TNS_CCAP_O7LOGON | TNS_CCAP_O8LOGON_LONG_IDENTIFIER | \
                TNS_CCAP_O9LOGON_LONG_PASSWORD
        self.compile_caps[TNS_CCAP_FEATURE_BACKPORT] = \
                TNS_CCAP_CTB_IMPLICIT_POOL | \
                TNS_CCAP_CTB_OAUTH_MSG_ON_ERR
        self.compile_caps[TNS_CCAP_FIELD_VERSION] = self.ttc_field_version
        self.compile_caps[TNS_CCAP_SERVER_DEFINE_CONV] = 1
        self.compile_caps[TNS_CCAP_DEQUEUE_WITH_SELECTOR] = 1
        self.compile_caps[TNS_CCAP_TTC1] = \
                TNS_CCAP_FAST_BVEC | TNS_CCAP_END_OF_CALL_STATUS | \
                TNS_CCAP_IND_RCD
        self.compile_caps[TNS_CCAP_OCI1] = \
                TNS_CCAP_FAST_SESSION_PROPAGATE | TNS_CCAP_APP_CTX_PIGGYBACK
        self.compile_caps[TNS_CCAP_TDS_VERSION] = TNS_CCAP_TDS_VERSION_MAX
        self.compile_caps[TNS_CCAP_RPC_VERSION] = TNS_CCAP_RPC_VERSION_MAX
        self.compile_caps[TNS_CCAP_RPC_SIG] = TNS_CCAP_RPC_SIG_VALUE
        self.compile_caps[TNS_CCAP_DBF_VERSION] = TNS_CCAP_DBF_VERSION_MAX
        self.compile_caps[TNS_CCAP_LOB] = TNS_CCAP_LOB_UB8_SIZE | \
                TNS_CCAP_LOB_ENCS | TNS_CCAP_LOB_PREFETCH_LENGTH | \
                TNS_CCAP_LOB_TEMP_SIZE | TNS_CCAP_LOB_12C | \
                TNS_CCAP_LOB_PREFETCH_DATA
        self.compile_caps[TNS_CCAP_UB2_DTY] = 1
        self.compile_caps[TNS_CCAP_LOB2] = TNS_CCAP_LOB2_QUASI | \
                TNS_CCAP_LOB2_2GB_PREFETCH
        self.compile_caps[TNS_CCAP_TTC3] = TNS_CCAP_IMPLICIT_RESULTS | \
                TNS_CCAP_BIG_CHUNK_CLR | TNS_CCAP_KEEP_OUT_ORDER | \
                TNS_CCAP_LTXID
        self.compile_caps[TNS_CCAP_TTC2] = TNS_CCAP_ZLNP
        self.compile_caps[TNS_CCAP_OCI2] = TNS_CCAP_DRCP
        self.compile_caps[TNS_CCAP_CLIENT_FN] = TNS_CCAP_CLIENT_FN_MAX
        self.compile_caps[TNS_CCAP_SESS_SIGNATURE_VERSION] = \
                TNS_CCAP_FIELD_VERSION_12_2
        self.compile_caps[TNS_CCAP_TTC4] = TNS_CCAP_INBAND_NOTIFICATION | \
                TNS_CCAP_EXPLICIT_BOUNDARY
        self.compile_caps[TNS_CCAP_TTC5] = TNS_CCAP_VECTOR_SUPPORT | \
                TNS_CCAP_TOKEN_SUPPORTED | TNS_CCAP_PIPELINING_SUPPORT | \
                TNS_CCAP_PIPELINING_BREAK | TNS_CCAP_TTC5_SESSIONLESS_TXNS
        self.compile_caps[TNS_CCAP_VECTOR_FEATURES] = \
                TNS_CCAP_VECTOR_FEATURE_BINARY | \
                TNS_CCAP_VECTOR_FEATURE_SPARSE
        self.compile_caps[TNS_CCAP_OCI3] = TNS_CCAP_OCI3_OCSSYNC
        self.compile_caps[TNS_CCAP_FEATURE_BACKPORT2] = \
                TNS_CCAP_END_USER_SEC_CTX_PIGGYBACK

    @cython.boundscheck(False)
    cdef void _init_runtime_caps(self):
        self.runtime_caps = bytearray(TNS_RCAP_MAX)
        self.runtime_caps[TNS_RCAP_COMPAT] = TNS_RCAP_COMPAT_81
        self.runtime_caps[TNS_RCAP_TTC] = TNS_RCAP_TTC_ZERO_COPY | \
                TNS_RCAP_TTC_32K
