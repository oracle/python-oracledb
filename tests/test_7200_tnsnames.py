# -----------------------------------------------------------------------------
# Copyright (c) 2024, Oracle and/or its affiliates.
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
7200 - Module for testing parsing of tnsnames.ora files.
"""

import os
import tempfile

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
    requires_connection = False

    def test_7200(self):
        "7200 - test simple tnsnames.ora entry"
        host = "host_7200"
        port = 7200
        service_name = "service_7200"
        network_service_name = "nsn_7200"
        connect_string = f"""
            (DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST={host})(PORT={port}))
            (CONNECT_DATA=(SERVICE_NAME={service_name})))"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_name = os.path.join(temp_dir, "tnsnames.ora")
            with open(file_name, "w") as f:
                f.write(f"{network_service_name} = {connect_string}")
            params = oracledb.ConnectParams(config_dir=temp_dir)
            params.parse_connect_string(network_service_name)
        self.assertEqual(params.host, host)
        self.assertEqual(params.port, port)
        self.assertEqual(params.service_name, service_name)

    def test_7201(self):
        "7201 - test missing entry in tnsnames.ora"
        with tempfile.TemporaryDirectory() as temp_dir:
            params = oracledb.ConnectParams(config_dir=temp_dir)
            file_name = os.path.join(temp_dir, "tnsnames.ora")
            with open(file_name, "w") as f:
                f.write("# no entries")
            with self.assertRaisesFullCode("DPY-4000"):
                params.parse_connect_string("nsn_7201")
            self.assertEqual(params.get_network_service_names(), [])

    def test_7202(self):
        "7202 - test missing tnsnames.ora in configuration directory"
        with tempfile.TemporaryDirectory() as temp_dir:
            params = oracledb.ConnectParams(config_dir=temp_dir)
            with self.assertRaisesFullCode("DPY-4026"):
                params.parse_connect_string("nsn_7202")
            with self.assertRaisesFullCode("DPY-4026"):
                params.get_network_service_names()

    def test_7203(self):
        "7203 - test tnsnames.ora with invalid entries"
        host = "host_7203"
        port = 7203
        service_name = "service_7203"
        connect_string = f"""
            (DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST={host})(PORT={port}))
            (CONNECT_DATA=(SERVICE_NAME={service_name})))"""
        network_service_name = "nsn_7203"
        with tempfile.TemporaryDirectory() as temp_dir:
            file_name = os.path.join(temp_dir, "tnsnames.ora")
            with open(file_name, "w") as f:
                f.write("some garbage data which is not a valid entry\n")
                f.write(f"{network_service_name} = {connect_string}\n")
            params = oracledb.ConnectParams(config_dir=temp_dir)
            params.parse_connect_string(network_service_name)
            self.assertEqual(params.host, host)
            self.assertEqual(params.port, port)
            self.assertEqual(params.service_name, service_name)

    def test_7204(self):
        "7204 - test tnsnames.ora with multiple aliases on one line"
        host = "host_7204"
        port = 7204
        service_name = "service_7204"
        connect_string = f"""
            (DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST={host})(PORT={port}))
            (CONNECT_DATA=(SERVICE_NAME={service_name})))"""
        network_service_names = "nsn_7204a,nsn_7204b"
        with tempfile.TemporaryDirectory() as temp_dir:
            file_name = os.path.join(temp_dir, "tnsnames.ora")
            with open(file_name, "w") as f:
                f.write(f"{network_service_names} = {connect_string}\n")
            params = oracledb.ConnectParams(config_dir=temp_dir)
            for name in network_service_names.split(","):
                params.parse_connect_string(name)
                self.assertEqual(params.host, host)
                self.assertEqual(params.port, port)
                self.assertEqual(params.service_name, service_name)
            self.assertEqual(
                params.get_network_service_names(),
                network_service_names.upper().split(","),
            )

    def test_7205(self):
        "7205 - test easy connect string in tnsnames.ora"
        host = "host_7205"
        port = 7205
        service_name = "service_7205"
        connect_string = f"tcp://{host}:{port}/{service_name}"
        network_service_name = "nsn_7205"
        with tempfile.TemporaryDirectory() as temp_dir:
            file_name = os.path.join(temp_dir, "tnsnames.ora")
            with open(file_name, "w") as f:
                f.write(f"{network_service_name} = {connect_string}")
            params = oracledb.ConnectParams(config_dir=temp_dir)
            params.parse_connect_string(network_service_name)
            self.assertEqual(
                params.get_network_service_names(),
                [network_service_name.upper()],
            )
        self.assertEqual(params.host, host)
        self.assertEqual(params.port, port)
        self.assertEqual(params.service_name, service_name)

    def test_7206(self):
        "7206 - parse connect descriptor with / character in tnsnames.ora"
        host = "host_7206"
        port = 7206
        service_name = "service_7206"
        wallet_location = "/some/dir/7206"
        connect_string = f"""
            (DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST={host})(PORT={port}))
            (CONNECT_DATA=(SERVICE_NAME={service_name}))
            (SECURITY=(MY_WALLET_DIRECTORY={wallet_location})))"""
        network_service_name = "nsn_7206"
        with tempfile.TemporaryDirectory() as temp_dir:
            file_name = os.path.join(temp_dir, "tnsnames.ora")
            with open(file_name, "w") as f:
                f.write(f"{network_service_name} = {connect_string}")
            params = oracledb.ConnectParams(config_dir=temp_dir)
            params.parse_connect_string(network_service_name)
        self.assertEqual(params.host, host)
        self.assertEqual(params.port, port)
        self.assertEqual(params.service_name, service_name)
        self.assertEqual(params.wallet_location, wallet_location)

    def test_7207(self):
        "7207 - parse IFILE with files in same directory"
        host_a = "host_7207a"
        host_b = "host_7207b"
        port_a = 72071
        port_b = 72072
        service_name_a = "service_7207a"
        service_name_b = "service_7207b"
        connect_string_a = f"{host_a}:{port_a}/{service_name_a}"
        connect_string_b = f"{host_b}:{port_b}/{service_name_b}"
        network_service_name_a = "nsn_7207a"
        network_service_name_b = "nsn_7207b"
        include_file_name = "inc_7207.ora"
        with tempfile.TemporaryDirectory() as temp_dir:
            file_name = os.path.join(temp_dir, include_file_name)
            with open(file_name, "w") as f:
                f.write(f"{network_service_name_b} = {connect_string_b}")
            file_name = os.path.join(temp_dir, "tnsnames.ora")
            with open(file_name, "w") as f:
                f.write(f"{network_service_name_a} = {connect_string_a}\n")
                f.write(f"ifile = {include_file_name}")
            params = oracledb.ConnectParams(config_dir=temp_dir)
            params.parse_connect_string(network_service_name_a)
            self.assertEqual(params.host, host_a)
            self.assertEqual(params.port, port_a)
            self.assertEqual(params.service_name, service_name_a)
            params.parse_connect_string(network_service_name_b)
            self.assertEqual(params.host, host_b)
            self.assertEqual(params.port, port_b)
            self.assertEqual(params.service_name, service_name_b)
            self.assertEqual(
                params.get_network_service_names(),
                [
                    network_service_name_a.upper(),
                    network_service_name_b.upper(),
                ],
            )

    def test_7208(self):
        "7208 - parse IFILE with files in different directories"
        host_a = "host_7208a"
        host_b = "host_7208b"
        port_a = 72081
        port_b = 72082
        service_name_a = "service_7208a"
        service_name_b = "service_7208b"
        connect_string_a = f"{host_a}:{port_a}/{service_name_a}"
        connect_string_b = f"{host_b}:{port_b}/{service_name_b}"
        network_service_name_a = "nsn_7208a"
        network_service_name_b = "nsn_7208b"
        include_file_name = "inc_7208.ora"
        dir_1 = tempfile.TemporaryDirectory()
        dir_2 = tempfile.TemporaryDirectory()
        with dir_1 as primary_temp_dir, dir_2 as included_temp_dir:
            file_name = os.path.join(included_temp_dir, include_file_name)
            with open(file_name, "w") as f:
                f.write(f"{network_service_name_b} = {connect_string_b}")
            primary_file_name = os.path.join(primary_temp_dir, "tnsnames.ora")
            with open(primary_file_name, "w") as f:
                f.write(f"{network_service_name_a} = {connect_string_a}\n")
                f.write(f"ifile = {file_name}")
            params = oracledb.ConnectParams(config_dir=primary_temp_dir)
            params.parse_connect_string(network_service_name_a)
            self.assertEqual(params.host, host_a)
            self.assertEqual(params.port, port_a)
            self.assertEqual(params.service_name, service_name_a)
            params.parse_connect_string(network_service_name_b)
            self.assertEqual(params.host, host_b)
            self.assertEqual(params.port, port_b)
            self.assertEqual(params.service_name, service_name_b)
            self.assertEqual(
                params.get_network_service_names(),
                [
                    network_service_name_a.upper(),
                    network_service_name_b.upper(),
                ],
            )

    def test_7209(self):
        "7209 - cycle detection in same file"
        with tempfile.TemporaryDirectory() as temp_dir:
            network_service_name = "nsn_7209"
            file_name = os.path.join(temp_dir, "tnsnames.ora")
            with open(file_name, "w") as f:
                f.write(f"{network_service_name} = some_host/some_service\n")
                f.write("IFILE = tnsnames.ora")
            params = oracledb.ConnectParams(config_dir=temp_dir)
            with self.assertRaisesFullCode("DPY-4030"):
                params.parse_connect_string(network_service_name)

    def test_7210(self):
        "7210 - cycle detection in directly included file"
        with tempfile.TemporaryDirectory() as temp_dir:
            network_service_name = "nsn_7210"
            include_name = "included_7210.ora"
            primary_file_name = os.path.join(temp_dir, "tnsnames.ora")
            include_file_name = os.path.join(temp_dir, include_name)
            with open(primary_file_name, "w") as f:
                f.write(f"{network_service_name} = some_host/some_service\n")
                f.write(f"IFILE = {include_name}")
            with open(include_file_name, "w") as f:
                f.write("IFILE = tnsnames.ora")
            params = oracledb.ConnectParams(config_dir=temp_dir)
            with self.assertRaisesFullCode("DPY-4030"):
                params.parse_connect_string(network_service_name)

    def test_7211(self):
        "7211 - cycle detection in indirectly included file"
        with tempfile.TemporaryDirectory() as temp_dir:
            network_service_name = "nsn_7211"
            include_name_a = "included_7211_a.ora"
            include_name_b = "included_7211_b.ora"
            primary_file_name = os.path.join(temp_dir, "tnsnames.ora")
            include_file_name_a = os.path.join(temp_dir, include_name_a)
            include_file_name_b = os.path.join(temp_dir, include_name_b)
            with open(primary_file_name, "w") as f:
                f.write(f"{network_service_name} = some_host/some_service\n")
                f.write(f"IFILE = {include_name_a}")
            with open(include_file_name_a, "w") as f:
                f.write(f"IFILE = {include_name_b}")
            with open(include_file_name_b, "w") as f:
                f.write("IFILE = tnsnames.ora")
            params = oracledb.ConnectParams(config_dir=temp_dir)
            with self.assertRaisesFullCode("DPY-4030"):
                params.parse_connect_string(network_service_name)

    def test_7212(self):
        "7212 - duplicate entry in same file, but identical connect strings"
        host = "host_7212"
        port = 7212
        service_name = "service_7212"
        connect_string = f"{host}:{port}/{service_name}"
        network_service_name = "nsn_7212"
        with tempfile.TemporaryDirectory() as temp_dir:
            file_name = os.path.join(temp_dir, "tnsnames.ora")
            with open(file_name, "w") as f:
                f.write(f"{network_service_name} = {connect_string}\n")
                f.write("some_other_nsn = some_host/some_service\n")
                f.write(f"{network_service_name} = {connect_string}\n")
            params = oracledb.ConnectParams(config_dir=temp_dir)
            params.parse_connect_string(network_service_name)
            self.assertEqual(params.host, host)
            self.assertEqual(params.port, port)
            self.assertEqual(params.service_name, service_name)

    def test_7213(self):
        "7213 - duplicate entry in same file, but different connect strings"
        host_a = "host_7213a"
        port = 7213
        service_name_a = "service_7213a"
        host_b = "host_7213b"
        service_name_b = "service_7213b"
        connect_string_a = f"{host_a}:{port}/{service_name_a}"
        connect_string_b = f"{host_b}:{port}/{service_name_b}"
        network_service_name = "nsn_7213"
        with tempfile.TemporaryDirectory() as temp_dir:
            file_name = os.path.join(temp_dir, "tnsnames.ora")
            with open(file_name, "w") as f:
                f.write(f"{network_service_name} = {connect_string_a}\n")
                f.write("some_other_nsn = some_host/some_service\n")
                f.write(f"{network_service_name} = {connect_string_b}\n")
            params = oracledb.ConnectParams(config_dir=temp_dir)
            params.parse_connect_string(network_service_name)
            self.assertEqual(params.host, host_b)
            self.assertEqual(params.port, port)
            self.assertEqual(params.service_name, service_name_b)

    def test_7214(self):
        "7214 - duplicate entry in other file, but identical connect strings"
        host = "host_7214"
        port = 7214
        service_name = "service_7214"
        connect_string = f"{host}:{port}/{service_name}"
        network_service_name = "nsn_7214"
        include_name = "inc_7214.ora"
        with tempfile.TemporaryDirectory() as temp_dir:
            file_name = os.path.join(temp_dir, "tnsnames.ora")
            include_file_name = os.path.join(temp_dir, include_name)
            with open(file_name, "w") as f:
                f.write(f"{network_service_name} = {connect_string}\n")
                f.write(f"IFILE = {include_name}")
            with open(include_file_name, "w") as f:
                f.write(f"{network_service_name} = {connect_string}\n")
            params = oracledb.ConnectParams(config_dir=temp_dir)
            params.parse_connect_string(network_service_name)
            self.assertEqual(params.host, host)
            self.assertEqual(params.port, port)
            self.assertEqual(params.service_name, service_name)

    def test_7215(self):
        "7215 - duplicate entry in other file, but different connect strings"
        host_a = "host_7215a"
        port = 7215
        service_name_a = "service_7215a"
        host_b = "host_7215b"
        service_name_b = "service_7215b"
        connect_string_a = f"{host_a}:{port}/{service_name_a}"
        connect_string_b = f"{host_b}:{port}/{service_name_b}"
        network_service_name = "nsn_7215"
        include_name = "inc_7215.ora"
        with tempfile.TemporaryDirectory() as temp_dir:
            file_name = os.path.join(temp_dir, "tnsnames.ora")
            include_file_name = os.path.join(temp_dir, include_name)
            with open(file_name, "w") as f:
                f.write(f"{network_service_name} = {connect_string_a}\n")
                f.write(f"IFILE = {include_name}")
            with open(include_file_name, "w") as f:
                f.write(f"{network_service_name} = {connect_string_b}\n")
            params = oracledb.ConnectParams(config_dir=temp_dir)
            params.parse_connect_string(network_service_name)
            self.assertEqual(params.host, host_b)
            self.assertEqual(params.port, port)
            self.assertEqual(params.service_name, service_name_b)

    def test_7216(self):
        "7216 - test missing IFILE in tnsnames.ora"
        with tempfile.TemporaryDirectory() as temp_dir:
            file_name = os.path.join(temp_dir, "tnsnames.ora")
            with open(file_name, "w") as f:
                f.write("IFILE = missing.ora\n")
            params = oracledb.ConnectParams(config_dir=temp_dir)
            with self.assertRaisesFullCode("DPY-4026"):
                params.parse_connect_string("anything")

    def test_7217(self):
        "7217 - test duplicate IFILE, same file"
        host = "host_7217"
        port = 7217
        service_name = "service_7217"
        connect_string = f"{host}:{port}/{service_name}"
        network_service_name = "nsn_7217"
        include_name = "inc_7217.ora"
        with tempfile.TemporaryDirectory() as temp_dir:
            file_name = os.path.join(temp_dir, "tnsnames.ora")
            include_file_name = os.path.join(temp_dir, include_name)
            with open(file_name, "w") as f:
                f.write(f"IFILE = {include_name}\n")
                f.write("another_nsn = some_host/some_service\n")
                f.write(f"IFILE = {include_name}\n")
            with open(include_file_name, "w") as f:
                f.write(f"{network_service_name} = {connect_string}\n")
            params = oracledb.ConnectParams(config_dir=temp_dir)
            params.parse_connect_string(network_service_name)
            self.assertEqual(params.host, host)
            self.assertEqual(params.port, port)
            self.assertEqual(params.service_name, service_name)
            self.assertEqual(
                params.get_network_service_names(),
                [network_service_name.upper(), "ANOTHER_NSN"],
            )

    def test_7218(self):
        "7218 - test duplicate IFILE, different files"
        host = "host_7218"
        port = 7218
        service_name = "service_7218"
        connect_string = f"{host}:{port}/{service_name}"
        network_service_name = "nsn_7218"
        include_name_a = "inc_7218_a.ora"
        include_name_b = "inc_7218_b.ora"
        include_name_c = "inc_7218_c.ora"
        with tempfile.TemporaryDirectory() as temp_dir:
            file_name = os.path.join(temp_dir, "tnsnames.ora")
            include_file_name_a = os.path.join(temp_dir, include_name_a)
            include_file_name_b = os.path.join(temp_dir, include_name_b)
            include_file_name_c = os.path.join(temp_dir, include_name_c)
            with open(file_name, "w") as f:
                f.write(f"IFILE = {include_name_a}\n")
                f.write("another_nsn = some_host/some_service\n")
                f.write(f"IFILE = {include_name_b}\n")
            with open(include_file_name_a, "w") as f:
                f.write("in_a = some_host/some_service\n")
                f.write(f"IFILE = {include_name_c}\n")
            with open(include_file_name_b, "w") as f:
                f.write("in_b = some_host/some_service\n")
                f.write(f"IFILE = {include_name_c}\n")
            with open(include_file_name_c, "w") as f:
                f.write(f"{network_service_name} = {connect_string}\n")
            params = oracledb.ConnectParams(config_dir=temp_dir)
            params.parse_connect_string(network_service_name)
            self.assertEqual(params.host, host)
            self.assertEqual(params.port, port)
            self.assertEqual(params.service_name, service_name)
            self.assertEqual(
                params.get_network_service_names(),
                ["IN_A", network_service_name.upper(), "ANOTHER_NSN", "IN_B"],
            )


if __name__ == "__main__":
    test_env.run_test_cases()
