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
import centralController.Events as Evts
from common.APIClient.HTTPStatusCode import HTTPStatusCode
from common.APIClient.MIMEType import MIMEType
from common.Event import Event
from common.Logger import Logger, LogType


## Implementation of thread that handles API calls to the keypad API.
class ApiController:
    # pylint: disable=too-few-public-methods

    __slots__ = ['__config', '__db', '__endpoint', '__eventMgr', '_logStore']

    ## KeypadAPIThread class constructor, passing in the network port that the
    #  API will listen to.
    #  @param self The object pointer.
    #  @param eventMgr Event management class instance.
    #  @param controllerDb Central controller internal database.
    #  @param config Configuration items.
    #  @param endpoint REST api endpoint instance.
    #  @param logStore Instance of log store.
    def __init__(self, eventMgr, controllerDb, config, endpoint, logStore):
        self.__config = config
        self.__db = controllerDb
        self.__endpoint = endpoint
        self.__eventMgr = eventMgr
        self._logStore = logStore

        # Add route : /receiveKeyCode
        self.__endpoint.add_url_rule('/receiveKeyCode', methods=['POST'],
                                     view_func=self.__ReceiveKeyCode)

        # Add route : /receiveKeyCode
        self.__endpoint.add_url_rule('/pleaseRespondToKeypad', methods=['POST'],
                                     view_func=self.__PleaseRespondToKeypad)

        # Add route : /retrieveConsoleLogs
        self.__endpoint.add_url_rule('/retrieveConsoleLogs', methods=['POST'],
                                     view_func=self._RetrieveConsoleLogs)


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

        # Validate the request to ensure that the auth key is firstly present,
        # then if it's valid.  None is returned if successful.
        validateReturn = self.__ValidateAuthKey()
        if validateReturn is not None:
            return validateReturn

        # Validate that the json body conforms to the expected schema.
        # If the message isn't valid then a 400 error should be generated.
        try:
            jsonschema.validate(instance=body,
                                schema=schemas.ReceiveKeyCode.Schema)

        except jsonschema.exceptions.ValidationError:
            errMsg = 'Message body validation failed.'
            return self.__endpoint.response_class(
                response=errMsg, status=HTTPStatusCode.BadRequest,
                mimetype='text')

        evt = Event(Evts.EvtType.KeypadKeyCodeEntered, body)
        self.__eventMgr.QueueEvent(evt)

        return self.__endpoint.response_class(
            response='Ok', status=HTTPStatusCode.OK,
            mimetype=MIMEType.Text)


    #  @param self The object pointer.
    def __PleaseRespondToKeypad(self):
        # Validate the request to ensure that the auth key is firstly present,
        # then if it's valid.  None is returned if successful.
        validateReturn = self.__ValidateAuthKey()
        if validateReturn is not None:
            return validateReturn

        sendAlivePingEvt = Event(Evts.EvtType.KeypadApiSendAlivePing)
        self.__eventMgr.QueueEvent(sendAlivePingEvt)

        return self.__endpoint.response_class(
            response='Ok', status=HTTPStatusCode.OK,
            mimetype=MIMEType.Text)


    def _RetrieveConsoleLogs(self):
        # Validate the request to ensure that the auth key is firstly present,
        # then if it's valid.  None is returned if successful.
        validateReturn = self.__ValidateAuthKey()
        if validateReturn is not None:
            return validateReturn

        # Check for that the message body ia of type application/json and that
        # there is one, if not report a 400 error status with a human-readable.
        body = request.get_json()
        if not body:
            errMsg = 'Missing/invalid json body'
            response = self.__endpoint.response_class(
                response=errMsg, status=HTTPStatusCode.BadRequest,
                mimetype=MIMEType.Text)
            return response

        # Validate that the json body conforms to the expected schema.
        # If the message isn't valid then a 400 error should be generated.
        try:
            jsonschema.validate(instance=body,
                                schema=schemas.RetrieveConsoleLogs.Schema)

        except jsonschema.exceptions.ValidationError:
            errMsg = 'Message body validation failed.'
            return self.__endpoint.response_class(
                response=errMsg, status=HTTPStatusCode.BadRequest,
                mimetype='text')

        start = body[schemas.RetrieveConsoleLogs.BodyElement.StartTimestamp]
        logEvents = self._logStore.GetLogEvents(start)

        return self.__endpoint.response_class(
            response=json.dumps(logEvents), status=HTTPStatusCode.OK,
            mimetype=MIMEType.JSON)


    #  @param self The object pointer.
    def __ValidateAuthKey(self):
        # Verify that an authorisation key exists in the requet header, if not
        # then return a 401 error with a human-readable reasoning.
        if schemas.AUTH_KEY not in request.headers:
            Logger.Instance().Log(LogType.Critical,
                                  'Missing controller auth key from keypad')
            errMsg = 'Authorisation key is missing'
            return self.__endpoint.response_class(
                response=errMsg, status=HTTPStatusCode.Unauthenticated,
                mimetype=MIMEType.Text)

        authorisationKey = request.headers[schemas.AUTH_KEY]

        # Verify the authorisation key against what is specified in the
        # configuration file.  If the key isn't valid then the error
        # code of 403 (Forbidden) is returned.
        if authorisationKey != self.__config.centralControllerApi.authKey:
            Logger.Instance().Log(LogType.Critical,
                                  'Invalid controller auth key from keypad')
            errMsg = 'Authorisation key is invalid'
            return self.__endpoint.response_class(
                response=errMsg, status=HTTPStatusCode.Forbidden,
                mimetype=MIMEType.Text)

        return None
