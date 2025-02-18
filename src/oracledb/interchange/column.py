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
# column.py
#
# Implements the Column class as documented in DataFrame API
# -----------------------------------------------------------------------------

from typing import Any, Dict, Iterable, Optional, Tuple

from .buffer import OracleColumnBuffer
from .protocol import (
    CategoricalDescription,
    Column,
    Dtype,
    ColumnBuffers,
    ColumnNullType,
    DtypeKind,
)

from .nanoarrow_bridge import (
    NANOARROW_TIME_UNIT_SECOND,
    NANOARROW_TIME_UNIT_MILLI,
    NANOARROW_TIME_UNIT_MICRO,
    NANOARROW_TIME_UNIT_NANO,
    NANOARROW_TYPE_DOUBLE,
    NANOARROW_TYPE_FLOAT,
    NANOARROW_TYPE_INT64,
    NANOARROW_TYPE_STRING,
    NANOARROW_TYPE_TIMESTAMP,
    NANOARROW_TYPE_DECIMAL128,
)


class OracleColumn(Column):
    """
    OracleColumn represents a column in the DataFrame Interchange Protocol. It
    provides a standardized way to expose a column's data, metadata and chunks,
    allowing interoperability between data frame libraries.
    """

    def __init__(self, ora_arrow_array: object):
        self.ora_arrow_array = ora_arrow_array
        self._buffer_info = ora_arrow_array.get_buffer_info()

    def __arrow_c_array__(self, requested_schema=None):
        return self.ora_arrow_array.__arrow_c_array__(
            requested_schema=requested_schema
        )

    def _data_buffer(self):
        buffer = self._buffer_info.get("data")
        if buffer is None:
            return None
        size_bytes, address = buffer
        data_buffer = OracleColumnBuffer(
            size_in_bytes=size_bytes, address=address, buffer_type="data"
        )
        return data_buffer, self.dtype

    def _offsets_buffer(self):
        buffer = self._buffer_info.get("offsets")
        if buffer is None:
            return None
        size_bytes, address = buffer
        offsets_buffer = OracleColumnBuffer(
            size_in_bytes=size_bytes, address=address, buffer_type="offsets"
        )
        dtype = (DtypeKind.INT, 32, "i", "=")
        return offsets_buffer, dtype

    def _validity_buffer(self):
        buffer = self._buffer_info.get("validity")
        if buffer is None:
            return None
        size_bytes, address = buffer
        validity_buffer = OracleColumnBuffer(
            size_in_bytes=size_bytes, address=address, buffer_type="validity"
        )
        dtype = (DtypeKind.BOOL, 1, "b", "=")
        return validity_buffer, dtype

    def describe_categorical(self) -> CategoricalDescription:
        """
        Returns a description of a categorical data type.
        """
        raise NotImplementedError()

    @property
    def describe_null(self) -> Tuple[ColumnNullType, Optional[int]]:
        """
        Returns a description of the null representation used by the column.
        """
        if self.null_count == 0:
            return ColumnNullType.NON_NULLABLE, None
        else:
            return ColumnNullType.USE_BITMASK, 0

    @property
    def dtype(self) -> Dtype:
        """
        Returns the data type of the column. The returned dtype provides
        information on the storage format and the type of data in the column.
        """
        if self.ora_arrow_array.arrow_type == NANOARROW_TYPE_INT64:
            return (DtypeKind.INT, 64, "l", "=")
        elif self.ora_arrow_array.arrow_type == NANOARROW_TYPE_DOUBLE:
            return (DtypeKind.FLOAT, 64, "g", "=")
        elif self.ora_arrow_array.arrow_type == NANOARROW_TYPE_FLOAT:
            return (DtypeKind.FLOAT, 64, "g", "=")
        elif self.ora_arrow_array.arrow_type == NANOARROW_TYPE_STRING:
            return (DtypeKind.STRING, 8, "u", "=")
        elif self.ora_arrow_array.arrow_type == NANOARROW_TYPE_TIMESTAMP:
            if self.ora_arrow_array.time_unit == NANOARROW_TIME_UNIT_MICRO:
                return (DtypeKind.DATETIME, 64, "tsu:", "=")
            elif self.ora_arrow_array.time_unit == NANOARROW_TIME_UNIT_SECOND:
                return (DtypeKind.DATETIME, 64, "tss:", "=")
            elif self.ora_arrow_array.time_unit == NANOARROW_TIME_UNIT_MILLI:
                return (DtypeKind.DATETIME, 64, "tsm:", "=")
            elif self.ora_arrow_array.time_unit == NANOARROW_TIME_UNIT_NANO:
                return (DtypeKind.DATETIME, 64, "tsn:", "=")
        elif self.ora_arrow_array.arrow_type == NANOARROW_TYPE_DECIMAL128:
            array = self.ora_arrow_array
            return (
                DtypeKind.DECIMAL,
                128,
                f"d:{array.precision}.{array.scale}",
                "=",
            )

    def get_buffers(self) -> ColumnBuffers:
        """
        Returns a dictionary specifying the memory buffers backing the column.
        This currently consists of:
        - "data": the main buffer storing column values
        - "validity": a buffer containing null/missing values
        - "offsets": a buffer for variable-length types like string
        """
        return {
            "data": self._data_buffer(),
            "validity": self._validity_buffer(),
            "offsets": self._offsets_buffer(),
        }

    def get_chunks(self, n_chunks: Optional[int] = None) -> Iterable[Column]:
        """
        Return an iterator containing the column chunks. Currently this only
        returns itself.
        """
        yield self

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Returns metadata about the column.
        """
        return {
            "name": self.ora_arrow_array.name,
            "size": self.size(),
            "num_chunks": self.num_chunks(),
        }

    @property
    def null_count(self) -> int:
        """
        Returns the number of null elements.
        """
        return self.ora_arrow_array.null_count

    def num_chunks(self) -> int:
        """
        Returns the number of chunks used by the column. This method currently
        always returns the value 1, implying that the column uses contiguous
        memory.
        """
        return 1

    @property
    def offset(self) -> int:
        """
        Returns the offset of the first element.
        """
        return self.ora_arrow_array.offset

    def size(self) -> int:
        """
        Returns the number of elements in the column.
        """
        return len(self.ora_arrow_array)
