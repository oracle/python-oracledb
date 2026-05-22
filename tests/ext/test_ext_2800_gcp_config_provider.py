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
E2800 - Module for testing Google Cloud Platform (GCP) config store.

These tests are part of the extended test suite and only run when
run_long_tests is enabled and when the following entries are also set:

    gcp_project_id
        GCP project ID used for the test resources.
    gcp_bucket_name
        Existing GCS bucket used to upload temporary config objects.
    gcp_object_prefix
        Base object prefix used to build temporary GCS object names for the
        test run. A run-specific suffix is appended automatically to make the
        final object names unique.
    gcp_secret_name
        Base name used to generate a unique temporary Secret Manager secret
        for the test run.

GCP authentication must be available through Application Default Credentials
(ADC).

The usual test environment supplies the Oracle Database connection parameters.
"""

import json
import uuid

import oracledb
import pytest

PYO_PARAMETERS = {
    "cclass": "pythontest_gcp",
    "connection_id_prefix": "my_connection_prefix",
    "disable_oob": "yes",
    "driver_name": "test_driver_name",
    "events": "yes",
    "expire_time": 1,
    "machine": "machine1",
    "matchanytag": "yes",
    "mode": "DEFAULT",
    "osuser": "username",
    "pool_boundary": "statement",
    "program": "python-application-name",
    "purity": "NEW",
    "stmtcachesize": 12,
    "tag": "mytag",
    "terminal": "myterminal",
    "getmode": "WAIT",
    "homogeneous": "yes",
    "increment": 2,
    "max": 5,
    "min": 2,
    "max_lifetime_session": 100,
    "ping_interval": 60,
    "ping_timeout": 5000,
    "soda_metadata_cache": "yes",
    "timeout": 4,
    "wait_timeout": 10,
}


def _assert_params_from_config(params_class, dsn, config):
    params = params_class()
    params.parse_connect_string(dsn)
    expected_params = params_class()
    expected_params.set_from_config(config)
    assert params == expected_params


class GcpConfig:
    """
    Manages GCP resources required by the GCP config store tests.
    """

    def __init__(self, test_env, extended_config):
        self.test_env = test_env
        self.extended_config = extended_config
        self.created_objects = []
        self.created_secret_paths = []
        self._load_setup_values()

    def _build_config(
        self, pyo=None, include_connect_descriptor=True, password=None
    ):
        config = {"user": self.test_env.main_user}
        if include_connect_descriptor:
            config["connect_descriptor"] = self.test_env.connect_string
        if password is not None:
            config["password"] = password
        if pyo is not None:
            config["pyo"] = pyo
        return config

    def _check_bucket(self):
        bucket = self.storage_client.lookup_bucket(self.bucket_name)
        if bucket is None:
            pytest.skip(f"GCP bucket {self.bucket_name} not found")

    def _create_clients(self):
        try:
            self.storage_client = self.storage.Client(project=self.project_id)
            self.secret_client = (
                self.secretmanager.SecretManagerServiceClient()
            )
        except Exception as exc:
            pytest.skip(f"GCP ADC/setup not available: {exc}")

    def _create_config_secret_dsn(self, secret_name, config, key=None):
        if not isinstance(config, str):
            config = json.dumps(config, indent=4)
        resource_name = self._create_text_secret(secret_name, config)
        return self.build_secretmanager_dsn(resource_name, key)

    def _create_secretmanager_configs(self):
        password_secret_ref = self._create_text_secret(
            f"{self.base_secret_name}-{self.run_id}-pwd",
            self.test_env.main_password,
        )
        password_dict = {
            "type": "gcpsecretmanager",
            "value": password_secret_ref,
        }
        self.config = self._build_config(
            PYO_PARAMETERS,
            password=password_dict,
        )
        self.missing_cd_config = self._build_config(
            PYO_PARAMETERS,
            include_connect_descriptor=False,
            password=password_dict,
        )
        self.plaintext_pwd_config = self._build_config(password="not_okay")
        self.keyed_config = {
            "config_alias": self.config,
            "not_an_object": "hello",
        }

        self.config_secret_dsn = self._create_config_secret_dsn(
            f"{self.base_secret_name}-{self.run_id}-cfg",
            self.config,
        )
        self.invalid_json_secret_dsn = self._create_config_secret_dsn(
            f"{self.base_secret_name}-{self.run_id}-cfg-invalid-json",
            "{invalid-json",
        )
        self.missing_cd_secret_dsn = self._create_config_secret_dsn(
            f"{self.base_secret_name}-{self.run_id}-cfg-missing-cd",
            self.missing_cd_config,
        )
        self.plaintext_pwd_secret_dsn = self._create_config_secret_dsn(
            f"{self.base_secret_name}-{self.run_id}-cfg-plaintext-pwd",
            self.plaintext_pwd_config,
        )

        keyed_secret_name = f"{self.base_secret_name}-{self.run_id}-cfg-keyed"
        keyed_secret_resource = self._create_text_secret(
            keyed_secret_name,
            json.dumps(self.keyed_config, indent=4),
        )
        self.keyed_secret_resource = keyed_secret_resource
        self.keyed_config_secret_dsn = self.build_secretmanager_dsn(
            keyed_secret_resource, "config_alias"
        )
        self.keyed_bad_target_secret_dsn = self.build_secretmanager_dsn(
            keyed_secret_resource, "not_an_object"
        )

    def _create_text_secret(self, secret_name, text):
        secret_path = self.secret_client.secret_path(
            self.project_id, secret_name
        )
        try:
            self.secret_client.create_secret(
                request={
                    "parent": f"projects/{self.project_id}",
                    "secret_id": secret_name,
                    "secret": {"replication": {"automatic": {}}},
                }
            )
        except self.permission_denied_error as exc:
            pytest.skip(
                "GCP Secret Manager create/delete permissions are required "
                f"for these tests: {exc}"
            )

        self.created_secret_paths.append(secret_path)

        self.secret_client.add_secret_version(
            request={
                "parent": secret_path,
                "payload": {"data": text.encode("utf-8")},
            }
        )

        return f"{secret_path}/versions/latest"

    def _import_gcp_modules(self):
        try:
            from google.api_core.exceptions import PermissionDenied
            from google.cloud import secretmanager, storage
        except ImportError as exc:
            pytest.skip(
                f"GCP config store requirements are not available: {exc}"
            )

        self.permission_denied_error = PermissionDenied
        self.secretmanager = secretmanager
        self.storage = storage

    def _init_resource_names(self):
        self.run_id = uuid.uuid4().hex[:16]
        self.config_object_name = self._object_name("config")
        self.invalid_json_object_name = self._object_name("invalid_json")
        self.missing_cd_object_name = self._object_name(
            "missing_connect_descriptor"
        )
        self.plaintext_pwd_object_name = self._object_name(
            "plaintext_password"
        )
        self.keyed_object_name = self._object_name("keyed")
        self.config_dsn = self.build_config_dsn(self.config_object_name)
        self.invalid_json_dsn = self.build_config_dsn(
            self.invalid_json_object_name
        )
        self.missing_cd_dsn = self.build_config_dsn(
            self.missing_cd_object_name
        )
        self.plaintext_pwd_dsn = self.build_config_dsn(
            self.plaintext_pwd_object_name
        )
        self.keyed_config_dsn = self.build_config_dsn(
            self.keyed_object_name, "config_alias"
        )
        self.keyed_bad_target_dsn = self.build_config_dsn(
            self.keyed_object_name, "not_an_object"
        )

    def _load_setup_values(self):
        self.project_id = self.extended_config.get_str_value("gcp_project_id")
        self.bucket_name = self.extended_config.get_str_value(
            "gcp_bucket_name"
        )
        self.object_prefix = self.extended_config.get_str_value(
            "gcp_object_prefix"
        )
        self.base_secret_name = self.extended_config.get_str_value(
            "gcp_secret_name"
        )
        if (
            not self.project_id
            or not self.bucket_name
            or not self.object_prefix
            or not self.base_secret_name
        ):
            pytest.skip("GCP config store setup not provided")

    def _object_name(self, suffix):
        return f"{self.object_prefix}_{self.run_id}_{suffix}.json"

    def _upload_config_object(self, object_name, config):
        """
        Upload a test configuration object and register it for cleanup.
        """
        if not isinstance(config, str):
            config = json.dumps(config, indent=4)
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(object_name)
        blob.upload_from_string(config, content_type="application/json")
        self.created_objects.append(object_name)

    def _upload_config_objects(self):
        self._upload_config_object(self.config_object_name, self.config)
        self._upload_config_object(
            self.invalid_json_object_name, "{invalid-json"
        )
        self._upload_config_object(
            self.missing_cd_object_name, self.missing_cd_config
        )
        self._upload_config_object(
            self.plaintext_pwd_object_name, self.plaintext_pwd_config
        )
        self._upload_config_object(self.keyed_object_name, self.keyed_config)

    def build_config_dsn(self, object_name, key=None):
        """
        Return a GCP config-store DSN for the given GCS object.
        """
        dsn = (
            "config-gcpstorage://"
            f"project={self.project_id};"
            f"bucket={self.bucket_name};"
            f"object={object_name}"
        )
        if key is not None:
            dsn += f"?key={key}"
        return dsn

    def build_secretmanager_dsn(self, resource_name, key=None):
        dsn = f"config-gcpsecretmanager://{resource_name}"
        if key is not None:
            dsn += f"?key={key}"
        return dsn

    def cleanup(self):
        """
        Remove GCS objects and Secret Manager secret created for the tests.
        """
        cleanup_errors = []

        for object_name in self.created_objects:
            try:
                bucket = self.storage_client.bucket(self.bucket_name)
                blob = bucket.blob(object_name)
                blob.delete()
            except Exception as exc:
                cleanup_errors.append(f"GCS object {object_name!r}: {exc!r}")

        for secret_path in self.created_secret_paths:
            try:
                self.secret_client.delete_secret(request={"name": secret_path})
            except Exception as exc:
                cleanup_errors.append(
                    f"Secret Manager secret {secret_path!r}: {exc!r}"
                )

        if cleanup_errors:
            raise RuntimeError(
                "Errors occurred while cleaning up GCP test resources: "
                + "; ".join(cleanup_errors)
            )

    def setup(self):
        """
        Create GCP resources and upload config objects used by the tests.
        """
        self._import_gcp_modules()
        self._create_clients()
        self._check_bucket()
        self._init_resource_names()
        self._create_secretmanager_configs()
        self._upload_config_objects()


@pytest.fixture(scope="module")
def gcp_setup(test_env, extended_config):
    config = GcpConfig(test_env, extended_config)
    config.setup()
    yield config
    config.cleanup()


@pytest.fixture(autouse=True)
def module_checks(skip_unless_run_long_tests):
    try:
        import oracledb.plugins.gcp_config_provider  # noqa: F401
    except ImportError as exc:
        pytest.skip(f"GCP config store requirements are not available: {exc}")


def test_ext_2800(gcp_setup):
    "E2800 - connect to DB using GCP config store"
    _assert_params_from_config(
        oracledb.ConnectParams, gcp_setup.config_dsn, gcp_setup.config
    )
    with oracledb.connect(dsn=gcp_setup.config_dsn):
        pass


def test_ext_2801(gcp_setup):
    "E2801 - create pool using GCP config store"
    _assert_params_from_config(
        oracledb.PoolParams, gcp_setup.config_dsn, gcp_setup.config
    )
    pool = oracledb.create_pool(dsn=gcp_setup.config_dsn)
    with pool.acquire():
        pass
    pool.close()


@pytest.mark.parametrize(
    "dsn",
    [
        "config-gcpstorage://bucket=test-bucket;object=config.json",
        "config-gcpstorage://project=test-project;object=config.json",
        "config-gcpstorage://project=test-project;bucket=test-bucket",
        "config-gcpstorage://project=test-project;bucket;object=config.json",
        "config-gcpstorage://",
    ],
)
def test_ext_2802(test_env, dsn):
    "E2802 - test invalid GCP config DSN values"
    connect_params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        connect_params.parse_connect_string(dsn)


def test_ext_2803(test_env, gcp_setup):
    "E2803 - test invalid connection string pointing to invalid JSON"
    connect_params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        connect_params.parse_connect_string(gcp_setup.invalid_json_dsn)


def test_ext_2804(test_env, gcp_setup):
    "E2804 - test missing connect_descriptor in GCP config store"
    connect_params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        connect_params.parse_connect_string(gcp_setup.missing_cd_dsn)


def test_ext_2805(test_env, gcp_setup):
    "E2805 - test plaintext password in config is rejected"
    with test_env.assert_raises_from_cause("DPY-2056", "DPY-2058"):
        connect_params = oracledb.ConnectParams()
        connect_params.parse_connect_string(gcp_setup.plaintext_pwd_dsn)


def test_ext_2806(gcp_setup):
    "E2806 - connect to DB using keyed GCP config"
    _assert_params_from_config(
        oracledb.ConnectParams, gcp_setup.keyed_config_dsn, gcp_setup.config
    )
    with oracledb.connect(dsn=gcp_setup.keyed_config_dsn):
        pass


def test_ext_2807(test_env, gcp_setup):
    "E2807 - test missing key in GCP config object"
    missing_key_dsn = gcp_setup.build_config_dsn(
        gcp_setup.keyed_object_name, "missing_alias"
    )
    connect_params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        connect_params.parse_connect_string(missing_key_dsn)


def test_ext_2808(test_env, gcp_setup):
    "E2808 - test key in GCP config object must map to a JSON object"
    connect_params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        connect_params.parse_connect_string(gcp_setup.keyed_bad_target_dsn)


def test_ext_2809(test_env, gcp_setup):
    "E2809 - test unsupported GCP query parameter"
    bad_dsn = (
        gcp_setup.build_config_dsn(gcp_setup.keyed_object_name) + "?foo=bar"
    )
    connect_params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        connect_params.parse_connect_string(bad_dsn)


def test_ext_2810(gcp_setup):
    "E2810 - connect to DB using GCP Secret Manager config store"
    _assert_params_from_config(
        oracledb.ConnectParams, gcp_setup.config_secret_dsn, gcp_setup.config
    )
    with oracledb.connect(dsn=gcp_setup.config_secret_dsn):
        pass


def test_ext_2811(gcp_setup):
    "E2811 - create pool using GCP Secret Manager config store"
    _assert_params_from_config(
        oracledb.PoolParams, gcp_setup.config_secret_dsn, gcp_setup.config
    )
    pool = oracledb.create_pool(dsn=gcp_setup.config_secret_dsn)
    with pool.acquire():
        pass
    pool.close()


@pytest.mark.parametrize(
    "dsn",
    [
        "config-gcpsecretmanager://",
        "config-gcpsecretmanager://?key=alias1",
    ],
)
def test_ext_2812(test_env, dsn):
    "E2812 - test invalid GCP Secret Manager config DSN values"
    connect_params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        connect_params.parse_connect_string(dsn)


def test_ext_2813(test_env, gcp_setup):
    "E2813 - test invalid JSON in GCP Secret Manager config store"
    connect_params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        connect_params.parse_connect_string(gcp_setup.invalid_json_secret_dsn)


def test_ext_2814(test_env, gcp_setup):
    "E2814 - test missing connect_descriptor in GCP Secret Manager config store"
    connect_params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        connect_params.parse_connect_string(gcp_setup.missing_cd_secret_dsn)


def test_ext_2815(test_env, gcp_setup):
    "E2815 - test plaintext password in Secret Manager config is rejected"
    with test_env.assert_raises_from_cause("DPY-2056", "DPY-2058"):
        connect_params = oracledb.ConnectParams()
        connect_params.parse_connect_string(gcp_setup.plaintext_pwd_secret_dsn)


def test_ext_2816(gcp_setup):
    "E2816 - connect to DB using keyed GCP Secret Manager config"
    _assert_params_from_config(
        oracledb.ConnectParams,
        gcp_setup.keyed_config_secret_dsn,
        gcp_setup.config,
    )
    with oracledb.connect(dsn=gcp_setup.keyed_config_secret_dsn):
        pass


def test_ext_2817(test_env, gcp_setup):
    "E2817 - test missing key in GCP Secret Manager config object"
    missing_key_dsn = gcp_setup.build_secretmanager_dsn(
        gcp_setup.keyed_secret_resource, "missing_alias"
    )
    connect_params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        connect_params.parse_connect_string(missing_key_dsn)


def test_ext_2818(test_env, gcp_setup):
    "E2818 - test key in GCP Secret Manager config must map to a JSON object"
    connect_params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        connect_params.parse_connect_string(
            gcp_setup.keyed_bad_target_secret_dsn
        )


def test_ext_2819(test_env, gcp_setup):
    "E2819 - test unsupported GCP Secret Manager query parameter"
    bad_dsn = (
        gcp_setup.build_secretmanager_dsn(gcp_setup.keyed_secret_resource)
        + "?foo=bar"
    )
    connect_params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        connect_params.parse_connect_string(bad_dsn)
