import serial
from abc import ABC, abstractmethod

class InterfaceABC(ABC):

    @abstractmethod
    def __init__(self, iface: serial.Serial):
        
        pass
        
    @abstractmethod
    def write(self, data):
        pass
        
    @abstractmethod
    def read(self):
        pass    
        
