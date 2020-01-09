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
import json
from flask import request
import APIs.Keypad.JsonSchemas as schemas
import centralController.Events as Evts
from common.APIClient.HTTPStatusCode import HTTPStatusCode
from common.APIClient.MIMEType import MIMEType
from common.Event import Event


## Implementation of thread that handles API calls to the keypad API.
class KeypadApiController:

    __slots__ = ['__config', '__db', '__endpoint', '__eventMgr', '__logger']

    ## KeypadAPIThread class constructor, passing in the network port that the
    #  API will listen to.
    #  @param self The object pointer.
    #  @param logger Logger instance.
    #  @param eventMgr Event management class instance.
    #  @param controllerDb Central controller internal database.
    #  @param config Configuration items.
    #  @param endpoint REST api endpoint instance.
    def __init__(self, logger, eventMgr, controllerDb, config, endpoint):
        self.__config = config
        self.__db = controllerDb
        self.__endpoint = endpoint
        self.__logger = logger
        self.__eventMgr = eventMgr

        # Add route : /receiveKeyCode
        self.__endpoint.add_url_rule('/receiveKeyCode', methods=['POST'],
                                     view_func=self.__ReceiveKeyCode)


    ## API route : receiveKeyCode
    #  Recieve a key code from the keypad.  This is for unlocking/disabling the
    #  alarm system.
    #  Return codes:
    #  * 200 (OK) - code accepted, rejected or refused.
    #  * 400 (Bad Request) - Missing or invalid json body or validation failed.
    #  * 401 (Unauthenticated) - Missing or invalid authentication key.
    def __ReceiveKeyCode(self):

        # Check for that the message body ia of type application/json and that
        # there is one, if not report a 400 error status with a human-readable.
        body = request.get_json()
        if not body:
            errMsg = 'Missing/invalid json body'
            response = self.__endpoint.response_class(
                response=errMsg, status=HTTPStatusCode.BadRequest,
                mimetype=MIMEType.Text)
            return response

        # Verify that an authorisation key exists in the requet header, if not
        # then return a 401 error with a human-readable reasoning.
        if schemas.receiveKeyCodeHeader.AuthKey not in request.headers:
            errMsg = 'Authorisation key is missing'
            response = self.__endpoint.response_class(
                response=errMsg, status=HTTPStatusCode.Unauthenticated,
                mimetype=MIMEType.Text)
            return response

        authorisationKey = request.headers[schemas.receiveKeyCodeHeader.AuthKey]

        # As the authorisation key functionality isn't currently implemented I
        # have hard-coded as 'authKey'.  If the key isn't valid then the error
        # code of 401 (Unauthenticated) is returned.
        if authorisationKey != 'authKey':
            errMsg = 'Authorisation key is invalid'
            response = self.__endpoint.response_class(
                response=errMsg, status=HTTPStatusCode.Forbidden,
                mimetype=MIMEType.Text)
            return response

        evt = Event(Evts.EvtType.KeypadKeyCodeEntered, body)
        self.__eventMgr.QueueEvent(evt)

        return self.__endpoint.response_class(response='Ok',
                                              status=HTTPStatusCode.OK,
                                              mimetype=MIMEType.Text)


    ## Generate a receive key code response message.
    #  @param self The object pointer.
    #  @param returnCode The return code for the response.
    #  @param actions List of actions to do with the response.
    #  @return Returns a JSON string with return code and actions.
    def __GenerateReceiveKeyCodeResponse(self, returnCode, actions):
        responseJson = \
        {
            schemas.receiveKeyCodeResponse.ReturnCode : returnCode,
            schemas.receiveKeyCodeResponse.Actions : actions
        }
        return json.dumps(responseJson)
