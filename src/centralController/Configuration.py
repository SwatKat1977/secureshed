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


KeypadAPIConfig = collections.namedtuple('KeypadAPIConfig', 'networkPort')


class Configuration:
    __slots__ = ['__failedAttemptResponses', '__keypadApiConfig']


    ## Property getter : Keypad API config
    #  @param self The object pointer.
    @property
    def keypadApiConfig(self):
        return self.__keypadApiConfig

    ## Property getter : Failed code entry attempt responses
    #  @param self The object pointer.
    @property
    def failedAttemptResponses(self):
        return self.__failedAttemptResponses


    ## Default constructor for Configuration class.
    #  @param self The object pointer.
    #  @param keypadAPIConfig Configuration items for keypad api.
    #  @param failedAttemptResponses Responses when an attempt fails.
    def __init__(self, keypadAPIConfig, failedAttemptResponses):
        if not isinstance(keypadAPIConfig, KeypadAPIConfig):
            raise TypeError('keypadAPIConfig param not type keypadAPIConfig')

        self.__keypadApiConfig = keypadAPIConfig

        self.__failedAttemptResponses = failedAttemptResponses
