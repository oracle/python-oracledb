# ------------------------------------------------------------------------------
# Copyright (c) 2026 Oracle and/or its affiliates.
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
END_USER_IDENTITY_KEY = "EUC_END_USER_IDENTITY"


def set_end_user_identity(value):
    if not (
        value is None
        or isinstance(value, str)
        or (
            isinstance(value, (list, tuple))
            and len(value) == 2
            and all(isinstance(v, str) for v in value)
        )
    ):
        raise ValueError(
            "End user identity must be None, a string or a 2-tuple "
            "(end_user_name, key) and each entry in the tuple must be a string"
        )
    oracledb.save_secret(
        END_USER_IDENTITY_KEY,
        json.dumps(value),
        thread_local=True,
    )


def get_end_user_identity():
    secret = oracledb.get_secret(END_USER_IDENTITY_KEY, thread_local=True)
    if secret is not None:
        return json.loads(secret.value)


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
        return self.get_response(request)


def validate_context_value(identity, auth_flow):
    """
    Returns (end_user_name, key) or end_user_token.

    - If value is a string => (OBO can be used)
    - If value is a tuple/list => (OBO should not be used)
      expected format: (end_user_name, key)
    """
    if auth_flow == "on_behalf_of" and isinstance(identity, (tuple, list)):
        raise ValueError(
            "auth_flow='on_behalf_of': cannot be used with "
            "(end_user_name, key)."
        )


def get_end_user_sec_context(end_user_sec_params, identity):
    spi_type = end_user_sec_params["spi_type"]
    supporting_plugin = importlib.import_module(f"oracledb.plugins.{spi_type}")
    database_access_token = supporting_plugin.get_database_access_token(
        end_user_sec_params, identity
    )
    return oracledb.create_end_user_security_context(
        end_user_identity=identity,
        database_access_token=database_access_token,
        data_roles=end_user_sec_params.get("data_roles"),
        attributes=end_user_sec_params.get("attributes"),
    )


def has_security_params(extra_auth_params):
    return bool(
        extra_auth_params and extra_auth_params.get("end_user_sec_params")
    )


def end_user_sec_context_hook(params: oracledb.ConnectParams):
    if has_security_params(params.extra_auth_params):
        end_user_sec_params = params.extra_auth_params["end_user_sec_params"]

        def on_connect_callback(connection: oracledb.Connection):
            auth_flow = end_user_sec_params["auth_flow"]
            identity = get_end_user_identity()
            if identity is not None:
                validate_context_value(identity, auth_flow)
                context = get_end_user_sec_context(
                    end_user_sec_params, identity
                )
                connection.set_end_user_security_context(context)

        params.set(on_connect_callback=on_connect_callback)


# Register the hook for end_user_sec_provider
oracledb.register_params_hook(end_user_sec_context_hook)
