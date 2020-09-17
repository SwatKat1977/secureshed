'''
Copyright 2019-2020 Secure Shed Project Dev Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
import json
from flask import request
import jsonschema
import APIs.CentralController.JsonSchemas as schemas
import central_controller.events as Evts
from common.APIClient.HTTPStatusCode import HTTPStatusCode
from common.APIClient.MIMEType import MIMEType
from common.Event import Event
from common.Logger import LogType


## Implementation of thread that handles API calls to the keypad API.
class ApiController:
    # pylint: disable=too-few-public-methods

    __slots__ = ['_config', '_database', '_endpoint', '_event_mgr', '_logger',
                 '_log_store']

    ## KeypadAPIThread class constructor, passing in the network port that the
    #  API will listen to.
    #  @param self The object pointer.
    #  @param eventMgr Event management class instance.
    #  @param controllerDb Central controller internal database.
    #  @param config Configuration items.
    #  @param endpoint REST api endpoint instance.
    #  @param logStore Instance of log store.
    def __init__(self, eventMgr, controllerDb, config, endpoint, logStore,
                 logger):
        # pylint: disable=too-many-arguments

        self._config = config
        self._database = controllerDb
        self._endpoint = endpoint
        self._event_mgr = eventMgr
        self._logger = logger
        self._log_store = logStore

        # Add route : /receiveKeyCode
        self._endpoint.add_url_rule('/receiveKeyCode', methods=['POST'],
                                    view_func=self._receive_key_code)

        # Add route : /receiveKeyCode
        self._endpoint.add_url_rule('/pleaseRespondToKeypad', methods=['POST'],
                                    view_func=self._please_respond_to_keypad)

        # Add route : /retrieveConsoleLogs
        self._endpoint.add_url_rule('/retrieveConsoleLogs', methods=['POST'],
                                    view_func=self._retrieve_console_logs)

        # Add route : /retrieveConsoleLogs
        self._endpoint.add_url_rule('/_health_status', methods=['GET'],
                                    view_func=self._health_status)


    ## API route : receiveKeyCode
    #  Recieve a key code from the keypad.  This is for unlocking/disabling the
    #  alarm system.
    #  Return codes:
    #  * 200 (OK) - code accepted, rejected or refused.
    #  * 400 (Bad Request) - Missing or invalid json body or validation failed.
    #  * 401 (Unauthenticated) - Missing or invalid authentication key.
    def _receive_key_code(self):

        # Check for that the message body ia of type application/json and that
        # there is one, if not report a 400 error status with a human-readable.
        body = request.get_json()
        if not body:
            err_msg = 'Missing/invalid json body'
            response = self._endpoint.response_class(
                response=err_msg, status=HTTPStatusCode.BadRequest,
                mimetype=MIMEType.Text)
            return response

        # Validate the request to ensure that the auth key is firstly present,
        # then if it's valid.  None is returned if successful.
        validate_return = self._validate_auth_key()
        if validate_return is not None:
            return validate_return

        # Validate that the json body conforms to the expected schema.
        # If the message isn't valid then a 400 error should be generated.
        try:
            jsonschema.validate(instance=body,
                                schema=schemas.ReceiveKeyCode.Schema)

        except jsonschema.exceptions.ValidationError:
            err_msg = 'Message body validation failed.'
            return self._endpoint.response_class(
                response=err_msg, status=HTTPStatusCode.BadRequest,
                mimetype='text')

        evt = Event(Evts.EvtType.KeypadKeyCodeEntered, body)
        self._event_mgr.QueueEvent(evt)

        return self._endpoint.response_class(
            response='Ok', status=HTTPStatusCode.OK,
            mimetype=MIMEType.Text)


    #  @param self The object pointer.
    def _please_respond_to_keypad(self):
        # Validate the request to ensure that the auth key is firstly present,
        # then if it's valid.  None is returned if successful.
        validate_return = self._validate_auth_key()
        if validate_return is not None:
            return validate_return

        send_alive_ping_evt = Event(Evts.EvtType.KeypadApiSendAlivePing)
        self._event_mgr.QueueEvent(send_alive_ping_evt)

        return self._endpoint.response_class(
            response='Ok', status=HTTPStatusCode.OK,
            mimetype=MIMEType.Text)


    def _retrieve_console_logs(self):
        # Validate the request to ensure that the auth key is firstly present,
        # then if it's valid.  None is returned if successful.
        validate_return = self._validate_auth_key()
        if validate_return is not None:
            return validate_return

        # Check for that the message body ia of type application/json and that
        # there is one, if not report a 400 error status with a human-readable.
        body = request.get_json()
        if not body:
            err_msg = 'Missing/invalid json body'
            response = self._endpoint.response_class(
                response=err_msg, status=HTTPStatusCode.BadRequest,
                mimetype=MIMEType.Text)
            return response

        # Validate that the json body conforms to the expected schema.
        # If the message isn't valid then a 400 error should be generated.
        try:
            jsonschema.validate(instance=body,
                                schema=schemas.RetrieveConsoleLogs.Schema)

        except jsonschema.exceptions.ValidationError:
            err_msg = 'Message body validation failed.'
            return self._endpoint.response_class(
                response=err_msg, status=HTTPStatusCode.BadRequest,
                mimetype='text')

        start = body[schemas.RetrieveConsoleLogs.BodyElement.StartTimestamp]
        log_events = self._log_store.get_log_events(start)

        return self._endpoint.response_class(
            response=json.dumps(log_events), status=HTTPStatusCode.OK,
            mimetype=MIMEType.JSON)



    def _health_status(self):
        # Validate the request to ensure that the auth key is firstly present,
        # then if it's valid.  None is returned if successful.
        validate_return = self._validate_auth_key()
        if validate_return is not None:
            return validate_return

        return_json = {
            "health": "normal"
        }

        return self._endpoint.response_class(
            response=json.dumps(return_json), status=HTTPStatusCode.OK,
            mimetype=MIMEType.JSON)
    #  @param self The object pointer.
    def _validate_auth_key(self):
        # Verify that an authorisation key exists in the requet header, if not
        # then return a 401 error with a human-readable reasoning.
        if schemas.AUTH_KEY not in request.headers:
            self._logger.Log(LogType.Critical,
                             'Missing controller auth key from keypad')
            err_msg = 'Authorisation key is missing'
            return self._endpoint.response_class(
                response=err_msg, status=HTTPStatusCode.Unauthenticated,
                mimetype=MIMEType.Text)

        authorisation_key = request.headers[schemas.AUTH_KEY]

        # Verify the authorisation key against what is specified in the
        # configuration file.  If the key isn't valid then the error
        # code of 403 (Forbidden) is returned.
        if authorisation_key != self._config.central_controller_api.authKey:
            self._logger.Log(LogType.Critical,
                             'Invalid controller auth key from keypad')
            err_msg = 'Authorisation key is invalid'
            return self._endpoint.response_class(
                response=err_msg, status=HTTPStatusCode.Forbidden,
                mimetype=MIMEType.Text)

        return None
