# -----------------------------------------------------------------------------
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
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# base.py
#
# Contains base classes and methods that have no internal dependencies.
# -----------------------------------------------------------------------------

from . import __name__ as MODULE_NAME


# metaclass used by all oracledb classes; currently this only ensures that when
# the class is displayed it only shows the overall module name instead of any
# subpackage names
class BaseMetaClass(type):

    def __new__(cls, name, bases, attrs):
        module_name = attrs["__module__"]
        qual_name = attrs["__qualname__"]
        if module_name.startswith(MODULE_NAME):
            module_name = MODULE_NAME
        attrs["_public_name"] = f"{module_name}.{qual_name}"
        return super().__new__(cls, name, bases, attrs)

    def __repr__(cls):
        return f"<class '{cls._public_name}'>"
