from abc import ABC, abstractmethod


class InterfaceABC(ABC):
    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    def __del__(self):
        self.stop()

    @abstractmethod
    def write(self, data):
        pass

    @abstractmethod
    def read(self):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def is_open(self):
        pass
