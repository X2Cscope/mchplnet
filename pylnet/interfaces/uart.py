import json
import logging
import serial

from pylnet.interfaces.abstract_interface import InterfaceABC

class LNetSerial(InterfaceABC):
    
    def write(self, data):
        pass

    def read(self):
        pass


def start_serial(
    port_name="COM11",
    baudrate=115200,
    parity=0,
    stop_bits=1,
    data_bits=8,
):
    """
    Set up the serial communication with the provided settings.

    Args:
        port_name (str): Serial port name.
        baudrate (int): Baud rate of the system (bits/sec).
        parity (int): Parity setting.
        stop_bits (int): Number of stop bits.
        data_bits (int): Number of data bits.

    Returns:
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

    parity_value = parity_options.get(parity)
    stop_bits_value = stop_bits_options.get(stop_bits)
    data_bits_value = data_bits_options.get(data_bits)

    if None in [parity_value, stop_bits_value, data_bits_value]:
        raise ValueError("Invalid serial settings provided.")

    try:
        serial_setup = serial.Serial(
            port=port_name,
            baudrate=baudrate,
            parity=parity_value,
            stopbits=stop_bits_value,
            bytesize=data_bits_value,
            write_timeout=1,
            timeout=1,
        )

        request_string = b"\x55\x01\x01\x00\x57"  # fixed string sent to the microcontroller for handshake
        serial_setup.write(request_string)
        response_list = []

        counter = 0
        i = 0
        read_size = 4
        while i < read_size:
            response_list.append(serial_setup.read().hex())
            counter += 1
            if counter == 3:
                read_size = int(response_list[1], 16) + read_size

            i += 1

        if response_list[3] == "00":  # Service ID for device info
            logging.debug("Serial handshake successful.")
            print("handshake successful")
            serial_setup.close()
            return serial.Serial(
                port=port_name,
                baudrate=baudrate,
                parity=parity_value,
                stopbits=stop_bits_value,
                bytesize=data_bits_value,
                write_timeout=1,
                timeout=1,
            )
        else:
            raise Exception("Serial handshake failed.")

    except Exception as e:
        logging.error(f"Error while setting up serial communication: {str(e)}")
        raise

