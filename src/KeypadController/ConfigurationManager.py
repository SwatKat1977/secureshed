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
import json
import jsonschema
from ConfigurationJsonSchema import CONFIGURATIONJSONSCHEMA


CentralController = collections.namedtuple('CentralController', 'endpoint')
Configuration = collections.namedtuple('Configuration', 'centralController')


class ConfigurationManager:

    # -----------------------------
    # -- Top-level json elements --
    # -----------------------------
    JSON_CentralControllerSettings = 'centralController'

    # ----------------------------------------------
    # -- Central controller settings sub-elements --
    # ----------------------------------------------
    JSON_CentralControllerSettings_Endpoint = 'endpoint'


    ## Property getter : Last error message
    @property
    def lastErrorMsg(self):
        return self.__lastErrorMsg


    #  @param self The object pointer.
    def __init__(self):
        self.__lastErrorMsg = ''


    #  @param self The object pointer.
    def ParseConfigFile(self, filename):
        self.__lastErrorMsg = ''

        try:
            with open(filename) as fileHandle:
                fileContents = fileHandle.read()

        except IOError as excpt:
            self.__lastErrorMsg = "Unable to open configuration file '" + \
                f"{filename}', reason: {excpt.strerror}"
            return None

        try:
            configJson = json.loads(fileContents)

        except json.JSONDecodeError as excpt:
            self.__lastErrorMsg = "Unable to parse configuration file" + \
                f"{filename}, reason: {excpt}"
            return None

        try:
            jsonschema.validate(instance=configJson,
                                schema=CONFIGURATIONJSONSCHEMA)

        except jsonschema.exceptions.ValidationError as ex:
            self.__lastErrorMsg = f"Configuration file {filename} failed " + \
                "to validate against expected schema.  Please check!.  "+ \
                f"Msg: {ex}"
            return None

        centralController = self.__ProcessCentralControllerSection(configJson)

        return Configuration(centralController=centralController)


    #  @param self The object pointer.
    def __ProcessCentralControllerSection(self, config):
        sctn = config[self.JSON_CentralControllerSettings]
        endpoint = sctn[self.JSON_CentralControllerSettings_Endpoint]
        return CentralController(endpoint)


testCls = ConfigurationManager()
x = testCls.ParseConfigFile('configuration.json')
print(x)
print(testCls.lastErrorMsg)
