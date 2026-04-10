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
from mw4.logic.focuser.focuserAlpaca import FocuserAlpaca
from tests.unit_tests.unitTestAddOns.baseTestApp import App


class Parent:
    app = App()
    data = {}
    signals = Signals()
    loadConfig = True
    updateRate = 1000


@pytest.fixture(autouse=True, scope="function")
def function():
    func = FocuserAlpaca(parent=Parent())
    yield func


def test_workerPollData_1_disconnected(function):
    function.deviceConnected = False
    function.workerPollData()  # no-op, must not raise


def test_workerPollData_2_stores_position(function):
    function.deviceConnected = True
    function._device = mock.MagicMock()
    function._device.Position = 1500
    function.workerPollData()
    assert function.data["ABS_FOCUS_POSITION.FOCUS_ABSOLUTE_POSITION"] == 1500


def test_workerPollData_3_device_raises(function):
    function.deviceConnected = True
    function._device = mock.MagicMock()
    type(function._device).Position = mock.PropertyMock(side_effect=Exception("err"))
    function.workerPollData()  # must not propagate exception


def test_move_1_disconnected(function):
    function.deviceConnected = False
    function.move(position=100)  # no-op


def test_move_2_calls_typed_move(function):
    function.deviceConnected = True
    function._device = mock.MagicMock()
    function.move(position=100)
    function._device.Move.assert_called_once_with(100)


def test_move_3_device_raises(function):
    function.deviceConnected = True
    function._device = mock.MagicMock()
    function._device.Move.side_effect = Exception("not impl")
    function.move(position=100)  # must not propagate


def test_halt_1_disconnected(function):
    function.deviceConnected = False
    function.halt()  # no-op


def test_halt_2_calls_typed_halt(function):
    function.deviceConnected = True
    function._device = mock.MagicMock()
    function.halt()
    function._device.Halt.assert_called_once()


def test_halt_3_device_raises(function):
    function.deviceConnected = True
    function._device = mock.MagicMock()
    function._device.Halt.side_effect = Exception("not impl")
    function.halt()  # must not propagate
