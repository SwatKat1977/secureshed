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
import logging
import signal
import sys
sys.path.append('..')
import time
from ConfigurationManager import ConfigurationManager
from KeypadAPIThread import KeypadAPIThread
from StatusObject import StatusObject


### https://stackoverflow.com/questions/23110383/how-to-dynamically-build-a-json-object-with-python

def handler(signum, frame):
    print('Shutting down...')
    server.shutdown()
    sys.exit(1)

signal.signal(signal.SIGINT, handler)

configFile = '../../configurations/centralController/configuration.json'

configManger = ConfigurationManager()

if configManger.ParseConfigFile(configFile) == False:
    print(f"Parse failed, last message : {cm.LastErrorMsg}")
    sys.exit(1)

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
    "%Y-%m-%d %H:%M:%S")
logger = logging.getLogger('system log')
consoleStream = logging.StreamHandler()
consoleStream.setFormatter(formatter)
logger.setLevel(logging.DEBUG)

# add the handlers to logger
logger.addHandler(consoleStream)

statusObject = StatusObject()

server = KeypadAPIThread(5000, logger, statusObject)
server.start()

while True:
    pass
    time.sleep(1)