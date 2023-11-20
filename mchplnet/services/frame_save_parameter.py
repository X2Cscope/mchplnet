"""
this framework is responsible to set up the configuration for scope functionality.
ensures, trigger configuration as well as adding and removing a channel from the scope.

"""
import logging

from parser.Elf_Parser import VariableInfo
from pyx2cscope.variable.variable import Variable

logging.basicConfig(
    level=logging.DEBUG,
    filename="save_prarameter.log",
)
from dataclasses import dataclass
from typing import List
from mchplnet.lnetframe import LNetFrame


@dataclass
class ScopeChannel:
    """
    represents a scope channel configuration.

    attributes:
        name (str): The name of the channel.
        source_type (int): The source type of the channel.
        source_location (int): The source location of the channel.
        data_type_size (int): The size of the data type used by the channel.
    """
    name: str
    source_location: int
    data_type_size: int
    source_type: int = 0  # set default to 0


@dataclass
class ScopeTrigger:
    """
    Represents a scope trigger configuration.

    Attributes:
        data_type (int): The data type of the trigger.
        source_type (int): The source type of the trigger.
        source_location (int): The source location of the trigger.
        trigger_level (int): The trigger level.
        trigger_delay (int): The trigger delay.
        trigger_edge (int): For Rising Edge, set the value to 0x01 and for falling 0x00
        trigger_mode (int): The trigger mode.
    """
    variable: Variable
    data_type: int
    source_type: int
    source_location: int
    trigger_level: int
    trigger_delay: int
    trigger_edge: int
    trigger_mode: int


@dataclass
class ScopeConfiguration:
    """
    represents a scope configuration.

    attributes:
        scope_state (int): The state of the scope. 0x02 is Auto without Trigger, 0x01 is Normal, with Trigger.
        sample_time_factor (int): Can be used to extend the total sampling time at the cost of sampling resolution.
        channels (List[ScopeChannel]): List of scope channels.
        trigger (ScopeTrigger): The scope trigger configuration (optional).
    """
    scope_state: int
    sample_time_factor: int
    channels: List[ScopeChannel]
    trigger: ScopeTrigger = None


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
        self.scope_config = None

    def _deserialize(self, received: bytearray) -> bytearray | None:
        """
        Deserialize the frame data.

        Args:
            received (bytearray): The received data.

        Returns:
            bytearray | None: The deserialized data or None in case of error.
        """
        data_received = int(received[-2], 16)
        if not data_received == 0:
            return
        logging.info("Error_id : {}".format(self.error_id(data_received)))
        return self.error_id(data_received)

    def _get_data(self) -> list:
        """
        Define the interface to get frame data.

        Returns:
            list: DATA part of the frame.
        """
        save_params = [self.service_id, *self.unique_ID]

        if self.scope_config:
            save_params.append(self.scope_config.scope_state)
            save_params.append(len(self.scope_config.channels))

            save_params.append(self.scope_config.sample_time_factor & 0xFF)
            save_params.append((self.scope_config.sample_time_factor >> 8) & 0xFF)
            for channel in self.scope_config.channels:
                save_params.append(channel.source_type)
                save_params.append(channel.source_location & 0xFF)
                save_params.append((channel.source_location >> 8) & 0xFF)
                save_params.append((channel.source_location >> 16) & 0xFF)
                save_params.append((channel.source_location >> 24) & 0xFF)
                save_params.append(channel.data_type_size)

            if self.scope_config.trigger:
                trigger = self.scope_config.trigger
                # trigger_data_type = ((trigger.data_type & 0x0F) << 4) | 0x80

                save_params.append(self.create_data_type(trigger.variable))
                save_params.append(trigger.source_type)
                save_params.append(trigger.source_location & 0xFF)
                save_params.append((trigger.source_location >> 8) & 0xFF)
                save_params.append((trigger.source_location >> 16) & 0xFF)
                save_params.append((trigger.source_location >> 24) & 0xFF)
                save_params.append(trigger.trigger_level & 0xFF)
                save_params.append((trigger.trigger_level >> 8) & 0xFF)
                save_params.append((trigger.trigger_level >> 16) & 0xFF)
                save_params.append((trigger.trigger_level >> 24) & 0xFF)
                save_params.append(trigger.trigger_delay & 0xFF)
                save_params.append((trigger.trigger_delay >> 8) & 0xFF)
                save_params.append((trigger.trigger_delay >> 16) & 0xFF)
                save_params.append((trigger.trigger_delay >> 24) & 0xFF)
                save_params.append(trigger.trigger_edge)
                save_params.append(trigger.trigger_mode)

        return save_params

    def create_data_type(self, variable: Variable):
        ret = 0x80  # Bit 7 is always set because of "New Scope Version"
        ret += 0x20 if variable.is_signed() else 0
        ret += 0x00 if variable.is_integer() else 0x10
        ret += variable._get_width()
        return ret

    def set_scope_configuration(self, scope_config: ScopeConfiguration):
        """
        Set the scope configuration for the frame.

        Args:
            scope_config (ScopeConfiguration): The scope configuration to be set.
        """
        self.scope_config = scope_config

    def remove_channel_by_name(self, channel_name: str):
        """
        Remove a channel from the scope configuration by its name.

        Args:
            channel_name (str): The name of the channel to be removed.
        """
        if self.scope_config:
            self.scope_config.channels = [
                channel for channel in self.scope_config.channels if channel.name != channel_name
            ]

    def add_channels(self, scope_config, *args):
        self.scope_config = scope_config
        for variable in args:
            self.scope_config.channels.append(self.create_scope_channel(variable))

    @staticmethod
    def create_scope_channel(variable: Variable):
        return ScopeChannel(
            name=variable.name,
            source_location=variable.address,
            data_type_size=variable._get_width(),
            source_type=0,
        )


if __name__ == "__main__":
    frame = FrameSaveParameter()

    # Set up scope configuration
    scope_config = ScopeConfiguration(
        scope_state=0x01, sample_time_factor=10, channels=[]
    )

    # Add channels to the scope configuration
    scope_config.channels.append(
        ScopeChannel(
            name="Channel 1",
            source_type=0x00,
            source_location=0xDEADCAFE,
            data_type_size=4,
        )
    )
    scope_config.channels.append(
        ScopeChannel(
            name="Channel 2",
            source_type=0x00,
            source_location=0x8899AABB,
            data_type_size=2,
        )
    )

    # Set up trigger configuration
    scope_config.trigger = ScopeTrigger(
        data_type=4,
        source_type=0x00,
        source_location=0x12345678,
        trigger_level=70000,
        trigger_delay=600,
        trigger_edge=0x00,
        trigger_mode=0x01,
    )

    # Set the scope configuration in the frame
    frame.set_scope_configuration(scope_config)

    logging.debug(frame._get_data())

    # Remove a channel by name
    # frame.remove_channel_by_name("Channel 2")

    # Convert to bytes again after removing a channel
    logging.debug(frame._get_data())
    print(frame._get_data())
