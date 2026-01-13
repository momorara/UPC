# -*- coding: utf-8 -*-
#!/usr/bin/python3
"""
XIAOのピン設定

2023/12/30
v1.0
2024/01/16  v01-1対応のためにはpin番号の変更が必要
"""

# 基板のバージョンによりpin_settingが一部異なります。
# 対象外の方をコメントアウトしてください。
# v03,v01
"""
def pin_setting():
    pin_FET_on  = 26
    pin_FET_off = 3 #
    pin_Load_on = 2
    pin_mode_A  = 27
    pin_mode_B  = 28 
    pin_mode_C  = 29 #
    return pin_FET_on, pin_FET_off, pin_Load_on, pin_mode_A, pin_mode_B, pin_mode_C
"""
# v01-1
def pin_setting():
    pin_FET_on  = 26
    pin_FET_off = 4  #
    pin_Load_on = 2
    pin_mode_A  = 27
    pin_mode_B  = 28
    pin_mode_C  = 1  #
    return pin_FET_on,pin_FET_off,pin_Load_on,pin_mode_A,pin_mode_B,pin_mode_C

def main():
    print(pin_setting())

if __name__=='__main__':
    main()
