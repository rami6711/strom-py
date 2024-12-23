# Strom HW class

from machine import Pin, PWM, ADC, I2C
from micropython import const
from neopixel import NeoPixel
import time

# display
import ssd1306
from fb_plus import fbadd
# from bmp_rd import BMPReader

# sensors
from hdc1080 import HDC1080
from veml7700 import VEML7700
from ina226 import INA226

BTN_IDLE = const(0)
BTN_SHORT = const(1)
BTN_LONG = const(2)
TIME_SHORT = const(100)
TIME_LONG = const(1000)

def bmp_to_oled(r,g,b):
    ''' convert bmp color to oled color for BMPReader '''
    if (r>127)|(g>127)|(b>127):
        # white dot is off
        return 0
    else:
        # black dot is on
        return 1

class STROM():
    def __init__(self):
        # Pin[21] - Input, button SW1
        # Pin[5] - Input, button SW2
        self.sw1 = Pin(21, Pin.IN, Pin.PULL_UP)
        self.sw2 = Pin(5, Pin.IN, Pin.PULL_UP)
        self.sw1.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self.button_handler)
        self.sw2.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self.button_handler)
        self.sw_time = time.ticks_ms()
        self.sw1_state = BTN_IDLE
        self.sw2_state = BTN_IDLE

        # Pin[0] - Analog input, ambient light
        # ATTN_0DB    ~ 100mV - 950mV
        # ATTN_2_5DB  ~ 100mV - 1250mV
        # ATTN_6DB    ~ 150mV - 1750mV
        # ATTN_11DB   ~ 150mV - 2450mV
        self.ambient = ADC(0)
        self.ambient.atten(self.ambient.ATTN_11DB)

        # Pin[1] - Neopixel Output, 37 x WS2812
        # 2+4+5+5+7+7+7 pixels
        self.np = NeoPixel(Pin(1, Pin.OUT), 37)
        # self.np = NeoPixel(Pin(1, Pin.OUT), 16*32)

        # Pin[2] - GPIO2, free pad
        # Pin[3] - GPIO3, free pad

        # Pin[4] - PWM output, buzzer
        self.buzzer = PWM(Pin(4), freq=5000, duty_u16=32768)
        self.buzzer.deinit()

        # Pin[6] - SDA, I2C data
        # Pin[7] - SCL, I2C clock
        self.i2c = I2C(0, scl=Pin(7), sda=Pin(6), freq=100000)

        # Pin[8] - PWM output, blue LED on module
        self.led = PWM(Pin(8), freq=1000, duty_u16=2**16-1)

        # Pin[9] - NC, Boot button
        self.boot = Pin(9, Pin.IN, Pin.PULL_UP)

        # Pin[10] - Output, +5V enable, supply for WS2812
        # Active high
        self.v5en = Pin(10, Pin.OUT)
        self.v5en.value(0)

        # Pin[20] - Input, Alert from INA226 and TPS25200
        self.alert = Pin(20, Pin.IN, Pin.PULL_UP)
        self.alert.irq(trigger=Pin.IRQ_FALLING, handler=self.alert_handler)

        # init
        self.start_up()

    def start_up(self):
        # blue LED init
        self.set_bled(0x10)
        self.bled_toggle()

        # Enable 5V for WS2812
        self.v5en.value(1)

        # Scan I2C bus
        i2c_devs = self.i2c.scan()

        if 0x3C in i2c_devs:
            self.oled_width = 128
            self.oled_height = 64
            self.oled = ssd1306.SSD1306_I2C(self.oled_width, self.oled_height, self.i2c)
            self.oled.fill(0)
            self.oled.invert(False)
            self.fb = fbadd(self.oled.get_fb())
            self.oled.show()
        else:
            print('Error: OLED display not found')
            # raise OSError('Error: OLED display not found')

        if 0x10 in i2c_devs:
            self.veml = VEML7700(i2c=self.i2c, it=400, gain=1/8)
        else:
            print('Error: VEML7700 not found')
            # raise OSError('Error: VEML7700 not found')

        if 0x40 in i2c_devs:
            self.hdc = HDC1080(self.i2c)
        else:
            print('Error: HDC1080 not found')
            # raise OSError('Error: HDC1080 not found')

        if 0x45 in i2c_devs:
            self.ina = INA226(self.i2c, 0x45)
            self.ina.set_config(0x4B27)
            self.ina.set_current_lsb(0.0001)
            self.ina.set_calibration(2048)
            # wait for first sample (Ttotal = 563.2ms)
            # time.sleep_ms(600)
        else:
            print('Error: INA226 not found')
            # raise OSError('Error: INA226 not found')

    def set_bled(self, value):
        # True: ON, False: OFF
        if type(value) == bool:
            if value:
                value = 0
            else:
                value = 2**16-1
        # 0: OFF, ... 255: ON
        elif type(value) == int:
            if value < 0:
                value = 0
            if value > 255:
                value = 255
            value = (255 - value) * 0x101
        if (value != 2**16-1):
            self.bled_setup = value
        self.bled_value = value
        self.led.duty_u16(value)

    def bled_toggle(self):
        if self.bled_value == 2**16-1:
            # Off -> On
            self.bled_value = self.bled_setup
            self.led.duty_u16(self.bled_setup)
        else:
            # On -> Off
            self.bled_value = 2**16-1
            self.led.duty_u16(2**16-1)

    def button_handler(self, pin):
        if pin.value() == 0:
            # pressed
            self.sw_time = time.ticks_ms()
        else:
            # released
            new_state = BTN_IDLE
            if (time.ticks_ms() - self.sw_time) > TIME_LONG:
                new_state = BTN_LONG
            elif (time.ticks_ms() - self.sw_time) > TIME_SHORT:
                new_state = BTN_SHORT
            # store result
            if pin == self.sw1:
                self.sw1_state = new_state
            elif pin == self.sw2:
                self.sw2_state = new_state

    def get_buttons(self):
        retval = (self.sw1_state, self.sw2_state)
        self.sw1_state = BTN_IDLE
        self.sw2_state = BTN_IDLE
        return retval

    def alert_handler(self, pin):
        if pin.value() == 0: 
            self.v5en.value(0)
            print('>> Alert')
