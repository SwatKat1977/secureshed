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


## Implementation of an event.
class Event:

    ## Property getter : Event ID
    @property
    def id(self):
        return self._eventId


    ## Property getter : Event body
    @property
    def body(self):
        return self._msgBody


    ## Event default constructor.
    #  @param self The object pointer.
    #  @param eventId Id of event.
    #  @param msgBody Optional message body for event.
    def __init__(self, eventId, msgBody=None):
        self._eventId = eventId
        self._msgBody = msgBody
