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

# (state_key_lower, data_key, typed_attr_name)
_WEATHER_PROPS = [
    ("temperature", "WEATHER_PARAMETERS.WEATHER_TEMPERATURE", "Temperature"),
    ("pressure", "WEATHER_PARAMETERS.WEATHER_PRESSURE", "Pressure"),
    ("dewpoint", "WEATHER_PARAMETERS.WEATHER_DEWPOINT", "DewPoint"),
    ("humidity", "WEATHER_PARAMETERS.WEATHER_HUMIDITY", "Humidity"),
    ("cloudcover", "WEATHER_PARAMETERS.CloudCover", "CloudCover"),
    ("rainrate", "WEATHER_PARAMETERS.RainVol", "RainRate"),
    ("skyquality", "SKY_QUALITY.SKY_BRIGHTNESS", "SkyQuality"),
]


class SensorWeatherAlpaca(AlpacaClass):
    """ """

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.signals = parent.signals
        self.data = parent.data

    def workerPollData(self) -> None:
        if not self.deviceConnected:
            return

        # Priority 2: single DeviceState call → 7 HTTP calls → 1 per cycle
        try:
            raw = self._device.DeviceState
            state = {sv["Name"].lower(): sv["Value"] for sv in raw}
        except Exception:
            state = {}

        for state_key, data_key, attr_name in _WEATHER_PROPS:
            try:
                value = (
                    state[state_key]
                    if state_key in state
                    else getattr(self._device, attr_name)
                )
                self.storePropertyToData(value, data_key)
            except Exception as e:
                self.log.error(f"[{self.deviceName}] {attr_name} error: [{e}]")
