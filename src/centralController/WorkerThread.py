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


## Main worker thread for the central controller.
class WorkerThread(threading.Thread):

    class IOPinState(enum.Enum):
        High = 0
        Low = 1

    ## Property getter : Last error message
    @property
    def shutdownCompleted(self):
        return self.__shutdownCompleted


    ## WorkerThread class constructor.
    #  @param self The object pointer.
    #  @param logger Network port to listen on.
    #  @param config Configuration items.
    #  @param deviceManager Device hardware management class.
    #  @param eventManager Event management class instance.
    #  @param stateMsr Statement management class instance.
    def __init__(self, logger, config, deviceManager, eventManager, stateMsr):
        threading.Thread.__init__(self)
        self.__logger = logger
        self.__config = config
        self.__deviceManager = deviceManager
        self.__eventManager = eventManager
        self.__shutdownRequested = False
        self.__shutdownCompleted = False
        self.__stateMgr = stateMsr


    ## Thread execution function, in this case run the Flask API interface.
    #  @param self The object pointer.
    def run(self):
        self.__logger.info('starting IO processing thread')

        while not self.__shutdownRequested:
            self.__stateMgr.UpdateTransitoryEvents()
            self.__deviceManager.CheckHardwareDevices()
            self.__eventManager.ProcessNextEvent()
            time.sleep(0.5)

        self.__shutdownCompleted = True


    #  @param self The object pointer.
    def SignalShutdownRequested(self):
        self.__shutdownRequested = True
