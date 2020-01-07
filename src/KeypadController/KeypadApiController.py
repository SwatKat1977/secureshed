'''
Copyright 2019 Secure Shed Project Dev Team

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
from flask import request
import jsonschema
import APIs.Keypad.JsonSchemas as schemas
from common.APIClient.HTTPStatusCode import HTTPStatusCode
from common.APIClient.MIMEType import MIMEType
from KeypadController.KeypadStateObject import KeypadStateObject


## Implementation of thread that handles API calls to the keypad API.
class KeypadApiController:

    __slots__ = ['__config', '__endpoint', '__logger', '__stateObject']


    ## KeypadAPIThread class constructor, passing in the network port that the
    #  API will listen to.
    #  @param self The object pointer.
    #  @param logger Logger instance.
    #  @param config Configuration items.
    #  @param endpoint REST api endpoint instance.
    def __init__(self, logger, config, endpoint, stateObject):
        self.__config = config
        self.__endpoint = endpoint
        self.__logger = logger
        self.__stateObject = stateObject

        # Add route : /receiveKeyCode
        self.__endpoint.add_url_rule('/receiveCentralControllerPing', methods=['POST'],
                                     view_func=self.__ReceiveCentralControllerPing)

        # Add route : /receiveKeyCode
        self.__endpoint.add_url_rule('/receiveKeypadLock', methods=['POST'],
                                     view_func=self.__ReceiveKeypadLock)


    #  @param self The object pointer.
    def __ReceiveCentralControllerPing(self):
        # We should only change the state if the current state is
        # 'CommunicationsLost', changing otherwise is unsafe and may result in
        # unexpected behaviour.
        currentPanel, _ = self.__stateObject.currentPanel
        if currentPanel != KeypadStateObject.PanelType.CommunicationsLost:
            errMsg = 'Keypad not in communications lost state'
            return self.__endpoint.response_class(response=errMsg,
                                                  status=HTTPStatusCode.BadRequest,
                                                  mimetype=MIMEType.Text)

        self.__stateObject.currentPanel = (KeypadStateObject.PanelType.Keypad, {})

        self.__logger.info("Received an 'alive ping' from central controller")
        return self.__endpoint.response_class(response='OK',
                                              status=HTTPStatusCode.OK,
                                              mimetype=MIMEType.Text)


    #  @param self The object pointer.
    def __ReceiveKeypadLock(self):

        # Check for that if a message body exists and if so, is it in a json
        # MIME type, if not report a 400 error status with a human-readable.
        body = request.get_json()
        if not body:
            errMsg = 'Missing/invalid json body'
            return self.__endpoint.response_class(response=errMsg,
                                                  status=HTTPStatusCode.BadRequest,
                                                  mimetype=MIMEType.Text)

        try:
            jsonschema.validate(instance=body,
                                schema=schemas.RECEIVEKEYPADLOCKSCHEMA)

        except jsonschema.exceptions.ValidationError as ex:
            lastErrorMsg = f"ReceiveKeypadLockReq message failed validation" +\
                           f"alidation, reason: {ex}"
            self.__logger.error(lastErrorMsg)
            return self.__endpoint.response_class(response=lastErrorMsg,
                                                  status=HTTPStatusCode.BadRequest,
                                                  mimetype=MIMEType.Text)

        lockTime = body['lockTime']
        newPanel = {KeypadStateObject.PanelType.KeypadIsLocked, lockTime}
        self.__stateObject.currentPanel = newPanel

        return self.__endpoint.response_class(response='OK',
                                              status=HTTPStatusCode.OK,
                                              mimetype=MIMEType.Text)
