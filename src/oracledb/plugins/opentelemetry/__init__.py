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
Embedded, opt-in OpenTelemetry instrumentation for python-oracledb.

Install the optional ``opentelemetry`` dependency group before importing this
plugin.
"""

from __future__ import annotations

from typing import Callable

import oracledb

from . import instrumentation


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
    Instruments subsequently created Oracle Database connections and pools.

    The ``db_statement_dump`` parameter determines whether SQL statement text
    is included in database spans. It defaults to *False*.

    The ``enable_database_trace_propagation`` parameter enables database-side
    tracing for supported Thin mode round trips and propagates the active
    OpenTelemetry trace context so database spans can be linked to application
    spans. This requires Oracle AI Database 26ai (version 23.26.2 or later) to
    advertise OpenTelemetry tracing support. Oracle Database OpenTelemetry
    must also be configured on the server. It defaults to *False*.

    The ``enhanced_database_reporting`` parameter determines whether additional
    database details, including bind values, are included in database spans. It
    defaults to *False*. Enable it only when this information is safe for the
    telemetry destination.

    The ``meter_provider`` parameter specifies the OpenTelemetry MeterProvider
    used to create metrics. If not specified, the global OpenTelemetry
    MeterProvider is used.

    The ``request_hook`` parameter specifies a callable that is invoked when a
    database operation starts. The hook can inspect or customize the span and
    operation details.

    The ``require_parent_span`` parameter determines whether database spans are
    created only when an active parent span exists. It defaults to *False*.

    The ``response_hook`` parameter specifies a callable that is invoked when a
    database operation completes. The hook can inspect or customize the span
    and operation result.

    The ``tracer_provider`` parameter specifies the OpenTelemetry
    TracerProvider used to create spans. If not specified, the global
    OpenTelemetry TracerProvider is used.

    Calling this function while instrumentation is already enabled raises
    a ``RuntimeError``.
    Call :func:`oracledb.plugins.opentelemetry.uninstrument()` before changing
    instrumentation options.
    """
    instrumentation.instrument(
        db_statement_dump=db_statement_dump,
        enable_database_trace_propagation=enable_database_trace_propagation,
        enhanced_database_reporting=enhanced_database_reporting,
        meter_provider=meter_provider,
        request_hook=request_hook,
        require_parent_span=require_parent_span,
        response_hook=response_hook,
        tracer_provider=tracer_provider,
    )


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
    Instruments an existing synchronous or asynchronous connection in place.

    The ``connection`` parameter is a synchronous or asynchronous connection to
    instrument. The plugin adds operation and Thin-mode round-trip callbacks
    while preserving any callbacks already configured on the connection.

    The remaining parameters are the same as those used by
    :func:`oracledb.plugins.opentelemetry.instrument()`.

    Calling this function again for the same connection raises
    a ``RuntimeError``. Use
    :func:`oracledb.plugins.opentelemetry.uninstrument_connection()` before
    instrumenting the connection again.
    """
    instrumentation.instrument_connection(
        connection,
        db_statement_dump=db_statement_dump,
        enable_database_trace_propagation=enable_database_trace_propagation,
        enhanced_database_reporting=enhanced_database_reporting,
        meter_provider=meter_provider,
        request_hook=request_hook,
        require_parent_span=require_parent_span,
        response_hook=response_hook,
        tracer_provider=tracer_provider,
    )


def uninstrument() -> None:
    """
    Disables instrumentation installed by
    :func:`oracledb.plugins.opentelemetry.instrument()`.

    This prevents newly created connections and pools from being instrumented.
    """
    instrumentation.uninstrument()


def uninstrument_connection(
    connection: oracledb.Connection | oracledb.AsyncConnection,
) -> None:
    """
    Restores callbacks on an explicitly instrumented connection in place.

    The ``connection`` parameter is a synchronous or asynchronous connection
    that was previously instrumented with
    :func:`oracledb.plugins.opentelemetry.instrument_connection()`.
    """
    instrumentation.uninstrument_connection(connection)


__all__ = [
    "instrument",
    "instrument_connection",
    "uninstrument",
    "uninstrument_connection",
]
