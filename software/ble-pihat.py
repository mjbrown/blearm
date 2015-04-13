import time
import logging

from bgapi.module import BlueGigaServer, PROCEDURE
from bgapi.cmd_def import RESULT_CODE

ser = "COM16"

logger = logging.getLogger("bgapi")


class BlePiHAT(BlueGigaServer):
    PCT2075_I2C_ADDR = 0x90  # 7-bit = 0x48
    MMA8451_I2C_ADDR = 0x38

    _temperature = []
    _last_analog = None

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

    def ble_evt_hardware_adc_result(self, input, value):
        logger.info("EVT-Hardware ADC Result: input - %d; value - %x" % (input, value))

    def get_accel(self):
        self.start_procedure(PROCEDURE)
        self._api.ble_cmd_hardware_i2c_read(address=self.MMA8451_I2C_ADDR, stop=1, length=2)
        self.wait_for_procedure(timeout=1)

    def set_pwm(self, channel, duty):
        #self.start_procedure(PROCEDURE)
        self._api.ble_cmd_hardware_timer_comparator(timer=1, channel=channel, mode=4, comparator_value=duty*4)

    def analog_read(self, channel):
        self._api.ble_cmd_hardware_adc_read(input=channel, decimation=3, reference_selection=2)

    def spi_write(self, data):
        #self._api.ble_cmd_hardware_io_port_write(port=0, mask=0x04, data=0xFF)
        self._api.ble_cmd_hardware_io_port_write(port=0, mask=0x04, data=0x00)
        self._api.ble_cmd_hardware_spi_transfer(channel=1, data=data)
        time.sleep(0.05)
        self._api.ble_cmd_hardware_io_port_write(port=0, mask=0x04, data=0xFF)

    def ble_rsp_hardware_spi_transfer(self, result, channel, data):
        logger.info("RSP-Hardware SPI Read - Result:[%s] - Channel: %d - Data: %s" % (RESULT_CODE[result], channel, "".join(["%02X" % ord(i) for i in data])))

if __name__ == "__main__":
    device = BlePiHAT(ser, baud=115200, timeout=0.1)
    device.pipe_logs_to_terminal()
    device.get_ble_address(timeout=3)
    print "Temperature: %fC" % (device.get_temperature())
    device._api.ble_cmd_hardware_io_port_config_direction(port=1, direction=0xDF)
    device._api.ble_cmd_hardware_io_port_write(port=1, mask=0x08, data=0xFF)
    device._api.ble_cmd_hardware_spi_config(channel=1, polarity=0, phase=1, bit_order=1, baud_e=11, baud_m=216)
    device._api.ble_cmd_hardware_io_port_config_direction(port=0, direction=0xDC)

    device._api.ble_cmd_hardware_io_port_write(port=0, mask=0x04, data=0xFF)
    device.spi_write(data="\x10\x02\x00\x00\x00")
    time.sleep(0.2)
    device.spi_write(data="\x50\x02\x20\x54\x00")
    time.sleep(0.2)
    device.spi_write(data="\xF0")
    time.sleep(0.2)
    device.spi_write(data="\xF1")
    time.sleep(0.2)
    device.spi_write(data="\xF2")
    time.sleep(0.2)
    device.spi_write(data="\x50\x02\x27\x54\x00")
    time.sleep(0.2)
    #exit(1)
    #device.spi_write(data="\x50\x01\x03")
    #time.sleep(0.05)
    #device.spi_write(data="\x51\x01\x32")
    #device.analog_read(0)
    #time.sleep(0.5)
    #device.analog_read(1)
    #time.sleep(0.5)
    #device.analog_read(0xE)
    #time.sleep(0.5)
    for i in range(200):
        device.spi_write(data="\x01\x00\x00\x00")
        time.sleep(0.05)
    time.sleep(0.5)