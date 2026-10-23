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
OpenTelemetry callback handlers used by the embedded plugin.
"""

from __future__ import annotations

import contextvars
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from opentelemetry import context as context_api
from opentelemetry import trace as trace_api
from opentelemetry.context import _SUPPRESS_INSTRUMENTATION_KEY
from opentelemetry.trace import SpanKind, Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import (
    TraceContextTextMapPropagator,
)

import oracledb

from .metadata import (
    connection_attributes,
    describe_operation,
    error_attributes,
    metric_attributes,
    safe_getattr,
)
from .semconv import (
    DB_CLIENT_OPERATION_DURATION,
    DB_SYSTEM_NAME,
    ORACLE_DB_SYSTEM_NAME,
)


def _close_span(span, scope) -> None:
    try:
        scope.__exit__(None, None, None)
    finally:
        span.end()


def _remove_disabled_callbacks(callback):
    if not isinstance(callback, ComposedCallback):
        return callback
    existing = _remove_disabled_callbacks(callback.existing)
    if not callback.handler._enabled:
        return existing
    if existing is callback.existing:
        return callback
    return ComposedCallback(
        existing, callback.handler, callback.handler_callback
    )


@dataclass(frozen=True, slots=True)
class InstrumentationConfig:
    """
    Normalized public instrumentation options.
    """

    db_statement_dump: bool = False
    enable_database_trace_propagation: bool = False
    enhanced_database_reporting: bool = False
    request_hook: Callable | None = None
    require_parent_span: bool = False
    response_hook: Callable | None = None


class ComposedCallback:
    """
    Preserve an application callback while adding an OpenTelemetry layer.
    """

    def __init__(self, existing: Callable | None, handler, handler_callback):
        self.existing = existing
        self.handler = handler
        self.handler_callback = handler_callback

    def __call__(self, *args):
        existing_completion = None
        if self.existing is not None:
            existing_completion = self.existing(*args)
            if existing_completion is not None and not callable(
                existing_completion
            ):
                # The driver validates callback returns and must retain its
                # standard error rather than an instrumentation-specific one.
                return existing_completion
        opentelemetry_completion = self.handler_callback(*args)
        if opentelemetry_completion is None:
            return existing_completion
        if existing_completion is None:
            return opentelemetry_completion

        def complete(value):
            try:
                opentelemetry_completion(value)
            finally:
                existing_completion(value)

        return complete


def compose_callback(existing: Callable | None, handler, handler_callback):
    """
    Compose once per handler, discarding disabled plugin layers.
    """
    existing = _remove_disabled_callbacks(existing)
    if (
        isinstance(existing, ComposedCallback)
        and existing.handler is handler
        and existing.handler_callback == handler_callback
    ):
        return existing
    return ComposedCallback(existing, handler, handler_callback)


class TracePropagation:
    """
    Propagate Thin round-trip trace context to supported databases.
    """

    def __init__(self):
        self._active_connection = contextvars.ContextVar(
            "oracledb_opentelemetry_active_connection", default=None
        )
        self._propagator = TraceContextTextMapPropagator()

    def activate(self, span, round_trip_name: str):
        if round_trip_name == "end_request":
            return None
        connection = self._active_connection.get()
        if connection is None or not safe_getattr(
            connection, "supports_opentelemetry_tracing"
        ):
            return None
        carrier = {}
        self._propagator.inject(
            carrier, context=trace_api.set_span_in_context(span)
        )
        traceparent = carrier.get("traceparent")
        if not traceparent:
            return None
        connection.set_opentelemetry_trace_context(
            traceparent, carrier.get("tracestate", "")
        )
        return connection

    def bind_connection(self, connection):
        if isinstance(
            connection, (oracledb.AsyncConnection, oracledb.Connection)
        ):
            return self._active_connection.set(connection)
        return None

    def deactivate(self, connection) -> None:
        if connection is not None:
            connection.set_opentelemetry_trace_context(None)

    def reset_connection(self, token) -> None:
        if token is not None:
            self._active_connection.reset(token)


class CallbackHandler:
    """
    Create OpenTelemetry spans from the driver's callback interfaces.
    """

    def __init__(self, tracer, config: InstrumentationConfig, meter=None):
        self._config = config
        self._enabled = True
        self._operation_duration = (
            meter.create_histogram(
                DB_CLIENT_OPERATION_DURATION,
                description="Duration of database client operations.",
                unit="s",
            )
            if meter is not None
            else None
        )
        self._propagation = TracePropagation()
        self._tracer = tracer

    def _apply_error(self, span, error: BaseException) -> None:
        span.record_exception(error)
        span.set_status(Status(StatusCode.ERROR, str(error)))
        for key, value in error_attributes(error).items():
            span.set_attribute(key, value)

    def _finish_operation(
        self, operation, scope, span, start_time: float, value
    ) -> None:
        try:
            result_connection = (
                value
                if isinstance(
                    value, (oracledb.AsyncConnection, oracledb.Connection)
                )
                else operation.connection
            )
            if operation.refresh_connection_attributes:
                for key, attribute_value in connection_attributes(
                    result_connection
                ).items():
                    span.set_attribute(key, attribute_value)
            if isinstance(value, BaseException):
                self._apply_error(span, value)
            self._run_hook(
                self._config.response_hook,
                span,
                {
                    "connection": result_connection,
                    "data": (
                        None if isinstance(value, BaseException) else value
                    ),
                    "error": (
                        value if isinstance(value, BaseException) else None
                    ),
                    "name": operation.name,
                    "operation": operation.operation_name,
                },
            )
            if self._operation_duration is not None:
                error = value if isinstance(value, BaseException) else None
                self._operation_duration.record(
                    time.perf_counter() - start_time,
                    metric_attributes(operation, result_connection, error),
                )
        finally:
            _close_span(span, scope)

    def _run_hook(self, hook, span, payload) -> None:
        if not callable(hook):
            return
        try:
            hook(span, payload)
        except Exception as e:
            span.record_exception(e)

    def _should_skip(self) -> bool:
        if not self._enabled or context_api.get_value(
            _SUPPRESS_INSTRUMENTATION_KEY
        ):
            return True
        return self._config.require_parent_span and not (
            trace_api.get_current_span().get_span_context().is_valid
        )

    def disable(self) -> None:
        self._enabled = False

    def operation_callback(self, name: str, arguments: Mapping[str, Any]):
        """
        Start a logical operation span and return its completion callback.
        """
        try:
            if self._should_skip():
                return None
            operation = describe_operation(
                name,
                arguments,
                db_statement_dump=self._config.db_statement_dump,
                enhanced_database_reporting=(
                    self._config.enhanced_database_reporting
                ),
            )
            start_time = time.perf_counter()
            span = self._tracer.start_span(
                operation.span_name,
                kind=SpanKind.CLIENT,
                attributes=operation.attributes,
            )
            scope = trace_api.use_span(span, end_on_exit=False)
            scope.__enter__()
            self._run_hook(
                self._config.request_hook,
                span,
                {
                    "connection": operation.connection,
                    "name": operation.name,
                    "operation": operation.operation_name,
                    "parameters": operation.parameters,
                    "statement": operation.statement,
                },
            )
            token = None
            if self._config.enable_database_trace_propagation:
                token = self._propagation.bind_connection(operation.connection)
            return _OperationSession(
                self, operation, scope, span, start_time, token
            ).finish
        except Exception as e:
            span.record_exception(e)
            return None

    def round_trip_callback(self, name: str):
        """
        Start a Thin round-trip child span and return its completion.
        """
        try:
            if self._should_skip():
                return None
            span = self._tracer.start_span(
                f"oracledb.{name}",
                kind=SpanKind.CLIENT,
                attributes={DB_SYSTEM_NAME: ORACLE_DB_SYSTEM_NAME},
            )
            scope = trace_api.use_span(span, end_on_exit=False)
            scope.__enter__()
            connection = None
            if self._config.enable_database_trace_propagation:
                connection = self._propagation.activate(span, name)
            return _RoundTripSession(self, scope, span, connection).finish
        except Exception as e:
            span.record_exception(e)


class ParamsHook:
    """
    Install composed callbacks on newly processed driver parameters.
    """

    def __init__(self, handler: CallbackHandler):
        self.handler = handler

    def __call__(self, params) -> None:
        params.set(
            operation_callback=compose_callback(
                params.operation_callback,
                self.handler,
                self.handler.operation_callback,
            ),
            round_trip_callback=compose_callback(
                params.round_trip_callback,
                self.handler,
                self.handler.round_trip_callback,
            ),
        )


class _OperationSession:
    def __init__(self, handler, operation, scope, span, start_time, token):
        self._finished = False
        self._handler = handler
        self._operation = operation
        self._scope = scope
        self._span = span
        self._start_time = start_time
        self._token = token

    def finish(self, value: Any) -> None:
        if self._finished:
            return
        self._finished = True
        try:
            self._handler._finish_operation(
                self._operation,
                self._scope,
                self._span,
                self._start_time,
                value,
            )
        except Exception as e:
            self._span.record_exception(e)
        finally:
            self._handler._propagation.reset_connection(self._token)


class _RoundTripSession:
    def __init__(self, handler, scope, span, traced_connection):
        self._finished = False
        self._handler = handler
        self._scope = scope
        self._span = span
        self._traced_connection = traced_connection

    def finish(self, error: Any) -> None:
        if self._finished:
            return
        self._finished = True
        try:
            if isinstance(error, BaseException):
                self._handler._apply_error(self._span, error)
        finally:
            try:
                self._handler._propagation.deactivate(self._traced_connection)
            except Exception as e:
                self._span.record_exception(e)
            finally:
                _close_span(self._span, self._scope)
