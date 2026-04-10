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
from mw4.logic.telescope.telescopeAlpaca import TelescopeAlpaca
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
        func = TelescopeAlpaca(parent=Parent())
        yield func


def test_workerGetInitialConfig_1_stores_values(function):
    function._device = mock.MagicMock()
    function._device.ApertureDiameter = 0.08
    function._device.FocalLength = 0.4
    function.workerGetInitialConfig()
    assert function.data["TELESCOPE_INFO.TELESCOPE_APERTURE"] == 0.08
    assert function.data["TELESCOPE_INFO.TELESCOPE_FOCAL_LENGTH"] == 0.4


def test_workerGetInitialConfig_2_aperture_raises(function):
    function._device = mock.MagicMock()
    type(function._device).ApertureDiameter = mock.PropertyMock(
        side_effect=Exception("not impl")
    )
    function._device.FocalLength = 0.4
    function.workerGetInitialConfig()
    assert function.data["TELESCOPE_INFO.TELESCOPE_FOCAL_LENGTH"] == 0.4


def test_workerGetInitialConfig_3_no_device(function):
    function._device = None
    function.workerGetInitialConfig()  # must not raise
