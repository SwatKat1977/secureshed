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
import threading
import time


## Main worker thread for the central controller.
class WorkerThread(threading.Thread):

    ## Property getter : Last error message
    @property
    def shutdown_completed(self):
        return self._shutdown_has_completed


    ## WorkerThread class constructor.
    #  @param self The object pointer.
    #  @param keypadControllerPanel TBD.
    #  @param centralControllerPanel TBD.
    def __init__(self, keypadControllerPanel, centralControllerPanel):
        threading.Thread.__init__(self)
        self._keypad_controller_panel = keypadControllerPanel
        self._central_controller_panel = centralControllerPanel
        self._shutdown_is_requested = False
        self._shutdown_has_completed = False


    ## Thread execution function, in this case run the Flask API interface.
    #  @param self The object pointer.
    def run(self):
        while not self._shutdown_is_requested:
            self._keypad_controller_panel.GetLogs()
            self._central_controller_panel.GetLogs()
            time.sleep(0.1)

        self._shutdown_has_completed = True


    #  @param self The object pointer.
    def request_shutdown(self):
        self._shutdown_is_requested = True
