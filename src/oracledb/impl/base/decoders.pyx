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
# decoders.pyx
#
# Cython file defining the low-level decoding routines used by the driver.
#------------------------------------------------------------------------------

cdef inline uint16_t decode_uint16be(const char_type *buf):
    """
    Decodes a 16-bit integer in big endian order (most significant byte first).
    """
    return (
        (<uint16_t> buf[0] << 8) |
        (<uint16_t> buf[1])
    )


cdef inline uint32_t decode_uint32be(const char_type *buf):
    """
    Decodes a 32-bit integer in big endian order (most significant byte first).
    """
    return (
        (<uint32_t> buf[0] << 24) |
        (<uint32_t> buf[1] << 16) |
        (<uint32_t> buf[2] << 8) |
        (<uint32_t> buf[3])
    )


cdef inline uint16_t decode_uint16le(const char_type *buf):
    """
    Decodes a 16-bit integer in little endian order (least significant byte
    first).
    """
    return (
        (<uint16_t> buf[1] << 8) |
        (<uint16_t> buf[0])
    )


cdef inline uint64_t decode_uint64be(const char_type *buf):
    """
    Decodes a 64-bit integer in big endian order (most significant byte first).
    """
    return (
        (<uint64_t> buf[0] << 56) |
        (<uint64_t> buf[1] << 48) |
        (<uint64_t> buf[2] << 40) |
        (<uint64_t> buf[3] << 32) |
        (<uint64_t> buf[4] << 24) |
        (<uint64_t> buf[5] << 16) |
        (<uint64_t> buf[6] << 8) |
        (<uint64_t> buf[7])
    )
