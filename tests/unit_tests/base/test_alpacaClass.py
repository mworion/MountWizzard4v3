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
import time
from alpaca.device import Device
from alpaca import management
from alpaca.exceptions import (
    AlpacaRequestException,
    NotImplementedException as AlpacaNotImplemented,
)
from mw4.base.alpacaClass import AlpacaClass
from mw4.base.loggerMW import setupLogging
from mw4.base.signalsDevices import Signals
from PySide6.QtCore import QTimer
from tests.unit_tests.unitTestAddOns.baseTestApp import App
from unittest import mock

setupLogging()

VALID_DEVICE_NAME = "MyDevice:camera:0"


@pytest.fixture(autouse=True, scope="function")
def function():
    class Parent:
        app = App()
        data = {}
        signals = Signals()

    with mock.patch.object(QTimer, "start"):
        func = AlpacaClass(parent=Parent())
        yield func


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

def test_properties_1(function):
    function.host = ("localhost", 11111)
    function.hostaddress = "localhost"
    function.port = 11111
    function.deviceName = "test"
    function.deviceName = "test:2"
    function.apiVersion = 1
    function.protocol = "1"


def test_properties_2(function):
    host = function.host
    assert host == ("localhost", 11111)
    assert function.hostaddress == "localhost"
    assert function.port == 11111
    assert function.deviceName == ""
    assert function.apiVersion == 1
    assert function.protocol == "http"


def test_properties_3(function):
    function.deviceName = "test:camera:3"
    assert function.deviceName == "test:camera:3"
    assert function.deviceType == "camera"
    assert function.number == 3
    assert function._device is not None


def test_rebuildDevice_on_hostaddress_change(function):
    function.deviceName = VALID_DEVICE_NAME
    old_device = function._device
    function.hostaddress = "192.168.1.1"
    assert function._device is not old_device


def test_rebuildDevice_on_port_change(function):
    function.deviceName = VALID_DEVICE_NAME
    old_device = function._device
    function.port = 4567
    assert function._device is not old_device


def test_rebuildDevice_no_device_when_invalid_name(function):
    function.deviceName = "noparts"
    assert function._device is None


def test_baseUrl_1(function):
    function.deviceName = "test:camera:3"
    val = function.generateBaseUrl()
    assert val == "http://localhost:11111/api/v1/camera/3"


# ---------------------------------------------------------------------------
# discoverAPIVersion
# ---------------------------------------------------------------------------

def test_discoverAPIVersion_1(function):
    with mock.patch.object(management, "apiversions", side_effect=Exception()):
        val = function.discoverAPIVersion()
        assert val == 0


def test_discoverAPIVersion_2(function):
    with mock.patch.object(
        management, "apiversions", side_effect=AlpacaRequestException(408, "timeout")
    ):
        val = function.discoverAPIVersion()
        assert val == 0


def test_discoverAPIVersion_3(function):
    with mock.patch.object(
        management, "apiversions", side_effect=AlpacaRequestException(503, "conn error")
    ):
        val = function.discoverAPIVersion()
        assert val == 0


def test_discoverAPIVersion_4(function):
    with mock.patch.object(
        management, "apiversions", side_effect=AlpacaRequestException(400, "bad request")
    ):
        val = function.discoverAPIVersion()
        assert val == 0


def test_discoverAPIVersion_5(function):
    with mock.patch.object(management, "apiversions", side_effect=Exception("driver error")):
        val = function.discoverAPIVersion()
        assert val == 0


def test_discoverAPIVersion_6(function):
    with mock.patch.object(management, "apiversions", return_value=[1]):
        val = function.discoverAPIVersion()
        assert val == 1


def test_discoverAPIVersion_7_empty_list(function):
    with mock.patch.object(management, "apiversions", return_value=[]):
        val = function.discoverAPIVersion()
        assert val == 0


# ---------------------------------------------------------------------------
# discoverAlpacaDevices
# ---------------------------------------------------------------------------

def test_discoverAlpacaDevices_1(function):
    with mock.patch.object(management, "configureddevices", side_effect=Exception):
        val = function.discoverAlpacaDevices()
        assert val == []


def test_discoverAlpacaDevices_2(function):
    with mock.patch.object(
        management, "configureddevices", side_effect=AlpacaRequestException(408, "timeout")
    ):
        val = function.discoverAlpacaDevices()
        assert val == []


def test_discoverAlpacaDevices_3(function):
    with mock.patch.object(
        management, "configureddevices", side_effect=AlpacaRequestException(503, "conn error")
    ):
        val = function.discoverAlpacaDevices()
        assert val == []


def test_discoverAlpacaDevices_4(function):
    with mock.patch.object(
        management, "configureddevices", side_effect=AlpacaRequestException(400, "bad request")
    ):
        val = function.discoverAlpacaDevices()
        assert val == []


def test_discoverAlpacaDevices_5(function):
    with mock.patch.object(
        management, "configureddevices", side_effect=Exception("driver error")
    ):
        val = function.discoverAlpacaDevices()
        assert val == []


def test_discoverAlpacaDevices_6(function):
    expected = [{"DeviceName": "test", "DeviceType": "Camera", "DeviceNumber": 0}]
    with mock.patch.object(management, "configureddevices", return_value=expected):
        val = function.discoverAlpacaDevices()
        assert val == expected


# ---------------------------------------------------------------------------
# getAlpacaProperty
# ---------------------------------------------------------------------------

def test_getAlpacaProperty_1(function):
    function.deviceName = ""
    val = function.getAlpacaProperty("")
    assert val == []


def test_getAlpacaProperty_2(function):
    function.deviceName = ""
    function.deviceConnected = True
    val = function.getAlpacaProperty("")
    assert val == []


def test_getAlpacaProperty_3(function):
    # single-part name → _device is None
    function.deviceName = "test"
    function.propertyExceptions = ["test"]
    val = function.getAlpacaProperty("test")
    assert val == []


def test_getAlpacaProperty_4_device_none(function):
    function._deviceName = "MyDevice:camera:0"
    function._device = None
    val = function.getAlpacaProperty("connected")
    assert val == []


def test_getAlpacaProperty_5_property_exception(function):
    function.deviceName = VALID_DEVICE_NAME
    function.propertyExceptions = ["connected"]
    val = function.getAlpacaProperty("connected")
    assert val == []


def test_getAlpacaProperty_6(function):
    function.deviceName = VALID_DEVICE_NAME
    with mock.patch.object(Device, "_get", side_effect=Exception("network error")):
        val = function.getAlpacaProperty("test")
        assert val == []


def test_getAlpacaProperty_7(function):
    function.deviceName = VALID_DEVICE_NAME
    with mock.patch.object(
        Device, "_get", side_effect=AlpacaRequestException(400, "bad request")
    ):
        val = function.getAlpacaProperty("test")
        assert val == []


def test_getAlpacaProperty_8(function):
    function.deviceName = VALID_DEVICE_NAME
    function.propertyExceptions = []
    with mock.patch.object(Device, "_get", side_effect=AlpacaNotImplemented("not impl")):
        val = function.getAlpacaProperty("test")
        assert val == []
        assert "test" in function.propertyExceptions


def test_getAlpacaProperty_9(function):
    function.deviceName = VALID_DEVICE_NAME
    with mock.patch.object(Device, "_get", return_value="test"):
        val = function.getAlpacaProperty("test")
        assert val == "test"


def test_getAlpacaProperty_10(function):
    function.deviceName = VALID_DEVICE_NAME
    with mock.patch.object(Device, "_get", return_value=[[1, 2], [3, 4]]):
        val = function.getAlpacaProperty("imagearray")
        assert val == [[1, 2], [3, 4]]


def test_getAlpacaProperty_11_with_kwargs(function):
    function.deviceName = VALID_DEVICE_NAME
    with mock.patch.object(Device, "_get", return_value=True) as mock_get:
        val = function.getAlpacaProperty("getswitch", Id=3)
        assert val is True
        mock_get.assert_called_once_with(
            "getswitch", tmo=AlpacaClass.ALPACA_TIMEOUT, Id=3
        )


# ---------------------------------------------------------------------------
# setAlpacaProperty
# ---------------------------------------------------------------------------

def test_setAlpacaProperty_1(function):
    function.deviceConnected = False
    val = function.setAlpacaProperty("")
    assert val == {}


def test_setAlpacaProperty_2(function):
    function.deviceConnected = True
    val = function.setAlpacaProperty("")
    assert val == {}


def test_setAlpacaProperty_3(function):
    function.deviceName = "test"
    function.deviceConnected = True
    function.propertyExceptions = ["test"]
    val = function.setAlpacaProperty("test")
    assert val == {}


def test_setAlpacaProperty_4_device_none(function):
    function._deviceName = "MyDevice:camera:0"
    function._device = None
    val = function.setAlpacaProperty("connected")
    assert val == {}


def test_setAlpacaProperty_5_property_exception(function):
    function.deviceName = VALID_DEVICE_NAME
    function.propertyExceptions = ["connected"]
    val = function.setAlpacaProperty("connected")
    assert val == {}


def test_setAlpacaProperty_6(function):
    function.deviceName = VALID_DEVICE_NAME
    function.deviceConnected = True
    with mock.patch.object(Device, "_put", side_effect=Exception("network error")):
        val = function.setAlpacaProperty("test")
        assert val == {}


def test_setAlpacaProperty_7(function):
    function.deviceName = VALID_DEVICE_NAME
    function.deviceConnected = True
    with mock.patch.object(
        Device, "_put", side_effect=AlpacaRequestException(400, "bad request")
    ):
        val = function.setAlpacaProperty("test")
        assert val == {}


def test_setAlpacaProperty_8(function):
    function.deviceName = VALID_DEVICE_NAME
    function.deviceConnected = True
    function.propertyExceptions = []
    with mock.patch.object(Device, "_put", side_effect=AlpacaNotImplemented("not impl")):
        val = function.setAlpacaProperty("test")
        assert val == {}
        assert "test" in function.propertyExceptions


def test_setAlpacaProperty_9(function):
    function.deviceName = VALID_DEVICE_NAME
    function.deviceConnected = True
    result = {"ErrorNumber": 0, "ErrorMessage": "", "Value": "ok"}
    with mock.patch.object(Device, "_put", return_value=result):
        val = function.setAlpacaProperty("test")
        assert val == result


def test_setAlpacaProperty_10_with_kwargs(function):
    function.deviceName = VALID_DEVICE_NAME
    with mock.patch.object(Device, "_put", return_value={}) as mock_put:
        function.setAlpacaProperty("cooleron", CoolerOn=True)
        mock_put.assert_called_once_with(
            "cooleron", tmo=AlpacaClass.ALPACA_TIMEOUT, CoolerOn=True
        )


# ---------------------------------------------------------------------------
# getAndStoreAlpacaProperty
# ---------------------------------------------------------------------------

def test_getAndStoreAlpacaProperty(function):
    with mock.patch.object(function, "getAlpacaProperty"):
        with mock.patch.object(function, "storePropertyToData"):
            function.getAndStoreAlpacaProperty("name", "DRIVER_INFO.DRIVER_NAME")


# ---------------------------------------------------------------------------
# workerConnectDevice
# ---------------------------------------------------------------------------

def test_workerConnectDevice_1_no_device(function):
    function.serverConnected = False
    function.deviceConnected = False
    function.workerConnectDevice()
    assert not function.serverConnected
    assert not function.deviceConnected


def test_workerConnectDevice_2_get_returns_false(function):
    function.deviceName = VALID_DEVICE_NAME
    function.serverConnected = False
    function.deviceConnected = False
    with mock.patch.object(time, "sleep"):
        with mock.patch.object(Device, "_put"):
            with mock.patch.object(Device, "_get", return_value=False):
                function.workerConnectDevice()
                assert not function.serverConnected
                assert not function.deviceConnected


def test_workerConnectDevice_3_get_returns_true(function):
    function.deviceName = VALID_DEVICE_NAME
    function.serverConnected = False
    function.deviceConnected = False
    with mock.patch.object(Device, "_put"):
        with mock.patch.object(Device, "_get", return_value=True):
            with mock.patch.object(function.threadPool, "start"):
                function.workerConnectDevice()
                assert function.serverConnected
                assert function.deviceConnected


def test_workerConnectDevice_4_put_raises_then_succeeds(function):
    function.deviceName = VALID_DEVICE_NAME
    function.serverConnected = False
    function.deviceConnected = False
    call_count = {"n": 0}

    def _put_side_effect(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise Exception("connection refused")

    with mock.patch.object(time, "sleep"):
        with mock.patch.object(Device, "_put", side_effect=_put_side_effect):
            with mock.patch.object(Device, "_get", return_value=True):
                with mock.patch.object(function.threadPool, "start"):
                    function.workerConnectDevice()
                    assert function.serverConnected
                    assert function.deviceConnected


# ---------------------------------------------------------------------------
# Timers
# ---------------------------------------------------------------------------

def test_startTimer(function):
    function.startAlpacaTimer()


def test_stopTimer(function):
    with mock.patch.object(PySide6.QtCore.QTimer, "stop"):
        function.stopAlpacaTimer()


# ---------------------------------------------------------------------------
# workerGetInitialConfig
# ---------------------------------------------------------------------------

def test_workerGetInitialConfig_1(function):
    with mock.patch.object(function, "getAlpacaProperty", return_value="test"):
        function.workerGetInitialConfig()
        assert function.data["DRIVER_INFO.DRIVER_NAME"] == "test"
        assert function.data["DRIVER_INFO.DRIVER_VERSION"] == "test"
        assert function.data["DRIVER_INFO.DRIVER_EXEC"] == "test"


# ---------------------------------------------------------------------------
# workerPollStatus
# ---------------------------------------------------------------------------

def test_workerPollStatus_1(function):
    function.deviceConnected = True
    with mock.patch.object(function, "getAlpacaProperty", return_value=False):
        function.workerPollStatus()
        assert not function.deviceConnected


def test_workerPollStatus_2(function):
    function.deviceConnected = False
    with mock.patch.object(function, "getAlpacaProperty", return_value=True):
        function.workerPollStatus()
        assert function.deviceConnected


# ---------------------------------------------------------------------------
# processPolledData / workerPollData
# ---------------------------------------------------------------------------

def test_processPolledData(function):
    function.processPolledData()


def test_workerPollData(function):
    function.workerPollData()


# ---------------------------------------------------------------------------
# pollData / pollStatus / getInitialConfig
# ---------------------------------------------------------------------------

def test_pollData_1(function):
    function.deviceConnected = True
    with mock.patch.object(function.threadPool, "start"):
        function.pollData()


def test_pollData_2(function):
    function.deviceConnected = False
    with mock.patch.object(function.threadPool, "start"):
        function.pollData()


def test_pollStatus_1(function):
    function.deviceConnected = True
    with mock.patch.object(function.threadPool, "start"):
        function.pollStatus()


def test_pollStatus_2(function):
    function.deviceConnected = False
    with mock.patch.object(function.threadPool, "start"):
        function.pollStatus()


def test_getInitialConfig_1(function):
    function.deviceConnected = True
    with mock.patch.object(function.threadPool, "start"):
        function.getInitialConfig()


def test_getInitialConfig_2(function):
    function.deviceConnected = False
    with mock.patch.object(function.threadPool, "start"):
        function.getInitialConfig()


# ---------------------------------------------------------------------------
# startCommunication / stopCommunication
# ---------------------------------------------------------------------------

def test_startCommunication(function):
    with mock.patch.object(function.threadPool, "start"):
        function.startCommunication()


def test_stopCommunication_1(function):
    function.deviceConnected = True
    function.serverConnected = True
    function.deviceName = "test"
    with mock.patch.object(function, "stopAlpacaTimer"):
        function.stopCommunication()
        assert not function.serverConnected
        assert not function.deviceConnected


def test_stopCommunication_2_with_active_device(function):
    function.deviceName = VALID_DEVICE_NAME
    function.deviceConnected = True
    function.serverConnected = True
    with mock.patch.object(function, "stopAlpacaTimer"):
        with mock.patch.object(Device, "_put"):
            function.stopCommunication()
            assert not function.serverConnected
            assert not function.deviceConnected


def test_stopCommunication_3_device_put_raises(function):
    function.deviceName = VALID_DEVICE_NAME
    function.deviceConnected = True
    function.serverConnected = True
    with mock.patch.object(function, "stopAlpacaTimer"):
        with mock.patch.object(Device, "_put", side_effect=Exception("timeout")):
            function.stopCommunication()
            assert not function.serverConnected
            assert not function.deviceConnected


# ---------------------------------------------------------------------------
# discoverDevices
# ---------------------------------------------------------------------------

def test_discoverDevices_1(function):
    devices = [
        {"DeviceName": "test", "DeviceNumber": 1, "DeviceType": "Dome"},
        {"DeviceName": "test1", "DeviceNumber": 3, "DeviceType": "Dome"},
    ]
    with mock.patch.object(function, "discoverAlpacaDevices", return_value=devices):
        val = function.discoverDevices("dome")
        assert val == ["test:dome:1", "test1:dome:3"]


def test_discoverDevices_2(function):
    with mock.patch.object(function, "discoverAlpacaDevices", return_value=[]):
        val = function.discoverDevices("dome")
        assert val == []


def test_discoverDevices_3_filters_type(function):
    devices = [
        {"DeviceName": "cam", "DeviceNumber": 0, "DeviceType": "Camera"},
        {"DeviceName": "dome", "DeviceNumber": 0, "DeviceType": "Dome"},
    ]
    with mock.patch.object(function, "discoverAlpacaDevices", return_value=devices):
        val = function.discoverDevices("camera")
        assert val == ["cam:camera:0"]
        val2 = function.discoverDevices("dome")
        assert val2 == ["dome:dome:0"]

