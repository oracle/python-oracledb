#!/bin/bash

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
#
# NAME
#
#   pyorcldb_generate_cert.sh
#
# PURPOSE
#
#   Sample generation of an SSL certificate and key for testing purposes
#
# USAGE
#   ./pyorcldb_generate_cert.sh
#
cd /opt/cert
openssl req -newkey rsa:4096 -x509 -sha512 -days 365 -nodes -out \
  certificate.pem -keyout privatekey.pem \
  -subj "/C=OC/ST=DEMO/L=DEMO/O=DEMO/CN=DEMO" 2>/dev/null
