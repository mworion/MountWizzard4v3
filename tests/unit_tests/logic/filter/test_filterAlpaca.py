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
from mw4.logic.filter.filterAlpaca import FilterAlpaca
from tests.unit_tests.unitTestAddOns.baseTestApp import App


class Parent:
    app = App()
    data = {}
    signals = Signals()
    loadConfig = True
    updateRate = 1000


@pytest.fixture(autouse=True, scope="function")
def function():
    func = FilterAlpaca(parent=Parent())
    yield func


def test_workerGetInitialConfig_1_no_device(function):
    function._device = None
    function.workerGetInitialConfig()  # must not raise


def test_workerGetInitialConfig_2_names_raises(function):
    function._device = mock.MagicMock()
    type(function._device).Names = mock.PropertyMock(side_effect=Exception("err"))
    function.workerGetInitialConfig()  # must not raise


def test_workerGetInitialConfig_3_names_none(function):
    function._device = mock.MagicMock()
    function._device.Names = None
    function.workerGetInitialConfig()  # must not raise


def test_workerGetInitialConfig_4_stores_names(function):
    function._device = mock.MagicMock()
    function._device.Names = ["Red", "Green"]
    function.workerGetInitialConfig()
    assert function.data["FILTER_NAME.FILTER_SLOT_NAME_0"] == "Red"
    assert function.data["FILTER_NAME.FILTER_SLOT_NAME_1"] == "Green"


def test_workerGetInitialConfig_5_none_slot_skipped(function):
    function.data.clear()  # start from empty data
    function._device = mock.MagicMock()
    function._device.Names = ["Red", None]
    function.workerGetInitialConfig()
    assert function.data["FILTER_NAME.FILTER_SLOT_NAME_0"] == "Red"
    assert "FILTER_NAME.FILTER_SLOT_NAME_1" not in function.data


def test_workerPollData_1_disconnected(function):
    function.deviceConnected = False
    function.workerPollData()  # no-op


def test_workerPollData_2_position_minus1(function):
    function.deviceConnected = True
    function._device = mock.MagicMock()
    function._device.Position = -1
    function.workerPollData()
    assert "FILTER_SLOT.FILTER_SLOT_VALUE" not in function.data


def test_workerPollData_3_stores_position(function):
    function.deviceConnected = True
    function._device = mock.MagicMock()
    function._device.Position = 2
    function.workerPollData()
    assert function.data["FILTER_SLOT.FILTER_SLOT_VALUE"] == 2


def test_workerPollData_4_device_raises(function):
    function.deviceConnected = True
    function._device = mock.MagicMock()
    type(function._device).Position = mock.PropertyMock(side_effect=Exception("err"))
    function.workerPollData()  # must not propagate


def test_sendFilterNumber_1_disconnected(function):
    function.deviceConnected = False
    function.sendFilterNumber(filterNumber=3)  # no-op


def test_sendFilterNumber_2_sets_position(function):
    function.deviceConnected = True
    function._device = mock.MagicMock()
    function.sendFilterNumber(filterNumber=3)
    assert function._device.Position == 3


def test_sendFilterNumber_3_device_raises(function):
    function.deviceConnected = True
    function._device = mock.MagicMock()
    type(function._device).Position = mock.PropertyMock(side_effect=Exception("err"))
    function.sendFilterNumber(filterNumber=3)  # must not propagate
