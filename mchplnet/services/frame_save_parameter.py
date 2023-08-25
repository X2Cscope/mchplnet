import logging
from dataclasses import dataclass
from typing import List

from mchplnet.lnetframe import LNetFrame


@dataclass
class ScopeChannel:
    name: str
    source_type: int
    source_location: int
    data_type_size: int


@dataclass
class ScopeTrigger:
    data_type: int
    source_type: int
    source_location: int
    trigger_level: int
    trigger_delay: int
    trigger_edge: int
    trigger_mode: int


@dataclass
class ScopeConfiguration:
    scope_state: int
    sample_time_factor: int
    channels: List[ScopeChannel]
    trigger: ScopeTrigger = None


class FrameSaveParameter(LNetFrame):
    def __init__(self):
        super().__init__()
        self.address = None
        self.size = None
        self.service_id = 18
        self.unique_ID = 65535
        self.unique_ID = self.unique_ID.to_bytes(length=2, byteorder="little")
        self.scope_config = None

    def _deserialize(self, received: bytearray) -> bytearray:
        data_received = int(received[-2], 16)
        if not data_received == 0:
            return
        logging.info("Error_id : {}".format(self.error_id(data_received)))
        return self.error_id(data_received)

    def _get_data(self):
        """
        Define interface, job of subclass to implement based on the service type

        Returns:
            list: DATA part of the frame
        """
        save_params = [self.service_id, *self.unique_ID]

        if self.scope_config:
            scope_config = self.scope_config
            save_params.append(scope_config.scope_state)
            save_params.append(len(scope_config.channels))

            save_params.append(scope_config.sample_time_factor & 0xFF)
            save_params.append((scope_config.sample_time_factor >> 8) & 0xFF)

            for channel in scope_config.channels:
                save_params.append(channel.source_type)
                save_params.append(channel.source_location & 0xFF)
                save_params.append((channel.source_location >> 8) & 0xFF)
                save_params.append((channel.source_location >> 16) & 0xFF)
                save_params.append((channel.source_location >> 24) & 0xFF)
                save_params.append(channel.data_type_size)

            if scope_config.trigger:
                trigger = scope_config.trigger
                trigger_data_type = ((trigger.data_type & 0x0F) << 4) | 0x80
                save_params.extend([trigger_data_type, trigger.source_type])
                save_params.append(trigger.source_location & 0xFF)
                save_params.append((trigger.source_location >> 8) & 0xFF)
                save_params.append((trigger.source_location >> 16) & 0xFF)
                save_params.append((trigger.source_location >> 24) & 0xFF)
                save_params.append(trigger.trigger_level & 0xFF)
                save_params.append((trigger.trigger_level >> 8) & 0xFF)
                save_params.append(trigger.trigger_delay & 0xFF)
                save_params.append((trigger.trigger_delay >> 8) & 0xFF)
                save_params.append((trigger.trigger_delay >> 16) & 0xFF)
                save_params.append((trigger.trigger_delay >> 24) & 0xFF)
                save_params.append(trigger.trigger_edge)
                save_params.append(trigger.trigger_mode)

        return save_params

    def set_scope_configuration(self, scope_config):
        self.scope_config = scope_config


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

    print(frame._get_data())

    # Remove a channel by name
    frame.remove_channel_by_name("Channel 2")

    # Convert to bytes again after removing a channel
    print(frame._get_data())
