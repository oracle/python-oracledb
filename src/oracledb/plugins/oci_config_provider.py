# -----------------------------------------------------------------------------
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
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
# oci_config_provider.py
#
# Python file contains the hook method config_oci_hook() that fetches config
# store from OCI Object Storage.
# -----------------------------------------------------------------------------

import base64
import json
import oci
import oracledb
import re

from urllib.parse import urlparse, parse_qs

oci_from_file = oci.config.from_file
oci_client_error = oci.exceptions.ClientError
oci_object_storage_client = oci.object_storage.ObjectStorageClient
oci_secrets_client = oci.secrets.SecretsClient


"""
Pattern to parse OCI Object Connect String
"""
cloud_net_naming_pattern_oci = re.compile(
    r"(?P<objservername>[^/]+)/n/(?P<namespace>[^/]+)/b/(?P<bucketname>[^/]+)/o/(?P<filename>[^/]+)(/c/(?P<alias>[^/]+))?"
)


def _get_config(parameters, connect_params):
    config = {}

    credential, signer = _get_credential(parameters)
    auth_method = parameters.get("authentication")
    if auth_method is not None:
        auth_method = auth_method.upper()

    if auth_method is None or auth_method == "OCI_DEFAULT":
        client_oci = oci_object_storage_client(credential)
    elif (
        auth_method == "OCI_INSTANCE_PRINCIPAL"
        or auth_method == "OCI_RESOURCE_PRINCIPAL"
    ):
        client_oci = oci_object_storage_client(
            config=credential, signer=signer
        )
    get_object_request = {
        "object_name": _get_required_parameter(parameters, "filename"),
        "bucket_name": _get_required_parameter(parameters, "bucketname"),
        "namespace_name": _get_required_parameter(parameters, "namespace"),
    }

    get_object_response = client_oci.get_object(**get_object_request)
    resp = _stream_to_string(get_object_response.data)
    settings = json.loads(resp)
    user_alias = parameters.get("alias")
    if user_alias:
        settings = settings[user_alias]

    # Connect Descriptor
    config["connect_descriptor"] = _get_required_parameter(
        settings, "connect_descriptor"
    )

    # user and password
    if connect_params.user is None:
        config["user"] = settings.get("user")
        if "password" in settings:
            config["password"] = pwd = settings["password"]
            if pwd["type"] == "ocivault":
                authentication = pwd.setdefault("authentication", {})
                authentication.setdefault("method", auth_method)
                authentication["credential"] = credential

    # config cache settings
    config["config_time_to_live"] = settings.get("config_time_to_live")
    config["config_time_to_live_grace_period"] = settings.get(
        "config_time_to_live_grace_period"
    )

    # pyo parameters settings
    config["pyo"] = settings.get("pyo", None)

    # set the configuration
    connect_params.set_from_config(config)


def _get_credential(parameters):
    """
    Returns the appropriate credential given the input supplied by the original
    connect string.
    """
    auth_method = parameters.get("authentication", parameters.get("method"))

    if auth_method is not None:
        auth_method = auth_method.upper()

    # if region is not in connection string, retrieve from object server name.
    region = parameters.get(
        "oci_region", _retrieve_region(parameters.get("objservername"))
    )

    try:
        if auth_method is None or auth_method == "OCI_DEFAULT":
            # Default Authentication
            # default path ~/.oci/config
            return oci_from_file(), None
    except oci.exceptions.ClientError:
        # try to create config with connection string parameters.
        if "oci_tenancy" in parameters and "oci_user" in parameters:
            with open(parameters["oci_key_file"], "r") as file_content:
                public_key = file_content.read()
            provider = dict(
                tenancy=parameters["oci_tenancy"],
                user=parameters["oci_user"],
                fingerprint=parameters["oci_fingerprint"],
                key_file=parameters["oci_key_file"],
                private_key_content=public_key,
                region=region,
            )
            return provider, None

    if auth_method == "OCI_INSTANCE_PRINCIPAL":
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        return (
            dict(region=region),
            signer,
        )

    elif auth_method == "OCI_RESOURCE_PRINCIPAL":
        signer = oci.auth.signers.get_resource_principals_signer()
        return {}, signer
    else:
        msg = "Authentication options were not available in Connection String"
        raise Exception(msg)


def _get_required_parameter(parameters, name, location="connection string"):
    try:
        return parameters[name]
    except KeyError:
        message = f'Parameter named "{name}" is missing from {location}'
        raise Exception(message) from None


def _parse_parameters(protocol_arg: str) -> dict:
    """
    Parse the parameters from the protocol argument string.
    """
    pos = protocol_arg.find("?")
    parsed_url = urlparse(protocol_arg[pos + 1 :])
    parsed_values = parse_qs(parsed_url.path)
    parameters = {
        key.lower(): value[0] for key, value in parsed_values.items()
    }

    match = cloud_net_naming_pattern_oci.match(protocol_arg[:pos])
    if match:
        parameters["objservername"] = match.group("objservername")
        parameters["namespace"] = match.group("namespace")
        parameters["bucketname"] = match.group("bucketname")
        parameters["filename"] = match.group("filename")
        if match.group("alias"):
            parameters["alias"] = match.group("alias")
    return parameters


def password_type_oci_vault_hook(args):
    secret_id = _get_required_parameter(
        args, "value", '"password" key section'
    )
    authentication = args.get("authentication")
    if authentication is None:
        raise Exception(
            "OCI Key Vault authentication details were not provided."
        )

    # if credentials are not present, create credentials with given
    # authentication details.
    credential = authentication.get("credential")
    if credential is None:
        credential, signer = _get_credential(authentication)

    auth_method = authentication.get("method")
    if auth_method is not None:
        auth_method = auth_method.upper()
    if auth_method is None or auth_method == "OCI_DEFAULT":
        secret_client_oci = oci_secrets_client(credential)
    elif auth_method == "OCI_INSTANCE_PRINCIPAL":
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        secret_client_oci = oci_secrets_client(
            config=credential, signer=signer
        )
    elif auth_method == "OCI_RESOURCE_PRINCIPAL":
        signer = oci.auth.signers.get_resource_principals_signer()
        secret_client_oci = oci_secrets_client(
            config=credential, signer=signer
        )

    get_secret_bundle_response = secret_client_oci.get_secret_bundle(
        secret_id=secret_id
    )
    # decoding the vault content
    b64content = get_secret_bundle_response.data.secret_bundle_content.content
    return base64.b64decode(b64content).decode()


def _retrieve_region(objservername):
    if objservername is not None:
        arr = objservername.split(".")
        return arr[1].lower().replace("_", "-")


def _stream_to_string(stream):
    return b"".join(stream).decode()


def config_oci_hook(
    protocol: str, protocol_arg: str, connect_params: oracledb.ConnectParams
):
    """
    Hook for handling parameters stored in an OCI Object store.
    """
    parameters = _parse_parameters(protocol_arg)
    _get_config(parameters, connect_params)


oracledb.register_password_type("ocivault", password_type_oci_vault_hook)
oracledb.register_protocol("config-ociobject", config_oci_hook)
