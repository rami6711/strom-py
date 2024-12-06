# Strom @ ESP32-C3 Super Mini
# import demo
from strom import STROM
from strom import bmp_to_oled
from bmp_rd import BMPReader
import time
import random
from micropython import const

COLOR_MAX = const(25)

def strom_v1():
    '''
    Very simple Xtree. Just a little visual effect. Warm colours - red and green are preferred. 
    '''
    hw = STROM()
    hw.start_up()

    hw.set_bled(True)       # ON
    time.sleep_ms(100)      # sleep for 0.2 second
    hw.set_bled(False)      # OFF
    time.sleep_ms(200)      # sleep for 0.2 second
    hw.set_bled(True)       # ON
    time.sleep_ms(100)      # sleep for 0.2 second
    hw.set_bled(False)      # OFF

    for i in range(hw.np.__len__()):
        hw.np[i] = (20, 0, 0)

    def update_color(color):
        r = color[0]
        g = color[1]
        b = color[2]
        r += 2 + random.randint(-2, 2)
        g += 1 + random.randint(-2, 2)
        b += random.randint(-2, 2)
        if r < 0 :
            r = 0
        if g < 0 :
            g = 0
        if b < 0 :
            b = 0
        if r > COLOR_MAX :
            r = COLOR_MAX
        if g > COLOR_MAX :
            g = COLOR_MAX
        if b > COLOR_MAX :
            b = COLOR_MAX
        sum = r + g + b
        if sum > COLOR_MAX:
            r = r * COLOR_MAX // sum
            g = g * COLOR_MAX // sum
            b = b * COLOR_MAX // sum
        return (r, g, b)

    print('Press any button to end')
    while True:
        for i in range(hw.np.__len__()):
            col= update_color(hw.np[i])
            hw.np[i] = col
        hw.np.write()
        time.sleep_ms(500)

        if hw.get_buttons() != (0, 0):
            break

# Main
print(">> Start up")

# Demo1:
# hw = demo.demo()
# print(">> Use 'hw' for tests.")

# Demo2:
strom_v1()
