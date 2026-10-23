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
import threading
import warnings

from google.cloud import pubsub_v1
from google.cloud import secretmanager
from google.cloud import storage
import google_crc32c
import oracledb

_CONFIG_LISTENERS = {}
_CONFIG_LISTENERS_LOCK = threading.Lock()
_GCS_CHANGE_EVENTS = frozenset(
    {
        "OBJECT_FINALIZE",
        "OBJECT_ARCHIVE",
        "OBJECT_DELETE",
    }
)
_SECRETMANAGER_CHANGE_EVENTS = frozenset(
    {
        "SECRET_DELETE",
        "SECRET_VERSION_ADD",
        "SECRET_VERSION_DISABLE",
        "SECRET_VERSION_DESTROY",
    }
)


def _gcs_download_object_as_text(
    project: str, bucket_name: str, object_name: str
) -> str:
    """
    Download GCS object content and return as text.
    Authentication: uses GCP ADC (Application Default Credentials).
    """
    with storage.Client(project=project) as client:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        # Use bytes to avoid version differences in download_as_text()
        # signatures.
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
    notification_fn = _get_notification_fn(parameters)
    _process_config(settings, connect_params, notification_fn)


def _get_notification_fn(parameters: dict):
    """
    Returns the notification function to use when config is cached.
    """
    subscription_name = parameters.get("subscriptionname")
    if subscription_name is None:
        return None
    if "resource_name" in parameters:
        resource_name = parameters["resource_name"]
        resolved_name = parameters["resolved_resource_name"]
        secret_name, _, version = resource_name.rpartition("/versions/")
        resolved_secret_name = resolved_name.rpartition("/versions/")[0]
        resource_names = {
            resource_name,
            resolved_name,
            secret_name,
            resolved_secret_name,
            f"{resolved_secret_name}/versions/{version}",
        }
    else:
        resource_names = {
            f'gs://{parameters["bucket"]}/{parameters["object"]}'
        }

    def notification_fn(dsn):
        _register_config_notification(dsn, subscription_name, resource_names)

    return notification_fn


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
    text, resolved_name = _secretmanager_access_secret(resource_name)
    parameters["resolved_resource_name"] = resolved_name
    settings = _load_settings(
        text,
        "GCP Secret Manager",
        parameters.get("key"),
    )
    notification_fn = _get_notification_fn(parameters)
    _process_config(settings, connect_params, notification_fn)


def _handle_gcs_event(
    event: dict, attributes: dict, subscription_name: str
) -> None:
    """
    Processes a Cloud Storage event and updates matching cache entries.
    """
    event_type = attributes["eventType"]
    if event_type not in _GCS_CHANGE_EVENTS:
        return
    bucket_name = event["bucket"]
    object_name = event["name"]

    remove_permanently = (
        event_type in {"OBJECT_DELETE", "OBJECT_ARCHIVE"}
        and "overwrittenByGeneration" not in attributes
    )
    _update_registered_config_cache(
        subscription_name,
        {f"gs://{bucket_name}/{object_name}"},
        remove_permanently=remove_permanently,
    )


def _handle_pubsub_message(message, subscription_name: str) -> None:
    """
    Processes a Pub/Sub notification and warns about unexpected errors.
    """
    try:
        attributes = dict(message.attributes)
        if attributes["eventType"].startswith("SECRET_"):
            _handle_secretmanager_event(attributes, subscription_name)
        elif attributes["eventType"] in _GCS_CHANGE_EVENTS:
            event = json.loads(message.data)
            _handle_gcs_event(event, attributes, subscription_name)
    except Exception as e:
        exc_type = type(e).__name__
        warnings.warn(
            f"Unexpected error during config change\n{exc_type}: {e}",
            RuntimeWarning,
        )


def _handle_secretmanager_event(
    attributes: dict, subscription_name: str
) -> None:
    """
    Processes a Secret Manager event and updates matching cache entries.
    """
    event_type = attributes["eventType"]
    if event_type not in _SECRETMANAGER_CHANGE_EVENTS:
        return
    secret_name = attributes["secretId"]

    if event_type == "SECRET_DELETE":
        resource_name = secret_name
    elif event_type == "SECRET_VERSION_ADD":
        resource_name = f"{secret_name}/versions/latest"
    else:
        resource_name = attributes["versionId"]

    _update_registered_config_cache(
        subscription_name,
        {resource_name},
        remove_permanently=event_type != "SECRET_VERSION_ADD",
    )


def _listen_for_config_changes(
    subscriber_client, subscription_name: str, stop_event: threading.Event
) -> None:
    """
    Receives Pub/Sub messages with retries until the listener is stopped.
    """
    wait_seconds = 1

    def callback(message):
        try:
            _handle_pubsub_message(message, subscription_name)
        finally:
            message.ack()

    try:
        while not stop_event.is_set():
            try:
                future = subscriber_client.subscribe(
                    subscription_name,
                    callback=callback,
                    await_callbacks_on_shutdown=True,
                )
                try:
                    while not stop_event.wait(1) and not future.done():
                        pass
                finally:
                    future.cancel()
                    future.result()
            except Exception:
                stop_event.wait(wait_seconds)
                wait_seconds = min(wait_seconds * 2, 60)
            else:
                wait_seconds = 1
    finally:
        subscriber_client.close()


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
        config-gcpstorage://<parameters>?key=<alias>
        config-gcpstorage://<parameters>?subscriptionname=<subscription>
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
    The key and subscriptionname parameters are supported.
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
            if key not in {"key", "subscriptionname"}:
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
        config-gcpsecretmanager://<secret-version-resource>
        config-gcpsecretmanager://<secret-version-resource>?key=<alias>
        config-gcpsecretmanager://<resource>?subscriptionname=<subscription>
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
    settings: dict, connect_params: oracledb.ConnectParams, notification_fn
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
    connect_params.set_from_config(config, notification_fn=notification_fn)


def _register_config_notification(
    dsn: str, subscription_name: str, resource_names: set[str]
) -> None:
    """
    Registers or reuses one listener for a GCP Pub/Sub subscription.
    The subscription must be dedicated to this process so that another
    subscriber does not acknowledge notifications needed by this cache.
    """
    with _CONFIG_LISTENERS_LOCK:
        listener = _CONFIG_LISTENERS.get(subscription_name)
        if listener is None:
            subscriber_client = pubsub_v1.SubscriberClient()
            stop_event = threading.Event()
            thread = threading.Thread(
                target=_listen_for_config_changes,
                args=(subscriber_client, subscription_name, stop_event),
                name="oracledb-gcp-config-listener",
                daemon=True,
            )
            try:
                thread.start()
            except Exception:
                subscriber_client.close()
                raise
            listener = _CONFIG_LISTENERS[subscription_name] = (
                stop_event,
                {},
            )
        listener[1][dsn] = resource_names


def _secretmanager_access_secret(resource_name: str) -> tuple[str, str]:
    """
    Return the GCP secret payload as text and its resolved resource name.
    Authentication: uses GCP ADC (Application Default Credentials).
    """
    with secretmanager.SecretManagerServiceClient() as client:
        response = client.access_secret_version(
            request={"name": resource_name}
        )
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
        return payload_bytes.decode(), response.name
    except UnicodeDecodeError as e:
        raise Exception(
            "GCP Secret Manager payload could not be decoded as UTF-8 text."
        ) from e


def _secretmanager_access_secret_text(resource_name: str) -> str:
    """
    Access a secret version from GCP Secret Manager and return payload as text.
    Authentication: uses GCP ADC (Application Default Credentials).
    """
    text, _ = _secretmanager_access_secret(resource_name)
    return text


def _update_registered_config_cache(
    subscription_name: str,
    resource_names: set[str],
    remove_permanently: bool,
) -> None:
    """
    Updates cached DSNs registered for the given GCP resource.
    """
    if not resource_names:
        return
    with _CONFIG_LISTENERS_LOCK:
        listener = _CONFIG_LISTENERS.get(subscription_name)
        if listener is None:
            return
        stop_event, users = listener
        dsns = [
            dsn
            for dsn, registered_resource_names in users.items()
            if resource_names & registered_resource_names
        ]
        if remove_permanently:
            for dsn in dsns:
                del users[dsn]
            if not users:
                del _CONFIG_LISTENERS[subscription_name]
                stop_event.set()
    for dsn in dsns:
        oracledb.update_config_cache(
            dsn, remove_permanently=remove_permanently
        )


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
