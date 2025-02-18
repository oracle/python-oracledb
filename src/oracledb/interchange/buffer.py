# -----------------------------------------------------------------------------
# Copyright (c) 2025, Oracle and/or its affiliates.
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
# buffer.py
#
# Implements the Buffer class as documented in DataFrame API
# -----------------------------------------------------------------------------

from typing import Tuple

from .protocol import (
    Buffer,
    DlpackDeviceType,
)


class OracleColumnBuffer(Buffer):
    """
    OracleColumnBuffer represents a contiguous memory buffer in the DataFrame
    Interchange Protocol. It provides access to raw binary data that backs
    various components of the data frame such as column values, validity masks
    and offsets for variable-length data types.
    """

    def __init__(self, buffer_type, size_in_bytes, address) -> None:
        self.buffer_type = buffer_type
        self.size_in_bytes = size_in_bytes
        self.address = address

    def __dlpack__(self):
        """
        Represent this structure as a DLPack interface.
        """
        raise NotImplementedError("__dlpack__")

    def __dlpack_device__(self) -> Tuple[DlpackDeviceType, None]:
        """
        Device type and device ID for where the data
        in the buffer resides
        """
        return (DlpackDeviceType.CPU, None)

    def __repr__(self) -> str:
        device = self.__dlpack_device__()[0].name
        return (
            f"OracleColumnBuffer(bufsize={self.bufsize}, "
            f"ptr={self.ptr}, type={self.buffer_type}, device={device!r})"
        )

    @property
    def bufsize(self) -> int:
        """
        Returns the total size of buffer in bytes.
        """
        return self.size_in_bytes

    @property
    def ptr(self) -> int:
        """
        Returns the memory address of the buffer.
        """
        return self.address
