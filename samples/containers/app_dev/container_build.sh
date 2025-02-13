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
#   container_build.sh
#
# PURPOSE
#
#   Top level script to build a container image for Python application
#   developers.
#
# USAGE
#
#   ./container_build.sh
#

# Sourcing environment file to setup the build environment
source container_build.env

# Pulling base image Oracle Linux container image
$CONTAINER_TOOL pull ghcr.io/oracle/oraclelinux:$OPY_OS_VERSION

# Building Container image
$CONTAINER_TOOL build --tag pyorcldbdev \
  --build-arg OPY_PYTHON_VERSION \
  --build-arg OPY_PYTHON_VERSION_WITHOUTPERIOD \
  --build-arg OPY_USERNAME \
  --build-arg OPY_GROUPNAME \
  --build-arg OPY_IMAGE_RELEASE_DATE \
  --build-arg OPY_APACHE_SERVER_VERSION \
  --build-arg OPY_INSTANT_CLIENT_VERSION \
  --build-arg OPY_APACHE_LISTEN_PORT . --no-cache
