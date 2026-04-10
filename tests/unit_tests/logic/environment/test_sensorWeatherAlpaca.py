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
import pytest
import unittest.mock as mock
from mw4.base.signalsDevices import Signals
from mw4.logic.environment.sensorWeatherAlpaca import SensorWeatherAlpaca
from tests.unit_tests.unitTestAddOns.baseTestApp import App


class Parent:
    app = App()
    data = {}
    signals = Signals()
    loadConfig = True
    updateRate = 1000


@pytest.fixture(autouse=True, scope="module")
def function():
    func = SensorWeatherAlpaca(parent=Parent())
    yield func


def _make_device(temp=20.0, pressure=1013.0, dewpoint=10.0, humidity=60.0,
                 cloudcover=0.0, rainrate=0.0, skyquality=19.0):
    dev = mock.MagicMock()
    dev.DeviceState = [
        {"Name": "Temperature", "Value": temp},
        {"Name": "Pressure", "Value": pressure},
        {"Name": "DewPoint", "Value": dewpoint},
        {"Name": "Humidity", "Value": humidity},
        {"Name": "CloudCover", "Value": cloudcover},
        {"Name": "RainRate", "Value": rainrate},
        {"Name": "SkyQuality", "Value": skyquality},
    ]
    dev.Temperature = temp
    dev.Pressure = pressure
    dev.DewPoint = dewpoint
    dev.Humidity = humidity
    dev.CloudCover = cloudcover
    dev.RainRate = rainrate
    dev.SkyQuality = skyquality
    return dev


def test_workerPollData_1_disconnected(function):
    function.deviceConnected = False
    function.workerPollData()  # no-op


def test_workerPollData_2_stores_values(function):
    function.deviceConnected = True
    function._device = _make_device()
    function.workerPollData()
    assert function.data["WEATHER_PARAMETERS.WEATHER_TEMPERATURE"] == 20.0
    assert function.data["WEATHER_PARAMETERS.WEATHER_PRESSURE"] == 1013.0
    assert function.data["SKY_QUALITY.SKY_BRIGHTNESS"] == 19.0


def test_workerPollData_3_devicestate_fails_falls_back(function):
    """DeviceState raises → individual property fallback."""
    function.deviceConnected = True
    function._device = mock.MagicMock()
    type(function._device).DeviceState = mock.PropertyMock(
        side_effect=Exception("not impl")
    )
    function._device.Temperature = 15.0
    function._device.Pressure = 1000.0
    function._device.DewPoint = 5.0
    function._device.Humidity = 50.0
    function._device.CloudCover = 10.0
    function._device.RainRate = 0.0
    function._device.SkyQuality = 18.0
    function.workerPollData()
    assert function.data["WEATHER_PARAMETERS.WEATHER_TEMPERATURE"] == 15.0


def test_workerPollData_4_one_property_raises(function):
    """One property raising must not abort the rest."""
    function.deviceConnected = True
    function._device = _make_device()
    function._device.DeviceState = []  # empty → all fall back to individual reads
    type(function._device).Temperature = mock.PropertyMock(
        side_effect=Exception("not impl")
    )
    function._device.Pressure = 1013.0
    function.workerPollData()
    assert function.data["WEATHER_PARAMETERS.WEATHER_PRESSURE"] == 1013.0
