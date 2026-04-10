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


class FocuserAlpaca(AlpacaClass):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.signals = parent.signals
        self.data = parent.data

    def workerPollData(self) -> None:
        if not self.deviceConnected:
            return
        try:
            self.storePropertyToData(
                self._device.Position, "ABS_FOCUS_POSITION.FOCUS_ABSOLUTE_POSITION"
            )
        except Exception as e:
            self.log.error(f"[{self.deviceName}] Position error: [{e}]")

    def move(self, position: int) -> None:
        if not self.deviceConnected:
            return
        try:
            self._device.Move(position)
        except Exception as e:
            self.log.error(f"[{self.deviceName}] Move error: [{e}]")

    def halt(self) -> None:
        if not self.deviceConnected:
            return
        try:
            self._device.Halt()
        except Exception as e:
            self.log.error(f"[{self.deviceName}] Halt error: [{e}]")
