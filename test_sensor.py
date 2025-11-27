# Testscript for testing the sensor with an Raspberry Pi Pico 2W
# SDA -> GP0
# SCL -> GP1
from machine import Pin, I2C
from hdc2080 import HDC2080, TEMP_AND_HUMID, MANUAL
import time

i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)

sensor = HDC2080(i2c, addr=0x40)

if not sensor.is_connected():
    print("HDC2080 not connected.")
else:
    print("HDC2080 connected.")

    sensor.reset()
    sensor.set_measurement_mode(TEMP_AND_HUMID)
    sensor.set_rate(MANUAL)

    while True:
        sensor.trigger_measurement()
        # Measurement time according to datasheet typically a few ms – small pause
        time.sleep_ms(20)
        t = sensor.read_temp()
        h = sensor.read_humidity()
        print("T = %.2f °C, RH = %.2f %%" % (t, h))
        time.sleep(1)
