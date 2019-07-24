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
import json
import jsonschema
from ConfigurationJsonSchema import ConfigurationJsonSchema

'''
https://python-jsonschema.readthedocs.io/en/stable/faq/#how-do-jsonschema-version-numbers-work

https://jsonschemalint.com/#/version/draft-07/markup/json
'''


class ConfigurationManager(object):

    ## Property getter : Last error message
    @property
    def LastErrorMsg(self):
        return self.__lastErrorMsg


    def __init__(self):
        self.__lastErrorMsg = ''


    def ParseConfigFile(self, filename):
        try:
            with open(filename) as fileHandle:
                fileContents = fileHandle.read()

        except IOError as excpt:
            self.__lastErrorMsg = "Unable to open configuration file" + \
                f"{filename}, reason: {excpt.strerror}"
            return False

        try:
            configJson = json.loads(fileContents)
        
        except json.JSONDecodeError as excpt:
            self.__lastErrorMsg = "Unable to parse configuration file" + \
                f"{filename}, reason: {excpt}"
            return False

        try:
            jsonschema.validate(instance = configJson,
                schema = ConfigurationJsonSchema)

        except Exception as ex:
            self.__lastErrorMsg = f"Configuration file {filename} failed " + \
                "to validate against expected schema.  Please check!"
            print(ex)
            return False
        
        print(configJson)


configFile = '../../configurations/centralController/configuration.json'
cm = ConfigurationManager()
if cm.ParseConfigFile(configFile) == False:
    print(f"Parse failed, last message : {cm.LastErrorMsg}")

class Configuration(object):

    def __init__(self):
        pass
