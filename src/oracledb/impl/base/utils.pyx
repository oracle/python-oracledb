#------------------------------------------------------------------------------
# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
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
# utils.pyx
#
# Cython file defining utility methods (embedded in base_impl.pyx).
#------------------------------------------------------------------------------

cdef int _set_bool_param(dict args, str name, bint *out_val) except -1:
    """
    Sets a boolean parameter to the value provided in the dictionary. This can
    be a case-insenstive string matching on/off, yes/no or true/false (such as
    when parsed from a connect string). It can also be a directly passed
    argument which will be explicitly converted to a boolean value.
    """
    in_val = args.get(name)
    if in_val is not None:
        if isinstance(in_val, str):
            out_val[0] = (in_val.strip().lower() in ("on", "yes", "true"))
        else:
            out_val[0] = bool(in_val)


cdef int _set_duration_param(dict args, str name, double *out_val) except -1:
    """
    Sets a duration parameter to the value provided in the dictionary. This can
    be a string (such as when parsed from a connect string) containing a
    floating point value followed by an otional unit: ms (milliseconds), sec
    (seconds) or min (minutes). It can also be a directly passed argument which
    will be explicitly converted to a floating point value.
    """
    in_val = args.get(name)
    if in_val is not None:
        if isinstance(in_val, str):
            in_val = in_val.strip().lower()
            if in_val.endswith("sec"):
                out_val[0] = float(in_val[:-3].strip())
            elif in_val.endswith("ms"):
                out_val[0] = float(in_val[:-2].strip()) / 1000
            elif in_val.endswith("min"):
                out_val[0] = float(in_val[:-3].strip()) * 60
            else:
                out_val[0] = float(in_val.strip())
        else:
            out_val[0] = float(in_val)


cdef int _set_int_param(dict args, str name, int* out_val) except -1:
    """
    Sets an integer parameter to the value provided in the dictionary. This
    can be a string (such as when parsed from a connect string). It can also be
    a directly passed argument which will be explicitly converted to an integer
    value.
    """
    in_val = args.get(name)
    if in_val is not None:
        out_val[0] = int(in_val)


cdef int _set_uint_param(dict args, str name, uint32_t* out_val) except -1:
    """
    Sets an unsigned integer parameter to the value provided in the dictionary.
    This can be a string (such as when parsed from a connect string). It can
    also be a directly passed argument which will be explicitly converted to an
    integer value.
    """
    in_val = args.get(name)
    if in_val is not None:
        out_val[0] = int(in_val)


cdef int _set_obj_param(dict args, str name, object target) except -1:
    """
    Sets an object parameter to the value provided in the dictionary, if a
    value is provided. This value is then set directly on the target.
    """
    in_val = args.get(name)
    if in_val is not None:
        setattr(target, name, in_val)


cdef int _set_protocol_param(dict args, str name, object target) except -1:
    """
    Sets a protocol parameter to the value provided in the dictionary. This
    must be one of "tcp" or "tcps" currently. If it is not one of these values
    an error is raised. If a value is specified and meets the criteria it is
    set directly on the target (since strings are treated as Python objects).
    """
    in_val = args.get(name)
    if in_val is not None:
        in_val = in_val.lower()
        if in_val not in ("tcp", "tcps"):
            errors._raise_err(errors.ERR_INVALID_PROTOCOL, protocol=in_val)
        setattr(target, name, in_val)


cdef int _set_purity_param(dict args, str name, uint32_t* out_val) except -1:
    """
    Sets a purity parameter to the value provided in the dictionary. This
    must be one of "new" or "self" currently (or the equivalent constants, if
    specified directly). If it is not one of these values an error is raised.
    """
    cdef bint ok = True
    in_val = args.get(name)
    if in_val is not None:
        if isinstance(in_val, str):
            in_val = in_val.lower()
            if in_val == "new":
                out_val[0] = PURITY_NEW
            elif in_val == "self":
                out_val[0] = PURITY_SELF
            else:
                ok = False
        elif isinstance(in_val, int):
            if in_val == PURITY_NEW:
                out_val[0] = PURITY_NEW
            elif in_val == PURITY_SELF:
                out_val[0] = PURITY_SELF
            elif in_val == PURITY_DEFAULT:
                out_val[0] = PURITY_DEFAULT
            else:
                ok = False
        else:
            ok = False
        if not ok:
            errors._raise_err(errors.ERR_INVALID_POOL_PURITY,
                              purity=in_val)


cdef int _set_server_type_param(dict args, str name, object target) except -1:
    """
    Sets a server type parameter to the value provided in the dictionary. This
    must be one of "dedicated", "pooled" or "shared" currently. If it is not
    one of these values an error is raised. If a value is specified and meets
    the criteria it is set directly on the target (since strings are treated as
    Python objects).
    """
    in_val = args.get(name)
    if in_val is not None:
        in_val = in_val.lower()
        if in_val not in ("dedicated", "pooled", "shared"):
            errors._raise_err(errors.ERR_INVALID_SERVER_TYPE,
                              server_type=in_val)
        setattr(target, name, in_val)


cdef int _set_str_param(dict args, str name, object target) except -1:
    """
    Sets a string parameter to the value provided in the dictionary. If a value
    is specified it is set directly on the target (since strings are treated as
    Python objects).
    """
    in_val = args.get(name)
    if in_val:
        setattr(target, name, str(in_val))


def init_base_impl(package):
    """
    Initializes globals after the package has been completely initialized. This
    is to avoid circular imports and eliminate the need for global lookups.
    """
    global PY_TYPE_ASYNC_CURSOR, PY_TYPE_ASYNC_LOB, PY_TYPE_CURSOR
    global PY_TYPE_DB_OBJECT, PY_TYPE_DB_OBJECT_TYPE, PY_TYPE_LOB, PY_TYPE_VAR
    global PY_TYPE_FETCHINFO, PY_TYPE_JSON_ID, PY_TYPE_INTERVAL_YM
    PY_TYPE_ASYNC_CURSOR = package.AsyncCursor
    PY_TYPE_ASYNC_LOB = package.AsyncLOB
    PY_TYPE_CURSOR = package.Cursor
    PY_TYPE_DB_OBJECT = package.DbObject
    PY_TYPE_DB_OBJECT_TYPE = package.DbObjectType
    PY_TYPE_JSON_ID = package.JsonId
    PY_TYPE_FETCHINFO = package.FetchInfo
    PY_TYPE_INTERVAL_YM = package.IntervalYM
    PY_TYPE_LOB = package.LOB
    PY_TYPE_VAR = package.Var
