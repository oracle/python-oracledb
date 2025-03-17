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
# queue.pyx
#
# Cython file defining the thin Queue implementation class (embedded in
# thin_impl.pyx).
#------------------------------------------------------------------------------

cdef class BaseThinQueueImpl(BaseQueueImpl):

    cdef:
        BaseThinConnImpl _conn_impl
        bytes payload_toid

    cdef AqArrayMessage _create_array_deq_message(self, uint32_t num_iters):
        """
        Create the message used for dequeuing multiple AQ messages
        """
        cdef:
            AqArrayMessage message
            uint32_t i
        message = self._conn_impl._create_message(AqArrayMessage)
        message.num_iters = num_iters
        message.props_impls = [ThinMsgPropsImpl() for i in range(num_iters)]
        message.queue_impl = self
        message.deq_options_impl = self.deq_options_impl
        message.operation = TNS_AQ_ARRAY_DEQ
        return message

    cdef AqArrayMessage _create_array_enq_message(self, list props_impls):
        """
        Create the message used for enqueuing multiple AQ messages
        """
        cdef AqArrayMessage message
        message = self._conn_impl._create_message(AqArrayMessage)
        message.queue_impl = self
        message.enq_options_impl = self.enq_options_impl
        message.props_impls = props_impls
        message.operation = TNS_AQ_ARRAY_ENQ
        message.num_iters = len(props_impls)
        return message

    cdef AqDeqMessage _create_deq_message(self):
        """
        Create the message for dequeuing a payload.
        """
        cdef:
            ThinMsgPropsImpl props_impl
            AqDeqMessage message
        props_impl = ThinMsgPropsImpl()
        message = self._conn_impl._create_message(AqDeqMessage)
        message.queue_impl = self
        message.deq_options_impl = self.deq_options_impl
        message.props_impl = props_impl
        return message

    cdef AqEnqMessage _create_enq_message(self, ThinMsgPropsImpl props_impl):
        """
        Create the message for enqueuing the provided payload.
        """
        cdef AqEnqMessage message
        message = self._conn_impl._create_message(AqEnqMessage)
        message.queue_impl = self
        message.enq_options_impl = self.enq_options_impl
        message.props_impl = props_impl
        return message

    def initialize(self, BaseThinConnImpl conn_impl, str name,
                   ThinDbObjectTypeImpl payload_type, bint is_json):
        """
        Internal method for initializing the queue.
        """
        self._conn_impl = conn_impl
        self.is_json = is_json
        self.deq_options_impl = ThinDeqOptionsImpl()
        self.enq_options_impl = ThinEnqOptionsImpl()
        self.payload_type = payload_type
        if self.is_json:
            self.payload_toid = bytes([0]*15+[0x47])
        elif self.payload_type is not None:
            self.payload_toid = payload_type.oid
        else:
            self.payload_toid = bytes([0]*15+[0x17])
        self.name = name


cdef class ThinQueueImpl(BaseThinQueueImpl):

    def deq_many(self, uint32_t max_num_messages):
        """
        Internal method for dequeuing multiple messages from a queue.
        """
        cdef:
            Protocol protocol = <Protocol> self._conn_impl._protocol
            AqArrayMessage message
        message = self._create_array_deq_message(max_num_messages)
        protocol._process_single_message(message)
        if message.no_msg_found:
            return []
        return message.props_impls[:message.num_iters]

    def deq_one(self):
        """
        Internal method for dequeuing a single message from a queue.
        """
        cdef:
            Protocol protocol = <Protocol> self._conn_impl._protocol
            AqDeqMessage message
        message = self._create_deq_message()
        protocol._process_single_message(message)
        if not message.no_msg_found:
            return message.props_impl

    def enq_many(self, list props_impls):
        """
        Internal method for enqueuing many messages into a queue.
        """
        cdef :
            Protocol protocol = <Protocol> self._conn_impl._protocol
            AqArrayMessage message
        message = self._create_array_enq_message(props_impls)
        protocol._process_single_message(message)

    def enq_one(self, ThinMsgPropsImpl props_impl):
        """
        Internal method for enqueuing a single message into a queue.
        """
        cdef:
            Protocol protocol = <Protocol> self._conn_impl._protocol
            AqEnqMessage message
        message = self._create_enq_message(props_impl)
        protocol._process_single_message(message)


cdef class AsyncThinQueueImpl(BaseThinQueueImpl):

    async def deq_many(self, uint32_t max_num_messages):
        """
        Internal method for dequeuing multiple messages from a queue.
        """
        cdef:
            BaseAsyncProtocol protocol
            AqArrayMessage message
        protocol = <BaseAsyncProtocol> self._conn_impl._protocol
        message = self._create_array_deq_message(max_num_messages)
        await protocol._process_single_message(message)
        if message.no_msg_found:
            return []
        return message.props_impls[:message.num_iters]

    async def deq_one(self):
        """
        Internal method for dequeuing a single message from a queue.
        """
        cdef:
            BaseAsyncProtocol protocol
            AqDeqMessage message
        protocol = <BaseAsyncProtocol> self._conn_impl._protocol
        message = self._create_deq_message()
        await protocol._process_single_message(message)
        if not message.no_msg_found:
            return message.props_impl

    async def enq_many(self, list props_impls):
        """
        Internal method for enqueuing many messages into a queue.
        """
        cdef :
            BaseAsyncProtocol protocol
            AqArrayMessage message
        protocol = <BaseAsyncProtocol> self._conn_impl._protocol
        message = self._create_array_enq_message(props_impls)
        await protocol._process_single_message(message)

    async def enq_one(self, ThinMsgPropsImpl props_impl):
        """
        Internal method for enqueuing a single message into a queue.
        """
        cdef:
            BaseAsyncProtocol protocol
            AqEnqMessage message
        protocol = <BaseAsyncProtocol> self._conn_impl._protocol
        message = self._create_enq_message(props_impl)
        await protocol._process_single_message(message)


cdef class ThinDeqOptionsImpl(BaseDeqOptionsImpl):
    cdef:
        str condition
        str consumer_name
        str correlation
        uint16_t delivery_mode
        uint32_t mode
        bytes msgid
        uint32_t navigation
        str transformation
        uint32_t visibility
        uint32_t wait

    def __init__(self):
        self.delivery_mode = TNS_AQ_MSG_PERSISTENT
        self.mode = TNS_AQ_DEQ_REMOVE
        self.navigation = TNS_AQ_DEQ_NEXT_MSG
        self.visibility = TNS_AQ_DEQ_ON_COMMIT
        self.wait = TNS_AQ_DEQ_WAIT_FOREVER

    def get_condition(self):
        """
        Internal method for getting the condition.
        """
        return self.condition

    def get_consumer_name(self):
        """
        Internal method for getting the consumer name.
        """
        return self.consumer_name

    def get_correlation(self):
        """
        Internal method for getting the correlation.
        """
        return self.correlation

    def get_message_id(self):
        """
        Internal method for getting the message id.
        """
        return self.msgid

    def get_mode(self):
        """
        Internal method for getting the mode.
        """
        return self.mode

    def get_navigation(self):
        """
        Internal method for getting the navigation.
        """
        return self.navigation

    def get_transformation(self):
        """
        Internal method for getting the transformation.
        """
        return self.transformation

    def get_visibility(self):
        """
        Internal method for getting the visibility.
        """
        return self.visibility

    def get_wait(self):
        """
        Internal method for getting the wait.
        """
        return self.wait

    def set_condition(self, str value):
        """
        Internal method for setting the condition.
        """
        self.condition = value

    def set_consumer_name(self, str value):
        """
        Internal method for setting the consumer name.
        """
        self.consumer_name =  value

    def set_correlation(self, str value):
        """
        Internal method for setting the correlation.
        """
        self.correlation = value

    def set_delivery_mode(self, uint16_t value):
        """
        Internal method for setting the delivery mode.
        """
        self.delivery_mode = value

    def set_mode(self, uint32_t value):
        """
        Internal method for setting the mode.
        """
        self.mode = value

    def set_message_id(self, bytes value):
        """
        Internal method for setting the message id.
        """
        self.msgid = value

    def set_navigation(self, uint32_t value):
        """
        Internal method for setting the navigation.
        """
        self.navigation = value

    def set_transformation(self, str value):
        """
        Internal method for setting the transformation.
        """
        self.transformation = value

    def set_visibility(self, uint32_t value):
        """
        Internal method for setting the visibility.
        """
        self.visibility = value

    def set_wait(self, uint32_t value):
        """
        Internal method for setting the wait.
        """
        self.wait = value


cdef class ThinEnqOptionsImpl(BaseEnqOptionsImpl):
    cdef:
        str transformation
        uint32_t visibility
        uint32_t delivery_mode

    def __init__(self):
        self.visibility = TNS_AQ_ENQ_ON_COMMIT
        self.delivery_mode = TNS_AQ_MSG_PERSISTENT

    def get_transformation(self):
        """
        Internal method for getting the transformation.
        """
        return self.transformation

    def get_visibility(self):
        """
        Internal method for getting the visibility.
        """
        return self.visibility

    def set_delivery_mode(self, uint16_t value):
        """
        Internal method for setting the delivery mode.
        """
        self.delivery_mode = value

    def set_transformation(self, str value):
        """
        Internal method for setting the transformation.
        """
        self.transformation = value

    def set_visibility(self, uint32_t value):
        """
        Internal method for setting the visibility.
        """
        self.visibility = value


cdef class ThinMsgPropsImpl(BaseMsgPropsImpl):

    cdef:
        int32_t delay
        str correlation
        str exceptionq
        int32_t expiration
        int32_t priority
        list recipients
        int32_t num_attempts
        uint32_t delivery_mode
        cydatetime.datetime enq_time
        bytes msgid
        int32_t state
        object payload_obj
        BaseThinConnImpl _conn_impl
        bytes enq_txn_id
        bytes sender_agent_name
        bytes sender_agent_address
        unsigned char sender_agent_protocol
        bytes original_msg_id

    def __init__(self):
        self.delay = TNS_AQ_MSG_NO_DELAY
        self.expiration = TNS_AQ_MSG_NO_EXPIRATION
        self.recipients = []
        self.sender_agent_protocol = 0

    def get_num_attempts(self):
        """
        Internal method for getting the number of attempts made.
        """
        return self.num_attempts

    def get_correlation(self):
        """
        Internal method for getting the correlation.
        """
        return self.correlation

    def get_delay(self):
        """
        Internal method for getting the delay.
        """
        return self.delay

    def get_delivery_mode(self):
        """
        Internal method for getting the delivery mode.
        """
        return self.delivery_mode

    def get_enq_time(self):
        """
        Internal method for getting the enqueue time.
        """
        return self.enq_time

    def get_exception_queue(self):
        """
        Internal method for getting the exception queue.
        """
        return self.exceptionq

    def get_expiration(self):
        """
        Internal method for getting the message expiration.
        """
        return self.expiration

    def get_message_id(self):
        """
        Internal method for getting the message id.
        """
        return self.msgid

    def get_priority(self):
        """
        Internal method for getting the priority.
        """
        return self.priority

    def get_state(self):
        """
        Internal method for getting the message state.
        """
        return self.state

    def set_correlation(self, str value):
        """
        Internal method for setting the correlation.
        """
        self.correlation = value

    def set_delay(self, int32_t value):
        """
        Internal method for setting the delay.
        """
        self.delay = value

    def set_exception_queue(self, str value):
        """
        Internal method for setting the exception queue.
        """
        self.exceptionq = value

    def set_expiration(self, int32_t value):
        """
        Internal method for setting the message expiration.
        """
        self.expiration = value

    def set_payload_bytes(self, bytes value):
        """
        Internal method for setting the payload from bytes.
        """
        self.payload_obj = value

    def set_payload_object(self, ThinDbObjectImpl value):
        """
        Internal method for setting the payload from an object.
        """
        if not isinstance(value, ThinDbObjectImpl):
            raise TypeError("Expected ThinDbObjectImpl instance.")
        self.payload_obj = value

    def set_payload_json(self, object json_val):
        """
        Internal method for setting the payload from a JSON object
        """
        self.payload_obj = json_val

    def set_priority(self, int32_t value):
        """
        Internal method for setting the priority.
        """
        self.priority = value

    def set_recipients(self, list value):
        """
        Internal method for setting the recipients list.
        """
        self.recipients = value
