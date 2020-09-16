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
# pylint: disable=ungrouped-imports
import collections
from central_controller.devices_config_loader import DevicesConfigLoader
import central_controller.events as Evts
from common.Logger import LogType

try:
    import RPi.GPIO as GPIO
    RPIO_EMULATED = False
except ModuleNotFoundError:
    from central_controller.emulated_raspberry_pi_io import GPIO
    RPIO_EMULATED = True


class DeviceManager:
    __slots__ = ['_devices', '_device_type_mgr', '_event_mgr', '_logger']

    Device = collections.namedtuple('Device',
                                    'name hardware deviceType pins triggerGracePeriod')


    #  @param self The object pointer.
    def __init__(self, deviceTypeMgr, eventMgr, logger):
        self._device_type_mgr = deviceTypeMgr
        self._devices = []
        self._event_mgr = eventMgr
        self._logger = logger

        if RPIO_EMULATED:
            self._logger.Log(LogType.Info, 'Using Raspberry PI IO Emulation...')
            GPIO.logger = logger

        GPIO.setmode(GPIO.BCM)


    #  @param self The object pointer.
    def load(self, devices):
        device_types = self._device_type_mgr.device_types

        for device in devices:
            name = device[DevicesConfigLoader.DeviceElement.Name]
            enabled = device[DevicesConfigLoader.DeviceElement.Enabled]

            if not enabled:
                self._logger.Log(LogType.Warn,
                                 "Device '%s' is disabled, not loading it!", name)
                continue

            try:
                trigger_grace_period = \
                    device[DevicesConfigLoader.DeviceElement.TriggerGracePeriodSecs]

            except KeyError:
                trigger_grace_period = None

            pins = device[DevicesConfigLoader.DeviceElement.Pins]
            hardware = device[DevicesConfigLoader.DeviceElement.Hardware]
            device_type = device[DevicesConfigLoader.DeviceElement.DeviceType]

            if device_type not in device_types:
                self._logger.Log(LogType.Warn,
                                 "Ignoring device '%s' as it has invalid " +\
                                 "device type of '%s'", name, device_type)
                continue

            try:
                device_inst = device_types[device_type](GPIO, self._event_mgr)
                new_device = self.Device(name=name, hardware=hardware,
                                         deviceType=device_inst, pins=pins,
                                         triggerGracePeriod=trigger_grace_period)
                self._devices.append(new_device)

            except TypeError:
                self._logger.Log(LogType.Warn,
                                 "Ignoring device '%s' as unable to " +\
                                 "instantiate device type of '%s'", name,
                                 device_type)
                continue


    #  @param self The object pointer.
    def initialise_hardware(self):

        devices = []

        for device in self._devices:
            try:
                additional_params = {
                    'triggerGracePeriodSecs': device.triggerGracePeriod
                }

                if not device.deviceType.initialise(device.name, device.pins,
                                                    additional_params):
                    self._logger.Log(LogType.Error,
                                     "Device plug-in '%s' initialisation" + \
                                     " failed so cannot be used.", device.name)
                    continue

                devices.append(device)

            except NotImplementedError:
                self._logger.Log(LogType.Error,
                                 "Device name '%s' plug-in does not " + \
                                 "implement initialise() so cannot be used.",
                                 device.name)

            except TypeError:
                self._logger.Log(LogType.Error,
                                 "Device name '%s' plug-in has syntax " + \
                                 "error(s) so cannot be used.", device.name)

        self._devices = devices


    #  @param self The object pointer.
    def check_hardware_devices(self):

        if RPIO_EMULATED:
            GPIO.update_from_pinout_file()

        for device in self._devices:
            try:
                device.deviceType.check_device()

            except NotImplementedError:
                self._logger.Log(LogType.Error,
                                 "Device name '%s' plug-in does not " + \
                                 "implement check_device() so cannot be used.",
                                 device.name)


    #  @param self The object pointer.
    def cleanup_devices(self):
        self._logger.Log(LogType.Info, "Cleaning up hardware devices")
        GPIO.cleanup()


    #  @param self The object pointer.
    def receive_event(self, event):
        # Event : Activate siren.
        if event.id == Evts.EvtType.ActivateSiren:
            self._process_activate_siren_event(event)

        elif event.id == Evts.EvtType.DeactivateSiren:
            self._process_deactivate_siren_event(event)

        elif event.id == Evts.EvtType.AlarmActivated:
            self._process_alarm_activated_event(event)

        elif event.id == Evts.EvtType.AlarmDeactivated:
            self._process_alarm_deactivated_event(event)


    #  @param self The object pointer.
    def _process_activate_siren_event(self, event):
        sirens = [s for s in self._devices if s.hardware == 'siren']

        for siren in sirens:
            self._logger.Log(LogType.Info, "Activating alarm siren '%s'",
                             siren.name)
            siren.deviceType.receive_event(event)


    #  @param self The object pointer.
    def _process_deactivate_siren_event(self, event):
        sirens = [s for s in self._devices if s.hardware == 'siren']

        for siren in sirens:
            self._logger.Log(LogType.Info,
                             "Deactivating alarm siren '%s'", siren.name)
            siren.deviceType.receive_event(event)


    #  @param self The object pointer.
    def _process_alarm_activated_event(self, event):
        if event.body['noGraceTime']:
            return

        sensors = [s for s in self._devices if s.hardware == 'sensor']
        for sensor in sensors:
            try:
                sensor.deviceType.receive_event(event)

            except NotImplementedError:
                self._logger.Log(LogType.Info,
                                 "Device '%s' missing receive_event()",
                                 sensor.name)


    #  @param self The object pointer.
    def _process_alarm_deactivated_event(self, event):
        sensors = [s for s in self._devices if s.hardware == 'sensor']
        for sensor in sensors:
            try:
                sensor.deviceType.receive_event(event)

            except NotImplementedError:
                self._logger.Log(LogType.Error,
                                 "Device '%s' missing receive_event()",
                                 sensor.name)
