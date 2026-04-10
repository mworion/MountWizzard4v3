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
from alpaca.device import Device
from alpaca import management, discovery
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
    with mock.patch.object(management, "apiversions", return_value=[1]):
        val = function.discoverAPIVersion()
        assert val == 1


def test_discoverAPIVersion_3_empty_list(function):
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
    expected = [{"DeviceName": "test", "DeviceType": "Camera", "DeviceNumber": 0}]
    with mock.patch.object(management, "configureddevices", return_value=expected):
        val = function.discoverAlpacaDevices()
        assert val == expected


# ---------------------------------------------------------------------------
# discoverAlpacaServers  (Priority 4)
# ---------------------------------------------------------------------------

def test_discoverAlpacaServers_1_exception(function):
    with mock.patch.object(discovery, "search_ipv4", side_effect=Exception("timeout")):
        val = function.discoverAlpacaServers()
        assert val == []


def test_discoverAlpacaServers_2_ok(function):
    with mock.patch.object(
        discovery, "search_ipv4", return_value=["192.168.1.10:11111"]
    ):
        val = function.discoverAlpacaServers()
        assert val == ["192.168.1.10:11111"]


# ---------------------------------------------------------------------------
# workerConnectDevice  (Priority 5)
# ---------------------------------------------------------------------------

def test_workerConnectDevice_1_no_device(function):
    function.serverConnected = False
    function.deviceConnected = False
    function.workerConnectDevice()
    assert not function.serverConnected
    assert not function.deviceConnected


def test_workerConnectDevice_2_connected_returns_false(function):
    function.deviceName = VALID_DEVICE_NAME
    function.serverConnected = False
    function.deviceConnected = False
    function._device = mock.MagicMock()
    function._device.Connecting = False
    function._device.Connected = False
    function.workerConnectDevice()
    assert not function.serverConnected
    assert not function.deviceConnected


def test_workerConnectDevice_3_connected_returns_true(function):
    function.deviceName = VALID_DEVICE_NAME
    function.serverConnected = False
    function.deviceConnected = False
    function._device = mock.MagicMock()
    function._device.Connecting = False
    function._device.Connected = True
    with mock.patch.object(function.threadPool, "start"):
        function.workerConnectDevice()
        assert function.serverConnected
        assert function.deviceConnected


def test_workerConnectDevice_4_connect_raises(function):
    function.deviceName = VALID_DEVICE_NAME
    function.serverConnected = False
    function.deviceConnected = False
    function._device = mock.MagicMock()
    function._device.Connect.side_effect = Exception("connection refused")
    function.workerConnectDevice()
    assert not function.serverConnected
    assert not function.deviceConnected


def test_workerConnectDevice_5_connecting_waits(function):
    """Verify that Connecting=True is polled until it becomes False."""
    function.deviceName = VALID_DEVICE_NAME
    function.serverConnected = False
    function.deviceConnected = False
    function._device = mock.MagicMock()
    function._device.Connecting.__bool__ = mock.Mock(
        side_effect=[True, True, False]
    )
    function._device.Connected = True
    import time
    with mock.patch.object(time, "sleep"):
        with mock.patch.object(function.threadPool, "start"):
            function.workerConnectDevice()
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
    function._device = mock.MagicMock()
    function._device.Name = "test"
    function._device.DriverVersion = "test"
    function._device.DriverInfo = "test"
    function.workerGetInitialConfig()
    assert function.data["DRIVER_INFO.DRIVER_NAME"] == "test"
    assert function.data["DRIVER_INFO.DRIVER_VERSION"] == "test"
    assert function.data["DRIVER_INFO.DRIVER_EXEC"] == "test"


def test_workerGetInitialConfig_2_device_none(function):
    function._device = None
    function.workerGetInitialConfig()  # must not raise


def test_workerGetInitialConfig_3_property_raises(function):
    function._device = mock.MagicMock()
    function._device.Name = mock.PropertyMock(side_effect=Exception("not impl"))
    function._device.DriverVersion = "v1"
    function._device.DriverInfo = "info"
    function.workerGetInitialConfig()  # must not raise; partial data is OK


# ---------------------------------------------------------------------------
# workerPollStatus
# ---------------------------------------------------------------------------

def test_workerPollStatus_1(function):
    function.deviceConnected = True
    function._device = mock.MagicMock()
    function._device.Connected = False
    function.workerPollStatus()
    assert not function.deviceConnected


def test_workerPollStatus_2(function):
    function.deviceConnected = False
    function._device = mock.MagicMock()
    function._device.Connected = True
    function.workerPollStatus()
    assert function.deviceConnected


def test_workerPollStatus_3_device_none(function):
    function._device = None
    function.workerPollStatus()  # must not raise


def test_workerPollStatus_4_connected_raises(function):
    function.deviceConnected = True
    function._device = mock.MagicMock()
    type(function._device).Connected = mock.PropertyMock(side_effect=Exception("err"))
    function.workerPollStatus()
    assert not function.deviceConnected  # suc=False → disconnects


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
    function._device = mock.MagicMock()
    with mock.patch.object(function, "stopAlpacaTimer"):
        function.stopCommunication()
        assert not function.serverConnected
        assert not function.deviceConnected


def test_stopCommunication_3_device_set_raises(function):
    function.deviceName = VALID_DEVICE_NAME
    function.deviceConnected = True
    function.serverConnected = True
    function._device = mock.MagicMock()
    type(function._device).Connected = mock.PropertyMock(side_effect=Exception("timeout"))
    with mock.patch.object(function, "stopAlpacaTimer"):
        function.stopCommunication()
        assert not function.serverConnected
        assert not function.deviceConnected


# ---------------------------------------------------------------------------
# discoverDevices  (Priority 4 — multi-server)
# ---------------------------------------------------------------------------

def test_discoverDevices_1(function):
    devices = [
        {"DeviceName": "test", "DeviceNumber": 1, "DeviceType": "Dome"},
        {"DeviceName": "test1", "DeviceNumber": 3, "DeviceType": "Dome"},
    ]
    with mock.patch.object(function, "discoverAlpacaServers", return_value=[]):
        with mock.patch.object(management, "configureddevices", return_value=devices):
            val = function.discoverDevices("dome")
            assert val == ["test:dome:1", "test1:dome:3"]


def test_discoverDevices_2(function):
    with mock.patch.object(function, "discoverAlpacaServers", return_value=[]):
        with mock.patch.object(management, "configureddevices", side_effect=Exception):
            val = function.discoverDevices("dome")
            assert val == []


def test_discoverDevices_3_filters_type(function):
    devices = [
        {"DeviceName": "cam", "DeviceNumber": 0, "DeviceType": "Camera"},
        {"DeviceName": "dome", "DeviceNumber": 0, "DeviceType": "Dome"},
    ]
    with mock.patch.object(function, "discoverAlpacaServers", return_value=[]):
        with mock.patch.object(management, "configureddevices", return_value=devices):
            val = function.discoverDevices("camera")
            assert val == ["cam:camera:0"]
            val2 = function.discoverDevices("dome")
            assert val2 == ["dome:dome:0"]


def test_discoverDevices_4_multi_server(function):
    """UDP-discovered server + manual host are both queried."""
    devices1 = [{"DeviceName": "cam1", "DeviceNumber": 0, "DeviceType": "Camera"}]
    devices2 = [{"DeviceName": "cam2", "DeviceNumber": 0, "DeviceType": "Camera"}]
    with mock.patch.object(
        function, "discoverAlpacaServers", return_value=["192.168.1.10:11111"]
    ):
        with mock.patch.object(
            management, "configureddevices", side_effect=[devices1, devices2]
        ):
            val = function.discoverDevices("camera")
            assert "cam1:camera:0" in val
            assert "cam2:camera:0" in val


def test_discoverDevices_5_manual_not_duplicated(function):
    """Manual host already in UDP list → no duplicate querying."""
    devices = [{"DeviceName": "cam", "DeviceNumber": 0, "DeviceType": "Camera"}]
    manual = f"{function._hostaddress}:{function._port}"
    with mock.patch.object(
        function, "discoverAlpacaServers", return_value=[manual]
    ):
        with mock.patch.object(
            management, "configureddevices", return_value=devices
        ) as mock_cfg:
            val = function.discoverDevices("camera")
            assert mock_cfg.call_count == 1  # only one unique server
            assert val == ["cam:camera:0"]

