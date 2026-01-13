# -*- coding: utf-8 -*-
#!/usr/bin/python3
"""
2023/11/23
v1.0
2023/12/20  設定をシンプルにする
v2.0
2023/01/08  ADJを追加
v2.1
2025/02/16  ADJ2を追加
v2.2
"""

"""
以下の設定は
offsetで16時とすると

毎日 11時、16時に15分onする

"""
def timer_setting():
    # モバイルバッテリーのエコ機能の働く時間より少し短い時間とする。(秒)
    # 各タイマーより短い時間である必要があります。
    BEC_timer  =30
    # モバイルバッテリーのエコ機能を負荷をかけて解除する最短時間より少し長い時間とする。(秒)
    Load_time =0.3

    # on時間を決めるタイマー値  modeB,modeCで使用。(分)
    # timer_on時間はBEC_timerより最低10秒は長い必要がある
    timer_on =1
    # timer_off時間はBEC_timerより最低10秒は長い必要がある
    # off時間を決めるタイマー値 modeA,modeCで使用。(分)
    timer_off =1
    # modeCで電源をつないでからUSB-Aをonにするまでの時間。(分)
    timer_offset =1

    # 1日の誤差を確認して、補正値を設定 (秒)
    # 1日に5秒の遅れなら 5秒
    # 1日に5秒の進みなら -5秒 と設定してください。
    # ただし ±1440より大きい数字は入れないでください。(そんな数字は入れないと思いますが...)
    ADJ  =0
    ADJ2 =0
    """
    実時間1分の間にUPCの時計が1秒進むということは
    実時間59秒でUPCが1分となる事、逆に言うと実時間1分でUPCが1分1秒となる
    このためADJとしては、UPCの時間を1秒遅らせるということが必要になる
    なので、ADJ=-1とする。

    実時間1分の間にUPCの時計が1秒遅れるということは
    実時間1分1秒でUPCが1分となる事、逆に言うと実時間1分でUPCが59秒となる
    このためADJとしては、UPCの時間を1秒進ませるということが必要になる
    なので、ADJ=1とする。

    さらに細かい補正を第二段階としてADJ2を設定 1日1秒以内の補正をします。
    """
    # ディープスリープの誤差調整用設定値。(ミリ秒)
    DeepSleep_Delay = 462    
    return BEC_timer, Load_time, timer_off, timer_on, timer_offset, DeepSleep_Delay, ADJ,ADJ2
"""
timerCに関して、当初onスタートとoffスタートを分けていたが、
基本onスタートにする。
ただし、最初にスタートをオフセットするタイマーを入れる
このオフセットで、1時間後にtimerCスタートみたいな感じにできる。
"""

def action_setting():
    # modeCの時何回までon動作を行うかの設定
    # 1: on_countを使用する 0:使用しない
    on_count_enable =0
    # 設定回数onを繰り返す -1 で回数制限なしとなる
    on_count =2
    # 1: on_countを日替わり時にリセットし、毎日処理  
    # 0: on_countを1回限り実施
    on_count_daily =1
    return on_count_enable, on_count, on_count_daily

def main():
    print(timer_setting())
    print(action_setting())

if __name__=='__main__':
    main()
