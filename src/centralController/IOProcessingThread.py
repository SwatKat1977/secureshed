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
import enum
import threading
import time


## Implementation of thread that handles API calls to the keypad API.
class IOProcessingThread(threading.Thread):

    class IOPinState(enum.Enum):
        High = 0
        Low = 1

    ## Property getter : Last error message
    @property
    def shutdownCompleted(self):
        return self.__shutdownCompleted


    ## KeypadAPIThread class constructor, passing in the network port that the
    #  API will listen to.
    #  @param self The object pointer.
    #  @param logger Network port to listen on.
    #  @param statusObject Network port to listen on.
    #  @param config Network port to listen on.
    def __init__(self, logger, statusObject, config, deviceManager):
        threading.Thread.__init__(self)
        self.__logger = logger
        self.__statusObject = statusObject
        self.__config = config
        self.__shutdownRequested = False
        self.__shutdownCompleted = False
        self.__deviceManager = deviceManager


    ## Thread execution function, in this case run the Flask API interface.
    #  @param self The object pointer.
    def run(self):
        self.__logger.info('starting IO processing thread')

        while not self.__shutdownRequested:
            self.__deviceManager.CheckHardwareDevices()
            time.sleep(2)

        self.__shutdownCompleted = True


    def SignalShutdownRequested(self):
        self.__shutdownRequested = True

'''
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
'''


'''
# the pin numbers refer to the board connector not the chip
GPIO.setmode(GPIO.BCM)

relayPin = 18

print(relayPin)
GPIO.setup(relayPin, GPIO.IN, pull_up_down = GPIO.PUD_UP) 
# set up pin ?? (one of the above listed pins) as an input with
# a pull-up resistor

while True:
    if GPIO.input(relayPin):
        print "switch is open"
    else:
        print "switch is closed"

    time.sleep(1)
'''
