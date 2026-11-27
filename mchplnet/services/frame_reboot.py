"""Frame implementation of the LNet Reboot service (0x19)."""

from mchplnet.lnetframe import LNetFrame


class FrameReboot(LNetFrame):
    """Reboot request (LNet service 0x19). Inherits from LNetFrame.

    Used to reset the device. Request and response have no service data. A device that executes the
    reset does not answer; a response therefore only carries an error ID (see LNet.reset_device()).
    """

    def __init__(self):
        """Initialize the FrameReboot class."""
        super().__init__()
        self.service_id = 0x19

    def _get_data(self):
        self.data.append(self.service_id)

    def _deserialize(self):
        """Deserialization of bytes received from device.

        Nothing to do: there is no service data, and the error and service IDs have already been checked
        by the superclass.
        """
        pass
