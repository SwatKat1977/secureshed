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
import jsonschema
from quart import Blueprint, request, Response
import APIs.CentralController.JsonSchemas as schemas
from event import Event
from event_manager import EventManager
import events
from view_decorators import validate_auth_key, validate_json_body
from configuration import Configuration

ENDPOINT_ROOT: str = "/keypad/"

def create_blueprint(logger: logging.Logger,
                     event_manager: EventManager) -> Blueprint:
    """
    Create a Flask Blueprint for the keypad API.

    Args:
        logger (logging.Logger): The logger instance to be used by the View.
        event_manager (EventManager): Event manager instance used by the view.

    Returns:
        Blueprint: The created Flask Blueprint.
    """
    view = View(logger, event_manager)

    blueprint: Blueprint = Blueprint("keypad_api", __name__)

    logger.info(f"> Adding endpoint | {ENDPOINT_ROOT}receive_key_code")
    @blueprint.route(f"{ENDPOINT_ROOT}receive_key_code", methods=["POST"])
    async def receive_key_code():
        """
        'Receive key code' endpoint.

        Returns:
            Response: The response from the view's receive_key_code method.
        """
        return await view.receive_key_code()

    logger.info(f"> Adding endpoint | {ENDPOINT_ROOT}please_respond_to_keypad")
    @blueprint.route(f"{ENDPOINT_ROOT}please_respond_to_keypad", methods=["POST"])
    async def please_respond_to_keypad():
        """
        'Please respond to keypad' endpoint.

        Returns:
            Response: The response from the view's please_respond_to_keypad
            method.
        """
        return await view.please_respond_to_keypad()

    return blueprint

class View:
    """ Service API view container class. """
    __slots__ = ["_event_manager", "_logger"]
    # pylint: disable=too-few-public-methods

    def __init__(self, logger: logging.Logger, event_manager: EventManager):
        self._logger: logging.Logger = logger.getChild(__name__)
        self._event_manager: EventManager = event_manager

        mimetypes.init()

    @validate_auth_key("authentication_key", Configuration())
    @validate_json_body(schemas.ReceiveKeyCode.Schema)
    async def receive_key_code(self):
        """
        Handle receiving a key code from a request.

        This method performs several checks and validations:
        1. Ensures the request body is of type application/json.
        2. Validates the presence and correctness of the authentication key.
        3. Validates the request body against the expected JSON schema.
        4. Queues an event if all validations pass.

        Returns:
            Response: Flask response object with appropriate status and message.
        """

        evt = Event(events.EvtType.KeypadKeyCodeEntered, await request.get_json())
        self._event_manager.QueueEvent(evt)

        content_type: str = mimetypes.types_map[".txt"]
        response_txt: str = "Ok"
        return Response(response_txt, status=http.HTTPStatus.OK,
                        content_type=content_type)

    @validate_auth_key("authentication_key", Configuration())
    @validate_json_body(schemas.ReceiveKeyCode.Schema)
    async def please_respond_to_keypad(self):

        send_alive_ping_evt = Event(events.EvtType.KeypadApiSendAlivePing)
        self._event_manager.QueueEvent(send_alive_ping_evt)

        content_type: str = mimetypes.types_map[".txt"]
        response_txt: str = "Ok"
        return Response(response_txt, status=http.HTTPStatus.OK,
                        content_type=content_type)
