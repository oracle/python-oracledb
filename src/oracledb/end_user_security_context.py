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
# end_user_security_context.py
#
# Contains the methods required to create the end user security context.
# -----------------------------------------------------------------------------

from . import errors, thin_impl
from .base import BaseMetaClass


class EndUserSecurityContext(metaclass=BaseMetaClass):

    def __init__(self):
        errors._raise_err(errors.ERR_INTERNAL_CREATION_REQUIRED)


def create_end_user_security_context(
    end_user_identity: str | tuple[str, str | None],
    database_access_token: str,
    data_roles: list[str] | None = None,
    attributes: dict | None = None,
) -> EndUserSecurityContext:
    """
    Creates a new end user security context that contains the identity and
    authorization details.

    The ``end_user_identity`` parameter can be a string or a two-item tuple and
    specifies the unique identifier of an end user. For OCI IAM or Microsoft
    Entra ID users, this parameter must be a string containing the token issued
    by these IAMs after user authentication. For database managed users, set
    this parameter to a two-item tuple containing the local database user name
    and a key, where the key may be None if not required.

    The ``database_access_token`` parameter is a string containing the security
    token issued by OCI IAM or Entra ID that authorizes an application to
    access Oracle Database. This can either be an On-Behalf-Of (OBO) token or a
    Client Credentials token.

    The ``data_roles`` parameter is a list containing the names of data roles
    granted to the application or local database user.

    The ``attributes`` parameter is a dictionary containing the attribute-value
    pairs of the end user context attributes.
    """
    end_user_token = end_user_name = key = None

    if isinstance(end_user_identity, str) and end_user_identity:
        end_user_token = end_user_identity
    elif isinstance(end_user_identity, tuple) and len(end_user_identity) == 2:
        end_user_name, key = end_user_identity
        if not isinstance(end_user_name, str) or not end_user_name:
            raise ValueError(
                "For a two-item tuple end_user_identity, the first item "
                "(end_user_name) must be a non-empty string."
            )

        if key is not None and (not isinstance(key, str) or not key):
            raise ValueError(
                "For a two-item tuple end_user_identity, the second item "
                "(key) must be a non-empty string or None."
            )
    else:
        raise ValueError(
            "end_user_identity must be a token string or a two-item tuple "
            "containing (end_user_name, key)."
        )

    if not isinstance(database_access_token, str) or not database_access_token:
        raise ValueError("database_access_token must be a non-empty string.")

    impl = thin_impl.EndUserSecurityContextImpl.create(
        end_user_token,
        end_user_name,
        key,
        database_access_token,
        data_roles,
        attributes,
    )
    context = EndUserSecurityContext.__new__(EndUserSecurityContext)
    context._impl = impl
    return context
