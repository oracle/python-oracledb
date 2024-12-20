# -----------------------------------------------------------------------------
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
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# config_provider.py
#
# Contains the built-in config providers.
# -----------------------------------------------------------------------------

import base64
import json
import os
import urllib.parse
import warnings

from . import errors
from .utils import register_password_type, register_protocol


def config_provider_file_hook(protocol, protocol_arg, connect_params):
    """
    Hook for "config-file://". The protocol_arg is expected to be the name of a
    file containing one or more configurations. An optional "key" parameter is
    allowed which will choose a configuration from a set of configurations
    stored in the file.
    """
    pos = protocol_arg.find("?")
    if pos < 0:
        file_name = protocol_arg
        key = None
    else:
        file_name = protocol_arg[:pos]
        args = urllib.parse.parse_qs(protocol_arg[pos + 1 :])
        key = args.get("key")
        if key is not None:
            key = key[0]
    if not os.path.isabs(file_name):
        if connect_params.config_dir is None:
            errors._raise_err(errors.ERR_NO_CONFIG_DIR)
        file_name = os.path.join(connect_params.config_dir, file_name)
    config = json.load(open(file_name))
    if key is not None:
        config = config[key]
    connect_params.set_from_config(config)


register_protocol("config-file", config_provider_file_hook)


def password_type_base64_hook(args):
    """
    Hook for password type "base64". The key "value" in the supplied args is
    expected to be a base64-encoded string.
    """
    warnings.warn("base64 encoded passwords are insecure")
    return base64.b64decode(args["value"].encode()).decode()


register_password_type("base64", password_type_base64_hook)
