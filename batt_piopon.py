# -*- coding: utf-8 -*-
#!/usr/bin/python3
"""
batt_pinpon.py

2023/10/24  電圧キャンセルを止められるチョン付時間を測定 ピンポンダッシュ
batt_sec.pyで測定した時間に
0.5秒、0.4,0.3,0.2,0.1とピンポンダッシュ時間を短くして
キャンセルを停止できる最短時間を測定する。
電源が切れたあとファィルに保存された時間ではキャンセルが止められなかったと言うことなので、
それより長い時間が必要ということになります。

main.pyとして起動

"""

from machine import Pin
import time
import lib_UserLED

batt_sec = 100
pinpon = [0.5,0.4,0.3,0.2,0.1,0.05]

load = Pin(2, Pin.OUT)

# ファィルへの書き込み
def save_data(data):
    with open('batt_pinpon.txt', 'w') as f:
        f.write(str(data) + '\n')  # ファイルに書き込み

def main():
    lib_UserLED.red(1)
    time.sleep(1)
    lib_UserLED.red(0)
    for pinpon_sec in pinpon:
        time.sleep(batt_sec)
        # 負荷をかける
        lib_UserLED.green(1)
        load.on()
        time.sleep(pinpon_sec)
        # 負荷を止める
        load.off()
        lib_UserLED.green(0)
        save_data(pinpon_sec)
        print(pinpon_sec)

if __name__=='__main__':
    main()
