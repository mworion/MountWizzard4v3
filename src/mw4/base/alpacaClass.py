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
import time
from alpaca import discovery, management
from alpaca.camera import Camera
from alpaca.covercalibrator import CoverCalibrator
from alpaca.device import Device
from alpaca.dome import Dome
from alpaca.filterwheel import FilterWheel
from alpaca.focuser import Focuser
from alpaca.observingconditions import ObservingConditions
from alpaca.switch import Switch
from alpaca.telescope import Telescope
from mw4.base.driverDataClass import DriverData
from mw4.base.tpool import Worker
from PySide6.QtCore import QThreadPool, QTimer
from typing import Any

DEVICE_CLASSES: dict[str, type] = {
    "camera": Camera,
    "dome": Dome,
    "focuser": Focuser,
    "filterwheel": FilterWheel,
    "telescope": Telescope,
    "covercalibrator": CoverCalibrator,
    "observingconditions": ObservingConditions,
    "switch": Switch,
}


class AlpacaClass(DriverData):
    ALPACA_TIMEOUT: int = 3

    def __init__(self, parent: Any) -> None:
        super().__init__(parent.data)
        self.app: Any = parent.app
        self.msg: Any = parent.app.msg
        self.data: dict = parent.data
        self.signals: Any = parent.signals
        self.threadPool: QThreadPool = parent.app.threadPool
        self.updateRate: int = 1000
        self.loadConfig: bool = False
        self._host: tuple[str, int] = ("localhost", 11111)
        self._port: int = 11111
        self._hostaddress: str = "localhost"
        self.protocol: str = "http"
        self.apiVersion: int = 1
        self._deviceName: str = ""
        self.deviceType: str = ""
        self.number: int = 0
        self._device: Device | None = None

        self.defaultConfig: dict[str, Any] = {
            "deviceName": "",
            "deviceList": [],
            "hostaddress": "localhost",
            "port": 11111,
            "apiVersion": 1,
            "user": "",
            "password": "",
            "updateRate": 1000,
        }

        self.deviceConnected: bool = False
        self.serverConnected: bool = False
        self.worker: Worker | None = None
        self.workerGetConfig: Worker | None = None
        self.workerStatus: Worker | None = None
        self.workerData: Worker | None = None
        self.workerConnect: Worker | None = None

        self.cycleDevice: QTimer = QTimer()
        self.cycleDevice.setSingleShot(False)
        self.cycleDevice.timeout.connect(self.pollStatus)
        self.cycleData: QTimer = QTimer()
        self.cycleData.setSingleShot(False)
        self.cycleData.timeout.connect(self.pollData)

    def _rebuildDevice(self) -> None:
        cls = DEVICE_CLASSES.get(self.deviceType)
        if cls:
            self._device = cls(
                f"{self._hostaddress}:{self._port}", self.number, self.protocol
            )

    @property
    def host(self) -> tuple[str, int]:
        return self._host

    @host.setter
    def host(self, value: tuple[str, int]) -> None:
        self._host = value

    @property
    def hostaddress(self) -> str:
        return self._hostaddress

    @hostaddress.setter
    def hostaddress(self, value: str) -> None:
        self._hostaddress = value
        self._host = (self._hostaddress, self._port)
        self._rebuildDevice()

    @property
    def port(self) -> int:
        return self._port

    @port.setter
    def port(self, value: int | str) -> None:
        self._port = int(value)
        self._host = (self._hostaddress, self._port)
        self._rebuildDevice()

    @property
    def baseUrl(self) -> str:
        return self.generateBaseUrl()

    @property
    def deviceName(self) -> str:
        return self._deviceName

    @deviceName.setter
    def deviceName(self, value: str) -> None:
        self._deviceName = value
        valueSplit = value.split(":")
        if len(valueSplit) != 3:
            return
        self.deviceType = valueSplit[1].strip()
        self.number = int(valueSplit[2].strip())
        self._rebuildDevice()

    def generateBaseUrl(self) -> str:
        val = (
            f"{self.protocol}://{self.host[0]}:{self.host[1]}"
            f"/api/v{self.apiVersion}/{self.deviceType}/{self.number}"
        )
        return val

    def discoverAPIVersion(self) -> int:
        addr = f"{self._hostaddress}:{self._port}"
        try:
            versions = management.apiversions(addr)
            return versions[0] if versions else 0
        except Exception as e:
            self.log.error(f"Discover API exception: [{e}]")
            return 0

    def discoverAlpacaDevices(self) -> list:
        addr = f"{self._hostaddress}:{self._port}"
        try:
            return management.configureddevices(addr)
        except Exception as e:
            self.log.error(f"Search devices exception: [{e}]")
            return []

    def discoverAlpacaServers(self) -> list[str]:
        """UDP broadcast discovery → list of 'host:port' strings."""
        try:
            return discovery.search_ipv4(numquery=2, timeout=2)
        except Exception as e:
            self.log.error(f"UDP discovery: [{e}]")
            return []

    def workerConnectDevice(self) -> None:
        self.deviceConnected = False
        self.serverConnected = False

        if self._device is None:
            self.msg.emit(2, "ALPACA", "Connect error", f"{self.deviceName}")
            return

        suc = False
        try:
            self._device.Connect()
            for _ in range(50):  # max 5 s
                if not self._device.Connecting:
                    break
                time.sleep(0.1)
            suc = bool(self._device.Connected)
        except Exception as e:
            self.log.error(f"[{self.deviceName}] connect error: [{e}]")

        if not suc:
            self.msg.emit(2, "ALPACA", "Connect error", f"{self.deviceName}")
            return

        if not self.serverConnected:
            self.serverConnected = True
            self.signals.serverConnected.emit()

        if not self.deviceConnected:
            self.deviceConnected = True
            self.signals.deviceConnected.emit(f"{self.deviceName}")
            self.msg.emit(0, "ALPACA", "Device found", f"{self.deviceName}")
            self.startAlpacaTimer()
            self.getInitialConfig()

    def startAlpacaTimer(self) -> None:
        self.cycleData.start(self.updateRate)
        self.cycleDevice.start(self.updateRate)

    def stopAlpacaTimer(self) -> None:
        self.cycleData.stop()
        self.cycleDevice.stop()

    def workerGetInitialConfig(self) -> None:
        if self._device is None:
            return
        try:
            self.data["DRIVER_INFO.DRIVER_NAME"] = self._device.Name
        except Exception as e:
            self.log.error(f"[{self.deviceName}] get Name error: [{e}]")
        try:
            self.data["DRIVER_INFO.DRIVER_VERSION"] = self._device.DriverVersion
        except Exception as e:
            self.log.error(f"[{self.deviceName}] get DriverVersion error: [{e}]")
        try:
            self.data["DRIVER_INFO.DRIVER_EXEC"] = self._device.DriverInfo
        except Exception as e:
            self.log.error(f"[{self.deviceName}] get DriverInfo error: [{e}]")

    def workerPollStatus(self) -> None:
        if self._device is None:
            return
        try:
            suc = bool(self._device.Connected)
        except Exception as e:
            self.log.error(f"[{self.deviceName}] poll status error: [{e}]")
            suc = False

        if self.deviceConnected and not suc:
            self.deviceConnected = False
            self.signals.deviceDisconnected.emit(f"{self.deviceName}")
            self.msg.emit(0, "ALPACA", "Device remove", f"{self.deviceName}")

        elif not self.deviceConnected and suc:
            self.deviceConnected = True
            self.signals.deviceConnected.emit(f"{self.deviceName}")
            self.msg.emit(0, "ALPACA", "Device found", f"{self.deviceName}")

    def processPolledData(self) -> None:
        pass

    def workerPollData(self) -> None:
        pass

    def pollData(self) -> None:
        if not self.deviceConnected:
            return
        self.workerData = Worker(self.workerPollData)
        self.workerData.signals.result.connect(self.processPolledData)
        self.threadPool.start(self.workerData)

    def pollStatus(self) -> None:
        if not self.deviceConnected:
            return
        self.workerStatus = Worker(self.workerPollStatus)
        self.threadPool.start(self.workerStatus)

    def getInitialConfig(self) -> None:
        if not self.deviceConnected:
            return
        self.workerGetConfig = Worker(self.workerGetInitialConfig)
        self.threadPool.start(self.workerGetConfig)

    def startCommunication(self) -> None:
        self.data.clear()
        self.workerConnect = Worker(self.workerConnectDevice)
        self.threadPool.start(self.workerConnect)

    def stopCommunication(self) -> None:
        self.stopAlpacaTimer()
        if self._device is not None:
            with contextlib.suppress(Exception):
                self._device.Connected = False
        self.deviceConnected = False
        self.serverConnected = False
        self.signals.deviceDisconnected.emit(f"{self.deviceName}")
        self.signals.serverDisconnected.emit({f"{self.deviceName}": 0})
        self.msg.emit(0, "ALPACA", "Device  remove", f"{self.deviceName}")

    def discoverDevices(self, deviceType: str) -> list:
        servers = self.discoverAlpacaServers()
        manual = f"{self._hostaddress}:{self._port}"
        if manual not in servers:
            servers.append(manual)

        allDevices: list = []
        for addr in servers:
            with contextlib.suppress(Exception):
                allDevices.extend(management.configureddevices(addr))

        temp = [x for x in allDevices if x["DeviceType"].lower() == deviceType]
        return [f"{x['DeviceName']}:{deviceType}:{x['DeviceNumber']}" for x in temp]
