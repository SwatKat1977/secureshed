"""
Copyright 2019-2024 Secure Shed Project Dev Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import functools
import http
import json
import jsonschema
from quart import request, Response

# Define 'validate_json_body' error messages
ERR_MSG_INVALID_BODY_TYPE: str = "Invalid body type, not JSON"
ERR_MSG_MISSING_INVALID_JSON_BODY: str = "Missing/invalid json body"
ERR_MSG_BODY_SCHEMA_MISMATCH: str = "Message body failed schema validation"

# Define 'validate_auth_key' error messages
ERR_MSG_AUTH_KEY_MISSING: str = "Authorisation key is missing"
ERR_MSG_AUTH_KEY_INVALID: str = "Authorisation key is invalid"

# Define content types
ERR_MSG_CONTENT_TYPE: str = 'text/plain'

def validate_json_body(json_schema : dict = None):
    """
    Decorator to validate the JSON body of a request.

    Args:
        json_schema (dict, optional): The JSON schema to validate against. Defaults to None.

    Returns:
        function: The decorated function with JSON body validation.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            """
            Wrapper function that performs the JSON body validation.

            Args:
                *args: Positional arguments passed to the wrapped function.
                **kwargs: Keyword arguments passed to the wrapped function.

            Returns:
                Response: A Flask response object indicating the validation result.
            """

            #body = await request.get_json()
            body = await request.body
            if body is None:
                return Response(ERR_MSG_MISSING_INVALID_JSON_BODY,
                                status=http.HTTPStatus.BAD_REQUEST,
                                content_type=ERR_MSG_CONTENT_TYPE)

            try:
                json_data = json.loads(body)

            except (TypeError, json.JSONDecodeError) as ex:
                print(ex)
                return Response(ERR_MSG_INVALID_BODY_TYPE,
                                status=http.HTTPStatus.BAD_REQUEST,
                                content_type=ERR_MSG_CONTENT_TYPE)

            # If there is a JSON schema then validate that the json body conforms
            # to the expected schema. If the body isn't valid then a 400 error
            # should be generated.
            if json_schema:
                try:
                    jsonschema.validate(instance=json_data,
                                        schema=json_schema)

                except jsonschema.exceptions.ValidationError:
                    return Response(ERR_MSG_BODY_SCHEMA_MISMATCH,
                                    status=http.HTTPStatus.BAD_REQUEST,
                                    content_type=ERR_MSG_CONTENT_TYPE)

            return await func(*args, **kwargs)

        return wrapper

    return decorator

def validate_auth_key(auth_key_key: str, configuration):
    """
    Decorator to validate the authorization key in the request header.

    Args:
        auth_key_key (str): The name of the authorization header key.
        auth_key_value (str): The expected value of the authorization key.

    Returns:
        function: The decorated function which includes authorization key validation.
    """

    def decorator(func):
        """
        Wrapper function to validate the authorization key.

        Returns:
            Response: HTTP response with 401 if the authorization key is missing,
                      403 if the authorization key is invalid, or
                      the result of the decorated function if the key is valid.
        """

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):

            # Verify that an authorisation key exists in the request header, if
            # not then return a 401 error with a human-readable reasoning.
            if auth_key_key not in request.headers:
                return Response(ERR_MSG_AUTH_KEY_MISSING,
                                status=http.HTTPStatus.UNAUTHORIZED,
                                content_type=ERR_MSG_CONTENT_TYPE)

            # Verify the authorisation key against what is specified in the
            # configuration file.  If the key isn't valid then the error
            # code of 403 (Forbidden) is returned.
            if configuration.general_authentication_key != request.headers[auth_key_key]:
                return Response(ERR_MSG_AUTH_KEY_INVALID,
                                status=http.HTTPStatus.FORBIDDEN,
                                content_type=ERR_MSG_CONTENT_TYPE)

            return await func(*args, **kwargs)

        return wrapper

    return decorator
