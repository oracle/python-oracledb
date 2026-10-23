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
Tests for the embedded OpenTelemetry plugin.
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


def test_hooks_1500(conn, span_exporter, tracer_provider):
    "1500 - test default metadata protects bind values"
    plugin.instrument_connection(conn, tracer_provider=tracer_provider)
    conn.cursor().execute("select :1 from dual", ["secret"])
    plugin.uninstrument_connection(conn)
    span = next(
        span
        for span in span_exporter.get_finished_spans()
        if span.attributes.get("db.operation.name") == "SELECT"
    )
    assert span.instrumentation_scope.name == "oracledb.plugins.opentelemetry"
    assert span.attributes["db.query.text"] == "select :1 from dual"
    assert "db.query.parameter.0" not in span.attributes
    assert "secret" not in str(span.attributes)


def test_hooks_1501(conn, span_exporter, tracer_provider):
    "1501 - test explicit instrumentation preserves application callbacks"
    calls = []

    def callback(name, arguments):
        calls.append((name, arguments))
        return lambda result: calls.append(result)

    conn.operation_callback = callback
    plugin.instrument_connection(conn, tracer_provider=tracer_provider)
    cursor = conn.cursor()
    cursor.execute("select 1 from dual")
    assert len(calls) == 2
    select_spans = [
        span
        for span in span_exporter.get_finished_spans()
        if span.attributes.get("db.operation.name") == "SELECT"
    ]
    assert len(select_spans) == 1
    plugin.uninstrument_connection(conn)
    assert conn.operation_callback is callback
    span_exporter.clear()
    cursor.execute("select 2 from dual")
    assert len(calls) == 4
    assert not span_exporter.get_finished_spans()


def test_hooks_1502():
    "1502 - test repeated global instrumentation raises an error"
    plugin.instrument()
    with pytest.raises(RuntimeError, match="already enabled"):
        plugin.instrument()
    plugin.uninstrument()
    plugin.instrument()
    plugin.uninstrument()
    plugin.uninstrument()


def test_hooks_1503(
    metric_reader, meter_provider, test_env, span_exporter, tracer_provider
):
    "1503 - test executing a statement creates telemetry"
    plugin.instrument(
        meter_provider=meter_provider,
        tracer_provider=tracer_provider,
    )
    with test_env.get_connection() as conn:
        conn.cursor().execute("select :1 from dual", [1])
    spans = span_exporter.get_finished_spans()
    operation_span = next(
        span
        for span in spans
        if span.attributes.get("db.operation.name") == "SELECT"
    )
    assert operation_span.attributes["db.query.text"] == "select :1 from dual"
    _assert_duration_data_point(metric_reader, "SELECT")


def test_hooks_1504(
    metric_reader, meter_provider, test_env, span_exporter, tracer_provider
):
    "1504 - test an operation failure records error telemetry"
    plugin.instrument(
        meter_provider=meter_provider,
        tracer_provider=tracer_provider,
    )
    with test_env.get_connection() as conn:
        with pytest.raises(oracledb.DatabaseError) as exc_info:
            conn.cursor().execute("select missing_column from dual")
    spans = span_exporter.get_finished_spans()
    operation_span = next(
        span
        for span in spans
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


def test_hooks_1505(
    skip_unless_thin_mode, span_exporter, test_env, tracer_provider
):
    "1505 - test a Thin round trip is a child of its operation span"
    plugin.instrument(tracer_provider=tracer_provider)
    with test_env.get_connection() as conn:
        conn.cursor().execute("select 1 from dual")
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


@pytest.mark.parametrize(
    "options, include_text",
    [({}, False), ({"db_statement_dump": True}, True)],
)
def test_hooks_1506(
    conn, options, include_text, span_exporter, tracer_provider
):
    "1506 - test SQL text collection with empty parameters"
    plugin.instrument_connection(
        conn, tracer_provider=tracer_provider, **options
    )
    conn.cursor().execute("select 'sensitive literal' from dual", [])
    plugin.uninstrument_connection(conn)
    span = next(
        span
        for span in span_exporter.get_finished_spans()
        if span.attributes.get("db.operation.name") == "SELECT"
    )
    assert ("db.query.text" in span.attributes) is include_text


def test_hooks_1507(conn):
    "1507 - test hooks receive the documented operation payloads"
    events = []

    def request_hook(span, info):
        if info["name"] == "execute":
            events.append(("request", info))

    def response_hook(span, info):
        if info["name"] == "execute":
            events.append(("response", info))

    plugin.instrument_connection(
        conn,
        request_hook=request_hook,
        response_hook=response_hook,
    )
    cursor = conn.cursor()
    cursor.execute("select :1 from dual", [1])
    plugin.uninstrument_connection(conn)
    assert events[0][1]["name"] == "execute"
    assert events[0][1]["operation"] == "SELECT"
    assert events[1][1]["data"] is cursor
    assert events[1][1]["error"] is None


def test_hooks_1508(metric_reader, meter_provider, test_env):
    "1508 - test exporter database calls do not create nested telemetry"

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
    # A second connection avoids reentering the active driver call.
    with (
        test_env.get_connection() as connection,
        test_env.get_connection() as export_connection,
    ):
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
        connection.cursor().execute("select 1 from dual")
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


def test_hooks_1509(
    skip_unless_database_opentelemetry_supported,
    skip_unless_thin_mode,
    span_exporter,
    test_env,
    tracer_provider,
):
    "1509 - test database trace context propagation and cleanup"
    plugin.instrument(
        enable_database_trace_propagation=True,
        tracer_provider=tracer_provider,
    )
    with test_env.get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "select sys_context('CLIENTCONTEXT', "
            "'ORA$OPENTELEM$TRACECTX') from dual"
        )
        (trace_context,) = cursor.fetchone()
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
        cursor.execute(
            "select sys_context('CLIENTCONTEXT', "
            "'ORA$OPENTELEM$TRACECTX') from dual"
        )
        assert cursor.fetchone()[0] is None


def test_hooks_1510(
    skip_unless_database_opentelemetry_supported,
    skip_unless_thin_mode,
    test_env,
    tracer_provider,
):
    "1510 - test propagation preserves a nonempty W3C tracestate"
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
        with test_env.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "select sys_context('CLIENTCONTEXT', "
                "'ORA$OPENTELEM$TRACECTX') from dual"
            )
            (trace_context,) = cursor.fetchone()
    assert "tracestate: vendor=opaque\r\n" in trace_context


def test_hooks_1511(
    skip_unless_database_opentelemetry_supported,
    span_exporter,
    test_env,
    tracer_provider,
):
    "1511 - test database trace propagation is disabled by default"
    plugin.instrument(tracer_provider=tracer_provider)
    with test_env.get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "select sys_context('CLIENTCONTEXT', "
            "'ORA$OPENTELEM$TRACECTX') from dual"
        )
        assert cursor.fetchone()[0] is None
    assert any(
        span.attributes.get("db.operation.name") == "SELECT"
        for span in span_exporter.get_finished_spans()
    )


def test_hooks_1512(
    conn, metric_reader, meter_provider, span_exporter, tracer_provider
):
    "1512 - test operation duration metrics omit SQL and bind values"
    plugin.instrument_connection(
        conn,
        enhanced_database_reporting=True,
        meter_provider=meter_provider,
        tracer_provider=tracer_provider,
    )
    conn.cursor().execute("select :1 from dual", ["secret"])
    plugin.uninstrument_connection(conn)
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


def test_hooks_1513(
    conn, metric_reader, meter_provider, span_exporter, tracer_provider
):
    "1513 - test require parent span prevents metric creation"
    plugin.instrument_connection(
        conn,
        meter_provider=meter_provider,
        require_parent_span=True,
        tracer_provider=tracer_provider,
    )
    conn.cursor().execute("select 1 from dual")
    plugin.uninstrument_connection(conn)
    assert not span_exporter.get_finished_spans()
    assert metric_reader.get_metrics_data() is None


def test_hooks_1514(meter_provider, metric_reader, test_env):
    "1514 - test PL/SQL execute records an operation duration metric"
    with test_env.get_connection():
        pass
    plugin.instrument(meter_provider=meter_provider)
    with test_env.get_connection() as conn:
        cursor = conn.cursor()
        value = cursor.var(int)
        cursor.execute("begin :value := 1; end;", value=value)
    _assert_duration_data_point(metric_reader, "BEGIN")


def test_hooks_1515(meter_provider, metric_reader, test_env):
    "1515 - test PL/SQL batch records an operation duration metric"
    with test_env.get_connection():
        pass
    plugin.instrument(meter_provider=meter_provider)
    with test_env.get_connection() as conn:
        conn.cursor().executemany("begin null; end;", 2)
    data_point = _assert_duration_data_point(metric_reader, "BATCH BEGIN")
    assert data_point.attributes["db.operation.batch.size"] == 2


def test_hooks_1516(conn):
    "1516 - test repeated connection instrumentation raises an error"
    assert plugin.instrument_connection(conn) is None
    operation_callback = conn.operation_callback
    round_trip_callback = conn.round_trip_callback
    with pytest.raises(RuntimeError, match="already instrumented"):
        plugin.instrument_connection(conn)
    assert conn.operation_callback is operation_callback
    assert conn.round_trip_callback is round_trip_callback
    assert plugin.uninstrument_connection(conn) is None
    assert plugin.instrument_connection(conn) is None
    plugin.uninstrument_connection(conn)
