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
# views.py
#
# Django views for the HR demo with chat application demonstrating Deep Data
# Security with Microsoft Entra ID authentication and OCI Generative AI.
# Handles Azure AD login, HR data queries with row-level security, and
# natural language to SQL chat interface using OCI Generative AI.
#
# For setup and run instructions, see README.md in this directory.
# -----------------------------------------------------------------------------

import json

import msal
import oci
from django.conf import settings
from django.db import connection
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from oci.exceptions import ServiceError
from oci.generative_ai_inference import GenerativeAiInferenceClient

# System prompt used to instruct the LLM to generate read-only Oracle SQL.
SYSTEM_PROMPT = """
    You are an expert Oracle SQL generator.
    Rules:
    -If the input is empty, blank, only whitespace, or does not contain a
     real question/request, reply exactly: please ask a query
    -If the input is a normal greeting like hi, hello, hey, reply with a short
     greeting
    - Generate ONLY valid SQL
    - SELECT statements only
    - NO INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE
    - Return SQL only, no explanation, no formatting, no markdown
    - If got an unpredefined schema generate the sql based on input

    Spelling tolerance rules (MANDATORY):
    - Treat minor spelling mistakes, pluralization, or casing differences as
      equivalent
    - Examples for hr.employees: employee, employees, employe, employes,
      emplyee, emplyees
    - Never use the misspelled word as a table name in SQL

    Schema:
    - hr.employees (
    EMPLOYEE_ID, FIRST_NAME, LAST_NAME, USER_NAME, PHONE_NUMBER,
    SSN, SALARY, MANAGER_ID, DEPARTMENT_ID
    )

    Table name normalization rules (MANDATORY):
    - Any reference to employees, employee, emp MUST use hr.employees
    - Always use schema-qualified table names exactly as defined above
    - Never use unqualified or inferred table names
    """.strip()


def _chat_model(model_id, user_input):
    """
    Call OCI Generative AI chat endpoint and return model text output.
    """
    compartment_id = settings.OCI_COMPARTMENT_ID
    client = _get_oci_chat_client()
    prompt = user_input
    chat_details = {
        "compartmentId": compartment_id,
        "servingMode": {
            "servingType": "ON_DEMAND",
            "modelId": model_id,
        },
        "chatRequest": {
            "apiFormat": "GENERIC",
            "messages": [
                {
                    "role": "SYSTEM",
                    "content": [{"type": "TEXT", "text": SYSTEM_PROMPT}],
                },
                {
                    "role": "USER",
                    "content": [{"type": "TEXT", "text": prompt}],
                },
            ],
            "temperature": 0,
            "topP": 0.9,
            "maxTokens": 200,
            "isStream": False,
        },
    }

    # OCI Python SDK expects ChatDetails directly (not wrapped in
    # {"chatDetails": ...})
    response = client.chat(chat_details)
    if not response:
        raise RuntimeError("Null response from OCI")

    # For chat(), response.data is already a ChatResult object
    chat_response = response.data.chat_response
    output = None

    # GENERIC format
    if hasattr(chat_response, "choices") and chat_response.choices:
        first_choice = chat_response.choices[0]
        if hasattr(first_choice, "message") and hasattr(
            first_choice.message, "content"
        ):
            content = first_choice.message.content
            if isinstance(content, list) and content:
                first_part = content[0]
                output = getattr(first_part, "text", str(first_part))
            else:
                output = str(content)

    # Cohere format
    elif hasattr(chat_response, "text"):
        output = chat_response.text
    if output is None:
        output = str(chat_response)
    return output


def _display_error(exc):
    """
    Return a useful, escaped-by-template diagnostic for unexpected errors.
    """
    return f"{type(exc).__name__}: {exc}"


def _get_msal_app():
    """
    Create and return a configured MSAL confidential client.
    """
    return msal.ConfidentialClientApplication(
        settings.AZURE_AD["CLIENT_ID"],
        authority=settings.AZURE_AD["AUTHORITY"],
        client_credential=settings.AZURE_AD["CLIENT_SECRET"],
    )


def _get_oci_chat_client():
    """
    Create and return a configured OCI Generative AI inference client.
    """
    config = oci.config.from_file(settings.OCI_CONFIG_FILE, "DEFAULT")
    client = GenerativeAiInferenceClient(config)
    client.base_client.endpoint = settings.OCI_ENDPOINT
    return client


def _is_safe_sql(sql):
    """
    Basic guardrail to allow only SELECT SQL and block DML/DDL keywords.
    """
    return sql.strip().lower().startswith("select")


def _llm_to_sql(user_input):
    """
    Convert user prompt to SQL using the configured LLM model.
    """
    model_id = "xai.grok-3"
    return _chat_model(model_id, user_input)


def azure_login(request):
    """
    Start Azure AD login by redirecting to the authorization URL.
    """
    msal_app = _get_msal_app()
    auth_url = msal_app.get_authorization_request_url(
        scopes=[settings.AZURE_AD["SCOPE"]],
        redirect_uri=settings.AZURE_AD["REDIRECT_URI"],
    )
    return redirect(auth_url)


def azure_callback(request):
    """
    Handle Azure AD OAuth callback and store identity token in cookie.
    """
    code = request.GET.get("code")
    if not code:
        return HttpResponseBadRequest("Missing authorization code")
    msal_app = _get_msal_app()
    result = msal_app.acquire_token_by_authorization_code(
        code=code,
        scopes=[settings.AZURE_AD["SCOPE"]],
        redirect_uri=settings.AZURE_AD["REDIRECT_URI"],
    )
    if "access_token" in result:
        value = json.dumps(result["access_token"])
        response = redirect("/home/")
        response.set_cookie(
            "identity",
            value,
            httponly=True,
            secure=False,
            samesite="Lax",
            max_age=3600,
        )
        return response
    return HttpResponse(str(result), status=400)


def azure_logout(request):
    """
    Log out from Azure AD, clear local identity cookie, and flush session.
    """
    logout_url = (
        f"{settings.AZURE_AD['AUTHORITY']}/oauth2/v2.0/logout"
        f"?post_logout_redirect_uri=http://localhost:8000/home/"
    )
    response = redirect(logout_url)
    response.delete_cookie(
        "identity",
        path="/",
        samesite="Lax",
    )
    request.session.flush()
    return response


def home_view(request):
    """
    Render the application home page.
    """
    return render(request, "main/home.html")


def hr_view(request):
    """
    Query HR employee data and render it in the HR template.
    """
    response_rows = []

    try:
        with connection.cursor() as cursor:
            cursor.execute("select count(*) from hr.employees")
            (count,) = cursor.fetchone()
            cursor.execute("""
                select department_id, first_name, salary, ssn
                from hr.employees
                """)
            response_rows = cursor.fetchall()
        return render(
            request,
            "main/hr.html",
            {
                "count": count,
                "employees": response_rows,
            },
        )
    except Exception as e:
        return render(
            request,
            "main/no_access.html",
            {"error_message": _display_error(e)},
        )


def chat_view(request):
    """
    Accept natural language prompt, generate SQL, execute, and render results.
    """
    raw_sql = None
    rows = []
    columns = []
    error_message = None

    def render_chat():
        return render(
            request,
            "main/chat.html",
            {
                "sql": raw_sql,
                "rows": rows,
                "columns": columns,
                "error_message": error_message,
            },
        )

    if request.method == "POST":
        prompt = request.POST.get("prompt")

        # Convert prompt → SQL
        try:
            raw_sql = _llm_to_sql(prompt)
        except ServiceError as e:
            if getattr(e, "status", None) == 401:
                error_message = (
                    "Could not authenticate with OCI Generative AI (401). "
                    "Please verify OCI credentials/profile and try again."
                )
            else:
                error_message = (
                    "OCI Generative AI request failed. "
                    "Please try again shortly or contact support."
                )
            return render_chat()
        except Exception as e:
            error_message = _display_error(e)
            return render_chat()

        # Validate SQL (CRITICAL)
        if not _is_safe_sql(raw_sql):
            error_message = "Not valid sql only select is allowed"
            return render_chat()

        try:
            with connection.cursor() as cursor:
                cursor.execute(raw_sql)
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
        except Exception as e:
            error_message = _display_error(e)

    return render_chat()
