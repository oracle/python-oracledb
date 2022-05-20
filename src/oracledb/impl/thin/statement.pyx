#------------------------------------------------------------------------------
# Copyright (c) 2020, 2022, Oracle and/or its affiliates.
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
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# statement.pyx
#
# Cython file defining the Statement and BindInfo classes used to hold
# information about statements that are executed and any bind parameters that
# may be bound to those statements (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

# Rules for named binds:
# 1. Quoted and non-quoted bind names are allowed.
# 2. Quoted binds can contain any characters.
# 3. Non-quoted binds must begin with an alphabet character.
# 4. Non-quoted binds can only contain alphanumeric characters, the underscore,
#    the dollar sign and the pound sign.
# 5. Non-quoted binds cannot be Oracle Database Reserved Names (Server handles
#    this case and returns an appropriate error)
BIND_PATTERN = r'(?<!"\:)(?<=\:)\s*("[^\"]*"|[^\W\d_][\w\$#]*|\d+)'

# pattern used for detecting a DML returning clause; bind variables in the
# first group are input variables; bind variables in the second group are
# output only variables
DML_RETURNING_PATTERN = r'(?si)( RETURNING [\s\S]+ INTO )(.*?$)'

cdef class BindInfo:

    cdef:
        uint32_t num_elements
        bint _is_return_bind
        uint8_t ora_type_num
        uint32_t buffer_size
        int16_t precision
        uint8_t bind_dir
        uint32_t size
        str _bind_name
        bint is_array
        int16_t scale
        uint8_t csfrm
        ThinVarImpl _bind_var_impl

    def __cinit__(self, str name, bint is_return_bind):
        self._bind_name = name
        self._is_return_bind = is_return_bind

    cdef BindInfo copy(self):
        return BindInfo(self._bind_name, self._is_return_bind)


cdef class Statement:

    cdef:
        str _sql
        bytes _sql_bytes
        uint32_t _sql_length
        uint16_t _cursor_id
        bint _is_query
        bint _is_plsql
        bint _is_dml
        bint _is_ddl
        bint _is_returning
        list _bind_info_list
        list _fetch_vars
        list _fetch_var_impls
        object _bind_info_dict
        object _last_output_type_handler
        uint32_t _num_columns
        bint _requires_full_execute
        bint _requires_define
        bint _return_to_cache
        bint _in_use
        bint _plsql_multiple_execs

    cdef Statement copy(self):
        cdef:
            Statement copied_statement = Statement()
            object bind_info_dict
            BindInfo bind_info
        copied_statement._sql = self._sql
        copied_statement._sql_bytes = self._sql_bytes
        copied_statement._sql_length = self._sql_length
        copied_statement._is_query = self._is_query
        copied_statement._is_plsql = self._is_plsql
        copied_statement._is_dml = self._is_dml
        copied_statement._is_ddl = self._is_ddl
        copied_statement._is_returning = self._is_returning
        copied_statement._bind_info_list = \
                [bind_info.copy() for bind_info in self._bind_info_list]
        copied_statement._bind_info_dict = collections.OrderedDict()
        bind_info_dict = copied_statement._bind_info_dict
        for bind_info in copied_statement._bind_info_list:
            if bind_info._bind_name in bind_info_dict:
                bind_info_dict[bind_info._bind_name].append(bind_info)
            else:
                bind_info_dict[bind_info._bind_name] = [bind_info]
        copied_statement._return_to_cache = False
        return copied_statement

    cdef int _add_binds(self, str sql, bint is_return_bind) except -1:
        """
        Add bind information to the statement by examining the passed SQL for
        bind variable names.
        """
        cdef:
            BindInfo info
            str name
        for name in re.findall(BIND_PATTERN, sql):
            if name.startswith('"') and name.endswith('"'):
                name = name[1:-1]
            else:
                name = name.upper()
            if self._is_plsql and name in self._bind_info_dict:
                continue
            info = BindInfo(name, is_return_bind)
            self._bind_info_list.append(info)
            if info._bind_name in self._bind_info_dict:
                self._bind_info_dict[info._bind_name].append(info)
            else:
                self._bind_info_dict[info._bind_name] = [info]

    cdef _determine_statement_type(self, str sql):
        """
        Determine the type of the SQL statement by examining the first keyword
        found in the statement.
        """
        tokens = sql.strip().lstrip("(")[:10].split()
        if tokens:
            sql_keyword = tokens[0].upper()
            if sql_keyword in ("DECLARE", "BEGIN", "CALL"):
                self._is_plsql = True
            elif sql_keyword in ("SELECT", "WITH"):
                self._is_query = True
            elif sql_keyword in ("INSERT", "UPDATE", "DELETE", "MERGE"):
                self._is_dml = True
            elif sql_keyword in ("CREATE", "ALTER", "DROP", "TRUNCATE"):
                self._is_ddl = True

    cdef int _prepare(self, str sql, bint char_conversion) except -1:
        """
        Prepare the SQL for execution by determining the list of bind names
        that are found within it. The length of the SQL text is also calculated
        at this time. If the character sets of the client and server are
        identical, the length is calculated in bytes; otherwise, the length is
        calculated in characters.
        """
        cdef:
            str input_sql, returning_sql = None
            object match

        # retain normalized SQL (as string and bytes) as well as the length
        self._sql = sql
        self._sql_bytes = self._sql.encode()
        if char_conversion:
            self._sql_length = <uint32_t> len(self._sql)
        else:
            self._sql_length = <uint32_t> len(self._sql_bytes)

        # create empty list (bind by position) and dict (bind by name)
        self._bind_info_dict = collections.OrderedDict()
        self._bind_info_list = []

        # Strip single/multiline comments and strings from the sql statement to
        # ease searching for bind variables.
        sql = re.sub(r"/\*[\S\n ]+\*/", "", sql)
        sql = re.sub(r"\--.*(\n|$)", "", sql)
        sql = re.sub(r"""'[^']*'(?=(?:[^']*[^']*')*[^']*$)*""", "", sql,
                     flags=re.MULTILINE)
        sql = re.sub(r'(:\s*)?("([^"]*)")',
                    lambda m: m.group(0) if sql[m.start(0)] == ":" else "",
                    sql)

        # determine statement type
        self._determine_statement_type(sql)

        # bind variables can only be found in queries, DML and PL/SQL
        if self._is_query or self._is_dml or self._is_plsql:
            input_sql = sql
            if not self._is_plsql:
                match = re.search(DML_RETURNING_PATTERN, sql)
                if match is not None:
                    pos = match.start(2)
                    input_sql = sql[:pos]
                    returning_sql = sql[pos:]
            self._add_binds(input_sql, is_return_bind=False)
            if returning_sql is not None:
                self._is_returning = True
                self._add_binds(returning_sql, is_return_bind=True)

    cdef int _set_var(self, BindInfo bind_info, ThinVarImpl var_impl,
                      ThinCursorImpl cursor_impl) except -1:
        """
        Set the variable on the bind information and copy across metadata that
        will be used for binding. If the bind metadata has changed, mark the
        statement as requiring a full execute. In addition, binding a REF
        cursor also requires a full execute.
        """
        cdef object value
        if var_impl.dbtype._ora_type_num == TNS_DATA_TYPE_CURSOR:
            for value in var_impl._values:
                if value is not None and value._impl is cursor_impl:
                    errors._raise_err(errors.ERR_SELF_BIND_NOT_SUPPORTED)
            self._requires_full_execute = True
        if var_impl.dbtype._ora_type_num != bind_info.ora_type_num \
                or var_impl.size != bind_info.size \
                or var_impl.buffer_size != bind_info.buffer_size \
                or var_impl.precision != bind_info.precision \
                or var_impl.scale != bind_info.scale \
                or var_impl.is_array != bind_info.is_array \
                or var_impl.num_elements != bind_info.num_elements \
                or var_impl.dbtype._csfrm != bind_info.csfrm:
            bind_info.ora_type_num = var_impl.dbtype._ora_type_num
            bind_info.csfrm = var_impl.dbtype._csfrm
            bind_info.is_array = var_impl.is_array
            bind_info.num_elements = var_impl.num_elements
            bind_info.size = var_impl.size
            bind_info.buffer_size = var_impl.buffer_size
            bind_info.precision = var_impl.precision
            bind_info.scale = var_impl.scale
            self._requires_full_execute = True
        bind_info._bind_var_impl = var_impl
