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
# secret_values.py
#
# Contains classes that allow storage of secret values that should not be
# exposed in memory dumps.
# -----------------------------------------------------------------------------

import contextvars
import datetime
import threading
import warnings
from typing import Any

from .base_impl import SecretValueImpl


class SecretValue:

    def __init__(
        self, value: str, *, expires: datetime.datetime | None = None
    ):
        self._impl = SecretValueImpl(value, expires)

    def __eq__(self, other):
        if isinstance(other, SecretValue):
            return self.value_bytes == other.value_bytes
        elif isinstance(other, bytes):
            return self.value_bytes == other
        elif isinstance(other, str):
            return self.value == other
        return NotImplemented

    def __hash__(self):
        return self._impl.__hash__()

    @property
    def value(self) -> str | None:
        """
        Returns the secret value as a string. If the value has expired, *None*
        will be returned instead.
        """
        return self._impl.get_value()

    @value.setter
    def value(
        self, value: str, expires: datetime.datetime | None = None
    ) -> None:
        """
        Sets the value of the secret from a string.
        """
        self._impl.set_value(value, expires)

    @property
    def value_bytes(self) -> bytes | None:
        """
        Returns the secret value as bytes. If the value has expired, *None*
        will be returned instead.
        """
        return self._impl.get_value_as_bytes()

    @value_bytes.setter
    def value_bytes(
        self, value: bytes, expires: datetime.datetime | None = None
    ) -> None:
        """
        Sets the value of the secret from bytes.
        """
        self._impl.set_value(value, expires)


class SecretValueCache:

    def __init__(self):
        self.lock = threading.Lock()
        self.context_local_data = contextvars.ContextVar(
            "oracledb_secret_values"
        )
        self.global_data = dict()

    def clear_all_values(self, context_local: bool) -> None:
        """
        Clears all secrets from the cache. If context_local is True, only the
        current context's local cache is cleared; otherwise, the global cache
        is cleared.
        """
        if context_local:
            self.context_local_data.set({})
        else:
            with self.lock:
                self.global_data.clear()

    def get_value(self, key: Any, context_local: bool) -> SecretValue | None:
        """
        Returns a value in the cache, or *None* if the key is not found. If the
        value has expired, *None* is also returned and the value is removed
        from the cache.
        """
        if context_local:
            secret_value = self.context_local_data.get({}).get(key)
        else:
            with self.lock:
                secret_value = self.global_data.get(key)
        if secret_value is not None and secret_value.value is None:
            self.store_value(key, None, context_local, None)
        else:
            return secret_value

    def store_value(
        self,
        key: Any,
        value: str | bytes,
        context_local: bool,
        expires: datetime.datetime | None,
    ) -> SecretValue:
        """
        Stores a value in the cache. If the value is None, the value is removed
        from the cache.
        """
        if value is None:
            secret_value = None
        else:
            secret_value = SecretValue(value, expires=expires)
        if context_local:
            d = self.context_local_data.get({}).copy()
            if value is None:
                d.pop(key, None)
            else:
                d[key] = secret_value
            self.context_local_data.set(d)
        else:
            with self.lock:
                if value is None:
                    self.global_data.pop(key, None)
                else:
                    self.global_data[key] = secret_value
        return secret_value


# create an instance of the cache for use by the functions below
secret_value_cache = SecretValueCache()


def clear_all_secrets(
    *, thread_local: bool | None = None, context_local: bool = False
) -> None:
    """
    Clears all secrets stored in the cache. If ``context_local`` is True, only
    the current context's cache is cleared; otherwise, the global cache is
    cleared.

    The ``thread_local`` parameter is deprecated; use ``context_local``
    instead. If supplied, its value takes precedence over ``context_local``
    and a warning is emitted.
    """
    if thread_local is not None:
        warnings.warn(
            "'thread_local' is deprecated; use 'context_local' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        context_local = thread_local
    secret_value_cache.clear_all_values(context_local)


def get_secret(
    key: Any,
    *,
    thread_local: bool | None = None,
    context_local: bool = False,
) -> SecretValue | None:
    """
    Returns a secret stored in the cache. If the ``context_local`` parameter is
    *True*, it will be specific to the current execution context; otherwise, it
    will be the value available to all threads. If the value is not found in
    the cache, *None* is returned. If the value is found in the cache but it
    has expired, *None* is also returned and the value is removed from the
    cache.

    The ``thread_local`` parameter is deprecated; use ``context_local``
    instead. If supplied, its value takes precedence over ``context_local``
    and a warning is emitted.
    """
    if thread_local is not None:
        warnings.warn(
            "'thread_local' is deprecated; use 'context_local' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        context_local = thread_local
    return secret_value_cache.get_value(key, context_local)


def save_secret(
    key: Any,
    value: str | bytes | None,
    *,
    thread_local: bool | None = None,
    context_local: bool = False,
    expires: datetime.datetime | None = None,
) -> SecretValue:
    """
    Saves a secret in an internal cache for later retrieval. This can help
    protect a secret from being exposed in memory dumps. If the
    ``context_local`` parameter is *True*, the cache will be specific to the
    current execution context; otherwise, the value will be available
    to all threads. If the value supplied is *None* and a value already exists
    in the cache for the supplied key, then the stored value will be removed
    from the cache.

    The ``thread_local`` parameter is deprecated; use ``context_local``
    instead. If supplied, its value takes precedence over ``context_local``
    and a warning is emitted.
    """
    if thread_local is not None:
        warnings.warn(
            "'thread_local' is deprecated; use 'context_local' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        context_local = thread_local
    return secret_value_cache.store_value(key, value, context_local, expires)
