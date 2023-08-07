#------------------------------------------------------------------------------
# Copyright (c) 2023, Oracle and/or its affiliates.
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
# cookie.pyx
#
# Cython file defining the cookie used to identify a server such that a number
# of round trips can be saved during connect (embedded in thin_impl.pyx).
#------------------------------------------------------------------------------

cdef class ConnectionCookie:
    cdef:
        uint8_t protocol_version
        bytes server_banner
        uint16_t charset_id
        uint16_t ncharset_id
        uint8_t flags
        bytes compile_caps
        bytes runtime_caps
        bint populated

cdef dict connection_cookies_by_uuid = {}

cdef ConnectionCookie get_connection_cookie_by_uuid(bytes uuid,
                                                    Description description):
    """
    Returns a connection cookie given the UUID supplied in the accept packet.
    If no such cookie exists, a new one is created and returned for population.
    """
    cdef:
        ConnectionCookie cookie
        str key_str
        bytes key
    key_str = description.service_name or description.sid or ""
    key = uuid + key_str.encode()
    cookie = connection_cookies_by_uuid.get(key)
    if cookie is None:
        cookie = ConnectionCookie.__new__(ConnectionCookie)
        connection_cookies_by_uuid[key] = cookie
    return cookie
