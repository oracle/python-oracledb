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
E3700 - Test database OpenTelemetry trace context with asyncio.

These tests require a Thin connection to a database that supports OpenTelemetry
tracing, and the opentelemetry-api package.
"""

import secrets

import pytest

trace = pytest.importorskip("opentelemetry.trace")
propagator = pytest.importorskip(
    "opentelemetry.trace.propagation.tracecontext"
).TraceContextTextMapPropagator()

TRACE_CONTEXT_QUERY = """
    select sys_context('CLIENTCONTEXT', 'ORA$OPENTELEM$TRACECTX')
    from dual
    """


def _create_trace_context(tracestate=""):
    span_context = trace.SpanContext(
        trace_id=secrets.randbits(128) or 1,
        span_id=secrets.randbits(64) or 1,
        is_remote=False,
        trace_flags=trace.TraceFlags(trace.TraceFlags.SAMPLED),
        trace_state=(
            trace.TraceState.from_header([tracestate])
            if tracestate
            else trace.TraceState()
        ),
    )
    carrier = {}
    propagator.inject(
        carrier,
        context=trace.set_span_in_context(
            trace.NonRecordingSpan(span_context)
        ),
    )
    return carrier


@pytest.fixture(autouse=True)
def module_checks(skip_unless_database_opentelemetry_supported, anyio_backend):
    pass


async def test_ext_3700(test_env):
    "E3700 - test async database OpenTelemetry trace parent"
    carrier = _create_trace_context()
    async with test_env.get_connection_async() as conn:
        conn.set_opentelemetry_trace_context(carrier["traceparent"])
        with conn.cursor() as cursor:
            await cursor.execute(TRACE_CONTEXT_QUERY)
            assert await cursor.fetchone() == (
                f"traceparent: {carrier['traceparent']}\r\n",
            )


async def test_ext_3701(test_env):
    "E3701 - test async database OpenTelemetry trace state"
    carrier = _create_trace_context("vendor=value")
    async with test_env.get_connection_async() as conn:
        conn.set_opentelemetry_trace_context(
            carrier["traceparent"], carrier["tracestate"]
        )
        with conn.cursor() as cursor:
            await cursor.execute(TRACE_CONTEXT_QUERY)
            expected = (
                f"traceparent: {carrier['traceparent']}\r\n"
                f"tracestate: {carrier['tracestate']}\r\n"
            )
            assert await cursor.fetchone() == (expected,)


async def test_ext_3702(test_env):
    "E3702 - test clearing async database OpenTelemetry trace context"
    carrier = _create_trace_context()
    async with test_env.get_connection_async() as conn:
        conn.set_app_context("CLIENTCONTEXT", other="kept")
        conn.set_opentelemetry_trace_context(carrier["traceparent"])
        conn.set_opentelemetry_trace_context(None)
        with conn.cursor() as cursor:
            await cursor.execute("""
                select sys_context('CLIENTCONTEXT', 'ORA$OPENTELEM$TRACECTX'),
                       sys_context('CLIENTCONTEXT', 'OTHER')
                from dual
                """)
            assert await cursor.fetchone() == (None, "kept")
