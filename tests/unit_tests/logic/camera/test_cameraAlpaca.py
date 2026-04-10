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

import numpy as np
import pytest
import unittest.mock as mock
from astropy.io import fits
from mw4.logic.camera.camera import Camera
from mw4.logic.camera.cameraAlpaca import CameraAlpaca
from tests.unit_tests.unitTestAddOns.baseTestApp import App


@pytest.fixture(autouse=True, scope="module")
def function():
    camera = Camera(App())
    camera.exposureTime = 1
    camera.binning = 1
    camera.focalLength = 1
    func = CameraAlpaca(camera)
    yield func


def _make_camera_device():
    dev = mock.MagicMock()
    dev.DeviceState = []
    dev.CameraXSize = 4096
    dev.CameraYSize = 3000
    dev.PixelSizeX = 5.4
    dev.PixelSizeY = 5.4
    dev.MaxBinX = 4
    dev.MaxBinY = 4
    dev.CanFastReadout = True
    dev.CanAbortExposure = True
    dev.CanSetCCDTemperature = True
    dev.CanGetCoolerPower = True
    dev.StartX = 0
    dev.StartY = 0
    dev.ImageReady = True
    dev.ImageArray = [[1, 2], [3, 4]]
    return dev


def test_workerGetInitialConfig_1(function):
    function._device = _make_camera_device()
    function.workerGetInitialConfig()
    assert function.data["CCD_INFO.CCD_MAX_X"] == 4096
    assert function.data["CCD_INFO.CCD_MAX_Y"] == 3000


def test_workerGetInitialConfig_2_optional_raises(function):
    function._device = _make_camera_device()
    type(function._device).GainMax = mock.PropertyMock(
        side_effect=Exception("not impl")
    )
    function.workerGetInitialConfig()  # must not raise; optional missing is OK


def test_workerPollData_1_devicestate(function):
    function._device = mock.MagicMock()
    function._device.DeviceState = [
        {"Name": "BinX", "Value": 2},
        {"Name": "BinY", "Value": 2},
        {"Name": "CameraState", "Value": 0},
        {"Name": "Gain", "Value": 100},
        {"Name": "Offset", "Value": 10},
        {"Name": "FastReadout", "Value": False},
        {"Name": "CCDTemperature", "Value": -10.0},
        {"Name": "CoolerOn", "Value": True},
        {"Name": "CoolerPower", "Value": 50.0},
    ]
    function.workerPollData()
    assert function.data["CCD_BINNING.HOR_BIN"] == 2
    assert function.data["CCD_TEMPERATURE.CCD_TEMPERATURE_VALUE"] == -10.0


def test_workerPollData_2_devicestate_fails_falls_back(function):
    function._device = mock.MagicMock()
    type(function._device).DeviceState = mock.PropertyMock(
        side_effect=Exception("not impl")
    )
    function._device.BinX = 1
    function._device.BinY = 1
    function._device.CameraState = 0
    function._device.Gain = 50
    function._device.Offset = 0
    function._device.FastReadout = False
    function._device.CCDTemperature = -5.0
    function._device.CoolerOn = True
    function._device.CoolerPower = 40.0
    function.workerPollData()
    assert function.data["CCD_BINNING.HOR_BIN"] == 1


def test_sendDownloadMode_1(function):
    function.data["CAN_FAST"] = True
    function._device = _make_camera_device()
    function.sendDownloadMode()
    assert function._device.FastReadout == function.parent.fastReadout


def test_waitFunc(function):
    function._device = _make_camera_device()
    function._device.ImageReady = True
    assert not function.waitFunc()  # waitFunc returns not ImageReady


def test_workerExpose_1(function):
    function._device = _make_camera_device()
    function._device.ImageArray = [[1, 2], [3, 4]]
    with mock.patch.object(function.parent, "waitExposed"):
        with mock.patch.object(function.parent, "writeImageFitsHeader"):
            with mock.patch.object(fits.HDUList, "writeto"):
                function.workerExpose()


def test_workerExpose_2_imagearray_raises(function):
    function._device = _make_camera_device()
    type(function._device).ImageArray = mock.PropertyMock(
        side_effect=Exception("transfer error")
    )
    with mock.patch.object(function.parent, "waitExposed"):
        function.workerExpose()  # must not propagate


def test_expose_1(function):
    with mock.patch.object(function.threadPool, "start"):
        function.expose()


def test_abort_1_no_abort_cap(function):
    function.data["CAN_ABORT"] = False
    suc = function.abort()
    assert suc


def test_abort_2_calls_stopexposure(function):
    function.data["CAN_ABORT"] = True
    function._device = _make_camera_device()
    suc = function.abort()
    assert suc
    function._device.StopExposure.assert_called_once()


def test_sendCoolerSwitch_1_off(function):
    function._device = _make_camera_device()
    function.sendCoolerSwitch(coolerOn=False)
    assert function._device.CoolerOn is False


def test_sendCoolerSwitch_2_on(function):
    function._device = _make_camera_device()
    function.sendCoolerSwitch(coolerOn=True)
    assert function._device.CoolerOn is True


def test_sendCoolerTemp_1(function):
    function.data["CAN_SET_CCD_TEMPERATURE"] = True
    function._device = _make_camera_device()
    function.sendCoolerTemp(temperature=-10.0)
    assert function._device.SetCCDTemperature == -10.0


def test_sendOffset_1(function):
    function._device = _make_camera_device()
    function.sendOffset(offset=50)
    assert function._device.Offset == 50


def test_sendGain_1(function):
    function._device = _make_camera_device()
    function.sendGain(gain=200)
    assert function._device.Gain == 200
