"""
this framework is responsible to set up the configuration for scope functionality.
ensures, trigger configuration as well as adding and removing a channel from the scope.

"""
import logging
from typing import Dict

from mchplnet.services.scope import ScopeSetup

logging.basicConfig(
    level=logging.DEBUG,
    filename="Scope_save_parameter.log",
)
from dataclasses import dataclass

from mchplnet.lnetframe import LNetFrame


class FrameSaveParameter(LNetFrame):
    """
    represents a frame for saving parameters.

    attributes:
        address: The address of the frame.
        size: The size of the frame.
        service_id: The service ID of the frame.
        unique_ID: The unique ID of the frame.
        scope_config: The scope configuration to be included in the frame.

    methods:
        __init__(): Initialize the FrameSaveParameter object.
        _deserialize (received: bytearray) -> bytearray | None: Deserialize the frame data.
        _get_data() -> list: Define the interface to get frame data.
        set_scope_configuration(scope_config: ScopeConfiguration): Set the scope configuration.
        remove_channel_by_name(channel_name: str): Remove a channel from the scope configuration by its name.
    """

    def __init__(self):
        """
        Initialize a FrameSaveParameter object.

        Initializes the address, size, service_id, unique_ID, and scope_config attributes.
        """
        super().__init__()
        self.address = None
        self.size = None
        self.service_id = 18
        self.unique_ID = 1
        self.unique_ID = self.unique_ID.to_bytes(length=2, byteorder="little")
        self.scope_setup = ScopeSetup()

    def _deserialize(self):
        """
        Nothing to do here once there is no service data on save parameter and
        errors and service id have already being checked by the superclass
        """

    def _get_data(self):
        self.data.extend([self.service_id, *self.unique_ID])
        self.data.extend(self.scope_setup.get_buffer())

    def set_scope_setup(self, scope_setup: ScopeSetup):
        self.scope_setup = scope_setup
