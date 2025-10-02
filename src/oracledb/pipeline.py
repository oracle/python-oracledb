# -----------------------------------------------------------------------------
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
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
# pipeline.py
#
# Contains the Pipeline class used for executing multiple operations.
# -----------------------------------------------------------------------------

from typing import Any, Callable, Optional, Union

from . import utils
from .base import BaseMetaClass
from .base_impl import PipelineImpl, PipelineOpImpl, PipelineOpResultImpl
from .defaults import defaults
from .enums import PipelineOpType
from .errors import _Error
from .fetch_info import FetchInfo


class PipelineOp(metaclass=BaseMetaClass):

    def __repr__(self):
        cls_name = self.__class__._public_name
        return f"<{cls_name} of type {self.op_type.name}>"

    def _create_result(self):
        """
        Internal method used for creating a result object that is returned when
        running a pipeline.
        """
        impl = PipelineOpResultImpl(self._impl)
        result = PipelineOpResult.__new__(PipelineOpResult)
        result._operation = self
        result._impl = impl
        return result

    @property
    def arraysize(self) -> int:
        """
        This read-only attribute returns the array size that will be used when
        fetching query rows with :meth:`Pipeline.add_fetchall()`. For all other
        operations, the value returned is *0*.
        """
        return self._impl.arraysize

    @property
    def fetch_decimals(self) -> bool:
        """
        Returns whether or not to fetch columns of type ``NUMBER`` as
        ``decimal.Decimal`` values for a query.
        """
        return self._impl.fetch_decimals

    @property
    def fetch_lobs(self) -> bool:
        """
        Returns whether or not to fetch LOB locators for a query.
        """
        return self._impl.fetch_lobs

    @property
    def keyword_parameters(self) -> Any:
        """
        This read-only attribute returns the keyword parameters to the stored
        procedure or function being called by the operation, if applicable.
        """
        return self._impl.keyword_parameters

    @property
    def name(self) -> Union[str, None]:
        """
        This read-only attribute returns the name of the stored procedure or
        function being called by the operation, if applicable.
        """
        return self._impl.name

    @property
    def num_rows(self) -> int:
        """
        This read-only attribute returns the number of rows to fetch when
        performing a query of a specific number of rows. For all other
        operations, the value returned is *0*.
        """
        return self._impl.num_rows

    @property
    def op_type(self) -> PipelineOpType:
        """
        This read-only attribute returns the type of operation that is taking
        place.
        """
        return PipelineOpType(self._impl.op_type)

    @property
    def parameters(self) -> Any:
        """
        This read-only attribute returns the parameters to the stored procedure
        or function or the parameters bound to the statement being executed by
        the operation, if applicable.
        """
        return self._impl.parameters

    @property
    def return_type(self) -> Any:
        """
        This read-only attribute returns the return type of the stored function
        being called by the operation, if applicable.
        """
        return self._impl.return_type

    @property
    def rowfactory(self) -> Union[Callable, None]:
        """
        This read-only attribute returns the row factory callable function to
        be used in a query executed by the operation, if applicable.
        """
        return self._impl.rowfactory

    @property
    def statement(self) -> Union[str, None]:
        """
        This read-only attribute returns the statement being executed by the
        operation, if applicable.
        """
        return self._impl.statement


class PipelineOpResult(metaclass=BaseMetaClass):

    def __repr__(self):
        cls_name = self.__class__._public_name
        return (
            f"<{cls_name} for operation of type {self.operation.op_type.name}>"
        )

    @property
    def columns(self) -> Union[list[FetchInfo], None]:
        """
        This read-only attribute is a list of FetchInfo objects. This
        attribute will be *None* for operations that do not return rows.
        """
        if self._impl.fetch_metadata is not None:
            return [FetchInfo._from_impl(i) for i in self._impl.fetch_metadata]

    @property
    def error(self) -> Union[_Error, None]:
        """
        This read-only attribute returns the error that occurred when running
        this operation. If no error occurred, then the value *None* is
        returned.
        """
        return self._impl.error

    @property
    def operation(self) -> PipelineOp:
        """
        This read-only attribute returns the PipelineOp operation object that
        generated the result.
        """
        return self._operation

    @property
    def return_value(self) -> Any:
        """
        This read-only attribute returns the return value of the called PL/SQL
        function, if a function was called for the operation.
        """
        return self._impl.return_value

    @property
    def rows(self) -> Union[list, None]:
        """
        This read-only attribute returns the rows that were fetched by the
        operation, if a query was executed.
        """
        return self._impl.rows

    @property
    def warning(self) -> Union[_Error, None]:
        """
        This read-only attribute returns any warning that was encountered when
        running this operation. If no warning was encountered, then the value
        *None* is returned.
        """
        return self._impl.warning


class Pipeline(metaclass=BaseMetaClass):

    def __repr__(self):
        cls_name = self.__class__._public_name
        return f"<{cls_name} with {len(self._impl.operations)} operations>"

    def _add_op(self, op_impl):
        """
        Internal method for adding an PipelineOpImpl instance to the list of
        operations, creating an associated PipelineOp instance to correspond to
        it.
        """
        self._impl.operations.append(op_impl)
        op = PipelineOp.__new__(PipelineOp)
        op._impl = op_impl
        self._operations.append(op)
        return op

    def add_callfunc(
        self,
        name: str,
        return_type: Any,
        parameters: Optional[Union[list, tuple]] = None,
        keyword_parameters: Optional[dict] = None,
    ) -> PipelineOp:
        """
        Adds an operation to the pipeline that calls a stored PL/SQL function
        with the given parameters and return type. The created PipelineOp
        object is also returned from this function.

        When the Pipeline is executed, the PipelineOpResult object that is
        returned for this operation will have the
        :attr:`~PipelineOpResult.return_value` attribute populated with the
        return value of the PL/SQL function if the call completes
        successfully.
        """
        utils.verify_stored_proc_args(parameters, keyword_parameters)
        op_impl = PipelineOpImpl(
            op_type=PipelineOpType.CALL_FUNC,
            name=name,
            return_type=return_type,
            parameters=parameters,
            keyword_parameters=keyword_parameters,
        )
        return self._add_op(op_impl)

    def add_callproc(
        self,
        name: str,
        parameters: Optional[Union[list, tuple]] = None,
        keyword_parameters: Optional[dict] = None,
    ) -> PipelineOp:
        """
        Adds an operation that calls a stored procedure with the given
        parameters. The created PipelineOp object is also returned from
        this function.
        """
        utils.verify_stored_proc_args(parameters, keyword_parameters)
        op_impl = PipelineOpImpl(
            op_type=PipelineOpType.CALL_PROC,
            name=name,
            parameters=parameters,
            keyword_parameters=keyword_parameters,
        )
        return self._add_op(op_impl)

    def add_commit(self) -> PipelineOp:
        """
        Adds an operation that performs a commit.
        """
        op_impl = PipelineOpImpl(op_type=PipelineOpType.COMMIT)
        return self._add_op(op_impl)

    def add_execute(
        self,
        statement: str,
        parameters: Optional[Union[list, tuple, dict]] = None,
    ) -> PipelineOp:
        """
        Adds an operation that executes a statement with the given parameters.
        The created PipelineOp object is also returned from this function.

        Do not use this for queries that return rows.  Instead use
        :meth:`Pipeline.add_fetchall()`, :meth:`Pipeline.add_fetchmany()`, or
        :meth:`Pipeline.add_fetchone()`.
        """
        op_impl = PipelineOpImpl(
            op_type=PipelineOpType.EXECUTE,
            statement=statement,
            parameters=parameters,
        )
        return self._add_op(op_impl)

    def add_executemany(
        self,
        statement: str,
        parameters: Union[list, int],
    ) -> PipelineOp:
        """
        Adds an operation that executes a SQL statement once using all bind
        value mappings or sequences found in the sequence parameters. This can
        be used to insert, update, or delete multiple rows in a table. It can
        also invoke a PL/SQL procedure multiple times.

        The created PipelineOp object is also returned from this function.

        The ``parameters`` parameter can be a list of tuples, where each tuple
        item maps to one bind variable placeholder in ``statement``. It can
        also be a list of dictionaries, where the keys match the bind variable
        placeholder names in ``statement``. If there are no bind values, or
        values have previously been bound, the ``parameters`` value can be an
        integer specifying the number of iterations.
        """
        op_impl = PipelineOpImpl(
            op_type=PipelineOpType.EXECUTE_MANY,
            statement=statement,
            parameters=parameters,
        )
        return self._add_op(op_impl)

    def add_fetchall(
        self,
        statement: str,
        parameters: Optional[Union[list, tuple, dict]] = None,
        arraysize: Optional[int] = None,
        rowfactory: Optional[Callable] = None,
        fetch_lobs: Optional[bool] = None,
        fetch_decimals: Optional[bool] = None,
    ) -> PipelineOp:
        """
        Adds an operation that executes a query and returns all of the rows
        from the result set.  The created PipelineOp object is also returned
        from this function.

        When the Pipeline is executed, the PipelineOpResult object that is
        returned for this operation will have the
        :attr:`~PipelineOpResult.rows` attribute populated with the list of
        rows returned by the query.

        The default value for ``arraysize`` is
        :attr:`oracledb.defaults.arraysize <Defaults.arraysize>`.

        Internally, this operation's :attr:`Cursor.prefetchrows` size is set
        to the value of the explicit or default ``arraysize`` parameter value.

        The ``fetch_lobs`` parameter specifies whether to return LOB locators
        or ``str``/``bytes`` values when fetching LOB columns. The default
        value is :data:`oracledb.defaults.fetch_lobs <Defaults.fetch_lobs>`.

        The ``fetch_decimals`` parameter specifies whether to return
        ``decimal.Decimal`` values when fetching columns of type ``NUMBER``.
        The default value is
        :data:`oracledb.defaults.fetch_decimals <Defaults.fetch_decimals>`.
        """
        if arraysize is None:
            arraysize = defaults.arraysize
        op_impl = PipelineOpImpl(
            op_type=PipelineOpType.FETCH_ALL,
            statement=statement,
            parameters=parameters,
            arraysize=arraysize,
            rowfactory=rowfactory,
            fetch_lobs=fetch_lobs,
            fetch_decimals=fetch_decimals,
        )
        return self._add_op(op_impl)

    def add_fetchmany(
        self,
        statement: str,
        parameters: Optional[Union[list, tuple, dict]] = None,
        num_rows: Optional[int] = None,
        rowfactory: Optional[Callable] = None,
        fetch_lobs: Optional[bool] = None,
        fetch_decimals: Optional[bool] = None,
    ) -> PipelineOp:
        """
        Adds an operation that executes a query and returns up to the specified
        number of rows from the result set.  The created PipelineOp object is
        also returned from this function.

        When the Pipeline is executed, the PipelineOpResult object that is
        returned for this operation will have the
        :attr:`~PipelineOpResult.rows` attribute populated with the list of
        rows returned by the query.

        The default value for ``num_rows`` is the value of
        :attr:`oracledb.defaults.arraysize <Defaults.arraysize>`.

        Internally, this operation's :attr:`Cursor.prefetchrows` size is set to
        the value of the explicit or default ``num_rows`` parameter, allowing
        all rows to be fetched in one round-trip.

        Since only one fetch is performed for a query operation, consider
        adding a ``FETCH NEXT`` clause to the statement to prevent the
        database processing rows that will never be fetched.

        The ``fetch_lobs`` parameter specifies whether to return LOB locators
        or ``str``/``bytes`` values when fetching LOB columns. The default
        value is :data:`oracledb.defaults.fetch_lobs <Defaults.fetch_lobs>`.

        The ``fetch_decimals`` parameter specifies whether to return
        ``decimal.Decimal`` values when fetching columns of type ``NUMBER``.
        The default value is
        :data:`oracledb.defaults.fetch_decimals <Defaults.fetch_decimals>`.
        """
        if num_rows is None:
            num_rows = defaults.arraysize
        op_impl = PipelineOpImpl(
            op_type=PipelineOpType.FETCH_MANY,
            statement=statement,
            parameters=parameters,
            num_rows=num_rows,
            rowfactory=rowfactory,
            fetch_lobs=fetch_lobs,
            fetch_decimals=fetch_decimals,
        )
        return self._add_op(op_impl)

    def add_fetchone(
        self,
        statement: str,
        parameters: Optional[Union[list, tuple, dict]] = None,
        rowfactory: Optional[Callable] = None,
        fetch_lobs: Optional[bool] = None,
        fetch_decimals: Optional[bool] = None,
    ) -> PipelineOp:
        """
        Adds an operation that executes a query and returns the first row of
        the result set if one exists (or *None*, if no rows exist).  The
        created PipelineOp object is also returned from this function.

        When the Pipeline is executed, the PipelineOpResult object that is
        returned for this operation will have the
        :attr:`~PipelineOpResult.rows` attribute populated with this row if the
        query is performed successfully.

        Internally, this operation's :attr:`Cursor.prefetchrows` and
        :attr:`Cursor.arraysize` sizes will be set to *1*.

        Since only one fetch is performed for a query operation, consider
        adding a ``WHERE`` condition or using a ``FETCH NEXT`` clause in the
        statement to prevent the database processing rows that will never be
        fetched.

        The ``fetch_lobs`` parameter specifies whether to return LOB locators
        or ``str``/``bytes`` values when fetching LOB columns. The default
        value is :data:`oracledb.defaults.fetch_lobs <Defaults.fetch_lobs>`.

        The ``fetch_decimals`` parameter specifies whether to return
        ``decimal.Decimal`` values when fetching columns of type ``NUMBER``.
        The default value is
        :data:`oracledb.defaults.fetch_decimals <Defaults.fetch_decimals>`.
        """
        op_impl = PipelineOpImpl(
            op_type=PipelineOpType.FETCH_ONE,
            statement=statement,
            parameters=parameters,
            rowfactory=rowfactory,
            fetch_lobs=fetch_lobs,
            fetch_decimals=fetch_decimals,
        )
        return self._add_op(op_impl)

    @property
    def operations(self) -> list[PipelineOp]:
        """
        This read-only attribute returns the list of operations associated with
        the pipeline.
        """
        return self._operations


def create_pipeline() -> Pipeline:
    """
    Creates a pipeline object which can be used to process a set of operations
    against a database.
    """
    pipeline = Pipeline.__new__(Pipeline)
    pipeline._impl = PipelineImpl()
    pipeline._operations = []
    return pipeline
