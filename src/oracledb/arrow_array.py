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
# arrow_array.py
#
# Implement an ArrowArray that is used for efficiently transferring Arrow
# array data to other data frame libraries.
# -----------------------------------------------------------------------------

from .arrow_impl import ArrowArrayImpl

from . import errors


class ArrowArray:
    _impl = None

    def __init__(self):
        errors._raise_err(errors.ERR_INTERNAL_CREATION_REQUIRED)

    def __len__(self):
        return self.num_rows

    def __repr__(self):
        return (
            f"ArrowArray(name={self.name}, "
            f"len={self.num_rows}, "
            f"type={self.dtype})"
        )

    def __str__(self):
        return self.__repr__()

    @classmethod
    def _from_arrow(cls, obj):
        array = cls.__new__(cls)
        array._impl = ArrowArrayImpl.from_arrow_array(obj)
        return array

    @classmethod
    def _from_impl(cls, impl):
        array = cls.__new__(cls)
        array._impl = impl
        return array

    def __arrow_c_array__(self, requested_schema=None):
        """
        Returns a tuple containing an ArrowSchema and ArrowArray PyCapsules.
        """
        if requested_schema is not None:
            raise NotImplementedError("requested_schema")
        return (
            self._impl.get_schema_capsule(),
            self._impl.get_array_capsule(),
        )

    def __arrow_c_schema__(self):
        """
        Returns an ArrowSchema PyCapsule.
        """
        return self._impl.get_schema_capsule()

    @property
    def dtype(self) -> str:
        """
        Returns the data type associated with the array.
        """
        return self._impl.get_data_type()

    @property
    def name(self) -> str:
        """
        Returns the name associated with the array.
        """
        return self._impl.get_name()

    @property
    def null_count(self) -> int:
        """
        Returns the number of rows that contain null values.
        """
        return self._impl.get_null_count()

    @property
    def num_rows(self) -> int:
        """
        Returns the number of rows in the array.
        """
        return self._impl.get_num_rows()
