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
# tpc_switch.pyx
#
# Cython file defining the messages that are sent to the database and the
# responses that are received by the client for switching two phase commit
# (TPC) transactions (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------


@cython.final
cdef class TransactionSwitchMessage(Message):
    """
    Used for two-phase commit (TPC) transaction start, attach and detach.
    """
    cdef:
        uint32_t operation, flags, timeout, application_value
        bytes context
        object xid

    cdef int _initialize_hook(self) except -1:
        """
        Perform initialization.
        """
        self.function_code = TNS_FUNC_TPC_TXN_SWITCH

    cdef int _process_return_parameters(self, ReadBuffer buf) except -1:
        """
        Process the parameters returned by the database.
        """
        cdef:
            const char_type* ptr
            uint16_t context_len
        buf.read_ub4(&self.application_value)
        buf.read_ub2(&context_len)
        ptr = buf.read_raw_bytes(context_len)
        self.context = ptr[:context_len]

    cdef int _write_message(self, WriteBuffer buf) except -1:
        """
        Writes the message to the database.
        """
        cdef:
            bytes global_transaction_id, branch_qualifier, xid_bytes
            bytes internal_name = None, external_name = None
            uint32_t format_id = 0

        # acquire data to send to the server
        if self.xid is not None:
            format_id = self.xid[0]
            global_transaction_id = self.xid[1] \
                    if isinstance(self.xid[1], bytes) \
                    else self.xid[1].encode()
            branch_qualifier = self.xid[2] \
                    if isinstance(self.xid[2], bytes) \
                    else self.xid[2].encode()
            xid_bytes = global_transaction_id + branch_qualifier
            xid_bytes += bytes(128 - len(xid_bytes))
        if self.conn_impl._internal_name is not None:
            internal_name = self.conn_impl._internal_name.encode()
        if self.conn_impl._external_name is not None:
            external_name = self.conn_impl._external_name.encode()

        # write message
        self._write_function_code(buf)
        buf.write_ub4(self.operation)
        if self.context is not None:
            buf.write_uint8(1)              # pointer (transaction context)
            buf.write_ub4(len(self.context))
        else:
            buf.write_uint8(0)              # pointer (transaction context)
            buf.write_ub4(0)                # transaction context length
        if self.xid is not None:
            buf.write_ub4(format_id)
            buf.write_ub4(len(global_transaction_id))
            buf.write_ub4(len(branch_qualifier))
            buf.write_uint8(1)              # pointer (XID)
            buf.write_ub4(len(xid_bytes))
        else:
            buf.write_ub4(0)                # format id
            buf.write_ub4(0)                # global transaction id length
            buf.write_ub4(0)                # branch qualifier length
            buf.write_uint8(0)              # pointer (XID)
            buf.write_ub4(0)                # XID length
        buf.write_ub4(self.flags)
        buf.write_ub4(self.timeout)
        buf.write_uint8(1)                  # pointer (application value)
        buf.write_uint8(1)                  # pointer (return context)
        buf.write_uint8(1)                  # pointer (return context length)
        if internal_name is not None:
            buf.write_uint8(1)              # pointer (internal name)
            buf.write_ub4(len(internal_name))
        else:
            buf.write_uint8(0)              # pointer (internal name)
            buf.write_ub4(0)                # length of internal name
        if external_name is not None:
            external_name = self.conn_impl._external_name.encode()
            buf.write_uint8(1)              # pointer (external name)
            buf.write_ub4(len(external_name))
        else:
            buf.write_uint8(0)              # pointer (external name)
            buf.write_ub4(0)                # length of external name
        if self.context is not None:
            buf.write_bytes(self.context)
        if self.xid is not None:
            buf.write_bytes(xid_bytes)
        buf.write_ub4(self.application_value)
        if internal_name is not None:
            buf.write_bytes(internal_name)
        if external_name is not None:
            buf.write_bytes(external_name)
