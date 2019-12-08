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
import enum
from Common.Singleton import Singleton


## <Description go here>
class EventManagerStatusCode(enum.Enum):
    Success = 0
    InvalidEventID = 1
    EventManagerDisabled = 2


## <Description go here>
@Singleton
class EventManager:

    ## <Description go here>
    #  @param self The object pointer.
    def __init__(self):
        self._enabled = True
        self._eventHandlers = {}
        self._events = []


    ## Queue a new event.
    #  @param self The object pointer.
    #  @param event Event to queue.
    #  @returns Return codes:
    #    EventManagerStatusCode.Success
    #    EventManagerStatusCode.InvalidEventID
    def QueueEvent(self, event):
        # Only queue the event, if event manager is enabled (running)
        if not self._enabled:
            return EventManagerStatusCode.EventManagerDisabled

        # Add event to queue.  Validate that the event is known about, if it is
        # then add it to the event queue for processing otherwise return
        # unknown status.
        if not self.IsValidEventType(event.id):
            return EventManagerStatusCode.InvalidEventID

        # Add the event into the queue.
        self._events.append(event)

        # Return 'success' status.
        return EventManagerStatusCode.Success


    ## Register an event with the event manager.
    #  @param self The object pointer.
    #  @param eventID ID of event to register.
    #  @param callback Event callback function.
    def RegisterEvent(self, eventID, callback):
        if eventID in self._eventHandlers:
            return

        self._eventHandlers[eventID] = callback


    # <summary>
    # Process the next event, if any exists.  An error will be generated
    # if the event ID is invalid (should never happen).
    # </summary>
    # <returns>Return codes:
    #    EventManagerStatusCode.Success
    #    EventManagerStatusCode.InvalidEventID
    # </returns>
    def ProcessNextEvent(self):
        # If nothing is ready for processing, return 0 (success)
        if not self._events:
            return EventManagerStatusCode.Success

        #  Get the first event from the list.
        event = self._events[0]

        # Check to see event ID is valid, if an unknown event ID then return
        # the 'invalid event id' error.
        if event.ID not in self._eventHandlers:
            return EventManagerStatusCode.InvalidEventID

        #  Call the event processing function, this is defined by the
        #  registered callback function.
        self._eventHandlers[event.ID](event)

        #  Once the event has been handled, delete it.. The event handler
        # function should deal with issues with the event and therefore
        #  deleting should be safe.
        self._events.pop(0)

        # Return 'success' status.
        return EventManagerStatusCode.Success


    # <summary>
    # Delete all events.
    # </summary>
    def DeleteAllEvents(self):
        del self._events[:]


    # <summary>
    # Check if an event is valid.
    # </summary>
    # <param name="eventID">Event ID to validate.</param>
    # <returns>Return codes: Valid = True.  Invalid = False# </returns>
    def IsValidEventType(self, eventID):
        return eventID in self._eventHandlers
