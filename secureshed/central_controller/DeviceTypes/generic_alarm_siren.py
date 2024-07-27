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
from central_controller.DeviceTypes.base_device_type import BaseDeviceType
import central_controller.events as Evts
from common.Logger import LogType


class GenericAlarmSiren(BaseDeviceType):

    ExpectedPinId = 'sirenPin'


    def __init__(self, hardwareIO, eventMgr, logger):
        self._additional_params = None
        self._device_name = None
        self._event_mgr = eventMgr
        self._hardware_io = hardwareIO
        self._io_pin = None
        self._is_triggered = False
        self._logger = logger


    def initialise(self, device_name, pins, additional_params):
        self._device_name = device_name
        self._additional_params = additional_params

        pin_prefix = 'GPIO'

        # Expecting one pin.
        if len(pins) != 1:
            self._logger.Log(LogType.Warn,
                             "Device '%s' was expecting 1 pin, actually %s",
                             device_name, len(pins))
            return False

        pin = [pin for pin in pins if pin['identifier'] == self.ExpectedPinId]
        if not pin:
            self._logger.Log(LogType.Warn,
                             "Device '%s' missing expected pin '%s'",
                             device_name, self.ExpectedPinId)
            return False

        self._io_pin = int(pin[0]['ioPin'][len(pin_prefix):])
        self._hardware_io.setup(self._io_pin, self._hardware_io.OUT)
        self._hardware_io.output(self._io_pin, self._hardware_io.HIGH)

        return True


    def check_device(self):
        pass


    def receive_event(self, event):
        if event.id == Evts.EvtType.ActivateSiren:
            self._hardware_io.output(self._io_pin, self._hardware_io.LOW)

        elif event.id == Evts.EvtType.DeactivateSiren:
            self._hardware_io.output(self._io_pin, self._hardware_io.HIGH)
