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


class TelescopeAlpaca(AlpacaClass):
    """ """

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.signals = parent.signals
        self.data = parent.data

    def workerGetInitialConfig(self) -> None:
        super().workerGetInitialConfig()
        try:
            self.storePropertyToData(
                self._device.ApertureDiameter, "TELESCOPE_INFO.TELESCOPE_APERTURE"
            )
        except Exception as e:
            self.log.error(f"[{self.deviceName}] ApertureDiameter error: [{e}]")
        try:
            self.storePropertyToData(
                self._device.FocalLength, "TELESCOPE_INFO.TELESCOPE_FOCAL_LENGTH"
            )
        except Exception as e:
            self.log.error(f"[{self.deviceName}] FocalLength error: [{e}]")
