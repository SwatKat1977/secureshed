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


class DeviceManager:
    __slots__ = ['__devices', '__deviceTypeMgr', '__logger']

    Device = collections.namedtuple('Device',
                                    'name hardware deviceType enabled pins')


    #  @param self The object pointer.
    def __init__(self, logger, deviceTypeMgr):
        self.__logger = logger
        self.__deviceTypeMgr = deviceTypeMgr
        self.__devices = []


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

            newDevice = self.Device(name=name, hardware=hardware,
                                    deviceType=deviceTypes[deviceType],
                                    enabled=enabled, pins=pins)
            self.__devices.append(newDevice)
