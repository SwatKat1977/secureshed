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
    __slots__ = ['__alarmSettingsConfig', '__failedAttemptResponses',
                 '__generalSettings', '__keypadApiConfig']

    GeneralSettings = collections.namedtuple('GeneralSettings', 'devicesConfigFile')

    KeypadAPICfg = collections.namedtuple('KeypadAPIConfig', 'networkPort')

    AlarmSettingsCfg = collections.namedtuple('AlarmSettingsConfig',
                                              'AlarmSetGraceTimeSecs')

    ## Property getter : Keypad API config
    #  @param self The object pointer.
    @property
    def keypadApiConfig(self):
        return self.__keypadApiConfig

    @property
    def generalSettings(self):
        return self.__generalSettings

    @property
    def failedAttemptResponses(self):
        return self.__failedAttemptResponses


    ## Default constructor for Configuration class.
    #  @param self The object pointer.
    #  @param keypadAPIConfig Configuration items for keypad api.
    #  @param generalSettings General settings configuration items.
    #  @param failedAttemptResponses Responses when an attempt fails.
    def __init__(self, keypadAPIConfig, generalSettings, failedAttemptResponses):
        if not isinstance(keypadAPIConfig, self.KeypadAPICfg):
            raise TypeError('keypadAPIConfig param not type KeypadAPICfg')

        self.__keypadApiConfig = keypadAPIConfig

        self.__failedAttemptResponses = failedAttemptResponses

        self.__generalSettings = generalSettings
