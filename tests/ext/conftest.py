# -----------------------------------------------------------------------------
# Copyright (c) 2024, 2026, Oracle and/or its affiliates.
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

# -----------------------------------------------------------------------------
# Loads the test environment found in the base directory and then extends it
# with some methods used to determine which extended tests to run.
# -----------------------------------------------------------------------------

import asyncio
import configparser
import os
import pytest
import socket
import threading

import oracledb

DATABASES_SECTION_NAME = "Databases"


@pytest.fixture(scope="session")
def extended_config(test_env):
    return ExtendedConfig(test_env)


@pytest.fixture(scope="session")
def skip_unless_has_orapki(extended_config):
    if not extended_config.get_bool_value("has_orapki"):
        pytest.skip("extended configuration has_orapki is disabled")


@pytest.fixture(scope="session")
def skip_unless_local_database(extended_config):
    if not extended_config.get_bool_value("local_database"):
        pytest.skip("extended configuration local_database is disabled")


@pytest.fixture(scope="session")
def skip_unless_run_long_tests(extended_config):
    if not extended_config.get_bool_value("run_long_tests"):
        pytest.skip("extended configuration run_long_tests is disabled")


@pytest.fixture(scope="session")
def skip_unless_deep_data_security(extended_config, test_env):
    if not test_env.has_server_version(23, 26):
        pytest.skip("no Deep Data Security support in database")
    if not test_env.has_client_version(23, 26, 4):
        pytest.skip("no Deep Data Security support in client")
    if (
        not extended_config.get_str_value("deep_data_security_db_token")
        or not extended_config.get_str_value("deep_data_security_user_token")
        or not extended_config.get_str_value("deep_data_security_xs_user")
    ):
        pytest.skip("missing Deep Data Security configuration")


# defines class used for setting up a tunnel that can easily be cut for testing
# certain aspects of pool and connection behaviour
class Tunnel:

    def __init__(self, test_env):
        self.params = test_env.get_connect_params()
        self.params.parse_connect_string(test_env.connect_string)
        if isinstance(self.params.port, list):
            pytest.skip("multiple addressses cannot be tunneled")
        self.pool_params = test_env.get_pool_params()
        self.pool_params.parse_connect_string(test_env.connect_string)
        self.pool_params.set(
            getmode=oracledb.POOL_GETMODE_TIMEDWAIT, wait_timeout=5_000
        )
        self.connections = []

    def _close(self, *socks):
        """
        Closes both halves of the pipe.
        """
        for s in socks:
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            s.close()

    def _pipe(self, src, dst):
        """
        Transmit data unchecked.
        """
        try:
            while data := src.recv(65536):
                dst.sendall(data)
        finally:
            self._close(src, dst)

    def _serve(self):
        """
        Accept connections and upon connection, create pipes that simply
        transmit the data unchecked, but keep track of the connections made so
        that they can be severed on demand.
        """
        while True:
            client, _ = self.listener.accept()
            target = (self.params.host, self.params.port)
            upstream = socket.create_connection(target)
            with self.lock:
                self.connections.append((client, upstream))
                for src, dst in ((client, upstream), (upstream, client)):
                    thread = threading.Thread(
                        target=self._pipe, args=(src, dst), daemon=True
                    )
                    thread.start()

    def cut(self):
        """
        Cuts the connection on all connections made so far.
        """
        with self.lock:
            for pair in self.connections:
                self._close(*pair)
            self.connections.clear()

    def get_connect_params(self):
        """
        Return the connection parameters used to establish a connection to the
        database. The existing parameters are retained and only the host and
        port are substituted so that the connection goes through the tunnel.
        """
        params = self.params.copy()
        params.set(host=self.host, port=self.port)
        return params

    def get_pool_params(self):
        """
        Return the pool parameters used to create a pool of connections to the
        database. The existing parameters are retained and only the host and
        port are substituted so that the connection goes through the tunnel.
        """
        params = self.pool_params.copy()
        params.set(host=self.host, port=self.port)
        return params

    def start(self):
        """
        Starts the tunnel.
        """
        self.lock = threading.Lock()
        self.listener = socket.create_server(("127.0.0.1", 0))
        self.host, self.port = self.listener.getsockname()
        thread = threading.Thread(target=self._serve, daemon=True)
        thread.start()


@pytest.fixture
def tunnel(skip_unless_run_long_tests, test_env):
    tunnel = Tunnel(test_env)
    tunnel.start()
    yield tunnel


# defines class used for setting up a tunnel that can easily be cut for testing
# certain aspects of pool and connection behaviour
class AsyncTunnel(Tunnel):

    def _close(self, *socks):
        """
        Closes both halves of the pipe.
        """
        for s in socks:
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            s.close()

    async def _pipe(self, reader, writer):
        """
        Transmit data unchecked.
        """
        try:
            while data := await reader.read(65536):
                writer.write(data)
                await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def _handle_client(self, local_reader, local_writer):
        """
        Handles a new client connecting to the tunnel.
        """
        tasks = []
        remote_reader, remote_writer = await asyncio.open_connection(
            self.params.host, self.params.port
        )
        async with self.lock:
            for reader, writer in (
                (local_reader, remote_writer),
                (remote_reader, local_writer),
            ):
                self.connections.append(writer)
                tasks.append(asyncio.create_task(self._pipe(reader, writer)))
        await asyncio.gather(*tasks)

    async def cut(self):
        """
        Cuts the connection on all connections made so far.
        """
        async with self.lock:
            for writer in self.connections:
                writer.close()
                await writer.wait_closed()
            self.connections.clear()

    async def start(self, event):
        """
        Starts the tunnel.
        """
        self.lock = asyncio.Lock()
        self.listener = await asyncio.start_server(
            self._handle_client, host="127.0.0.1"
        )
        self.host, self.port = self.listener.sockets[0].getsockname()
        event.set()
        async with self.listener:
            await self.listener.serve_forever()

    async def stop(self):
        """
        Stops the tunnel.
        """
        await self.cut()
        self.listener.close()
        await self.listener.wait_closed()


@pytest.fixture
async def async_tunnel(skip_unless_run_long_tests, test_env):
    tunnel = AsyncTunnel(test_env)
    event = asyncio.Event()
    _task = asyncio.create_task(tunnel.start(event))
    await event.wait()
    yield tunnel
    await tunnel.stop()


class ExtendedConfig:

    def __init__(self, test_env):
        default_file_name = os.path.join(
            os.path.dirname(__file__), "config.ini"
        )
        file_name = os.environ.get(
            "PYO_TEST_EXT_CONFIG_FILE", default_file_name
        )
        self.parser = configparser.ConfigParser()
        self.parser.read(file_name)
        self.section_name = "DEFAULT"
        if self.parser.has_section(DATABASES_SECTION_NAME):
            for section_name, connect_string in self.parser.items(
                DATABASES_SECTION_NAME
            ):
                if connect_string.upper() == test_env.connect_string.upper():
                    self.section_name = section_name
                    break

    def get_bool_value(self, name, fallback=False):
        """
        Returns a boolean for a specifically named value.
        """
        return self.parser.getboolean(
            self.section_name, name, fallback=fallback
        )

    def get_file_value(self, name, fallback=""):
        """
        Returns the contents of a file for a specifically named value.
        """
        file_name = self.get_str_value(name, fallback)
        if file_name:
            with open(file_name, encoding="utf-8") as f:
                return f.read()

    def get_str_value(self, name, fallback=""):
        """
        Returns a string for a specifically named value.
        """
        return self.parser.get(self.section_name, name, fallback=fallback)
