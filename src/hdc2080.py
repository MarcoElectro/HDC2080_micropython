# MicroPython HDC2080 Temperature and Humidity Sensor Driver by Marco R.
# Ported from Arduino Library https://github.com/libdriver/hdc2080/blob/main/src/driver_hdc2080.c
# Repository: https://github.com/MarcoElectro/HDC2080_micropython
from machine import I2C
import time

# Register Map
TEMP_LOW          = 0x00
TEMP_HIGH         = 0x01
HUMID_LOW         = 0x02
HUMID_HIGH        = 0x03
INTERRUPT_DRDY    = 0x04
TEMP_MAX          = 0x05
HUMID_MAX         = 0x06
INTERRUPT_CONFIG  = 0x07
TEMP_OFFSET_ADJ   = 0x08
HUM_OFFSET_ADJ    = 0x09
TEMP_THR_L        = 0x0A
TEMP_THR_H        = 0x0B
HUMID_THR_L       = 0x0C
HUMID_THR_H       = 0x0D
CONFIG            = 0x0E
MEAS_CFG          = 0x0F
MID_L             = 0xFC
MID_H             = 0xFD
DEVICE_ID_L       = 0xFE
DEVICE_ID_H       = 0xFF

# Constants for settings
FOURTEEN_BIT = 0
ELEVEN_BIT   = 1
NINE_BIT     = 2

TEMP_AND_HUMID = 0
TEMP_ONLY      = 1
HUMID_ONLY     = 2

MANUAL       = 0
TWO_MINS     = 1
ONE_MINS     = 2
TEN_SECONDS  = 3
FIVE_SECONDS = 4
ONE_HZ       = 5
TWO_HZ       = 6
FIVE_HZ      = 7

ACTIVE_LOW  = 0
ACTIVE_HIGH = 1

LEVEL_MODE      = 0
COMPARATOR_MODE = 1


class HDC2080:
    def __init__(self, i2c: I2C, addr: int = 0x40):
        self.i2c = i2c
        self.addr = addr

    def is_connected(self) -> bool:
        return self.addr in self.i2c.scan()

    # Low-Level Register Access
    def _write_reg(self, reg: int, value: int):
        self.i2c.writeto_mem(self.addr, reg, bytes([value & 0xFF]))

    def _read_reg(self, reg: int) -> int:
        return int.from_bytes(self.i2c.readfrom_mem(self.addr, reg, 1), "little")

    # Temperature / Humidity
    def read_temp(self) -> float:
        low = self._read_reg(TEMP_LOW)
        high = self._read_reg(TEMP_HIGH)
        raw = (high << 8) | low
        f = float(raw)
        #((raw * 165) / 65536) - 40.5
        f = (f * 165.0 / 65536.0) - 40.5
        return f

    def read_humidity(self) -> float:
        low = self._read_reg(HUMID_LOW)
        high = self._read_reg(HUMID_HIGH)
        raw = (high << 8) | low
        f = float(raw)
        f = f / 65536.0 * 100.0
        return f

    # Offset‑Register
    def read_temp_offset_adjust(self) -> int:
        return self._read_reg(TEMP_OFFSET_ADJ)

    def set_temp_offset_adjust(self, value: int) -> int:
        self._write_reg(TEMP_OFFSET_ADJ, value)
        return self.read_temp_offset_adjust()

    def read_humidity_offset_adjust(self) -> int:
        return self._read_reg(HUM_OFFSET_ADJ)

    def set_humidity_offset_adjust(self, value: int) -> int:
        self._write_reg(HUM_OFFSET_ADJ, value)
        return self.read_humidity_offset_adjust()

    # Heater
    def enable_heater(self):
        c = self._read_reg(CONFIG)
        c |= 0x08
        self._write_reg(CONFIG, c)

    def disable_heater(self):
        c = self._read_reg(CONFIG)
        c &= 0xF7
        self._write_reg(CONFIG, c)

    # Thresholds
    def set_low_temp(self, temp_c: float):
        if temp_c < -40.0:
            temp_c = -40.0
        elif temp_c > 125.0:
            temp_c = 125.0
        val = int(256.0 * (temp_c + 40.0) / 165.0) & 0xFF
        self._write_reg(TEMP_THR_L, val)

    def set_high_temp(self, temp_c: float):
        if temp_c < -40.0:
            temp_c = -40.0
        elif temp_c > 125.0:
            temp_c = 125.0
        val = int(256.0 * (temp_c + 40.0) / 165.0) & 0xFF
        self._write_reg(TEMP_THR_H, val)

    def set_high_humidity(self, rh: float):
        if rh < 0.0:
            rh = 0.0
        elif rh > 100.0:
            rh = 100.0
        val = int(256.0 * rh / 100.0) & 0xFF
        self._write_reg(HUMID_THR_H, val)

    def set_low_humidity(self, rh: float):
        if rh < 0.0:
            rh = 0.0
        elif rh > 100.0:
            rh = 100.0
        val = int(256.0 * rh / 100.0) & 0xFF
        self._write_reg(HUMID_THR_L, val)

    # Thresholds read
    def read_low_humidity_threshold(self) -> float:
        v = self._read_reg(HUMID_THR_L)
        return float(v) * 100.0 / 256.0

    def read_high_humidity_threshold(self) -> float:
        v = self._read_reg(HUMID_THR_H)
        return float(v) * 100.0 / 256.0

    def read_low_temp_threshold(self) -> float:
        v = self._read_reg(TEMP_THR_L)
        return float(v) * 165.0 / 256.0 - 40.0

    def read_high_temp_threshold(self) -> float:
        v = self._read_reg(TEMP_THR_H)
        return float(v) * 165.0 / 256.0 - 40.0

    # Resolution
    def set_temp_res(self, resolution: int):
        c = self._read_reg(MEAS_CFG)
        if resolution == FOURTEEN_BIT:
            c &= 0x3F
        elif resolution == ELEVEN_BIT:
            c &= 0x7F
            c |= 0x40
        elif resolution == NINE_BIT:
            c &= 0xBF
            c |= 0x80
        else:
            c &= 0x3F
        self._write_reg(MEAS_CFG, c)

    def set_humid_res(self, resolution: int):
        c = self._read_reg(MEAS_CFG)
        if resolution == FOURTEEN_BIT:
            c &= 0xCF
        elif resolution == ELEVEN_BIT:
            c &= 0xDF
            c |= 0x10
        elif resolution == NINE_BIT:
            c &= 0xEF
            c |= 0x20
        else:
            c &= 0xCF
        self._write_reg(MEAS_CFG, c)

    # Measurement mode
    def set_measurement_mode(self, mode: int):
        c = self._read_reg(MEAS_CFG)
        if mode == TEMP_AND_HUMID:
            c &= 0xF9
        elif mode == TEMP_ONLY:
            c &= 0xFC
            c |= 0x02
        elif mode == HUMID_ONLY:
            c &= 0xFD
            c |= 0x04
        else:
            c &= 0xF9
        self._write_reg(MEAS_CFG, c)

    # Trigger measurement
    def trigger_measurement(self):
        c = self._read_reg(MEAS_CFG)
        c |= 0x01
        self._write_reg(MEAS_CFG, c)

    # Reset
    def reset(self):
        c = self._read_reg(CONFIG)
        c |= 0x80
        self._write_reg(CONFIG, c)
        time.sleep_ms(50)

    # Interrupt-Pin enable/disable
    def enable_interrupt(self):
        c = self._read_reg(CONFIG)
        c |= 0x04
        self._write_reg(CONFIG, c)

    def disable_interrupt(self):
        c = self._read_reg(CONFIG)
        c &= 0xFB
        self._write_reg(CONFIG, c)

    # Measurement rate
    def set_rate(self, rate: int):
        c = self._read_reg(CONFIG)
        if rate == MANUAL:
            c &= 0x8F
        elif rate == TWO_MINS:
            c &= 0x9F
            c |= 0x10
        elif rate == ONE_MINS:
            c &= 0xAF
            c |= 0x20
        elif rate == TEN_SECONDS:
            c &= 0xBF
            c |= 0x30
        elif rate == FIVE_SECONDS:
            c &= 0xCF
            c |= 0x40
        elif rate == ONE_HZ:
            c &= 0xDF
            c |= 0x50
        elif rate == TWO_HZ:
            c &= 0xEF
            c |= 0x60
        elif rate == FIVE_HZ:
            c |= 0x70
        else:
            c &= 0x8F
        self._write_reg(CONFIG, c)

    # Interrupt-Polarity & Mode
    def set_interrupt_polarity(self, polarity: int):
        c = self._read_reg(CONFIG)
        if polarity == ACTIVE_LOW:
            c &= 0xFD
        elif polarity == ACTIVE_HIGH:
            c |= 0x02
        else:
            c &= 0xFD
        self._write_reg(CONFIG, c)

    def set_interrupt_mode(self, mode: int):
        c = self._read_reg(CONFIG)
        if mode == LEVEL_MODE:
            c &= 0xFE
        elif mode == COMPARATOR_MODE:
            c |= 0x01
        else:
            c &= 0xFE
        self._write_reg(CONFIG, c)

    def read_interrupt_status(self) -> int:
        return self._read_reg(INTERRUPT_DRDY)

    # Max values
    def clear_max_temp(self):
        self._write_reg(TEMP_MAX, 0x00)

    def clear_max_humidity(self):
        self._write_reg(HUMID_MAX, 0x00)

    def read_max_temp(self) -> float:
        v = self._read_reg(TEMP_MAX)
        return float(v) * 165.0 / 256.0 - 40.0

    def read_max_humidity(self) -> float:
        v = self._read_reg(HUMID_MAX)
        return float(v) / 256.0 * 100.0

    # Threshold/DRDY Interrupts
    def enable_threshold_interrupt(self):
        c = self._read_reg(INTERRUPT_CONFIG)
        c |= 0x78
        self._write_reg(INTERRUPT_CONFIG, c)

    def disable_threshold_interrupt(self):
        c = self._read_reg(INTERRUPT_CONFIG)
        c &= 0x87
        self._write_reg(INTERRUPT_CONFIG, c)

    def enable_drdy_interrupt(self):
        c = self._read_reg(INTERRUPT_CONFIG)
        c |= 0x80
        self._write_reg(INTERRUPT_CONFIG, c)

    def disable_drdy_interrupt(self):
        c = self._read_reg(INTERRUPT_CONFIG)
        c &= 0x7F
        self._write_reg(INTERRUPT_CONFIG, c)
