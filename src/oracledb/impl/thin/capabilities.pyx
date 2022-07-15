#------------------------------------------------------------------------------
# Copyright (c) 2021, 2022, Oracle and/or its affiliates.
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

cdef class Capabilities:
    cdef:
        uint16_t protocol_version
        uint8_t ttc_field_version
        uint16_t charset_id
        uint16_t ncharset_id
        bytearray compile_caps
        bytearray runtime_caps
        bint char_conversion
        bint supports_oob

    def __init__(self):
        self._init_compile_caps()
        self._init_runtime_caps()

    cdef void _adjust_for_protocol(self, uint16_t protocol_version,
                                   uint16_t protocol_options):
        self.protocol_version = protocol_version
        self.supports_oob = protocol_options & TNS_CAN_RECV_ATTENTION

    @cython.boundscheck(False)
    cdef void _adjust_for_server_compile_caps(self, bytearray server_caps):
        if server_caps[TNS_CCAP_FIELD_VERSION] < self.ttc_field_version:
            self.ttc_field_version = server_caps[TNS_CCAP_FIELD_VERSION]
            self.compile_caps[TNS_CCAP_FIELD_VERSION] = self.ttc_field_version

    @cython.boundscheck(False)
    cdef void _adjust_for_server_runtime_caps(self, bytearray server_caps):
        pass

    cdef int _check_ncharset_id(self) except -1:
        """
        Checks that the national character set id is AL16UTF16, which is the
        only id that is currently supported.
        """
        if self.ncharset_id != TNS_CHARSET_UTF16:
            errors._raise_err(errors.ERR_NCHAR_CS_NOT_SUPPORTED,
                              charset_id=self.ncharset_id)

    @cython.boundscheck(False)
    cdef void _init_compile_caps(self):
        self.ttc_field_version = TNS_CCAP_FIELD_VERSION_MAX
        self.compile_caps = bytearray(TNS_CCAP_MAX)
        self.compile_caps[TNS_CCAP_SQL_VERSION] = TNS_CCAP_SQL_VERSION_MAX
        self.compile_caps[TNS_CCAP_LOGON_TYPES] = \
                TNS_CCAP_O5LOGON | TNS_CCAP_O5LOGON_NP | \
                TNS_CCAP_O7LOGON | TNS_CCAP_O8LOGON_LONG_IDENTIFIER
        self.compile_caps[TNS_CCAP_FIELD_VERSION] = self.ttc_field_version
        self.compile_caps[TNS_CCAP_SERVER_DEFINE_CONV] = 1
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
                TNS_CCAP_LOB_ENCS
        self.compile_caps[TNS_CCAP_UB2_DTY] = 1
        self.compile_caps[TNS_CCAP_TTC3] = TNS_CCAP_IMPLICIT_RESULTS | \
                TNS_CCAP_BIG_CHUNK_CLR | TNS_CCAP_KEEP_OUT_ORDER
        self.compile_caps[TNS_CCAP_TTC2] = TNS_CCAP_ZLNP
        self.compile_caps[TNS_CCAP_OCI2] = TNS_CCAP_DRCP
        self.compile_caps[TNS_CCAP_CLIENT_FN] = TNS_CCAP_CLIENT_FN_MAX
        self.compile_caps[TNS_CCAP_TTC4] = TNS_CCAP_INBAND_NOTIFICATION

    @cython.boundscheck(False)
    cdef void _init_runtime_caps(self):
        self.runtime_caps = bytearray(TNS_RCAP_MAX)
        self.runtime_caps[TNS_RCAP_COMPAT] = TNS_RCAP_COMPAT_81
        self.runtime_caps[TNS_RCAP_TTC] = TNS_RCAP_TTC_ZERO_COPY | \
                TNS_RCAP_TTC_32K
