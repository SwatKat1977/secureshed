import json
import threading
import time
from flask import Flask, request, abort
from werkzeug.serving import make_server
import jsonschema


KeypadAPIEndpoint = Flask(__name__)


ReceiveKeyCodeJsonSchema = {
    "type" : "object",
    "additionalProperties": False,

    "properties" : {
        "additionalProperties": False,
        "authorisationKey" : {"type" : "string"},
        "keySequence" : {"type" : "string"},
    },
}

class KeypadAPIEndpointThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.srv = make_server('127.0.0.1', 5000, KeypadAPIEndpoint)
        KeypadAPIEndpoint.debug = True
        self.ctx = KeypadAPIEndpoint.app_context()
        self.ctx.push()

    def run(self):
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()

    @KeypadAPIEndpoint.route('/success/<name>',methods = ['POST'])
    def __success(name):
        return '[TEST] Call made with key %s' % name


    @KeypadAPIEndpoint.route('/receiveKeyCode',methods = ['POST'])
    def ReceiveKeyCode():

        body = request.get_json()

        if body == None:
            abort(400)
       
        KeypadAPIEndpoint.logger.info(f"Msg Header        : {request.headers}")
        KeypadAPIEndpoint.logger.info(f"Msg Request method : {request.method}")
        KeypadAPIEndpoint.logger.info(f"Msg Request json   : {body}")
        KeypadAPIEndpoint.logger.info(f"Msg Request json   : {ReceiveKeyCodeJsonSchema}")

        try:
            jsonschema.validate(instance = body, schema = ReceiveKeyCodeJsonSchema)
        except Exception:
            KeypadAPIEndpoint.logger.info(f"caught : {body}")

        # As the authorisation key functionality isn't currently implemented I
        # have hard-coded as 'authKey'.  If the key isn't valid then the error
        # code of 401 (Unauthenticated) is returned.
        if body['authorisationKey'] != 'authKey':
            print('not valid')
            abort(401)

        KeypadAPIEndpoint.logger.info(f"authorisationKey : {body['authorisationKey']}")
        KeypadAPIEndpoint.logger.info(f"keySequence      : {body['keySequence']}")

        return 'Got a post'


server = KeypadAPIEndpointThread()
server.start()

#while True:
#    pass

time.sleep(20)
server.shutdown()

