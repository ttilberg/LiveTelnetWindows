from .LiveTelnet import LiveTelnet

def create_instance(c_instance):
    return LiveTelnet(c_instance)
