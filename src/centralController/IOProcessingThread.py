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
import threading
from flask import Flask, request, abort
from werkzeug.serving import make_server
import jsonschema
import APIs.Keypad.JsonSchemas as schemas
from APIs.Keypad.ReceiveKeyCodeReturnCode import ReceiveKeyCodeReturnCode
from common.APIClient.HTTPStatusCode import HTTPStatusCode


## Implementation of thread that handles API calls to the keypad API.
class IOProcessingThread(threading.Thread):

    KeypadAPIEndpoint = Flask(__name__)

    ConsoleLogger = None
    
    StatusObject = None

    ControllerDb = None
    
    Config = None


    ## KeypadAPIThread class constructor, passing in the network port that the
    #  API will listen to.
    #  @param self The object pointer.
    #  @param listeningPort Network port to listen on.
    def __init__(self, logger, statusObject, config):        
        threading.Thread.__init__(self)
        self.__logger = logger
        self.__statusObject = statusObject
        self.__config = config


    ## Thread execution function, in this case run the Flask API interface.
    #  @param self The object pointer.
    def run(self):
        self.__logger.info('starting IO processing thread')


    ## Thread shutdown function to stop the keypad API endpoint interface.
    #  @param self The object pointer.
    def shutdown(self):
        self.__logger.info('shutting down IO processing thread')
