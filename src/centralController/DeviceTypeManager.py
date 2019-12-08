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
from centralController.DeviceTypes.BaseDeviceType import BaseDeviceType


class DeviceTypeManager:
    # pylint: disable=R0903
    __slots__ = ['__deviceTypes', '__expectedDeviceTypes', '__logger']

    @property
    def deviceTypes(self):
        return self.__deviceTypes


    def __init__(self, logger):
        self.__logger = logger

        self.__expectedDeviceTypes = {
            'GenericAlarmSiren': None,
            'MagneticContactSensor': None,
            'InvalidForTesting': None
        }

        self.__deviceTypes = {}


    def LoadDeviceTypes(self):
        defaultModulePath = 'centralController.DeviceTypes.'

        for device in self.__expectedDeviceTypes:
            moduleName = f'{defaultModulePath}{device}'

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

                valid = BaseDeviceType in importedCls.__bases__

                if not valid:
                    self.__logger.warn(f"Plug-in for device type '{device}'" +\
                        " is not derived from plug-in class.  It cannot be " +\
                         "used and was removed from the devices list.")
                    continue

                self.__deviceTypes[device] = importedCls
                self.__logger.info(f"Loaded plug-in for device type '{device}'")

            except AttributeError:
                pass
