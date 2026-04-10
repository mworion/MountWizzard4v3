############################################################
#
#       #   #  #   #   #    #
#      ##  ##  #  ##  #    #
#     # # # #  # # # #    #  #
#    #  ##  #  ##  ##    ######
#   #   #   #  #   #       #
#
# Python-based Tool for interaction with the 10_micron mounts
# GUI with PySide
#
# written in python3, (c) 2019-2026 by mworion
# Licence APL2.0
#
###########################################################
from mw4.base.alpacaClass import AlpacaClass


class FilterAlpaca(AlpacaClass):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.signals = parent.signals
        self.data = parent.data

    def workerGetInitialConfig(self) -> None:
        super().workerGetInitialConfig()
        try:
            names = self._device.Names
        except Exception as e:
            self.log.error(f"[{self.deviceName}] Names error: [{e}]")
            return
        if names is None:
            return
        for i, name in enumerate(names):
            if name is None:
                continue
            self.data[f"FILTER_NAME.FILTER_SLOT_NAME_{i:1.0f}"] = name

    def workerPollData(self) -> None:
        if not self.deviceConnected:
            return
        try:
            position = self._device.Position
        except Exception as e:
            self.log.error(f"[{self.deviceName}] Position error: [{e}]")
            return
        if position == -1 or position is None:
            return
        self.storePropertyToData(position, "FILTER_SLOT.FILTER_SLOT_VALUE")

    def sendFilterNumber(self, filterNumber: int = 0) -> None:
        if not self.deviceConnected:
            return
        try:
            self._device.Position = filterNumber
        except Exception as e:
            self.log.error(f"[{self.deviceName}] set Position error: [{e}]")
