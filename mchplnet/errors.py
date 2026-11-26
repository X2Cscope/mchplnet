"""Exceptions and error identifiers of the LNet protocol.

Error IDs are those of LNet v5 and v6 (LCM) plus the X2Cscope extensions, see
X2Cscope_library_make doc/lnet/x2cscope_lnet_profile.md, section 8.
"""

ERROR_DESCRIPTIONS = {
    0x00: "No error",
    0x13: "Checksum error",
    0x14: "Format error",
    0x15: "Size too large",
    0x21: "Service not available",
    0x22: "Invalid DSP state",
    0x23: "Invalid data type",
    0x24: "Scope busy",
    0x30: "Flash write error",
    0x31: "Flash write protect error",
    0x32: "Flash erase error",
    0x33: "Flash address alignment error",
    0x34: "Flash data error",
    0x40: "Invalid parameter ID",
    0x41: "Invalid block ID",
    0x42: "Parameter limit error",
    0x43: "Parameter table not initialized",
    0x44: "Function table not initialized",
    0x45: "Inport parameter table not initialized",
    0x46: "Outport parameter table not initialized",
    0x47: "Mask parameter table not initialized",
    0x48: "Save mask parameter error",
    0x49: "Load mask parameter error",
    0x50: "Power-on error",
    0xFF: "Unknown error",
}

SERVICE_NAMES = {
    0x00: "Get Device Info",
    0x01: "Get Target State",
    0x02: "Set Target State",
    0x04: "Erase Flash",
    0x07: "Get Block Data",
    0x08: "Put Block Data",
    0x09: "Get RAM Block",
    0x0A: "Put RAM Block",
    0x0B: "Get Flash Block",
    0x0C: "Put Flash Block",
    0x11: "Load Parameter",
    0x12: "Save Parameter",
    0x16: "Stream Control",
    0x19: "Reboot",
}


def error_description(error_id: int) -> str:
    """Return the description of an LNet error ID, also for unknown IDs."""
    return ERROR_DESCRIPTIONS.get(error_id, f"Unknown error ID 0x{error_id:02X}")


def service_name(service_id) -> str:
    """Return the name of an LNet service ID, also for unknown or missing IDs."""
    if service_id is None:
        return "unknown service"
    return f"0x{service_id:02X} ({SERVICE_NAMES.get(service_id, 'unknown service')})"


class LNetError(Exception):
    """Base class of all LNet protocol errors."""


class LNetFrameError(LNetError):
    """The response frame is invalid: checksum error, wrong length or unexpected service ID."""


class LNetDeviceError(LNetError):
    """The device answered the request with an error ID.

    Attributes:
        service_id (int): Service ID of the request.
        error_id (int): Error ID sent by the device.
    """

    def __init__(self, service_id: int, error_id: int):
        """Create the exception from the request's service ID and the device's error ID."""
        self.service_id = service_id
        self.error_id = error_id
        super().__init__(
            f"Device answered service {service_name(service_id)} with error "
            f"0x{error_id:02X} ({error_description(error_id)})"
        )

    @property
    def description(self) -> str:
        """Return the description of the error ID."""
        return error_description(self.error_id)
