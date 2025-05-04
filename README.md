# UPC
Usb Power Controller

USB電源を制御する基板のためのプログラムです。
マイコンはXIAO-RP2040
言語はMicroPython

機能概要
・USB-microB電源をつないで、USB-Aに出力
・つないでから設定時間後にON
・つなぐとON、設定時間後にOFF
・指定時間ごとにONを繰り返す
等の動作ができます。
BEC機能(バッテリー省電力機能キャンセル)もあります。

