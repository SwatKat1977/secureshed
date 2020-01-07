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


    def __ReceiveCentralControllerPing(self):
        pass
