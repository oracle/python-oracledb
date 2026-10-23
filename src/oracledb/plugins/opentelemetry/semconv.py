# -----------------------------------------------------------------------------
# Copyright (c) 2026, Oracle and/or its affiliates.
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
# -----------------------------------------------------------------------------

"""
OpenTelemetry semantic-convention names used by the plugin.
"""

DB_CLIENT_OPERATION_DURATION = "db.client.operation.duration"
DB_NAMESPACE = "db.namespace"
DB_OPERATION_BATCH_SIZE = "db.operation.batch.size"
DB_OPERATION_NAME = "db.operation.name"
DB_QUERY_TEXT = "db.query.text"
DB_RESPONSE_STATUS_CODE = "db.response.status_code"
DB_SYSTEM_NAME = "db.system.name"
ERROR_TYPE = "error.type"
ORACLE_DB_DOMAIN = "oracle.db.domain"
ORACLE_DB_INSTANCE_NAME = "oracle.db.instance.name"
ORACLE_DB_NAME = "oracle.db.name"
ORACLE_DB_PDB = "oracle.db.pdb"
ORACLE_DB_SERVICE = "oracle.db.service"
ORACLE_DB_SYSTEM_NAME = "oracle.db"
SERVER_ADDRESS = "server.address"
SERVER_PORT = "server.port"


def db_query_parameter(key: str) -> str:
    """
    Return the semantic-convention name for a query parameter.
    """
    return f"db.query.parameter.{key}"
