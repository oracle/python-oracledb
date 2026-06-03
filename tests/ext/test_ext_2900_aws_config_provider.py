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
E2900 - Module for testing the AWS centralized configuration provider.

These tests are part of the extended test suite and only run when
run_long_tests is enabled.

Required entries in extended configuration file:
    aws_bucket_name
        Existing S3 bucket used to upload temporary config objects.
    aws_region
        AWS region used for test resources.

Optional entries in extended configuration file:
    aws_object_prefix
        Base object prefix used to build temporary S3 object names.
    aws_profile
        Named AWS profile used for authentication, if required.

AWS authentication must be available through boto3.
The AWS credentials must permit temporary S3 object creation/deletion and
temporary Secrets Manager secret creation/deletion.

The usual test environment supplies the Oracle Database connect information.
"""

import json
import os
import uuid
from urllib.parse import quote

import oracledb
import pytest

PYO_PARAMETERS = {
    "cclass": "pythontest_aws",
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


def _build_query_args(config, include_profile=True, **kwargs):
    query_args = dict(aws_region=config.aws_region)
    if include_profile and config.aws_profile is not None:
        query_args["aws_profile"] = config.aws_profile
    query_args.update(kwargs)
    return query_args


def _build_s3_dsn(config, object_key, include_profile=True, **kwargs):
    query = _build_query(
        **_build_query_args(config, include_profile, **kwargs)
    )
    return f"config-awss3://{config.bucket_name}/{object_key}?{query}"


def _build_secret_dsn(config, secret_name, include_profile=True, **kwargs):
    query = _build_query(
        **_build_query_args(config, include_profile, **kwargs)
    )
    return f"config-awssecretsmanager://{secret_name}?{query}"


class AwsConfig:
    """
    Manages AWS resources required by the AWS config store tests.
    """

    def __init__(self, test_env, extended_config):
        self.bucket_name = extended_config.get_str_value("aws_bucket_name")
        self.object_prefix = extended_config.get_str_value("aws_object_prefix")
        self.aws_region = extended_config.get_str_value("aws_region")
        self.aws_profile = extended_config.get_str_value(
            "aws_profile", os.environ.get("AWS_PROFILE")
        )
        self.connect_descriptor = test_env.connect_string
        self.db_user = test_env.main_user
        self.db_password = test_env.main_password
        self.object_keys = []
        self.secret_names = []
        if not self.bucket_name:
            pytest.skip("AWS S3 bucket name is not configured")
        if not self.aws_region:
            pytest.skip("AWS region is not configured")

    def _build_config(self, pyo, secret_name=None, field_name=None):
        if secret_name is None:
            secret_name = self.password_secret_name
        config = dict(
            connect_descriptor=self.connect_descriptor,
            user=self.db_user,
            pyo=pyo,
        )
        config["password"] = self._build_password_config(
            secret_name, field_name
        )
        return config

    def _build_object_key(self, name, suffix):
        base_prefix = "python-oracledb-test"
        if self.object_prefix:
            base_prefix = f"{self.object_prefix}/{base_prefix}"
        return f"{base_prefix}/{name}-{suffix}.json"

    def _build_password_config(self, secret_name, field_name=None):
        password_config = dict(
            type="awssecretsmanager",
            value=secret_name,
            authentication=dict(aws_region=self.aws_region),
        )
        if field_name is not None:
            password_config["field_name"] = field_name
        return password_config

    def _build_payloads(self):
        self.params_config = self._build_config(PYO_PARAMETERS)
        self.config = self._build_config(PYO_PARAMETERS)
        self.binary_password_config = self._build_config(
            PYO_PARAMETERS, secret_name=self.binary_password_secret_name
        )
        self.json_password_config = self._build_config(
            PYO_PARAMETERS,
            secret_name=self.json_password_secret_name,
            field_name="password",
        )
        self.keyed_config = dict(test_key=self.config)
        self.plaintext_password_config = dict(
            connect_descriptor=self.connect_descriptor,
            user=self.db_user,
            password="not-a-real-password",
        )
        return dict(
            params_config=self._to_json(self.params_config),
            config=self._to_json(self.config),
            binary_password_config=self._to_json(self.binary_password_config),
            json_password_config=self._to_json(self.json_password_config),
            keyed_config=self._to_json(self.keyed_config),
            plaintext_password_config=self._to_json(
                self.plaintext_password_config
            ),
        )

    def _create_binary_secret(self, name, value):
        self.secrets_client.create_secret(Name=name, SecretBinary=value)
        self.secret_names.append(name)

    def _create_secret(self, name, value):
        self.secrets_client.create_secret(Name=name, SecretString=value)
        self.secret_names.append(name)

    def _create_secrets(self, payloads):
        self._create_secret(
            self.params_config_secret_name, payloads["params_config"]
        )
        self._create_secret(self.config_secret_name, payloads["config"])
        self._create_secret(
            self.config_binary_password_secret_name,
            payloads["binary_password_config"],
        )
        self._create_secret(
            self.config_json_password_secret_name,
            payloads["json_password_config"],
        )
        self._create_secret(self.password_secret_name, self.db_password)
        self._create_secret(
            self.json_password_secret_name,
            self._to_json(dict(password=self.db_password)),
        )
        self._create_binary_secret(
            self.binary_password_secret_name,
            self.db_password.encode(),
        )

    def _put_object(self, key, body):
        self.s3_client.put_object(Bucket=self.bucket_name, Key=key, Body=body)
        self.object_keys.append(key)

    def _set_resource_names(self, suffix):
        self.params_object_key = self._build_object_key(
            "aws-params-config", suffix
        )
        self.object_key = self._build_object_key(
            "aws-connectable-config", suffix
        )
        self.keyed_object_key = self._build_object_key(
            "aws-keyed-config", suffix
        )
        self.plaintext_password_object_key = self._build_object_key(
            "aws-plaintext-password-config", suffix
        )
        self.params_config_secret_name = (
            f"python-oracledb-test/aws-params-config-{suffix}"
        )
        self.config_secret_name = f"python-oracledb-test/aws-config-{suffix}"
        self.config_binary_password_secret_name = (
            f"python-oracledb-test/aws-binary-password-config-{suffix}"
        )
        self.config_json_password_secret_name = (
            f"python-oracledb-test/aws-json-password-config-{suffix}"
        )
        self.password_secret_name = (
            f"python-oracledb-test/aws-password-{suffix}"
        )
        self.json_password_secret_name = (
            f"python-oracledb-test/aws-json-password-{suffix}"
        )
        self.binary_password_secret_name = (
            f"python-oracledb-test/aws-binary-password-{suffix}"
        )

    def _set_static_credentials(self):
        credentials = (
            self.aws_session.get_credentials().get_frozen_credentials()
        )
        self.aws_access_key_id = credentials.access_key
        self.aws_secret_access_key = credentials.secret_key
        self.aws_session_token = credentials.token

    def _set_test_dsns(self):
        self.s3_dsn = _build_s3_dsn(self, self.object_key)
        self.secret_dsn = _build_secret_dsn(self, self.config_secret_name)
        self.params_s3_dsn = _build_s3_dsn(self, self.params_object_key)
        self.params_secret_dsn = _build_secret_dsn(
            self, self.params_config_secret_name
        )
        self.keyed_s3_dsn = _build_s3_dsn(
            self, self.keyed_object_key, key="test_key"
        )
        self.config_json_password_secret_dsn = _build_secret_dsn(
            self, self.config_json_password_secret_name
        )
        self.config_binary_password_secret_dsn = _build_secret_dsn(
            self, self.config_binary_password_secret_name
        )
        self.profile_s3_dsn = _build_s3_dsn(
            self,
            self.object_key,
            authentication="aws_profile",
            aws_profile=self.aws_profile,
        )
        self.plaintext_password_s3_dsn = _build_s3_dsn(
            self, self.plaintext_password_object_key
        )

    def _to_json(self, value):
        return json.dumps(value, separators=(",", ":"))

    def _upload_s3_objects(self, payloads):
        self._put_object(self.params_object_key, payloads["params_config"])
        self._put_object(self.object_key, payloads["config"])
        self._put_object(self.keyed_object_key, payloads["keyed_config"])
        self._put_object(
            self.plaintext_password_object_key,
            payloads["plaintext_password_config"],
        )

    def create_session(self):
        try:
            import boto3
        except ModuleNotFoundError:
            pytest.skip("boto3 is not installed for AWS tests")

        self.aws_session = boto3.session.Session(
            profile_name=self.aws_profile, region_name=self.aws_region
        )
        if self.aws_session.get_credentials() is None:
            raise RuntimeError("AWS credentials are not configured")
        self.aws_session.client("sts").get_caller_identity()

    def cleanup(self):
        cleanup_errors = []

        if hasattr(self, "s3_client") and hasattr(self, "bucket_name"):
            for key in self.object_keys:
                try:
                    self.s3_client.delete_object(
                        Bucket=self.bucket_name, Key=key
                    )
                except Exception as exc:
                    cleanup_errors.append(f"S3 object {key!r}: {exc!r}")
        if hasattr(self, "secrets_client"):
            for secret_name in self.secret_names:
                try:
                    self.secrets_client.delete_secret(
                        SecretId=secret_name, ForceDeleteWithoutRecovery=True
                    )
                except Exception as exc:
                    cleanup_errors.append(
                        f"Secrets Manager secret {secret_name!r}: {exc!r}"
                    )
        if cleanup_errors:
            raise RuntimeError(
                "Errors occurred while cleaning up AWS test resources: "
                + "; ".join(cleanup_errors)
            )
        self.object_keys.clear()
        self.secret_names.clear()

    def get_s3_resource(self, resource_format):
        if resource_format == "s3_uri":
            return f"s3://{self.bucket_name}/{self.object_key}"
        if resource_format == "arn":
            return f"arn:aws:s3:::{self.bucket_name}/{self.object_key}"
        if resource_format == "virtual_hosted_url":
            return (
                f"https://{self.bucket_name}.s3.{self.aws_region}"
                f".amazonaws.com/{self.object_key}"
            )
        if resource_format == "path_style_url":
            return (
                f"https://s3.{self.aws_region}.amazonaws.com/"
                f"{self.bucket_name}/{self.object_key}"
            )
        raise ValueError(f"Unknown S3 resource format: {resource_format}")

    def get_s3_resource_dsn(self, resource_format):
        resource = self.get_s3_resource(resource_format)
        query = _build_query(**_build_query_args(self))
        return f"config-awss3://{resource}?{query}"

    def setup(self):
        self.s3_client = self.aws_session.client("s3")
        self.secrets_client = self.aws_session.client("secretsmanager")
        self._set_resource_names(uuid.uuid4().hex)
        payloads = self._build_payloads()
        self._upload_s3_objects(payloads)
        self._create_secrets(payloads)
        self._set_test_dsns()
        self._set_static_credentials()
        self.static_s3_dsn = _build_s3_dsn(
            self,
            self.object_key,
            include_profile=False,
            authentication="aws_static",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            aws_session_token=self.aws_session_token,
        )


@pytest.fixture(scope="module", autouse=True)
def module_checks(extended_config):
    if not extended_config.get_bool_value("run_long_tests"):
        pytest.skip("extended configuration run_long_tests is disabled")
    try:
        import oracledb.plugins.aws_config_provider  # noqa: F401
    except ImportError as exc:
        pytest.skip(f"AWS config store requirements are not available: {exc}")


@pytest.fixture(scope="module")
def aws_config(test_env, extended_config):
    config = AwsConfig(test_env, extended_config)
    config.create_session()
    config.setup()
    yield config
    config.cleanup()


def test_ext_2900(aws_config):
    "E2900 - test for config-awss3 protocol"
    with oracledb.connect(dsn=aws_config.s3_dsn):
        pass


def test_ext_2901(aws_config):
    "E2901 - test for config-awssecretsmanager protocol"
    with oracledb.connect(dsn=aws_config.secret_dsn):
        pass


@pytest.mark.parametrize(
    "dsn_attr_name, params_class",
    [
        ("params_s3_dsn", oracledb.ConnectParams),
        ("params_s3_dsn", oracledb.PoolParams),
        ("params_secret_dsn", oracledb.ConnectParams),
        ("params_secret_dsn", oracledb.PoolParams),
    ],
)
def test_ext_2902(aws_config, dsn_attr_name, params_class):
    "E2902 - test for pyo params from AWS config store"
    params = params_class()
    params.parse_connect_string(getattr(aws_config, dsn_attr_name))
    expected_params = params_class()
    expected_params.set_from_config(aws_config.params_config)
    assert params == expected_params


@pytest.mark.parametrize(
    "resource_format",
    ("arn", "path_style_url", "s3_uri", "virtual_hosted_url"),
)
def test_ext_2903(aws_config, resource_format):
    "E2903 - test for AWS S3 resource formats"
    dsn = aws_config.get_s3_resource_dsn(resource_format)
    with oracledb.connect(dsn=dsn):
        pass


def test_ext_2904(aws_config):
    "E2904 - test for key selection in AWS S3 config"
    with oracledb.connect(dsn=aws_config.keyed_s3_dsn):
        pass


def test_ext_2905(aws_config):
    "E2905 - test for JSON password field from AWS Secrets Manager"
    with oracledb.connect(dsn=aws_config.config_json_password_secret_dsn):
        pass


def test_ext_2906(aws_config):
    "E2906 - test for binary password from AWS Secrets Manager"
    with oracledb.connect(dsn=aws_config.config_binary_password_secret_dsn):
        pass


def test_ext_2907(aws_config):
    "E2907 - test for profile authentication"
    if aws_config.aws_profile is None:
        pytest.skip("AWS profile is not configured for tests")
    with oracledb.connect(dsn=aws_config.profile_s3_dsn):
        pass


def test_ext_2908(aws_config):
    "E2908 - test for static authentication"
    with oracledb.connect(dsn=aws_config.static_s3_dsn):
        pass


def test_ext_2909(test_env, aws_config):
    "E2909 - test for invalid AWS S3 resource"
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        params.parse_connect_string("config-awss3://bucket-only")


def test_ext_2910(test_env, aws_config):
    "E2910 - test for missing AWS Secrets Manager secret name"
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        params.parse_connect_string("config-awssecretsmanager://")


def test_ext_2911(aws_config):
    "E2911 - test for create_pool using AWS config store"
    pool = oracledb.create_pool(dsn=aws_config.s3_dsn)
    try:
        with pool.acquire():
            pass
    finally:
        pool.close()


def test_ext_2912(test_env, aws_config):
    "E2912 - test plaintext password in AWS config is rejected"
    params = oracledb.ConnectParams()
    with test_env.assert_raises_from_cause("DPY-2056", "DPY-2058"):
        params.parse_connect_string(aws_config.plaintext_password_s3_dsn)


def test_ext_2913(test_env, aws_config):
    "E2913 - test for invalid AWS config hook"
    dsn = (
        f"config1-awss3://{aws_config.bucket_name}/{aws_config.object_key}"
        f"?aws_region={aws_config.aws_region}"
    )
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-4021"):
        params.parse_connect_string(dsn)


@pytest.mark.parametrize(
    "dsn",
    [
        "config-awss3://bucket/key?foo=bar",
        "config-awss3://bucket/key?key=",
        "config-awss3://bucket/key?key=one&key=two",
        "config-awss3://bucket/key?versionstage=AWSPREVIOUS",
        "config-awssecretsmanager://secret?foo=bar",
    ],
)
def test_ext_2914(test_env, dsn):
    "E2914 - test for invalid AWS config query parameters"
    params = oracledb.ConnectParams()
    with test_env.assert_raises_full_code("DPY-2056"):
        params.parse_connect_string(dsn)


if __name__ == "__main__":
    pytest.main([__file__])
