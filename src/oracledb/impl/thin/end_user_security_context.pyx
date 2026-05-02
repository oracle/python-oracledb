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

cdef class EndUserSecurityContextImpl:
    cdef:
        SecretValueImpl oson_bytes

    @classmethod
    def create_end_user_security_context(
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
            OsonEncoder encoder = OsonEncoder.__new__(OsonEncoder)
            bytes oson_bytes

        value = {}
        value["ver"] = "1.0"
        if end_user_token is not None:
            value["end_user_token"] = end_user_token
        if end_user_name is not None:
            value["end_user_name"] = end_user_name
        if key is not None:
            value["end_user_contextid"] = key
        if database_access_token is not None:
            value["database_access_token"] = database_access_token
        if data_roles is not None:
            value["data_roles"] = list(data_roles)
        if attributes is not None:
            value["attributes"] = [
                dict(name=k, values=v) for k, v in attributes.items()
            ]

        encoder.encode(value)
        if encoder._pos > 65535:
            errors._raise_err(
                errors.ERR_INVALID_END_USER_SECURITY_CONTEXT_LENGTH
            )
        oson_bytes = encoder._data[:encoder._pos]
        impl.oson_bytes = SecretValueImpl(oson_bytes)
        return impl
