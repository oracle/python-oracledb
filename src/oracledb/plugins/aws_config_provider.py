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

# -----------------------------------------------------------------------------
# aws_config_provider.py
#
# Python file contains hook methods that fetch centralized configuration from
# AWS S3 and AWS Secrets Manager.
# -----------------------------------------------------------------------------

import base64
import json
from urllib.parse import parse_qsl, unquote, urlparse

import boto3
import oracledb

_COMMON_QUERY_PARAMETERS = frozenset(
    (
        "authentication",
        "aws_access_key_id",
        "aws_endpoint_url",
        "aws_profile",
        "aws_region",
        "aws_secret_access_key",
        "aws_session_token",
        "key",
    )
)

_S3_QUERY_PARAMETERS = _COMMON_QUERY_PARAMETERS | frozenset(("versionid",))

_SECRETS_MANAGER_QUERY_PARAMETERS = _COMMON_QUERY_PARAMETERS | frozenset(
    (
        "versionid",
        "versionstage",
    )
)


def _extract_secret_field(secret_value: str, parameters: dict) -> str:
    """
    Extract a specific field from a structured JSON secret when requested.
    """
    field_name = parameters.get("field_name")
    if field_name is None:
        return secret_value
    try:
        payload = json.loads(secret_value)
    except json.JSONDecodeError as e:
        raise Exception(
            'The "field_name" option requires the secret value to be JSON.'
        ) from e
    if not isinstance(payload, dict):
        raise Exception(
            'The "field_name" option requires the secret value to be a JSON '
            "object."
        )
    try:
        value = payload[field_name]
    except KeyError:
        raise Exception(
            f'Secret field named "{field_name}" is missing from secret '
            "payload."
        ) from None
    if not isinstance(value, str):
        raise Exception(
            f'Secret field named "{field_name}" must contain a string value.'
        )
    return value


def _get_aws_client(parameters: dict, service_name: str):
    """
    Get an AWS service client from the supplied parameters.
    """
    session = _get_credential(parameters)
    return session.client(
        service_name,
        region_name=parameters.get("aws_region"),
        endpoint_url=parameters.get("aws_endpoint_url"),
    )


def _get_credential(parameters: dict) -> boto3.session.Session:
    """
    Returns the appropriate AWS credential/session based on the input
    supplied by the original connect string.
    """
    auth_method = parameters.get("authentication", "aws_default").lower()
    aws_params = dict(region_name=parameters.get("aws_region"))

    if auth_method == "aws_static":
        aws_params.update(
            aws_access_key_id=_get_required_parameter(
                parameters, "aws_access_key_id"
            ),
            aws_secret_access_key=_get_required_parameter(
                parameters, "aws_secret_access_key"
            ),
            aws_session_token=parameters.get("aws_session_token"),
        )
    elif auth_method == "aws_profile":
        aws_params["profile_name"] = _get_required_parameter(
            parameters, "aws_profile"
        )
    elif auth_method != "aws_default":
        raise Exception(
            f'Unsupported AWS authentication method "{auth_method}"'
        )

    return boto3.session.Session(**aws_params)


def _get_required_parameter(
    parameters: dict, name: str, location: str = "connection string"
) -> str:
    try:
        return parameters[name]
    except KeyError:
        message = f'Parameter named "{name}" is missing from {location}'
        raise Exception(message) from None


def _get_secret_value(parameters: dict) -> str:
    """
    Fetch a secret value from AWS Secrets Manager.
    """
    client = _get_aws_client(parameters, "secretsmanager")
    secret_name = _get_required_parameter(parameters, "secret_name")
    aws_params = {}
    if "versionid" in parameters:
        aws_params["VersionId"] = parameters["versionid"]
    if "versionstage" in parameters:
        aws_params["VersionStage"] = parameters["versionstage"]
    try:
        response = client.get_secret_value(SecretId=secret_name, **aws_params)
    except Exception as e:
        _raise_aws_call_error(e, "Secrets Manager", "get_secret_value")
    text_value = response.get("SecretString")
    binary_value = response.get("SecretBinary")
    if text_value is None and binary_value is None:
        raise Exception(
            "No secret value was returned from AWS Secrets Manager"
        )
    if binary_value is None:
        return text_value
    if isinstance(binary_value, bytes):
        try:
            return binary_value.decode()
        except UnicodeDecodeError as e:
            raise Exception(
                "SecretBinary value must be UTF-8 text data."
            ) from e
    try:
        return base64.b64decode(binary_value).decode()
    except Exception as e:
        raise Exception(
            "SecretBinary value was not decodable as text data."
        ) from e


def _load_settings(text: str, config_key: str | None = None) -> dict:
    """
    Load a JSON configuration payload and select a named config, if requested.
    """
    try:
        settings = json.loads(text)
    except json.JSONDecodeError as e:
        raise Exception("Configuration payload is not valid JSON") from e
    if not isinstance(settings, dict):
        raise Exception("Configuration payload must be a JSON object.")
    if config_key is not None:
        settings = _get_required_parameter(
            settings, config_key, "config payload"
        )
        if not isinstance(settings, dict):
            raise Exception(
                'Configuration selected by "key" must be a JSON object.'
            )
    return settings


def _parse_parameters(
    protocol_arg: str, supported_parameters: frozenset
) -> dict:
    """
    Parse path and query parameters from the protocol argument string.
    """
    parameters = {}
    resource, _, query_part = protocol_arg.lstrip("/").strip().partition("?")
    for key, value in parse_qsl(query_part, keep_blank_values=True):
        key = key.strip().lower()
        value = value.strip()
        if not key or not value:
            raise Exception(
                f'Invalid query parameter "{key}" in connection string'
            )
        if key not in supported_parameters:
            raise Exception(
                f'Unsupported query parameter "{key}" ' "in connection string"
            )
        if key in parameters:
            raise Exception(
                f'Duplicate query parameter "{key}" in connection string'
            )
        parameters[key] = value
    return unquote(resource.strip()), parameters


def _parse_s3_resource(resource: str, parameters: dict) -> None:
    """
    Parse an S3 resource into bucket and key values.
    """
    if resource.startswith(("http://", "https://")):
        parsed = urlparse(resource)
        path = parsed.path.lstrip("/")
        host = parsed.netloc
        # Support virtual-hosted-style and path-style S3 object URLs.
        if ".s3." in host:
            bucket, _, _ = host.partition(".s3.")
            key = path
        elif host.startswith("s3.") and "/" in path:
            bucket, key = path.split("/", 1)
        else:
            raise Exception(
                "AWS S3 resource must be an S3 URI, object URL, ARN, or "
                "bucket/object-key value."
            )
    else:
        for prefix in ("arn:aws:s3:::", "s3://"):
            if resource.startswith(prefix):
                resource = resource.removeprefix(prefix)
                break
        resource = resource.lstrip("/")
        if "/" not in resource:
            raise Exception(
                "AWS S3 resource must include both bucket and object key "
                "values."
            )
        bucket, key = resource.split("/", 1)
    if not bucket or not key:
        raise Exception(
            "AWS S3 resource must include both bucket and object key values."
        )
    parameters["bucket_name"] = bucket
    parameters["object_key"] = key


def _process_aws_secrets_manager_config(
    parameters: dict, connect_params: oracledb.ConnectParams
) -> None:
    """
    Fetch and process centralized configuration from AWS Secrets Manager.
    """
    settings = _load_settings(
        _get_secret_value(parameters), parameters.get("key")
    )
    _set_config_from_settings(settings, connect_params, parameters)


def _process_s3_config(
    parameters: dict, connect_params: oracledb.ConnectParams
) -> None:
    """
    Fetch and process centralized configuration from S3.
    """
    client = _get_aws_client(parameters, "s3")
    bucket_name = _get_required_parameter(parameters, "bucket_name")
    object_key = _get_required_parameter(parameters, "object_key")
    aws_params = dict(Bucket=bucket_name, Key=object_key)
    if "versionid" in parameters:
        aws_params["VersionId"] = parameters["versionid"]
    try:
        response = client.get_object(**aws_params)
    except Exception as e:
        _raise_aws_call_error(e, "S3", "get_object")
    settings = _load_settings(
        response["Body"].read().decode(), parameters.get("key")
    )
    _set_config_from_settings(settings, connect_params, parameters)


def _raise_aws_call_error(
    exception: Exception, service_name: str, operation_name: str
) -> None:
    """
    Raise a standardized AWS SDK call error message.
    """
    error = getattr(exception, "response", {}).get("Error", {})
    code = error.get("Code")
    message = error.get("Message")
    details = []
    if code:
        details.append(f"code={code}")
    if message:
        details.append(f"message={message}")
    elif str(exception):
        details.append(str(exception))
    suffix = f' ({", ".join(details)})' if details else ""
    raise Exception(
        f'AWS {service_name} operation "{operation_name}" failed{suffix}'
    ) from exception


def _set_config_from_settings(
    settings: dict, connect_params: oracledb.ConnectParams, parameters: dict
) -> None:
    """
    Build the configuration dictionary and set it on ConnectParams.
    """
    config = {}
    config["connect_descriptor"] = _get_required_parameter(
        settings, "connect_descriptor", "config payload"
    )
    if connect_params.user is None:
        config["user"] = settings.get("user")
        config["password"] = settings.get("password")
    config["config_time_to_live"] = settings.get("config_time_to_live")
    config["config_time_to_live_grace_period"] = settings.get(
        "config_time_to_live_grace_period"
    )
    config["pyo"] = settings.get("pyo")
    connect_params.set_from_config(config)


def config_aws_secrets_manager_hook(
    protocol: str, protocol_arg: str, connect_params: oracledb.ConnectParams
) -> None:
    """
    Hook for handling parameters stored in AWS Secrets Manager.
    """
    resource, parameters = _parse_parameters(
        protocol_arg, _SECRETS_MANAGER_QUERY_PARAMETERS
    )
    secret_name = resource.lstrip("/")
    if not secret_name:
        raise Exception("Secret name is missing from connection string")
    parameters["secret_name"] = secret_name
    _process_aws_secrets_manager_config(parameters, connect_params)


def config_awss3_hook(
    protocol: str, protocol_arg: str, connect_params: oracledb.ConnectParams
) -> None:
    """
    Hook for handling parameters stored in AWS S3.
    """
    resource, parameters = _parse_parameters(
        protocol_arg, _S3_QUERY_PARAMETERS
    )
    if not resource:
        raise Exception("S3 URI is missing from connection string")
    _parse_s3_resource(resource, parameters)
    _process_s3_config(parameters, connect_params)


def password_type_aws_secrets_manager_hook(args: dict) -> str:
    parameters = {}
    parameters["secret_name"] = _get_required_parameter(
        args,
        "value",
        '"password" key section',
    )
    if "field_name" in args:
        parameters["field_name"] = args["field_name"]
    auth = args.get("authentication")
    if auth is not None:
        if not isinstance(auth, dict):
            raise Exception(
                'The "authentication" key in password must be a JSON object.'
            )
        parameters.update(auth)
    return _extract_secret_field(_get_secret_value(parameters), parameters)


oracledb.register_password_type(
    "awssecretsmanager", password_type_aws_secrets_manager_hook
)
oracledb.register_protocol("config-awss3", config_awss3_hook)
oracledb.register_protocol(
    "config-awssecretsmanager", config_aws_secrets_manager_hook
)
