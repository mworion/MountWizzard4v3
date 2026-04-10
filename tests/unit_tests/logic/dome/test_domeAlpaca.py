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
from mw4.logic.dome.domeAlpaca import DomeAlpaca
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
        func = DomeAlpaca(parent=Parent())
        yield func


def _make_device(azimuth=180.0, slewing=False, shutter=0):
    dev = mock.MagicMock()
    dev.DeviceState = [
        {"Name": "Azimuth", "Value": azimuth},
        {"Name": "Slewing", "Value": slewing},
        {"Name": "ShutterStatus", "Value": shutter},
    ]
    dev.Azimuth = azimuth
    dev.Slewing = slewing
    dev.ShutterStatus = shutter
    dev.CanSetAltitude = True
    dev.CanSetAzimuth = True
    dev.CanSetShutter = True
    return dev


def test_workerGetInitialConfig_1(function):
    function._device = _make_device()
    function.workerGetInitialConfig()
    assert function.data["CanSetAltitude"] is True
    assert function.data["CanSetAzimuth"] is True
    assert function.data["CanSetShutter"] is True


def test_workerGetInitialConfig_2_raises(function):
    function._device = mock.MagicMock()
    type(function._device).CanSetAzimuth = mock.PropertyMock(
        side_effect=Exception("not impl")
    )
    function.workerGetInitialConfig()  # must not raise


def test_processPolledData_1(function):
    function.data["ABS_DOME_POSITION.DOME_ABSOLUTE_POSITION"] = 90.0
    function.processPolledData()  # emits signal


def test_workerPollData_1_disconnected(function):
    function.deviceConnected = False
    function.workerPollData()  # no-op


def test_workerPollData_2_shutter_open(function):
    function.deviceConnected = True
    function._device = _make_device(azimuth=90.0, shutter=0)
    function.workerPollData()
    assert function.data["ABS_DOME_POSITION.DOME_ABSOLUTE_POSITION"] == 90.0
    assert function.data["DOME_SHUTTER.SHUTTER_OPEN"] is True
    assert function.data["DOME_SHUTTER.SHUTTER_CLOSED"] is False


def test_workerPollData_3_shutter_closed(function):
    function.deviceConnected = True
    function._device = _make_device(azimuth=0.0, shutter=1)
    function.workerPollData()
    assert function.data["DOME_SHUTTER.SHUTTER_OPEN"] is False
    assert function.data["DOME_SHUTTER.SHUTTER_CLOSED"] is True


def test_workerPollData_4_shutter_other(function):
    function.deviceConnected = True
    function._device = _make_device(azimuth=0.0, shutter=3)
    function.workerPollData()
    assert function.data.get("DOME_SHUTTER.SHUTTER_OPEN") is None
    assert function.data.get("DOME_SHUTTER.SHUTTER_CLOSED") is None


def test_workerPollData_5_devicestate_fails_falls_back(function):
    """DeviceState raises → per-property fallback is used."""
    function.deviceConnected = True
    function._device = mock.MagicMock()
    type(function._device).DeviceState = mock.PropertyMock(
        side_effect=Exception("not impl")
    )
    function._device.Azimuth = 270.0
    function._device.Slewing = True
    function._device.ShutterStatus = 0
    function.workerPollData()
    assert function.data["ABS_DOME_POSITION.DOME_ABSOLUTE_POSITION"] == 270.0


def test_slewToAltAz_1_disconnected(function):
    function.deviceConnected = False
    function.slewToAltAz(30.0, 180.0)  # no-op


def test_slewToAltAz_2_calls_typed_methods(function):
    function.deviceConnected = True
    function.data["CanSetAzimuth"] = True
    function.data["CanSetAltitude"] = True
    function._device = mock.MagicMock()
    function.slewToAltAz(30.0, 180.0)
    function._device.SlewToAzimuth.assert_called_once_with(180.0)
    function._device.SlewToAltitude.assert_called_once_with(30.0)


def test_closeShutter_1_disconnected(function):
    function.deviceConnected = False
    function.closeShutter()  # no-op


def test_closeShutter_2_calls_typed(function):
    function.deviceConnected = True
    function.data["CanSetShutter"] = True
    function._device = mock.MagicMock()
    function.closeShutter()
    function._device.CloseShutter.assert_called_once()


def test_openShutter_1_disconnected(function):
    function.deviceConnected = False
    function.openShutter()  # no-op


def test_openShutter_2_calls_typed(function):
    function.deviceConnected = True
    function.data["CanSetShutter"] = True
    function._device = mock.MagicMock()
    function.openShutter()
    function._device.OpenShutter.assert_called_once()


def test_slewCW_1(function):
    function.slewCW()


def test_slewCCW_1(function):
    function.slewCCW()


def test_abortSlew_1_disconnected(function):
    function.deviceConnected = False
    function.abortSlew()  # no-op


def test_abortSlew_2_calls_typed(function):
    function.deviceConnected = True
    function._device = mock.MagicMock()
    function.abortSlew()
    function._device.AbortSlew.assert_called_once()
