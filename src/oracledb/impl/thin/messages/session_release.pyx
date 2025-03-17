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
# session_release.pyx
#
# Cython file defining the messages that are sent to the database and the
# responses that are received by the client for releasing a session (embedded
# in thin_impl.pyx).
#------------------------------------------------------------------------------

@cython.final
cdef class SessionReleaseMessage(Message):

    cdef:
        uint32_t release_mode

    cdef int _initialize_hook(self) except -1:
        """
        Perform initialization.
        """
        self.message_type = TNS_MSG_TYPE_ONEWAY_FN
        self.function_code = TNS_FUNC_SESSION_RELEASE

    cdef int _write_message(self, WriteBuffer buf) except -1:
        """
        Write the message for a DRCP session release.
        """
        self._write_function_code(buf)
        buf.write_uint8(0)                  # pointer (tag name)
        buf.write_uint8(0)                  # tag name length
        buf.write_ub4(self.release_mode)    # mode
