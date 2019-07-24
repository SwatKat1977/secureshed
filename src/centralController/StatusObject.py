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


class StatusObject(object):

    ## Property getter : Failed entry attempts
    @property
    def FailedEntryAttempts(self):
        return self.__failedEntryAttempts

    ## Property getter : Is authenticated flag.
    @property
    def IsAuthenticated(self):
        return self.__isAuthenticated

    @IsAuthenticated.setter
    def IsAuthenticated(self, newValue):

        if type(newValue) != bool:
            raise TypeError()

        self.__isAuthenticated = newValue


	## StatusObject default constructor.
	#  @param self The object pointer.
    def __init__(self):
        self.__failedEntryAttempts = 0
        self.__isAuthenticated = False


	## Increment the failed entry attempts.
	#  @param self The object pointer.
    def IncrementFailedEntryAttempts(self):
        self.__failedEntryAttempts += 1


	## Reset the failed entry attempts.
	#  @param self The object pointer.
    def ResetFailedEntryAttempts(self):
        self.__failedEntryAttempts = 0
