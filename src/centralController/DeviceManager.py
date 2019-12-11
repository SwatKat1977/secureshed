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

try:
    import RPi.GPIO as GPIO
    RPIO_EMULATED = False
except ModuleNotFoundError:
    from centralController.EmulatedRaspberryPiIO import GPIO
    RPIO_EMULATED = True


class DeviceManager:
    __slots__ = ['__devices', '__deviceTypeMgr', '__eventMgr', '__logger']

    Device = collections.namedtuple('Device', 'name hardware deviceType pins')


    #  @param self The object pointer.
    def __init__(self, logger, deviceTypeMgr, eventMgr):
        self.__logger = logger
        self.__deviceTypeMgr = deviceTypeMgr
        self.__devices = []
        self.__eventMgr = eventMgr

        if RPIO_EMULATED:
            self.__logger.info('Using Raspberry PI IO Emulation...')

        GPIO.setmode(GPIO.BCM)


    #  @param self The object pointer.
    def Load(self, devices):
        deviceTypes = self.__deviceTypeMgr.deviceTypes

        for device in devices:
            name = device[DevicesConfigLoader.DeviceElement.Name]
            enabled = device[DevicesConfigLoader.DeviceElement.Enabled]

            if not enabled:
                self.__logger.warn("Device '%s' is disabled, not loading it!",
                                   name)
                continue

            pins = device[DevicesConfigLoader.DeviceElement.Pins]
            hardware = device[DevicesConfigLoader.DeviceElement.Hardware]
            deviceType = device[DevicesConfigLoader.DeviceElement.DeviceType]

            if deviceType not in deviceTypes:
                self.__logger.warn("Ignoring device '%s' as it has invalid " +\
                                   "device type of '%s'", name, deviceType)
                continue

            try:
                deviceInst = deviceTypes[deviceType](self.__logger, GPIO,
                                                    self.__eventMgr)
                newDevice = self.Device(name=name, hardware=hardware,
                                        deviceType=deviceInst, pins=pins)
                self.__devices.append(newDevice)

            except TypeError:
                self.__logger.warn("Ignoring device '%s' as unable to " +\
                                   "instantiate device type of '%s'", name,
                                   deviceType)
                continue


    #  @param self The object pointer.
    def InitialiseHardware(self):

        devices = []

        for device in self.__devices:
            try:
                if not device.deviceType.Initialise(device.name, device.pins):
                    self.__logger.error("Device plug-in '%s' initialisation" +\
                        " failed so cannot be used.", device.name)
                    continue

                devices.append(device)

            except NotImplementedError:
                self.__logger.error("Device name '%s' plug-in does not " +\
                    "implement Initialise() so cannot be used.", device.name)


        self.__devices = devices


    #  @param self The object pointer.
    def CheckHardwareDevices(self):

        if RPIO_EMULATED:
            GPIO.UpdateFromPinOutFile(self.__logger)

        for device in self.__devices:
            try:
                device.deviceType.CheckDevice()

            except NotImplementedError:
                self.__logger.error("Device name '%s' plug-in does not " +\
                    "implement CheckDevice() so cannot be used.", device.name)


    #  @param self The object pointer.
    def CleanupDevices(self):
        GPIO.cleanup()


    #  @param self The object pointer.
    def ReceiveEvent(self, eventInst):
        # Event : Activate siren.
        if eventInst.id == Evts.EvtType.ActivateSiren:
            sirens = [s for s in self.__devices if s.hardware == 'siren']

            for siren in sirens:
                self.__logger.info("Activating alarm siren '%s'", siren.name)
                siren.deviceType.ReceiveEvent(eventInst)

        if eventInst.id == Evts.EvtType.DeactivateSiren:
            sirens = [s for s in self.__devices if s.hardware == 'siren']

            for siren in sirens:
                self.__logger.info("Deactivating alarm siren '%s'", siren.name)
                siren.deviceType.ReceiveEvent(eventInst)