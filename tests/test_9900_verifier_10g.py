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
9900 - Module for testing authentication against accounts whose password only
carries the legacy 10G (DES) verifier (verifier type 0x939) in thin mode.
"""

import oracledb
import pytest

from cryptography.hazmat.primitives.ciphers import Cipher, modes

try:  # DES was relocated to "decrepit" in cryptography 43+
    from cryptography.hazmat.decrepit.ciphers.algorithms import TripleDES
except ImportError:  # pragma: no cover
    from cryptography.hazmat.primitives.ciphers.algorithms import TripleDES


# temporary account provisioned with a 10G-only verifier; the 10G verifier is
# case-insensitive (user and password are upper-cased before hashing)
TEST_USER = "PYO_TEST_V10G"
TEST_PASSWORD = "Welcome_12345"


@pytest.fixture(autouse=True)
def module_checks(skip_unless_thin_mode):
    pass


def _compute_10g_verifier(user, password):
    """
    Independently computes the legacy 10G (DES) password verifier and returns
    it as 16 hex characters. Used to provision the test account through
    "IDENTIFIED BY VALUES"; kept separate from the driver implementation so the
    test does not simply mirror the code under test.
    """

    def des_cbc(key, data):
        encryptor = Cipher(TripleDES(key), modes.CBC(bytes(8))).encryptor()
        return encryptor.update(data) + encryptor.finalize()

    text = (user + password).upper().encode("utf-16-be")
    if len(text) % 8:
        text += bytes(8 - len(text) % 8)
    interim_key = des_cbc(bytes.fromhex("0123456789ABCDEF"), text)[-8:]
    return des_cbc(interim_key, text)[-8:].hex().upper()


def test_9900(admin_conn, test_env):
    "9900 - connect to an account that only has a 10G password verifier"

    # anchor the local verifier implementation against a well-known vector
    # before relying on it to provision the account
    assert _compute_10g_verifier("SYSTEM", "MANAGER") == "D4DF7931AB130E37"

    # create a user whose password carries only the 10G verifier;
    # "IDENTIFIED BY VALUES" avoids any server-side hashing, so no 11G/12C
    # verifier is generated
    verifier = _compute_10g_verifier(TEST_USER, TEST_PASSWORD)
    with admin_conn.cursor() as cursor:
        try:
            cursor.execute(f"drop user {TEST_USER} cascade")
        except oracledb.DatabaseError:
            pass
        try:
            cursor.execute(
                f"create user {TEST_USER} identified by values '{verifier}'"
            )
        except oracledb.DatabaseError as e:
            pytest.skip(f"cannot provision a 10G-verifier account: {e}")
        cursor.execute(f"grant create session to {TEST_USER}")

    try:
        # the database must permit 10G logons (a sufficiently low
        # SQLNET.ALLOWED_LOGON_VERSION_SERVER); otherwise the server rejects the
        # protocol with ORA-28040 and the scenario cannot be exercised here
        try:
            conn = test_env.get_connection(
                user=TEST_USER, password=TEST_PASSWORD
            )
        except oracledb.DatabaseError as e:
            (error,) = e.args
            if error.full_code == "ORA-28040":
                pytest.skip("database does not allow 10G password verifiers")
            raise
        with conn.cursor() as cursor:
            cursor.execute("select user from dual")
            (current_user,) = cursor.fetchone()
            assert current_user == TEST_USER.upper()
        conn.close()
    finally:
        with admin_conn.cursor() as cursor:
            cursor.execute(f"drop user {TEST_USER} cascade")
