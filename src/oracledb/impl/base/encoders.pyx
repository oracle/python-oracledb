#------------------------------------------------------------------------------
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
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# encoders.pyx
#
# Cython file defining the low-level encoding routines used by the driver.
#------------------------------------------------------------------------------

cdef inline void encode_uint16be(char_type *buf, uint16_t value):
    """
    Encodes a 16-bit integer in big endian order (most significant byte first).
    """
    buf[0] = <char_type> ((value >> 8) & 0xff)
    buf[1] = <char_type> (value & 0xff)


cdef inline void encode_uint16le(char_type *buf, uint16_t value):
    """
    Encodes a 16-bit integer in big endian order (most significant byte first).
    """
    buf[1] = <char_type> ((value >> 8) & 0xff)
    buf[0] = <char_type> (value & 0xff)


cdef inline void encode_uint32be(char_type *buf, uint32_t value):
    """
    Encodes a 32-bit integer in big endian order (most significant byte first).
    """
    buf[0] = <char_type> ((value >> 24) & 0xff)
    buf[1] = <char_type> ((value >> 16) & 0xff)
    buf[2] = <char_type> ((value >> 8) & 0xff)
    buf[3] = <char_type> (value & 0xff)


cdef inline void encode_uint64be(char_type *buf, uint64_t value):
    """
    Decodes a 64-bit integer in big endian order (most significant byte first).
    """
    buf[0] = <char_type> ((value >> 56) & 0xff)
    buf[1] = <char_type> ((value >> 48) & 0xff)
    buf[2] = <char_type> ((value >> 40) & 0xff)
    buf[3] = <char_type> ((value >> 32) & 0xff)
    buf[4] = <char_type> ((value >> 24) & 0xff)
    buf[5] = <char_type> ((value >> 16) & 0xff)
    buf[6] = <char_type> ((value >> 8) & 0xff)
    buf[7] = <char_type> (value & 0xff)
