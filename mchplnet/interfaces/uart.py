import logging

import serial
from mchplnet.interfaces.abstract_interface import InterfaceABC


class LNetSerial(InterfaceABC):
    def __init__(self, *args, **kwargs):
        self.com_port = kwargs["port"] if "port" in kwargs else "COM11"
        self.baud_rate = kwargs["baud_rate"] if "baud_rate" in kwargs else 115200
        self.parity = kwargs["parity"] if "parity" in kwargs else 0
        self.stop_bit = kwargs["stop_bit"] if "stop_bit" in kwargs else 1
        self.data_bits = kwargs["data_bits"] if "data_bits" in kwargs else 8
        self.serial = None
        self.start()

    def start(self):
        """
        set up the serial communication with the provided settings.

        Args:
            self.com_port (str): Serial port name.
            self.baud-rate (int): Baud rate of the system (bits/sec).
            self.parity (int): Parity setting.
            self.stop_bits (int): Number of stop bits.
            self.data_bits (int): Number of data bits.

        returns:
            serial.Serial: Initialized serial object for communication.

        Raises:
            ValueError: If the provided settings are invalid.
        """
        parity_options = {
            0: serial.PARITY_NONE,
            2: serial.PARITY_EVEN,
            3: serial.PARITY_ODD,
            4: serial.PARITY_SPACE,
            5: serial.PARITY_MARK,
        }
        stop_bits_options = {
            1: serial.STOPBITS_ONE,
            2: serial.STOPBITS_TWO,
            3: serial.STOPBITS_ONE_POINT_FIVE,
        }
        data_bits_options = {
            5: serial.FIVEBITS,
            6: serial.SIXBITS,
            7: serial.SEVENBITS,
            8: serial.EIGHTBITS,
        }

        parity_value = parity_options.get(self.parity)
        stop_bits_value = stop_bits_options.get(self.stop_bit)
        data_bits_value = data_bits_options.get(self.data_bits)

        if None in [parity_value, stop_bits_value, data_bits_value]:
            raise ValueError("Invalid serial settings provided.")

        try:
            self.serial = serial.Serial(
                port=self.com_port,
                baudrate=self.baud_rate,
                parity=parity_value,
                stopbits=stop_bits_value,
                bytesize=data_bits_value,
                write_timeout=1,
                timeout=1,
            )
        except Exception as e:
            logging.debug(e)

    def stop(self):
        self.serial.close()

    def write(self, data):
        self.serial.write(data)

    def is_open(self):
        return self.serial.is_open

    def read(self):
        response_list = []
        counter = 0
        i = 0
        read_size = 4
        while i < read_size:
            byte = self.serial.read().hex()  # Get in hex
            response_list.append(byte)
            counter += 1
            if counter == 3:
                read_size = int(response_list[1], 16) + read_size
            if i == 0:
                pass
            elif byte == "55" or byte == "02":
                read_size += 1
            i += 1
        if response_list:
            return response_list
        else:
            return None
