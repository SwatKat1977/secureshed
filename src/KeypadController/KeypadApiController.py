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
import APIs.Keypad.JsonSchemas as schemas
from common.APIClient.HTTPStatusCode import HTTPStatusCode
from common.APIClient.MIMEType import MIMEType
from common.Logger import Logger, LogType
from KeypadStateObject import KeypadStateObject


## Implementation of thread that handles API calls to the keypad API.
class KeypadApiController(resource.Resource):
    ## __slots__ allow us to explicitly declare data members.
    __slots__ = ['__config', '__stateObject']

    isLeaf = True


    ## KeypadAPIThread class constructor, passing in the network port that the
    #  API will listen to.
    #  @param self The object pointer.
    #  @param config Configuration items.
    #  @param stateObject Instance of the state object.
    def __init__(self, config, stateObject, logStore):
        super().__init__()

        ## Instance of the current configuration.
        self.__config = config

        ## Instance of the keypad state object.
        self.__stateObject = stateObject
        
        self._logStore = logStore


    ## Render a GET HTTP method type.
    #  Note: Disabled pylint warning about name as inherited method.
    #  @param self The object pointer.
    #  @param requestInst GET request to process.
    def render_POST(self, requestInst):
        # pylint: disable=C0103

        requestUri = str(requestInst.path, 'utf-8').lstrip('/')

        if requestUri == 'receiveCentralControllerPing':
            return self.__ReceiveCentralControllerPing(requestInst)

        if requestUri == 'receiveKeypadLock':
            return self.__ReceiveKeypadLock(requestInst)

        if requestUri == 'retrieveConsoleLogs':
            return self._RetrieveConsoleLogs(requestInst)

        requestInst.setResponseCode(HTTPStatusCode.NotFound)
        return b''


    ## Function to handle processing of a 'receiveCentralControllerPing' route.
    #  @param self The object pointer.
    #  @param requestInst Request to be processed.
    def __ReceiveCentralControllerPing(self, requestInst):
        # Verify that an authorisation key exists in the request header, if not
        # then return a 401 (Unauthenticated) status with a human-readable
        # reason.
        if requestInst.getHeader(schemas.AUTH_KEY) is None:
            requestInst.setResponseCode(HTTPStatusCode.Unauthenticated)
            requestInst.setHeader('Content-Type', MIMEType.Text)
            return b'Authorisation key is missing'

        authorisationKey = requestInst.getHeader(schemas.AUTH_KEY)
        expectedKey = self.__config.keypadController.authKey

        # Verify that authorisation key passed in is matches what is in the
        # configuration file. If the key isn't valid then return a 403
        # (forbidden) status with a human-readable reason.
        if authorisationKey != expectedKey:
            requestInst.setResponseCode(HTTPStatusCode.Forbidden)
            requestInst.setHeader('Content-Type', MIMEType.Text)
            return b'Authorisation key is invalid'

        # We should only change the state if the current state is
        # 'CommunicationsLost', changing otherwise is unsafe and may result in
        # unexpected behaviour.  Since we don't need to report this we will
        # return an OK.
        currentPanel, _ = self.__stateObject.currentPanel
        if currentPanel == KeypadStateObject.PanelType.CommunicationsLost:
            newPanel = (KeypadStateObject.PanelType.Keypad, {})
            self.__stateObject.newPanel = newPanel

        Logger.Instance().Log(LogType.Info,
                              "Received an 'alive ping' from central controller")
        requestInst.setResponseCode(HTTPStatusCode.OK)
        requestInst.setHeader('Content-Type', MIMEType.Text)
        return b'OK'


    ## Function to handle processing of a 'receiveKeypadLock' route.
    #  @param self The object pointer.
    #  @param requestInst Request to be processed.
    def __ReceiveKeypadLock(self, requestInst):

        response = self.__ValidateAuthKey(requestInst)
        if response is not None:
            return response

        # Check for that if a message body exists and if so, is it in a json
        # MIME type, if not report a 400 error status with a human-readable.
        contentType = requestInst.getHeader(b'content-type')
        if contentType is None or contentType != str.encode(MIMEType.JSON):
            requestInst.setResponseCode(HTTPStatusCode.BadRequest)
            requestInst.setHeader('Content-Type', MIMEType.Text)
            return b'Message body not type JSON'

        try:
            rawBody = requestInst.content.read()
            body = json.loads(rawBody)

        except json.decoder.JSONDecodeError:
            requestInst.setResponseCode(HTTPStatusCode.BadRequest)
            requestInst.setHeader('Content-Type', MIMEType.Text)
            return b'Message body not valid JSON'

        try:
            jsonschema.validate(instance=body,
                                schema=schemas.KeypadLockRequest.Schema)

        except jsonschema.exceptions.ValidationError as ex:
            errrMsg = "ReceiveKeypadLockReq message failed validation, " +\
                      f"reason: {ex}"
            Logger.Instance().Log(LogType.Error, errrMsg)
            requestInst.setResponseCode(HTTPStatusCode.BadRequest)
            requestInst.setHeader('Content-Type', MIMEType.Text)
            return str.encode(errrMsg)

        lockTime = body[schemas.KeypadLockRequest.BodyElement.LockTime]
        newPanel = (KeypadStateObject.PanelType.KeypadIsLocked, lockTime)
        self.__stateObject.newPanel = newPanel

        Logger.Instance().Log(LogType.Info,
                              "Received an 'lock keypad' from central controller")
        requestInst.setResponseCode(HTTPStatusCode.OK)
        requestInst.setHeader('Content-Type', MIMEType.Text)
        return b'OK'


    def _RetrieveConsoleLogs(self, requestInst):
        # Validate the request to ensure that the auth key is firstly present,
        # then if it's valid.  None is returned if successful.
        response = self.__ValidateAuthKey(requestInst)
        if response is not None:
            return response

       # Check for that if a message body exists and if so, is it in a json
        # MIME type, if not report a 400 error status with a human-readable.
        contentType = requestInst.getHeader(b'content-type')
        if contentType is None or contentType != str.encode(MIMEType.JSON):
            requestInst.setResponseCode(HTTPStatusCode.BadRequest)
            requestInst.setHeader('Content-Type', MIMEType.Text)
            return b'Message body not type JSON'

        try:
            rawBody = requestInst.content.read()
            body = json.loads(rawBody)

        except json.decoder.JSONDecodeError:
            requestInst.setResponseCode(HTTPStatusCode.BadRequest)
            requestInst.setHeader('Content-Type', MIMEType.Text)
            return b'Message body not valid JSON'

        try:
            jsonschema.validate(instance=body,
                                schema=schemas.RetrieveConsoleLogs.Schema)

        except jsonschema.exceptions.ValidationError as ex:
            errrMsg = "ReceiveKeypadLockReq message failed validation, " +\
                      f"reason: {ex}"
            Logger.Instance().Log(LogType.Error, errrMsg)
            requestInst.setResponseCode(HTTPStatusCode.BadRequest)
            requestInst.setHeader('Content-Type', MIMEType.Text)
            return str.encode(errrMsg)

        start = body[schemas.RetrieveConsoleLogs.BodyElement.StartTimestamp]
        logEvents = self._logStore.GetLogEvents(start)

        requestInst.setResponseCode(HTTPStatusCode.OK)
        requestInst.setHeader('Content-Type', MIMEType.JSON)
        return str.encode(json.dumps(logEvents))


    ## Validate the authentication key for a request.
    #  @param self The object pointer.
    #  @param requestInst Request to verify auth key on.
    #  @returns On success None is returned, otherwise a binary string is
    #  returned on failed.
    def __ValidateAuthKey(self, requestInst):
        # Verify that an authorisation key exists in the request header, if not
        # then return a 401 (Unauthenticated) status with a human-readable
        # reason.
        if requestInst.getHeader(schemas.AUTH_KEY) is None:
            requestInst.setResponseCode(HTTPStatusCode.Unauthenticated)
            requestInst.setHeader('Content-Type', MIMEType.Text)
            return b'Authorisation key is missing'

        authorisationKey = requestInst.getHeader(schemas.AUTH_KEY)
        expectedKey = self.__config.keypadController.authKey

        # Verify that authorisation key passed in is matches what is in the
        # configuration file. If the key isn't valid then return a 403
        # (forbidden) status with a human-readable reason.
        if authorisationKey != expectedKey:
            requestInst.setResponseCode(HTTPStatusCode.Forbidden)
            requestInst.setHeader('Content-Type', MIMEType.Text)
            return b'Authorisation key is invalid'

        # Return None if auth key was successful.
        return None
