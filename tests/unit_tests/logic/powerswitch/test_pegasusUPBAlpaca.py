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
from mw4.logic.powerswitch.pegasusUPBAlpaca import PegasusUPBAlpaca
from tests.unit_tests.unitTestAddOns.baseTestApp import App


class Parent:
    app = App()
    data = {}
    signals = Signals()
    loadConfig = True
    updateRate = 1000


@pytest.fixture(autouse=True, scope="function")
def function():
    func = PegasusUPBAlpaca(parent=Parent())
    yield func


def _make_upb_device(max_switch=15):
    dev = mock.MagicMock()
    dev.MaxSwitch = max_switch
    dev.GetSwitch.return_value = True
    dev.GetSwitchValue.return_value = 5.0
    return dev


def test_workerPollData_1_disconnected(function):
    function.deviceConnected = False
    function.workerPollData()  # no-op


def test_workerPollData_2_upb_model(function):
    function.deviceConnected = True
    function._device = _make_upb_device(max_switch=15)
    with mock.patch.object(function, "storePropertyToData"):
        function.workerPollData()
    assert function.data["FIRMWARE_INFO.VERSION"] == "1.4"


def test_workerPollData_3_upbv2_model(function):
    function.deviceConnected = True
    function._device = _make_upb_device(max_switch=21)
    with mock.patch.object(function, "storePropertyToData"):
        function.workerPollData()
    assert function.data["FIRMWARE_INFO.VERSION"] == "2.1"


def test_workerPollData_4_maxswitch_raises(function):
    function.deviceConnected = True
    function._device = mock.MagicMock()
    type(function._device).MaxSwitch = mock.PropertyMock(side_effect=Exception("err"))
    function.workerPollData()  # returns early, must not raise


def test_togglePowerPort_1_disconnected(function):
    function.deviceConnected = False
    function.togglePowerPort("1")  # no-op


def test_togglePowerPort_2_calls_setswitchvalue(function):
    function.deviceConnected = True
    function._device = _make_upb_device()
    function.data["POWER_CONTROL.POWER_CONTROL_1"] = True
    function.togglePowerPort("1")
    function._device.SetSwitchValue.assert_called_once_with(0, float(False))


def test_togglePowerPort_3_device_missing(function):
    function.deviceConnected = True
    function._device = None
    function.togglePowerPort("1")  # _getMaxSwitch handles None gracefully


def test_togglePowerPortBoot_1(function):
    function.togglePowerPortBoot("1")  # pass


def test_toggleHubUSB_1(function):
    function.toggleHubUSB()  # pass


def test_togglePortUSB_1_disconnected(function):
    function.deviceConnected = False
    function.togglePortUSB("1")  # no-op


def test_togglePortUSB_2_upbv2(function):
    function.deviceConnected = True
    function._device = _make_upb_device(max_switch=21)
    function.data["USB_PORT_CONTROL.PORT_1"] = False
    function.togglePortUSB("1")
    function._device.SetSwitchValue.assert_called_with(7, float(False))


def test_togglePortUSB_3_upb_no_action(function):
    function.deviceConnected = True
    function._device = _make_upb_device(max_switch=15)  # UPB → no USB port toggle
    function.togglePortUSB("1")
    function._device.SetSwitchValue.assert_not_called()


def test_toggleAutoDew_1_disconnected(function):
    function.deviceConnected = False
    function.toggleAutoDew()  # no-op


def test_toggleAutoDew_2_upbv2(function):
    function.deviceConnected = True
    function._device = _make_upb_device(max_switch=21)
    function.data["AUTO_DEW.DEW_A"] = False
    function.toggleAutoDew()
    function._device.SetSwitchValue.assert_called_once_with(13, float(False))


def test_toggleAutoDew_3_upb(function):
    function.deviceConnected = True
    function._device = _make_upb_device(max_switch=15)
    function.data["AUTO_DEW.INDI_ENABLED"] = True
    function.toggleAutoDew()
    function._device.SetSwitchValue.assert_called_once_with(7, float(True))


def test_sendDew_1_disconnected(function):
    function.deviceConnected = False
    function.sendDew("A", 50.0)  # no-op


def test_sendDew_2_upbv2(function):
    function.deviceConnected = True
    function._device = _make_upb_device(max_switch=21)
    function.sendDew("A", 50.0)
    expected_val = float(int(50.0 * 2.55))
    function._device.SetSwitchValue.assert_called_once_with(4, expected_val)


def test_sendDew_3_upb_no_action(function):
    function.deviceConnected = True
    function._device = _make_upb_device(max_switch=15)
    function.sendDew("A", 50.0)
    function._device.SetSwitchValue.assert_not_called()


def test_sendAdjustableOutput_1(function):
    function.sendAdjustableOutput(1)  # pass


def test_reboot_1(function):
    function.reboot()  # pass
