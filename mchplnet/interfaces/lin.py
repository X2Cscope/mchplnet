from mchplnet.interfaces.abstract_interface import Interface


class LNetLin(Interface):
    def is_open(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def __init__(self, *args, **kwargs):
        pass

    def write(self, data):
        pass

    def read(self):
        pass
