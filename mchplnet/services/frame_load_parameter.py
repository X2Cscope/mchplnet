from dataclasses import dataclass

from mchplnet.lnetframe import LNetFrame


@dataclass
class LoadScopeData:
    scope_state: int  # Value = 0 Scope is idle and if Value > 0 Scope is busy
    num_channels: int  # The number of active channels, max 8 channel
    sample_time_factor: int  # 0 means to sample data at every Update function call. Value 1 means to sample every 2nd...
    data_array_pointer: int  # This value is for debug purposes only. It points to the next free location in the Scope Data Array for the next dataset to be stored. This value is an index, not a memory address.
    data_array_address: int  # This value contains the memory address of the Scope Data Array.
    trigger_delay: int  # This is the current trigger delay value.
    trigger_event_position: int
    data_array_used_length: int
    data_array_size: int
    scope_version: int


class FrameLoadParameter(LNetFrame):
    def __init__(self):
        super().__init__()
        self.address = None
        self.size = None
        self.service_id = 17
        self.unique_parameter = 1

    def _deserialize(self, received):
        data_bytes = bytes.fromhex("".join(received[5:-1]))
        # Defining the data structure based on size
        data_structure = [
            ("scope_state", 1),
            ("num_channels", 1),
            ("sample_time_factor", 2),
            ("data_array_pointer", 4),
            ("data_array_address", 4),
            ("trigger_delay", 4),
            ("trigger_event_position", 4),
            ("data_array_used_length", 4),
            ("data_array_size", 4),
            ("scope_version", 1),
        ]

        # Helper function to extract data
        def extract_data(start, field_size):
            return int.from_bytes(
                data_bytes[start : start + field_size], byteorder="little", signed=False
            )

        # Extract data according to the data structure
        extracted_data = {}
        start_pos = 0
        for field, size in data_structure:
            extracted_data[field] = extract_data(start_pos, size)
            start_pos += size

        # Create and return the ScopeData instance
        return LoadScopeData(**extracted_data)

    def _get_data(self):
        """
        Define interface, job of subclass to implement based on the service type

        Returns:
            list: DATA part of the frame
        """
        self.unique_parameter = self.unique_parameter.to_bytes(
            length=2, byteorder="little"
        )
        data = [*self.unique_parameter]
        return [self.service_id, *data]
