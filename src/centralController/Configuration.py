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


class Configuration:
    __slots__ = ['__failedAttemptResponses', '__generalSettings',
                 '__centralControllerApi', '__keypadController']

    GeneralSettings = collections.namedtuple('GeneralSettings',
                                             'devicesConfigFile deviceTypesConfigFile')

    KeypadControllerCfg = collections.namedtuple('KeypadControllerCfg', 'endpoint authKey')

    CentralControllerApiCfg = collections.namedtuple('CentralControllerApiCfg',
                                                     'networkPort authKey')

    ## Property getter : Keypad API config
    #  @param self The object pointer.
    @property
    def centralControllerApi(self):
        return self.__centralControllerApi

    @property
    def generalSettings(self):
        return self.__generalSettings

    @property
    def failedAttemptResponses(self):
        return self.__failedAttemptResponses

    @property
    def keypadController(self):
        return self.__keypadController


    ## Default constructor for Configuration class.
    #  @param self The object pointer.
    #  @param cenControllerApiCfg Config items for central controller api.
    #  @param generalSettings General settings configuration items.
    #  @param failedAttemptResponses Responses when an attempt fails.
    def __init__(self, cenControllerApiCfg, generalSettings,
                 failedAttemptResponses, keypadController):
        self.__centralControllerApi = cenControllerApiCfg

        self.__failedAttemptResponses = failedAttemptResponses

        self.__generalSettings = generalSettings

        self.__keypadController = keypadController
