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
# azure_tokens.py
#
# Methods that generates an OAuth2 access token using the MSAL SDK
# -----------------------------------------------------------------------------

import enum

import msal
import oracledb


class AuthType(str, enum.Enum):
    AzureServicePrincipal = "AzureServicePrincipal".lower()


def _service_principal_credentials(token_auth_config):
    """
    Returns the access token for authentication as a service principal.
    """
    msal_config = {
        "authority": token_auth_config["authority"],
        "client_id": token_auth_config["client_id"],
        "client_credential": token_auth_config["client_credential"],
    }
    # Initialize the Confidential Client Application
    cca = msal.ConfidentialClientApplication(**msal_config)
    auth_response = cca.acquire_token_for_client(
        scopes=[token_auth_config["scopes"]]
    )

    if "access_token" in auth_response:
        return auth_response["access_token"]


def generate_token(token_auth_config, refresh=False):
    """
    Generates an Azure access token based on provided credentials.
    """
    auth_type = token_auth_config["auth_type"].lower()
    if auth_type == AuthType.AzureServicePrincipal:
        return _service_principal_credentials(token_auth_config)


def has_azure_auth_type(extra_auth_params):
    """
    Validates that extra_auth_params contains a valid 'auth_type'
    """
    if extra_auth_params is None:
        return False
    auth_type = extra_auth_params.get("auth_type")
    return auth_type is not None and auth_type.lower() in AuthType


def azure_token_hook(params: oracledb.ConnectParams):
    """
    Azure-specific hook for generating a token.
    """
    if has_azure_auth_type(params.extra_auth_params):

        def token_callback(refresh):
            return generate_token(params.extra_auth_params, refresh)

        params.set(access_token=token_callback)


# Register the token hook for Azure
oracledb.register_params_hook(azure_token_hook)
