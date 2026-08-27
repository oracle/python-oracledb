# -----------------------------------------------------------------------------
# Copyright (c) 2021, 2026, Oracle and/or its affiliates.
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
# lob.py
#
# Contains the LOB class for managing BLOB, CLOB, NCLOB and BFILE data.
# -----------------------------------------------------------------------------

import functools

from .base import BaseMetaClass
from .base_impl import DbType, DB_TYPE_BFILE, DB_TYPE_BLOB
from . import errors


class BaseLOB(metaclass=BaseMetaClass):

    def __del__(self):
        self._impl.free_lob()

    def _check_is_bfile(self):
        if self._impl.dbtype is not DB_TYPE_BFILE:
            errors._raise_err(errors.ERR_OPERATION_ONLY_SUPPORTED_ON_BFILE)

    def _check_not_bfile(self):
        if self._impl.dbtype is DB_TYPE_BFILE:
            errors._raise_err(errors.ERR_OPERATION_NOT_SUPPORTED_ON_BFILE)

    def _check_value_to_write(self, value):
        """
        Checks the value to write and returns the actual value to write.
        Character LOBs must write strings but can accept UTF-8 encoded bytes
        (which will be decoded to strings). Binary LOBs must write bytes but
        can accept strings (which will be encoded in UTF-8).
        """
        if self.type is DB_TYPE_BLOB:
            if isinstance(value, str):
                return value.encode()
            elif isinstance(value, bytes):
                return value
        else:
            if isinstance(value, str):
                return value
            elif isinstance(value, bytes):
                return value.decode()
        type_name = type(value).__name__
        raise TypeError(f"expecting string or bytes, found {type_name}")

    def _close(self) -> None:
        """
        Common logic for close().
        first.
        """
        yield from self._impl.close()

    def _fileexists(self) -> bool:
        """
        Common logic for fileexists().
        """
        self._check_is_bfile()
        yield from self._impl.file_exists()

    def _getchunksize(self) -> int:
        """
        Common logic for getchunksize().
        """
        self._check_not_bfile()
        return (yield from self._impl.get_chunk_size())

    def _isopen(self) -> bool:
        """
        Common logic for isopen().
        """
        return (yield from self._impl.get_is_open())

    def _open(self) -> None:
        """
        Common logic for open().
        """
        yield from self._impl.open()

    def _read(self, offset: int = 1, amount: int | None = None) -> str | bytes:
        """
        Common logic for read().
        """
        if amount is None:
            amount = self._impl.get_max_amount()
            if amount >= offset:
                amount = amount - offset + 1
            else:
                amount = 1
        elif amount <= 0:
            errors._raise_err(errors.ERR_INVALID_LOB_AMOUNT)
        if offset <= 0:
            errors._raise_err(errors.ERR_INVALID_LOB_OFFSET)
        return (yield from self._impl.read(offset, amount))

    def _size(self) -> int:
        """
        Common logic for size().
        """
        return (yield from self._impl.get_size())

    def _trim(self, new_size: int = 0, *, newSize: int | None = None) -> None:
        """
        Common logic for trim().
        """
        self._check_not_bfile()
        if newSize is not None:
            if new_size != 0:
                errors._raise_err(
                    errors.ERR_DUPLICATED_PARAMETER,
                    deprecated_name="newSize",
                    new_name="new_size",
                )
            new_size = newSize
        yield from self._impl.trim(new_size)

    def _write(self, data: str | bytes, offset: int = 1) -> None:
        """
        Common logic for write().
        """
        self._check_not_bfile()
        yield from self._impl.write(self._check_value_to_write(data), offset)

    @classmethod
    def _from_impl(cls, impl):
        if isinstance(impl, BaseLOB):
            return impl
        lob = cls.__new__(cls)
        lob._impl = impl
        return lob

    def getfilename(self) -> tuple:
        """
        Returns a two-tuple consisting of the directory alias and file name for
        a BFILE type LOB.
        """
        self._check_is_bfile()
        return self._impl.get_file_name()

    def setfilename(self, dir_alias: str, name: str) -> None:
        """
        Sets the directory alias and name of a BFILE type LOB.
        """
        self._check_is_bfile()
        self._impl.set_file_name(dir_alias, name)

    @property
    def type(self) -> DbType:
        """
        This read-only attribute returns the type of the LOB as one of the
        database type constants.
        """
        return self._impl.dbtype


def sync_operation(f):
    """
    Decorator function which is used on all synchronous operations that
    interact with the database.
    """

    @functools.wraps(f)
    def wrapped_f(self, *args, **kwargs):
        return self._impl.process_sync_operation(
            self, f.__name__, args, kwargs
        )

    return wrapped_f


class LOB(BaseLOB):

    def __reduce__(self):
        value = self.read()
        return (type(value), (value,))

    def __str__(self):
        return self.read()

    @sync_operation
    def close(self) -> None:
        """
        Closes the LOB. Call this when writing is completed so that the indexes
        associated with the LOB can be updated -– but only if open() was called
        first.
        """
        pass

    @sync_operation
    def fileexists(self) -> bool:
        """
        Returns a boolean indicating if the file referenced by a BFILE type LOB
        exists.
        """
        pass

    @sync_operation
    def getchunksize(self) -> int:
        """
        Returns the chunk size for the LOB. Reading and writing to the LOB in
        chunks of multiples of this size will improve performance.
        """
        pass

    @sync_operation
    def isopen(self) -> bool:
        """
        Returns a boolean indicating if the LOB has been opened using the
        method open().
        """
        pass

    @sync_operation
    def open(self) -> None:
        """
        Opens the LOB for writing. This will improve performance when writing
        to the LOB in chunks and there are functional or extensible indexes
        associated with the LOB. If this method is not called, each write will
        perform an open internally followed by a close after the write has been
        completed.
        """
        pass

    @sync_operation
    def read(self, offset: int = 1, amount: int | None = None) -> str | bytes:
        """
        Returns a portion (or all) of the data in the LOB. Note that the amount
        and offset are in bytes for BLOB and BFILE type LOBs and in UCS-2 code
        points for CLOB and NCLOB type LOBs. UCS-2 code points are equivalent
        to characters for all but supplemental characters. If supplemental
        characters are in the LOB, the offset and amount will have to be chosen
        carefully to avoid splitting a character.
        """
        pass

    @sync_operation
    def size(self) -> int:
        """
        Returns the size of the data in the LOB. For BLOB and BFILE type LOBs,
        this is the number of bytes. For CLOB and NCLOB type LOBs, this is the
        number of UCS-2 code points. UCS-2 code points are equivalent to
        characters for all but supplemental characters.
        """
        pass

    @sync_operation
    def trim(self, new_size: int = 0, *, newSize: int | None = None) -> None:
        """
        Trims the LOB to the new size (the second parameter is deprecated and
        should not be used).
        """
        pass

    @sync_operation
    def write(self, data: str | bytes, offset: int = 1) -> None:
        """
        Writes the data to the LOB at the given offset. The offset is in bytes
        for BLOB type LOBs and in UCS-2 code points for CLOB and NCLOB type
        LOBs. UCS-2 code points are equivalent to characters for all but
        supplemental characters. If supplemental characters are in the LOB, the
        offset will have to be chosen carefully to avoid splitting a character.
        Note that if you want to make the LOB value smaller, you must use the
        trim() function.
        """
        pass


def async_operation(f):
    """
    Decorator function which is used on all asynchronous operations that
    interact with the database.
    """

    @functools.wraps(f)
    async def wrapped_f(self, *args, **kwargs):
        return await self._impl.process_async_operation(
            self, f.__name__, args, kwargs
        )

    return wrapped_f


class AsyncLOB(BaseLOB):

    @async_operation
    async def close(self) -> None:
        """
        Closes the LOB. Call this when writing is completed so that the indexes
        associated with the LOB can be updated -– but only if open() was called
        first.
        """
        pass

    @async_operation
    async def fileexists(self) -> bool:
        """
        Returns a boolean indicating if the file referenced by a BFILE type LOB
        exists.
        """
        pass

    @async_operation
    async def getchunksize(self) -> int:
        """
        Returns the chunk size for the LOB. Reading and writing to the LOB in
        chunks of multiples of this size will improve performance.
        """
        pass

    @async_operation
    async def isopen(self) -> bool:
        """
        Returns a boolean indicating if the LOB has been opened using the
        method open().
        """
        pass

    @async_operation
    async def open(self) -> None:
        """
        Opens the LOB for writing. This will improve performance when writing
        to the LOB in chunks and there are functional or extensible indexes
        associated with the LOB. If this method is not called, each write will
        perform an open internally followed by a close after the write has been
        completed.
        """
        pass

    @async_operation
    async def read(
        self, offset: int = 1, amount: int | None = None
    ) -> str | bytes:
        """
        Returns a portion (or all) of the data in the LOB. Note that the amount
        and offset are in bytes for BLOB and BFILE type LOBs and in UCS-2 code
        points for CLOB and NCLOB type LOBs. UCS-2 code points are equivalent
        to characters for all but supplemental characters. If supplemental
        characters are in the LOB, the offset and amount will have to be chosen
        carefully to avoid splitting a character.
        """
        pass

    @async_operation
    async def size(self) -> int:
        """
        Returns the size of the data in the LOB. For BLOB and BFILE type LOBs
        this is the number of bytes. For CLOB and NCLOB type LOBs this is the
        number of UCS-2 code points. UCS-2 code points are equivalent to
        characters for all but supplemental characters.
        """
        pass

    @async_operation
    async def trim(
        self, new_size: int = 0, *, newSize: int | None = None
    ) -> None:
        """
        Trims the LOB to the new size (the second parameter is deprecated and
        should not be used).
        """
        pass

    @async_operation
    async def write(self, data: str | bytes, offset: int = 1) -> None:
        """
        Writes the data to the LOB at the given offset. The offset is in bytes
        for BLOB type LOBs and in UCS-2 code points for CLOB and NCLOB type
        LOBs. UCS-2 code points are equivalent to characters for all but
        supplemental characters. If supplemental characters are in the LOB, the
        offset will have to be chosen carefully to avoid splitting a character.
        Note that if you want to make the LOB value smaller, you must use the
        trim() function.
        """
        pass
