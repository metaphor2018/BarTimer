from m5stack import *
from m5ui import *
from uiflow import *
import time

# 初期化
lcd.clear()
setScreenColor(0x000000)

# 設定
pomodoro_work_time = 25 * 60  # ポモドーロ作業時間（秒）
pomodoro_break_time = 5 * 60  # ポモドーロ休憩時間（秒）
custom_times = [30, 60, 180, 300, 600, 900, 1800, 2700, 3600]  # カスタムタイマーの選択肢（秒）

# 状態変数
is_pomodoro_mode = True  # True=ポモドーロモード, False=カスタムタイマー
is_work_phase = True  # True=作業, False=休憩
remaining_time = pomodoro_work_time
is_running = False
custom_timer_index = 0  # カスタムタイマーの現在の選択肢
sound_enabled = True  # タイマー終了時の音
last_c_button_press = 0  # Cボタンが押された時刻

# バーの描画設定
bar_x = 10  # バーの左端のX座標
bar_y = 50  # バーのY座標
bar_width = 300  # バーの全幅（画面幅いっぱい）
bar_height = 40  # 各ブロックの高さ
block_count = 20  # ブロックの数
block_spacing = 5  # ブロック間の隙間

# M5TextBoxの初期設定
label_timer_mode = M5TextBox(50, 10, "", lcd.FONT_DejaVu24, 0xFFFFFF, rotate=0)
label_time = M5TextBox(60, 110, "00:00", lcd.FONT_DejaVu72, 0xFFFFFF, rotate=0)
label_mode = M5TextBox(10, 200, "Mode: Pomodoro", lcd.FONT_DejaVu18, 0xFFFFFF, rotate=0)
label_sound = M5TextBox(10, 220, "Sound: ON", lcd.FONT_DejaVu18, 0xFFFFFF, rotate=0)  # サウンド状態表示

# 状態の保存（ちらつき防止用）
last_remaining_time = None
last_blocks_to_fill = None
last_phase_text = None

# Aボタンでタイマー開始・停止
def toggle_timer():
    global is_running
    is_running = not is_running

btnA.wasPressed(toggle_timer)

# Bボタンでモード切替または終了音の切替
def handle_b_button():
    global is_pomodoro_mode, remaining_time, is_work_phase, sound_enabled

    if is_running:
        sound_enabled = not sound_enabled  # 動作中の場合、音のオン/オフ切替
        update_sound_display()  # サウンド状態を更新
    else:
        is_pomodoro_mode = not is_pomodoro_mode
        if is_pomodoro_mode:
            remaining_time = pomodoro_work_time
            is_work_phase = True
            label_mode.setText("Mode: Pomodoro")
            update_timer_display(remaining_time)  # ポモドーロモードに切り替えたら25:00を表示
        else:
            remaining_time = custom_times[custom_timer_index]
            label_mode.setText("Mode: Custom Timer")
            update_timer_display(remaining_time)  # カスタムタイマーの現在の時間を表示

btnB.wasPressed(handle_b_button)

# Cボタンでカスタムタイマー時間切替、またはダブルクリックでリセット
def handle_c_button():
    global custom_timer_index, remaining_time, is_running, is_work_phase, last_c_button_press

    current_time = time.ticks_ms()  # 現在時刻をミリ秒で取得
    if current_time - last_c_button_press < 500:  # 500ms以内に2回押されたらリセット
        is_running = False
        if is_pomodoro_mode:
            remaining_time = pomodoro_work_time
            is_work_phase = True
        else:
            remaining_time = custom_times[custom_timer_index]
        update_timer_display(remaining_time)  # リセット時も画面を更新
    else:
        if not is_pomodoro_mode:  # 通常のボタンクリックで時間切替
            custom_timer_index = (custom_timer_index + 1) % len(custom_times)  # 選択肢をループ
            remaining_time = custom_times[custom_timer_index]
            update_timer_display(remaining_time)  # 時間切替時に新しい時間を表示

    last_c_button_press = current_time  # 押下時刻を更新

btnC.wasPressed(handle_c_button)

# タイマー終了時の音
def play_sound():
    speaker.setVolume(1)  # 音量を設定（小さめ）
    speaker.tone(440, 200)  # 周波数440Hz, 持続時間200ms
    time.sleep(0.3)
    speaker.tone(440, 200)

# タイマー時間を更新表示
def update_timer_display(new_time):
    minutes = new_time // 60
    seconds = new_time % 60
    time_text = "{:02}:{:02}".format(minutes, seconds)
    label_time.setText(time_text)

# サウンド状態を更新表示
def update_sound_display():
    global sound_enabled
    sound_text = "Sound: ON" if sound_enabled else "Sound: OFF"
    label_sound.setText(sound_text)

# タイマー表示更新（ちらつき防止）
def draw_timer(remaining_time, total_time, is_work_phase):
    global last_remaining_time, last_blocks_to_fill, last_phase_text

    # フェーズテキストの更新
    phase_text = "Work Time" if is_work_phase else "Break Time"
    phase_color = lcd.GREEN if is_work_phase else lcd.BLUE
    if not is_pomodoro_mode:
        phase_text = "Custom Timer"
        phase_color = lcd.ORANGE

    if phase_text != last_phase_text:
        label_timer_mode.setColor(phase_color)
        label_timer_mode.setText(phase_text)
        last_phase_text = phase_text

    # タイマーの時間表示を更新
    if remaining_time != last_remaining_time:
        minutes = remaining_time // 60
        seconds = remaining_time % 60
        time_text = "{:02}:{:02}".format(minutes, seconds)
        label_time.setText(time_text)
        last_remaining_time = remaining_time

    # バーのブロック表示を更新
    blocks_to_fill = int((remaining_time / total_time) * block_count)
    if blocks_to_fill != last_blocks_to_fill:
        block_width = (bar_width - (block_spacing * (block_count - 1))) // block_count

        for i in range(block_count):
            block_x = bar_x + i * (block_width + block_spacing)
            if i < blocks_to_fill:
                lcd.fillRect(block_x, bar_y, block_width, bar_height, phase_color)
            else:
                lcd.fillRect(block_x, bar_y, block_width, bar_height, lcd.BLACK)
                lcd.rect(block_x, bar_y, block_width, bar_height, lcd.WHITE)

        last_blocks_to_fill = blocks_to_fill

# メインループ
while True:
    if is_running:
        time.sleep(1)
        remaining_time -= 1

        if remaining_time <= 0:
            if is_pomodoro_mode:
                is_work_phase = not is_work_phase
                remaining_time = pomodoro_work_time if is_work_phase else pomodoro_break_time
            else:
                is_running = False  # カスタムタイマーの場合、停止

            if sound_enabled:
                play_sound()

        draw_timer(remaining_time, pomodoro_work_time if is_pomodoro_mode else custom_times[custom_timer_index], is_work_phase)

    update_sound_display()  # メインループ内でサウンド状態を更新
