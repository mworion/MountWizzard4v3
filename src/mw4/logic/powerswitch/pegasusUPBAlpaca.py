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


class PegasusUPBAlpaca(AlpacaClass):
    """ """

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.signals = parent.signals
        self.data = parent.data

    def _getSwitch(self, i: int) -> bool | None:
        try:
            return self._device.GetSwitch(i)
        except Exception as e:
            self.log.error(f"[{self.deviceName}] GetSwitch({i}) error: [{e}]")
            return None

    def _getSwitchValue(self, i: int) -> float | None:
        try:
            return self._device.GetSwitchValue(i)
        except Exception as e:
            self.log.error(f"[{self.deviceName}] GetSwitchValue({i}) error: [{e}]")
            return None

    def _setSwitchValue(self, i: int, value: float) -> None:
        try:
            self._device.SetSwitchValue(i, value)
        except Exception as e:
            self.log.error(f"[{self.deviceName}] SetSwitchValue({i}) error: [{e}]")

    def _getMaxSwitch(self) -> int | None:
        try:
            return self._device.MaxSwitch
        except Exception as e:
            self.log.error(f"[{self.deviceName}] MaxSwitch error: [{e}]")
            return None

    def workerPollData(self) -> None:
        if not self.deviceConnected:
            return

        maxSwitch = self._getMaxSwitch()
        if maxSwitch is None:
            return

        model = "UPB" if maxSwitch == 15 else "UPBv2"
        self.data["FIRMWARE_INFO.VERSION"] = "1.4" if model == "UPB" else "2.1"

        if model == "UPB":
            self.storePropertyToData(self._getSwitch(0), "POWER_CONTROL.POWER_CONTROL_1")
            self.storePropertyToData(self._getSwitch(1), "POWER_CONTROL.POWER_CONTROL_2")
            self.storePropertyToData(self._getSwitch(2), "POWER_CONTROL.POWER_CONTROL_3")
            self.storePropertyToData(self._getSwitch(3), "POWER_CONTROL.POWER_CONTROL_4")
            self.storePropertyToData(self._getSwitchValue(4), "DEW_CURRENT.DEW_CURRENT_A")
            self.storePropertyToData(self._getSwitchValue(5), "DEW_CURRENT.DEW_CURRENT_B")
            self.storePropertyToData(self._getSwitch(6), "USB_HUB_CONTROL.INDI_ENABLED")
            self.storePropertyToData(self._getSwitch(7), "AUTO_DEW.INDI_ENABLED")
            self.storePropertyToData(
                self._getSwitchValue(11), "POWER_SENSORS.SENSOR_VOLTAGE"
            )
            self.storePropertyToData(
                self._getSwitchValue(12), "POWER_SENSORS.SENSOR_CURRENT"
            )
            self.storePropertyToData(
                self._getSwitchValue(13), "POWER_SENSORS.SENSOR_POWER"
            )

        if model == "UPBv2":
            self.storePropertyToData(self._getSwitch(0), "POWER_CONTROL.POWER_CONTROL_1")
            self.storePropertyToData(self._getSwitch(1), "POWER_CONTROL.POWER_CONTROL_2")
            self.storePropertyToData(self._getSwitch(2), "POWER_CONTROL.POWER_CONTROL_3")
            self.storePropertyToData(self._getSwitch(3), "POWER_CONTROL.POWER_CONTROL_4")
            v = self._getSwitchValue(4)
            self.storePropertyToData(v / 2.55 if v is not None else None, "DEW_PWM.DEW_A")
            v = self._getSwitchValue(5)
            self.storePropertyToData(v / 2.55 if v is not None else None, "DEW_PWM.DEW_B")
            v = self._getSwitchValue(6)
            self.storePropertyToData(v / 2.55 if v is not None else None, "DEW_PWM.DEW_C")
            self.storePropertyToData(self._getSwitch(7), "USB_PORT_CONTROL.PORT_1")
            self.storePropertyToData(self._getSwitch(8), "USB_PORT_CONTROL.PORT_2")
            self.storePropertyToData(self._getSwitch(9), "USB_PORT_CONTROL.PORT_3")
            self.storePropertyToData(self._getSwitch(10), "USB_PORT_CONTROL.PORT_4")
            self.storePropertyToData(self._getSwitch(11), "USB_PORT_CONTROL.PORT_5")
            self.storePropertyToData(self._getSwitch(12), "USB_PORT_CONTROL.PORT_6")
            self.storePropertyToData(self._getSwitch(13), "AUTO_DEW.DEW_A")
            self.storePropertyToData(self._getSwitch(13), "AUTO_DEW.DEW_B")
            self.storePropertyToData(self._getSwitch(13), "AUTO_DEW.DEW_C")
            self.storePropertyToData(
                self._getSwitchValue(17), "POWER_SENSORS.SENSOR_VOLTAGE"
            )
            self.storePropertyToData(
                self._getSwitchValue(18), "POWER_SENSORS.SENSOR_CURRENT"
            )
            self.storePropertyToData(
                self._getSwitchValue(19), "POWER_SENSORS.SENSOR_POWER"
            )

    def togglePowerPort(self, port: str) -> None:
        if not self.deviceConnected:
            return
        switchNumber = int(port) - 1
        val = self.data.get(f"POWER_CONTROL.POWER_CONTROL_{port}", True)
        self._setSwitchValue(switchNumber, float(not val))

    def togglePowerPortBoot(self, port: str):
        pass

    def toggleHubUSB(self) -> None:
        pass

    def togglePortUSB(self, port: str) -> None:
        if not self.deviceConnected:
            return
        maxSwitch = self._getMaxSwitch()
        if maxSwitch is None:
            return
        model = "UPB" if maxSwitch == 15 else "UPBv2"
        if model == "UPBv2":
            switchNumber = int(port) + 6
            val = self.data.get(f"USB_PORT_CONTROL.PORT_{port}", True)
            self._setSwitchValue(switchNumber, float(val))

    def toggleAutoDew(self) -> None:
        if not self.deviceConnected:
            return
        maxSwitch = self._getMaxSwitch()
        if maxSwitch is None:
            return
        model = "UPB" if maxSwitch == 15 else "UPBv2"
        if model == "UPB":
            val = self.data.get("AUTO_DEW.INDI_ENABLED", False)
            self._setSwitchValue(7, float(val))
        else:
            val = self.data.get("AUTO_DEW.DEW_A", False)
            self._setSwitchValue(13, float(val))

    def sendDew(self, port: str, value: float) -> None:
        if not self.deviceConnected:
            return
        maxSwitch = self._getMaxSwitch()
        if maxSwitch is None:
            return
        model = "UPB" if maxSwitch == 15 else "UPBv2"
        switchNumber = ord(port) - ord("A") + 4
        val = int(value * 2.55)
        if model == "UPBv2":
            self._setSwitchValue(switchNumber, float(val))

    def sendAdjustableOutput(self, value: float) -> None:
        pass

    def reboot(self) -> None:
        pass
