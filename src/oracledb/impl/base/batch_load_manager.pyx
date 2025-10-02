#------------------------------------------------------------------------------
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
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# batch_load_manager.pyx
#
# Cython file defining the BatchLoadManager implementation class (embedded in
# base_impl.pyx).
#------------------------------------------------------------------------------

cdef class BatchLoadManager:

    cdef int _calculate_num_rows_in_batch(self, uint64_t total_rows) except -1:
        """
        Calculates the total number of rows to put in the next batch.
        """
        cdef uint64_t rows_remaining = total_rows - self.offset
        self.num_rows = <uint32_t> min(rows_remaining, self.batch_size)

    cdef int _next_batch(self) except -1:
        """
        Goes to the next batch in the set of data, if applicable.
        """
        raise NotImplementedError()

    cdef int _setup_cursor(self) except -1:
        """
        Called after the manager has been populated and helps set up the cursor
        if one is being used.
        """
        pass

    @staticmethod
    cdef BatchLoadManager create_for_executemany(
        object cursor,
        BaseCursorImpl cursor_impl,
        object parameters,
        uint32_t batch_size,
    ):
        """
        Creates a batch load manager object for calling cursor.executemany()
        with the given parameters. This allows splitting large source arrays
        into multiple chunks and also supports data frames with multiple
        chunks.
        """
        cdef:
            BatchLoadManager manager
            DataFrameImpl df_impl

        # batch size must be a positive integer
        if batch_size == 0:
            raise TypeError("batch_size must be a positive integer")

        # create and populate manager object
        # if parameters are an instance, the value refers to the number of
        # times to execute the statement
        if isinstance(parameters, int):
            manager = PrePopulatedBatchLoadManager.create(parameters)

        # if parameters are a list, the value refers to the actual data that is
        # to be loaded
        elif isinstance(parameters, list):
            manager = FullDataBatchLoadManager.create(parameters)

        # if parameters are an Oracle dataframe we can use it directly
        elif isinstance(parameters, PY_TYPE_DATAFRAME):
            manager = DataFrameBatchLoadManager.create(parameters._impl)

        # if parameters implement the Arrow PyCapsule stream interface, convert
        # it to an Oracle dataframe for further processing
        elif hasattr(parameters, "__arrow_c_stream__"):
            df_impl = DataFrameImpl.from_arrow_stream(parameters)
            manager = DataFrameBatchLoadManager.create(df_impl)

        # the parameters are of an unknown type
        else:
            errors._raise_err(errors.ERR_WRONG_EXECUTEMANY_PARAMETERS_TYPE)

        # setup cursor
        manager.cursor_impl = cursor_impl
        manager.cursor = cursor
        manager.conn = cursor.connection
        manager.batch_size = batch_size
        manager._setup_cursor()

        # setup for first batch
        manager._next_batch()

        return manager

    def next_batch(self):
        """
        Goes to the next batch in the set of data, if applicable.
        """
        self.offset += self.num_rows
        self._next_batch()


@cython.final
cdef class DataFrameBatchLoadManager(BatchLoadManager):
    cdef:
        DataFrameImpl df_impl
        ssize_t num_chunks
        ssize_t chunk_index
        ssize_t chunk_num
        ssize_t num_cols
        int64_t chunk_length
        uint64_t num_rows_in_chunk

    cdef int _calculate_num_rows_in_chunk(self) except -1:
        """
        Calculates the number of rows in the chunk and stores it for future
        use.
        """
        cdef:
            ArrowArrayImpl array_impl
            int64_t num_rows
        array_impl = self.df_impl.arrays[self.chunk_index]
        array_impl.get_length(&num_rows)
        self.num_rows_in_chunk = <uint64_t> num_rows

    cdef int _next_batch(self) except -1:
        """
        Goes to the next batch of data.
        """
        cdef:
            ssize_t array_index, num_cols
            ArrowArrayImpl array_impl
            BindVar bind_var
            ssize_t i
        self.message_offset = self.offset
        self._calculate_num_rows_in_batch(self.num_rows_in_chunk)
        if self.num_rows == 0:
            self._next_chunk()
        if self.num_rows > 0:
            for i, bind_var in enumerate(self.cursor_impl.bind_vars):
                array_impl = self.df_impl.arrays[self.chunk_index + i]
                bind_var.var_impl._arrow_array = array_impl
                bind_var.var_impl._on_reset_bind(self.offset, self.num_rows)

    cdef int _next_chunk(self) except -1:
        """
        Goes to the next chunk in the list of chunks for the dataframe.
        """
        while self.chunk_num + 1 < self.num_chunks:
            self.offset = 0
            self.message_offset = 0
            self.chunk_num += 1
            self.chunk_index += self.num_cols
            self._calculate_num_rows_in_chunk()
            self._calculate_num_rows_in_batch(self.num_rows_in_chunk)
            if self.num_rows > 0:
                break

    cdef int _setup_cursor(self) except -1:
        """
        Called after the manager has been populated and helps set up the cursor
        if one is being used.
        """
        cdef:
            ArrowSchemaImpl schema_impl
            BaseVarImpl var_impl
            BindVar bind_var
            ssize_t i
        self.cursor_impl.bind_vars = []
        for i, schema_impl in enumerate(self.df_impl.schema_impls):
            bind_var = BindVar.__new__(BindVar)
            bind_var.pos = i + 1
            var_impl = self.cursor_impl._create_var_impl(self.conn)
            var_impl.metadata = OracleMetadata.from_arrow_schema(schema_impl)
            bind_var.var_impl = var_impl
            self.cursor_impl.bind_vars.append(bind_var)

    @staticmethod
    cdef BatchLoadManager create(DataFrameImpl df_impl):
        """
        Creates a batch load manager given a dataframe.
        """
        cdef DataFrameBatchLoadManager m
        m = DataFrameBatchLoadManager.__new__(DataFrameBatchLoadManager)
        m.df_impl = df_impl
        m.num_cols = len(df_impl.schema_impls)
        m.num_chunks = len(df_impl.arrays) // m.num_cols
        m._calculate_num_rows_in_chunk()
        return m


@cython.final
cdef class FullDataBatchLoadManager(BatchLoadManager):
    cdef:
        list all_rows
        uint64_t total_num_rows
        object type_handler

    cdef int _next_batch(self) except -1:
        """
        Goes to the next batch of data.
        """
        cdef:
            bint defer_type_assignment = (self.offset == 0)
            object row
            ssize_t i
        self._calculate_num_rows_in_batch(self.total_num_rows)
        self.cursor_impl._reset_bind_vars(self.offset, self.num_rows)
        for i in range(self.num_rows):
            if i == self.num_rows - 1:
                defer_type_assignment = False
            row = self.all_rows[self.offset + i]
            self.cursor_impl._bind_values(self.cursor, self.type_handler,
                                          row, self.num_rows, i,
                                          defer_type_assignment)

    cdef int _setup_cursor(self) except -1:
        """
        Called after the manager has been populated and helps set up the cursor
        if one is being used.
        """
        self.type_handler = self.cursor_impl._get_input_type_handler()

    @staticmethod
    cdef BatchLoadManager create(list all_rows):
        """
        Creates a batch load manager given a list of rows.
        """
        cdef FullDataBatchLoadManager m
        m = FullDataBatchLoadManager.__new__(FullDataBatchLoadManager)
        m.all_rows = all_rows
        m.total_num_rows = <uint64_t> len(all_rows)
        return m


@cython.final
cdef class PrePopulatedBatchLoadManager(BatchLoadManager):
    cdef:
        uint64_t total_num_rows

    cdef int _next_batch(self) except -1:
        """
        Goes to the next batch in the set of data, if applicable.
        """
        cdef:
            BaseVarImpl var_impl
            BindVar bind_var
        self._calculate_num_rows_in_batch(self.total_num_rows)
        if self.cursor_impl.bind_vars is not None:
            for bind_var in self.cursor_impl.bind_vars:
                if bind_var is None or bind_var.var_impl is None:
                    continue
                var_impl = bind_var.var_impl
                if var_impl.num_elements < self.num_rows:
                    errors._raise_err(errors.ERR_INCORRECT_VAR_ARRAYSIZE,
                                      var_arraysize=var_impl.num_elements,
                                      required_arraysize=self.num_rows)

    @staticmethod
    cdef BatchLoadManager create(uint64_t total_num_rows):
        """
        Creates a batch load manager given the number of pre-populated rows.
        """
        cdef PrePopulatedBatchLoadManager m
        m = PrePopulatedBatchLoadManager.__new__(PrePopulatedBatchLoadManager)
        m.total_num_rows = total_num_rows
        return m
