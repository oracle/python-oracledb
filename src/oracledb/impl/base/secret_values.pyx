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
# secret_values.pyx
#
# Cython file defining the classes and methods used for encoding and decoding
# VECTOR data (embedded in base_impl.pyx).
#------------------------------------------------------------------------------

@cython.final
cdef class SecretValueImpl:

    def __init__(self, object value, expires=None):
        self.set_value(value, expires)

    def __hash__(self):
        return hash(self.get_value_as_bytes())

    cdef bytearray _xor_bytes(self, bytearray value):
        """
        Perform an XOR of the input value with the obfuscator. Performing once
        with the secret value creates an obfuscated value. Performing a second
        time with the obfuscated value returns the original secret value.
        """
        cdef:
            ssize_t length, i
            bytearray result
        length = len(self.obfuscator)
        result = bytearray(length)
        for i in range(length):
            result[i] = value[i] ^ self.obfuscator[i]
        return result

    cpdef str get_value(self):
        """
        Returns the original value that was stored, unless the value has
        expired, in which case None is returned.
        """
        if not self.has_expired():
            return self._xor_bytes(self.value).decode()

    cdef bytes get_value_as_bytes(self):
        """
        Returns the original value that was stored, unless the value has
        expired, in which case None is returned.
        """
        if not self.has_expired():
            return bytes(self._xor_bytes(self.value))

    cpdef bool has_expired(self):
        """
        Returns whether or not the value has expired.
        """
        if self.expires is not None:
            return self.expires < datetime.datetime.now(datetime.timezone.utc)
        return False

    cpdef int set_value(self, str secret_value, object expires=None) except -1:
        """
        Creates and stores a byte array suitable for obfuscating the specified
        secret value, then uses it to store the secret value securely.
        """
        cdef bytearray secret_value_bytes = bytearray(secret_value.encode())
        self.obfuscator = bytearray(
            secrets.token_bytes(len(secret_value_bytes))
        )
        self.value = self._xor_bytes(secret_value_bytes)
        if expires is not None and \
                (not isinstance(expires, PY_TYPE_DATETIME) or \
                expires.tzinfo is None):
            raise ValueError("expires must be a timezone-aware date")
        self.expires = expires
