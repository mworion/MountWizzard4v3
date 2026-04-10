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

_COVER_STATES = ["NotPresent", "Closed", "Moving", "Open", "Unknown", "Error"]


class CoverAlpaca(AlpacaClass):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent = parent
        self.alpacaSignals = parent.signals
        self.data = parent.data

    def workerPollData(self) -> None:
        if not self.deviceConnected:
            return

        # Priority 2: single DeviceState call → N properties in one round-trip
        try:
            raw = self._device.DeviceState
            state = {sv["Name"].lower(): sv["Value"] for sv in raw}
        except Exception:
            state = {}

        try:
            cover_state = (
                state["coverstate"] if "coverstate" in state else self._device.CoverState
            )
            state_text = _COVER_STATES[cover_state] if 0 <= cover_state < len(
                _COVER_STATES
            ) else "Unknown"
            self.storePropertyToData(state_text, "Status.Cover")
        except Exception as e:
            self.log.error(f"[{self.deviceName}] CoverState error: [{e}]")

        try:
            brightness = (
                state["brightness"] if "brightness" in state else self._device.Brightness
            )
            self.storePropertyToData(
                brightness, "FLAT_LIGHT_INTENSITY.FLAT_LIGHT_INTENSITY_VALUE"
            )
        except Exception as e:
            self.log.error(f"[{self.deviceName}] Brightness error: [{e}]")

        try:
            max_brightness = (
                state["maxbrightness"]
                if "maxbrightness" in state
                else self._device.MaxBrightness
            )
            self.storePropertyToData(
                max_brightness, "FLAT_LIGHT_INTENSITY.FLAT_LIGHT_INTENSITY_MAX"
            )
        except Exception as e:
            self.log.error(f"[{self.deviceName}] MaxBrightness error: [{e}]")

    def closeCover(self) -> None:
        if not self.deviceConnected:
            return
        try:
            self._device.CloseCover()
        except Exception as e:
            self.log.error(f"[{self.deviceName}] CloseCover error: [{e}]")

    def openCover(self) -> None:
        if not self.deviceConnected:
            return
        try:
            self._device.OpenCover()
        except Exception as e:
            self.log.error(f"[{self.deviceName}] OpenCover error: [{e}]")

    def haltCover(self) -> None:
        if not self.deviceConnected:
            return
        try:
            self._device.HaltCover()
        except Exception as e:
            self.log.error(f"[{self.deviceName}] HaltCover error: [{e}]")

    def lightOn(self) -> None:
        if not self.deviceConnected:
            return
        max_brightness = self.app.cover.data.get(
            "FLAT_LIGHT_INTENSITY.FLAT_LIGHT_INTENSITY_MAX", 255
        )
        brightness = int(max_brightness / 2)
        try:
            self._device.CalibratorOn(brightness)
        except Exception as e:
            self.log.error(f"[{self.deviceName}] CalibratorOn error: [{e}]")

    def lightOff(self) -> None:
        if not self.deviceConnected:
            return
        try:
            self._device.CalibratorOff()
        except Exception as e:
            self.log.error(f"[{self.deviceName}] CalibratorOff error: [{e}]")

    def lightIntensity(self, value: float) -> None:
        if not self.deviceConnected:
            return
        try:
            self._device.CalibratorOn(int(value))
        except Exception as e:
            self.log.error(f"[{self.deviceName}] CalibratorOn error: [{e}]")
