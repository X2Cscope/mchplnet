"""LNet TCP Server Example

This module implements a simple TCP server that simulates an LNet device
for testing and development purposes. It responds to device info and
parameter loading requests using the LNet protocol.

Usage:
    python tcp_server.py

The server will start listening on port 12666 and respond to LNet protocol
requests from X2CScope clients.
"""

import socket

def calc_checksum(frame_bytes):
    """Calculate checksum for LNet frame.
    
    Args:
        frame_bytes (bytes): Frame data to checksum
        
    Returns:
        int: Checksum value (0-255)
    """
    return sum(frame_bytes) & 0xFF

def make_deviceinfo_response(slave_id=0x01, device_id=0x8240):
    """Create a device info response packet.
    
    Args:
        slave_id (int): Slave ID for the device (default: 0x01)
        device_id (int): Device ID (default: 0x8240)
        
    Returns:
        bytes: Device info response packet
    """
    response = bytearray(b'U.\x01\x00\x00\x05\x00\x01\x00\xff@\x82Nov1920251028\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\xfcT\x00\x00\xcd')
    return bytes(response)

def make_loadparameter_response():
    """Create a load parameter response packet.
    
    Returns:
        bytearray: Load parameter response packet
    """
    # Your provided response
    resp = bytearray(b'U\x1f\x01\x11\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1e@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x88\x13\x00\x00\x88\x13\x00\x00\x82\x9c')
    return resp

def is_deviceinfo_request(data, slave_id=0x01):
    """Check if received data is a device info request.
    
    Args:
        data (bytes): Received data packet
        slave_id (int): Expected slave ID (default: 0x01)
        
    Returns:
        bool: True if this is a valid device info request
    """
    return (
        len(data) == 5 and
        data[0] == 0x55 and
        data[1] == 0x01 and
        data[2] == slave_id and
        data[3] == 0x00
    )

def is_loadparameter_request(data, slave_id=0x01):
    """Check if received data is a load parameter request.
    
    Args:
        data (bytes): Received data packet
        slave_id (int): Expected slave ID (default: 0x01)
        
    Returns:
        bool: True if this is a valid load parameter request
    """
    return (
        len(data) == 7 and
        data[0] == 0x55 and
        data[1] == 0x03 and
        data[2] == slave_id and
        data[3] == 0x11
    )

def run_server(port=12666, slave_id=0x01, device_id=0x8240):
    """Run the LNet TCP server.
    
    This server listens for incoming TCP connections and responds to
    LNet protocol requests for device info and parameter loading.
    
    Args:
        port (int): Port to listen on (default: 12666)
        slave_id (int): Slave ID for the device (default: 0x01)
        device_id (int): Device ID (default: 0x8240)
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', port))
        s.listen(1)
        print(f"LNet TCP server running on port {port}...")
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                while True:
                    data = conn.recv(64)
                    if not data:
                        break
                    if is_deviceinfo_request(data, slave_id):
                        resp = make_deviceinfo_response(slave_id, device_id)
                        conn.sendall(resp)
                    elif is_loadparameter_request(data, slave_id):
                        resp = make_loadparameter_response()
                        conn.sendall(resp)
                    else:
                        print(f"Unknown request: {data.hex()}")

if __name__ == "__main__":
    # Run the server with default settings
    # Port: 12666, Slave ID: 0x01, Device ID: 0x8240 (dsPIC33AK)
    run_server()




