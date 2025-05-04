"""
2023/10/19  XIAOのLED制御
    USBコネクタ横のフルカラーLED
    USBコネクタの横のLEDは回路図を見ると、RGB2となっており以下の通り直結されています。
    R　GPIO16　緑
    G　GPIO17　赤
    B　GPIO25　青
    なので、USBコネクタの横のLEDは単純にGPIOをON/OFFすれば光らせる事ができます。
    ただ負論理なので、LOWで点灯、HIGHで消灯なのがご愛敬です。
2023/11/14  ライブラリとして使いやすいようにします。

"""
from machine import Pin
import time

LED_green = Pin(16, Pin.OUT)
LED_red   = Pin(17, Pin.OUT)
LED_blue  = Pin(25, Pin.OUT)

LED_green.on()
LED_red.on()
LED_blue.on()

# 緑色LED
def green(sw):
    if sw == 1:
        LED_green.off()
    if sw == 0:
        LED_green.on()
    
# 赤色LED
def red(sw):
    if sw == 1:
        LED_red.off()
    if sw == 0:
        LED_red.on()

# 青色LED
def blue(sw):
    if sw == 1:
        LED_blue.off()
    if sw == 0:
        LED_blue.on()

def main():
    green(1)
    time.sleep(1)
    green(0)
    red(1)
    time.sleep(1)
    red(0)
    blue(1)
    time.sleep(1)
    blue(0)
0
if __name__=='__main__':
    main()