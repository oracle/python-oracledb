# ------------------------------------------------------------------------------
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
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# end_user_sec_provider.pyx
#
# Python file that automates token retrieval and context setup.
# ------------------------------------------------------------------------------

import importlib
import json

import oracledb

# key to use in thread local cache
END_USER_ATTRIBUTES_KEY = "EUC_END_USER_ATTRIBUTES"
END_USER_DATA_ROLES_KEY = "EUC_END_USER_DATA_ROLES"
END_USER_IDENTITY_KEY = "EUC_END_USER_IDENTITY"


def _get_secret(key):
    """
    Returns the secret value stored under the given key or None if no such
    secret was stored.
    """
    secret = oracledb.get_secret(key, thread_local=True)
    if secret is not None:
        return json.loads(secret.value)


def _save_secret(key, value):
    """
    Saves the secret value under the given key, or clears the value if the
    value None is supplied.
    """
    if value is not None:
        value = json.dumps(value)
    oracledb.save_secret(key, value, thread_local=True)


def get_end_user_attributes():
    """
    Returns the context attributes that were saved earlier.
    """
    return _get_secret(END_USER_ATTRIBUTES_KEY)


def get_end_user_data_roles():
    """
    Returns the data roles that were saved earlier.
    """
    return _get_secret(END_USER_DATA_ROLES_KEY)


def get_end_user_identity():
    """
    Returns the user identity that was saved earlier.
    """
    return _get_secret(END_USER_IDENTITY_KEY)


def set_end_user_attributes(value):
    """
    Securely stores the context attributes for the current thread.
    """
    _save_secret(END_USER_ATTRIBUTES_KEY, value)


def set_end_user_data_roles(value):
    """
    Securely stores the data roles for the current thread.
    """
    _save_secret(END_USER_DATA_ROLES_KEY, value)


def set_end_user_identity(value):
    """
    Securely stores the end user identity for the current thread.
    """
    _save_secret(END_USER_IDENTITY_KEY, value)


# Django specific Middleware
class EndUserSecMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        identity = None
        try:
            identity = json.loads(request.COOKIES["identity"])
        except KeyError:
            auth_header = request.META.get("HTTP_AUTHORIZATION")
            if auth_header is not None and auth_header.startswith("Bearer "):
                identity = auth_header.split()[1]
        set_end_user_identity(identity)
        try:
            return self.get_response(request)
        finally:
            oracledb.clear_all_secrets(thread_local=True)


def get_end_user_sec_context(end_user_sec_params, identity):
    auth_flow = end_user_sec_params["auth_flow"]
    if auth_flow == "on_behalf_of" and not isinstance(identity, str):
        raise ValueError(
            "auth_flow='on_behalf_of' requires a token for its user identity"
        )
    spi_type = end_user_sec_params["spi_type"]
    supporting_plugin = importlib.import_module(f"oracledb.plugins.{spi_type}")
    database_access_token = supporting_plugin.get_database_access_token(
        end_user_sec_params, identity
    )
    data_roles = get_end_user_data_roles()
    attributes = get_end_user_attributes()
    return oracledb.create_end_user_security_context(
        end_user_identity=identity,
        database_access_token=database_access_token,
        data_roles=data_roles or end_user_sec_params.get("data_roles"),
        attributes=attributes or end_user_sec_params.get("attributes"),
    )


def has_security_params(extra_auth_params):
    return bool(
        extra_auth_params and extra_auth_params.get("end_user_sec_params")
    )


def end_user_sec_context_hook(params: oracledb.ConnectParams):
    if has_security_params(params.extra_auth_params):
        end_user_sec_params = params.extra_auth_params["end_user_sec_params"]

        def set_end_user_sec_context(connection):
            identity = get_end_user_identity()
            if identity is not None:
                context = get_end_user_sec_context(
                    end_user_sec_params, identity
                )
                connection.set_end_user_security_context(context)

        async def async_on_connect_callback(
            connection: oracledb.AsyncConnection,
        ):
            set_end_user_sec_context(connection)

        def on_connect_callback(connection: oracledb.Connection):
            if isinstance(connection, oracledb.AsyncConnection):
                return async_on_connect_callback(connection)
            set_end_user_sec_context(connection)

        params.set(on_connect_callback=on_connect_callback)


# Register the hook for end_user_sec_provider
oracledb.register_params_hook(end_user_sec_context_hook)
