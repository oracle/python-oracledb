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
# azure_config_provider.py
#
# Python file contains the hook method config_azure_hook() that fetches config
# store from Azure App Configuration.
# -----------------------------------------------------------------------------

import json
import re

import oracledb

from urllib.parse import urlparse, parse_qs
from azure.appconfiguration import AzureAppConfigurationClient
from azure.keyvault.secrets import SecretClient
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import (
    ClientSecretCredential,
    CertificateCredential,
    ManagedIdentityCredential,
    ChainedTokenCredential,
    EnvironmentCredential,
)


def _get_authentication_method(parameters):
    auth_method = parameters.get("authentication", parameters.get("method"))
    if auth_method is not None:
        auth_method = auth_method.upper()
        if auth_method == "AZURE_DEFAULT":
            auth_method = None
    return auth_method


def _get_credential(parameters):
    """
    Returns the appropriate credential given the input supplied by the original
    connect string.
    """

    tokens = []
    auth_method = _get_authentication_method(parameters)

    if auth_method is None or auth_method == "AZURE_SERVICE_PRINCIPAL":
        if "azure_client_secret" in parameters:
            tokens.append(
                ClientSecretCredential(
                    _get_required_parameter(parameters, "azure_tenant_id"),
                    _get_required_parameter(parameters, "azure_client_id"),
                    _get_required_parameter(parameters, "azure_client_secret"),
                )
            )
        elif "azure_client_certificate_path" in parameters:
            tokens.append(
                CertificateCredential(
                    _get_required_parameter(parameters, "azure_tenant_id"),
                    _get_required_parameter(parameters, "azure_client_id"),
                    _get_required_parameter(
                        parameters, "azure_client_certificate_path"
                    ),
                )
            )
    if auth_method is None or auth_method == "AZURE_MANAGED_IDENTITY":
        client_id = parameters.get("azure_managed_identity_client_id")
        if client_id is not None:
            tokens.append(ManagedIdentityCredential(client_id=client_id))

    if len(tokens) == 0:
        message = (
            "Authentication options were not available in Connection String"
        )
        raise Exception(message)
    elif len(tokens) == 1:
        return tokens[0]
    tokens.append(EnvironmentCredential())
    return ChainedTokenCredential(*tokens)


def _get_password(pwd_string, parameters):
    try:
        pwd = json.loads(pwd_string)
    except json.JSONDecodeError:
        message = (
            "Password is expected to be JSON"
            " containing Azure Vault details."
        )
        raise Exception(message)

    pwd["value"] = pwd.pop("uri")
    pwd["type"] = "azurevault"

    # make authentication section
    pwd["authentication"] = authentication = {}

    authentication["method"] = auth_method = _get_authentication_method(
        parameters
    )

    if auth_method is None or auth_method == "AZURE_SERVICE_PRINCIPAL":
        if "azure_client_secret" in parameters:
            authentication["azure_tenant_id"] = _get_required_parameter(
                parameters, "azure_tenant_id"
            )
            authentication["azure_client_id"] = _get_required_parameter(
                parameters, "azure_client_id"
            )
            authentication["azure_client_secret"] = _get_required_parameter(
                parameters, "azure_client_secret"
            )

        elif "azure_client_certificate_path" in parameters:
            authentication["azure_tenant_id"] = (
                _get_required_parameter(parameters, "azure_tenant_id"),
            )
            authentication["azure_client_id"] = (
                _get_required_parameter(parameters, "azure_client_id"),
            )
            authentication["azure_client_certificate_path"] = (
                _get_required_parameter(
                    parameters, "azure_client_certificate_path"
                )
            )

    if auth_method is None or auth_method == "AZURE_MANAGED_IDENTITY":
        authentication["azure_managed_identity_client_id"] = parameters.get(
            "azure_managed_identity_client_id"
        )
    return pwd


def _get_required_parameter(parameters, name, location="connection string"):
    try:
        return parameters[name]
    except KeyError:
        message = f'Parameter named "{name}" is missing from {location}'
        raise Exception(message) from None


def _get_setting(client, key, sub_key, label, required=True):
    """
    Returns the configuration setting given the client, key and label.
    """
    try:
        if key.endswith("/"):
            actual_key = f"{key}{sub_key}"
        else:
            actual_key = f"{key}/{sub_key}"
        obj = client.get_configuration_setting(key=actual_key, label=label)
    except ResourceNotFoundError:
        if required:
            message = f"Missing required configuration key: {actual_key}"
            raise Exception(message)
        return None
    return obj.value


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
    parameters["appconfigname"] = (
        protocol_arg[:pos].rstrip("/").rstrip(".azconfig.io") + ".azconfig.io"
    )
    return parameters


def password_type_azure_vault_hook(args):
    uri = _get_required_parameter(args, "value", '"password" key section')
    credential = args.get("credential")

    if credential is None:
        # if credential not present, this might be coming
        # from oci config provider, so create credential
        # for azure key vault.
        auth = args.get("authentication")
        if auth is None:
            raise Exception(
                "Azure Vault authentication details were not provided."
            )
        credential = _get_credential(auth)

    pattern = re.compile(
        r"(?P<vault_url>https://[A-Za-z0-9._-]+)/"
        r"secrets/(?P<secretKey>[A-Za-z][A-Za-z0-9-]*)$"
    )
    match = pattern.match(uri)
    if match is None:
        raise Exception("Invalid Azure Vault details")
    vault_url = match.group("vault_url")
    secret_key = match.group("secretKey")
    secret_client = SecretClient(vault_url, credential)
    return secret_client.get_secret(secret_key).value


def _process_config(parameters, connect_params):
    """
    Processes the configuration stored in the Azure App configuration store.
    """

    credential = _get_credential(parameters)
    client = AzureAppConfigurationClient(
        "https://" + _get_required_parameter(parameters, "appconfigname"),
        credential,
    )
    key = _get_required_parameter(parameters, "key")
    label = parameters.get("label")

    # get the common parameters
    config = {}
    config["connect_descriptor"] = _get_setting(
        client, key, "connect_descriptor", label
    )
    config["user"] = _get_setting(client, key, "user", label, required=False)
    pwd = _get_setting(client, key, "password", label, required=False)
    if pwd is not None:
        config["password"] = _get_password(pwd, parameters)

    config["config_time_to_live"] = _get_setting(
        client, key, "config_time_to_live", label, required=False
    )
    config["config_time_to_live_grace_period"] = _get_setting(
        client, key, "config_time_to_live_grace_period", label, required=False
    )

    # get the python-oracledb specific parameters
    settings = _get_setting(client, key, "pyo", label, required=False)
    if settings is not None:
        config["pyo"] = json.loads(settings)

    # set the configuration
    connect_params.set_from_config(config)


def config_azure_hook(protocol, protocol_arg, connect_params):
    """
    Hook for handling parameters stored in an Azure configuration store.
    """
    parameters = _parse_parameters(protocol_arg)
    _process_config(parameters, connect_params)


oracledb.register_password_type("azurevault", password_type_azure_vault_hook)
oracledb.register_protocol("config-azure", config_azure_hook)
