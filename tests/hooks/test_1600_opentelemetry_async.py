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
Tests for the embedded OpenTelemetry plugin with async connections.
"""

import pytest

import oracledb

in_memory_span_exporter = pytest.importorskip(
    "opentelemetry.sdk.trace.export.in_memory_span_exporter"
)
metric_export = pytest.importorskip("opentelemetry.sdk.metrics.export")
metric_sdk = pytest.importorskip("opentelemetry.sdk.metrics")
plugin = pytest.importorskip("oracledb.plugins.opentelemetry")
trace_api = pytest.importorskip("opentelemetry.trace")
trace_export = pytest.importorskip("opentelemetry.sdk.trace.export")
trace_sdk = pytest.importorskip("opentelemetry.sdk.trace")


def _assert_duration_data_point(reader, operation_name):
    metric = _operation_duration_metric(reader)
    data_point = next(
        point
        for point in metric.data.data_points
        if point.attributes.get("db.operation.name") == operation_name
    )
    assert data_point.count == 1
    assert data_point.max > 0
    assert data_point.min > 0
    assert data_point.sum > 0
    return data_point


def _operation_duration_metric(reader):
    metrics_data = reader.get_metrics_data()
    return next(
        metric
        for resource_metrics in metrics_data.resource_metrics
        for scope_metrics in resource_metrics.scope_metrics
        for metric in scope_metrics.metrics
        if metric.name == "db.client.operation.duration"
    )


@pytest.fixture
def meter_provider(metric_reader):
    return metric_sdk.MeterProvider(metric_readers=[metric_reader])


@pytest.fixture
def metric_reader():
    return metric_export.InMemoryMetricReader()


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


@pytest.fixture(autouse=True)
def reset_plugin():
    yield
    plugin.uninstrument()


@pytest.fixture
def span_exporter():
    return in_memory_span_exporter.InMemorySpanExporter()


@pytest.fixture
def tracer_provider(span_exporter):
    provider = trace_sdk.TracerProvider()
    provider.add_span_processor(
        trace_export.SimpleSpanProcessor(span_exporter)
    )
    return provider


async def test_hooks_1600(async_conn, span_exporter, tracer_provider):
    "1600 - test async default metadata protects bind values"
    plugin.instrument_connection(async_conn, tracer_provider=tracer_provider)
    await async_conn.cursor().execute("select :1 from dual", ["secret"])
    plugin.uninstrument_connection(async_conn)
    span = next(
        span
        for span in span_exporter.get_finished_spans()
        if span.attributes.get("db.operation.name") == "SELECT"
    )
    assert span.instrumentation_scope.name == "oracledb.plugins.opentelemetry"
    assert span.attributes["db.query.text"] == "select :1 from dual"
    assert "db.query.parameter.0" not in span.attributes
    assert "secret" not in str(span.attributes)


@pytest.mark.parametrize(
    "options, include_text",
    [({}, False), ({"db_statement_dump": True}, True)],
)
async def test_hooks_1601(
    async_conn, options, include_text, span_exporter, tracer_provider
):
    "1601 - test async SQL text collection with empty parameters"
    plugin.instrument_connection(
        async_conn, tracer_provider=tracer_provider, **options
    )
    await async_conn.cursor().execute(
        "select 'sensitive literal' from dual", []
    )
    plugin.uninstrument_connection(async_conn)
    span = next(
        span
        for span in span_exporter.get_finished_spans()
        if span.attributes.get("db.operation.name") == "SELECT"
    )
    assert ("db.query.text" in span.attributes) is include_text


async def test_hooks_1602(
    metric_reader, meter_provider, test_env, span_exporter, tracer_provider
):
    "1602 - test an asynchronous driver execute creates telemetry"
    with test_env.get_connection():
        pass
    plugin.instrument(
        meter_provider=meter_provider,
        tracer_provider=tracer_provider,
    )
    async with test_env.get_connection_async() as conn:
        cursor = conn.cursor()
        await cursor.execute("select :1 from dual", [1])
    spans = span_exporter.get_finished_spans()
    operation_span = next(
        span
        for span in spans
        if span.attributes.get("db.operation.name") == "SELECT"
    )
    assert operation_span.attributes["db.query.text"] == "select :1 from dual"
    _assert_duration_data_point(metric_reader, "SELECT")


async def test_hooks_1603(
    skip_unless_thin_mode, span_exporter, test_env, tracer_provider
):
    "1603 - test an async Thin round trip is a child of its operation span"
    plugin.instrument(tracer_provider=tracer_provider)
    async with test_env.get_connection_async() as conn:
        cursor = conn.cursor()
        await cursor.execute("select 1 from dual")
    spans = span_exporter.get_finished_spans()
    operation_span = next(
        span
        for span in spans
        if span.attributes.get("db.operation.name") == "SELECT"
    )
    round_trip_span = next(
        span for span in spans if span.name == "oracledb.execute"
    )
    assert round_trip_span.parent.span_id == operation_span.context.span_id


async def test_hooks_1604(async_conn):
    "1604 - test async hooks receive the documented operation payloads"
    events = []

    def request_hook(span, info):
        if info["name"] == "execute":
            events.append(("request", info))

    def response_hook(span, info):
        if info["name"] == "execute":
            events.append(("response", info))

    plugin.instrument_connection(
        async_conn,
        request_hook=request_hook,
        response_hook=response_hook,
    )
    cursor = async_conn.cursor()
    await cursor.execute("select :1 from dual", [1])
    plugin.uninstrument_connection(async_conn)
    assert events[0][1]["name"] == "execute"
    assert events[0][1]["operation"] == "SELECT"
    assert events[1][1]["data"] is cursor
    assert events[1][1]["error"] is None


async def test_hooks_1605(async_conn, span_exporter, tracer_provider):
    "1605 - test explicit async instrumentation preserves callbacks"
    calls = []

    def callback(name, arguments):
        calls.append((name, arguments))
        return lambda result: calls.append(result)

    async_conn.operation_callback = callback
    plugin.instrument_connection(async_conn, tracer_provider=tracer_provider)
    cursor = async_conn.cursor()
    await cursor.execute("select 1 from dual")
    assert len(calls) == 2
    select_spans = [
        span
        for span in span_exporter.get_finished_spans()
        if span.attributes.get("db.operation.name") == "SELECT"
    ]
    assert len(select_spans) == 1
    plugin.uninstrument_connection(async_conn)
    assert async_conn.operation_callback is callback
    span_exporter.clear()
    await cursor.execute("select 2 from dual")
    assert len(calls) == 4
    assert not span_exporter.get_finished_spans()


async def test_hooks_1606(metric_reader, meter_provider, test_env):
    "1606 - test exporter database calls do not create nested async telemetry"

    class QueryingExporter(in_memory_span_exporter.InMemorySpanExporter):
        connection = None
        queried = False

        def export(self, spans):
            if self.connection is not None and not self.queried:
                self.queried = True
                self.connection.cursor().execute("select 2 from dual")
            return super().export(spans)

    exporter = QueryingExporter()
    provider = trace_sdk.TracerProvider()
    provider.add_span_processor(trace_export.SimpleSpanProcessor(exporter))
    # Exporters are synchronous; use a separate connection.
    with test_env.get_connection() as export_connection:
        async with test_env.get_connection_async() as connection:
            plugin.instrument_connection(
                connection,
                meter_provider=meter_provider,
                tracer_provider=provider,
            )
            plugin.instrument_connection(
                export_connection,
                meter_provider=meter_provider,
                tracer_provider=provider,
            )
            exporter.connection = export_connection
            await connection.cursor().execute("select 1 from dual")
            plugin.uninstrument_connection(export_connection)
            plugin.uninstrument_connection(connection)
    select_spans = [
        span
        for span in exporter.get_finished_spans()
        if span.attributes.get("db.operation.name") == "SELECT"
    ]
    assert exporter.queried
    assert len(select_spans) == 1
    _assert_duration_data_point(metric_reader, "SELECT")


async def test_hooks_1607(
    metric_reader, meter_provider, test_env, span_exporter, tracer_provider
):
    "1607 - test async operation failures record error telemetry"
    with test_env.get_connection():
        pass
    plugin.instrument(
        meter_provider=meter_provider,
        tracer_provider=tracer_provider,
    )
    async with test_env.get_connection_async() as connection:
        span_exporter.clear()
        with pytest.raises(oracledb.DatabaseError) as exc_info:
            await connection.cursor().execute(
                "select missing_column from dual"
            )
    operation_span = next(
        span
        for span in span_exporter.get_finished_spans()
        if span.attributes.get("db.operation.name") == "SELECT"
    )
    assert operation_span.status.status_code is trace_api.StatusCode.ERROR
    assert "error.type" in operation_span.attributes
    data_point = _assert_duration_data_point(metric_reader, "SELECT")
    assert (
        data_point.attributes["error.type"] == exc_info.value.args[0].full_code
    )
    assert data_point.attributes["db.system.name"] == "oracle.db"
    assert set(data_point.attributes) <= {
        "db.namespace",
        "db.operation.name",
        "db.system.name",
        "error.type",
        "server.address",
        "server.port",
    }


async def test_hooks_1608(
    async_conn, metric_reader, meter_provider, span_exporter, tracer_provider
):
    "1608 - test async operation metrics omit SQL and bind values"
    plugin.instrument_connection(
        async_conn,
        enhanced_database_reporting=True,
        meter_provider=meter_provider,
        tracer_provider=tracer_provider,
    )
    await async_conn.cursor().execute("select :1 from dual", ["secret"])
    plugin.uninstrument_connection(async_conn)
    metric = _operation_duration_metric(metric_reader)
    data_point = _assert_duration_data_point(metric_reader, "SELECT")
    assert metric.description == "Duration of database client operations."
    assert metric.unit == "s"
    assert data_point.attributes["db.system.name"] == "oracle.db"
    assert set(data_point.attributes) <= {
        "db.namespace",
        "db.operation.name",
        "db.system.name",
        "server.address",
        "server.port",
    }
    assert "secret" not in str(data_point.attributes)
    span = next(
        span
        for span in span_exporter.get_finished_spans()
        if span.attributes.get("db.operation.name") == "SELECT"
    )
    assert span.attributes["db.query.parameter.0"] == "secret"


async def test_hooks_1609(
    async_conn, metric_reader, meter_provider, span_exporter, tracer_provider
):
    "1609 - test async require parent span prevents telemetry creation"
    plugin.instrument_connection(
        async_conn,
        meter_provider=meter_provider,
        require_parent_span=True,
        tracer_provider=tracer_provider,
    )
    await async_conn.cursor().execute("select 1 from dual")
    plugin.uninstrument_connection(async_conn)
    assert not span_exporter.get_finished_spans()
    assert metric_reader.get_metrics_data() is None


async def test_hooks_1610(
    skip_unless_database_opentelemetry_supported,
    skip_unless_thin_mode,
    span_exporter,
    test_env,
    tracer_provider,
):
    "1610 - test async database trace context propagation and cleanup"
    plugin.instrument(
        enable_database_trace_propagation=True,
        tracer_provider=tracer_provider,
    )
    async with test_env.get_connection_async() as connection:
        cursor = connection.cursor()
        await cursor.execute(
            "select sys_context('CLIENTCONTEXT', "
            "'ORA$OPENTELEM$TRACECTX') from dual"
        )
        (trace_context,) = await cursor.fetchone()
        round_trip_span = next(
            span
            for span in span_exporter.get_finished_spans()
            if span.name == "oracledb.execute"
        )
        expected_traceparent = (
            f"traceparent: 00-{round_trip_span.context.trace_id:032x}-"
            f"{round_trip_span.context.span_id:016x}-"
            f"{int(round_trip_span.context.trace_flags):02x}\r\n"
        )
        assert trace_context == expected_traceparent
        plugin.uninstrument()
        await cursor.execute(
            "select sys_context('CLIENTCONTEXT', "
            "'ORA$OPENTELEM$TRACECTX') from dual"
        )
        assert (await cursor.fetchone())[0] is None


async def test_hooks_1611(
    skip_unless_database_opentelemetry_supported,
    skip_unless_thin_mode,
    test_env,
    tracer_provider,
):
    "1611 - test async propagation preserves a nonempty W3C tracestate"
    plugin.instrument(
        enable_database_trace_propagation=True,
        tracer_provider=tracer_provider,
    )
    span = trace_api.NonRecordingSpan(
        trace_api.SpanContext(
            trace_id=1,
            span_id=2,
            is_remote=False,
            trace_flags=trace_api.TraceFlags(trace_api.TraceFlags.SAMPLED),
            trace_state=trace_api.TraceState([("vendor", "opaque")]),
        )
    )
    with trace_api.use_span(span):
        async with test_env.get_connection_async() as connection:
            cursor = connection.cursor()
            await cursor.execute(
                "select sys_context('CLIENTCONTEXT', "
                "'ORA$OPENTELEM$TRACECTX') from dual"
            )
            (trace_context,) = await cursor.fetchone()
    assert "tracestate: vendor=opaque\r\n" in trace_context


async def test_hooks_1612(
    skip_unless_database_opentelemetry_supported,
    span_exporter,
    test_env,
    tracer_provider,
):
    "1612 - test async database trace propagation is disabled by default"
    plugin.instrument(tracer_provider=tracer_provider)
    async with test_env.get_connection_async() as connection:
        cursor = connection.cursor()
        await cursor.execute(
            "select sys_context('CLIENTCONTEXT', "
            "'ORA$OPENTELEM$TRACECTX') from dual"
        )
        assert (await cursor.fetchone())[0] is None
    assert any(
        span.attributes.get("db.operation.name") == "SELECT"
        for span in span_exporter.get_finished_spans()
    )


async def test_hooks_1613(meter_provider, metric_reader, test_env):
    "1613 - test async PL/SQL execute records an operation duration metric"
    with test_env.get_connection():
        pass
    plugin.instrument(meter_provider=meter_provider)
    async with test_env.get_connection_async() as connection:
        cursor = connection.cursor()
        value = cursor.var(int)
        await cursor.execute("begin :value := 1; end;", value=value)
    _assert_duration_data_point(metric_reader, "BEGIN")


async def test_hooks_1614(meter_provider, metric_reader, test_env):
    "1614 - test async PL/SQL batch records an operation duration metric"
    with test_env.get_connection():
        pass
    plugin.instrument(meter_provider=meter_provider)
    async with test_env.get_connection_async() as connection:
        await connection.cursor().executemany("begin null; end;", 2)
    data_point = _assert_duration_data_point(metric_reader, "BATCH BEGIN")
    assert data_point.attributes["db.operation.batch.size"] == 2


async def test_hooks_1615(async_conn):
    "1615 - test repeated async connection instrumentation raises an error"
    assert plugin.instrument_connection(async_conn) is None
    operation_callback = async_conn.operation_callback
    round_trip_callback = async_conn.round_trip_callback
    with pytest.raises(RuntimeError, match="already instrumented"):
        plugin.instrument_connection(async_conn)
    assert async_conn.operation_callback is operation_callback
    assert async_conn.round_trip_callback is round_trip_callback
    assert plugin.uninstrument_connection(async_conn) is None
    assert plugin.instrument_connection(async_conn) is None
    plugin.uninstrument_connection(async_conn)
