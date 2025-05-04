# -*- coding: utf-8 -*-
#!/usr/bin/python3
"""
batt_sec.py

2023/10/24  XIAOでバッテリーキャンセル時間の測定
ファィルの書かれた時間は電圧が出ていたということなので、
これより短い時間に負荷をかける必要があります。

main.pyとして起動し、5秒ごとにファィル書き込みをします。
"""

from machine import Pin
import time

# ファィルへの書き込み
def save_data(data):
    with open('batt_sec.txt', 'w') as f:
        f.write(str(data) + '\n')  # ファイルに書き込み

def main():
    batt_sec = 0
    while True:
        time.sleep(5)
        batt_sec = batt_sec +5
        save_data(batt_sec)
        print(batt_sec)

if __name__=='__main__':
    main()
