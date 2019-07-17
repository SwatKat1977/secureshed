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
from enum import Enum
import json
import threading
import time
from flask import Flask, request, abort
from werkzeug.serving import make_server
import jsonschema

### application/json
### https://stackoverflow.com/questions/23110383/how-to-dynamically-build-a-json-object-with-python

ReceiveKeyCodeJsonSchema = {
    "type" : "object",
    "additionalProperties": False,

    "properties" : {
        "additionalProperties": False,
        "keySequence" : {"type" : "string"},
    },
}


## Return codes for ReceiveKeyCode route.
class ReceiveKeyCodeReturnCode(Enum):
    # The keycode has been accepted and the alarm is now off/disabled.
    KeycodeAccepted = 0

    # The keycode entered was invalid, as a result the keypad could get locked
    # for a period of time.
    KeycodeIncorrect = 1

    # The keycode was refused, possibly you are trying to enter a keycode when
    # the keypad is meant to be disabled.    
    KeycodeRefused = 2

    # a keycode was received out of sequence and is not expected so rejecting.
    OutOfSequence = 3

'''
KeycodeIncorrect and KeycodeRefused have atateChange value:
DisablePad : <timeInSeconds>
'''

class receiveKeyCodeHeader(object):
    AuthKey = 'authorisationKey'

class receiveKeyCodeBody(object):
    KeySeq = 'keySequence'


## Implementation of thread that handles API calls to the keypad API.
class KeypadAPIThread(threading.Thread):

    KeypadAPIEndpoint = Flask(__name__)


    ## KeypadAPIThread class constructor, passing in the network port that the
    #  API will listen to.
    #  @param self The object pointer.
    #  @param listeningPort Network port to listen on.
    def __init__(self, listeningPort):
        threading.Thread.__init__(self)
        self.srv = make_server('127.0.0.1', listeningPort,
            KeypadAPIThread.KeypadAPIEndpoint)
        KeypadAPIThread.KeypadAPIEndpoint.debug = True
        self.ctx = KeypadAPIThread.KeypadAPIEndpoint.app_context()
        self.ctx.push()


    ## Thread execution function, in this case run the Flask API interface.
    #  @param self The object pointer.
    def run(self):
        self.srv.serve_forever()


    ## Thread shutdown function to stop the keypad API endpoint interface.
    #  @param self The object pointer.
    def shutdown(self):
        self.srv.shutdown()


    ## API route : receiveKeyCode
    #  Recieve a key code from the keypad.  This is for unlocking/disabling the
    #  alarm system.
    #  Return codes:
    #  * 200 (OK) - code accepted, trip alarm, disable keypad.
    #  * 400 (Bad Request) - Missing or invalid json body or validation failed.
    #  * 401 (Unauthenticated) - Missing or invalid authentication key.
    @KeypadAPIEndpoint.route('/receiveKeyCode',methods = ['POST'])
    def ReceiveKeyCode():

        # Check for that the message body ia of type application/json and that
        # there is one, if not report a 400 error status with a human-readable.
        body = request.get_json()
        if body == None:
            errMsg = 'Missing/invalid json body'
            response = KeypadAPIThread.KeypadAPIEndpoint.response_class(
                response=errMsg, status=400, mimetype='text')
            return response

        # Verify that an authorisation key exists in the requet header, if not
        # then return a 401 error with a human-readable reasoning. 
        if receiveKeyCodeHeader.AuthKey not in request.headers:
            errMsg = 'Authorisation key is missing'
            response = KeypadAPIThread.KeypadAPIEndpoint.response_class(
                response=errMsg, status=401, mimetype='text')
            return response

        authorisationKey = request.headers[receiveKeyCodeHeader.AuthKey]

        # As the authorisation key functionality isn't currently implemented I
        # have hard-coded as 'authKey'.  If the key isn't valid then the error
        # code of 401 (Unauthenticated) is returned.
        if authorisationKey != 'authKey':
            errMsg = 'Authorisation key is invalid'
            response = KeypadAPIThread.KeypadAPIEndpoint.response_class(
                response=errMsg, status=401, mimetype='text')
            return response

        # Validate that the json body conforms to the expected schema.
        # If the message isn't valid then a 400 error should be generated.        
        try:
            jsonschema.validate(instance = body, schema = ReceiveKeyCodeJsonSchema)

        except Exception as ex:
            errMsg = 'Message body validation failed.'
            response = KeypadAPIThread.KeypadAPIEndpoint.response_class(
                response=errMsg, status=400, mimetype='text')
            return response

        keySeq = body[receiveKeyCodeBody.KeySeq]
        KeypadAPIThread.KeypadAPIEndpoint.logger.info(f"keySequence : {keySeq}")

        responseJson = {}
        responseJson["StatusCode"] = ReceiveKeyCodeReturnCode.KeycodeAccepted.value
        return 'OK'


server = KeypadAPIThread(5000)
server.start()

#while True:
#    pass

time.sleep(20)
server.shutdown()