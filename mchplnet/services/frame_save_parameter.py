"""
this framework is responsible to set up the configuration for scope functionality.
ensures, trigger configuration as well as adding and removing a channel from the scope.

"""
import logging
from itertools import chain
from typing import Dict

logging.basicConfig(
    level=logging.DEBUG,
    filename="Scope_save_parameter.log",
)
from dataclasses import dataclass
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
    source_type: int = 0
    is_integer: bool = False
    is_signed: bool = True
    is_enable: bool = True


@dataclass
class ScopeTrigger:
    """
    represents a scope trigger configuration.

    attributes:
        channel: ScopeChannel: Scope channel consist of :
        (name: str
        source_location: int
        data_type_size: int
        source_type: int = 0
        is_integer: bool = False
        is_signed: bool = True
        is_enable: bool = True)
        #TODO add link to the class ScopeChannel

        trigger_level (int): The trigger level.
        trigger_delay (int): The trigger delay.
        trigger_edge (int): For Rising Edge, set the value to 0x01 and for falling 0x00
        trigger_mode (int): The trigger mode.
    """

    channel: ScopeChannel = None
    trigger_level: int = 0
    trigger_delay: int = 0
    trigger_edge: int = 1
    trigger_mode: int = 0


class ScopeSetup:
    """
    represents a scope configuration.

    attributes:
        scope_state (int): The state of the scope.
        0x02 is Auto without Trigger, 0x01 is Normal with Trigger.
        sample_time_factor (int): Can be used to extend the total sampling time at the cost of sampling resolution.
        channels (List[ScopeChannel]): List of scope channels.
        trigger (ScopeTrigger): The scope trigger configuration (optional).
    """

    def __init__(self):
        self.scope_state = 1
        self.sample_time_factor = 1
        self.channels: Dict[str, ScopeChannel] = {}
        self.scope_trigger = ScopeTrigger()

    def set_sample_time_factor(self, sample_time_factor: int = 1):
        self.sample_time_factor = sample_time_factor

    def set_scope_state(self, scope_state: int = 1):
        self.scope_state = scope_state

    def add_channel(self, channel: ScopeChannel, trigger: bool= False) -> int:
        if channel.name in self.channels:
            return len(self.channels)
        if len(self.channels) > 8:
            return -1
        self.channels[channel.name] = channel
        return len(self.channels)

    def remove_channel(self, channel_name: str):
        if channel_name in self.channels:
            self.channels.pop(channel_name)

    def get_channel(self, channel_name: str):
        if channel_name in self.channels:
            return self.channels[channel_name]
        return None

    def list_channels(self) -> dict:
        return self.channels

    def reset_trigger(self):
        self.scope_trigger = ScopeTrigger()

    def set_trigger(self, channel: ScopeChannel, trigger_level: int, trigger_mode: int, trigger_delay: int,
                    trigger_edge: int):
        if channel is None:
            return False
        self.scope_trigger = ScopeTrigger(
            channel=channel,
            trigger_level=trigger_level,
            trigger_delay=trigger_delay,
            trigger_edge=trigger_edge,
            trigger_mode=trigger_mode
        )
        return True

    def get_buffer(self):
        if not self.channels:
            return []

        buffer = [
            self.scope_state,
            len(self.channels),
            self.sample_time_factor & 0xFF,
            (self.sample_time_factor >> 8) & 0xFF,
        ]

        for channel_name, channel in self.channels.items():
            if not channel.is_enable:
                continue
            buffer.append(channel.source_type)
            buffer.append(channel.source_location & 0xFF)
            buffer.append((channel.source_location >> 8) & 0xFF)
            buffer.append((channel.source_location >> 16) & 0xFF)
            buffer.append((channel.source_location >> 24) & 0xFF)
            buffer.append(channel.data_type_size)

        buffer.extend(self._get_scope_trigger_buffer())  # add scope trigger
        return buffer

    def _get_scope_trigger_buffer(self):
        buffer = [
            self.create_trigger_data_type(),
            self.scope_trigger.channel.source_type,
            self.scope_trigger.channel.source_location & 0xFF,
            (self.scope_trigger.channel.source_location >> 8) & 0xFF,
            (self.scope_trigger.channel.source_location >> 16) & 0xFF,
            (self.scope_trigger.channel.source_location >> 24) & 0xFF,
            self.scope_trigger.trigger_level & 0xFF,
            (self.scope_trigger.trigger_level >> 8) & 0xFF,
            (self.scope_trigger.trigger_level >> 16) & 0xFF,
            (self.scope_trigger.trigger_level >> 24) & 0xFF,
            self.scope_trigger.trigger_delay & 0xFF,
            (self.scope_trigger.trigger_delay >> 8) & 0xFF,
            (self.scope_trigger.trigger_delay >> 16) & 0xFF,
            (self.scope_trigger.trigger_delay >> 24) & 0xFF,
            self.scope_trigger.trigger_edge,
            self.scope_trigger.trigger_mode,
        ]
        return buffer

    def create_trigger_data_type(self):
        ret = 0x80  # Bit 7 is always set because of "New Scope Version"
        ret += 0x20 if self.scope_trigger.channel.is_signed else 0
        ret += 0x00 if self.scope_trigger.channel.is_integer else 0x10
        ret += self.scope_trigger.channel.data_type_size  # ._get_width()
        return ret


# def get_trigger(self):


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
        self.scope_setup = ScopeSetup()  # only need getter,
        # as its been already initiated at this point and we just use a pointer.

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
        save_params.extend(self.scope_setup.get_buffer())
        return save_params

    # def create_trigger_data_type(self, variable: Variable):
    #     ret = 0x80  # Bit 7 is always set because of "New Scope Version"
    #     ret += 0x20 if variable.is_signed() else 0
    #     ret += 0x00 if variable.is_integer() else 0x10
    #     ret += variable._get_width()
    #     return ret

    def set_scope_configuration(self, scope_config: ScopeSetup):
        """
        Set the scope configuration for the frame.

        Args:
            scope_config (ScopeSetup): The scope configuration to be set.
        """
        self.scope_setup = scope_config

    def remove_channel_by_name(self, channel_name: str):
        """
        Remove a channel from the scope configuration by its name.

        Args:
            channel_name (str): The name of the channel to be removed.
        """
        if self.scope_setup:
            self.scope_setup.channels = [
                channel
                for channel in self.scope_setup.channels
                if channel.name != channel_name
            ]

    def add_channels(self, scope_config, *args):
        self.scope_setup = scope_config
        for variable in args:
            self.scope_setup.channels.append(self.create_scope_channel(variable))

    # @staticmethod
    # def create_scope_channel(variable: Variable):
    #     return ScopeChannel(
    #         name=variable.name,
    #         source_location=variable.address,
    #         data_type_size=variable._get_width(),
    #         source_type=0,
    #     )


if __name__ == "__main__":
    frame = FrameSaveParameter()

    # Set up scope configuration
    scope_config = ScopeSetup(scope_state=0x01, sample_time_factor=10, channels=[])

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
    scope_config.scope_trigger = ScopeTrigger(
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
