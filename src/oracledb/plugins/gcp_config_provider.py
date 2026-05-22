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
# gcp_config_provider.py
#
# Python file contains the hook method config_gcpstorage_hook() that fetches
# config store from GCP Cloud Storage. It also contains the password type
# handler for retrieving passwords from GCP Secret Manager.
# -----------------------------------------------------------------------------

import json

from google.cloud import secretmanager
from google.cloud import storage
import google_crc32c
import oracledb


def _gcs_download_object_as_text(
    project: str, bucket_name: str, object_name: str
) -> str:
    """
    Download GCS object content and return as text.
    Authentication: uses GCP ADC (Application Default Credentials).
    """
    client = storage.Client(project=project)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)

    # Use bytes to avoid version differences in download_as_text() signatures.
    return blob.download_as_bytes().decode()


def _get_gcs_config(
    parameters: dict, connect_params: oracledb.ConnectParams
) -> None:
    """
    Processes the configuration stored in GCP Cloud Storage.
    """
    project = _get_required_parameter(parameters, "project")
    bucket_name = _get_required_parameter(parameters, "bucket")
    object_name = _get_required_parameter(parameters, "object")
    text = _gcs_download_object_as_text(project, bucket_name, object_name)
    settings = _load_settings(
        text,
        "GCP Cloud Storage",
        parameters.get("key"),
    )
    _process_config(settings, connect_params)


def _get_required_parameter(parameters, name, location="connection string"):
    try:
        return parameters[name]
    except KeyError:
        message = f'Parameter named "{name}" is missing from {location}'
        raise Exception(message) from None


def _get_secretmanager_config(
    parameters: dict, connect_params: oracledb.ConnectParams
) -> None:
    """
    Processes the configuration stored in GCP Secret Manager.
    """
    resource_name = _get_required_parameter(parameters, "resource_name")
    text = _secretmanager_access_secret_text(resource_name)
    settings = _load_settings(
        text,
        "GCP Secret Manager",
        parameters.get("key"),
    )
    _process_config(settings, connect_params)


def _load_settings(text: str, location: str, key_name: str) -> dict:
    """
    Loads a JSON object and returns the selected configuration as a dictionary.
    """
    try:
        settings = json.loads(text)
    except json.JSONDecodeError:
        message = f"Content retrieved from {location} is not valid JSON"
        raise Exception(message) from None
    if not isinstance(settings, dict):
        message = f"Content retrieved from {location} must be a JSON object"
        raise Exception(message)

    if key_name is not None:
        try:
            settings = settings[key_name]
        except KeyError:
            raise Exception(
                f'Key "{key_name}" not found in GCP config object'
            ) from None
        if not isinstance(settings, dict):
            raise Exception(
                f'Key "{key_name}" in GCP config object must map to a JSON object'
            )
    return settings


def _parse_gcs_parameters(protocol_arg: str) -> dict:
    """
    Parse the GCS protocol argument.

    Expected formats:
        config-gcpstorage://project=<project>;bucket=<bucket>;object=<object>
        config-gcpstorage://project=<project>;bucket=<bucket>;object=<object>?key=<alias>
    """
    parameters = {}
    base_part, _, query_part = protocol_arg.lstrip("/").strip().partition("?")
    for part in base_part.split(";"):
        key, _, value = part.strip().partition("=")
        key = key.strip().lower()
        value = value.strip()
        if not key or not value:
            raise Exception(
                f'Invalid key/value segment "{part}" in connection string'
            )
        parameters[key] = value
    _get_required_parameter(parameters, "project")
    _get_required_parameter(parameters, "bucket")
    _get_required_parameter(parameters, "object")
    parameters.update(_parse_query_parameters(query_part))
    return parameters


def _parse_query_parameters(query_part: str) -> dict:
    """
    Parse optional query parameters.
    Currently only ?key=<alias> is supported.
    """
    parameters = {}
    if query_part:
        for part in query_part.split("&"):
            key, _, value = part.strip().partition("=")
            key = key.strip().lower()
            value = value.strip()
            if not key or not value:
                raise Exception(
                    f'Invalid query parameter "{part}" in connection string'
                )
            if key != "key":
                raise Exception(
                    f'Unsupported query parameter "{key}" in connection string'
                )
            parameters[key] = value
    return parameters


def _parse_secretmanager_parameters(protocol_arg: str) -> dict:
    """
    Parse the GCP Secret Manager protocol argument.

    Expected formats:
        config-gcpsecretmanager://projects/<project>/secrets/<name>/versions/<ver|latest>
        config-gcpsecretmanager://projects/<project>/secrets/<name>/versions/<ver|latest>?key=<alias>
    """
    resource_name, _, query_part = (
        protocol_arg.lstrip("/").strip().partition("?")
    )
    if not resource_name:
        raise Exception(
            "Secret Manager resource name is missing from connection string"
        )
    parameters = {"resource_name": resource_name}
    parameters.update(_parse_query_parameters(query_part))
    return parameters


def _process_config(
    settings: dict, connect_params: oracledb.ConnectParams
) -> None:
    """
    Convert JSON settings dict into the 'config' dict expected by
    ConnectParams.set_from_config().
    """
    config = {}
    config["connect_descriptor"] = _get_required_parameter(
        settings, "connect_descriptor", location="config object"
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


def _secretmanager_access_secret_text(resource_name: str) -> str:
    """
    Access a secret version from GCP Secret Manager and return payload as text.
    Authentication: uses GCP ADC (Application Default Credentials).
    """
    client = secretmanager.SecretManagerServiceClient()
    response = client.access_secret_version(request={"name": resource_name})
    payload_bytes = response.payload.data
    expected_crc32c = response.payload.data_crc32c
    if expected_crc32c is not None:
        crc32c = google_crc32c.Checksum()
        crc32c.update(payload_bytes)
        actual_crc32c = int(crc32c.hexdigest(), 16)
        if actual_crc32c != expected_crc32c:
            raise Exception(
                "GCP Secret Manager payload checksum verification failed."
            )
    try:
        return payload_bytes.decode()
    except UnicodeDecodeError as e:
        raise Exception(
            "GCP Secret Manager payload could not be decoded as UTF-8 text."
        ) from e


def config_gcpsecretmanager_hook(
    protocol: str, protocol_arg: str, connect_params: oracledb.ConnectParams
):
    """
    Hook for handling parameters stored in GCP Secret Manager.
    DSN format:
        config-gcpsecretmanager://projects/.../secrets/.../versions/...
    """
    parameters = _parse_secretmanager_parameters(protocol_arg)
    _get_secretmanager_config(parameters, connect_params)


def config_gcpstorage_hook(
    protocol: str, protocol_arg: str, connect_params: oracledb.ConnectParams
):
    """
    Hook for handling parameters stored in GCP Cloud Storage (GCS).
    DSN format:
        config-gcpstorage://project=<project>;bucket=<bucket>;object=<object>
    """
    parameters = _parse_gcs_parameters(protocol_arg)
    _get_gcs_config(parameters, connect_params)


def password_type_gcpsecretmanager_hook(args: dict) -> str:
    """
    Password type handler for:
        "password": {
            "type": "gcpsecretmanager",
            "value": "projects/.../secrets/.../versions/..."
        }
    Returns the resolved secret string.
    """
    resource_name = _get_required_parameter(
        args, "value", '"password" key section'
    )
    return _secretmanager_access_secret_text(resource_name)


oracledb.register_password_type(
    "gcpsecretmanager", password_type_gcpsecretmanager_hook
)
oracledb.register_protocol("config-gcpstorage", config_gcpstorage_hook)
oracledb.register_protocol(
    "config-gcpsecretmanager", config_gcpsecretmanager_hook
)
