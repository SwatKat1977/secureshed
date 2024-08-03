"""
Copyright 2019-2024 Secure Shed Project Dev Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

class Event:
    """
    A class to represent an event with an identifier and an optional message 
    body.

    Attributes:
    ----------
    _id : int
        A unique identifier for the event.
    _body : str, optional
        A message body associated with the event (default is None).
    """
    __slots__ = ["_id", "_body"]

    @property
    def event_id(self) -> int:
        """
        Gets the unique identifier of the event.

        Returns:
            The unique identifier of the event.
        """
        return self._id

    ## Property getter : Event body
    @property
    def body(self):
        """
        Gets the message body of the event.

        Returns:
            The message body of the event, or None if not body.
        """
        return self._body

    def __init__(self, event_id: int, msg_body:object | None = None):
        """
        Constructs all the necessary attributes for the event object.

        Parameters:
        ----------
        eventId : int
            The unique identifier for the event.
        msgBody : object, optional
            The message body associated with the event (default is None).
        """
        self._id: int = event_id
        self._body: object | None = msg_body
