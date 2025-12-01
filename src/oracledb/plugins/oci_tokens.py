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

import enum
import pathlib

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import oci
import oracledb


class AuthType(str, enum.Enum):
    ConfigFileAuthentication = "ConfigFileAuthentication".lower()
    InstancePrincipal = "InstancePrincipal".lower()
    SecurityToken = "SecurityToken".lower()
    SecurityTokenSimple = "SecurityTokenSimple".lower()
    SimpleAuthentication = "SimpleAuthentication".lower()


def _config_file_based_authentication(token_auth_config):
    """
    Config file base authentication implementation: config parameters
    are provided in a file.
    """
    config = _load_oci_config(token_auth_config)
    client = oci.identity_data_plane.DataplaneClient(config)
    return _generate_access_token(client, token_auth_config)


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
        private_key_pem = "".join(
            line.strip()
            for line in private_key_pem.splitlines()
            if not (
                line.startswith("-----BEGIN") or line.startswith("-----END")
            )
        )

    return {"private_key": private_key_pem, "public_key": public_key_pem}


def _instance_principal_authentication(token_auth_config):
    """
    Instance principal authentication: for compute instances
    with dynamic group access.
    """
    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
    client = oci.identity_data_plane.DataplaneClient(config={}, signer=signer)
    return _generate_access_token(client, token_auth_config)


def _load_oci_config(token_auth_config):
    """
    Load OCI configuration using the file location and profile specified
    in token_auth_config, or fall back to OCI defaults.
    """
    file_location = token_auth_config.get(
        "file_location", oci.config.DEFAULT_LOCATION
    )
    profile = token_auth_config.get("profile", oci.config.DEFAULT_PROFILE)
    config = oci.config.from_file(file_location, profile)
    oci.config.validate_config(config)
    return config


def _security_token_authentication(token_auth_config):
    """
    Session token-based authentication: uses the security token specified by
    the security_token_file parameter based on the OCI config file.
    """
    config = _load_oci_config(token_auth_config)
    client = _security_token_create_dataplane_client(config)
    return _generate_access_token(client, token_auth_config)


def _security_token_create_dataplane_client(config):
    """
    Create and return an OCI Identity Data Plane client using
    the security token and private key specified in the given OCI config.
    """
    token = pathlib.Path(config["security_token_file"]).read_text()
    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    return oci.identity_data_plane.DataplaneClient(config, signer=signer)


def _security_token_simple_authentication(token_auth_config):
    """
    Session token-based authentication: uses security token authentication.
    Config parameters are passed as parameters.
    """
    config = {
        "key_file": token_auth_config["key_file"],
        "fingerprint": token_auth_config["fingerprint"],
        "tenancy": token_auth_config["tenancy"],
        "region": token_auth_config["region"],
        "security_token_file": token_auth_config["security_token_file"],
    }
    client = _security_token_create_dataplane_client(config)
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


def generate_token(token_auth_config, refresh=False):
    """
    Generates an OCI access token based on provided credentials.
    """
    auth_type = token_auth_config["auth_type"].lower()
    if auth_type == AuthType.ConfigFileAuthentication:
        return _config_file_based_authentication(token_auth_config)
    elif auth_type == AuthType.InstancePrincipal:
        return _instance_principal_authentication(token_auth_config)
    elif auth_type == AuthType.SecurityToken:
        return _security_token_authentication(token_auth_config)
    elif auth_type == AuthType.SecurityTokenSimple:
        return _security_token_simple_authentication(token_auth_config)
    elif auth_type == AuthType.SimpleAuthentication:
        return _simple_authentication(token_auth_config)


def has_oci_auth_type(extra_auth_params):
    """
    Validates that extra_auth_params contains a valid 'auth_type'
    """
    if extra_auth_params is None:
        return False
    auth_type = extra_auth_params.get("auth_type")
    return auth_type is not None and auth_type.lower() in AuthType


def oci_token_hook(params: oracledb.ConnectParams):
    """
    OCI-specific hook for generating a token.
    """
    if has_oci_auth_type(params.extra_auth_params):

        def token_callback(refresh):
            return generate_token(params.extra_auth_params, refresh)

        params.set(access_token=token_callback)


# Register the token hook for OCI
oracledb.register_params_hook(oci_token_hook)
