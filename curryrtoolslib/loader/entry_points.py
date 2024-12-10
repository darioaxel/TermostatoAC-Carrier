
def main_devices():
    from curryrtoolslib.interfaces.devices_interface import DeviceInterface

    iface = DeviceInterface()
    if iface.parse_args():
        iface.execute_actions()

def main_trainning():
    from curryrtoolslib.interfaces.trainning_interface import TrainningInterface

    iface = TrainningInterface()
    if iface.parse_args():
        iface.execute_actions()

