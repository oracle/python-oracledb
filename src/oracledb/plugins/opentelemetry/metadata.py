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
Metadata collection for the optional OpenTelemetry plugin.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

import oracledb

from .semconv import (
    DB_NAMESPACE,
    DB_OPERATION_BATCH_SIZE,
    DB_OPERATION_NAME,
    DB_QUERY_TEXT,
    DB_RESPONSE_STATUS_CODE,
    DB_SYSTEM_NAME,
    ERROR_TYPE,
    ORACLE_DB_DOMAIN,
    ORACLE_DB_INSTANCE_NAME,
    ORACLE_DB_NAME,
    ORACLE_DB_PDB,
    ORACLE_DB_SERVICE,
    ORACLE_DB_SYSTEM_NAME,
    SERVER_ADDRESS,
    SERVER_PORT,
    db_query_parameter,
)

_CONNECT_ATTRIBUTES = (
    ("db_domain", ORACLE_DB_DOMAIN),
    ("db_name", ORACLE_DB_NAME),
    ("db_unique_name", DB_NAMESPACE),
    ("host", SERVER_ADDRESS),
    ("instance_name", ORACLE_DB_INSTANCE_NAME),
    ("pdb_name", ORACLE_DB_PDB),
    ("port", SERVER_PORT),
    ("service_name", ORACLE_DB_SERVICE),
)
_CONNECTION_ATTRIBUTES = (
    ("db_domain", ORACLE_DB_DOMAIN),
    ("db_name", ORACLE_DB_NAME),
    ("instance_name", ORACLE_DB_INSTANCE_NAME),
    ("pdb_name", ORACLE_DB_PDB),
    ("service_name", ORACLE_DB_SERVICE),
)
_CONNECTION_TYPES = (oracledb.AsyncConnection, oracledb.Connection)
_DEFAULT_SERVER_PORT = 1521
_TARGET_PREFIXES = (
    ((oracledb.AsyncCursor, oracledb.Cursor), "cursor"),
    ((oracledb.AsyncLOB, oracledb.LOB), "lob"),
    ((oracledb.AsyncQueue, oracledb.Queue), "queue"),
    ((oracledb.Subscription,), "subscription"),
)
_THIN_ATTRIBUTES = (
    ("db_unique_name", DB_NAMESPACE),
    ("host", SERVER_ADDRESS),
    ("port", SERVER_PORT),
)


@dataclass(frozen=True)
class OperationInfo:
    """
    The normalized metadata for a driver operation.
    """

    attributes: dict[str, Any]
    connection: Any
    name: str
    operation_name: str
    parameters: Any
    refresh_connection_attributes: bool
    span_name: str
    statement: Any


def _bind_attributes(parameters: Any) -> dict[str, str]:
    if isinstance(parameters, dict):
        items = parameters.items()
    elif isinstance(parameters, (list, tuple)):
        items = enumerate(parameters)
    else:
        return {}
    attributes = {}
    for key, value in items:
        if isinstance(value, oracledb.Var):
            value = ""
        try:
            if value is None:
                value = "null"
            elif isinstance(value, (bytes, bytearray, memoryview)):
                value = bytes(value).decode("utf-8", errors="replace")
            elif not isinstance(value, (bool, float, int, str)):
                value = json.dumps(value, default=str)
            else:
                value = str(value)
        except Exception:
            continue
        attributes[db_query_parameter(key)] = value
    return attributes


def _connect_attributes(arguments: Mapping[str, Any]) -> dict[str, Any]:
    attributes = {DB_SYSTEM_NAME: ORACLE_DB_SYSTEM_NAME}
    params = arguments.get("params")
    kwargs = arguments.get("kwargs")
    values = kwargs if isinstance(kwargs, dict) else {}
    for name, attribute_name in _CONNECT_ATTRIBUTES:
        value = values.get(name)
        if value is None and params is not None:
            value = safe_getattr(params, name)
        if value is not None:
            attributes[attribute_name] = value
    _normalize_server_endpoint(attributes)
    return attributes


def _normalize_server_endpoint(attributes: dict[str, Any]) -> None:
    port = _server_port(attributes.get(SERVER_PORT))
    if not attributes.get(SERVER_ADDRESS) or port in (
        None,
        _DEFAULT_SERVER_PORT,
    ):
        attributes.pop(SERVER_PORT, None)
    else:
        attributes[SERVER_PORT] = port


def _operation_batch_size(name: str, parameters: Any) -> int | None:
    if name != "executemany" or isinstance(parameters, bool):
        return None
    if isinstance(parameters, int):
        size = parameters
    else:
        size = safe_getattr(parameters, "num_rows")
        if not isinstance(size, int) or isinstance(size, bool):
            try:
                size = len(parameters)
            except Exception:
                return None
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        return None
    return size if size != 1 else None


def _operation_metadata(name: str, arguments: Mapping[str, Any]):
    statement = arguments.get("statement")
    parameters = arguments.get("parameters")
    if parameters is None and arguments.get("keyword_parameters"):
        parameters = arguments["keyword_parameters"]
    batch_size = _operation_batch_size(name, parameters)
    if name in ("execute", "executemany"):
        operation_name = "EXECUTE"
        if isinstance(statement, str):
            first_word = statement.strip().split(maxsplit=1)
            if first_word:
                candidate = first_word[0].removesuffix(";").upper()
                if candidate.isalpha():
                    operation_name = candidate
        if batch_size is not None:
            operation_name = f"BATCH {operation_name}"
    else:
        operation_name = "FETCH" if name == "fetchone" else name.upper()
    return statement, parameters, operation_name, batch_size


def _server_port(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        port = value
    elif isinstance(value, str):
        try:
            port = int(value)
        except ValueError:
            return None
    else:
        return None
    return port if 0 < port <= 65535 else None


def _span_name(
    arguments: Mapping[str, Any],
    name: str,
    operation_name: str,
    attributes: Mapping[str, Any],
) -> str:
    if name == "connect":
        return "oracledb.connect"
    target = arguments.get("self")
    target_prefix = _target_prefix(target)
    if target_prefix in ("lob", "queue", "subscription"):
        return f"oracledb.{target_prefix}.{name}"
    if target_prefix == "connection" and name in (
        "direct_path_load",
        "run_pipeline",
    ):
        return f"oracledb.connection.{name}"
    if name == "close" and target_prefix in ("connection", "cursor"):
        return f"oracledb.{target_prefix}.close"
    namespace = attributes.get(DB_NAMESPACE)
    if namespace:
        return f"{operation_name} {namespace}"
    address = attributes.get(SERVER_ADDRESS)
    if address:
        port = attributes.get(SERVER_PORT)
        return (
            f"{operation_name} {address}:{port}"
            if port
            else f"{operation_name} {address}"
        )
    return operation_name


def _target_prefix(target: Any) -> str | None:
    if isinstance(target, _CONNECTION_TYPES):
        return "connection"
    for target_types, prefix in _TARGET_PREFIXES:
        if isinstance(target, target_types):
            return prefix
    return None


def connection_attributes(connection: Any) -> dict[str, Any]:
    """
    Return only non-sensitive public connection attributes.
    """
    attributes = {DB_SYSTEM_NAME: ORACLE_DB_SYSTEM_NAME}
    if connection is None:
        return attributes
    for source_name, attribute_name in _CONNECTION_ATTRIBUTES:
        value = safe_getattr(connection, source_name)
        if value is not None:
            attributes[attribute_name] = value
    if safe_getattr(connection, "thin"):
        for source_name, attribute_name in _THIN_ATTRIBUTES:
            value = safe_getattr(connection, source_name)
            if value is not None:
                attributes[attribute_name] = value
        _normalize_server_endpoint(attributes)
    return attributes


def connection_from_arguments(arguments: Mapping[str, Any]) -> Any:
    """
    Find the public connection associated with an operation callback.
    """
    target = arguments.get("self")
    if isinstance(target, _CONNECTION_TYPES):
        return target
    for target_types, _ in _TARGET_PREFIXES:
        if isinstance(target, target_types):
            return safe_getattr(target, "connection")
    return None


def describe_operation(
    name: str,
    arguments: Mapping[str, Any],
    *,
    db_statement_dump: bool,
    enhanced_database_reporting: bool,
) -> OperationInfo:
    """
    Create safe OpenTelemetry metadata from a driver callback.
    """
    connection = connection_from_arguments(arguments)
    statement, parameters, operation_name, batch_size = _operation_metadata(
        name, arguments
    )
    attributes = (
        _connect_attributes(arguments)
        if name == "connect"
        else connection_attributes(connection)
    )
    attributes[DB_OPERATION_NAME] = operation_name
    if batch_size is not None:
        attributes[DB_OPERATION_BATCH_SIZE] = batch_size
    if statement and (
        bool(parameters) or db_statement_dump or enhanced_database_reporting
    ):
        attributes[DB_QUERY_TEXT] = statement
    if enhanced_database_reporting and batch_size is None:
        attributes.update(_bind_attributes(parameters))
    if name == "connect":
        attributes.update(connection_attributes(connection))
    return OperationInfo(
        attributes=attributes,
        connection=connection,
        name=name,
        operation_name=operation_name,
        parameters=parameters,
        refresh_connection_attributes=name == "connect",
        span_name=_span_name(arguments, name, operation_name, attributes),
        statement=statement,
    )


def error_attributes(error: BaseException) -> dict[str, str]:
    """
    Return stable error attributes without exposing error details.
    """
    details = error.args[0] if error.args else None
    code = safe_getattr(error, "code") or safe_getattr(details, "code")
    full_code = safe_getattr(error, "full_code") or safe_getattr(
        details, "full_code"
    )
    attributes = {}
    if isinstance(code, int) and not isinstance(code, bool) and code > 0:
        attributes[DB_RESPONSE_STATUS_CODE] = f"ORA-{code:05d}"
    if full_code:
        attributes[ERROR_TYPE] = str(full_code)
    elif DB_RESPONSE_STATUS_CODE in attributes:
        attributes[ERROR_TYPE] = attributes[DB_RESPONSE_STATUS_CODE]
    else:
        attributes[ERROR_TYPE] = type(error).__name__
    return attributes


def metric_attributes(
    operation: OperationInfo,
    connection: Any,
    error: BaseException | None = None,
) -> dict[str, Any]:
    """
    Return the approved semantic-convention attributes for metrics.
    """
    values = operation.attributes.copy()
    if connection is not None:
        values.update(connection_attributes(connection))
    attribute_names = (
        DB_NAMESPACE,
        DB_OPERATION_BATCH_SIZE,
        DB_OPERATION_NAME,
        DB_SYSTEM_NAME,
        SERVER_ADDRESS,
        SERVER_PORT,
    )
    attributes = {
        name: values[name] for name in attribute_names if name in values
    }
    if error is not None:
        attributes[ERROR_TYPE] = error_attributes(error)[ERROR_TYPE]
    return attributes


def safe_getattr(value: Any, name: str) -> Any:
    """
    Get public driver state without changing application behavior.
    """
    try:
        return getattr(value, name, None)
    except Exception:
        return None
