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
# dbapi_extension.py
#
# Used to document functionality that is an extension to the DB API definition.
# -----------------------------------------------------------------------------

from docutils import nodes
from docutils.parsers.rst import Directive


class DbApiExtension(Directive):
    has_content = True

    def run(self):
        text = f"{self.prefix} {' '.join(self.content)}"
        result = [nodes.emphasis(text=text), nodes.paragraph()]
        return result


class DbApiMethodExtension(DbApiExtension):
    prefix = "This method is an extension to the DB API definition."


class DbApiAttributeExtension(DbApiExtension):
    prefix = "This attribute is an extension to the DB API definition."


class DbApiConstantExtension(DbApiExtension):
    prefix = "These constants are extensions to the DB API definition."


class DbApiObjectExtension(DbApiExtension):
    prefix = "This object is an extension to the DB API definition."


def setup(app):
    app.add_directive("dbapimethodextension", DbApiMethodExtension)
    app.add_directive("dbapiattributeextension", DbApiAttributeExtension)
    app.add_directive("dbapiconstantextension", DbApiConstantExtension)
    app.add_directive("dbapiobjectextension", DbApiObjectExtension)
