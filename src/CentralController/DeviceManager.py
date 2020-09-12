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
import collections
from centralController.DevicesConfigLoader import DevicesConfigLoader
import centralController.Events as Evts
from common.Logger import Logger, LogType

try:
    import RPi.GPIO as GPIO
    RPIO_EMULATED = False
except ModuleNotFoundError:
    from CentralController.EmulatedRaspberryPiIO import GPIO
    RPIO_EMULATED = True


class DeviceManager:
    __slots__ = ['__devices', '__deviceTypeMgr', '__eventMgr']

    Device = collections.namedtuple('Device',
                                    'name hardware deviceType pins triggerGracePeriod')


    #  @param self The object pointer.
    def __init__(self, deviceTypeMgr, eventMgr):
        self.__deviceTypeMgr = deviceTypeMgr
        self.__devices = []
        self.__eventMgr = eventMgr

        if RPIO_EMULATED:
            Logger.Instance().Log(LogType.Info, 'Using Raspberry PI IO Emulation...')

        GPIO.setmode(GPIO.BCM)


    #  @param self The object pointer.
    def Load(self, devices):
        deviceTypes = self.__deviceTypeMgr.deviceTypes

        for device in devices:
            name = device[DevicesConfigLoader.DeviceElement.Name]
            enabled = device[DevicesConfigLoader.DeviceElement.Enabled]

            if not enabled:
                Logger.Instance().Log(LogType.Warn,
                                      "Device '%s' is disabled, not loading it!", name)
                continue

            try:
                triggerGracePeriod = \
                    device[DevicesConfigLoader.DeviceElement.TriggerGracePeriodSecs]

            except KeyError:
                triggerGracePeriod = None

            pins = device[DevicesConfigLoader.DeviceElement.Pins]
            hardware = device[DevicesConfigLoader.DeviceElement.Hardware]
            deviceType = device[DevicesConfigLoader.DeviceElement.DeviceType]

            if deviceType not in deviceTypes:
                Logger.Instance().Log(LogType.Warn,
                                      "Ignoring device '%s' as it has invalid " +\
                                      "device type of '%s'", name, deviceType)
                continue

            try:
                deviceInst = deviceTypes[deviceType](GPIO, self.__eventMgr)
                newDevice = self.Device(name=name, hardware=hardware,
                                        deviceType=deviceInst, pins=pins,
                                        triggerGracePeriod=triggerGracePeriod)
                self.__devices.append(newDevice)

            except TypeError:
                Logger.Instance().Log(LogType.Warn,
                                      "Ignoring device '%s' as unable to " +\
                                      "instantiate device type of '%s'", name,
                                      deviceType)
                continue


    #  @param self The object pointer.
    def InitialiseHardware(self):

        devices = []

        for device in self.__devices:
            try:
                additionalParams = {
                    'triggerGracePeriodSecs': device.triggerGracePeriod
                }

                if not device.deviceType.Initialise(device.name, device.pins,
                                                    additionalParams):
                    Logger.Instance().Log(LogType.Error,
                                          "Device plug-in '%s' initialisation" +\
                                          " failed so cannot be used.", device.name)
                    continue

                devices.append(device)

            except NotImplementedError:
                Logger.Instance().Log(LogType.Error,
                                      "Device name '%s' plug-in does not " +\
                                      "implement Initialise() so cannot be used.", device.name)

            except TypeError:
                Logger.Instance().Log(LogType.Error,
                                      "Device name '%s' plug-in has syntax " +\
                                      "error(s) so cannot be used.", device.name)

        self.__devices = devices


    #  @param self The object pointer.
    def CheckHardwareDevices(self):

        if RPIO_EMULATED:
            GPIO.UpdateFromPinOutFile()

        for device in self.__devices:
            try:
                device.deviceType.CheckDevice()

            except NotImplementedError:
                Logger.Instance().Log(LogType.Error,
                                      "Device name '%s' plug-in does not " +\
                                      "implement CheckDevice() so cannot be used.",
                                      device.name)


    #  @param self The object pointer.
    def CleanupDevices(self):
        Logger.Instance().Log(LogType.Info, "Cleaning up hardware devices")
        GPIO.cleanup()


    #  @param self The object pointer.
    def ReceiveEvent(self, eventInst):
        # Event : Activate siren.
        if eventInst.id == Evts.EvtType.ActivateSiren:
            self.__ProcessActivateSirenEvent(eventInst)

        elif eventInst.id == Evts.EvtType.DeactivateSiren:
            self.__ProcessDeactivateSirenEvent(eventInst)

        elif eventInst.id == Evts.EvtType.AlarmActivated:
            self.__ProcessAlarmActivatedEvent(eventInst)

        elif eventInst.id == Evts.EvtType.AlarmDeactivated:
            self.__ProcessAlarmDeactivatedEvent(eventInst)


    #  @param self The object pointer.
    def __ProcessActivateSirenEvent(self, eventInst):
        sirens = [s for s in self.__devices if s.hardware == 'siren']

        for siren in sirens:
            Logger.Instance().Log(LogType.Info, "Activating alarm siren '%s'",
                                  siren.name)
            siren.deviceType.ReceiveEvent(eventInst)


    #  @param self The object pointer.
    def __ProcessDeactivateSirenEvent(self, eventInst):
        sirens = [s for s in self.__devices if s.hardware == 'siren']

        for siren in sirens:
            Logger.Instance().Log(LogType.Info,
                                  "Deactivating alarm siren '%s'", siren.name)
            siren.deviceType.ReceiveEvent(eventInst)


    #  @param self The object pointer.
    def __ProcessAlarmActivatedEvent(self, eventInst):
        if eventInst.body['noGraceTime']:
            return

        sensors = [s for s in self.__devices if s.hardware == 'sensor']
        for sensor in sensors:
            try:
                sensor.deviceType.ReceiveEvent(eventInst)

            except NotImplementedError:
                Logger.Instance().Log(LogType.Info,
                                      "Device '%s' missing ReceiveEvent()",
                                      sensor.name)


    #  @param self The object pointer.
    def __ProcessAlarmDeactivatedEvent(self, eventInst):
        sensors = [s for s in self.__devices if s.hardware == 'sensor']
        for sensor in sensors:
            try:
                sensor.deviceType.ReceiveEvent(eventInst)

            except NotImplementedError:
                Logger.Instance().Log(LogType.Error,
                                      "Device '%s' missing ReceiveEvent()",
                                      sensor.name)
