import time
import logging

from bgapi.module import BlueGigaServer, PROCEDURE
from bgapi.cmd_def import RESULT_CODE

ser = "COM9"

logger = logging.getLogger("bgapi")


class BlePiHAT(BlueGigaServer):
    PCT2075_I2C_ADDR = 0x90  # 7-bit = 0x48
    _temperature = []
    def get_temperature(self):
        self.start_procedure(PROCEDURE)
        self._api.ble_cmd_hardware_i2c_read(address=self.PCT2075_I2C_ADDR, stop=1, length=2)
        self.wait_for_procedure(timeout=1)
        if len(self._temperature) < 2:
            raise Exception("Failed to read temperature from BlePiHAT.")
        temperature_int = (ord(self._temperature[0]) << 3) + (ord(self._temperature[1]) >> 5)
        if temperature_int < 0x400:
            return float(temperature_int) * 0.125
        else:
            return float(((~temperature_int) & 0x7FF) + 1) * -0.125

    def ble_rsp_hardware_i2c_read(self, result, data):
        logger.info("RSP-Hardware I2C Read: [%s] %s" % (RESULT_CODE[result], "".join(["%02X" % ord(i) for i in data])))
        self._temperature = data
        self.procedure_complete(PROCEDURE)

if __name__ == "__main__":
    device = BlePiHAT(ser, baud=115200, timeout=0.1)
    device.pipe_logs_to_terminal()
    device.get_ble_address(timeout=3)
    print "Temperature: %fC" % (device.get_temperature())
