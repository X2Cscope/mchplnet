"""Scope classes needed to implement scope functionality being called under frame_save_parameter"""


from dataclasses import dataclass
from typing import Dict

from mchplnet.services.frame_load_parameter import LoadScopeData


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
    offset: int = 0


@dataclass
class ScopeTrigger:
    """
    Scope trigger configuration.

    Attributes:
        channel: (:func:`ScopeChannel`): the channel to trigger
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

    Attributes:
        scope_state (int): The state of the scope.
        0x02 is Auto without Trigger, 0x01 is Normal with Trigger.
        sample_time_factor (int): Can be used to extend the total sampling time at the cost of sampling resolution.
        channels (List[ScopeChannel]): List of scope channels.
        scope_trigger (ScopeTrigger): The scope trigger configuration (optional).
    """

    def __init__(self):
        self.scope_state = 1
        self.sample_time_factor = 1
        self.channels: Dict[str, ScopeChannel] = {}
        self.scope_trigger = ScopeTrigger()
        self.scope_data = None

    def set_scope_data(self, scope_data: LoadScopeData):
        self.scope_data = scope_data

    def set_sample_time_factor(self, sample_time_factor: int = 1):
        self.sample_time_factor = sample_time_factor

    def set_scope_state(self, scope_state: int = 1):
        self.scope_state = scope_state

    def add_channel(self, channel: ScopeChannel, trigger: bool = False) -> int:
        if channel.name not in self.channels:
            if len(self.channels) > 8:
                return -1
            self.channels[channel.name] = channel
        if trigger:
            self.reset_trigger()
            self.scope_trigger.channel = channel
        return len(self.channels)

    def remove_channel(self, channel_name: str):
        if channel_name in self.channels:
            self.channels.pop(channel_name)
            if self.scope_trigger.channel.name == channel_name:
                self.reset_trigger()

    def get_channel(self, channel_name: str):
        if channel_name in self.channels:
            return self.channels[channel_name]
        return None

    def list_channels(self) -> dict[str, ScopeChannel]:
        return self.channels

    def reset_trigger(self):
        self.scope_trigger = ScopeTrigger()

    def set_trigger(self, scope_trigger: ScopeTrigger):
        self.scope_trigger = scope_trigger

    def _trigger_level_to_bytes(self):
        return self.scope_trigger.trigger_level.to_bytes(
            self.scope_trigger.channel.data_type_size, byteorder="little", signed=True
        )

    def get_dataset_size(self):
        return sum(channel.data_type_size for channel in self.channels.values())

    def _trigger_delay_to_bytes(self):
        sample_number = self.scope_trigger.trigger_delay * self.get_dataset_size()
        return sample_number.to_bytes(length=4, byteorder="little", signed=True)

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
            self._get_trigger_data_type(),
            self.scope_trigger.channel.source_type,
            self.scope_trigger.channel.source_location & 0xFF,
            (self.scope_trigger.channel.source_location >> 8) & 0xFF,
            (self.scope_trigger.channel.source_location >> 16) & 0xFF,
            (self.scope_trigger.channel.source_location >> 24) & 0xFF,
        ]

        buffer.extend(self._trigger_level_to_bytes())
        buffer.extend(self._trigger_delay_to_bytes())
        buffer.extend(
            [self.scope_trigger.trigger_edge, self.scope_trigger.trigger_mode]
        )
        return buffer

    def _get_trigger_data_type(self):
        ret = 0x80  # Bit 7 is always set because of "New Scope Version"
        ret += 0x20 if self.scope_trigger.channel.is_signed else 0
        ret += 0x00 if self.scope_trigger.channel.is_integer else 0x10
        ret += self.scope_trigger.channel.data_type_size  # ._get_width()
        return ret

    def _read_array_chunks(self, chunk_size=253, data_type=1):
        chunks = []

        # Calculate the number of chunks
        num_chunks = self._calc_sda_used_length() // chunk_size

        for i in range(num_chunks):
            # Calculate the starting address for the current chunk
            current_address = self.scope_data.data_array_address + i * chunk_size

            try:
                # Read the chunk of data
                chunk_data = l_net.get_ram_array(
                    address=current_address,
                    data_type=data_type,
                    bytes_to_read=chunk_size,
                )

                # Append the chunk data to the list
                chunks.extend(chunk_data)
            except Exception as e:
                logging.error(f"Error reading chunk {i}: {str(e)}")

        extracted_channels = extract_channels(chunks, channel_config())

        extracted_channel_data = convert_data(
            extracted_channels, variable1.get_width()
        )  # TODO dynamic width
        # values = [int.from_bytes(chunks[i:i + 2], byteorder='little') for i in range(0, len(chunks), variable1._get_width())]
        return extracted_channel_data

    def decode_channels(self):
        self._read_array_chunks()