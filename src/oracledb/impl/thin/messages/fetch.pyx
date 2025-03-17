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
# fetch.pyx
#
# Cython file defining the messages that are sent to the database and the
# responses that are received by the client for fetching data (embedded in
# thin_impl.pyx).
#------------------------------------------------------------------------------

@cython.final
cdef class FetchMessage(MessageWithData):

    cdef int _initialize_hook(self) except -1:
        """
        Perform initialization.
        """
        self.function_code = TNS_FUNC_FETCH

    cdef int _write_message(self, WriteBuffer buf) except -1:
        self.cursor_impl._set_fetch_array_size(self.cursor_impl.arraysize)
        self._write_function_code(buf)
        if self.cursor_impl._statement._cursor_id == 0:
            errors._raise_err(errors.ERR_CURSOR_HAS_BEEN_CLOSED)
        buf.write_ub4(self.cursor_impl._statement._cursor_id)
        buf.write_ub4(self.cursor_impl._fetch_array_size)
