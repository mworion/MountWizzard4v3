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

import PySide6
import pytest
import unittest.mock as mock
from mw4.base.signalsDevices import Signals
from mw4.logic.cover.coverAlpaca import CoverAlpaca
from tests.unit_tests.unitTestAddOns.baseTestApp import App


class Parent:
    app = App()
    data = {}
    signals = Signals()
    loadConfig = True
    updateRate = 1000


@pytest.fixture(autouse=True, scope="function")
def function():
    with mock.patch.object(PySide6.QtCore.QTimer, "start"):
        func = CoverAlpaca(parent=Parent())
        yield func


def _make_device(cover_state=1, brightness=128, max_brightness=255):
    dev = mock.MagicMock()
    dev.DeviceState = [
        {"Name": "CoverState", "Value": cover_state},
        {"Name": "Brightness", "Value": brightness},
        {"Name": "MaxBrightness", "Value": max_brightness},
    ]
    dev.CoverState = cover_state
    dev.Brightness = brightness
    dev.MaxBrightness = max_brightness
    return dev


def test_workerPollData_1_disconnected(function):
    function.deviceConnected = False
    function.workerPollData()  # no-op


def test_workerPollData_2_stores_values(function):
    function.deviceConnected = True
    function._device = _make_device(cover_state=1, brightness=100, max_brightness=255)
    function.workerPollData()
    assert function.data["Status.Cover"] == "Closed"
    assert function.data["FLAT_LIGHT_INTENSITY.FLAT_LIGHT_INTENSITY_VALUE"] == 100
    assert function.data["FLAT_LIGHT_INTENSITY.FLAT_LIGHT_INTENSITY_MAX"] == 255


def test_workerPollData_3_devicestate_fails_falls_back(function):
    function.deviceConnected = True
    function._device = mock.MagicMock()
    type(function._device).DeviceState = mock.PropertyMock(
        side_effect=Exception("not impl")
    )
    function._device.CoverState = 3  # "Open"
    function._device.Brightness = 50
    function._device.MaxBrightness = 255
    function.workerPollData()
    assert function.data["Status.Cover"] == "Open"


def test_closeCover_1_disconnected(function):
    function.deviceConnected = False
    function.closeCover()  # no-op


def test_closeCover_2_calls_typed(function):
    function.deviceConnected = True
    function._device = mock.MagicMock()
    function.closeCover()
    function._device.CloseCover.assert_called_once()


def test_openCover_1_disconnected(function):
    function.deviceConnected = False
    function.openCover()  # no-op


def test_openCover_2_calls_typed(function):
    function.deviceConnected = True
    function._device = mock.MagicMock()
    function.openCover()
    function._device.OpenCover.assert_called_once()


def test_haltCover_1_disconnected(function):
    function.deviceConnected = False
    function.haltCover()  # no-op


def test_haltCover_2_calls_typed(function):
    function.deviceConnected = True
    function._device = mock.MagicMock()
    function.haltCover()
    function._device.HaltCover.assert_called_once()


def test_lightOn_1_disconnected(function):
    function.deviceConnected = False
    function.lightOn()  # no-op


def test_lightOn_2_calls_calibratoron(function):
    function.deviceConnected = True
    function._device = mock.MagicMock()
    function.lightOn()
    function._device.CalibratorOn.assert_called_once_with(127)  # 255 // 2


def test_lightOff_1_disconnected(function):
    function.deviceConnected = False
    function.lightOff()  # no-op


def test_lightOff_2_calls_calibratoroff(function):
    function.deviceConnected = True
    function._device = mock.MagicMock()
    function.lightOff()
    function._device.CalibratorOff.assert_called_once()


def test_lightIntensity_1_disconnected(function):
    function.deviceConnected = False
    function.lightIntensity(0)  # no-op


def test_lightIntensity_2_calls_calibratoron(function):
    function.deviceConnected = True
    function._device = mock.MagicMock()
    function.lightIntensity(200.0)
    function._device.CalibratorOn.assert_called_once_with(200)
