from pylnet.pylnet.interfaces.abstract_interface import InterfaceABC


class LNetTcpIp(InterfaceABC):

    def start(self):
        pass

    def stop(self):
        pass

    def __init__(self, params=dict):
        pass

    def write(self, data):
        pass

    def read(self):
        pass
