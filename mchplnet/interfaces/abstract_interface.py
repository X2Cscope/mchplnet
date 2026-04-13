"""Abstract base class defining the interface contract for LNet communication."""

from abc import ABC, abstractmethod


class Interface(ABC):
    r"""An abstract base class defining the interface for a generic interface.

    This abstract base class (ABC) defines the methods and attributes that must be implemented by
    concrete interface classes. It serves as a blueprint for creating interface classes for various
    communication protocols.

    The interface provides built-in support for connection validation through a callback mechanism,
    enabling features like automatic COM port detection for serial interfaces.

    Attributes:
        _test_connection_callback (callable): Optional callback function to validate connection.

    Methods:
        __init__(\\*args, \\*\\*kwargs):
            Constructor for the interface. Subclasses should call this method before implementing
            their own constructor.

        __del__():
            Destructor for the interface. Stops the interface when the object is deleted.

        write(data):
            Write data to the interface. Subclasses should implement this method.

        read():
            Read data from the interface. Subclasses should implement this method.

        start():
            Start the interface. Subclasses should call this method after performing startup tasks.
            If a test connection callback is set, it will be called to validate the connection.

        stop():
            Stop the interface. Subclasses should implement this method.

        set_test_connection(callback):
            Set a callback function to validate connections. Used for auto-detection features.

        is_open() -> bool:
            Check if the interface is open and operational. Subclasses should implement this method.

    Example:
        Define a concrete interface class that implements Interface::

            class SerialInterface(Interface):
                def __init__(self, port, baud_rate):
                    # Constructor implementation here
                    super().__init__() # call this method prior to implementing your own constructor

                def write(self, data):
                    # Write data implementation here
                    pass

                def read(self):
                    # Read data implementation here
                    pass

                def start(self):
                    # Start implementation here
                    super().start() # call this method AFTER initialising the interface

                def stop(self):
                    # Stop implementation here
                    pass

                def is_open(self):
                    # is_open implementation here
                    return True
    """

    def __init__(self, *args, **kwargs):
        r"""Constructor for the interface.

        Args:
            *args: Variable-length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            None
        """
        self._test_connection_callback = None
        self.initialised = False

    def __del__(self):
        """Destructor for the interface.

        Stops the interface when the object is deleted.

        Args:
            None

        Returns:
            None
        """
        self.stop()

    @abstractmethod
    def write(self, data: bytearray):
        """Write data to the interface.

        Args:
            data: The data to be written to the interface.

        Returns:
            None
        """
        pass

    @abstractmethod
    def read(self) -> bytearray:
        """Read data from the interface.

        This method includes logic to handle framing, which may be specific to the LNet protocol.

        Returns:
            A bytearray read from the interface or None.
        """
        pass

    def start(self) -> bool:
        """Starts the interface.

        if test_connection is provided, it will be called to validate the connection.
        Any subclass implementing this method should call the super() implementation after
        performing startup tasks.

        Args:
            None

        Returns:
            None
        """
        if self._test_connection_callback and not self.initialised:
            if not self._test_connection_callback():
                return False
        self.initialised = True
        return True

    @abstractmethod
    def stop(self):
        """Stops the interface.

        Args:
            None

        Returns:
            None
        """
        pass

    def set_test_connection(self, callback):
        """Set a callback function to test if connection is valid.

        Used for auto-detection to validate if a port has a valid device connected.

        Args:
            callback (callable): Function that returns True if connection is valid, False otherwise.

        Returns:
            None
        """
        self._test_connection_callback = callback

    @abstractmethod
    def is_open(self) -> bool:
        """Check if the interface is open and operational.

        Args:
            None

        Returns:
            bool: True if the interface is open, False otherwise.
        """
        pass
