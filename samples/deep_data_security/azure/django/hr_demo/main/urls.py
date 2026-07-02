# -----------------------------------------------------------------------------
# Copyright (c) 2026, Oracle and/or its affiliates.
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
# urls.py
#
# URL routing configuration for the Django main app. Defines URL patterns for
# Azure AD authentication (login, callback, logout), the home page, HR data
# view with Deep Data Security, and the natural language chat interface.
# -----------------------------------------------------------------------------

from django.urls import path
from .views import (
    azure_login,
    azure_callback,
    azure_logout,
    chat_view,
    home_view,
    hr_view,
)

urlpatterns = [
    path("", home_view, name="start"),
    path("login/", azure_login, name="login"),
    path("logout/", azure_logout, name="logout"),
    path("auth/callback/", azure_callback, name="callback"),
    path("home/", home_view, name="home"),
    path("chat/", chat_view, name="chat"),
    path("hrapp/", hr_view, name="hrapp"),
]
