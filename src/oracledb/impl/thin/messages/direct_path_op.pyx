#------------------------------------------------------------------------------
# Copyright (c) 2025, Oracle and/or its affiliates.
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
# direct_path_op.pyx
#
# Cython file defining the messages that are sent to the database and the
# responses that are received by the client for sending direct path operations
# to the database (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

@cython.final
cdef class DirectPathOpMessage(Message):
    cdef:
        uint16_t cursor_id
        uint32_t op_code

    cdef int _initialize_hook(self) except -1:
        """
        Perform initialization.
        """
        self.function_code = TNS_FUNC_DIRECT_PATH_OP

    cdef int _process_return_parameters(self, ReadBuffer buf) except -1:
        """
        Process the return parameters sent by the database.
        """
        cdef uint16_t num_out_values, i
        buf.read_ub2(&num_out_values)
        for i in range(num_out_values):
            buf.skip_ub4()

    cdef int _write_message(self, WriteBuffer buf) except -1:
        """
        Writes the message to the database.
        """
        self._write_function_code(buf)
        buf.write_ub4(self.op_code)
        buf.write_ub2(self.cursor_id)
        buf.write_uint8(0)                  # pointer (input values)
        buf.write_ub4(0)                    # number of input values
        buf.write_uint8(1)                  # pointer (output values)
        buf.write_uint8(1)                  # pointer (output values length)

    cdef int prepare(self, uint16_t cursor_id, uint32_t op_code) except -1:
        """
        Prepares the values for writing to the message.
        """
        self.cursor_id = cursor_id
        self.op_code = op_code
