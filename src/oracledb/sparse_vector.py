# -----------------------------------------------------------------------------
# Copyright (c) 2024, Oracle and/or its affiliates.
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
# sparse_vector.py
#
# Contains the SparseVector class which stores information about a sparse
# vector. Sparse vectors are available in Oracle Database 23.6 and higher.
# -----------------------------------------------------------------------------

import array
from typing import Union

from .base_impl import get_array_type_code_uint32, SparseVectorImpl
from . import __name__ as MODULE_NAME

ARRAY_TYPE_CODE_UINT32 = get_array_type_code_uint32()


class SparseVector:
    """
    Provides information about sparse vectors.
    """

    __module__ = MODULE_NAME

    def __init__(
        self,
        num_dimensions: int,
        indices: Union[list, array.array],
        values: Union[list, array.array],
    ):
        if (
            not isinstance(indices, array.array)
            or indices.typecode != ARRAY_TYPE_CODE_UINT32
        ):
            indices = array.array(ARRAY_TYPE_CODE_UINT32, indices)
        if not isinstance(values, array.array):
            values = array.array("d", values)
        if len(indices) != len(values):
            raise TypeError("indices and values must be of the same length!")
        self._impl = SparseVectorImpl.from_values(
            num_dimensions, indices, values
        )

    def __repr__(self):
        return (
            f"{MODULE_NAME}.{self.__class__.__name__}({self.num_dimensions}, "
            f"{self.indices}, {self.values})"
        )

    def __str__(self):
        return (
            f"[{self.num_dimensions}, {list(self.indices)}, "
            f"{list(self.values)}]"
        )

    @classmethod
    def _from_impl(cls, impl):
        vector = cls.__new__(cls)
        vector._impl = impl
        return vector

    @property
    def indices(self) -> array.array:
        """
        Returns the indices (zero-based) of non-zero values in the vector.
        """
        return self._impl.indices

    @property
    def num_dimensions(self) -> int:
        """
        Returns the number of dimensions contained in the vector.
        """
        return self._impl.num_dimensions

    @property
    def values(self) -> array.array:
        """
        Returns the non-zero values stored in the vector.
        """
        return self._impl.values
