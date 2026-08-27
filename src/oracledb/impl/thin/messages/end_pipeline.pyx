#------------------------------------------------------------------------------
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
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
# end_pipeline.pyx
#
# Cython file defining the messages sent to the database and the responses that
# are received by the client for ending a pipeline (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

@cython.final
cdef class EndPipelineMessage(Message):
    cdef:
        list messages
        bint continue_on_error
        bint in_completion

    def _complete_pipeline_op(self, Message message):
        """
        Completes a particular pipeline operation.
        """
        cdef:
            PipelineOpResultImpl result_impl = message.pipeline_result_impl
            MessageWithData fetch_message, message_with_data
            PipelineOpImpl op_impl = result_impl.operation
            uint8_t op_type = op_impl.op_type
            ThinCursorImpl cursor_impl
            BindVar bind_var

        # all operations other than commit make use of a cursor
        if op_type == PIPELINE_OP_TYPE_COMMIT:
            return

        # keep warning, if applicable
        message_with_data = <MessageWithData> message
        result_impl.warning = message_with_data.warning

        # get return value of functions and process rows for fetch operations
        cursor_impl = message_with_data.cursor_impl
        if op_impl.op_type == PIPELINE_OP_TYPE_CALL_FUNC:
            bind_var = <BindVar> cursor_impl.bind_vars[0]
            result_impl.return_value = bind_var.var_impl.get_value(0)
        elif op_type in (
            PIPELINE_OP_TYPE_FETCH_ONE,
            PIPELINE_OP_TYPE_FETCH_MANY,
            PIPELINE_OP_TYPE_FETCH_ALL,
        ):
            result_impl.rows = []
            while cursor_impl._buffer_rowcount > 0:
                result_impl.rows.append(cursor_impl._create_row())
        result_impl.fetch_metadata = cursor_impl.fetch_metadata

        # for fetchall(), perform as many round trips as are required to
        # complete the fetch
        if op_type == PIPELINE_OP_TYPE_FETCH_ALL \
                and cursor_impl._more_rows_to_fetch:
            fetch_message = cursor_impl._create_message(
                FetchMessage, message_with_data.cursor
            )
            while cursor_impl._more_rows_to_fetch:
                yield fetch_message
                while cursor_impl._buffer_rowcount > 0:
                    result_impl.rows.append(cursor_impl._create_row())
                if op_type != PIPELINE_OP_TYPE_FETCH_ALL:
                    break

        # for PL/SQL blocks that required a single execute, perform any
        # remaining executes now
        if op_type == PIPELINE_OP_TYPE_EXECUTE_MANY \
                and message_with_data.num_execs < op_impl.num_execs:
            while op_impl.num_execs > 0:
                op_impl.num_execs -= 1
                message_with_data.offset += 1
                if not cursor_impl._statement.requires_single_execute():
                    break
                yield message
            if op_impl.num_execs > 0:
                message_with_data.num_execs = op_impl.num_execs
                yield message

        # populate the metadata for any partial types observed during the
        # execution of the pipeline
        if message_with_data.type_cache is not None:
            conn = message_with_data.cursor.connection
            yield from message_with_data.type_cache.populate_partial_types(conn)

    def _complete_pipeline_ops(self):
        """
        Completes any pipeline operations that have not actually completed.
        This could be due to the fact that LOBs were fetched or a fetch all
        operation has more rows to fetch.
        """
        cdef:
            PipelineOpResultImpl result_impl
            Message message
        for message in self.messages:
            result_impl = message.pipeline_result_impl
            if result_impl.error is not None:
                continue
            try:
                yield from self._complete_pipeline_op(message)
            except Exception as e:
                if not self.continue_on_error:
                    raise
                result_impl._capture_err(e)

    cdef int _initialize_hook(self) except -1:
        """
        Perform initialization.
        """
        self.function_code = TNS_FUNC_PIPELINE_END

    def _resend_messages(self):
        """
        Resends any messages that require that (for operations that fetch LOBS,
        for example).
        """
        cdef Message message
        for message in self.messages:
            try:
                if message.resend:
                    message.resend = False
                    yield message
            except Exception as e:
                if not self.continue_on_error:
                    raise
                message.pipeline_result_impl._capture_err(e)

    async def _run_postprocess_for_messages(self):
        """
        Runs any postprocessing required for messages.
        """
        cdef Message message
        for message in self.messages:
            try:
                await message.postprocess_async()
            except Exception as e:
                if not self.continue_on_error:
                    raise
                message.pipeline_result_impl._capture_err(e)

    cdef int _send_messages(self) except -1:
        """
        Sends the messages for the pipeline to the database for processing.
        """
        cdef:
            WriteBuffer buf = self.conn_impl._protocol._write_buf
            Message message
        for message in self.messages:
            try:
                message.send(buf)
            except Exception as e:
                if not self.continue_on_error:
                    raise
                message.pipeline_result_impl._capture_err(e)

    cdef int _write_message(self, WriteBuffer buf) except -1:
        """
        Write the message to the buffer.
        """
        self._write_function_code(buf)
        buf.write_ub4(0)                    # ID (unused)

    async def process_pipeline(self):
        """
        Run the requested pipeline. If the database supports it, the message
        itself will be sent; otherwise, the pipeline will be run separately.
        """
        cdef:
            BaseAsyncProtocol protocol = self.conn_impl._protocol
            ReadBuffer buf = protocol._read_buf
            ssize_t num_responses_to_discard
            Message message
        if self.in_completion:
            return await self._run_postprocess_for_messages()
        self._send_messages()
        self.send(protocol._write_buf)
        buf._check_request_boundary = True
        buf._in_pipeline = True
        try:
            num_responses_to_discard = len(self.messages) + 1
            for message in self.messages:
                try:
                    if not buf.has_response():
                        await buf.wait_for_response_async()
                    buf._start_packet()
                    message.preprocess()
                    message.process(buf)
                    num_responses_to_discard -= 1
                    protocol._process_call_status(
                        self.conn_impl, message.call_status
                    )
                    message._check_and_raise_exception()
                except Exception as e:
                    if not self.continue_on_error:
                        raise
                    message.pipeline_result_impl._capture_err(e)
            await protocol._receive_packet(
                self, check_request_boundary=True
            )
            self.process(buf)
            num_responses_to_discard = 0
            self._check_and_raise_exception()
            self.in_completion = True
        except:
            await buf.discard_pipeline_responses(num_responses_to_discard)
            raise
        finally:
            buf._check_request_boundary = False
            buf._in_pipeline = False
