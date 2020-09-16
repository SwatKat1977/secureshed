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
    __slots__ = ['_failed_attempt_responses', '_general_settings',
                 '_central_controller_api', '_keypad_controller']

    GeneralSettings = collections.namedtuple('GeneralSettings',
                                             'devicesConfigFile deviceTypesConfigFile')

    KeypadControllerCfg = collections.namedtuple('KeypadControllerCfg', 'endpoint authKey')

    CentralControllerApiCfg = collections.namedtuple('CentralControllerApiCfg',
                                                     'networkPort authKey')

    ## Property getter : Keypad API config
    #  @param self The object pointer.
    @property
    def central_controller_api(self):
        return self._central_controller_api

    @property
    def general_settings(self):
        return self._general_settings

    @property
    def failed_attempt_responses(self):
        return self._failed_attempt_responses

    @property
    def keypad_controller(self):
        return self._keypad_controller


    ## Default constructor for Configuration class.
    #  @param self The object pointer.
    #  @param cenControllerApiCfg Config items for central controller api.
    #  @param generalSettings General settings configuration items.
    #  @param failedAttemptResponses Responses when an attempt fails.
    def __init__(self, cenControllerApiCfg, generalSettings,
                 failedAttemptResponses, keypadController):
        self._central_controller_api = cenControllerApiCfg

        self._failed_attempt_responses = failedAttemptResponses

        self._general_settings = generalSettings

        self._keypad_controller = keypadController
