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
import jsonschema
from twisted.web import resource
from keypad_state_object import KeypadStateObject
import APIs.Keypad.JsonSchemas as schemas
from common.APIClient.HTTPStatusCode import HTTPStatusCode
from common.APIClient.MIMEType import MIMEType
from common.Logger import LogType


## Implementation of thread that handles API calls to the keypad API.
class KeypadApiController(resource.Resource):
    __slots__ = ['_config', '_state_object']

    isLeaf = True


    ## KeypadAPIThread class constructor, passing in the network port that the
    #  API will listen to.
    #  @param self The object pointer.
    #  @param config Configuration items.
    #  @param stateObject Instance of the state object.
    def __init__(self, config, stateObject, logStore, logger):
        super().__init__()

        self._config = config
        self._state_object = stateObject
        self._logger = logger
        self._log_store = logStore


    ## Render a POST HTTP method type.
    #  Note: Disabled pylint warning about name as inherited method.
    #  @param self The object pointer.
    #  @param requestInst GET request to process.
    def render_POST(self, requestInst):
        # pylint: disable=C0103

        requestUri = str(requestInst.path, 'utf-8').lstrip('/')

        if requestUri == 'receiveCentralControllerPing':
            return self._receive_central_controller_ping(requestInst)

        if requestUri == 'receiveKeypadLock':
            return self._receive_keypad_lock(requestInst)

        if requestUri == 'retrieveConsoleLogs':
            return self._retrieve_console_logs(requestInst)

        requestInst.setResponseCode(HTTPStatusCode.NotFound)
        return b''


    ## Render a GET HTTP method type.
    #  Note: Disabled pylint warning about name as inherited method.
    #  @param self The object pointer.
    #  @param requestInst GET request to process.
    def render_GET(self, request_inst):
        # pylint: disable=C0103

        request_uri = str(request_inst.path, 'utf-8').lstrip('/')

        if request_uri == '_healthStatus':
            return self._health_status(request_inst)

        request_inst.setResponseCode(HTTPStatusCode.NotFound)
        return b''


    ## Function to handle processing of a 'receiveCentralControllerPing' route.
    #  @param self The object pointer.
    #  @param requestInst Request to be processed.
    def _receive_central_controller_ping(self, request_inst):
        # Verify that an authorisation key exists in the request header, if not
        # then return a 401 (Unauthenticated) status with a human-readable
        # reason.
        if request_inst.getHeader(schemas.AUTH_KEY) is None:
            request_inst.setResponseCode(HTTPStatusCode.Unauthenticated)
            request_inst.setHeader('Content-Type', MIMEType.Text)
            return b'Authorisation key is missing'

        authorisation_key = request_inst.getHeader(schemas.AUTH_KEY)
        expected_key = self._config.keypadController.authKey

        # Verify that authorisation key passed in is matches what is in the
        # configuration file. If the key isn't valid then return a 403
        # (forbidden) status with a human-readable reason.
        if authorisation_key != expected_key:
            request_inst.setResponseCode(HTTPStatusCode.Forbidden)
            request_inst.setHeader('Content-Type', MIMEType.Text)
            return b'Authorisation key is invalid'

        # We should only change the state if the current state is
        # 'CommunicationsLost', changing otherwise is unsafe and may result in
        # unexpected behaviour.  Since we don't need to report this we will
        # return an OK.
        current_panel, _ = self._state_object.current_panel
        if current_panel == KeypadStateObject.PanelType.CommunicationsLost:
            new_panel = (KeypadStateObject.PanelType.Keypad, {})
            self._state_object.new_panel = new_panel

        self._logger.Log(LogType.Info,
                         "Received an 'alive ping' from central controller")
        request_inst.setResponseCode(HTTPStatusCode.OK)
        request_inst.setHeader('Content-Type', MIMEType.Text)
        return b'OK'


    ## Function to handle processing of a 'receiveKeypadLock' route.
    #  @param self The object pointer.
    #  @param requestInst Request to be processed.
    def _receive_keypad_lock(self, request_inst):

        response = self._validate_auth_key(request_inst)
        if response is not None:
            return response

        # Check for that if a message body exists and if so, is it in a json
        # MIME type, if not report a 400 error status with a human-readable.
        content_type = request_inst.getHeader(b'content-type')
        if content_type is None or content_type != str.encode(MIMEType.JSON):
            request_inst.setResponseCode(HTTPStatusCode.BadRequest)
            request_inst.setHeader('Content-Type', MIMEType.Text)
            return b'Message body not type JSON'

        try:
            raw_body = request_inst.content.read()
            body = json.loads(raw_body)

        except json.decoder.JSONDecodeError:
            request_inst.setResponseCode(HTTPStatusCode.BadRequest)
            request_inst.setHeader('Content-Type', MIMEType.Text)
            return b'Message body not valid JSON'

        try:
            jsonschema.validate(instance=body,
                                schema=schemas.KeypadLockRequest.Schema)

        except jsonschema.exceptions.ValidationError as ex:
            err_msg = "ReceiveKeypadLockReq message failed validation, " +\
                      f"reason: {ex}"
            self._logger.Log(LogType.Error, err_msg)
            request_inst.setResponseCode(HTTPStatusCode.BadRequest)
            request_inst.setHeader('Content-Type', MIMEType.Text)
            return str.encode(err_msg)

        lock_time = body[schemas.KeypadLockRequest.BodyElement.LockTime]
        new_panel = (KeypadStateObject.PanelType.KeypadIsLocked, lock_time)
        self._state_object.new_panel = new_panel

        self._logger.Log(LogType.Info,
                              "Received an 'lock keypad' from central controller")
        request_inst.setResponseCode(HTTPStatusCode.OK)
        request_inst.setHeader('Content-Type', MIMEType.Text)
        return b'OK'


    def _retrieve_console_logs(self, request_inst):
        # Validate the request to ensure that the auth key is firstly present,
        # then if it's valid.  None is returned if successful.
        response = self._validate_auth_key(request_inst)
        if response is not None:
            return response

       # Check for that if a message body exists and if so, is it in a json
        # MIME type, if not report a 400 error status with a human-readable.
        content_type = request_inst.getHeader(b'content-type')
        if content_type is None or content_type != str.encode(MIMEType.JSON):
            request_inst.setResponseCode(HTTPStatusCode.BadRequest)
            request_inst.setHeader('Content-Type', MIMEType.Text)
            return b'Message body not type JSON'

        try:
            raw_body = request_inst.content.read()
            body = json.loads(raw_body)

        except json.decoder.JSONDecodeError:
            request_inst.setResponseCode(HTTPStatusCode.BadRequest)
            request_inst.setHeader('Content-Type', MIMEType.Text)
            return b'Message body not valid JSON'

        try:
            jsonschema.validate(instance=body,
                                schema=schemas.RetrieveConsoleLogs.Schema)

        except jsonschema.exceptions.ValidationError as ex:
            err_msg = "ReceiveKeypadLockReq message failed validation, " +\
                      f"reason: {ex}"
            self._logger.Log(LogType.Error, err_msg)
            request_inst.setResponseCode(HTTPStatusCode.BadRequest)
            request_inst.setHeader('Content-Type', MIMEType.Text)
            return str.encode(err_msg)

        start = body[schemas.RetrieveConsoleLogs.BodyElement.StartTimestamp]
        log_events = self._log_store.GetLogEvents(start)

        request_inst.setResponseCode(HTTPStatusCode.OK)
        request_inst.setHeader('Content-Type', MIMEType.JSON)
        return str.encode(json.dumps(log_events))


    #  @param self The object pointer.
    def _health_status(self, request_inst):
        # pylint: disable=no-self-use

        return_json = {
            "health": "normal"
        }
        request_inst.setResponseCode(HTTPStatusCode.OK)
        request_inst.setHeader('Content-Type', MIMEType.JSON)
        return json.dumps(return_json).encode("UTF-8")


    ## Validate the authentication key for a request.
    #  @param self The object pointer.
    #  @param requestInst Request to verify auth key on.
    #  @returns On success None is returned, otherwise a binary string is
    #  returned on failed.
    def _validate_auth_key(self, request_inst):
        # Verify that an authorisation key exists in the request header, if not
        # then return a 401 (Unauthenticated) status with a human-readable
        # reason.
        if request_inst.getHeader(schemas.AUTH_KEY) is None:
            request_inst.setResponseCode(HTTPStatusCode.Unauthenticated)
            request_inst.setHeader('Content-Type', MIMEType.Text)
            return b'Authorisation key is missing'

        authorisation_key = request_inst.getHeader(schemas.AUTH_KEY)
        expected_key = self._config.keypadController.authKey

        # Verify that authorisation key passed in is matches what is in the
        # configuration file. If the key isn't valid then return a 403
        # (forbidden) status with a human-readable reason.
        if authorisation_key != expected_key:
            request_inst.setResponseCode(HTTPStatusCode.Forbidden)
            request_inst.setHeader('Content-Type', MIMEType.Text)
            return b'Authorisation key is invalid'

        # Return None if auth key was successful.
        return None
