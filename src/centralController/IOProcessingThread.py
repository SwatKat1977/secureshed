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
import threading

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    from centralController.EmulatedRaspberryPiIO import GPIO


## Implementation of thread that handles API calls to the keypad API.
class IOProcessingThread(threading.Thread):

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
        # pylint: disable=C0103
        self.__logger.info('shutting down IO processing thread')


import time
#import RPi.GPIO as GPIO

RelayPin = 23

GPIO.cleanup() 

GPIO.setmode(GPIO.BCM)  


GPIO.setup(RelayPin, GPIO.OUT)
GPIO.output(RelayPin, GPIO.HIGH)
print('SETUP relay')
time.sleep(10)

print('Activating')
GPIO.output(RelayPin, GPIO.LOW)
time.sleep(10)
print('De-activating')
GPIO.output(RelayPin, GPIO.HIGH)

time.sleep(10)
print('Activating')
GPIO.output(RelayPin, GPIO.LOW)

time.sleep(10)

GPIO.cleanup() 
