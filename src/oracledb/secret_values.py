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

import datetime
import threading
from typing import Any, Optional, Union

from .base_impl import SecretValueImpl


class SecretValue:

    def __init__(
        self, value: str, *, expires: Optional[datetime.datetime] = None
    ):
        self._impl = SecretValueImpl(value, expires)

    def __hash__(self):
        return self._impl.__hash__()

    @property
    def value(self) -> Optional[str]:
        """
        Returns the secret value as a string. If the value has expired, *None*
        will be returned instead.
        """
        return self._impl.get_value()

    @value.setter
    def value(
        self, value: str, expires: Optional[datetime.datetime] = None
    ) -> None:
        """
        Sets the value of the secret from a string.
        """
        self._impl.set_value(value, expires)

    @property
    def value_bytes(self) -> Optional[bytes]:
        """
        Returns the secret value as bytes. If the value has expired, *None*
        will be returned instead.
        """
        return self._impl.get_value_as_bytes()

    @value_bytes.setter
    def value_bytes(
        self, value: bytes, expires: Optional[datetime.datetime] = None
    ) -> None:
        """
        Sets the value of the secret from bytes.
        """
        self._impl.set_value(value, expires)


class SecretValueCache:

    def __init__(self):
        self.lock = threading.Lock()
        self.thread_local_data = threading.local()
        self.global_data = dict()

    def get_value(
        self, key: Any, thread_local: bool = False
    ) -> Optional[SecretValue]:
        """
        Returns a value in the cache, or *None* if the key is not found. If the
        value has expired, *None* is also returned and the value is removed
        from the cache.
        """
        with self.lock:
            d = (
                self.thread_local_data.__dict__
                if thread_local
                else self.global_data
            )
            secret_value = d.get(key)
            if secret_value is not None and secret_value.value is None:
                del d[key]
                return None
            return secret_value

    def store_value(
        self,
        key: Any,
        value: Union[str, bytes],
        thread_local: bool = False,
        expires: Optional[datetime.datetime] = None,
    ) -> SecretValue:
        """
        Stores a value in the cache.
        """
        with self.lock:
            d = (
                self.thread_local_data.__dict__
                if thread_local
                else self.global_data
            )
            if value is None:
                if key in d:
                    del d[key]
            else:
                secret_value = SecretValue(value, expires=expires)
                d[key] = secret_value
                return secret_value


# create an instance of the cache for use by the functions below
secret_value_cache = SecretValueCache()


def get_secret(
    key: Any, *, thread_local: bool = False
) -> Optional[SecretValue]:
    """
    Returns a secret stored in the cache. If the ``thread_local`` parameter is
    *True*, it will be specific to the particular thread that is running;
    otherwise, it will be the value available to all threads. If the value is
    not found in the cache, *None* is returned. If the value is found in the
    cache but it has expired, *None* is also returned and the value is removed
    from the cache.
    """
    return secret_value_cache.get_value(key, thread_local)


def save_secret(
    key: Any,
    value: Optional[Union[str, bytes]],
    *,
    thread_local: bool = False,
    expires: Optional[datetime.datetime] = None,
) -> SecretValue:
    """
    Saves a secret in an internal cache for later retrieval. This can help
    protect a secret from being exposed in memory dumps. If the
    ``thread_local`` parameter is *True*, the cache will be specific to the
    particular thread that is running; otherwise, the value will be available
    to all threads. If the value supplied is *None* and a value already exists
    in the cache for the supplied key, then the stored value will be removed
    from the cache.
    """
    return secret_value_cache.store_value(key, value, thread_local, expires)
