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
import http
import json
import logging
import mimetypes
from quart import Blueprint, Response # Temp import
# from quart import request, Blueprint, Response
import APIs.CentralController.JsonSchemas as schemas
from view_decorators import validate_auth_key, validate_json_body
from configuration import Configuration

ENDPOINT_ROOT: str = "/service/"

def create_blueprint(logger: logging.Logger) -> Blueprint:
    """
    Create a Flask Blueprint for the service API.

    Args:
        logger (logging.Logger): The logger instance to be used by the View.

    Returns:
        Blueprint: The created Flask Blueprint.
    """
    view = View(logger)

    blueprint: Blueprint = Blueprint("service_api", __name__)

    logger.info(f"> Adding endpoint | {ENDPOINT_ROOT}health_status")
    @blueprint.route(f"{ENDPOINT_ROOT}health_status", methods=["GET"])
    async def health_status():
        """
        Health status endpoint.

        Returns:
            Response: The response from the view's health_status method.
        """
        return await view.health_status()

    logger.info(f"> Adding endpoint | {ENDPOINT_ROOT}retrieve_console_logs")
    @blueprint.route(f"{ENDPOINT_ROOT}retrieve_console_logs", methods=["POST"])
    async def retrieve_console_logs():
        """
        'Retrieve console logs' endpoint.

        Returns:
            Response: The response from the view's retrieve_console_logs
            method.
        """
        return await view.retrieve_console_logs()

    return blueprint

class View:
    """ Service API view container class. """
    __slots__ = ["_logger"]
    # pylint: disable=too-few-public-methods

    def __init__(self, logger : logging.Logger):
        self._logger = logger.getChild(__name__)

        mimetypes.init()

    async def health_status(self):
        """
        Asynchronous method to return the health status of the service.

        Returns:
            Response: A Flask response object with a JSON payload indicating the health status,
                      HTTP status code, and content type.
        """

        content_type: str = mimetypes.types_map['.json']
        request_status: http.HTTPStatus = http.HTTPStatus.OK
        return_json = {
            "health": "normal"
        }

        return Response(json.dumps(return_json), status=request_status,
                        content_type=content_type)

    @validate_json_body(schemas.RetrieveConsoleLogs.Schema)
    @validate_auth_key("authentication_key", Configuration())
    async def retrieve_console_logs(self):
        """
        Asynchronous endpoint to retrieve console logs.

        This endpoint validates the JSON body against the RetrieveConsoleLogs
        schema and checks the authentication key before processing the request.
        Currently, it returns an empty list of log events.

        Returns:
            Response: A Flask response object with the log events in JSON
            format, HTTP status code, and content type.
        """

        # For the moment, this API endpoint returns an empty list.
        # Uncomment and use the following lines to process the request body and retrieve log events.
        # body = await request.get_json()
        # start = body[schemas.RetrieveConsoleLogs.BodyElement.StartTimestamp]
        # log_events = self._log_store.get_log_events(start)

        log_events = {}  # Placeholder for log events

        content_type: str = mimetypes.types_map['.json']
        return Response(json.dumps(log_events), status=http.HTTPStatus.OK,
                        content_type=content_type)
