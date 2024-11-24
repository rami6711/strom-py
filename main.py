# Strom @ ESP32-C3 Super Mini

from machine import Pin, PWM, ADC, I2C, SoftI2C
from neopixel import NeoPixel
import time
import ssd1306
from fb_plus import fbadd
from bmp_rd import BMPReader
# import sleeep

# sensors
from hdc1080 import HDC1080
from veml7700 import VEML7700
from ina226 import INA226

# Pin[21] - Input, button SW1
# Pin[5] - Input, button SW2
sw1 = Pin(21, Pin.IN, Pin.PULL_UP)
sw2 = Pin(5, Pin.IN, Pin.PULL_UP)

# Pin[0] - Analog input, ambient light
# ATTN_0DB    ~ 100mV - 950mV
# ATTN_2_5DB  ~ 100mV - 1250mV
# ATTN_6DB    ~ 150mV - 1750mV
# ATTN_11DB   ~ 150mV - 2450mV
ambient = ADC(0)
ambient.atten(ambient.ATTN_11DB)

# Pin[1] - Neopixel Output, N x WS2812
pinWS2812 = Pin(1, Pin.OUT)
np = NeoPixel(pinWS2812, 37)   # 2+4+5+5+7+7+7 pixels

# Pin[4] - PWM output, buzzer
buzz = PWM(Pin(4), freq=5000, duty_u16=32768)
buzz.deinit()

# Pin[6] - SDA, I2C data
# Pin[7] - SCL, I2C clock
i2c = I2C(0, scl=Pin(7), sda=Pin(6), freq=100000)

# Pin[8] - PWM output, blue LED
led_b = Pin(8, Pin.OUT)

# Pin[9] - NC, Boot button
bootPin = Pin(9, Pin.IN, Pin.PULL_UP)

# Pin[10] - V5en, 5V enable (active high)
v5en = Pin(10, Pin.OUT)
v5en.value(0)

# Pin[20] - Alert, alert signal (active low)
alert = Pin(20, Pin.IN, Pin.PULL_UP)


# Start-up
def startup():
    led_b.value(0)          # ON
    buzz.init()
    time.sleep_ms(100)      # sleep for 0.2 second
    buzz.deinit()
    led_b.value(1)          # OFF
    time.sleep_ms(200)      # sleep for 0.2 second
    led_b.value(0)          # ON
    buzz.init()
    time.sleep_ms(100)      # sleep for 0.2 second
    buzz.deinit()
    led_b.value(1)          # OFF
    print("start up")

def bmp_to_oled(r,g,b):
    if (r>127)|(g>127)|(b>127):
        # white dot is off
        return 0
    else:
        # black dot is on
        return 1

def demo():
    startup()

    # Enable 5V for WS2812
    v5en.value(1)
    time.sleep_ms(100)

    # Set minimal intensity for all LEDs
    for i in range(np.__len__()):
       np[i] = (5, 0, 0)
       time.sleep_ms(100)
       np.write()
       print('.', end='')
    print('')

    print('ADC value: ' + str(ambient.read_uv()/1000) + 'mV')
    i2c_devs = i2c.scan()
    print('I2C scan: ' + str(i2c_devs))

    if 0x3C in i2c_devs:
        print('\n>>> OLED display found')
        oled_width = 128
        oled_height = 64
        global oled
        oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)
        oled.fill(0)
        oled.invert(False)
        # set last pixel on
        oled.pixel(127, 63, 1)

        global fb
        fb = fbadd(oled.get_fb())

        # Radio buttons
        fb.circle(16,7,7,1)
        fb.circle(34,7,7,1)
        fb.circle(34,7,4,1,True)
        fb.circle(52,7,7,1)

        logo = BMPReader("mpy_logo48x48.bmp", user_convert=bmp_to_oled).get_pixels()
        fb.img(0,16,logo)

        fb.setText32(7,5,3,0,3)
        fb.putText32('TEST3',48,24,1)
        fb.setText32(5,3,1,0,3)
        fb.putText32('ABCDEFGH',48,42,1)

        oled.show()

    if 0x10 in i2c_devs:
        print('\n>>> VEML7700 found')
        global veml_sen
        veml_sen = VEML7700(i2c=i2c, it=400, gain=1/8)
        print('Ambient light: ' + str(veml_sen.read_lux()))
    
    if 0x40 in i2c_devs:
        print('\n>>> HDC1080 found')
        global th_sen
        th_sen = HDC1080(i2c)
        print('Temperature: ' + str(th_sen.temperature()) + 'C')
        print('Humidity: ' + str(th_sen.humidity()) + '%')

    if 0x45 in i2c_devs:
        print('\n>>> INA226 found')
        global ina_sen
        ina_sen = INA226(i2c, 0x45)
        ina_sen.set_config(0x4B27)
        ina_sen.set_current_lsb(0.0001)
        ina_sen.set_calibration(2048)
        # wait for first sample (Ttotal = 563.2ms)
        time.sleep_ms(600)
        print('Bus voltage: ' + str(ina_sen.bus_voltage) + 'V')
        print('Shunt voltage: ' + str(1000*ina_sen.shunt_voltage) + 'mV')
        print('Current: ' + str(ina_sen.current) + 'A')
        print('Power: ' + str(ina_sen.power) + 'W')

    if sw1.value() == 0:
        print('Display off')
        oled.fill(0)
        oled.show()

# Main
print('Press SW2 to skip demo')
if sw2.value() == 1:
    demo()
else:
    print('Exit to REPL')


