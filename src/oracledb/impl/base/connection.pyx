#------------------------------------------------------------------------------
# Copyright (c) 2020, 2022, Oracle and/or its affiliates.
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
# connection.pyx
#
# Cython file defining the base Connection implementation class (embedded in
# base_impl.pyx).
#------------------------------------------------------------------------------

cdef class BaseConnImpl:

    def __init__(self, str dsn, ConnectParamsImpl params):
        self.dsn = dsn
        self.username = params.user

    @utils.CheckImpls("getting a connection OCI attribute")
    def _get_oci_attr(self, uint32_t handle_type, uint32_t attr_num,
                      uint32_t attr_type):
        pass

    @utils.CheckImpls("setting a connection OCI attribute")
    def _set_oci_attr(self, uint32_t handle_type, uint32_t attr_num,
                      uint32_t attr_type, object value):
        pass

    @utils.CheckImpls("aborting a currently executing statement")
    def cancel(self):
        pass

    @utils.CheckImpls("changing a password")
    def change_password(self, old_password, new_password):
        pass

    @utils.CheckImpls("checking if the connection is healthy")
    def get_is_healthy(self):
        pass

    @utils.CheckImpls("closing a connection")
    def close(self, in_del=False):
        pass

    @utils.CheckImpls("committing a transaction")
    def commit(self):
        pass

    @utils.CheckImpls("creating a cursor")
    def create_cursor_impl(self):
        pass

    @utils.CheckImpls("creating a queue")
    def create_queue_impl(self):
        pass

    @utils.CheckImpls("creating a SODA database object")
    def create_soda_database_impl(self, conn):
        pass

    @utils.CheckImpls("creating a subscription")
    def create_subscr_impl(self, object conn, object callback,
                           uint32_t namespace, str name, uint32_t protocol,
                           str ip_address, uint32_t port, uint32_t timeout,
                           uint32_t operations, uint32_t qos,
                           uint8_t grouping_class, uint32_t grouping_value,
                           uint8_t grouping_type, bint client_initiated):
        pass

    @utils.CheckImpls("creating a temporary LOB")
    def create_temp_lob_impl(self, DbType dbtype):
        pass

    @utils.CheckImpls("getting the call timeout")
    def get_call_timeout(self):
        pass

    @utils.CheckImpls("getting the current schema")
    def get_current_schema(self):
        pass

    @utils.CheckImpls("getting the edition")
    def get_edition(self):
        pass

    @utils.CheckImpls("getting the external name")
    def get_external_name(self):
        pass

    @utils.CheckImpls("getting the OCI service context handle")
    def get_handle(self):
        pass

    @utils.CheckImpls("getting the internal name")
    def get_internal_name(self):
        pass

    @utils.CheckImpls("getting the logical transaction id")
    def get_ltxid(self):
        pass

    @utils.CheckImpls("getting the statement cache size")
    def get_stmt_cache_size(self):
        pass

    @utils.CheckImpls("getting an object type")
    def get_type(self, str name):
        pass

    @utils.CheckImpls("getting the database version")
    def get_version(self):
        pass

    @utils.CheckImpls("pinging the database")
    def ping(self):
        pass

    @utils.CheckImpls("rolling back a transaction")
    def rollback(self):
        pass

    @utils.CheckImpls("setting the action")
    def set_action(self, value):
        pass

    @utils.CheckImpls("setting the call timeout")
    def set_call_timeout(self, value):
        pass

    @utils.CheckImpls("setting the client identifier")
    def set_client_identifier(self, value):
        pass

    @utils.CheckImpls("setting the client info")
    def set_client_info(self, value):
        pass

    @utils.CheckImpls("setting the current schema")
    def set_current_schema(self, value):
        pass

    @utils.CheckImpls("setting the database operation")
    def set_dbop(self, value):
        pass

    @utils.CheckImpls("setting the execution context id")
    def set_econtext_id(self, value):
        pass

    @utils.CheckImpls("setting the external name")
    def set_external_name(self, value):
        pass

    @utils.CheckImpls("setting the internal name")
    def set_internal_name(self, value):
        pass

    @utils.CheckImpls("setting the module")
    def set_module(self, value):
        pass

    @utils.CheckImpls("setting the statement cache size")
    def set_stmt_cache_size(self, value):
        pass

    @utils.CheckImpls("shutting down the database")
    def shutdown(self, uint32_t mode):
        pass

    @utils.CheckImpls("starting up the database")
    def startup(self, bint force, bint restrict, str pfile):
        pass

    @utils.CheckImpls("starting a TPC (two-phase commit) transaction")
    def tpc_begin(self, xid, uint32_t flags, uint32_t timeout):
        pass

    @utils.CheckImpls("committing a TPC (two-phase commit) transaction")
    def tpc_commit(self, xid, bint one_phase):
        pass

    @utils.CheckImpls("ending a TPC (two-phase commit) transaction")
    def tpc_end(self, xid, uint32_t flags):
        pass

    @utils.CheckImpls("forgetting a TPC (two-phase commit) transaction")
    def tpc_forget(self, xid):
        pass

    @utils.CheckImpls("preparing a TPC (two-phase commit) transaction")
    def tpc_prepare(self, xid):
        pass

    @utils.CheckImpls("rolling back a TPC (two-phase commit) transaction")
    def tpc_rollback(self, xid):
        pass
