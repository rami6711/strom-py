# Strom @ ESP32-C3 Super Mini

from strom import STROM
from strom import bmp_to_oled
from bmp_rd import BMPReader
import time

print("start up")
hw = STROM()
hw.start_up()

def demo():
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
    
    # Set minimal intensity for all LEDs
    for i in range(hw.np.__len__()):
       hw.np[i] = (5, 0, 0)
       time.sleep_ms(100)
       hw.np.write()
       print('.', end='')
    print('')

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

# Main
print('Press SW2 to skip demo')
if hw.sw2.value() == 1:
    demo()
else:
    print('Exit to REPL')


