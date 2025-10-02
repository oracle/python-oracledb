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
# Implement a data frame that can be used for efficiently transferring Arrow
# array data to other data frame libraries.
# -----------------------------------------------------------------------------

from .arrow_array import ArrowArray
from .arrow_impl import DataFrameImpl
from .base import BaseMetaClass
from . import errors


class DataFrame(metaclass=BaseMetaClass):
    _impl = None

    def __init__(self):
        errors._raise_err(errors.ERR_INTERNAL_CREATION_REQUIRED)

    @classmethod
    def _from_arrow(cls, obj):
        df = cls.__new__(cls)
        df._initialize(DataFrameImpl.from_arrow_stream(obj))
        return df

    @classmethod
    def _from_impl(cls, impl):
        df = cls.__new__(cls)
        df._initialize(impl)
        return df

    def _initialize(self, impl):
        """
        Initializes the object given the implementation.
        """
        self._impl = impl
        self._arrays = [ArrowArray._from_impl(a) for a in impl.get_arrays()]
        self._arrays_by_name = {}
        for array in self._arrays:
            self._arrays_by_name[array.name] = array

    def __arrow_c_stream__(self, requested_schema=None):
        """
        Returns the ArrowArrayStream PyCapsule which allows direct conversion
        to foreign data frames that support this interface.
        """
        if requested_schema is not None:
            raise NotImplementedError("requested_schema")
        return self._impl.get_stream_capsule()

    def column_arrays(self) -> list[ArrowArray]:
        """
        Returns a list of ArrowArray objects, each containing a select list
        column.
        """
        return self._arrays

    def column_names(self) -> list[str]:
        """
        Returns a list of the column names in the data frame.
        """
        return [a.name for a in self._arrays]

    def get_column(self, i: int) -> ArrowArray:
        """
        Returns an :ref:`ArrowArray <oraclearrowarrayobj>` object for the
        column at the given index ``i``. If the index is out of range, an
        IndexError exception is raised.
        """
        if i < 0 or i >= self.num_columns():
            raise IndexError(
                f"Column index {i} is out of bounds for "
                f"DataFrame with {self.num_columns()} columns"
            )
        return self._arrays[i]

    def get_column_by_name(self, name: str) -> ArrowArray:
        """
        Returns an :ref:`ArrowArray <oraclearrowarrayobj>` object for the
        column with the given name ``name``. If the column name is not found,
        a KeyError exception is raised.
        """
        try:
            return self._arrays_by_name[name]
        except KeyError:
            raise KeyError(f"Column {name} not found in DataFrame")

    def num_columns(self) -> int:
        """
        Returns the number of columns in the data frame.
        """
        return len(self._arrays)

    def num_rows(self) -> int:
        """
        Returns the number of rows in the data frame.
        """
        return len(self._arrays[0])
