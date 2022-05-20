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
# queue.pyx
#
# Cython file defining the base Queue implementation class (embedded in
# base_impl.pyx).
#------------------------------------------------------------------------------

cdef class BaseQueueImpl:

    @utils.CheckImpls("dequeuing multiple messages")
    def deq_many(self, uint32_t max_num_messages):
        pass

    @utils.CheckImpls("dequeuing a single message")
    def deq_one(self):
        pass

    @utils.CheckImpls("enqueueing multiple messages")
    def enq_many(self, list props_impls):
        pass

    @utils.CheckImpls("enqueuing a single message")
    def enq_one(self, BaseMsgPropsImpl props_impl):
        pass

    @utils.CheckImpls("initializing a queue")
    def initialize(self, BaseConnImpl conn_impl, str name,
                   BaseDbObjectImpl payload_type):
        pass


cdef class BaseDeqOptionsImpl:

    @utils.CheckImpls("getting the condition")
    def get_condition(self):
        pass

    @utils.CheckImpls("getting the consumer name")
    def get_consumer_name(self):
        pass

    @utils.CheckImpls("getting the correlation")
    def get_correlation(self):
        pass

    @utils.CheckImpls("getting the message id")
    def get_message_id(self):
        pass

    @utils.CheckImpls("getting the mode")
    def get_mode(self):
        pass

    @utils.CheckImpls("getting the navigation")
    def get_navigation(self):
        pass

    @utils.CheckImpls("getting the transformation")
    def get_transformation(self):
        pass

    @utils.CheckImpls("getting the visibility")
    def get_visibility(self):
        pass

    @utils.CheckImpls("getting the wait time")
    def get_wait(self):
        pass

    @utils.CheckImpls("setting the condition")
    def set_condition(self, str value):
        pass

    @utils.CheckImpls("setting the consumer name")
    def set_consumer_name(self, str value):
        pass

    @utils.CheckImpls("setting the correlation")
    def set_correlation(self, str value):
        pass

    @utils.CheckImpls("setting the delivery mode")
    def set_delivery_mode(self, uint16_t value):
        pass

    @utils.CheckImpls("setting the mode")
    def set_mode(self, uint32_t value):
        pass

    @utils.CheckImpls("setting the message id")
    def set_message_id(self, bytes value):
        pass

    @utils.CheckImpls("setting the navigation")
    def set_navigation(self, uint32_t value):
        pass

    @utils.CheckImpls("setting the transformation")
    def set_transformation(self, str value):
        pass

    @utils.CheckImpls("setting the visibility")
    def set_visibility(self, uint32_t value):
        pass

    @utils.CheckImpls("setting the wait time")
    def set_wait(self, uint32_t value):
        pass


cdef class BaseEnqOptionsImpl:

    @utils.CheckImpls("getting the transformation")
    def get_transformation(self):
        pass

    @utils.CheckImpls("getting the visibility")
    def get_visibility(self):
        pass

    @utils.CheckImpls("setting the delivery mode")
    def set_delivery_mode(self, uint16_t value):
        pass

    @utils.CheckImpls("setting the transformation")
    def set_transformation(self, str value):
        pass

    @utils.CheckImpls("setting the visibility")
    def set_visibility(self, uint32_t value):
        pass


cdef class BaseMsgPropsImpl:

    @utils.CheckImpls("getting the number of attempts")
    def get_num_attempts(self):
        pass

    @utils.CheckImpls("getting the correlation")
    def get_correlation(self):
        pass

    @utils.CheckImpls("getting the delay")
    def get_delay(self):
        pass

    @utils.CheckImpls("getting the delivery mode")
    def get_delivery_mode(self):
        pass

    @utils.CheckImpls("getting the enqueue time")
    def get_enq_time(self):
        pass

    @utils.CheckImpls("getting the name of the exception queue")
    def get_exception_queue(self):
        pass

    @utils.CheckImpls("getting the expiration")
    def get_expiration(self):
        pass

    @utils.CheckImpls("getting the message id")
    def get_message_id(self):
        pass

    @utils.CheckImpls("getting the priority")
    def get_priority(self):
        pass

    @utils.CheckImpls("getting the message state")
    def get_state(self):
        pass

    @utils.CheckImpls("setting the correlation")
    def set_correlation(self, str value):
        pass

    @utils.CheckImpls("setting the delay")
    def set_delay(self, int32_t value):
        pass

    @utils.CheckImpls("setting the name of the exception queue")
    def set_exception_queue(self, str value):
        pass

    @utils.CheckImpls("setting the expiration")
    def set_expiration(self, int32_t value):
        pass

    @utils.CheckImpls("setting the payload from bytes")
    def set_payload_bytes(self, bytes value):
        pass

    @utils.CheckImpls("setting the payload from a database object")
    def set_payload_object(self, BaseDbObjectImpl value):
        pass

    @utils.CheckImpls("setting the priority")
    def set_priority(self, int32_t value):
        pass

    @utils.CheckImpls("setting recipients list")
    def set_recipients(self, list value):
        pass
