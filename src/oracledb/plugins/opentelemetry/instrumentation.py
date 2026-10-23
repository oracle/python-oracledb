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
Lifecycle management for the embedded OpenTelemetry plugin.
"""

from __future__ import annotations

import weakref
from dataclasses import dataclass
from typing import Callable

from opentelemetry import metrics, trace

import oracledb

from .tracing import (
    CallbackHandler,
    InstrumentationConfig,
    ParamsHook,
    compose_callback,
)


@dataclass
class _ConnectionState:
    handler: CallbackHandler
    operation_callback: Callable
    previous_operation_callback: Callable | None
    previous_round_trip_callback: Callable | None
    round_trip_callback: Callable


_connection_states = weakref.WeakKeyDictionary()
_global_handler = None
_params_hook = None


def _build_handler(
    db_statement_dump: bool,
    enable_database_trace_propagation: bool,
    enhanced_database_reporting: bool,
    meter_provider,
    request_hook: Callable | None,
    require_parent_span: bool,
    response_hook: Callable | None,
    tracer_provider=None,
) -> CallbackHandler:
    config = InstrumentationConfig(
        db_statement_dump=db_statement_dump,
        enable_database_trace_propagation=enable_database_trace_propagation,
        enhanced_database_reporting=enhanced_database_reporting,
        require_parent_span=require_parent_span,
        request_hook=request_hook,
        response_hook=response_hook,
    )
    meter = metrics.get_meter(
        __package__,
        version=oracledb.__version__,
        meter_provider=meter_provider,
    )
    tracer = trace.get_tracer(
        __package__,
        instrumenting_library_version=oracledb.__version__,
        tracer_provider=tracer_provider,
    )
    return CallbackHandler(tracer, config, meter)


def instrument(
    *,
    db_statement_dump: bool = False,
    enable_database_trace_propagation: bool = False,
    enhanced_database_reporting: bool = False,
    meter_provider=None,
    request_hook: Callable | None = None,
    require_parent_span: bool = False,
    response_hook: Callable | None = None,
    tracer_provider=None,
) -> None:
    """
    Instrument connections and pools subsequently created by the driver.
    """
    global _global_handler, _params_hook
    if _global_handler is not None:
        raise RuntimeError(
            "OpenTelemetry instrumentation is already enabled; call "
            "uninstrument() before calling instrument() again"
        )
    _global_handler = _build_handler(
        db_statement_dump=db_statement_dump,
        enable_database_trace_propagation=enable_database_trace_propagation,
        enhanced_database_reporting=enhanced_database_reporting,
        meter_provider=meter_provider,
        request_hook=request_hook,
        require_parent_span=require_parent_span,
        response_hook=response_hook,
        tracer_provider=tracer_provider,
    )
    _params_hook = ParamsHook(_global_handler)
    oracledb.register_params_hook(_params_hook)


def instrument_connection(
    connection: oracledb.Connection | oracledb.AsyncConnection,
    *,
    db_statement_dump: bool = False,
    enable_database_trace_propagation: bool = False,
    enhanced_database_reporting: bool = False,
    meter_provider=None,
    request_hook: Callable | None = None,
    require_parent_span: bool = False,
    response_hook: Callable | None = None,
    tracer_provider=None,
) -> None:
    """
    Instrument an existing connection.
    """
    if connection in _connection_states:
        raise RuntimeError(
            "connection is already instrumented with OpenTelemetry; call "
            "uninstrument_connection() before calling instrument_connection() "
            "again"
        )
    handler = _build_handler(
        db_statement_dump=db_statement_dump,
        enable_database_trace_propagation=enable_database_trace_propagation,
        enhanced_database_reporting=enhanced_database_reporting,
        meter_provider=meter_provider,
        request_hook=request_hook,
        require_parent_span=require_parent_span,
        response_hook=response_hook,
        tracer_provider=tracer_provider,
    )
    previous_operation_callback = connection.operation_callback
    previous_round_trip_callback = connection.round_trip_callback
    operation_callback = compose_callback(
        previous_operation_callback, handler, handler.operation_callback
    )
    round_trip_callback = compose_callback(
        previous_round_trip_callback, handler, handler.round_trip_callback
    )
    connection.operation_callback = operation_callback
    connection.round_trip_callback = round_trip_callback
    _connection_states[connection] = _ConnectionState(
        handler=handler,
        operation_callback=operation_callback,
        previous_operation_callback=previous_operation_callback,
        previous_round_trip_callback=previous_round_trip_callback,
        round_trip_callback=round_trip_callback,
    )


def uninstrument() -> None:
    """
    Disable global instrumentation without changing application callbacks.
    """
    global _global_handler, _params_hook
    if _global_handler is not None:
        _global_handler.disable()
    if _params_hook is not None:
        try:
            oracledb.unregister_params_hook(_params_hook)
        except (AttributeError, ValueError):
            pass
    _global_handler = None
    _params_hook = None


def uninstrument_connection(
    connection: oracledb.Connection | oracledb.AsyncConnection,
) -> None:
    """
    Restore callbacks replaced by :func:`instrument_connection`.
    """
    state = _connection_states.pop(connection, None)
    if state is None:
        return
    try:
        if connection.operation_callback is state.operation_callback:
            connection.operation_callback = state.previous_operation_callback
        if connection.round_trip_callback is state.round_trip_callback:
            connection.round_trip_callback = state.previous_round_trip_callback
    except Exception:
        # Callback properties are unavailable after a connection is closed.
        pass
    finally:
        if state.handler is not _global_handler:
            state.handler.disable()
