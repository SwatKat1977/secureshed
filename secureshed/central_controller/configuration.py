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
import dataclasses
import typing
from configuration_system.configuration_manager import ConfigurationManager
from thread_safe_singleton import ThreadSafeSingleton

@dataclasses.dataclass
class FailedAttemptResponseParameter:
    """
    Represents a parameter associated with a failed attempt response.

    Attributes:
        key (str): The name or identifier of the parameter.
        value (str): The value associated with the key, which may provide
                     additional information about the failure.
    """
    key: str
    value: str

@dataclasses.dataclass
class FailedAttemptResponseAction:
    """
    Represents an action that occurred during a failed attempt response.

    Attributes:
        action_type (str): The type of the action, describing what kind of
                           action was performed.
        parameters (List[FailedAttemptResponseParameter]): A list of
            parameters related to the action, providing additional context or
            details.
    """
    action_type: str
    parameters: typing.List[FailedAttemptResponseParameter]

@dataclasses.dataclass
class FailedAttemptResponse:
    """
    Represents the overall response for a failed attempt, including multiple
    actions.

    Attributes:
        attempt_no (int): The number of the failed attempt.
        actions (List[FailedAttemptResponseAction]): A list of actions
            related to the failed attempt, detailing what occurred during the
            attempt.
    """
    attempt_no: int
    actions: typing.List[FailedAttemptResponseAction]

class Configuration(ConfigurationManager, metaclass=ThreadSafeSingleton):
    """ Thread-safe singleton for the config """

    def __init__(self):
        super().__init__()
        self._attempt_responses : dict = {}

    @property
    def general_devices_config_file(self) -> str:
        """
        Get the path to the general devices configuration file.

        This property retrieves the value of the "devices_config_file" entry
        from the "general" section of the configuration.

        Returns:
            str: The path to the general devices configuration file.
        """
        return Configuration().get_entry("general", "devices_config_file")

    @property
    def general_device_types_config_file(self) -> str:
        """
        Get the path to the general device types configuration file.

        This property retrieves the value of the "device_types_config_file"
        entry from the "general" section of the configuration.

        Returns:
            str: The path to the general device types configuration file.
        """
        return Configuration().get_entry("general", "device_types_config_file")

    @property
    def general_authentication_key(self) -> str:
        """
        Get the general authentication key.

        This property retrieves the value of the "authentication_key" entry
        from the "general" section of the configuration.

        Returns:
            str: The general authentication key.
        """
        return Configuration().get_entry("general", "authentication_key")

    @property
    def general_failed_attempt_responses(self) -> str:
        """
        Get the configuration entry for general failed attempt responses.

        This property retrieves the value of the "failed_attempt_responses"
        entry from the "general" section of the configuration.

        Returns:
            str: The configuration entry for general failed attempt responses.
        """
        return Configuration().get_entry("general", "failed_attempt_responses")

    @property
    def keypad_controller_endpoint(self) -> str:
        """
        Get the endpoint configuration for the keypad controller.

        This property retrieves the value of the "endpoint" entry from the
        "keypad_controller" section of the configuration.

        Returns:
            str: The endpoint configuration for the keypad controller.
        """
        return Configuration().get_entry("keypad_controller", "endpoint")

    def add_failed_attempt_response(self, response: FailedAttemptResponse):
        """
        Add a failed attempt response to the internal dictionary.

        This method adds a new failed attempt response to the internal
        dictionary, using the attempt number as the key.

        Args:
            response (FailedAttemptResponse): The response to add.
        """
        self._attempt_responses[int(response["attemptNo"])] = response

    def get_failed_attempt_response(self, attempt_no: int) -> \
        FailedAttemptResponse | None:
        """
        Retrieve a failed attempt response by attempt number.

        This method retrieves a failed attempt response by its attempt number.
        If the attempt number is not found, it returns None.

        Args:
            attempt_no (int): The attempt number to retrieve the response for.

        Returns:
            Optional[FailedAttemptResponse]: The response for the specified
            attempt number, or None if not found.
        """
        return self._attempt_responses.get(attempt_no, None)

    def get_failed_attempt_responses(self) -> typing.ValuesView:
        """
        Return all stored failed attempt responses.

        This method returns a dictionary of all stored failed attempt responses.

        Returns:
            dict: A dictionary containing all failed attempt responses.
        """
        return self._attempt_responses.values()
