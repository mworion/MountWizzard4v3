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

_SHUTTER_STATES = ["Open", "Closed", "Opening", "Closing", "Error"]


class DomeAlpaca(AlpacaClass):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.signals = parent.signals

    def workerGetInitialConfig(self) -> None:
        super().workerGetInitialConfig()
        for attr, key in [
            ("CanSetAltitude", "CanSetAltitude"),
            ("CanSetAzimuth", "CanSetAzimuth"),
            ("CanSetShutter", "CanSetShutter"),
        ]:
            try:
                self.storePropertyToData(getattr(self._device, attr), key)
            except Exception as e:
                self.log.error(f"[{self.deviceName}] {attr} error: [{e}]")
        self.log.debug(f"Initial data: {self.data}")

    def processPolledData(self) -> None:
        azimuth = self.data.get("ABS_DOME_POSITION.DOME_ABSOLUTE_POSITION", 0)
        self.signals.azimuth.emit(azimuth)

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
            azimuth = state["azimuth"] if "azimuth" in state else self._device.Azimuth
            self.storePropertyToData(azimuth, "ABS_DOME_POSITION.DOME_ABSOLUTE_POSITION")
            self.signals.azimuth.emit(azimuth)
        except Exception as e:
            self.log.error(f"[{self.deviceName}] Azimuth error: [{e}]")

        try:
            slewing = state["slewing"] if "slewing" in state else self._device.Slewing
            self.storePropertyToData(slewing, "Slewing")
        except Exception as e:
            self.log.error(f"[{self.deviceName}] Slewing error: [{e}]")

        try:
            shutter = (
                state["shutterstatus"]
                if "shutterstatus" in state
                else self._device.ShutterStatus
            )
            if shutter == 0:
                self.storePropertyToData(_SHUTTER_STATES[0], "Status.Shutter")
                self.storePropertyToData(True, "DOME_SHUTTER.SHUTTER_OPEN")
                self.storePropertyToData(False, "DOME_SHUTTER.SHUTTER_CLOSED")
            elif shutter == 1:
                self.storePropertyToData(_SHUTTER_STATES[1], "Status.Shutter")
                self.storePropertyToData(False, "DOME_SHUTTER.SHUTTER_OPEN")
                self.storePropertyToData(True, "DOME_SHUTTER.SHUTTER_CLOSED")
            else:
                self.data["DOME_SHUTTER.SHUTTER_OPEN"] = None
                self.data["DOME_SHUTTER.SHUTTER_CLOSED"] = None
        except Exception as e:
            self.log.error(f"[{self.deviceName}] ShutterStatus error: [{e}]")

    def slewToAltAz(self, altitude: float, azimuth: float) -> None:
        if not self.deviceConnected:
            return
        if self.data.get("CanSetAzimuth"):
            try:
                self._device.SlewToAzimuth(azimuth)
            except Exception as e:
                self.log.error(f"[{self.deviceName}] SlewToAzimuth error: [{e}]")
        if self.data.get("CanSetAltitude"):
            try:
                self._device.SlewToAltitude(altitude)
            except Exception as e:
                self.log.error(f"[{self.deviceName}] SlewToAltitude error: [{e}]")

    def openShutter(self) -> None:
        if not self.deviceConnected:
            return
        if self.data.get("CanSetShutter"):
            try:
                self._device.OpenShutter()
            except Exception as e:
                self.log.error(f"[{self.deviceName}] OpenShutter error: [{e}]")

    def closeShutter(self) -> None:
        if not self.deviceConnected:
            return
        if self.data.get("CanSetShutter"):
            try:
                self._device.CloseShutter()
            except Exception as e:
                self.log.error(f"[{self.deviceName}] CloseShutter error: [{e}]")

    def slewCW(self) -> None:
        pass

    def slewCCW(self) -> None:
        pass

    def abortSlew(self) -> None:
        if not self.deviceConnected:
            return
        try:
            self._device.AbortSlew()
        except Exception as e:
            self.log.error(f"[{self.deviceName}] AbortSlew error: [{e}]")
