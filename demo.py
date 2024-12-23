# Demo of Strom @ ESP32-C3 Super Mini

from strom import STROM
from strom import bmp_to_oled
from bmp_rd import BMPReader
import time
# import machine


def demo():
    # create and initialize STROM instance
    hw = STROM()
    hw.start_up()

    print("demo")
    # 2x blink & beep
    hw.set_bled(True)       # ON
    hw.buzzer.init()
    time.sleep_ms(100)      # sleep for 0.2 second
    hw.buzzer.deinit()
    hw.set_bled(False)      # OFF
    time.sleep_ms(200)      # sleep for 0.2 second
    hw.set_bled(True)       # ON
    hw.buzzer.init()
    time.sleep_ms(100)      # sleep for 0.2 second
    hw.buzzer.deinit()
    hw.set_bled(False)      # OFF

    # Radio buttons
    hw.fb.circle(16,7,7,1)
    hw.fb.circle(34,7,7,1)
    hw.fb.circle(34,7,4,1,True)
    hw.fb.circle(52,7,7,1)
    # Display image
    logo = BMPReader("mpy_logo48x48.bmp", user_convert=bmp_to_oled).get_pixels()
    hw.fb.img(0,16,logo)
    # Display text
    hw.fb.setText32(7,5,3,0,3)
    hw.fb.putText32('TEST3',48,24,1)
    hw.fb.setText32(5,3,1,0,3)
    hw.fb.putText32('ABCDEFGH',48,42,1)

    hw.oled.show()

    # alert on INA226 (0.40A @ 25mOhm)
    hw.ina.set_over_current(0.40, 0.025)
    
    # Set minimal intensity for all LEDs
    print('WS2812 test; press button to finish')
    print('Red:   ', end='')
    button = (0, 0)
    for i in range(hw.np.__len__()):
        if button != (0, 0):
            break
        button = hw.get_buttons()
        hw.np[i] = (10, 0, 0)
        time.sleep_ms(100)
        hw.np.write()
        print('.', end='')
    print('\nGreen: ', end='')
    for i in range(hw.np.__len__()):
        if button != (0, 0):
            break
        button = hw.get_buttons()
        hw.np[i] = (0, 10, 0)
        time.sleep_ms(100)
        hw.np.write()
        print('.', end='')
    print('\nBlue:  ', end='')
    for i in range(hw.np.__len__()):
        if button != (0, 0):
            break
        button = hw.get_buttons()
        hw.np[i] = (0, 0, 10)
        time.sleep_ms(100)
        hw.np.write()
        print('.', end='')
    print('')
    time.sleep_ms(600)

    print('ADC value: ' + str(hw.ambient.read_uv()/1000) + 'mV')
    print('Ambient light: ' + str(hw.veml.read_lux()))

    print('Temperature: ' + str(hw.hdc.temperature()) + 'C')
    print('Humidity: ' + str(hw.hdc.humidity()) + '%')

    print('Bus voltage: ' + str(hw.ina.bus_voltage) + 'V')
    print('Shunt voltage: ' + str(1000 * hw.ina.shunt_voltage) + 'mV')
    print('Current: ' + str(hw.ina.current) + 'A')
    print('Power: ' + str(hw.ina.power) + 'W')

    hw.oled.off()
    hw.set_bled(16)

    return hw
