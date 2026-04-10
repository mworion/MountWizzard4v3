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
import time
from alpaca.device import Device
from alpaca import management
from alpaca.exceptions import NotImplementedException as AlpacaNotImplemented
from mw4.base.driverDataClass import DriverData
from mw4.base.tpool import Worker
from PySide6.QtCore import QThreadPool, QTimer
from typing import Any


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
        self.propertyExceptions: list[str] = []
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
        if self.deviceType:
            address = f"{self._hostaddress}:{self._port}"
            self._device = Device(address, self.deviceType, self.number, self.protocol)

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
        val = f"{self.protocol}://{self.host[0]}:{self.host[1]}/api/v{self.apiVersion}/{self.deviceType}/{self.number}"
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

    def getAlpacaProperty(self, valueProp: str, **data) -> Any:
        if not self.deviceName or self._device is None:
            return []
        if valueProp in self.propertyExceptions:
            return []

        self.log.trace(f"[{self.deviceName}], get [{valueProp}], data:[{data}]")

        try:
            value = self._device._get(valueProp, tmo=self.ALPACA_TIMEOUT, **data)
            if valueProp != "imagearray":
                self.log.trace(f"[{self.deviceName}], response: [{value}]")
            else:
                self.log.trace(f"[{self.deviceName}] imagearray received")
            return value
        except AlpacaNotImplemented:
            self.log.warning(f"[{self.deviceName}] [{valueProp}] not implemented")
            self.propertyExceptions.append(valueProp)
            return []
        except Exception as e:
            self.log.error(f"[{self.deviceName}] get [{valueProp}] error: [{e}]")
            return []

    def setAlpacaProperty(self, valueProp: str, **data) -> dict:
        if not self.deviceName or self._device is None:
            return {}
        if valueProp in self.propertyExceptions:
            return {}

        self.log.trace(f"[{self.deviceName}], set [{valueProp}] to: [{data}]")

        try:
            result = self._device._put(valueProp, tmo=self.ALPACA_TIMEOUT, **data)
            self.log.trace(f"[{self.deviceName}], response: [{result}]")
            return result
        except AlpacaNotImplemented:
            self.log.warning(f"[{self.deviceName}] [{valueProp}] not implemented")
            self.propertyExceptions.append(valueProp)
            return {}
        except Exception as e:
            self.log.error(f"[{self.deviceName}] set [{valueProp}] error: [{e}]")
            return {}

    def getAndStoreAlpacaProperty(self, valueProp: str, element: str) -> None:
        value = self.getAlpacaProperty(valueProp)
        self.storePropertyToData(value, element)

    def workerConnectDevice(self) -> None:
        self.propertyExceptions = []
        self.deviceConnected = False
        self.serverConnected = False

        if self._device is None:
            self.msg.emit(2, "ALPACA", "Connect error", f"{self.deviceName}")
            return

        suc = False
        for retry in range(10):
            try:
                self._device.Connected = True
                suc = bool(self._device.Connected)
                if suc:
                    self.log.debug(f"[{self.deviceName}] connected, [{retry}] retries")
                    break
                else:
                    self.log.info(f"[{self.deviceName}] Connection retry: [{retry}]")
                    time.sleep(0.2)
            except Exception as e:
                self.log.info(f"[{self.deviceName}] retry [{retry}]: [{e}]")
                time.sleep(0.2)

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
        self.data["DRIVER_INFO.DRIVER_NAME"] = self.getAlpacaProperty("name")
        self.data["DRIVER_INFO.DRIVER_VERSION"] = self.getAlpacaProperty("driverversion")
        self.data["DRIVER_INFO.DRIVER_EXEC"] = self.getAlpacaProperty("driverinfo")

    def workerPollStatus(self) -> None:
        suc = self.getAlpacaProperty("connected")
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
            try:
                self._device.Connected = False
            except Exception:
                pass
        self.deviceConnected = False
        self.serverConnected = False
        self.propertyExceptions = []
        self.signals.deviceDisconnected.emit(f"{self.deviceName}")
        self.signals.serverDisconnected.emit({f"{self.deviceName}": 0})
        self.msg.emit(0, "ALPACA", "Device  remove", f"{self.deviceName}")

    def discoverDevices(self, deviceType: str) -> list:
        devices = self.discoverAlpacaDevices()
        if not devices:
            return []

        temp = [x for x in devices if x["DeviceType"].lower() == deviceType]
        discoverList = [f"{x['DeviceName']}:{deviceType}:{x['DeviceNumber']}" for x in temp]
        return discoverList
