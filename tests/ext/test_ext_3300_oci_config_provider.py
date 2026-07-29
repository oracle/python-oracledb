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
E3300 - Module for testing the OCI Object Storage config provider.

These tests are part of the extended test suite and only run when
run_long_tests is enabled and when the following entries are also set:

    oci_config_file
        OCI SDK config file used for authentication. This defaults to
        ~/.oci/config when not set.
    oci_profile
        OCI SDK config profile used for authentication. This defaults to
        DEFAULT when not set.
    oci_namespace
        OCI Object Storage namespace for the test bucket. This can be left
        empty when the authenticated user can look up the namespace.
    oci_bucket_name
        Existing OCI Object Storage bucket used to upload temporary config
        objects.
    oci_compartment_id
        OCI compartment OCID used to create the temporary Vault secret.
    oci_vault_id
        OCI Vault OCID used to create the temporary password secret.
    oci_key_id
        OCI Vault encryption key OCID used for the temporary password secret.

OCI authentication must be available through the configured SDK config file
and profile. The credentials must allow creating/deleting Object Storage
objects and creating/scheduling deletion of Vault secrets.

The usual test environment supplies the Oracle Database connection parameters.
"""

import base64
import json
import os
import uuid
from urllib.parse import quote

import oracledb
import pytest

PYO_PARAMETERS = {
    "cclass": "pythontest_oci",
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


def _build_query(**kwargs):
    return "&".join(
        f"{key}={quote(str(value), safe='')}"
        for key, value in kwargs.items()
        if value is not None
    )


class OciConfig:
    """
    Manages temporary OCI resources for the config-store tests.
    """

    def __init__(self, test_env, extended_config):
        self.connect_descriptor = test_env.connect_string
        self.db_password = test_env.main_password
        self.db_user = test_env.main_user
        self.created_objects = []
        self.secret_ids = []
        self._load_setup_values(extended_config)

    def _auth_query_args(self):
        return dict(
            authentication="OCI_DEFAULT",
            oci_tenancy=self.config_auth_params["tenancy"],
            oci_user=self.config_auth_params["user"],
            oci_fingerprint=self.config_auth_params["fingerprint"],
            oci_key_file=self.config_auth_params["key_file"],
            oci_region=self.config_auth_params["region"],
            oci_profile_path=self.config_file,
            oci_profile=self.profile_name,
        )

    def _build_config(
        self, pyo=None, include_connect_descriptor=True, password=None
    ):
        config = dict(user=self.db_user)
        if include_connect_descriptor:
            config["connect_descriptor"] = self.connect_descriptor
        if password is not None:
            config["password"] = password
        if pyo is not None:
            config["pyo"] = pyo
        return config

    def _create_clients(self):
        self.object_storage_client = (
            self.oci.object_storage.ObjectStorageClient(
                config=self.config_auth_params
            )
        )
        self.vaults_client = self.oci.vault.VaultsClient(
            config=self.config_auth_params
        )
        self.vaults_composite_client = (
            self.oci.vault.VaultsClientCompositeOperations(self.vaults_client)
        )

    def _create_password_secret(self):
        secret_name = f"python-oracledb-live-oci-password-{self.run_id}"
        encoded_password = base64.b64encode(
            self.db_password.encode("utf-8")
        ).decode("ascii")
        secret_content = self.oci.vault.models.Base64SecretContentDetails(
            content_type="BASE64",
            content=encoded_password,
            stage="CURRENT",
        )
        details = self.oci.vault.models.CreateSecretDetails(
            compartment_id=self.compartment_id,
            secret_name=secret_name,
            vault_id=self.vault_id,
            key_id=self.key_id,
            secret_content=secret_content,
            description="Temporary python-oracledb OCI config-store secret",
        )
        response = (
            self.vaults_composite_client.create_secret_and_wait_for_state(
                details,
                wait_for_states=["ACTIVE"],
                waiter_kwargs=dict(
                    max_wait_seconds=90, max_interval_seconds=5
                ),
            )
        )
        self.password_secret_id = response.data.id
        self.secret_ids.append(self.password_secret_id)

    def _import_oci_modules(self):
        try:
            import oci
        except ImportError as error:
            pytest.skip(f"OCI config store requirements not found: {error}")
        self.oci = oci

    def _init_resource_names(self):
        self.run_id = uuid.uuid4().hex[:16]
        self.config_object_name = self._object_name("config")
        self.invalid_json_object_name = self._object_name("invalid_json")
        self.missing_cd_object_name = self._object_name("missing_cd")
        self.plaintext_password_object_name = self._object_name(
            "plaintext_password"
        )
        self.keyed_object_name = self._object_name("keyed")
        self.missing_object_name = self._object_name("missing_object")
        query = _build_query(**self._auth_query_args())
        self.missing_namespace_dsn = (
            f"config-ociobject://{self.object_storage_host}/b/"
            f"{self.bucket_name}/o/{self.config_object_name}?{query}"
        )
        self.missing_bucket_dsn = (
            f"config-ociobject://{self.object_storage_host}/n/"
            f"{self.namespace_name}/o/{self.config_object_name}?{query}"
        )
        self.missing_object_dsn = (
            f"config-ociobject://{self.object_storage_host}/n/"
            f"{self.namespace_name}/b/{self.bucket_name}?{query}"
        )
        self.malformed_bucket_dsn = (
            f"config-ociobject://{self.object_storage_host}/n/"
            f"{self.namespace_name}/b/bad/bucket/o/"
            f"{self.config_object_name}?{query}"
        )
        self.empty_resource_dsn = f"config-ociobject://?{query}"
        self.bucket_not_found_dsn = self.build_config_dsn(
            self.config_object_name,
            bucket_name=f"missing-bucket-{self.run_id}",
        )
        self.object_not_found_dsn = self.build_config_dsn(
            self.missing_object_name
        )

    def _load_auth_config(self):
        self.config_auth_params = self.oci.config.from_file(
            file_location=self.config_file,
            profile_name=self.profile_name,
        )
        self._normalize_key_file()
        self.oci.config.validate_config(self.config_auth_params)

    def _load_setup_values(self, extended_config):
        self.config_file = extended_config.get_str_value(
            "oci_config_file", "~/.oci/config"
        )
        self.profile_name = extended_config.get_str_value(
            "oci_profile", "DEFAULT"
        )
        self.namespace_name = extended_config.get_str_value("oci_namespace")
        self.bucket_name = extended_config.get_str_value("oci_bucket_name")
        self.compartment_id = extended_config.get_str_value(
            "oci_compartment_id"
        )
        self.vault_id = extended_config.get_str_value("oci_vault_id")
        self.key_id = extended_config.get_str_value("oci_key_id")
        self.object_prefix = extended_config.get_str_value(
            "oci_object_prefix", "python_oracledb_live_oci"
        ).strip("_")
        if (
            not self.bucket_name
            or not self.compartment_id
            or not self.vault_id
            or not self.key_id
        ):
            pytest.skip("OCI config store setup not provided")

    def _normalize_key_file(self):
        key_file = os.path.expanduser(self.config_auth_params["key_file"])
        if not os.path.isabs(key_file):
            config_dir = os.path.dirname(
                os.path.abspath(os.path.expanduser(self.config_file))
            )
            key_file = os.path.join(config_dir, key_file)
        self.config_auth_params["key_file"] = key_file

    def _object_name(self, suffix):
        return f"{self.object_prefix}_{self.run_id}_{suffix}.json"

    def _set_namespace_if_needed(self):
        if self.namespace_name:
            return
        response = self.object_storage_client.get_namespace()
        self.namespace_name = response.data

    def _upload_config_object(self, object_name, config):
        """
        Upload a test configuration object and register it for cleanup.
        """
        if not isinstance(config, str):
            config = json.dumps(config)
        self.object_storage_client.put_object(
            namespace_name=self.namespace_name,
            bucket_name=self.bucket_name,
            object_name=object_name,
            put_object_body=config.encode("utf-8"),
        )
        self.created_objects.append(object_name)

    def _upload_config_objects(self):
        password_auth = dict(
            method="OCI_DEFAULT",
            oci_profile_path=self.config_file,
            oci_profile=self.profile_name,
        )
        password_config = dict(
            type="ocivault",
            value=self.password_secret_id,
            authentication=password_auth,
        )
        self.config = self._build_config(
            PYO_PARAMETERS, password=password_config
        )
        self.missing_cd_config = self._build_config(
            PYO_PARAMETERS,
            include_connect_descriptor=False,
            password=password_config,
        )
        self.plaintext_password_config = self._build_config(
            password="not-a-real-password"
        )
        self.keyed_config = dict(
            config_alias=self.config,
            not_an_object="not-a-config-object",
        )
        self._upload_config_object(self.config_object_name, self.config)
        self._upload_config_object(
            self.invalid_json_object_name, "{invalid-json"
        )
        self._upload_config_object(
            self.missing_cd_object_name, self.missing_cd_config
        )
        self._upload_config_object(
            self.plaintext_password_object_name,
            self.plaintext_password_config,
        )
        self._upload_config_object(self.keyed_object_name, self.keyed_config)
        self.config_dsn = self.build_config_dsn(self.config_object_name)
        self.invalid_json_dsn = self.build_config_dsn(
            self.invalid_json_object_name
        )
        self.missing_cd_dsn = self.build_config_dsn(
            self.missing_cd_object_name
        )
        self.plaintext_password_dsn = self.build_config_dsn(
            self.plaintext_password_object_name
        )
        self.keyed_config_dsn = self.build_config_dsn(
            self.keyed_object_name, alias="config_alias"
        )
        self.keyed_bad_target_dsn = self.build_config_dsn(
            self.keyed_object_name, alias="not_an_object"
        )

    def build_config_dsn(
        self,
        object_name,
        alias=None,
        namespace_name=None,
        bucket_name=None,
        **kwargs,
    ):
        namespace_name = (
            self.namespace_name if namespace_name is None else (namespace_name)
        )
        bucket_name = self.bucket_name if bucket_name is None else bucket_name
        resource = (
            f"{self.object_storage_host}/n/{namespace_name}/b/{bucket_name}"
            f"/o/{object_name}"
        )
        if alias is not None:
            resource += f"/c/{alias}"
        query_args = self._auth_query_args()
        query_args.update(kwargs)
        return f"config-ociobject://{resource}?{_build_query(**query_args)}"

    def cleanup(self):
        """
        Remove OCI Object Storage objects and schedule Vault secret deletion.
        """
        cleanup_errors = []
        if hasattr(self, "object_storage_client"):
            for object_name in reversed(self.created_objects):
                try:
                    self.object_storage_client.delete_object(
                        namespace_name=self.namespace_name,
                        bucket_name=self.bucket_name,
                        object_name=object_name,
                    )
                except Exception as error:
                    cleanup_errors.append(
                        f"OCI object {object_name!r}: {error!r}"
                    )
        if hasattr(self, "vaults_client"):
            vault_models = self.oci.vault.models
            for secret_id in self.secret_ids:
                try:
                    details = vault_models.ScheduleSecretDeletionDetails()
                    self.vaults_client.schedule_secret_deletion(
                        secret_id, details
                    )
                except Exception as error:
                    cleanup_errors.append(
                        f"OCI Vault secret {secret_id!r}: {error!r}"
                    )
        if cleanup_errors:
            raise RuntimeError(
                "Errors occurred while cleaning up OCI test resources: "
                + "; ".join(cleanup_errors)
            )
        self.created_objects.clear()
        self.secret_ids.clear()

    def setup(self, set_oci_provider_config_file):
        """
        Create OCI resources and upload config objects used by the tests.
        """
        self._import_oci_modules()
        self._load_auth_config()
        self.object_storage_host = (
            f"objectstorage.{self.config_auth_params['region']}"
            ".oraclecloud.com"
        )
        set_oci_provider_config_file(self.config_auth_params)
        self._create_clients()
        self._set_namespace_if_needed()
        self._init_resource_names()
        self._create_password_secret()
        self._upload_config_objects()


@pytest.fixture(scope="module", autouse=True)
def module_checks(extended_config):
    if not extended_config.get_bool_value("run_long_tests"):
        pytest.skip("extended configuration run_long_tests is disabled")
    try:
        import oracledb.plugins.oci_config_provider  # noqa: F401
    except ImportError as error:
        pytest.skip(
            f"OCI config store requirements are not available: " f"{error}"
        )


@pytest.fixture(scope="module")
def set_oci_provider_config_file(tmp_path_factory):
    previous_oci_config_file = os.environ.get("OCI_CONFIG_FILE")
    config_dir = tmp_path_factory.mktemp("python_oracledb_oci_config")
    file_name = config_dir / "config"

    def set_provider_config_file(config_auth_params):
        with file_name.open("w") as file:
            file.write("[DEFAULT]\n")
            for key in (
                "user",
                "fingerprint",
                "tenancy",
                "region",
                "key_file",
                "pass_phrase",
            ):
                value = config_auth_params.get(key)
                if value is not None:
                    file.write(f"{key}={value}\n")
        os.chmod(file_name, 0o600)
        os.environ["OCI_CONFIG_FILE"] = str(file_name)

    yield set_provider_config_file
    if previous_oci_config_file is None:
        os.environ.pop("OCI_CONFIG_FILE", None)
    else:
        os.environ["OCI_CONFIG_FILE"] = previous_oci_config_file


@pytest.fixture(scope="module")
def oci_config(test_env, extended_config, set_oci_provider_config_file):
    config = OciConfig(test_env, extended_config)
    config.setup(set_oci_provider_config_file)
    yield config
    config.cleanup()


def test_ext_3300(oci_config):
    "E3300 - connect to DB using OCI config store"
    with oracledb.connect(dsn=oci_config.config_dsn):
        pass


def test_ext_3301(oci_config):
    "E3301 - create pool using OCI config store"
    pool = oracledb.create_pool(dsn=oci_config.config_dsn)
    try:
        with pool.acquire():
            pass
    finally:
        pool.close()


@pytest.mark.parametrize(
    "params_class",
    [
        pytest.param(oracledb.ConnectParams, id="connect"),
        pytest.param(oracledb.PoolParams, id="pool"),
    ],
)
def test_ext_3302(oci_config, params_class):
    "E3302 - compare OCI config parameters"
    params = params_class()
    params.parse_connect_string(oci_config.config_dsn)
    expected_params = params_class()
    expected_params.set_from_config(oci_config.config)
    assert params == expected_params


@pytest.mark.parametrize(
    "dsn_attr",
    [
        pytest.param("missing_namespace_dsn", id="missing-namespace"),
        pytest.param("missing_bucket_dsn", id="missing-bucket"),
        pytest.param("missing_object_dsn", id="missing-object"),
        pytest.param("malformed_bucket_dsn", id="malformed-bucket"),
        pytest.param("empty_resource_dsn", id="empty-resource"),
        pytest.param("bucket_not_found_dsn", id="bucket-not-found"),
        pytest.param("object_not_found_dsn", id="object-not-found"),
    ],
)
def test_ext_3303(test_env, oci_config, dsn_attr):
    "E3303 - invalid OCI Object Storage DSN/resource values"
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        params.parse_connect_string(getattr(oci_config, dsn_attr))


def test_ext_3304(test_env, oci_config):
    "E3304 - invalid JSON object in OCI Object Storage"
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        params.parse_connect_string(oci_config.invalid_json_dsn)


def test_ext_3305(test_env, oci_config):
    "E3305 - missing connect_descriptor in OCI config store"
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        params.parse_connect_string(oci_config.missing_cd_dsn)


def test_ext_3306(test_env, oci_config):
    "E3306 - plain-text password in OCI config store is rejected"
    with test_env.assert_raises_from_cause("DPY-2056", "DPY-2058"):
        params = oracledb.ConnectParams()
        params.parse_connect_string(oci_config.plaintext_password_dsn)


def test_ext_3307(oci_config):
    "E3307 - connect to DB using keyed OCI config"
    with oracledb.connect(dsn=oci_config.keyed_config_dsn):
        pass


def test_ext_3308(test_env, oci_config):
    "E3308 - missing OCI config object alias"
    dsn = oci_config.build_config_dsn(
        oci_config.keyed_object_name, alias="missing_alias"
    )
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        params.parse_connect_string(dsn)


def test_ext_3309(test_env, oci_config):
    "E3309 - OCI config alias maps to text"
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        params.parse_connect_string(oci_config.keyed_bad_target_dsn)


@pytest.mark.parametrize(
    "params_class",
    [
        pytest.param(oracledb.ConnectParams, id="connect"),
        pytest.param(oracledb.PoolParams, id="pool"),
    ],
)
def test_ext_3310(oci_config, params_class):
    "E3310 - extra OCI config query parameter is ignored"
    dsn = oci_config.build_config_dsn(oci_config.config_object_name, foo="bar")
    params = params_class()
    params.parse_connect_string(dsn)
    expected_params = params_class()
    expected_params.set_from_config(oci_config.config)
    assert params == expected_params


def test_ext_3311(test_env, oci_config):
    "E3311 - bad OCI config DSN string"
    dsn = (
        f"config-ociobject://{oci_config.object_storage_host}/"
        f"{oci_config.config_object_name}"
        f"?{_build_query(**oci_config._auth_query_args())}"
    )
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        params.parse_connect_string(dsn)


def test_ext_3312(test_env):
    "E3312 - invalid OCI config hook protocol"
    dsn = "config-ocix://objectstorage.us-ashburn-1.oraclecloud.com"
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-4021"):
        params.parse_connect_string(dsn)


def test_ext_3313(test_env, oci_config):
    "E3313 - query key syntax is not used for OCI aliases"
    dsn = oci_config.build_config_dsn(
        oci_config.keyed_object_name, key="config_alias"
    )
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        params.parse_connect_string(dsn)
