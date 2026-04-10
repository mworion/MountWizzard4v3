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
import contextlib
import numpy as np
from astropy.io import fits
from mw4.base.alpacaClass import AlpacaClass
from mw4.base.tpool import Worker

# (stateKeyLower, dataKey, typedAttrName)
_pollProps = [
    ("binx", "CCD_BINNING.HOR_BIN", "BinX"),
    ("biny", "CCD_BINNING.VERT_BIN", "BinY"),
    ("camerastate", "CAMERA.STATE", "CameraState"),
    ("gain", "CCD_GAIN.GAIN", "Gain"),
    ("offset", "CCD_OFFSET.OFFSET", "Offset"),
    ("fastreadout", "READOUT_QUALITY.QUALITY_LOW", "FastReadout"),
    ("ccdtemperature", "CCD_TEMPERATURE.CCD_TEMPERATURE_VALUE", "CCDTemperature"),
    ("cooleron", "CCD_COOLER.COOLER_ON", "CoolerOn"),
    ("coolerpower", "CCD_COOLER_POWER.CCD_COOLER_VALUE", "CoolerPower"),
]


class CameraAlpaca(AlpacaClass):
    def __init__(self, parent):
        self.parent = parent
        self.app = parent.app
        self.data = parent.data
        self.signals = parent.signals
        self.worker: Worker = None
        super().__init__(parent=parent)

    def workerGetInitialConfig(self) -> None:
        super().workerGetInitialConfig()
        # Mandatory properties
        for attr, key in [
            ("CameraXSize", "CCD_INFO.CCD_MAX_X"),
            ("CameraYSize", "CCD_INFO.CCD_MAX_Y"),
            ("PixelSizeX", "CCD_INFO.CCD_PIXEL_SIZE_X"),
            ("PixelSizeY", "CCD_INFO.CCD_PIXEL_SIZE_Y"),
            ("MaxBinX", "CCD_BINNING.HOR_BIN_MAX"),
            ("MaxBinY", "CCD_BINNING.VERT_BIN_MAX"),
            ("CanFastReadout", "CAN_FAST"),
            ("CanAbortExposure", "CAN_ABORT"),
            ("CanSetCCDTemperature", "CAN_SET_CCD_TEMPERATURE"),
            ("CanGetCoolerPower", "CAN_GET_COOLER_POWER"),
            ("StartX", "CCD_FRAME.X"),
            ("StartY", "CCD_FRAME.Y"),
        ]:
            try:
                self.storePropertyToData(getattr(self._device, attr), key)
            except Exception as e:
                self.log.error(f"[{self.deviceName}] {attr} error: [{e}]")
        # Optional properties — wrap individually (Priority 6)
        for attr, key in [
            ("GainMax", "CCD_GAIN.GAIN_MAX"),
            ("GainMin", "CCD_GAIN.GAIN_MIN"),
            ("Gains", "CCD_GAIN.GAIN_LIST"),
            ("OffsetMax", "CCD_OFFSET.OFFSET_MAX"),
            ("OffsetMin", "CCD_OFFSET.OFFSET_MIN"),
            ("Offsets", "CCD_OFFSET.OFFSET_LIST"),
        ]:
            with contextlib.suppress(Exception):
                self.storePropertyToData(getattr(self._device, attr), key)

        self.log.debug(f"Initial data: {self.data}")

    def workerPollData(self) -> None:
        # Priority 2: single DeviceState call → 9 HTTP calls → 1 per cycle
        try:
            raw = self._device.DeviceState
            state = {sv["Name"].lower(): sv["Value"] for sv in raw}
        except Exception:
            state = {}

        for stateKey, dataKey, attrName in _pollProps:
            try:
                value = (
                    state[stateKey]
                    if stateKey in state
                    else getattr(self._device, attrName)
                )
                self.storePropertyToData(value, dataKey)
            except Exception as e:
                self.log.error(f"[{self.deviceName}] {attrName} error: [{e}]")

    def sendDownloadMode(self) -> None:
        if self.data.get("CAN_FAST", False):
            try:
                self._device.FastReadout = self.parent.fastReadout
            except Exception as e:
                self.log.error(f"[{self.deviceName}] FastReadout set error: [{e}]")

    def waitFunc(self) -> bool:
        return not self._device.ImageReady  # typed bool property

    def workerExpose(self) -> None:
        self.sendDownloadMode()
        try:
            self._device.BinX = self.parent.binning
            self._device.BinY = self.parent.binning
            self._device.StartX = self.parent.posXASCOM
            self._device.StartY = self.parent.posYASCOM
            self._device.NumX = self.parent.widthASCOM
            self._device.NumY = self.parent.heightASCOM
            self._device.StartExposure(self.parent.exposureTime, Light=True)
        except Exception as e:
            self.log.error(f"[{self.deviceName}] StartExposure error: [{e}]")
            return

        self.parent.waitExposed(self.parent.exposureTime, self.waitFunc)
        self.signals.exposed.emit(self.parent.imagePath)

        # Priority 3: ImageArray auto-negotiates binary ImageBytes transport
        self.signals.message.emit("download")
        try:
            rawData = self._device.ImageArray
        except Exception as e:
            self.log.error(f"[{self.deviceName}] ImageArray error: [{e}]")
            return
        data = np.array(rawData, dtype=np.uint16).T

        self.signals.downloaded.emit(self.parent.imagePath)
        self.signals.message.emit("saving")
        hdu = fits.PrimaryHDU(data=data)
        hdu.writeto(self.parent.imagePath, overwrite=True)
        self.parent.writeImageFitsHeader()

    def expose(self) -> None:
        self.worker = Worker(self.workerExpose)
        self.worker.signals.finished.connect(self.parent.exposeFinished)
        self.threadPool.start(self.worker)

    def abort(self) -> bool:
        if self.data.get("CAN_ABORT", False):
            try:
                self._device.StopExposure()
            except Exception as e:
                self.log.error(f"[{self.deviceName}] StopExposure error: [{e}]")
        return True

    def sendCoolerSwitch(self, coolerOn: bool = False) -> None:
        try:
            self._device.CoolerOn = coolerOn
        except Exception as e:
            self.log.error(f"[{self.deviceName}] CoolerOn set error: [{e}]")

    def sendCoolerTemp(self, temperature: float = 0) -> None:
        if self.data.get("CAN_SET_CCD_TEMPERATURE", False):
            try:
                self._device.SetCCDTemperature = temperature
            except Exception as e:
                self.log.error(f"[{self.deviceName}] SetCCDTemperature error: [{e}]")

    def sendOffset(self, offset: int = 0) -> None:
        try:
            self._device.Offset = offset
        except Exception as e:
            self.log.error(f"[{self.deviceName}] Offset set error: [{e}]")

    def sendGain(self, gain: int = 0) -> None:
        try:
            self._device.Gain = gain
        except Exception as e:
            self.log.error(f"[{self.deviceName}] Gain set error: [{e}]")
