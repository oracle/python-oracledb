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
# dataframe.py
#
# Implement DataFrame class as documented in the standard
# https://data-apis.org/dataframe-protocol/latest/API.html
# -----------------------------------------------------------------------------

from typing import Any, Dict, Iterable, List, Optional, Sequence

from .column import OracleColumn

from .protocol import DataFrame


class OracleDataFrame(DataFrame):
    """
    OracleDataFrame is an implementation of the DataFrame Interchange Protocol.
    It provides an interface for exchanging tabular data between different data
    frame libraries (e.g. pandas, pyarrow, polars).
    """

    def __init__(
        self,
        oracle_arrow_arrays: List,
        allow_copy: bool = True,
    ):
        self._cols = []
        self._cols_map = {}
        self._rows = None
        self._arrays = oracle_arrow_arrays
        for ora_arrow_array in oracle_arrow_arrays:
            column = OracleColumn(ora_arrow_array=ora_arrow_array)
            self._rows = column.size()
            self._cols.append(column)
            self._cols_map[ora_arrow_array.name] = column
        self.allow_copy = allow_copy

    def __dataframe__(
        self,
        nan_as_null: bool = False,  # noqa: FBT001
        allow_copy: bool = True,  # noqa: FBT001
    ) -> DataFrame:
        """
        Returns a data frame adhering to the DataFrame Interchange protocol.
        """
        return self

    def get_chunks(
        self, n_chunks: Optional[int] = None
    ) -> Iterable[DataFrame]:
        """
        Returns an iterator for each of the chunks in the data frame. Since
        there is currently only one chunk, this simply returns itself.
        """
        yield self

    def column_arrays(self) -> List:
        """
        Returns a list of the Arrow arrays corresponding to each column in the
        data frame.
        """
        return self._arrays

    def column_names(self) -> List[str]:
        """
        Returns a list of the names of the columns in the data frame.
        """
        return list(self._cols_map.keys())

    def get_column(self, i: int) -> OracleColumn:
        """
        Returns a column from the data frame given its zero-based index. If the
        index is out of range, an IndexError exception is raised.
        """
        if i < 0 or i >= self.num_columns():
            raise IndexError(
                f"Column index {i} is out of bounds for "
                f"DataFrame with {self.num_columns()} columns"
            )
        return self._cols[i]

    def get_column_by_name(self, name: str) -> OracleColumn:
        """
        Returns a column from the data frame given the name of the column. If
        the column name is not found, a KeyError exception is raised.
        """
        if name not in self._cols_map:
            raise KeyError(f"Column {name} not found in DataFrame")
        return self._cols_map[name]

    def get_columns(self) -> List[OracleColumn]:
        """
        Returns a list of all of the columns in the data frame.
        """
        return self._cols

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Returns metadata for the data frame. Currently this returns
        information about the number of columns (num_columns), number of rows
        (num_rows) and number of chunks (num_chunks).
        """
        return {
            "num_columns": self.num_columns(),
            "num_rows": self.num_rows(),
            "num_chunks": self.num_chunks(),
        }

    def num_chunks(self) -> int:
        """
        Returns the number of chunks (contiguous memory blocks) in the data
        frame. Currently this always returns 1.
        """
        return 1

    def num_columns(self) -> int:
        """
        Returns the number of columns in the data frame.
        """
        return len(self._cols)

    def num_rows(self) -> int:
        """
        Returns the number of rows in the data frame.
        """
        return self._rows

    def select_columns(self, indices: Sequence[int]) -> "DataFrame":
        """
        Create a new DataFrame by selecting a subset of columns by index.
        """
        raise NotImplementedError()

    def select_columns_by_name(self, names: Sequence[str]) -> "DataFrame":
        """
        Create a new DataFrame by selecting a subset of columns by name.
        """
        raise NotImplementedError()
