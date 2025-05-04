# XIAOのGPIOを主力に設定し、出力する
"""
UPC_test01.pyを基本にRTCを採用した場合の機能を考える。
2023/12/17  DS1302+が意外に簡単に使えそうなので、検討する。

step1 
modeA,BはRTCを使わず実現しているものをそのまま流用
modeCでRTCを使う

step2
2023/12/19
起動初回のみ
timerC_offsetの間BECし、FETがONになる
水晶の接触不良があったが、無事完成
回路設計、基板設計に移る
基板設計でpinの接続が変わる可能性大

step3
mode-c オフセットタイマーカウント後ON BECも実施
2024/1/6 コンデンサ不要充電の問題があったが、解決

step4
mode-c onタイマー実装しテスト
mode-c offタイマー実装しテスト
2024/1/10   一応出来た

step5
mode-c 総合テスト
設定時間BECし、設定時間が経過した後、1440(1日)を割り切れるサイクルでon,offを繰り返す

2023/12/20  config.pyをシンプル化した
            回路変更への対応
2024/01/03  config_pin.py対応
            UserLED7s color red   = loadをかける
                            green = プログラム停止
                            blue  = sleep
2024/01/04  past_time(ADJ)を保存して終了
2024/01/06  コンデンサ不要充電対策
2024/01/07  通常ループで毎回時刻をリセットしていると誤差が蓄積する。この対策。
            一応できた感じだが、時計としての誤差がそこそこありそうだ。
            そのため補正値を設定して、誤差を補正する仕組みを千島として構築。
2024/01/08  スタートすると必ず2秒遅れるが、これをoffsetから出る時のLED時間で調整。
2024/01/14  past_time_loop()に日替わり処理を追加 
    v10
2024/01/18  86400/ADJより長い時間のtimer_offsetの場合時刻補正ができない。
    v10_1   補正処理をdef化し、offset時も動作させる
2024/01/18  on_count機能を追加
    v11
2024/01/20  v10_1とV11を統合
2024/01/22  offset終了後時計をリセットする。
2024/01/30  回数onの場合、回数カウントアップ後on時間が考慮されないため、日替わり処理でタイマーがズレる
    v13     改修する
2024/01/31  ADJの考え方を整理した
            ADJの効果を確認する必要がある                ***
            先ずADJ=0として、1日の誤差を確認する 15秒
            誤差に対応したADJを設定して、効果を確認する。 1日目は大丈夫そうだが、2日以降おかしい?
            大きくADJを設定して、その効果を確認する
2024/02/05  ADJの日替わり処理修正
    v14
2024/02/08  ADJの処理がおかしいので、全面的に書き換え
    v15
2024/02/08  ADJの補正方向が逆なので修正
    v16
2024/03/28  ADJの確認
    v17
2024/03/29  print文を使ってもディープスリープするので、意味がない
    v18     logに書かないと意味がない
2024/03/29  ADJをカウントではなく経過時間で起動
    v20
2024/03/30  どうも、RTCに時刻を書き込むと、RTC内部処理が再起動するか何かで
    v21     時間が1,2秒ずれるのか何かあるみたいである。
            なので、RTCの時刻は触らないで、読み取った時間に加工して、補正をすれば良いのかもしれない。
            具体的には、pasttimeを作るところで、細工ができれば、いいと思う。
2024/04/07  past_time_ADJ.txtが大きくなりすぎてフリーズするので、初回起動時にバックアップにする
    v22
2024/04/    一日の間での誤差補正と日替わり時の補正を両方実現
    v23
2024/05/06  modeA,Bで2秒ほど遅れるので、補正する。
    v24     modeCも起動処理分遅れるので、
            modeNo 111で電源投入し起動準備をして待機、modeNoを101か11にすると起動する。
            上記2点の改良でスタート時の誤差を減らす。
2025/02/16  ADJ2を追加する
    v25
2025/04/04  on_count_enable =1 and on_count_daily =0 で、終わればずっとスリープ

UPC_RTC_25.py
"""
from machine import Pin,deepsleep,reset_cause
import time
import uos
import sys

import config
import config_pin
import lib_UserLED

import random
import utime
# 現在の日を取得
current_day = utime.localtime()[2]  # 日（1〜31）
# 現在のミリ秒を取得
millis = utime.ticks_ms()
# 日とミリ秒を組み合わせてシードを設定
seed_value = current_day * 100000 + (millis % 100000)  # 5桁のミリ秒を使用
random.seed(seed_value)


lib_UserLED.green(0)
lib_UserLED.red(0)
lib_UserLED.blue(0)

def log_write(log1, log2 = " ", log3 = " ", log4 = " "):
    with open("log.txt", 'a') as f:
        log_str = log1 + "/" + log2  + "/" + log3 + "/" + log4 + '\n' 
        f.write(log_str)

# 設定
XIAO_start = 500 #XIAOの起動時間 500msむ

# 設定値を読み込む
BEC_timer, Load_time, timer_off, timer_on, timer_offset, DeepSleep_Delay, ADJ,ADJ2= config.timer_setting()
print(BEC_timer,Load_time,timer_off,timer_on,timer_offset,DeepSleep_Delay,ADJ,ADJ2)
ADJ = int(ADJ)

# action_setting設定値を読み込む
on_count_enable, on_count, on_count_daily= config.action_setting()

# タイマーを秒に変換
timer_off    = timer_off * 60
timer_on     = timer_on  * 60
timer_offset = timer_offset * 60

pin_FET_on, pin_FET_off, pin_Load_on, pin_mode_A, pin_mode_B, pin_mode_C = config_pin.pin_setting()

# GPIO を出力ピンとして設定
FET_on  = Pin(pin_FET_on , Pin.OUT)
FET_off = Pin(pin_FET_off, Pin.OUT)
Load_on = Pin(pin_Load_on, Pin.OUT)

# 起動初回の動作、
if reset_cause() == 1:
    # 一応誤動作しないように
    FET_off.off()
    Load_on.off()

# FET on offの関数化
def FET(on_off):
    if on_off == "on":
        # FETを通電状態に
        FET_on.on()
        time.sleep(1)
        FET_on.off()
    if on_off == "off":
        # FETを通電状態に
        FET_off.on()
        time.sleep(1)
        FET_off.off()   
    return

# Load on offの関数化
def Load():
    # Load_timeの間 負荷をけかる
    lib_UserLED.red(1)
    Load_on.on()
    time.sleep(Load_time)
    Load_on.off()
    lib_UserLED.red(0)
    return

def LED_on_off(color):
    if color == "green":
        lib_UserLED.green(1)
        time.sleep(0.3)
        lib_UserLED.green(0)
        time.sleep(0.2)
    if color == "blue":
        lib_UserLED.blue(1)
        time.sleep(0.3)
        lib_UserLED.blue(0)
        time.sleep(0.2)

# GPIO を入力ピンとして設定
mode_A_pin = Pin(pin_mode_A, Pin.IN, Pin.PULL_DOWN)
mode_B_pin = Pin(pin_mode_B, Pin.IN, Pin.PULL_DOWN)
mode_C_pin = Pin(pin_mode_C, Pin.IN, Pin.PULL_DOWN)

# 設定ピンの状態を確認
mode = 0
if mode_A_pin.value() == 1 :mode = 100
if mode_B_pin.value() == 1 :mode = mode + 10
if mode_C_pin.value() == 1 :mode = mode + 1
print("mode:",mode)

# Cが0で両モード1なので、BEC動作
# if mode_A == 1 and mode_B == 1:
if mode == 110 :
    print("両モード1なので、BEC動作")
    FET("on")
    # モバイルバッテリーに負荷を Load_time秒 かける 
    Load()
    #                                 FET 
    dt_time = int(BEC_timer * 1000 - 1000 - Load_time * 1000 - DeepSleep_Delay)
    deepsleep(dt_time)


# モード設定されていないので何もせずにプログラム終了
# if mode == 0 or mode == 1 or mode == 111:
if mode == 0 or mode == 1:
    FET("off")
    # 赤LEDを3回点滅させて、プログラム終了
    print("モード設定ないので、終了します。")
    for _ in range(3):
        LED_on_off("green")
    FET("off")
    sys.exit()


# modeA
# timerAカウント後にFETをオンとする。
if mode == 100:
    timer_off = timer_off -1
    BEC_n = timer_off // BEC_timer + 1
    print(BEC_n)
    # 正常起動ならBECの回数を保存
    if reset_cause() == 1:
        FET("off")
        with open("deepsleep_count.txt", 'w') as f:
            f.write(str(BEC_n))
    with open("deepsleep_count.txt", 'r') as f:
        BEC_n = f.read()
    BEC_n = int(BEC_n)    
    print(BEC_n)
    BEC_n = BEC_n - 1
    # 回数分BECを行う
    if BEC_n > 0 :
        with open("deepsleep_count.txt", 'w') as f:
            f.write(str(BEC_n))
        Load()
        # 1回のBECに必要な時間は DeepSleep_Delay 0.326秒 なのでこれを引く
        deepsleepTime = int(BEC_timer * 1000 - Load_time *1000 - DeepSleep_Delay - 1000)
        if reset_cause() == 1 and deepsleepTime > 2000:
            # 初回だけ FET("off") の 1秒を引く
            deepsleepTime = deepsleepTime -1*1000 
        # print(deepsleepTime)
        if deepsleepTime < 100 :deepsleepTime = 100
        # コンデンサへの不要充電をリセットするためFET offをする
        FET("off")
        deepsleep(deepsleepTime)
    # 回数分BECを実行したら余りをBEC
    if BEC_n == 0 :    
        with open("deepsleep_count.txt", 'w') as f:
            f.write(str(BEC_n-1))
        lastBecTimer = timer_off %  BEC_timer
        if lastBecTimer != 0:
            Load()
            # 1回のBECに必要な時間は DeepSleep_Delay 0.326秒 なのでこれを引く
            deepsleepTime = int(lastBecTimer * 1000 - Load_time *1000 - DeepSleep_Delay) 
            if deepsleepTime < 100 :deepsleepTime = 100
            deepsleep(deepsleepTime)
        BEC_n = -1
    # 回数分+あまりが終わったら通常ベックになる
    if BEC_n < 0:  
        # 通常ベック
        FET("on")
        # モバイルバッテリーに負荷を Load_time秒 かける 
        Load()
        deepsleepTime = int(BEC_timer * 1000 -1*1000 - Load_time *1000)
        if deepsleepTime < 100 :deepsleepTime = 100
        deepsleep(deepsleepTime)


# modeB
# FETをオンとしてtimerBカウント後にFETをオフとする。
if mode == 10 :
    timer_on = timer_on -1
    BEC_n = timer_on // BEC_timer + 1
    print(BEC_n)
    # 正常起動ならBECの回数を保存
    if reset_cause() == 1:
        FET("on")
        with open("deepsleep_count.txt", 'w') as f:
            f.write(str(BEC_n))
    with open("deepsleep_count.txt", 'r') as f:
        BEC_n = f.read()
    BEC_n = int(BEC_n)    
    print(BEC_n)
    BEC_n = BEC_n - 1
    # 回数分BECを行う
    if BEC_n > 0 :
        with open("deepsleep_count.txt", 'w') as f:
            f.write(str(BEC_n))
        Load()
        # 1回のBECに必要な時間は DeepSleep_Delay 0.326秒 なのでこれを引く
        deepsleepTime = int(BEC_timer * 1000 - Load_time *1000 - DeepSleep_Delay)
        if reset_cause() == 1 and deepsleepTime > 2000:
            # 初回だけ FET("off") の 1秒を引く
            # 起動などで2秒ほど遅れるので -2秒
            deepsleepTime = deepsleepTime -1*1000 
        # print(deepsleepTime)
        if deepsleepTime < 100 :deepsleepTime = 100
        deepsleep(deepsleepTime)
    # 回数分BECを実行したら余りをBEC
    if BEC_n == 0 :    
        with open("deepsleep_count.txt", 'w') as f:
            f.write(str(BEC_n-1))
        lastBecTimer = timer_on %  BEC_timer
        if lastBecTimer != 0:
            Load()
            # 1回のBECに必要な時間は DeepSleep_Delay 0.326秒 なのでこれを引く
            deepsleepTime = int(lastBecTimer * 1000 - Load_time *1000 -2*1000 - DeepSleep_Delay) 
            if deepsleepTime < 100 :deepsleepTime = 100
            deepsleep(deepsleepTime)
        BEC_n = -1
    # 回数分+あまりが終わったらFETをoffにして眠りにつく
    if BEC_n < 0:  
        for _ in range(3):
            LED_on_off("green")
        FET("off")
        # 継続電源の場合にコンデンサ充電を防止する必要があるのか?
        # ハード対策で十分な時間問題なければ、対策不要かな
        sys.exit()


# modeC
# (101)( 11) どちらでも動作は同じ、先ずtimer_offsetの間off,その後timer_on、timer_offを繰り返します。
if mode == 101 or mode == 11 or mode == 111 :
    DeepSleep_totalTime = BEC_timer
    DeepSleep_Delay = DeepSleep_Delay/1000
    LED_time = 3
    FET_time = 1
    # FET_timeによるディレイが思いの外大きい
    FET_time = FET_time + 0.01

    """
    0.477  160回で 3秒早い -0.017
    ちょいおくれるので -0.015
    DeepSleep_Delay = 0.477 - 0.015
    FET_timeを入れた。
    とりあえず、on、offにしているので、2回かかるが、実際は1回にするのかな
    """
    def DeepSleep():
        lib_UserLED.blue(1)
        time.sleep(LED_time)
        lib_UserLED.blue(0)
        Load()
        #deepsleepTime = int((DeepSleep_totalTime - LED_time - DeepSleep_Delay - Load_time - FET_time*2)*1000)
        deepsleepTime = int((DeepSleep_totalTime - LED_time - DeepSleep_Delay - Load_time - FET_time )*1000)
        deepsleep(deepsleepTime)

    """
    仕様上の制限
        24時間を越えるタイマーは設定できない。
        必ず、24時間以内にon,offを1回は繰り返す。
        繰り返す回数が増えても必ず、24時間で完結すること。
        60分onで1440分offとかはだめ 60分onで1380分offなどとすること。
        トータルのonとoffを足すと1440分になること。
        タイマー設定は全て分単位とする。
        modeCのタイマーは必ずBECより大きい事。

    使用する関数
    def past_time(ADJ)
        これは、2001年11月21日0時0分0秒からの経過秒を計算する。
        ただし、日付は使用せず、日替わりの認識で計算する。
        単位は秒とする。
        --

    def RTC_init(delay=0)
        RTCの時計を2001年11月21日0時0分0秒にセットする。
        delay:設定するたびに遅延なり生じるなら考える。

    毎回実施
    timerC_offsetを秒に変換
    timerC_onを秒に変換
    timerC_offを秒に変換
        
    起動初回の動作、
    RTCの時計を2001年11月21日0時0分0秒にセットする。
    mode_c.txtに onを書き込む

    offsetループ
    timerC_offset > past_time(ADJ) + BEC_timer + 10 
        DeepSleep
    timerC_offset >=  past_time(ADJ) の間はループ
        1秒スリープ
    条件成立したら FETをonにする
    RTCの時計を2001年11月21日0時0分0秒にセットする。
    """

    # RTCの設定
    import lib_DS1302
    #                         clk,   dio,   cs
    ds = lib_DS1302.DS1302(Pin(0),Pin(7),Pin(6))
    #datatime format: [Year, month, day, weekday, hour, minute, second]

    def past_time(ADJ):
    #     これは、2001年11月21日0時0分0秒からの経過秒を計算する。
    #     ただし、日付は使用せず、計算するので、日替わり時おかしくなる
    #     past_time_loop()にて日替わり処理を行う。

        # RTCの思っている時間
        RTC_time = ds.hour() * 3600 + ds.minute() * 60 + ds.second()

        # 1日に遅れる時間が12秒の場合 ADJ= 12
        # 1日に進む時間が12秒の場合  ADJ= -12 とする
        # 1日は60秒*60分*24時間=86400秒なので、1日に12秒遅れるということは、実際に86400秒立った時にRTCは86388秒になっている
        # これを12秒進めて、86400秒にする。かつ、12秒を24時間で補正するので、24/12=2時間に1秒補正する。
        if ADJ == 0 :
            RTC_time_ADJ = RTC_time
        else:
            ADJ_timing = int(86400 / (abs(ADJ)))
            if ADJ > 0 :
                RTC_time_ADJ = RTC_time + (RTC_time // ADJ_timing)
            if ADJ < 0 :
                RTC_time_ADJ = RTC_time - (RTC_time // ADJ_timing)

        # # ファィルが大きくなりすぎてプログラムが止まるので、ほどほどに
        # with open("past_time_ADJ.txt", 'a') as f:
        #     mes = "ADJ:" + str(ADJ) + " RTC:" + str(RTC_time) + " RTC_ADJ:" + str(RTC_time_ADJ) + '\n' 
        #     f.write(mes)
  
        return RTC_time_ADJ
    
    # 時計補正処理
    """
    実時間1分の間にUPCの時計が1秒進むということは
    実時間59秒でUPCが1分となる事、逆に言うと実時間1分でUPCが1分1秒となる
    このためADJとしては、UPCの時間を1秒遅らせるということが必要になる
    なので、ADJ=-1とする。
    補正処理は直接RTCを操作するのではなく、past_time(ADJ)で処理する
    """
    print("起動モード",reset_cause())
    
    # 起動初回の動作、
    if reset_cause() == 1:
       
        # mode_c.txtに onを書き込む
        with open("mode_c.txt", 'w') as f:
            f.write("offset")

        # on_count設定値をenableなら保存
        if on_count_enable == 1:
            with open("on_count.txt", 'w') as f:
                f.write(str(on_count))
        # past_time_ADJ.txtの退避　不要ファイルを削除、退避
        try:
            uos.remove("past_time_ADJ.bak")
        except:
            pass
        try:
            uos.rename("past_time_ADJ.txt", "past_time_ADJ.bak")
        except:
            pass

        # modeが 111であれば、待機。それ以外ならスタート
        while mode == 111:
            if mode_A_pin.value() == 1 :mode = 100
            if mode_B_pin.value() == 1 :mode = mode + 10
            if mode_C_pin.value() == 1 :mode = mode + 1
            time.sleep(0.01)
        
        # RTCの時計を2001年11月21日0時0分0秒にセットする。
        ds.date_time([2001, 11, 21, 1, 0, 0, 0]) # set datetime.
        # スタート時間と経過時間を記録していく、最終盤には不要
        start_time = str(ds.hour()) + ":" + str(ds.minute()) + "." + str(ds.second()) + "\n"
        with open("past_time1.txt", 'w') as f:
            f.write(start_time)
            f.write(" ")


    with open("mode_c.txt", 'r') as f:
        mode_c = f.read()


    if mode_c == "offset":
        # offsetループ
        # 残り時間の算出
        Remaining_time = timer_offset - past_time(ADJ)
        while Remaining_time > BEC_timer + 10:
            # コンデンサへの不要充電をリセットするためFET offをする
            FET("off")
            DeepSleep()
            #print(timerC_offset,past_time(ADJ),BEC_timer)
            # 残り時間は最大 (BEC_timer + 10) 最小は (10秒強)

        harf_BEC = int(BEC_timer/2)
        if Remaining_time > harf_BEC:
            # 負荷をかけてBECし、ハーフディープスリープ
            Load()
            harf_BEC = int(harf_BEC * 1000)
            deepsleep(harf_BEC)

        if Remaining_time > 20:
            Load()
            # 残りを20秒未満にするようにディープスリープ
            last_BEC = int((Remaining_time - 18) * 1000)
            deepsleep(last_BEC)    

        # timer_offsetカウントアップまで1秒スリープで待つ
        count = 10
        while timer_offset - 1 > past_time(ADJ):
            count = count -1
            if count == 0:
                Load()
            #LED_on_off("blue")
            lib_UserLED.blue(1)
            time.sleep(0.1)
            lib_UserLED.blue(0)
            time.sleep(0.05)

        # offsetが終わった時点を時計のスタートとする。
        ds.date_time([2001, 11, 21, 1, 0, 0, 0])
        with open("mode_c.txt", 'w') as f:
            f.write("on")
        with open("past_time.txt", 'w') as f:
            f.write(str(past_time(ADJ)))
        mode_c = "on"
        # オフセットタイマーが終わったので、通常ループに移行する。

    """

    """
    # 保存した経過時間を考慮した現在の経過時間
    def past_time_loop():
        # 今までの経過時間を読み込む
        with open("past_time.txt", 'r') as f:
            past_time_ago = int(f.read())
        # 現在の経過時間を返す
        # 日替わり処理を追加
        past_time_now1 = past_time(ADJ)
        past_time_now2 = past_time_now1 - past_time_ago
        if past_time_now2 < 0 : # 日替わり処理 
            past_time_now2 = (86400 + ADJ) - past_time_ago + past_time_now1 # 日の誤差を蓄積させないため、1日の長さを調整

            # ADJ2による時刻第二段階補正　
            ADJ2_rand = random.uniform(0, 1)  # 0.0 〜 1.0 の乱数
            if abs(ADJ2) > ADJ2_rand :  # ADJ2の確率で実行 ADJ2を超えない乱数なら実行
                if ADJ2 > 0: # プラスということは進ませたい 
                    past_time_now2 = past_time_now2 + 1
                else:        # マイナスということは遅らせたい
                    past_time_now2 = past_time_now2 - 1
            #  +10  で日替わり時に10秒進んだ
            #  +ADJ2で進ませたい
            #  -ADJ2で遅らせたい
            
            #on_count.txtを日替わり時にリセットする
            if on_count_enable == 1:# on_count実施設定
                if on_count_daily == 1:# 毎日設定
                    # on_count.txtをリセットする
                    with open("on_count.txt", 'w') as f:
                        f.write(str(on_count))
                else:
                    # on_count_enable =1
                    # on_count_daily  =0 の場合
                    # ずっとディープスリープとする
                    FET("off") #念の為offとする
                    DeepSleep() #ずっとスリープ状態
            # 日替わりで改行
            with open("past_time1.txt", 'a') as f:
                f.write("\n")
        return past_time_now2
    
    while True:        
        # onループ
        if mode_c == "on":
            on_count_now = 1
            if on_count_enable == 1:# onの回数制限実施の場合
                # onの回数制限読み込み
                with open("on_count.txt", 'r') as f:
                    on_count_now = int(f.read())
            
            # 残り時間の算出
            Remaining_time = timer_on - past_time_loop()
            while Remaining_time > BEC_timer + 10:
                # 一日のon回数が終わったら、その日はonしない
                if on_count_now > 0:
                    FET("on")
                else:
                    FET("off")
                DeepSleep()
                #print(timerC_offset,past_time(ADJ),BEC_timer)
                # 残り時間は最大 (BEC_timer + 10) 最小は (10秒強)

            harf_BEC = int(BEC_timer/2)
            if Remaining_time > harf_BEC:
                # 負荷をかけてBECし、ハーフディープスリープ
                Load()
                harf_BEC = int(harf_BEC * 1000)
                deepsleep(harf_BEC)

            if Remaining_time > 20:
                Load()
                # 残りを20秒未満にするようにディープスリープ
                last_BEC = int((Remaining_time - 18) * 1000)
                deepsleep(last_BEC)    

            # カウントアップまで1秒スリープで待つ
            count = 10
            while timer_on -0 > past_time_loop():
                count = count -1
                if count == 0:
                    Load()
                LED_on_off("blue")

            # 現時点の経過時間を保存
            with open("past_time.txt", 'w') as f:
                f.write(str(past_time(ADJ)))
            with open("past_time1.txt", 'a') as f:
                f.write(str(past_time(ADJ)))
                f.write(" ")
            with open("mode_c.txt", 'w') as f:
                f.write("off")
            mode_c = "off"

            # onを1回実施したらカウントダウン
            if on_count_enable == 1:
                with open("on_count.txt", 'r') as f:
                    on_count_now = int(f.read())
                if on_count_now > 0:
                    with open("on_count.txt", 'w') as f:
                        f.write(str(on_count_now -1))
                        

        # offループ
        if mode_c == "off":
            # 残り時間の算出
            Remaining_time = timer_off - past_time_loop()
            while Remaining_time > BEC_timer + 10:
                # コンデンサへの不要充電をリセットするためFET offをする
                FET("off")
                DeepSleep()
                #print(timerC_offset,past_time(ADJ),BEC_timer)
                # 残り時間は最大 (BEC_timer + 10) 最小は (10秒強)

            harf_BEC = int(BEC_timer/2)
            if Remaining_time > harf_BEC:
                # 負荷をかけてBECし、ハーフディープスリープ
                Load()
                harf_BEC = int(harf_BEC * 1000)
                deepsleep(harf_BEC)

            if Remaining_time > 20:
                Load()
                # 残りを20秒未満にするようにディープスリープ
                last_BEC = int((Remaining_time - 18) * 1000)
                deepsleep(last_BEC)    

            # カウントアップまで1秒スリープで待つ
            count = 10
            while timer_off + 0 > past_time_loop():
                count = count -1
                if count == 0:
                    Load()
                LED_on_off("blue")

            # 現時点の経過時間を保存
            with open("past_time.txt", 'w') as f:
                f.write(str(past_time(ADJ)))
            with open("past_time1.txt", 'a') as f:
                f.write(str(past_time(ADJ)))
                f.write(" ")
            with open("mode_c.txt", 'w') as f:
                f.write("on")
            mode_c = "on"

        # ----------------------- err --------------------------------
        # 本来onとoffのはずだが、違う場合はエラーなので、プログラム終了
        if mode_c != "on"  and mode_c != "off" :
            for _ in range(3):
                LED_on_off("green")
            FET("off")
            sys.exit()
            