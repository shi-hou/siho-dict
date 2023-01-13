from pyqt5Custom import ToggleSwitch


class ISwitch(ToggleSwitch):
    def __init__(self, text="", on=False):
        super().__init__(text, "ios", on)
