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
import importlib
from DeviceTypes.BaseSirenDeviceType import BaseSirenDeviceType
from DeviceTypes.BaseSensorDeviceType import BaseSensorDeviceType


class DeviceTypeManager:
    __slots__ = ['__deviceTypes', '__logger']

    @property
    def deviceTypes(self):
        return self.__deviceTypes


    def __init__(self, logger):
        self.__logger = logger

        self.__deviceTypes = {
            'GenericAlarmSiren': None,
            'GenericMageticSensor': None
        }

        newDeviceTypes = {}

        for device in self.__deviceTypes:
            moduleName = f'DeviceTypes.{device}'

            try:
                importedModule = importlib.import_module(moduleName)

            except ModuleNotFoundError:
                self.__logger.warn(f"No plug-in for device type '{device}'," +\
                    " it has been removed from the devices list.")
                continue

            except NameError:
                self.__logger.warn(f"Device type '{device}' Plug-in has a " +\
                    "syntax error, it has been removed from the devices list.")
                continue

            try:
                importedCls = getattr(importedModule, device)

                valid = BaseSirenDeviceType in importedCls.__bases__ or \
                    BaseSensorDeviceType in importedCls.__bases__

                if not valid:
                    self.__logger.warn(f"Plug-in for device type '{device}'" +\
                        " is not derived from plug-in class.  It cannot be " +\
                         "used and was removed from the devices list.")
                    continue

                newDeviceTypes[device] = importedCls

            except AttributeError:
                pass

        self.__deviceTypes = newDeviceTypes


class testLogger:
    def warn(self, msg):
        print(f'[WARN] {msg}')

d = DeviceTypeManager(testLogger())
