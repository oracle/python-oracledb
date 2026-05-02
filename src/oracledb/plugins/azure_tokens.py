# -----------------------------------------------------------------------------
# Copyright (c) 2024, 2026, Oracle and/or its affiliates.
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

import datetime
import enum

import msal
import oracledb


class AuthType(str, enum.Enum):
    AzureServicePrincipal = "AzureServicePrincipal".lower()


def _build_msal_app(params):
    return msal.ConfidentialClientApplication(
        client_id=params["client_id"],
        client_credential=params["client_credential"],
        authority=params["authority"],
    )


def _service_principal_credentials(token_auth_config):
    """
    Returns the access token for authentication as a service principal.
    """
    # Initialize the Confidential Client Application
    cca = _build_msal_app(token_auth_config)
    auth_response = cca.acquire_token_for_client(
        scopes=[token_auth_config["scopes"]]
    )

    if "access_token" in auth_response:
        return auth_response["access_token"]


def get_database_access_token(deepsec_params, user_token):
    auth_flow = deepsec_params.get("auth_flow")
    if auth_flow == "client_credentials":
        return get_database_access_token_client_cred_flow(deepsec_params)
    elif auth_flow == "on_behalf_of":
        return get_database_access_token_obo_flow(deepsec_params, user_token)
    else:
        raise ValueError(f"Incorrect value for auth_flow: {auth_flow}.")


def get_database_access_token_client_cred_flow(deepsec_params):
    key = (
        deepsec_params["authority"],
        deepsec_params["client_id"],
        deepsec_params["client_credential"],
        deepsec_params["scopes"],
    )
    secret_value = oracledb.get_secret(key)
    if secret_value is not None:
        return secret_value.value

    # fetch fresh token, if not present in cache
    app = _build_msal_app(deepsec_params)
    result = app.acquire_token_for_client(scopes=[deepsec_params["scopes"]])
    if "access_token" not in result:
        raise Exception(f"Token acquisition failed: {result}")

    token = result.get("access_token")
    expires_in = result.get("expires_in")
    expires = datetime.datetime.fromtimestamp(
        expires_in - 60, datetime.timezone.utc
    )
    oracledb.save_secret(key, token, expires=expires)
    return token


def get_database_access_token_obo_flow(deepsec_params, user_token):
    key = (
        user_token,
        deepsec_params["authority"],
        deepsec_params["client_id"],
        deepsec_params["client_credential"],
        deepsec_params["scopes"],
    )
    secret_value = oracledb.get_secret(key)
    if secret_value is not None:
        return secret_value.value

    # fetch fresh token, if not present in cache
    app = _build_msal_app(deepsec_params)
    result = app.acquire_token_on_behalf_of(
        user_assertion=user_token,
        scopes=[deepsec_params["scopes"]],
    )
    if "access_token" not in result:
        raise Exception(f"OBO token acquisition failed: {result}")

    token = result.get("access_token")
    expires_in = result.get("expires_in")
    expires = datetime.datetime.fromtimestamp(
        expires_in - 60, datetime.timezeon.utc
    )
    oracledb.save_secret(key, token, expires=expires)
    return token


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
