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
from common.Logger import LogType


## Main worker thread for the central controller.
class WorkerThread(threading.Thread):

    class IOPinState(enum.Enum):
        High = 0
        Low = 1

    ## Property getter : Last error message
    @property
    def shutdown_completed(self):
        return self._shutdown_completed


    ## WorkerThread class constructor.
    #  @param self The object pointer.
    #  @param config Configuration items.
    #  @param deviceManager Device hardware management class.
    #  @param eventManager Event management class instance.
    #  @param stateMsr Statement management class instance.
    def __init__(self, config, deviceManager, eventManager, stateMsr, logger):
        # pylint: disable=too-many-arguments

        threading.Thread.__init__(self)
        self._config = config
        self._device_manager = deviceManager
        self._event_manager = eventManager
        self._logger = logger
        self._shutdown_requested = False
        self._shutdown_completed = False
        self._state_mgr = stateMsr


    ## Thread execution function, in this case run the Flask API interface.
    #  @param self The object pointer.
    def run(self):
        self._logger.Log(LogType.Info, 'starting IO processing thread')

        while not self._shutdown_requested:
            self._state_mgr.update_transitory_events()
            self._device_manager.check_hardware_devices()
            self._event_manager.ProcessNextEvent()
            time.sleep(0.1)

        self._shutdown_completed = True


    #  @param self The object pointer.
    def signal_shutdown_requested(self):
        self._shutdown_requested = True
