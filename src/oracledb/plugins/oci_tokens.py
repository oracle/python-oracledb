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
# oci_tokens.py
#
# Methods that generates an OCI access token using the OCI SDK
# -----------------------------------------------------------------------------

import oci
import oracledb
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def generate_token(token_auth_config, refresh=False):
    """
    Generates an OCI access token based on provided credentials.
    """
    user_auth_type = token_auth_config.get("auth_type") or ""
    auth_type = user_auth_type.lower()
    if auth_type == "configfileauthentication":
        return _config_file_based_authentication(token_auth_config)
    elif auth_type == "simpleauthentication":
        return _simple_authentication(token_auth_config)
    elif auth_type == "instanceprincipal":
        return _instance_principal_authentication(token_auth_config)
    else:
        raise ValueError(
            f"Unrecognized auth_type authentication method {user_auth_type}"
        )


def _get_key_pair():
    """
    Generates a public-private key pair for proof of possession.
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
    )
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_key_pem = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("utf-8")
    )

    if not oracledb.is_thin_mode():
        p_key = "".join(
            line.strip()
            for line in private_key_pem.splitlines()
            if not (
                line.startswith("-----BEGIN") or line.startswith("-----END")
            )
        )
        private_key_pem = p_key

    return {"private_key": private_key_pem, "public_key": public_key_pem}


def _generate_access_token(client, token_auth_config):
    """
    Token generation logic used by authentication methods.
    """
    key_pair = _get_key_pair()
    scope = token_auth_config.get("scope", "urn:oracle:db::id::*")

    details = oci.identity_data_plane.models.GenerateScopedAccessTokenDetails(
        scope=scope, public_key=key_pair["public_key"]
    )
    response = client.generate_scoped_access_token(
        generate_scoped_access_token_details=details
    )

    return (response.data.token, key_pair["private_key"])


def _config_file_based_authentication(token_auth_config):
    """
    Config file base authentication implementation: config parameters
    are provided in a file.
    """
    file_location = token_auth_config.get(
        "file_location", oci.config.DEFAULT_LOCATION
    )
    profile = token_auth_config.get("profile", oci.config.DEFAULT_PROFILE)

    # Load OCI config
    config = oci.config.from_file(file_location, profile)
    oci.config.validate_config(config)

    # Initialize service client with default config file
    client = oci.identity_data_plane.DataplaneClient(config)

    return _generate_access_token(client, token_auth_config)


def _simple_authentication(token_auth_config):
    """
    Simple authentication: config parameters are passed as parameters
    """
    config = {
        "user": token_auth_config["user"],
        "key_file": token_auth_config["key_file"],
        "fingerprint": token_auth_config["fingerprint"],
        "tenancy": token_auth_config["tenancy"],
        "region": token_auth_config["region"],
        "profile": token_auth_config["profile"],
    }
    oci.config.validate_config(config)

    client = oci.identity_data_plane.DataplaneClient(config)
    return _generate_access_token(client, token_auth_config)


def _instance_principal_authentication(token_auth_config):
    """
    Instance principal authentication: for compute instances
    with dynamic group access.
    """
    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
    client = oci.identity_data_plane.DataplaneClient(config={}, signer=signer)
    return _generate_access_token(client, token_auth_config)


def oci_token_hook(params: oracledb.ConnectParams):
    """
    OCI-specific hook for generating a token.
    """
    if params.extra_auth_params is not None:

        def token_callback(refresh):
            return generate_token(params.extra_auth_params, refresh)

        params.set(access_token=token_callback)


# Register the token hook for OCI
oracledb.register_params_hook(oci_token_hook)
