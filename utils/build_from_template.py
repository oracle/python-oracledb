#------------------------------------------------------------------------------
# Copyright (c) 2022, Oracle and/or its affiliates.
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
# build_from_template.py
#
# Builds the parameter file from the template supplied on the command line.
# The generated file is written to the src/oracledb directory. The following
# template keys are recognized:
#
#   #{{ generated_notice }}
#       is replaced by a notice that the file is generated and should not be
#       modified directly
#   #{{ __init__ }}
#       is replaced by the generated __init__() method
#   #{{ __repr__ }}
#       is replaced by the generated repr() method
#   #{{ __properties__ }}
#       is replaced by the generated property getter and setter methods
#   #{{ __set__ }}
#       is replaced by the generated set() method
#
# All of these could be accomplished by decorators, but doing so would
# eliminate the usefulness of static analyzers such as those used within Visual
# Studio Code.
#------------------------------------------------------------------------------

import argparse
import configparser
import dataclasses
import os
import sys
import textwrap

TEXT_WIDTH = 79
GENERATED_NOTICE = """
*** NOTICE *** This file is generated from a template and should not be
modified directly. See build_from_template.py in the utils subdirectory for
more information.
"""

@dataclasses.dataclass
class Field:
    name: str = ""
    typ: str = ""
    default: str = ""
    hidden: bool = False
    pool_only: bool = False
    description: str = ""
    decorator: str = None

# parse command line
parser = argparse.ArgumentParser(description="build module from template")
parser.add_argument("name", help="the name of the module to generate")
args = parser.parse_args()

# determine location of template and source and validate template
template_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
target_dir = os.path.join(os.path.dirname(template_dir), "src", "oracledb")
template_name = os.path.join(template_dir, f"{args.name}_template.py")
config_name = os.path.join(template_dir, "fields.cfg")
target_name = os.path.join(target_dir, f"{args.name}.py")
if not os.path.exists(template_name):
    raise Exception(f"template {template_name} does not exist!")
if not os.path.exists(config_name):
    raise Exception(f"configuration {config_name} does not exist!")
code = open(template_name).read()
pool_only = "pool" in args.name

# acquire the fields from the configuration file
fields = []
config = configparser.ConfigParser()
config.read(config_name)
for section in config.sections():
    field = Field()
    field.name = section
    field.typ = config.get(section, "type")
    field.default = config.get(section, "default", fallback="None")
    field.hidden = config.getboolean(section, "hidden", fallback=False)
    field.pool_only = config.getboolean(section, "pool_only", fallback=False)
    field.description = config.get(section, "description", fallback="").strip()
    field.decorator = config.get(section, "decorator", fallback="")
    if not field.pool_only or pool_only:
        fields.append(field)

# replace the generated notice template tag
notice = textwrap.fill(GENERATED_NOTICE.strip(), initial_indent="# ",
                       subsequent_indent="# ", width=TEXT_WIDTH)
code = code.replace("#{{ generated_notice }}", notice)

# generate the constructor
indent = "        "
args = [f"{f.name}: {f.typ}={f.default}" for f in fields]
raw_header = "All parameters are optional. A brief description of each " + \
             "parameter follows:"
header = textwrap.fill(raw_header, initial_indent=indent,
                       subsequent_indent=indent, width=TEXT_WIDTH)
raw_descriptions = [f"- {f.name}: {f.description} (default: {f.default})" \
                    for f in fields if f.description]
descriptions = [textwrap.fill(d, initial_indent=indent,
                              subsequent_indent=indent + "  ",
                              width=TEXT_WIDTH) \
                for d in raw_descriptions]
doc_string = header + '\n\n' + '\n\n'.join(descriptions)
body = '    @utils.params_initer\n' + \
       '    def __init__(self, *,\n' + \
       '                 ' + \
       ',\n                 '.join(args) + '):\n' + \
       '        """\n' + \
       doc_string + '\n' + \
       '        """\n' + \
       '        pass'
code = code.replace("#{{ __init__ }}", body)

# generate the repr() function
reprs = []
prefix = "("
for field in fields:
    if field.hidden:
        continue
    reprs.append(f'f"{prefix}{field.name}={{self.{field.name}!r}}"')
    prefix = ", "
reprs[-1] = reprs[-1][:-1] + ')"'
body = '    def __repr__(self):\n' + \
       '        return self.__class__.__qualname__ + \\\n' + \
       '               ' + ' + \\\n               '.join(reprs)
code = code.replace("#{{ __repr__ }}", body)

# generate the property functions
indent = "        "
functions = []
for field in sorted(fields, key=lambda f: f.name.upper()):
    if field.hidden:
        continue
    if field.pool_only != pool_only:
        continue
    description = field.description[0].upper() + field.description[1:] + "."
    doc_string = textwrap.fill(description, initial_indent=indent,
                               subsequent_indent=indent, width=TEXT_WIDTH)
    return_type = f"Union[list, {field.typ}]" if field.decorator else field.typ
    body = f'    @property\n' + \
           (f'    @{field.decorator}\n' if field.decorator else '') + \
           f'    def {field.name}(self) -> {return_type}:\n' + \
           f'        """\n' + \
           f'{doc_string}\n' + \
           f'        """\n' + \
           f'        return self._impl.{field.name}'
    functions.append(body)
code = code.replace("#{{ properties }}", '\n\n'.join(functions))

# generate the set() method
args = [f"{f.name}: {f.typ}=None" for f in fields]
raw_descriptions = [f"- {f.name}: {f.description}" for f in fields \
                    if f.description]
descriptions = [textwrap.fill(d, initial_indent=indent,
                              subsequent_indent=indent + "  ",
                              width=TEXT_WIDTH) \
                for d in raw_descriptions]
doc_string = header + '\n\n' + '\n\n'.join(descriptions)
body = '    @utils.params_setter\n' + \
       '    def set(self, *,\n' + \
       '            ' + \
       ',\n            '.join(args) + '):\n' + \
       '        """\n' + \
       doc_string + '\n' + \
       '        """\n' + \
       '        pass'
code = code.replace("#{{ set }}", body)

# write the final code to the target location
open(target_name, "w").write(code)
