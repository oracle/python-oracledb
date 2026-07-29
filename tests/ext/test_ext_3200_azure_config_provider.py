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
E3200 - Module for testing the Azure App Configuration provider.

These tests are part of the extended test suite and only run when
run_long_tests is enabled and when the following entries are also set:

    azure_app_config_host
        Azure App Configuration host used with service-principal
        authentication.
    azure_vault_url
        Azure Key Vault URL used to create a temporary password secret.
    azure_client_id
        Azure service principal client ID.
    azure_client_secret
        Azure service principal client secret.
    azure_tenant_id
        Azure tenant ID for the service principal.

Azure authentication uses the configured service principal. The credentials
must allow creating/deleting Azure App Configuration settings and Key Vault
secrets.

The usual test environment supplies the Oracle Database connection parameters.
"""

import json
import uuid
from urllib.parse import quote

import oracledb
import pytest

KEY_VAULT_CONTENT_TYPE = (
    "application/vnd.microsoft.appconfig.keyvaultref+json;charset=utf-8"
)

PYO_PARAMETERS = {
    "cclass": "pythontest_azure",
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


class AzureConfig:
    """
    Manages temporary Azure resources for the config-store tests.
    """

    def __init__(self, test_env, extended_config):
        self.extended_config = extended_config
        self.connect_descriptor = test_env.connect_string
        self.db_password = test_env.main_password
        self.db_user = test_env.main_user
        self.created_settings = []
        self.secret_names = []
        self._load_setup_values()

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
        self.credential = self.ClientSecretCredential(
            tenant_id=self.azure_tenant_id,
            client_id=self.azure_client_id,
            client_secret=self.azure_client_secret,
        )
        self.app_config_client = self.AzureAppConfigurationClient(
            base_url=self.app_config_base_url,
            credential=self.credential,
        )
        self.secret_client = self.SecretClient(
            vault_url=self.vault_url,
            credential=self.credential,
        )

    def _create_password_secret(self):
        secret_name = f"python-oracledb-live-azure-password-{self.run_id}"
        self.secret_client.set_secret(secret_name, self.db_password)
        self.secret_names.append(secret_name)
        self.password_secret_uri = f"{self.vault_url}/secrets/{secret_name}"

    def _import_azure_modules(self):
        try:
            from azure.appconfiguration import (
                AzureAppConfigurationClient,
                ConfigurationSetting,
            )
            from azure.core.exceptions import (
                ResourceNotFoundError,
            )
            from azure.identity import ClientSecretCredential
            from azure.keyvault.secrets import SecretClient
        except ImportError as error:
            pytest.skip(f"Azure config store requirements not found: {error}")
        self.AzureAppConfigurationClient = AzureAppConfigurationClient
        self.ClientSecretCredential = ClientSecretCredential
        self.ConfigurationSetting = ConfigurationSetting
        self.ResourceNotFoundError = ResourceNotFoundError
        self.SecretClient = SecretClient

    def _init_resource_names(self):
        self.run_id = uuid.uuid4().hex[:16]
        self.config_key = self._key_prefix("config")
        self.invalid_json_key = self._key_prefix("invalid-json")
        self.missing_cd_key = self._key_prefix("missing-cd")
        self.plaintext_password_key = self._key_prefix("plaintext-password")
        self.text_setting_key = self._key_prefix("text-setting")
        self.config_dsn = self.build_config_dsn(self._dsn_key(self.config_key))
        self.invalid_json_dsn = self.build_config_dsn(
            self._dsn_key(self.invalid_json_key)
        )
        self.missing_cd_dsn = self.build_config_dsn(
            self._dsn_key(self.missing_cd_key)
        )
        self.plaintext_password_dsn = self.build_config_dsn(
            self._dsn_key(self.plaintext_password_key)
        )
        self.text_setting_dsn = self.build_config_dsn(self.text_setting_key)

    def _dsn_key(self, key_prefix):
        return f"{key_prefix.rstrip('/')}/"

    def _key_prefix(self, name):
        return f"{self.base_key_prefix}/{name}-{self.run_id}"

    def _load_setup_values(self):
        self.app_config_host = self.extended_config.get_str_value(
            "azure_app_config_host"
        )
        self.vault_url = self.extended_config.get_str_value("azure_vault_url")
        self.azure_client_id = self.extended_config.get_str_value(
            "azure_client_id"
        )
        self.azure_client_secret = self.extended_config.get_str_value(
            "azure_client_secret"
        )
        self.azure_tenant_id = self.extended_config.get_str_value(
            "azure_tenant_id"
        )
        self.base_key_prefix = self.extended_config.get_str_value(
            "azure_key_prefix", "python-oracledb-live/azure"
        ).rstrip("/")
        if (
            not self.app_config_host
            or not self.vault_url
            or not self.azure_client_id
            or not self.azure_client_secret
            or not self.azure_tenant_id
        ):
            pytest.skip("Azure config store setup not provided")
        self.app_config_host = self.app_config_host.strip()
        self.app_config_base_url = f"https://{self.app_config_host}"
        self.vault_url = self.vault_url.strip().rstrip("/")

    def _setting_value(self, key, value):
        content_type = None
        tags = None
        if key == "password" and isinstance(value, dict):
            value = json.dumps(dict(uri=value["value"]))
            content_type = KEY_VAULT_CONTENT_TYPE
            tags = dict(source="keyvault")
        elif key == "pyo" and isinstance(value, dict):
            value = json.dumps(value)
        return value, content_type, tags

    def _set_setting(
        self, key, value, label=None, content_type=None, tags=None
    ):
        setting = self.ConfigurationSetting(
            key=key,
            value=value,
            label=label,
            content_type=content_type,
            tags=tags,
        )
        self.app_config_client.set_configuration_setting(setting)
        self.created_settings.append((key, label))

    def _upload_config(self, key_prefix, config, label=None):
        key_prefix = key_prefix.rstrip("/")
        for name in ("connect_descriptor", "user", "password", "pyo"):
            if name not in config:
                continue
            value, content_type, tags = self._setting_value(name, config[name])
            self._set_setting(
                f"{key_prefix}/{name}",
                value,
                label=label,
                content_type=content_type,
                tags=tags,
            )

    def _upload_configs(self):
        auth_config = dict(
            azure_client_id=self.azure_client_id,
            azure_client_secret=self.azure_client_secret,
            azure_tenant_id=self.azure_tenant_id,
        )
        password_config = dict(
            type="azurevault",
            value=self.password_secret_uri,
            authentication=auth_config,
        )
        self.config = self._build_config(
            PYO_PARAMETERS, password=password_config
        )
        self.invalid_json_config = self._build_config(
            password=password_config,
            pyo="{invalid-json",
        )
        self.missing_cd_config = self._build_config(
            PYO_PARAMETERS,
            include_connect_descriptor=False,
            password=password_config,
        )
        self.plaintext_password_config = self._build_config(
            password="not-a-real-password"
        )
        self._upload_config(self.config_key, self.config)
        self._upload_config(self.invalid_json_key, self.invalid_json_config)
        self._upload_config(self.missing_cd_key, self.missing_cd_config)
        self._upload_config(
            self.plaintext_password_key, self.plaintext_password_config
        )
        self._set_setting(self.text_setting_key, "not-a-config-object")

    def build_config_dsn(self, key_prefix, label=None, **kwargs):
        query_args = dict(
            key=key_prefix,
            azure_client_id=self.azure_client_id,
            azure_client_secret=self.azure_client_secret,
            azure_tenant_id=self.azure_tenant_id,
        )
        if label is not None:
            query_args["label"] = label
        query_args.update(kwargs)
        query = "&".join(
            f"{key}={quote(str(value), safe='')}"
            for key, value in query_args.items()
            if value is not None
        )
        return f"config-azure://{self.app_config_host}" f"?{query}"

    def cleanup(self):
        cleanup_errors = []
        if hasattr(self, "app_config_client"):
            for key, label in reversed(self.created_settings):
                try:
                    kwargs = dict(key=key)
                    if label is not None:
                        kwargs["label"] = label
                    self.app_config_client.delete_configuration_setting(
                        **kwargs
                    )
                except Exception as error:
                    if isinstance(error, self.ResourceNotFoundError):
                        continue
                    cleanup_errors.append(
                        f"Azure App Configuration key {key!r}: {error!r}"
                    )
        if hasattr(self, "secret_client"):
            for secret_name in self.secret_names:
                try:
                    poller = self.secret_client.begin_delete_secret(
                        secret_name
                    )
                    poller.wait()
                except Exception as error:
                    if isinstance(error, self.ResourceNotFoundError):
                        continue
                    cleanup_errors.append(
                        f"Azure Key Vault secret {secret_name!r}: "
                        f"{error!r}"
                    )
        if cleanup_errors:
            raise RuntimeError(
                "Errors occurred while cleaning up Azure test resources: "
                + "; ".join(cleanup_errors)
            )
        self.created_settings.clear()
        self.secret_names.clear()

    def setup(self):
        self._import_azure_modules()
        self._init_resource_names()
        self._create_clients()
        self._create_password_secret()
        self._upload_configs()


@pytest.fixture(scope="module", autouse=True)
def module_checks(extended_config):
    if not extended_config.get_bool_value("run_long_tests"):
        pytest.skip("extended configuration run_long_tests is disabled")
    try:
        import oracledb.plugins.azure_config_provider  # noqa: F401
    except ImportError as error:
        pytest.skip(
            f"Azure config store requirements are not available: {error}"
        )


@pytest.fixture(scope="module")
def azure_config(test_env, extended_config):
    config = AzureConfig(test_env, extended_config)
    config.setup()
    yield config
    config.cleanup()


def test_ext_3200(azure_config):
    "E3200 - connect to DB using Azure config store"
    with oracledb.connect(dsn=azure_config.config_dsn):
        pass


def test_ext_3201(azure_config):
    "E3201 - create pool using Azure config store"
    pool = oracledb.create_pool(dsn=azure_config.config_dsn)
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
def test_ext_3202(azure_config, params_class):
    "E3202 - compare Azure config parameters"
    params = params_class()
    params.parse_connect_string(azure_config.config_dsn)
    expected_params = params_class()
    expected_params.set_from_config(azure_config.config)
    assert params == expected_params


@pytest.mark.parametrize(
    "dsn",
    [
        "config-azure://",
        "config-azure://?key=pythontest/",
        "config-azure://example.azconfig.io",
        "config-azure://example.azconfig.io?key=",
        "config-azure://localhost/orclpdb1?key=pythontest/",
        "config-azure://example.azconfig.io?key=pythontest/",
        (
            "config-azure://example.azconfig.io?key=pythontest/"
            "&azure_client_id=client&azure_client_secret=secret"
        ),
        (
            "config-azure://example.azconfig.io?key=pythontest/"
            "&azure_client_id=client&azure_tenant_id=tenant"
        ),
        (
            "config-azure://example.azconfig.io?key=pythontest/"
            "&azure_client_secret=secret&azure_tenant_id=tenant"
        ),
    ],
)
def test_ext_3203(test_env, dsn):
    "E3203 - invalid Azure config DSN values"
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        params.parse_connect_string(dsn)


def test_ext_3204(test_env, azure_config):
    "E3204 - invalid JSON setting in Azure config store"
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        params.parse_connect_string(azure_config.invalid_json_dsn)


def test_ext_3205(test_env, azure_config):
    "E3205 - missing connect_descriptor in Azure config store"
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        params.parse_connect_string(azure_config.missing_cd_dsn)


def test_ext_3206(test_env, azure_config):
    "E3206 - plain-text password in Azure config store is rejected"
    with test_env.assert_raises_from_cause("DPY-2056", "DPY-2058"):
        params = oracledb.ConnectParams()
        params.parse_connect_string(azure_config.plaintext_password_dsn)


def test_ext_3207(test_env, azure_config):
    "E3207 - missing Azure config key prefix"
    dsn = azure_config.build_config_dsn(
        azure_config._dsn_key(azure_config._key_prefix("missing-alias"))
    )
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        params.parse_connect_string(dsn)


def test_ext_3208(test_env, azure_config):
    "E3208 - Azure config key prefix maps only to text"
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        params.parse_connect_string(azure_config.text_setting_dsn)


@pytest.mark.parametrize(
    "params_class",
    [
        pytest.param(oracledb.ConnectParams, id="connect"),
        pytest.param(oracledb.PoolParams, id="pool"),
    ],
)
def test_ext_3209(azure_config, params_class):
    "E3209 - extra Azure config query parameter is ignored"
    dsn = azure_config.build_config_dsn(
        azure_config._dsn_key(azure_config.config_key), foo="bar"
    )
    params = params_class()
    params.parse_connect_string(dsn)
    expected_params = params_class()
    expected_params.set_from_config(azure_config.config)
    assert params == expected_params


def test_ext_3210(test_env, azure_config):
    "E3210 - bad Azure config DSN string"
    dsn = (
        f"config-azure://{azure_config.app_config_host}/"
        f"{quote(azure_config.config_key, safe='')}"
    )
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        params.parse_connect_string(dsn)


def test_ext_3211(test_env):
    "E3211 - invalid Azure config hook protocol"
    dsn = "config-azurex://example.azconfig.io?key=pythontest/"
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-4021"):
        params.parse_connect_string(dsn)
