# -----------------------------------------------------------------------------
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
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
# cursor.py
#
# Contains the Cursor class used for executing statements on connections and
# fetching results from queries.
# -----------------------------------------------------------------------------

from typing import Any, Union, Callable, Optional

from . import connection as connection_module
from . import errors
from . import utils
from .base import BaseMetaClass
from .base_impl import DbType, DB_TYPE_OBJECT
from .dbobject import DbObjectType
from .fetch_info import FetchInfo
from .var import Var


class BaseCursor(metaclass=BaseMetaClass):
    _impl = None

    def __init__(
        self,
        connection: "connection_module.Connection",
        scrollable: bool = False,
    ) -> None:
        self._connection = connection
        self._impl = connection._impl.create_cursor_impl(scrollable)

    def __del__(self):
        if self._impl is not None:
            self._impl.close(in_del=True)

    def __enter__(self):
        """
        The entry point for the cursor as a context manager. It returns itself.
        """
        self._verify_open()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        """
        The exit point for the cursor as a context manager. It closes the
        cursor.
        """
        self._verify_open()
        self._impl.close(in_del=True)
        self._impl = None

    def __repr__(self):
        cls_name = self.__class__._public_name
        return f"<{cls_name} on {self.connection!r}>"

    def _call(
        self,
        name: str,
        parameters: Union[list, tuple],
        keyword_parameters: dict,
        return_value: Any = None,
    ) -> None:
        """
        Internal method used for generating the PL/SQL block used to call
        stored procedures.
        """
        utils.verify_stored_proc_args(parameters, keyword_parameters)
        self._verify_open()
        statement, bind_values = self._call_get_execute_args(
            name, parameters, keyword_parameters, return_value
        )
        return self.execute(statement, bind_values)

    def _call_get_execute_args(
        self,
        name: str,
        parameters: Union[list, tuple],
        keyword_parameters: dict,
        return_value: str = None,
    ) -> None:
        """
        Internal method used for generating the PL/SQL block used to call
        stored procedures and functions. A tuple containing this statement and
        the bind values is returned.
        """
        bind_names = []
        bind_values = []
        statement_parts = ["begin "]
        if return_value is not None:
            statement_parts.append(":retval := ")
            bind_values.append(return_value)
        statement_parts.append(name + "(")
        if parameters:
            bind_values.extend(parameters)
            bind_names = [":%d" % (i + 1) for i in range(len(parameters))]
        if keyword_parameters:
            for arg_name, arg_value in keyword_parameters.items():
                bind_values.append(arg_value)
                bind_names.append(f"{arg_name} => :{len(bind_names) + 1}")
        statement_parts.append(",".join(bind_names))
        statement_parts.append("); end;")
        statement = "".join(statement_parts)
        return (statement, bind_values)

    def _normalize_statement(self, statement: Optional[str]) -> Optional[str]:
        """
        Normalizes a statement by stripping leading and trailing spaces. If the
        result is an empty string, an error is raised immediately.
        """
        if statement is not None:
            statement = statement.strip()
            if not statement:
                errors._raise_err(errors.ERR_EMPTY_STATEMENT)
        return statement

    def _prepare(
        self, statement: str, tag: str = None, cache_statement: bool = True
    ) -> None:
        """
        Internal method used for preparing a statement for execution.
        """
        self._impl.prepare(statement, tag, cache_statement)

    def _prepare_for_execute(
        self, statement, parameters, keyword_parameters=None
    ):
        """
        Internal method for preparing a statement for execution.
        """
        self._verify_open()
        self._impl._prepare_for_execute(
            self,
            self._normalize_statement(statement),
            parameters,
            keyword_parameters,
        )

    def _verify_fetch(self) -> None:
        """
        Verifies that fetching is possible from this cursor.
        """
        self._verify_open()
        if not self._impl.is_query(self):
            errors._raise_err(errors.ERR_NOT_A_QUERY)

    def _verify_open(self) -> None:
        """
        Verifies that the cursor is open and the associated connection is
        connected. If either condition is false an exception is raised.
        """
        if self._impl is None:
            errors._raise_err(errors.ERR_CURSOR_NOT_OPEN)
        self.connection._verify_connected()

    @property
    def arraysize(self) -> int:
        """
        This read-write attribute can be used to tune the number of rows
        internally fetched and buffered by internal calls to the database when
        fetching rows from SELECT statements and REF CURSORS.

        The value of ``arraysize`` can drastically affect the performance of a
        query since it directly affects the number of network round trips
        between Python and the database.  For methods like :meth:`fetchone()`
        and :meth:`fetchall()` it affects internal behavior but does not change
        how many rows are returned to the application. For :meth:`fetchmany()`
        it is the default number of rows to fetch.

        The attribute is only used for tuning row and SODA document fetches
        from the database.  It does not affect data inserts.

        Due to the performance benefits, the default ``arraysize`` is *100*
        instead of the *1* that the Python DB API recommends.
        """
        self._verify_open()
        return self._impl.arraysize

    @arraysize.setter
    def arraysize(self, value: int) -> None:
        self._verify_open()
        if not isinstance(value, int) or value <= 0:
            errors._raise_err(errors.ERR_INVALID_ARRAYSIZE)
        self._impl.arraysize = value

    def arrayvar(
        self,
        typ: Union[DbType, DbObjectType, type],
        value: Union[list, int],
        size: int = 0,
    ) -> Var:
        """
        Creates an array variable associated with the cursor of the given type
        and size and returns a :ref:`variable object <varobj>`. The value is
        either an integer specifying the number of elements to allocate or it
        is a list and the number of elements allocated is drawn from the size
        of the list. If the value is a list, the variable is also set with the
        contents of the list. If the size is not specified and the type is a
        string or binary, 4000 bytes is allocated. This is needed for passing
        arrays to PL/SQL (in cases where the list might be empty and the type
        cannot be determined automatically) or returning arrays from PL/SQL.
        """
        self._verify_open()
        if isinstance(value, list):
            num_elements = len(value)
        elif isinstance(value, int):
            num_elements = value
        else:
            raise TypeError("expecting integer or list of values")
        var = self._impl.create_var(
            self.connection,
            typ,
            size=size,
            num_elements=num_elements,
            is_array=True,
        )
        if isinstance(value, list):
            var.setvalue(0, value)
        return var

    def bindnames(self) -> list:
        """
        Returns the list of bind variable names bound to the statement. Note
        that a statement must have been prepared first.
        """
        self._verify_open()
        if self._impl.statement is None:
            errors._raise_err(errors.ERR_NO_STATEMENT_PREPARED)
        return self._impl.get_bind_names()

    @property
    def bindvars(self) -> list:
        """
        This read-only attribute provides the bind variables used for the last
        statement that was executed on the cursor. The value will be either a
        list or a dictionary, depending on whether binding was done by position
        or name. Care should be taken when referencing this attribute. In
        particular, elements should not be removed or replaced.
        """
        self._verify_open()
        return self._impl.get_bind_vars()

    def close(self) -> None:
        """
        Closes the cursor now, rather than whenever ``__del__`` is called. The
        cursor will be unusable from this point forward; an Error exception
        will be raised if any operation is attempted with the cursor.
        """
        self._verify_open()
        self._impl.close()
        self._impl = None

    @property
    def description(self) -> Union[list[FetchInfo], None]:
        """
        This read-only attribute contains information about the columns used in
        a query. It is a list of FetchInfo objects, one per column. This
        attribute will be *None* for statements that are not SELECT or WITH
        statements, or if the cursor has not had :meth:`execute()` invoked yet.
        """
        self._verify_open()
        if self._impl.is_query(self):
            return [FetchInfo._from_impl(i) for i in self._impl.fetch_metadata]

    @property
    def fetchvars(self) -> list:
        """
        This read-only attribute specifies the list of variables created for
        the last SELECT query that was executed on the cursor.  Care should be
        taken when referencing this attribute. In particular, elements should
        not be removed or replaced.
        """
        self._verify_open()
        return self._impl.get_fetch_vars()

    def getarraydmlrowcounts(self) -> list:
        """
        Retrieves the DML row counts after a call to :meth:`executemany()` with
        ``arraydmlrowcounts`` enabled. This will return a list of integers
        corresponding to the number of rows affected by the DML statement for
        each element of the array passed to :meth:`executemany()`.

        This method is only available for Oracle Database 12.1 and later.
        """
        self._verify_open()
        return self._impl.get_array_dml_row_counts()

    def getbatcherrors(self) -> list:
        """
        Retrieves the exceptions that took place after a call to
        :meth:`executemany()` with ``batcherrors`` enabled. This will
        return a list of Error objects, one error for each iteration that
        failed. The offset can be determined by looking at the offset attribute
        of the error object.
        """
        self._verify_open()
        return self._impl.get_batch_errors()

    def getimplicitresults(self) -> list:
        """
        Returns a list of cursors which correspond to implicit results made
        available from a PL/SQL block or procedure without the use of OUT ref
        cursor parameters. The PL/SQL block or procedure opens the cursors and
        marks them for return to the client using the procedure
        dbms_sql.return_result. In python-oracledb Thick mode, closing the
        parent cursor will result in the automatic closure of the implicit
        result set cursors. See :ref:`implicitresults`.

        This method is only available for Oracle Database 12.1 (or later). For
        python-oracledb :ref:`Thick <enablingthick>` mode, Oracle Client 12.1
        (or later) is additionally required.
        """
        self._verify_open()
        return self._impl.get_implicit_results(self.connection)

    @property
    def inputtypehandler(self) -> Callable:
        """
        This read-write attribute specifies a method called for each value that
        is bound to a statement executed on the cursor and overrides the
        attribute with the same name on the connection if specified. The method
        signature is handler(cursor, value, arraysize) and the return value is
        expected to be a variable object or *None* in which case a default
        variable object will be created. If this attribute is *None*, the
        default behavior will take place for all values bound to the
        statements.
        """
        self._verify_open()
        return self._impl.inputtypehandler

    @inputtypehandler.setter
    def inputtypehandler(self, value: Callable) -> None:
        self._verify_open()
        self._impl.inputtypehandler = value

    @property
    def lastrowid(self) -> str:
        """
        This read-only attribute returns the rowid of the last row modified by
        the cursor. If no row was modified by the last operation performed on
        the cursor, the value *None* is returned.
        """
        self._verify_open()
        return self._impl.get_lastrowid()

    @property
    def outputtypehandler(self) -> Callable:
        """
        This read-write attribute specifies a method called for each column
        that is to be fetched from this cursor. The method signature is
        handler(cursor, metadata) and the return value is expected to be a
        :ref:`variable object <varobj>` or *None* in which case a default
        variable object will be created. If this attribute is *None*, then the
        default behavior will take place for all columns fetched from this
        cursor.
        """
        self._verify_open()
        return self._impl.outputtypehandler

    @outputtypehandler.setter
    def outputtypehandler(self, value: Callable) -> None:
        self._verify_open()
        self._impl.outputtypehandler = value

    @property
    def prefetchrows(self) -> int:
        """
        This read-write attribute can be used to tune the number of rows that
        python-oracledb initially fetches from Oracle Database when a SELECT
        query is executed. The value can improve performance by reducing the
        number of round-trips to the database. The attribute does not affect
        data insertion.

        In python-oracledb Thin mode, prefetching can reuse the
        :attr:`arraysize` buffer. However in Thick mode, extra memory is
        required.

        Setting this value to *0* can be useful when the timing of fetches must
        be explicitly controlled.

        Queries that return :ref:`LOB <lobobj>` objects and similar types do
        not support prefetching. The ``prefetchrows`` attribute is ignored in
        queries that involve these types.
        """
        self._verify_open()
        return self._impl.prefetchrows

    @prefetchrows.setter
    def prefetchrows(self, value: int) -> None:
        self._verify_open()
        self._impl.prefetchrows = value

    def prepare(
        self, statement: str, tag: str = None, cache_statement: bool = True
    ) -> None:
        """
        This can be used before a call to :meth:`execute()` or
        :meth:`executemany()` to define the statement that will be
        executed. When this is done, the prepare phase will not be performed
        when the call to :meth:`execute()` or :meth:`executemany()` is made
        with *None* or the same string object as the statement.

        If the ``tag`` parameter is specified and the ``cache_statement``
        parameter is *True*, the statement will be returned to the statement
        cache with the given tag.

        If the ``cache_statement`` parameter is *False*, the statement will be
        removed from the statement cache (if it was found there) or will simply
        not be cached.
        """
        self._verify_open()
        self._prepare(statement, tag, cache_statement)

    @property
    def rowcount(self) -> int:
        """
        This read-only attribute specifies the number of rows that have
        currently been fetched from the cursor (for select statements) or that
        have been affected by the operation (for insert, update, delete, and
        merge statements). For all other statements the value is always *0*. If
        the cursor or connection is closed, the value returned is *-1*.
        """
        if self._impl is not None and self.connection._impl is not None:
            return self._impl.rowcount
        return -1

    @property
    def rowfactory(self) -> Callable:
        """
        This read-write attribute specifies a method to call for each row that
        is retrieved from the database. Ordinarily, a tuple is returned for
        each row but if this attribute is set, the method is called with the
        tuple that would normally be returned, and the result of the method is
        returned instead.

        The ``rowfactory`` attribute should be set after each statement
        execution before data is fetched from the cursor.
        """
        self._verify_open()
        return self._impl.rowfactory

    @rowfactory.setter
    def rowfactory(self, value: Callable) -> None:
        self._verify_open()
        self._impl.rowfactory = value

    @property
    def scrollable(self) -> bool:
        """
        This read-write boolean attribute specifies whether the cursor can be
        scrolled or not. By default, cursors are not scrollable, as the server
        resources and response times are greater than nonscrollable cursors.
        This attribute is checked and the corresponding mode set in Oracle when
        calling the method :meth:`execute()`.
        """
        self._verify_open()
        return self._impl.scrollable

    @scrollable.setter
    def scrollable(self, value: bool) -> None:
        self._verify_open()
        self._impl.scrollable = value

    def setinputsizes(self, *args: Any, **kwargs: Any) -> Union[list, dict]:
        """
        This can be used before calls to :meth:`execute()` or
        :meth:`executemany()` to predefine memory areas used for
        :ref:`bind variables <bind>`. Each parameter should be a type object
        corresponding to the data that will be used for a bind variable
        placeholder in the SQL or PL/SQL statement. Alternatively, it can be an
        integer specifying the maximum length of a string bind variable value.

        Use keyword parameters when :ref:`binding by name <bindbyname>`. Use
        positional parameters when :ref:`binding by position <bindbyposition>`.
        The parameter value can be *None* to indicate that python-oracledb
        should determine the required space from the data value provided.

        The parameters or keyword names correspond to the bind variable
        placeholders used in the SQL or PL/SQL statement. Note this means that
        for use with :meth:`executemany()` it does not correspond to the number
        of bind value mappings or sequences being passed.

        When repeated calls to :meth:`execute()` or :meth:`executemany()` are
        made binding different string data lengths, using
        :meth:`setinputsizes()` can help reduce the database's SQL "version
        count" for the statement. See
        :ref:`Reducing the SQL Version Count <sqlversioncount>`.
        """
        if args and kwargs:
            errors._raise_err(errors.ERR_ARGS_AND_KEYWORD_ARGS)
        elif args or kwargs:
            self._verify_open()
            return self._impl.setinputsizes(self.connection, args, kwargs)
        return []

    def setoutputsize(self, size: int, column: int = 0) -> None:
        """
        This method does nothing and is retained solely for compatibility with
        the DB API. Python-oracledb automatically allocates as much space as
        needed to fetch LONG and LONG RAW columns, and also to fetch CLOB as
        string and BLOB as bytes.
        """
        pass

    @property
    def statement(self) -> Union[str, None]:
        """
        This read-only attribute provides the string object that was previously
        prepared with :meth:`prepare()` or executed with :meth:`execute()`.
        """
        if self._impl is not None:
            return self._impl.statement

    def var(
        self,
        typ: Union[DbType, DbObjectType, type],
        size: int = 0,
        arraysize: int = 1,
        inconverter: Callable = None,
        outconverter: Callable = None,
        typename: str = None,
        encoding_errors: str = None,
        bypass_decode: bool = False,
        convert_nulls: bool = False,
        *,
        encodingErrors: str = None,
    ) -> "Var":
        """
        Creates a :ref:`variable object <varobj>` with the specified
        characteristics. This method can be used for binding to PL/SQL IN and
        OUT parameters where the length or type cannot be determined
        automatically from the Python variable being bound. It can also be used
        in :ref:`input <inputtypehandlers>` and :ref:`output
        <outputtypehandlers>` type handlers.

        The ``typ`` parameter specifies the type of data that should be stored
        in the variable. This should be one of the :ref:`database type
        constants <dbtypes>`, :ref:`DB API constants <types>`, an object type
        returned from the method :meth:`Connection.gettype()` or one of the
        following Python types:

        - bool (uses :attr:`oracledb.DB_TYPE_BOOLEAN`)
        - bytes (uses :attr:`oracledb.DB_TYPE_RAW`)
        - datetime.date (uses :attr:`oracledb.DB_TYPE_DATE`)
        - datetime.datetime (uses :attr:`oracledb.DB_TYPE_DATE`)
        - datetime.timedelta (uses :attr:`oracledb.DB_TYPE_INTERVAL_DS`)
        - decimal.Decimal (uses :attr:`oracledb.DB_TYPE_NUMBER`)
        - float (uses :attr:`oracledb.DB_TYPE_NUMBER`)
        - int (uses :attr:`oracledb.DB_TYPE_NUMBER`)
        - str (uses :attr:`oracledb.DB_TYPE_VARCHAR`)

        The ``size`` parameter specifies the length of string and raw variables
        and is ignored in all other cases. If not specified for string and raw
        variables, the value *4000* is used.

        The ``arraysize`` parameter specifies the number of elements the
        variable will have. If not specified the bind array size (usually *1*)
        is used. When a variable is created in an output type handler this
        parameter should be set to the cursor's array size.

        The ``inconverter`` and ``outconverter`` parameters specify methods
        used for converting values to/from the database. More information can
        be found in the section on :ref:`variable objects<varobj>`.

        The ``typename`` parameter specifies the name of a SQL object type and
        must be specified when using type :data:`oracledb.OBJECT` unless the
        type object was passed directly as the first parameter.

        The ``encoding_errors`` parameter specifies what should happen when
        decoding byte strings fetched from the database into strings. It should
        be one of the values noted in the builtin `decode
        <https://docs.python.org/3/library/stdtypes.html#bytes.decode>`__
        function.

        The ``bypass_decode`` parameter, if specified, should be passed as a
        boolean value. Passing a *True* value causes values of database types
        :data:`~oracledb.DB_TYPE_VARCHAR`, :data:`~oracledb.DB_TYPE_CHAR`,
        :data:`~oracledb.DB_TYPE_NVARCHAR`, :data:`~oracledb.DB_TYPE_NCHAR` and
        :data:`~oracledb.DB_TYPE_LONG` to be returned as bytes instead of str,
        meaning that python-oracledb does not do any decoding. See
        :ref:`Fetching raw data <fetching-raw-data>` for more information.

        The ``convert_nulls`` parameter, if specified, should be passed as a
        boolean value. Passing the value *True* causes the ``outconverter`` to
        be called when a null value is fetched from the database; otherwise,
        the ``outconverter`` is only called when non-null values are fetched
        from the database.

        For consistency and compliance with the PEP 8 naming style, the
        parameter ``encodingErrors`` was renamed to ``encoding_errors``. The
        old name will continue to work as a keyword parameter for a period of
        time.
        """
        self._verify_open()
        if typename is not None:
            typ = self.connection.gettype(typename)
        elif typ is DB_TYPE_OBJECT:
            errors._raise_err(errors.ERR_MISSING_TYPE_NAME_FOR_OBJECT_VAR)
        if encodingErrors is not None:
            if encoding_errors is not None:
                errors._raise_err(
                    errors.ERR_DUPLICATED_PARAMETER,
                    deprecated_name="encodingErrors",
                    new_name="encoding_errors",
                )
            encoding_errors = encodingErrors
        return self._impl.create_var(
            self.connection,
            typ,
            size,
            arraysize,
            inconverter,
            outconverter,
            encoding_errors,
            bypass_decode,
            convert_nulls=convert_nulls,
        )

    @property
    def warning(self) -> Union[errors._Error, None]:
        """
        This read-only attribute provides an
        :ref:`oracledb._Error<exchandling>` object giving information about any
        database warnings (such as PL/SQL compilation warnings) that were
        generated during the last call to :meth:`execute()` or
        :meth:`executemany()`. This value is automatically cleared on
        the next call to :meth:`execute()` or :meth:`executemany()`. If no
        warning was generated the value *None* is returned.
        """
        self._verify_open()
        return self._impl.warning


class Cursor(BaseCursor):

    def __iter__(self):
        """
        Returns the cursor itself to be used as an iterator.
        """
        return self

    def __next__(self):
        self._verify_fetch()
        row = self._impl.fetch_next_row(self)
        if row is not None:
            return row
        raise StopIteration

    def _get_oci_attr(self, attr_num: int, attr_type: int) -> Any:
        """
        Returns the value of the specified OCI attribute from the internal
        handle. This is only supported in python-oracledb's thick mode and
        should only be used as directed by Oracle.
        """
        self._verify_open()
        return self._impl._get_oci_attr(attr_num, attr_type)

    def _set_oci_attr(self, attr_num: int, attr_type: int, value: Any) -> None:
        """
        Sets the value of the specified OCI attribute on the internal handle.
        This is only supported in python-oracledb's thick mode and should only
        be used as directed by Oracle.
        """
        self._verify_open()
        self._impl._set_oci_attr(attr_num, attr_type, value)

    def callfunc(
        self,
        name: str,
        return_type: Any,
        parameters: Optional[Union[list, tuple]] = None,
        keyword_parameters: Optional[dict] = None,
        *,
        keywordParameters: Optional[dict] = None,
    ) -> Any:
        """
        Calls a PL/SQL function with the given name and returns its value.

        The ``return_type`` parameter is expected to be a Python type, one of
        the :ref:`oracledb types <types>` or an
        :ref:`Object Type <dbobjecttype>`.

        The sequence of parameters must contain one entry for each parameter
        that the PL/SQL function expects. Any keyword parameters will be
        included after the positional parameters.

        Use :meth:`var()` to define any OUT or IN OUT parameters, if necessary.

        For consistency and compliance with the PEP 8 naming style, the
        parameter ``keywordParameters`` was renamed to ``keyword_parameters``.
        The old name will continue to work for a period of time.
        """
        var = self.var(return_type)
        if keywordParameters is not None:
            if keyword_parameters is not None:
                errors._raise_err(
                    errors.ERR_DUPLICATED_PARAMETER,
                    deprecated_name="keywordParameters",
                    new_name="keyword_parameters",
                )
            keyword_parameters = keywordParameters
        self._call(name, parameters, keyword_parameters, var)
        return var.getvalue()

    def callproc(
        self,
        name: str,
        parameters: Optional[Union[list, tuple]] = None,
        keyword_parameters: Optional[dict] = None,
        *,
        keywordParameters: Optional[dict] = None,
    ) -> list:
        """
        Calls a PL/SQL procedure with the given name.

        The sequence of parameters must contain one entry for each parameter
        that the procedure expects. The result of the call is a modified copy
        of the input sequence. Input parameters are left untouched; output and
        input/output parameters are replaced with possibly new values. Keyword
        parameters will be included after the positional parameters and are not
        returned as part of the output sequence.

        Use :meth:`var()` to define any OUT or IN OUT parameters if necessary.

        No query result set is returned by this method. Instead, use
        :ref:`REF CURSOR <refcur>` parameters or
        :ref:`Implicit Results <implicitresults>`.

        For consistency and compliance with the PEP 8 naming style, the
        parameter ``keywordParameters`` was renamed to ``keyword_parameters``.
        The old name will continue to work for a period of time.
        """
        if keywordParameters is not None:
            if keyword_parameters is not None:
                errors._raise_err(
                    errors.ERR_DUPLICATED_PARAMETER,
                    deprecated_name="keywordParameters",
                    new_name="keyword_parameters",
                )
            keyword_parameters = keywordParameters
        self._call(name, parameters, keyword_parameters)
        if parameters is None:
            return []
        return [
            v.get_value(0) for v in self._impl.bind_vars[: len(parameters)]
        ]

    @property
    def connection(self) -> "connection_module.Connection":
        """
        This read-only attribute returns a reference to the connection object
        on which the cursor was created.
        """
        return self._connection

    def execute(
        self,
        statement: Optional[str],
        parameters: Optional[Union[list, tuple, dict]] = None,
        *,
        suspend_on_success: bool = False,
        fetch_lobs: Optional[bool] = None,
        fetch_decimals: Optional[bool] = None,
        **keyword_parameters: Any,
    ) -> Any:
        """
        Executes a statement against the database. See :ref:`sqlexecution`.

        Parameters may be passed as a dictionary or sequence or as keyword
        parameters. If the parameters are a dictionary, the values will be
        bound by name and if the parameters are a sequence the values will be
        bound by position. Note that if the values are bound by position, the
        order of the variables is from left to right as they are encountered in
        the statement and SQL statements are processed differently than PL/SQL
        statements. For this reason, it is generally recommended to bind
        parameters by name instead of by position.

        Parameters passed as a dictionary are name and value pairs. The name
        maps to the bind variable name used by the statement and the value maps
        to the Python value you wish bound to that bind variable.

        A reference to the statement will be retained by the cursor. If *None*
        or the same string object is passed in again, the cursor will execute
        that statement again without performing a prepare or rebinding and
        redefining.  This is most effective for algorithms where the same
        statement is used, but different parameters are bound to it (many
        times). Note that parameters that are not passed in during subsequent
        executions will retain the value passed in during the last execution
        that contained them.

        The ``suspend_on_success`` parameter is specific to :ref:`sessionless
        transactions <sessionlesstxns>`. When set to *True*, the active
        sessionless transaction will be suspended when ``execute()`` completes
        successfully.  See :ref:`suspendtxns`.

        The ``fetch_lobs`` parameter specifies whether to return LOB locators
        or ``str``/``bytes`` values when fetching LOB columns. The default
        value is :data:`oracledb.defaults.fetch_lobs <Defaults.fetch_lobs>`.

        The ``fetch_decimals`` parameter specifies whether to return
        ``decimal.Decimal`` values when fetching columns of type ``NUMBER``.
        The default value is :data:`oracledb.defaults.fetch_decimals
        <Defaults.fetch_decimals>`.

        For maximum efficiency when reusing a statement, it is best to use the
        :meth:`Cursor.setinputsizes()` method to specify the parameter types
        and sizes ahead of time; in particular, *None* is assumed to be a
        string of length 1 so any values that are later bound as numbers or
        dates will raise a TypeError exception.

        If the statement is a SELECT query, the cursor is returned as a
        convenience to the caller (so it can be used directly as an iterator
        over the rows in the cursor); otherwise, *None* is returned.
        """
        self._prepare_for_execute(statement, parameters, keyword_parameters)
        impl = self._impl
        if fetch_lobs is not None:
            impl.fetch_lobs = fetch_lobs
        if fetch_decimals is not None:
            impl.fetch_decimals = fetch_decimals
        impl.suspend_on_success = suspend_on_success
        impl.execute(self)
        if impl.fetch_vars is not None:
            return self

    def executemany(
        self,
        statement: Optional[str],
        parameters: Any,
        *,
        batcherrors: bool = False,
        arraydmlrowcounts: bool = False,
        suspend_on_success: bool = False,
        batch_size: int = 2**32 - 1,
    ) -> None:
        """
        Executes a SQL statement once using all bind value mappings or
        sequences found in the sequence parameters. This can be used to insert,
        update, or delete multiple rows in a table with a single
        python-oracledb call. It can also invoke a PL/SQL procedure multiple
        times. See :ref:`batchstmnt`.

        The ``statement`` parameter is managed in the same way as the
        :meth:`execute()` method manages it.

        The ``parameters`` parameter can be a list of tuples, where each tuple
        item maps to one bind variable placeholder in ``statement``. It can
        also be a list of dictionaries, where the keys match the bind variable
        placeholder names in ``statement``. If there are no bind values, or
        values have previously been bound, the ``parameters`` value can be an
        integer specifying the number of iterations. The ``parameters``
        parameter can also be a :ref:`DataFrame <oracledataframeobj>`, or a
        third-party data frame that supports the `Apache Arrow PyCapsule
        <https://arrow.apache.org/docs/
        format/CDataInterface/PyCapsuleInterface.html>`__ Interface.

        In python-oracledb Thick mode, if the size of the buffers allocated for
        any of the parameters exceeds 2 GB, you will receive the error
        ``DPI-1015: array size of <n> is too large``. If you receive this
        error, decrease the number of rows being inserted.

        When *True*, the ``batcherrors`` parameter enables batch error support
        within Oracle Database and ensures that the call succeeds even if an
        exception takes place in one or more of the sequence of bind values.
        The errors can then be retrieved using :meth:`getbatcherrors()`.

        When *True*, the ``arraydmlrowcounts`` parameter enables DML row counts
        to be retrieved from Oracle after the method has completed. The row
        counts can then be retrieved using
        :meth:`getarraydmlrowcounts()`.

        Both the ``batcherrors`` parameter and the ``arraydmlrowcounts``
        parameter can only be *True* when executing an insert, update, delete,
        or merge statement; in all other cases an error will be raised.

        The ``suspend_on_success`` parameter is specific to :ref:`sessionless
        transactions <sessionlesstxns>`. When set to *True*, the active
        sessionless transaction will be suspended when ``executemany()``
        completes successfully. See :ref:`suspendtxns`.

        The ``batch_size`` parameter is used to split large data sets into
        smaller pieces for sending to the database. It is the number of records
        in each batch. This parameter can be used to tune performance. When
        ``Connection.autocommit`` is *True*, a commit will take place for each
        batch.

        For maximum efficiency, it is best to use the :meth:`setinputsizes()`
        method to specify the bind value types and sizes. In particular, if the
        type is not explicitly specified, the value *None* is assumed to be a
        string of length 1 so any values that are later bound as numbers or
        dates will raise a TypeError exception.
        """
        self._verify_open()
        manager = self._impl._prepare_for_executemany(
            self,
            self._normalize_statement(statement),
            parameters,
            batch_size,
        )
        self._impl.suspend_on_success = suspend_on_success
        while manager.num_rows > 0:
            self._impl.executemany(
                self,
                manager.num_rows,
                batcherrors,
                arraydmlrowcounts,
                manager.message_offset,
            )
            manager.next_batch()

    def fetchall(self) -> list:
        """
        Fetches all (remaining) rows of a SELECT query result, returning them
        as a list of tuples. An empty list is returned if no more rows are
        available. An exception is raised if the previous call to
        :meth:`execute()` did not produce any result set or no call was issued
        yet.

        Note that the cursor's :attr:`~Cursor.arraysize` attribute can affect
        the performance of this operation, as internally data is fetched in
        batches of that size from the database. See :ref:`Tuning Fetch
        Performance <tuningfetch>`.

        An exception is raised if the previous call to :meth:`execute()` did
        not produce any result set or no call was issued yet.
        """
        self._verify_fetch()
        result = []
        fetch_next_row = self._impl.fetch_next_row
        while True:
            row = fetch_next_row(self)
            if row is None:
                break
            result.append(row)
        return result

    def fetchmany(
        self, size: Optional[int] = None, numRows: Optional[int] = None
    ) -> list:
        """
        Fetches the next set of rows of a SELECT query result, returning a list
        of tuples.  An empty list is returned if no more rows are available.
        Note that the cursor's :attr:`arraysize` attribute can affect the
        performance of this operation.

        The number of rows to fetch is specified by the ``size`` parameter. If
        it is not given, the cursor's :attr:`arraysize` attribute determines
        the number of rows to be fetched. If the number of rows available to be
        fetched is fewer than the amount requested, fewer rows will be
        returned.

        An exception is raised if the previous call to :meth:`execute()` did
        not produce any result set or no call was issued yet.
        """
        self._verify_fetch()
        if size is None:
            if numRows is not None:
                size = numRows
            else:
                size = self._impl.arraysize
        elif numRows is not None:
            errors._raise_err(
                errors.ERR_DUPLICATED_PARAMETER,
                deprecated_name="numRows",
                new_name="size",
            )
        result = []
        fetch_next_row = self._impl.fetch_next_row
        while len(result) < size:
            row = fetch_next_row(self)
            if row is None:
                break
            result.append(row)
        return result

    def fetchone(self) -> Any:
        """
        Fetches the next row of a SELECT query result set, returning a single
        tuple or *None* when no more data is available.  An exception is raised
        if the previous call to :meth:`execute()` did not produce any result
        set or no call was issued yet.

        When ``fetchone()`` is used to iterate over a result set, the cursor’s
        :attr:`arraysize` attribute can affect performance, as internally data
        is fetched in batches of that size from Oracle Database.
        """
        self._verify_fetch()
        return self._impl.fetch_next_row(self)

    def parse(self, statement: str) -> None:
        """
        This can be used to parse a statement without actually executing it
        (parsing step is done automatically by Oracle when a statement is
        :meth:`executed <execute>`).
        """
        self._verify_open()
        self._prepare(statement)
        self._impl.parse(self)

    def scroll(self, value: int = 0, mode: str = "relative") -> None:
        """
        Scrolls the cursor in the result set to a new position according to the
        mode.

        If mode is *relative* (the default value), the value is taken as an
        offset to the current position in the result set. If set to *absolute*,
        value states an absolute target position. If set to *first*, the cursor
        is positioned at the first row and if set to *last*, the cursor is set
        to the last row in the result set.

        An error is raised if the mode is *relative* or *absolute* and the
        scroll operation would position the cursor outside of the result set.
        """
        self._verify_open()
        if not self._impl.scrollable:
            errors._raise_err(errors.ERR_SCROLL_NOT_SUPPORTED)
        self._impl.scroll(self, value, mode)


class AsyncCursor(BaseCursor):

    async def __aenter__(self):
        """
        The entry point for the cursor as a context manager. It returns itself.
        """
        self._verify_open()
        return self

    async def __aexit__(self, *exc_info):
        """
        The exit point for the cursor as a context manager. It closes the
        cursor.
        """
        self._verify_open()
        self._impl.close(in_del=True)
        self._impl = None

    def __aiter__(self):
        """
        Returns the cursor itself to be used as an asynchronous iterator.
        """
        return self

    async def __anext__(self):
        self._verify_fetch()
        row = await self._impl.fetch_next_row(self)
        if row is not None:
            return row
        raise StopAsyncIteration

    async def callfunc(
        self,
        name: str,
        return_type: Any,
        parameters: Optional[Union[list, tuple]] = None,
        keyword_parameters: Optional[dict] = None,
    ) -> Any:
        """
        Calls a PL/SQL function with the given name and returns its value.

        The ``return_type`` parameter is expected to be a Python type, one of
        the :ref:`oracledb types <types>` or an :ref:`Object Type
        <dbobjecttype>`.

        The sequence of parameters must contain one entry for each parameter
        that the PL/SQL function expects. Any keyword parameters will be
        included after the positional parameters.

        Use :meth:`var()` to define any OUT or IN OUT parameters, if necessary.
        """
        var = self.var(return_type)
        await self._call(name, parameters, keyword_parameters, var)
        return var.getvalue()

    async def callproc(
        self,
        name: str,
        parameters: Optional[Union[list, tuple]] = None,
        keyword_parameters: Optional[dict] = None,
    ) -> list:
        """
        Calls a PL/SQL procedure with the given name.

        The sequence of parameters must contain one entry for each parameter
        that the procedure expects. The result of the call is a modified copy
        of the input sequence. Input parameters are left untouched; output and
        input/output parameters are replaced with possibly new values. Keyword
        parameters will be included after the positional parameters and are not
        returned as part of the output sequence.

        Use :meth:`var()` to define any OUT or IN OUT parameters if necessary.

        No query result set is returned by :meth:`callproc()`.  Instead, use
        :ref:`REF CURSOR <refcur>` parameters or :ref:`Implicit Results
        <implicitresults>`.
        """
        await self._call(name, parameters, keyword_parameters)
        if parameters is None:
            return []
        return [
            v.get_value(0) for v in self._impl.bind_vars[: len(parameters)]
        ]

    @property
    def connection(self) -> "connection_module.AsyncConnection":
        """
        This read-only attribute returns a reference to the connection object
        on which the cursor was created.
        """
        return self._connection

    async def execute(
        self,
        statement: Optional[str],
        parameters: Optional[Union[list, tuple, dict]] = None,
        *,
        suspend_on_success: bool = False,
        fetch_lobs: Optional[bool] = None,
        fetch_decimals: Optional[bool] = None,
        **keyword_parameters: Any,
    ) -> None:
        """
        Executes a statement against the database. See :ref:`sqlexecution`.

        Parameters may be passed as a dictionary or sequence or as keyword
        parameters. If the parameters are a dictionary, the values will be
        bound by name and if the parameters are a sequence the values will be
        bound by position. Note that if the values are bound by position, the
        order of the variables is from left to right as they are encountered in
        the statement and SQL statements are processed differently than PL/SQL
        statements. For this reason, it is generally recommended to bind
        parameters by name instead of by position.

        Parameters passed as a dictionary are name and value pairs. The name
        maps to the bind variable name used by the statement and the value maps
        to the Python value you wish bound to that bind variable.

        A reference to the statement will be retained by the cursor. If *None*
        or the same string object is passed in again, the cursor will execute
        that statement again without performing a prepare or rebinding and
        redefining.  This is most effective for algorithms where the same
        statement is used, but different parameters are bound to it (many
        times). Note that parameters that are not passed in during subsequent
        executions will retain the value passed in during the last execution
        that contained them.

        The ``suspend_on_success`` parameter is specific to :ref:`sessionless
        transactions <sessionlesstxns>`. When set to *True*, the active
        sessionless transaction will be suspended when ``execute()`` completes
        successfully.  See :ref:`suspendtxns`.

        The ``fetch_lobs`` parameter specifies whether to return LOB locators
        or ``str``/``bytes`` values when fetching LOB columns. The default
        value is :data:`oracledb.defaults.fetch_lobs <Defaults.fetch_lobs>`.

        The ``fetch_decimals`` parameter specifies whether to return
        ``decimal.Decimal`` values when fetching columns of type ``NUMBER``.
        The default value is :data:`oracledb.defaults.fetch_decimals
        <Defaults.fetch_decimals>`.

        For maximum efficiency when reusing a statement, it is best to use the
        :meth:`setinputsizes()` method to specify the parameter types and sizes
        ahead of time; in particular, *None* is assumed to be a string of
        length 1 so any values that are later bound as numbers or dates will
        raise a TypeError exception.

        If the statement is a SELECT query, the cursor is returned as a
        convenience to the caller (so it can be used directly as an iterator
        over the rows in the cursor); otherwise, *None* is returned.
        """
        self._prepare_for_execute(statement, parameters, keyword_parameters)
        impl = self._impl
        impl.suspend_on_success = suspend_on_success
        if fetch_lobs is not None:
            impl.fetch_lobs = fetch_lobs
        if fetch_decimals is not None:
            impl.fetch_decimals = fetch_decimals
        await self._impl.execute(self)

    async def executemany(
        self,
        statement: Optional[str],
        parameters: Any,
        *,
        batcherrors: bool = False,
        arraydmlrowcounts: bool = False,
        suspend_on_success: bool = False,
        batch_size: int = 2**32 - 1,
    ) -> None:
        """
        Executes a SQL statement once using all bind value mappings or
        sequences found in the sequence parameters. This can be used to insert,
        update, or delete multiple rows in a table with a single
        python-oracledb call. It can also invoke a PL/SQL procedure multiple
        times. See :ref:`batchstmnt`.

        The ``statement`` parameter is managed in the same way as the
        :meth:`execute()` method manages it.

        The ``parameters`` parameter can be a list of tuples, where each tuple
        item maps to one bind variable placeholder in ``statement``. It can
        also be a list of dictionaries, where the keys match the bind variable
        placeholder names in ``statement``. If there are no bind values, or
        values have previously been bound, the ``parameters`` value can be an
        integer specifying the number of iterations. The ``parameters``
        parameter can also be a :ref:`DataFrame <oracledataframeobj>`, or a
        third-party data frame that supports the `Apache Arrow PyCapsule
        <https://arrow.apache.org/docs/
        format/CDataInterface/PyCapsuleInterface.html>`__ Interface.

        In python-oracledb Thick mode, if the size of the buffers allocated for
        any of the parameters exceeds 2 GB, you will receive the error
        ``DPI-1015: array size of <n> is too large``. If you receive this
        error, decrease the number of rows being inserted.

        When True, the ``batcherrors`` parameter enables batch error support
        within Oracle and ensures that the call succeeds even if an exception
        takes place in one or more of the sequence of parameters. The errors
        can then be retrieved using :meth:`getbatcherrors()`.

        When True, the ``arraydmlrowcounts`` parameter enables DML row counts
        to be retrieved from Oracle after the method has completed. The row
        counts can then be retrieved using :meth:`getarraydmlrowcounts()`.

        Both the ``batcherrors`` parameter and the ``arraydmlrowcounts``
        parameter can only be True when executing an insert, update, delete, or
        merge statement. In all other cases, an error will be raised.

        The ``suspend_on_success`` parameter is specific to :ref:`sessionless
        transactions <sessionlesstxns>`. When set to *True*, the active
        sessionless transaction will be suspended when ``executemany()``
        completes successfully. See :ref:`suspendtxns`.

        The ``batch_size`` parameter is used to split large data sets into
        smaller pieces for sending to the database. It is the number of records
        in each batch. This parameter can be used to tune performance. When
        ``Connection.autocommit`` is *True*, a commit will take place for each
        batch. Do not set ``batch_size`` when ``suspend_on_success`` is *True*.

        For maximum efficiency, it is best to use the :meth:`setinputsizes()`
        method to specify the parameter types and sizes ahead of time. In
        particular, the value *None* is assumed to be a string of length 1 so
        any values that are later bound as numbers or dates will raise a
        TypeError exception.
        """
        self._verify_open()
        manager = self._impl._prepare_for_executemany(
            self, self._normalize_statement(statement), parameters, batch_size
        )
        self._impl.suspend_on_success = suspend_on_success
        while manager.num_rows > 0:
            await self._impl.executemany(
                self,
                manager.num_rows,
                batcherrors,
                arraydmlrowcounts,
                manager.message_offset,
            )
            manager.next_batch()

    async def fetchall(self) -> list:
        """
        Fetches all (remaining) rows of a SELECT query result, returning them
        as a list of tuples. An empty list is returned if no more rows are
        available. An exception is raised if the previous call to
        :meth:`execute()` did not produce any result set or no call was issued
        yet.

        Note that the cursor's :attr:`~AsyncCursor.arraysize` attribute can
        affect the performance of this operation, as internally data is fetched
        in batches of that size from the database.
        """
        self._verify_fetch()
        result = []
        fetch_next_row = self._impl.fetch_next_row
        while True:
            row = await fetch_next_row(self)
            if row is None:
                break
            result.append(row)
        return result

    async def fetchmany(self, size: Optional[int] = None) -> list:
        """
        Fetches the next set of rows of a SELECT query result, returning a list
        of tuples.  An empty list is returned if no more rows are available.
        Note that the cursor's :attr:`arraysize` attribute can affect the
        performance of this operation.

        The number of rows to fetch is specified by the parameter. If it is not
        given, the cursor's :attr:`arraysize` attribute determines the number
        of rows to be fetched. If the number of rows available to be fetched is
        fewer than the amount requested, fewer rows will be returned.

        An exception is raised if the previous call to :meth:`execute()` did
        not produce any result set or no call was issued yet.
        """
        self._verify_fetch()
        if size is None:
            size = self._impl.arraysize
        result = []
        fetch_next_row = self._impl.fetch_next_row
        while len(result) < size:
            row = await fetch_next_row(self)
            if row is None:
                break
            result.append(row)
        return result

    async def fetchone(self) -> Any:
        """
        Fetches the next row of a SELECT query result set, returning a single
        tuple or *None* when no more data is available.  An exception is raised
        if the previous call to :meth:`execute()` did not produce any result
        set or no call was issued yet.

        When ``fetchone()`` is used to iterate over a result set, the cursor’s
        :attr:`arraysize` attribute can affect performance, as internally data
        is fetched in batches of that size from Oracle Database.
        """
        self._verify_fetch()
        return await self._impl.fetch_next_row(self)

    async def parse(self, statement: str) -> None:
        """
        This can be used to parse a statement without actually executing it
        (parsing step is done automatically by Oracle when a statement is
        :meth:`executed <execute>`).
        """
        self._verify_open()
        self._prepare(statement)
        await self._impl.parse(self)

    async def scroll(self, value: int = 0, mode: str = "relative") -> None:
        """
        Scrolls the cursor in the result set to a new position according to the
        mode.

        If mode is *relative* (the default value), the value is taken as an
        offset to the current position in the result set. If set to *absolute*,
        value states an absolute target position. If set to *first*, the cursor
        is positioned at the first row and if set to *last*, the cursor is set
        to the last row in the result set.

        An error is raised if the mode is *relative* or *absolute* and the
        scroll operation would position the cursor outside of the result set.
        """
        self._verify_open()
        if not self._impl.scrollable:
            errors._raise_err(errors.ERR_SCROLL_NOT_SUPPORTED)
        await self._impl.scroll(self, value, mode)
