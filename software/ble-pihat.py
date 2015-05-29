import time
import logging

from bgapi.module import BlueGigaServer, PROCEDURE
from bgapi.cmd_def import RESULT_CODE

ser = "COM20"

logger = logging.getLogger("bgapi")


class BlePiHAT(BlueGigaServer):
    PCT2075_I2C_ADDR = 0x90  # 7-bit = 0x48
    MMA8451_I2C_ADDR = 0x38

    _temperature = []
    _last_analog = None
    _last_spi_data = None

    def ble_evt_hardware_adc_result(self, input, value):
        logger.info("EVT-Hardware ADC Result: input - %d; value - %x" % (input, value))

    def set_t1pwm(self, channel, duty):
        #self.start_procedure(PROCEDURE)
        self._api.ble_cmd_hardware_timer_comparator(timer=1, channel=channel, mode=4, comparator_value=duty*2)

    def set_t3pwm(self, channel, duty):
        self._api.ble_cmd_hardware_timer_comparator(timer=3, channel=channel, mode=4, comparator_value=duty*.016)

    def set_t4pwm(self, channel, duty):
        self._api.ble_cmd_hardware_timer_comparator(timer=4, channel=channel, mode=4, comparator_value=duty*.016)

    def analog_read(self, channel):
        self._api.ble_cmd_hardware_adc_read(input=channel, decimation=3, reference_selection=2)

    def spi_write(self, data):
        #self._api.ble_cmd_hardware_io_port_write(port=0, mask=0x04, data=0xFF)
        self.start_procedure(PROCEDURE)
        self._api.ble_cmd_hardware_io_port_write(port=0, mask=0x04, data=0x00)
        self._api.ble_cmd_hardware_spi_transfer(channel=1, data=data)
        time.sleep(0.05)
        self._api.ble_cmd_hardware_io_port_write(port=0, mask=0x04, data=0xFF)
        self.wait_for_procedure(timeout=1)
        return self._last_spi_data

    def ble_rsp_hardware_spi_transfer(self, result, channel, data):
        logger.info("RSP-Hardware SPI Read - Result:[%s] - Channel: %d - Data: %s" % (RESULT_CODE[result], channel, "".join(["%02X" % ord(i) for i in data])))
        self._last_spi_data = data
        self.procedure_complete(PROCEDURE)

def Main():
    device = BlePiHAT(ser, baud=115200, timeout=0.1)
    device.pipe_logs_to_terminal()
    device.get_ble_address(timeout=3)
    device._api.ble_cmd_hardware_io_port_config_direction(port=1, direction=0xFF)
    device.set_t1pwm(0, 1500)   # Rotate
    device.set_t1pwm(1, 2000)   # Wrist
    device.set_t1pwm(3, 1500)   # Elbow
    device.set_t1pwm(4, 1200)   # Hand
    device.set_t4pwm(0, 1450)
    device.set_t3pwm(1, 1450)
    time.sleep(1)
    return

    device._api.ble_cmd_hardware_io_port_write(port=1, mask=0x08, data=0xFF)
    time.sleep(1)
    device._api.ble_cmd_hardware_spi_config(channel=1, polarity=0, phase=1, bit_order=1, baud_e=11, baud_m=216)
    device._api.ble_cmd_hardware_io_port_config_direction(port=0, direction=0xDC)

    device._api.ble_cmd_hardware_io_port_write(port=0, mask=0x04, data=0xFF)
    time.sleep(1)
    device.spi_write(data="\xFE")
    time.sleep(0.2)
    device.spi_write(data="\x10\x06\x00\x00\x00\x00\x00\x00\x00") # 10062701200000FF00
    time.sleep(0.2)
    device.spi_write(data="\x50\x02\x07\x23\x20")
    time.sleep(0.2)
    device.spi_write(data="\xF0")
    time.sleep(1)
    #device.spi_write(data="\xF1")
    #time.sleep(1)
    #device.spi_write(data="\xF2")
    #time.sleep(1)
    #device.spi_write(data="\x50\x02\x07\x23\x20")
    #time.sleep(0.2)
    #return
    #exit(1)
    #device.spi_write(data="\x50\x01\x03")
    #time.sleep(0.2)
    #device.spi_write(data="\x51\x01\x23")
    #time.sleep(0.2)
    #device.analog_read(0)
    #time.sleep(0.5)
    #device.analog_read(1)
    #time.sleep(0.5)
    #device.analog_read(0xE)
    #time.sleep(0.5)
    adc_readings = []
    for i in range(10):
        resp = device.spi_write(data="\x01\x00\x00\x00")
        adc_readings += [ (ord(resp[1]) << 16) + (ord(resp[2]) << 8) + ord(resp[3]) ]
        time.sleep(0.05)
    print adc_readings
    print "Average:", sum(adc_readings) / len(adc_readings)
    time.sleep(0.5)

if __name__ == "__main__":
    Main()