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
# Makefile to generate parameter files from templates
#------------------------------------------------------------------------------


SOURCE_DIR = ../src/oracledb
TEMPLATE_DIR = templates

all: $(SOURCE_DIR)/connect_params.py $(SOURCE_DIR)/pool_params.py \
		$(SOURCE_DIR)/connection.py $(SOURCE_DIR)/pool.py

$(SOURCE_DIR)/connection.py: fields.cfg $(TEMPLATE_DIR)/connection.py
	python build_from_template.py connection

$(SOURCE_DIR)/connect_params.py: fields.cfg $(TEMPLATE_DIR)/connect_params.py
	python build_from_template.py connect_params

$(SOURCE_DIR)/pool.py: fields.cfg $(TEMPLATE_DIR)/pool.py
	python build_from_template.py pool

$(SOURCE_DIR)/pool_params.py: fields.cfg $(TEMPLATE_DIR)/pool_params.py
	python build_from_template.py pool_params
