#------------------------------------------------------------------------------
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
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# end_user_security_context.pyx
#
# Cython file defining the EndUserSecurityContextImpl.
#------------------------------------------------------------------------------

cdef SecretValueImpl _encode_payload(dict payload):
    """
    Encodes a payload as OSON and returns the encoded bytes securely.
    Raises an error if the encoded payload exceeds 65535 bytes.
    """
    cdef OsonEncoder encoder = OsonEncoder.__new__(OsonEncoder)
    encoder.encode(payload)
    if encoder._pos > 65535:
        errors._raise_err(
            errors.ERR_INVALID_END_USER_SECURITY_CONTEXT_LENGTH
        )
    return SecretValueImpl(encoder._data[:encoder._pos])


cdef class EndUserSecurityContextImpl:
    cdef:
        SecretValueImpl full_payload_oson_bytes
        SecretValueImpl partial_payload_oson_bytes
        SecretValueImpl hash_value
        bint is_localuser

    @classmethod
    def create(
        cls,
        str end_user_token,
        str end_user_name,
        str key,
        str database_access_token,
        list data_roles,
        dict attributes
    ):
        """
        Creates an instance from its component values.
        """
        cdef:
            EndUserSecurityContextImpl impl = cls.__new__(cls)
            str hash_value

        full_payload = {}
        partial_payload = {}
        hash_value_parts = []
        full_payload["ver"] = "1.0"
        if end_user_token is not None:
            full_payload["end_user_token"] = end_user_token
            hash_value_parts.append(end_user_token)
        if end_user_name is not None:
            full_payload["end_user_name"] = end_user_name
        if key is not None:
            full_payload["end_user_contextid"] = key
        if database_access_token is not None:
            full_payload["database_access_token"] = database_access_token
            hash_value_parts.append(database_access_token)
        if data_roles is not None:
            full_payload["data_roles"] = list(data_roles)
            hash_value_parts.append(
                "".join(f"{len(role)}:{role}" for role in sorted(data_roles))
            )
        if attributes is not None:
            full_payload["attributes"] = [
                dict(name=k, values=v) for k, v in attributes.items()
            ]
            partial_payload["attributes"] = [
                dict(name=k, values=v) for k, v in attributes.items()
            ]

        impl.full_payload_oson_bytes = _encode_payload(full_payload)
        if end_user_name is None:
            if attributes is not None:
                impl.partial_payload_oson_bytes = _encode_payload(partial_payload)
            hash_value = "".join(hash_value_parts)
            impl.hash_value = SecretValueImpl(
                base64.b64encode(
                    hashlib.sha256(hash_value.encode()).digest()
                )
            )
        return impl
