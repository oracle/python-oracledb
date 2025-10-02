# -----------------------------------------------------------------------------
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
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
# fetch_info.py
#
# Contains the FetchInfo class which stores metadata about columns that are
# being fetched.
# -----------------------------------------------------------------------------

from typing import Union

import oracledb

from . import constants
from .base import BaseMetaClass
from .base_impl import (
    DbType,
    DB_TYPE_DATE,
    DB_TYPE_TIMESTAMP,
    DB_TYPE_TIMESTAMP_LTZ,
    DB_TYPE_TIMESTAMP_TZ,
    DB_TYPE_BINARY_FLOAT,
    DB_TYPE_BINARY_DOUBLE,
    DB_TYPE_BINARY_INTEGER,
    DB_TYPE_NUMBER,
    DB_TYPE_VECTOR,
)
from .dbobject import DbObjectType


class FetchInfo(metaclass=BaseMetaClass):
    """
    Identifies metadata of columns that are being fetched.
    """

    def __eq__(self, other):
        return tuple(self) == other

    def __getitem__(self, index):
        """
        Return the parts mandated by the Python Database API.
        """
        if index == 0 or index == -7:
            return self.name
        elif index == 1 or index == -6:
            return self.type_code
        elif index == 2 or index == -5:
            return self.display_size
        elif index == 3 or index == -4:
            return self.internal_size
        elif index == 4 or index == -3:
            return self.precision
        elif index == 5 or index == -2:
            return self.scale
        elif index == 6 or index == -1:
            return self.null_ok
        elif isinstance(index, slice):
            return tuple(self).__getitem__(index)
        raise IndexError("list index out of range")

    def __len__(self):
        """
        Length mandated by the Python Database API.
        """
        return 7

    def __repr__(self):
        return repr(tuple(self))

    def __str__(self):
        return str(tuple(self))

    @classmethod
    def _from_impl(cls, impl):
        info = cls.__new__(cls)
        info._impl = impl
        info._type = None
        return info

    @property
    def annotations(self) -> Union[dict, None]:
        """
        This read-only attribute returns a dictionary containing the
        `annotations <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
        GUID-1AC16117-BBB6-4435-8794-2B99F8F68052>`__ associated with the
        fetched column. If there are no annotations, the value *None* is
        returned. Annotations require Oracle Database version 23, or later. If
        using python-oracledb Thick mode, Oracle Client version 23 or later is
        also required.
        """
        return self._impl.annotations

    @property
    def display_size(self) -> Union[int, None]:
        """
        This read-only attribute returns the display size of the column.
        """
        if self._impl.max_size > 0:
            return self._impl.max_size
        dbtype = self._impl.dbtype
        if (
            dbtype is DB_TYPE_DATE
            or dbtype is DB_TYPE_TIMESTAMP
            or dbtype is DB_TYPE_TIMESTAMP_LTZ
            or dbtype is DB_TYPE_TIMESTAMP_TZ
        ):
            return 23
        elif (
            dbtype is DB_TYPE_BINARY_FLOAT
            or dbtype is DB_TYPE_BINARY_DOUBLE
            or dbtype is DB_TYPE_BINARY_INTEGER
            or dbtype is DB_TYPE_NUMBER
        ):
            if self._impl.precision:
                display_size = self._impl.precision + 1
                if self._impl.scale > 0:
                    display_size += self._impl.scale + 1
            else:
                display_size = 127
            return display_size

    @property
    def domain_name(self) -> Union[str, None]:
        """
        This read-only attribute returns the name of the `data use case
        domain
        <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-17D3A9C6
        -D993-4E94-BF6B-CACA56581F41>`__ associated with the fetched column. If
        there is no data use case domain, the value *None* is returned. `Data
        use case domains <https://www.oracle.com/pls/topic/lookup?ctx=dblatest
        &id=GUID-4743FDE1-7C6E-471B-BC9D-442383CCA2F9>`__ require Oracle
        Database version 23, or later. If using python-oracledb Thick mode,
        Oracle Client version 23 or later is also required.
        """
        return self._impl.domain_name

    @property
    def domain_schema(self) -> Union[str, None]:
        """
        This read-only attribute returns the schema of the `data use case
        domain <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-
        17D3A9C6-D993-4E94-BF6B-CACA56581F41>`__ associated with the fetched
        column. If there is no data use case domain, the value *None* is
        returned. `Data use case domains <https://www.oracle.com/pls/topic/
        lookup?ctx=dblatest&id=GUID-4743FDE1-7C6E-471B-BC9D-442383CCA2F9>`__
        require Oracle Database version 23, or later. If using python-oracledb
        Thick mode, Oracle Client version 23 or later is also required.
        """
        return self._impl.domain_schema

    @property
    def internal_size(self) -> Union[int, None]:
        """
        This read-only attribute returns the internal size of the column as
        mandated by the Python Database API.
        """
        if self._impl.max_size > 0:
            return self._impl.buffer_size

    @property
    def is_json(self) -> bool:
        """
        This read-only attribute returns whether the column is known to contain
        JSON data. This will be *True* when the type code is
        :data:`oracledb.DB_TYPE_JSON` as well as when an "IS JSON" constraint
        is enabled on LOB and VARCHAR2 columns.
        """
        return self._impl.is_json

    @property
    def is_oson(self) -> bool:
        """
        This read-only attribute returns whether the column is known to contain
        binary encoded `OSON <https://www.oracle.com/pls/topic/lookup?ctx=
        dblatest&id=GUID-911D302C-CFAF-406B-B6A5-4E99DD38ABAD>`__ data. This
        will be *True* when an "IS JSON FORMAT OSON" check constraint is
        enabled on BLOB columns.
        """
        return self._impl.is_oson

    @property
    def name(self) -> str:
        """
        This read-only attribute returns the name of the column as mandated by
        the Python Database API.
        """
        return self._impl.name

    @property
    def null_ok(self) -> bool:
        """
        This read-only attribute returns whether nulls are allowed in the
        column as mandated by the Python Database API.
        """
        return self._impl.nulls_allowed

    @property
    def precision(self) -> Union[int, None]:
        """
        This read-only attribute returns the precision of the column as
        mandated by the Python Database API.
        """
        if self._impl.precision or self._impl.scale:
            return self._impl.precision

    @property
    def scale(self) -> Union[int, None]:
        """
        This read-only attribute returns the scale of the column as mandated by
        the Python Database API.
        """
        if self._impl.precision or self._impl.scale:
            return self._impl.scale

    @property
    def type(self) -> Union[DbType, DbObjectType]:
        """
        This read-only attribute returns the type of the column. This will be
        an :ref:`Oracle Object Type <dbobjecttype>` if the column contains
        Oracle objects; otherwise, it will be one of the
        :ref:`database type constants <dbtypes>` defined at the module level.
        """
        if self._type is None:
            if self._impl.objtype is not None:
                self._type = DbObjectType._from_impl(self._impl.objtype)
            else:
                self._type = self._impl.dbtype
        return self._type

    @property
    def type_code(self) -> DbType:
        """
        This read-only attribute returns the type of the column as mandated by
        the Python Database API. The type will be one of the
        :ref:`database type constants <dbtypes>` defined at the module level.
        """
        return self._impl.dbtype

    @property
    def vector_dimensions(self) -> Union[int, None]:
        """
        This read-only attribute returns the number of dimensions required by
        VECTOR columns. If the column is not a VECTOR column or allows for any
        number of dimensions, the value returned is *None*.
        """
        if self._impl.dbtype is DB_TYPE_VECTOR:
            flags = self._impl.vector_flags
            if not (flags & constants.VECTOR_META_FLAG_FLEXIBLE_DIM):
                return self._impl.vector_dimensions

    @property
    def vector_format(self) -> Union[oracledb.VectorFormat, None]:
        """
        This read-only attribute returns the storage type used by VECTOR
        columns. The value of this attribute can be:

        - :data:`oracledb.VECTOR_FORMAT_BINARY` which represents 8-bit unsigned
          integers
        - :data:`oracledb.VECTOR_FORMAT_INT8` which represents 8-bit signed
          integers
        - :data:`oracledb.VECTOR_FORMAT_FLOAT32` which represents 32-bit
          floating-point numbers
        - :data:`oracledb.VECTOR_FORMAT_FLOAT64` which represents 64-bit
          floating-point numbers

        If the column is not a VECTOR column or allows for any type of storage,
        the value returned is *None*.
        """
        if (
            self._impl.dbtype is DB_TYPE_VECTOR
            and self._impl.vector_format != 0
        ):
            return oracledb.VectorFormat(self._impl.vector_format)

    @property
    def vector_is_sparse(self) -> Union[bool, None]:
        """
        This read-only attribute returns a boolean indicating if the vector is
        sparse or not.

        If the column contains vectors that are SPARSE, the value returned is
        *True*. If the column contains vectors that are DENSE, the value
        returned is *False*. If the column is not a VECTOR column, the value
        returned is *None*.
        """
        if self._impl.dbtype is DB_TYPE_VECTOR:
            flags = self._impl.vector_flags
            return bool(flags & constants.VECTOR_META_FLAG_SPARSE_VECTOR)
