"""
PureClick  (Tkinter GUI + pynput)

One app, two interface languages (Русский / English) - switch in the window.

Tab 1 "Simple": one action, repeated or held.
    Mouse click / Mouse hold / Key click / Key hold.
    Keys can be typed or recorded: press "Record key", then press any key.

Tab 2 "Sequence": a list of steps. Each step is a click or a hold of a mouse
    button or key. A step either starts after the previous one finishes, or
    together with it, so actions can run one by one or at the same time.

Tab 3 "Recording": press Record (or F9), do things with the mouse and keyboard
    anywhere, press it again to stop. The recorded actions are listed and can
    be played back, with repeats and a speed factor.

A dot on screen marks the click coordinates (mouse actions).

Global hotkeys: F8 = start/stop (or play), F6 = capture cursor position,
                F9 = start/stop recording

Install / Установка:  pip install pynput
Run / Запуск:         python autoclicker.py
"""

import math
import queue
import re
import sys
import threading
import time
import traceback
import webbrowser
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, ttk

from pynput import keyboard, mouse
from pynput.keyboard import Key, KeyCode

# Make coordinates match real screen pixels on high-DPI Windows displays
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

DEFAULT_LANG = "ru"
LANG_NAMES = {"ru": "Русский", "en": "English"}

STRINGS = {
    "en": {
        "title": "PureClick",
        "language": "Language",
        "tab_simple": "Simple",
        "tab_seq": "Sequence",
        "coffee": "Buy me a coffee",
        "donate_title": "Support PureClick",
        "donate_intro": "PureClick is free. If it saves you time, you can say thanks.",
        "donate_money": "Card or bank payment",
        "donate_crypto": "Cryptocurrency",
        "donate_note": "Send only on the network shown next to the coin.",
        "donate_copy": "Copy",
        "donate_copied": "Copied",
        "donate_close": "Close",
        "donate_pick": "How would you like to say thanks?",
        "donate_back": "Back",
        "donate_soon": "Coming soon",
        "donate_money_btn": "Money (card or bank)",
        "donate_crypto_btn": "Cryptocurrency",
        # tab 1
        "action_frame": "Action",
        "act_mouse_click": "Mouse click",
        "act_mouse_hold": "Mouse hold",
        "act_key_click": "Key click",
        "act_key_hold": "Key hold",
        "hint_click": "Presses and releases again and again.",
        "hint_hold": "Holds down until you press F8 or the run time ends.",
        "target_frame": "What to press",
        "mouse_button_label": "Mouse button",
        "keys_label": "Keyboard key",
        "record_key": "Record key",
        "recording_key": "Press any key... (click to cancel)",
        "btn_left": "Left button",
        "btn_right": "Right button",
        "btn_middle": "Middle button",
        "timing_frame": "Timing",
        "hold_for": "Hold time (s, 0 = until stopped)",
        "interval": "Interval between clicks (ms)",
        "total": "Total run time (s, 0 = until stopped)",
        # position
        "pos_frame": "Position",
        "fixed_chk": "Fixed coordinates, marked by a dot (off = where the cursor is)",
        "capture_btn": "Capture in 3 s (F6)",
        # tab 2
        "steps_frame": "Steps",
        "col_start": "Start",
        "col_action": "Action",
        "col_target": "Target",
        "col_delay": "Delay, ms",
        "col_dur": "Time, ms",
        "start_after": "After previous",
        "start_with": "Together with previous",
        "start_after_short": "After",
        "start_with_short": "Together",
        "btn_add": "Add step",
        "btn_edit": "Edit",
        "btn_delete": "Delete",
        "btn_up": "Up",
        "btn_down": "Down",
        "seq_hint": "Top to bottom. \"Together\" runs at the same time as the step above.",
        "seq_empty": "No steps yet. Press \"Add step\".",
        "repeat_frame": "Repeat",
        "repeats": "Repeat the sequence (times, 0 = until stopped)",
        "pause": "Pause between repeats (ms)",
        # step dialog
        "dlg_add": "New step",
        "dlg_edit": "Edit step",
        "fld_action": "Action",
        "fld_target": "Target",
        "fld_start": "Start",
        "fld_delay": "Delay before the step (ms)",
        "fld_dur": "Press time (ms)",
        "dlg_save": "Save",
        "dlg_cancel": "Cancel",
        # run
        "start": "Start (F8)",
        "stop": "Stop (F8)",
        "st_idle": "Ready",
        "st_running": "Running...",
        "st_holding": "Holding: {names}",
        "st_captured": "Captured position: ({x}, {y})",
        "st_countdown": "Move the cursor to the target... 3 s",
        "st_stopped": "Stopped. Total presses: {n}",
        "st_released": "Released. Held for {s} s",
        "st_seq_running": "Running the sequence, round {n}",
        "st_seq_done": "Stopped. Rounds completed: {n}",
        "st_recorded": "Recorded key: {key}",
        # errors
        "err_title": "Invalid settings",
        "err_numbers": "Coordinates and timing must be valid numbers.",
        "err_negative": "Values cannot be negative.",
        "err_key_empty": "Choose a key.",
        "err_key_unknown": (
            "Unknown key '{name}'. Use a single character or a name like "
            "space, enter, tab, esc, shift, ctrl, alt, up, down, f1..f12."
        ),
        "err_key_reserved": "F6, F8 and F9 are reserved for the app's hotkeys.",
        "err_coords": "Enter both X and Y, or turn off fixed coordinates.",
        "err_seq_empty": "Add at least one step.",
        "err_hold_dur": "A hold needs a time greater than 0.",
        # recording tab
        "tab_macro": "Recording",
        "macro_frame": "Record",
        "macro_rec_start": "\u25CF  Record (F9)",
        "macro_rec_stop": "\u25A0  Stop recording (F9)",
        "macro_move_chk": "Also record mouse movement",
        "macro_list_frame": "Recorded actions",
        "macro_summary": "{n} actions, {s} s",
        "macro_empty": "Nothing recorded yet",
        "macro_clear": "Clear",
        "macro_play_frame": "Playback (Start, F8)",
        "macro_repeats": "Repeats (0 = until stopped)",
        "macro_speed": "Speed (x)",
        "macro_pause": "Pause (ms)",
        "col_no": "#",
        "col_time": "Time, s",
        "col_event": "Event",
        "col_detail": "Details",
        "ev_move": "Mouse move",
        "ev_mouse_down": "Mouse press",
        "ev_mouse_up": "Mouse release",
        "ev_scroll": "Scroll",
        "ev_key_down": "Key press",
        "ev_key_up": "Key release",
        "scroll_up": "up",
        "scroll_down": "down",
        "scroll_left": "left",
        "scroll_right": "right",
        "st_recording": "Recording... {n} actions. Press F9 to stop.",
        "st_rec_done": "Recorded {n} actions ({s} s). Press Start (F8) to play them.",
        "st_rec_empty": "Nothing was recorded.",
        "st_rec_limit": "Recording stopped: limit of {n} actions reached.",
        "st_macro_running": "Playing the recording, round {n}",
        "st_macro_done": "Playback stopped. Rounds completed: {n}",
        "err_macro_empty": "Record something first.",
        "err_speed": "Speed must be greater than 0.",
    },
    "ru": {
        "title": "PureClick",
        "language": "Язык",
        "tab_simple": "Простой",
        "tab_seq": "Последовательность",
        "coffee": "Угостить кофе",
        "donate_title": "Поддержать PureClick",
        "donate_intro": "PureClick бесплатный. Если он экономит вам время, можно сказать спасибо.",
        "donate_money": "Картой или банковским переводом",
        "donate_crypto": "Криптовалюта",
        "donate_note": "Отправляйте только по сети, указанной рядом с монетой.",
        "donate_copy": "Копировать",
        "donate_copied": "Скопировано",
        "donate_close": "Закрыть",
        "donate_pick": "Как хотите отблагодарить?",
        "donate_back": "Назад",
        "donate_soon": "Скоро",
        "donate_money_btn": "Деньги (картой или банком)",
        "donate_crypto_btn": "Криптовалюта",
        # tab 1
        "action_frame": "Действие",
        "act_mouse_click": "Клик мыши",
        "act_mouse_hold": "Удержание мыши",
        "act_key_click": "Клик клавиши",
        "act_key_hold": "Удержание клавиши",
        "hint_click": "Нажимает и отпускает снова и снова.",
        "hint_hold": "Удерживает, пока вы не нажмёте F8 или не истечёт время.",
        "target_frame": "Что нажимать",
        "mouse_button_label": "Кнопка мыши",
        "keys_label": "Клавиша клавиатуры",
        "record_key": "Записать клавишу",
        "recording_key": "Нажмите любую клавишу... (клик — отмена)",
        "btn_left": "Левая кнопка",
        "btn_right": "Правая кнопка",
        "btn_middle": "Средняя кнопка",
        "timing_frame": "Время",
        "hold_for": "Время удержания (с, 0 = до остановки)",
        "interval": "Интервал между кликами (мс)",
        "total": "Общее время работы (с, 0 = до остановки)",
        # position
        "pos_frame": "Позиция",
        "fixed_chk": "Фиксированные координаты с точкой (выкл. — там, где курсор)",
        "capture_btn": "Запомнить через 3 с (F6)",
        # tab 2
        "steps_frame": "Шаги",
        "col_start": "Начало",
        "col_action": "Действие",
        "col_target": "Цель",
        "col_delay": "Задержка, мс",
        "col_dur": "Время, мс",
        "start_after": "После предыдущего",
        "start_with": "Вместе с предыдущим",
        "start_after_short": "После",
        "start_with_short": "Вместе",
        "btn_add": "Добавить шаг",
        "btn_edit": "Изменить",
        "btn_delete": "Удалить",
        "btn_up": "Выше",
        "btn_down": "Ниже",
        "seq_hint": "Сверху вниз. «Вместе» — одновременно с шагом выше.",
        "seq_empty": "Шагов пока нет. Нажмите «Добавить шаг».",
        "repeat_frame": "Повтор",
        "repeats": "Повторить последовательность (раз, 0 = до остановки)",
        "pause": "Пауза между повторами (мс)",
        # step dialog
        "dlg_add": "Новый шаг",
        "dlg_edit": "Изменить шаг",
        "fld_action": "Действие",
        "fld_target": "Цель",
        "fld_start": "Начало",
        "fld_delay": "Задержка перед шагом (мс)",
        "fld_dur": "Время нажатия (мс)",
        "dlg_save": "Сохранить",
        "dlg_cancel": "Отмена",
        # run
        "start": "Старт (F8)",
        "stop": "Стоп (F8)",
        "st_idle": "Готово к запуску",
        "st_running": "Работает...",
        "st_holding": "Удерживается: {names}",
        "st_captured": "Позиция сохранена: ({x}, {y})",
        "st_countdown": "Наведите курсор на цель... 3 с",
        "st_stopped": "Остановлено. Всего нажатий: {n}",
        "st_released": "Отпущено. Удерживалось {s} с",
        "st_seq_running": "Выполняется последовательность, круг {n}",
        "st_seq_done": "Остановлено. Завершено кругов: {n}",
        "st_recorded": "Записана клавиша: {key}",
        # errors
        "err_title": "Неверные настройки",
        "err_numbers": "Координаты и время должны быть корректными числами.",
        "err_negative": "Значения не могут быть отрицательными.",
        "err_key_empty": "Укажите клавишу.",
        "err_key_unknown": (
            "Неизвестная клавиша «{name}». Введите один символ или название: "
            "space, enter, tab, esc, shift, ctrl, alt, up, down, f1..f12."
        ),
        "err_key_reserved": "F6, F8 и F9 заняты горячими клавишами программы.",
        "err_coords": "Введите X и Y или выключите фиксированные координаты.",
        "err_seq_empty": "Добавьте хотя бы один шаг.",
        "err_hold_dur": "Для удержания время должно быть больше 0.",
        # recording tab
        "tab_macro": "Запись",
        "macro_frame": "Запись",
        "macro_rec_start": "\u25CF  Записать (F9)",
        "macro_rec_stop": "\u25A0  Остановить запись (F9)",
        "macro_move_chk": "Записывать и движение мыши",
        "macro_list_frame": "Записанные действия",
        "macro_summary": "Действий: {n}, {s} с",
        "macro_empty": "Пока ничего не записано",
        "macro_clear": "Очистить",
        "macro_play_frame": "Воспроизведение (Старт, F8)",
        "macro_repeats": "Повторы (0 = до остановки)",
        "macro_speed": "Скорость (x)",
        "macro_pause": "Пауза (мс)",
        "col_no": "№",
        "col_time": "Время, с",
        "col_event": "Событие",
        "col_detail": "Подробности",
        "ev_move": "Движение мыши",
        "ev_mouse_down": "Нажатие мыши",
        "ev_mouse_up": "Отпускание мыши",
        "ev_scroll": "Прокрутка",
        "ev_key_down": "Нажатие клавиши",
        "ev_key_up": "Отпускание клавиши",
        "scroll_up": "вверх",
        "scroll_down": "вниз",
        "scroll_left": "влево",
        "scroll_right": "вправо",
        "st_recording": "Идёт запись... Действий: {n}. F9 — остановить.",
        "st_rec_done": "Записано действий: {n} ({s} с). Нажмите Старт (F8), чтобы воспроизвести.",
        "st_rec_empty": "Ничего не записано.",
        "st_rec_limit": "Запись остановлена: достигнут предел в {n} действий.",
        "st_macro_running": "Воспроизведение записи, круг {n}",
        "st_macro_done": "Воспроизведение остановлено. Завершено кругов: {n}",
        "err_macro_empty": "Сначала запишите действия.",
        "err_speed": "Скорость должна быть больше 0.",
    },
}

# "<device>_<style>": device = mouse | key, style = click | hold
ACTION_KINDS = ["mouse_click", "mouse_hold", "key_click", "key_hold"]
BUTTON_CHOICES = ["left", "right", "middle"]
MOUSE_BUTTONS = {
    "left": mouse.Button.left,
    "right": mouse.Button.right,
    "middle": mouse.Button.middle,
}
START_CHOICES = ["after", "with"]
DEFAULT_MS = {"click": 50.0, "hold": 1000.0}   # default press time per style (sequence steps)
CLICK_PRESS_S = 0.05                           # how long one click on the Simple page lasts

RESERVED_KEYS = {"f6", "f8", "f9"}
MACRO_MAX_EVENTS = 10000       # a recording stops by itself at this size
MOVE_MIN_GAP_S = 0.02          # mouse movement is sampled at most every 20 ms

# Behind the "Buy me a coffee" button. Fill these in; the button stays hidden
# while both lists are empty.
#   DONATE_LINKS:  (name shown on the button, https:// link)
#   DONATE_CRYPTO: (coin, network, wallet address)
DONATE_LINKS = [
    ("DonationAlerts", "https://www.donationalerts.com/r/PURE_clikerr"),
]
DONATE_CRYPTO = [
    ("BTC", "Bitcoin", "bc1q50za6zmd25hhksun98pv9ws496ky9ja8xdy6lz"),
    ("ETH", "Ethereum", "0xd3bafE7C49A125C0F5cA887179519216Bf18885B"),
]
# QR codes (PNG, base64) keyed by wallet address. A coin without an entry here
# is shown without a QR code.
DONATE_QR = {
    "bc1q50za6zmd25hhksun98pv9ws496ky9ja8xdy6lz": (
        "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"
    ),
    "0xd3bafE7C49A125C0F5cA887179519216Bf18885B": (
        "iVBORw0KGgoAAAANSUhEUgAAAOYAAADmCAAAAADkAaZnAAAOzElEQVR4AeXBQYorSQDFQOn+h9bwVgmJq+yBv+sI4y8w/gLjLzD+"
        "AuMvMP4C4y8w/gLjLzD+AuMvMP4C4y8w/gLjLzD+AuMvMP4C4y8w/gLjLzD+AuMvMP4C4y8w/gLjLzD+AuOZ/CpuMjEyMTJxyMTI"
        "xCG/imfGM/lV3GRiZGJk4pCJkYlDfhXPjGfyq7jJxMjEyMQhEyMTh/wqnhnP5Fdxk4mRiZGJQyZGJg75VTwznsmv4iYTIxMjE4dM"
        "jEwc8qt4ZjyTX8VNJkYmRiYOmRiZOORX8cx4JhNvZGJkYmTiM5k4ZGJkYmTijUw8M57JxBuZGJkYmfhMJg6ZGJkYmXgjE8+MZzLx"
        "RiZGJkYmPpOJQyZGJkYm3sjEM+OZTLyRiZGJkYnPZOKQiZGJkYk3MvHMeCYTb2RiZGJk4jOZOGRiZGJk4o1MPDOeycQbmRiZGJn4"
        "TCYOmRiZGJl4IxPPjGcyMXKLkYk3MjEyMTIxMnGTiZFbjEw8M57JxMgtRibeyMTIxMjEyMRNJkZuMTLxzHgmEyO3GJl4IxMjEyMT"
        "IxM3mRi5xcjEM+OZTIzcYmTijUyMTIxMjEzcZGLkFiMTz4xnMjFyi5GJNzIxMjEyMTJxk4mRW4xMPDOeycTILUYm3sjEyMTIxMjE"
        "TSZGbjEy8cx4JhMjtxiZGLnFyBEjEyNH3GRi5BYjE8+MZzIxcouRiZFbjBwxMjFyxE0mRm4xMvHMeCYTI7cYmRi5xcgRIxMjR9xk"
        "YuQWIxPPjGcyMXKLkYmRW4wcMTIxcsRNJkZuMTLxzHgmEyO3GJkYucXIESMTI0fcZGLkFiMTz4xnMjFyi5GJkVuMHDEyMXLETSZG"
        "bjEy8cx4JhMjtxiZOGTiJkeMHHHIxMjEyC1GJp4Zz2Ri5BYjE4dM3OSIkSMOmRiZGLnFyMQz45lMjNxiZOKQiZscMXLEIRMjEyO3"
        "GJl4ZjyTiZFbjEwcMnGTI0aOOGRiZGLkFiMTz4xnMjFyi5GJQyZucsTIEYdMjEyM3GJk4pnxTCZGbjEyccjETY4YOeKQiZGJkVuM"
        "TDwznsnEG5kYOWLkiEMmDpkYmRiZeCMTz4xnMvFGJkaOGDnikIlDJkYmRibeyMQz45lMvJGJkSNGjjhk4pCJkYmRiTcy8cx4JhNv"
        "ZGLkiJEjDpk4ZGJkYmTijUw8M57JxBuZGDli5IhDJg6ZGJkYmXgjE8+MZzLxRiZGjhg54pCJQyZGJkYm3sjEM+OZ/CpGJkYmRiZG"
        "JkYmRiZGJkZ+Fc+MZ/KrGJkYmRiZGJkYmRiZGJkY+VU8M57Jr2JkYmRiZGJkYmRiZGJkYuRX8cx4Jr+KkYmRiZGJkYmRiZGJkYmR"
        "X8Uz45n8KkYmRiZGJkYmRiZGJkYmRn4Vz4xn8qsYmRiZGJkYmRiZGJkYmRj5VTwz/jW5xXdyxL9m/Gtyi+/kiH/N+NfkFt/JEf+a"
        "8a/JLb6TI/4141+TW3wnR/xrxr8mt/hOjvjXjGfyJkY+i5GJkYmRiZEjDpkYmRiZGJn4xngmb2LksxiZGJkYmRg54pCJkYmRiZGJ"
        "b4xn8iZGPouRiZGJkYmRIw6ZGJkYmRiZ+MZ4Jm9i5LMYmRiZGJkYOeKQiZGJkYmRiW+MZ/ImRj6LkYmRiZGJkSMOmRiZGJkYmfjG"
        "eCZvYuSzGJkYmRiZGDnikImRiZGJkYlvjGcyMXLEZzIxMjHyJg65xcgRN5l4ZjyTiZEjPpOJkYmRN3HILUaOuMnEM+OZTIwc8ZlM"
        "jEyMvIlDbjFyxE0mnhnPZGLkiM9kYmRi5E0ccouRI24y8cx4JhMjR3wmEyMTI2/ikFuMHHGTiWfGM5kYOeIzmRiZGHkTh9xi5Iib"
        "TDwzvpEjRm4xMjEy8ZlMjEwccsTIm/jG+EaOGLnFyMTIxGcyMTJxyBEjb+Ib4xs5YuQWIxMjE5/JxMjEIUeMvIlvjG/kiJFbjEyM"
        "THwmEyMThxwx8ia+Mb6RI0ZuMTIxMvGZTIxMHHLEyJv4xvhGjhi5xcjEyMRnMjEyccgRI2/iG+OZHHGTie9k4iYTN5n4TCZGJr4x"
        "nskRN5n4TiZuMnGTic9kYmTiG+OZHHGTie9k4iYTN5n4TCZGJr4xnskRN5n4TiZuMnGTic9kYmTiG+OZHHGTie9k4iYTN5n4TCZG"
        "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"
        "R9A4W9bpZiYAAAAASUVORK5CYII="
    ),
}
WRAP = 440

# Cool mineral greys with a cobalt accent. Amber is reserved for one meaning:
# "something is physically held down right now".
C = {
    "bg": "#E7ECF0",
    "panel": "#F8FAFB",
    "line": "#C5CFD8",
    "ink": "#18232C",
    "muted": "#5A6A77",
    "accent": "#2850B8",
    "accent_hi": "#1F4099",
    "stop": "#B83A2A",
    "stop_hi": "#982F21",
    "field_off": "#EEF1F3",
    "text_off": "#9AA7B2",
}
PILL_TONES = {
    "idle": ("#DAE1E7", C["ink"]),
    "running": ("#CFE8DC", "#17573B"),
    "hold": ("#F7DFA6", "#5E3F00"),
    "rec": ("#F4D3CE", "#7A241A"),
}
STATUS_TONE = {
    "st_running": "running",
    "st_seq_running": "running",
    "st_holding": "hold",
    "st_recording": "rec",
    "st_macro_running": "running",
}


def fmt_ms(v) -> str:
    return f"{v:g}"


def key_to_name(k):
    """pynput key -> short text the key field understands (None = ignore)."""
    if isinstance(k, Key):
        base = re.sub(r"_[lr]$", "", k.name)       # shift_l -> shift
        return base if base in Key.__members__ else k.name
    char = getattr(k, "char", None)
    if char and char.isascii() and char.isprintable() and not char.isspace():
        return char.lower()
    vk = getattr(k, "vk", None)
    if vk is not None:                             # layout-independent fallback
        return f"vk{vk}"
    if char and char.isprintable() and not char.isspace():
        return char
    return None


class Held:
    """Everything currently pressed down, so nothing is ever left stuck."""

    def __init__(self):
        self._lock = threading.Lock()
        self._items = []

    def add(self, ctl, target):
        with self._lock:
            self._items.append((ctl, target))

    def discard(self, ctl, target):
        with self._lock:
            try:
                self._items.remove((ctl, target))
            except ValueError:
                pass

    def release_all(self):
        with self._lock:
            items, self._items = self._items, []
        for ctl, target in reversed(items):
            try:
                ctl.release(target)
            except Exception:
                pass


class KeyRecorder:
    """Waits for one key press anywhere and hands its name to a callback."""

    def __init__(self, app):
        self.app = app
        self.listener = None
        self.on_name = None
        self.on_end = None

    def start(self, on_name, on_end):
        self.stop()
        self.on_name, self.on_end = on_name, on_end
        self.app.capturing = True
        self.listener = keyboard.Listener(on_press=self._on_press)
        self.listener.start()

    def _on_press(self, k):
        name = key_to_name(k)
        if name is None:
            return None
        if name.lower() in RESERVED_KEYS:
            self.app.post(self.app.set_status, "err_key_reserved")
            return None                      # keep listening
        self.app.post(self._finish, name)
        return False                         # stop listening

    def _finish(self, name):
        if self.listener is None:            # cancelled in the meantime
            return
        on_name = self.on_name
        self.stop()
        if on_name:
            on_name(name)

    def stop(self):
        listener, self.listener = self.listener, None
        on_end, self.on_end = self.on_end, None
        self.on_name = None
        self.app.capturing = False
        if listener is not None:
            try:
                listener.stop()
            except Exception:
                pass
        if on_end:
            on_end()


class MacroRecorder:
    """Records global mouse and keyboard activity as a list of timed events.

    Event dicts: {"t": seconds from the first event, "type": move | mouse_down |
    mouse_up | scroll | key_down | key_up, ...}. Clicks inside the app's own
    window and the app's hotkeys (F6/F8/F9) are never recorded, and a release
    is only kept when its press was, so playback can't leave anything stuck."""

    def __init__(self, app):
        self.app = app
        self.events = []
        self.recording = False
        self.limit_hit = False
        self._lock = threading.Lock()
        self._listeners = []
        self._t0 = 0.0
        self._with_moves = False
        self._btn_down = set()
        self._skip_btn = set()
        self._keys_down = {}          # key identity -> recorded name
        self._last_move = 0.0
        self._pos = (0, 0)

    # -- control (Tk thread)
    def start(self, with_moves: bool):
        self.stop()
        with self._lock:
            self.events = []
            self.limit_hit = False
            self._btn_down.clear()
            self._skip_btn.clear()
            self._keys_down.clear()
            self._with_moves = with_moves
            self._last_move = 0.0
            self._t0 = time.monotonic()
            self.recording = True
        self._listeners = [
            mouse.Listener(on_move=self._on_move, on_click=self._on_click,
                           on_scroll=self._on_scroll),
            keyboard.Listener(on_press=self._on_press, on_release=self._on_release),
        ]
        for lst in self._listeners:
            lst.start()

    def stop(self):
        with self._lock:
            was = self.recording
            self.recording = False
            listeners, self._listeners = self._listeners, []
        for lst in listeners:
            try:
                lst.stop()
            except Exception:
                pass
        if not was:
            return self.events
        with self._lock:
            now = time.monotonic() - self._t0
            x, y = self._pos
            for name in sorted(self._btn_down):         # close whatever is still down
                self.events.append({"t": now, "type": "mouse_up", "button": name,
                                    "x": x, "y": y})
            for name in self._keys_down.values():
                self.events.append({"t": now, "type": "key_up", "key": name})
            self._btn_down.clear()
            self._keys_down.clear()
            if self.events:                              # start at zero: no idle lead-in
                first = self.events[0]["t"]
                for ev in self.events:
                    ev["t"] = round(max(ev["t"] - first, 0.0), 3)
        return self.events

    # -- helpers (listener threads)
    def _inside(self, x, y) -> bool:
        rect = self.app.app_rect
        return bool(rect) and rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]

    def _add(self, ev):
        with self._lock:
            if not self.recording:
                return
            if len(self.events) >= MACRO_MAX_EVENTS:
                if not self.limit_hit:
                    self.limit_hit = True
                    self.app.post(self.app.stop_record)
                return
            ev["t"] = time.monotonic() - self._t0
            self.events.append(ev)

    @staticmethod
    def _ident(k):
        vk = getattr(k, "vk", None)
        return ("vk", vk) if vk is not None else ("key", k)

    def _on_move(self, x, y, *_):
        self._pos = (int(x), int(y))
        if not self._with_moves or self._inside(x, y):
            return
        now = time.monotonic()
        if now - self._last_move < MOVE_MIN_GAP_S:
            return
        self._last_move = now
        self._add({"type": "move", "x": int(x), "y": int(y)})

    def _on_click(self, x, y, button, pressed, *_):
        name = getattr(button, "name", None)
        if name not in BUTTON_CHOICES:                  # side buttons aren't supported
            return
        self._pos = (int(x), int(y))
        if pressed:
            if self._inside(x, y):                      # the app's own buttons
                self._skip_btn.add(name)
                return
            self._btn_down.add(name)
            self._add({"type": "mouse_down", "button": name, "x": int(x), "y": int(y)})
        else:
            if name in self._skip_btn:
                self._skip_btn.discard(name)
                return
            if name not in self._btn_down:
                return
            self._btn_down.discard(name)
            self._add({"type": "mouse_up", "button": name, "x": int(x), "y": int(y)})

    def _on_scroll(self, x, y, dx, dy, *_):
        if self._inside(x, y):
            return
        self._add({"type": "scroll", "x": int(x), "y": int(y),
                   "dx": int(dx), "dy": int(dy)})

    def _on_press(self, k, *_):
        name = key_to_name(k)
        if name is None or name.lower() in RESERVED_KEYS:
            return
        ident = self._ident(k)
        if ident in self._keys_down:                    # auto-repeat of a held key
            return
        self._keys_down[ident] = name
        self._add({"type": "key_down", "key": name})

    def _on_release(self, k, *_):
        name = self._keys_down.pop(self._ident(k), None)
        if name is not None:
            self._add({"type": "key_up", "key": name})


class PositionMarker:
    """A small dot, always on top, centred on the click coordinates.

    On Windows the dot is click-through, so it never swallows the clicks it
    points at and can stay visible while running. On other platforms it can't
    be made click-through, so callers hide it while a run is active.
    """

    SIZE = 22
    KEY_COLOR = "#010203"   # becomes transparent on Windows

    def __init__(self, root: tk.Tk):
        self.root = root
        self.win = None
        self.click_through = False

    def _create(self):
        s = self.SIZE
        win = tk.Toplevel(self.root)
        win.withdraw()
        win.overrideredirect(True)
        try:
            win.attributes("-topmost", True)
        except tk.TclError:
            pass

        bg = "#18232C"   # fallback: dark square behind the dot
        if sys.platform == "win32":
            bg = self.KEY_COLOR
            win.configure(bg=bg)
            try:
                win.attributes("-transparentcolor", bg)
            except tk.TclError:
                bg = "#18232C"
        elif sys.platform == "darwin":
            try:
                win.attributes("-transparent", True)
                bg = "systemTransparent"
                win.configure(bg=bg)
            except tk.TclError:
                bg = "#18232C"

        canvas = tk.Canvas(win, width=s, height=s, bg=bg, highlightthickness=0)
        canvas.pack()
        c = s // 2
        canvas.create_oval(2, 2, s - 2, s - 2, fill=C["accent"],
                           outline="white", width=2)
        canvas.create_oval(c - 1, c - 1, c + 1, c + 1, fill="white", outline="white")

        self.win = win
        if sys.platform == "win32":
            self.click_through = self._make_click_through(win)

    @staticmethod
    def _make_click_through(win) -> bool:
        try:
            import ctypes
            win.update_idletasks()
            user32 = ctypes.windll.user32
            hwnd = user32.GetAncestor(win.winfo_id(), 2)   # GA_ROOT
            GWL_EXSTYLE = -20
            LAYERED, TRANSPARENT = 0x00080000, 0x00000020
            TOOLWINDOW, NOACTIVATE = 0x00000080, 0x08000000
            style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            user32.SetWindowLongW(
                hwnd, GWL_EXSTYLE,
                style | LAYERED | TRANSPARENT | TOOLWINDOW | NOACTIVATE)
            return True
        except Exception:
            return False

    def show(self, x: int, y: int):
        if self.win is None:
            self._create()
        half = self.SIZE // 2
        self.win.geometry(f"{self.SIZE}x{self.SIZE}+{x - half}+{y - half}")
        self.win.deiconify()
        self.win.lift()

    def hide(self):
        if self.win is not None:
            self.win.withdraw()

    def destroy(self):
        if self.win is not None:
            try:
                self.win.destroy()
            except tk.TclError:
                pass
            self.win = None


class StepDialog:
    """Modal dialog to add or edit one sequence step. `result` is None if cancelled."""

    def __init__(self, app, step, first):
        self.app = app
        self.result = None
        t = app.t

        editing = step is not None
        step = step or {
            "kind": "mouse_click", "target": "left", "start": "after",
            "delay": 0.0, "duration": DEFAULT_MS["click"],
        }
        is_mouse = step["kind"].startswith("mouse")

        self.top = top = tk.Toplevel(app.root)
        top.withdraw()
        top.title(t("dlg_edit" if editing else "dlg_add"))
        top.configure(bg=C["bg"])
        top.resizable(False, False)
        top.transient(app.root)
        top.protocol("WM_DELETE_WINDOW", self._cancel)

        frm = ttk.Frame(top, padding=16)
        frm.grid()
        frm.columnconfigure(1, weight=1)
        lab = {"sticky": "w", "pady": 5, "padx": (0, 14)}

        ttk.Label(frm, text=t("fld_action")).grid(row=0, column=0, **lab)
        self.kind_box = ttk.Combobox(
            frm, state="readonly", width=30,
            values=[t("act_" + k) for k in ACTION_KINDS])
        self.kind_box.current(ACTION_KINDS.index(step["kind"]))
        self.kind_box.grid(row=0, column=1, sticky="ew", pady=5)
        self.kind_box.bind("<<ComboboxSelected>>", self._on_kind)

        ttk.Label(frm, text=t("fld_target")).grid(row=1, column=0, **lab)
        holder = ttk.Frame(frm)
        holder.grid(row=1, column=1, sticky="ew", pady=5)
        holder.columnconfigure(0, weight=1)
        self.mouse_box = ttk.Combobox(
            holder, state="readonly",
            values=[t("btn_" + k) for k in BUTTON_CHOICES])
        self.mouse_box.current(
            BUTTON_CHOICES.index(step["target"]) if is_mouse else 0)
        self.key_var = tk.StringVar(value="" if is_mouse else step["target"])
        self.key_entry = ttk.Entry(holder, textvariable=self.key_var, width=12)
        self.rec_btn = ttk.Button(holder, text=t("record_key"), width=20,
                                  style="Quiet.TButton", command=self._record)

        ttk.Label(frm, text=t("fld_start")).grid(row=2, column=0, **lab)
        self.start_box = ttk.Combobox(
            frm, state="readonly", width=30,
            values=[t("start_after"), t("start_with")])
        self.start_box.current(START_CHOICES.index(step["start"]))
        self.start_box.grid(row=2, column=1, sticky="ew", pady=5)
        if first:
            self.start_box.current(0)
            self.start_box.configure(state="disabled")

        self.delay_var = tk.StringVar(value=fmt_ms(step["delay"]))
        self.dur_var = tk.StringVar(value=fmt_ms(step["duration"]))
        ttk.Label(frm, text=t("fld_delay")).grid(row=3, column=0, **lab)
        ttk.Entry(frm, textvariable=self.delay_var, width=10
                  ).grid(row=3, column=1, sticky="w", pady=5)
        ttk.Label(frm, text=t("fld_dur")).grid(row=4, column=0, **lab)
        ttk.Entry(frm, textvariable=self.dur_var, width=10
                  ).grid(row=4, column=1, sticky="w", pady=5)

        bar = ttk.Frame(frm)
        bar.grid(row=5, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(bar, text=t("dlg_cancel"), style="Quiet.TButton",
                   command=self._cancel).pack(side="left")
        ttk.Button(bar, text=t("dlg_save"), style="Start.TButton",
                   command=self._save).pack(side="left", padx=(8, 0))

        self._on_kind(keep_duration=True)

        top.update_idletasks()
        x = app.root.winfo_rootx() + 40
        y = app.root.winfo_rooty() + 70
        top.geometry(f"+{x}+{y}")
        top.deiconify()
        try:
            top.wait_visibility()
            top.grab_set()
        except tk.TclError:
            pass
        app.modal = True
        app.dialog = self
        try:
            app.root.wait_window(top)
        finally:
            app.modal = False
            app.dialog = None

    # -------------------------------------------------------------- helpers
    def _kind(self):
        return ACTION_KINDS[self.kind_box.current()]

    def _on_kind(self, _event=None, keep_duration=False):
        kind = self._kind()
        if kind.startswith("mouse"):
            self.key_entry.grid_remove()
            self.rec_btn.grid_remove()
            self.mouse_box.grid(row=0, column=0, columnspan=2, sticky="ew")
        else:
            self.mouse_box.grid_remove()
            self.key_entry.grid(row=0, column=0, sticky="ew")
            self.rec_btn.grid(row=0, column=1, padx=(6, 0))
        if not keep_duration:
            style = kind.split("_")[1]
            if self.dur_var.get().strip() in {fmt_ms(v) for v in DEFAULT_MS.values()}:
                self.dur_var.set(fmt_ms(DEFAULT_MS[style]))

    def _record(self):
        app = self.app
        if app.capturing:
            app.recorder.stop()
            return
        self.top.focus_set()
        self.rec_btn.configure(text=app.t("recording_key"))
        app.recorder.start(on_name=self.key_var.set, on_end=self._record_ended)

    def _record_ended(self):
        try:
            self.rec_btn.configure(text=self.app.t("record_key"))
        except tk.TclError:
            pass

    def _error(self, text):
        messagebox.showerror(self.app.t("err_title"), text, parent=self.top)

    def _save(self):
        app = self.app
        kind = self._kind()
        style = kind.split("_")[1]
        try:
            delay = app.num(self.delay_var.get())
            duration = app.num(self.dur_var.get())
        except ValueError as e:
            self._error(str(e))
            return
        if style == "hold" and duration <= 0:
            self._error(app.t("err_hold_dur"))
            return
        if kind.startswith("mouse"):
            target = BUTTON_CHOICES[self.mouse_box.current()]
        else:
            target = self.key_var.get().strip()
            try:
                keys, _ = app.parse_keys(target)
            except ValueError as e:
                self._error(str(e))
                return
            if not keys:
                self._error(app.t("err_key_empty"))
                return
        self.result = {
            "kind": kind,
            "target": target,
            "start": START_CHOICES[self.start_box.current()],
            "delay": delay,
            "duration": duration,
        }
        self._close()

    def _cancel(self):
        self._close()

    def _close(self):
        self.app.recorder.stop()
        try:
            self.top.grab_release()
        except tk.TclError:
            pass
        self.top.destroy()


class DonateDialog:
    """Where to send thanks. First a choice (money / crypto), then the details."""

    def __init__(self, app):
        self.app = app
        self.images = []            # keep PhotoImage references alive
        self.top = top = tk.Toplevel(app.root)
        top.title(app.t("donate_title"))
        top.configure(bg=C["bg"])
        top.resizable(False, False)
        top.transient(app.root)
        top.protocol("WM_DELETE_WINDOW", self.close)

        self.frm = ttk.Frame(top, padding=16)
        self.frm.grid()
        self.show("menu")

    def show(self, page):
        t = self.app.t
        for w in self.frm.winfo_children():
            w.destroy()
        self.images.clear()
        frm = self.frm
        frm.columnconfigure(0, weight=1)
        ttk.Label(frm, text=t("donate_title"), style="Title.TLabel"
                  ).grid(row=0, column=0, sticky="w")
        if page == "menu":
            self._menu(frm)
        elif page == "money":
            self._money(frm)
        else:
            self._crypto(frm)
        self.top.update_idletasks()
        self.top.geometry(f"+{self.app.root.winfo_rootx() + 50}"
                          f"+{self.app.root.winfo_rooty() + 40}")

    def _bottom(self, frm, row, back):
        t = self.app.t
        bar = ttk.Frame(frm)
        bar.grid(row=row, column=0, sticky="ew")
        bar.columnconfigure(0, weight=1)
        if back:
            ttk.Button(bar, text="\u2190 " + t("donate_back"), style="Quiet.TButton",
                       command=lambda: self.show("menu")).grid(row=0, column=0, sticky="w")
        ttk.Button(bar, text=t("donate_close"), style="Quiet.TButton",
                   command=self.close).grid(row=0, column=1, sticky="e")

    def _menu(self, frm):
        t = self.app.t
        ttk.Label(frm, text=t("donate_intro"), style="Muted.TLabel", wraplength=420,
                  justify="left").grid(row=1, column=0, sticky="w", pady=(4, 14))
        for i, (key, label, ready) in enumerate((
                ("money", t("donate_money_btn"), bool(DONATE_LINKS)),
                ("crypto", t("donate_crypto_btn"), bool(DONATE_CRYPTO)))):
            ttk.Button(frm, text=label if ready else f"{label} \u2014 {t('donate_soon')}",
                       style="Quiet.TButton", padding=(12, 14),
                       state="normal" if ready else "disabled",
                       command=lambda k=key: self.show(k)
                       ).grid(row=2 + i, column=0, sticky="ew", pady=(0, 8))
        self._bottom(frm, 4, back=False)

    def _money(self, frm):
        t = self.app.t
        card = self.app._card(frm, 1, t("donate_money"))
        card.columnconfigure(0, weight=1)
        for i, (name, url) in enumerate(DONATE_LINKS):
            ttk.Button(card, text=name, style="Quiet.TButton",
                       command=lambda u=url: self.app.open_url(u)
                       ).grid(row=i + 1, column=0, sticky="ew", pady=2)
        self._bottom(frm, 2, back=True)

    def _crypto(self, frm):
        t = self.app.t
        ttk.Label(frm, text=t("donate_crypto"), style="Muted.TLabel"
                  ).grid(row=1, column=0, sticky="w", pady=(4, 10))
        grid = ttk.Frame(frm)
        grid.grid(row=2, column=0, sticky="ew")
        for i, (coin, network, address) in enumerate(DONATE_CRYPTO):
            outer = tk.Frame(grid, bg=C["panel"], highlightthickness=1,
                             highlightbackground=C["line"], highlightcolor=C["line"])
            outer.grid(row=0, column=i, sticky="n", padx=(0 if i == 0 else 10, 0))
            card = ttk.Frame(outer, style="Card.TFrame", padding=(12, 10))
            card.pack()
            label = f"{coin} ({network})" if network else coin
            ttk.Label(card, text=label, style="CardTitle.TLabel"
                      ).grid(row=0, column=0, pady=(0, 6))
            data = DONATE_QR.get(address)
            if data:
                img = tk.PhotoImage(data=data)
                self.images.append(img)
                tk.Label(card, image=img, bg="white", bd=0
                         ).grid(row=1, column=0, pady=(0, 8))
            ttk.Label(card, text=address, style="Card.TLabel", wraplength=230,
                      justify="center").grid(row=2, column=0)
            btn = ttk.Button(card, text=t("donate_copy"), style="Quiet.TButton")
            btn.configure(command=lambda a=address, b=btn: self._copy(a, b))
            btn.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(frm, text=t("donate_note"), style="Muted.TLabel", wraplength=440,
                  justify="left").grid(row=3, column=0, sticky="w", pady=(10, 10))
        self._bottom(frm, 4, back=True)

    def _copy(self, text, button):
        self.app.copy_text(text)
        button.configure(text=self.app.t("donate_copied"))

        def restore():
            try:
                button.configure(text=self.app.t("donate_copy"))
            except tk.TclError:
                pass
        self.top.after(1500, restore)

    def alive(self) -> bool:
        try:
            return bool(self.top.winfo_exists())
        except tk.TclError:
            return False

    def close(self):
        try:
            self.top.destroy()
        except tk.TclError:
            pass


class AutoClicker:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.resizable(False, False)

        self.lang = DEFAULT_LANG
        self.mouse_ctl = mouse.Controller()
        self.kb_ctl = keyboard.Controller()
        self.stop_event = threading.Event()
        self.input_lock = threading.Lock()
        self.held = Held()
        self.worker = None
        self.click_count = 0
        self.run_id = 0
        self.capturing = False      # a key is being recorded
        self.modal = False          # the step dialog is open
        self.dialog = None
        self.donate = None
        self.recorder = KeyRecorder(self)
        self.macro = MacroRecorder(self)
        self.app_rect = None         # the window's screen rectangle (for the recorder)
        self._rec_tick_id = None
        self._inbox = queue.Queue()  # worker/listener threads -> Tk thread
        self._drain_id = None

        # Settings live here so they survive a language switch
        self.tab_index = 0
        self.simple_mode = tk.StringVar(value="mouse_click")
        self.button_key = "left"                          # one of BUTTON_CHOICES
        self.key_var = tk.StringVar(value="space")
        self.use_fixed = tk.BooleanVar(value=False)   # off until coordinates are chosen
        self.x_var = tk.StringVar(value="")
        self.y_var = tk.StringVar(value="")
        self.interval_var = tk.StringVar(value="100")
        self.total_var = tk.StringVar(value="0")       # click modes: run time
        self.hold_for_var = tk.StringVar(value="0")    # hold modes: how long to hold
        self.repeats_var = tk.StringVar(value="1")
        self.pause_var = tk.StringVar(value="0")
        self.steps = []             # sequence steps (dicts)
        self.macro_moves_var = tk.BooleanVar(value=False)
        self.macro_repeats_var = tk.StringVar(value="1")
        self.macro_speed_var = tk.StringVar(value="1")
        self.macro_pause_var = tk.StringVar(value="0")
        self.status = tk.StringVar()
        self.status_state = ("st_idle", {})
        self.frm = None
        self.pill = None
        self.active = False        # True from Start until the worker has finished
        self.marker = PositionMarker(root)

        self._setup_style()
        self._build_ui()

        # Keep the on-screen dot in sync with the coordinate fields
        for var in (self.x_var, self.y_var, self.use_fixed):
            var.trace_add("write", lambda *_: self._update_marker())
        # Typing or capturing coordinates means "I chose a position"
        for var in (self.x_var, self.y_var):
            var.trace_add("write", lambda *_: self._coords_chosen())
        self._update_marker()

        self._drain_inbox()
        root.bind("<Configure>", self._on_configure, add="+")
        root.after(50, self._update_rect)

        self.hotkeys = keyboard.GlobalHotKeys({
            "<f8>": lambda: self.post(self.toggle),
            "<f6>": lambda: self.post(self.capture_position),
            "<f9>": lambda: self.post(self.toggle_record),
        })
        self.hotkeys.start()
        root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ------------------------------------------------------------ helpers
    def post(self, fn, *args):
        """Run fn on the Tk thread later. Safe to call from any thread: the
        message goes into a queue that the Tk thread empties every 20 ms."""
        self._inbox.put((fn, args))

    def _drain_inbox(self):
        try:
            while True:
                fn, args = self._inbox.get_nowait()
                try:
                    fn(*args)
                except tk.TclError:
                    pass                     # a widget vanished (language switch)
                except Exception:
                    traceback.print_exc()
        except queue.Empty:
            pass
        self._drain_id = self.root.after(20, self._drain_inbox)

    def _on_configure(self, event):
        if event.widget is self.root:
            self._update_rect()

    def _update_rect(self):
        try:
            r = self.root
            self.app_rect = (r.winfo_x(), r.winfo_y(),
                             r.winfo_rootx() + r.winfo_width(),
                             r.winfo_rooty() + r.winfo_height())
        except tk.TclError:
            self.app_rect = None

    # text_id is positional-only so a placeholder may itself be called "key"/"name"
    def open_url(self, url: str):
        if url.lower().startswith("https://"):      # never open anything else
            webbrowser.open(url)

    def copy_text(self, text: str):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update_idletasks()

    def _open_donate(self):
        if self.donate is not None and self.donate.alive():
            self.donate.top.lift()
            return
        self.donate = DonateDialog(self)

    def t(self, text_id, /, **kw):
        return STRINGS[self.lang][text_id].format(**kw)

    def _status_text(self, text_id, kw):
        if text_id == "st_holding":
            names = [self.t("btn_" + b) for b in kw["buttons"]] + kw["keys"]
            return self.t(text_id, names=", ".join(names))
        return self.t(text_id, **kw)

    def set_status(self, text_id, /, **kw):
        self.status_state = (text_id, kw)
        self.status.set(self._status_text(text_id, kw))
        if self.pill is not None:
            bg, fg = PILL_TONES[STATUS_TONE.get(text_id, "idle")]
            self.pill.configure(bg=bg, fg=fg)

    @property
    def running(self):
        return bool(self.worker and self.worker.is_alive())

    def _on_lang(self, _event=None):
        chosen = self.lang_box.get()
        for code, name in LANG_NAMES.items():
            if name == chosen and code != self.lang:
                self.lang = code
                self._build_ui()
                break

    def num(self, text) -> float:
        """Parse a non-negative number; a comma works as the decimal mark."""
        try:
            v = float(str(text).strip().replace(",", "."))
        except ValueError:
            raise ValueError(self.t("err_numbers"))
        if not math.isfinite(v):
            raise ValueError(self.t("err_numbers"))
        if v < 0:
            raise ValueError(self.t("err_negative"))
        return v

    # ----------------------------------------------------------- styling
    def _setup_style(self):
        available = set(tkfont.families(self.root))
        family = next(
            (f for f in ("Segoe UI", "SF Pro Text", "Helvetica Neue", "Inter",
                         "Noto Sans", "DejaVu Sans") if f in available),
            "TkDefaultFont")
        self.fonts = {
            "base": (family, 10),
            "bold": (family, 10, "bold"),
            "small": (family, 9),
            "title": (family, 20, "bold"),
            "link": (family, 10, "underline"),
        }

        s = ttk.Style(self.root)
        s.theme_use("clam")
        self.root.configure(bg=C["bg"])

        s.configure(".", background=C["bg"], foreground=C["ink"],
                    font=self.fonts["base"], focuscolor=C["accent"])
        s.configure("TFrame", background=C["bg"])
        s.configure("TLabel", background=C["bg"])
        s.configure("Title.TLabel", font=self.fonts["title"])
        s.configure("Muted.TLabel", foreground=C["muted"], font=self.fonts["small"])

        s.configure("Card.TFrame", background=C["panel"])
        s.configure("Card.TLabel", background=C["panel"])
        s.configure("CardTitle.TLabel", background=C["panel"], font=self.fonts["bold"])
        s.configure("Hint.TLabel", background=C["panel"], foreground=C["muted"],
                    font=self.fonts["small"])
        s.configure("Card.TCheckbutton", background=C["panel"])
        s.map("Card.TCheckbutton",
              background=[("active", C["panel"])],
              foreground=[("disabled", C["text_off"])],
              indicatorcolor=[("selected", C["accent"]), ("!selected", "white")])
        s.map("Card.TLabel", foreground=[("disabled", C["text_off"])])

        s.configure("TEntry", fieldbackground="white", bordercolor=C["line"],
                    lightcolor=C["line"], darkcolor=C["line"], padding=4)
        s.map("TEntry",
              fieldbackground=[("disabled", C["field_off"])],
              foreground=[("disabled", C["text_off"])],
              bordercolor=[("focus", C["accent"])])
        s.configure("TCombobox", fieldbackground="white", bordercolor=C["line"],
                    arrowcolor=C["ink"], padding=3)
        s.map("TCombobox", fieldbackground=[("readonly", "white"),
                                            ("disabled", C["field_off"])],
              foreground=[("disabled", C["text_off"])])

        # Tabs: the selected one is dark, the rest recede
        s.configure("TNotebook", background=C["bg"], borderwidth=0,
                    bordercolor=C["bg"], lightcolor=C["bg"], darkcolor=C["bg"],
                    tabmargins=(0, 0, 0, 0))
        s.configure("TNotebook.Tab", background="#D3DBE2", foreground=C["muted"],
                    padding=(20, 9), font=self.fonts["bold"], borderwidth=0,
                    bordercolor="#D3DBE2", lightcolor="#D3DBE2", darkcolor="#D3DBE2")
        s.map("TNotebook.Tab",
              padding=[("selected", (20, 9))],     # clam shrinks the selected tab
              expand=[("selected", (0, 0, 0, 0))],
              background=[("selected", C["ink"]), ("active", "#C4CED7")],
              foreground=[("selected", "white")],
              bordercolor=[("selected", C["ink"])],
              lightcolor=[("selected", C["ink"])],
              darkcolor=[("selected", C["ink"])])

        # Segmented control for the action kind
        s.configure("Seg.Toolbutton", background="#E9EEF2", foreground=C["ink"],
                    bordercolor=C["line"], lightcolor="#E9EEF2", darkcolor="#E9EEF2",
                    padding=(14, 7), relief="solid", anchor="center")
        s.map("Seg.Toolbutton",
              background=[("selected", C["accent"]), ("active", "#DCE4EB")],
              lightcolor=[("selected", C["accent"]), ("active", "#DCE4EB")],
              darkcolor=[("selected", C["accent"]), ("active", "#DCE4EB")],
              bordercolor=[("selected", C["accent_hi"])],
              foreground=[("selected", "white")])

        s.configure("Quiet.TButton", background="white", foreground=C["ink"],
                    bordercolor=C["line"], padding=(10, 6))
        s.map("Quiet.TButton", background=[("active", "#EDF1F5"),
                                           ("disabled", C["field_off"])],
              foreground=[("disabled", C["text_off"])])

        s.configure("Link.TButton", background=C["bg"], foreground=C["accent"],
                    borderwidth=0, padding=(8, 4), font=self.fonts["link"])
        s.map("Link.TButton", background=[("active", C["bg"])],
              foreground=[("active", C["accent_hi"])])

        s.configure("Start.TButton", background=C["accent"], foreground="white",
                    font=self.fonts["bold"], padding=(12, 10), borderwidth=0)
        s.map("Start.TButton",
              background=[("active", C["accent_hi"]), ("pressed", C["accent_hi"])])
        s.configure("Stop.TButton", background=C["stop"], foreground="white",
                    font=self.fonts["bold"], padding=(12, 10), borderwidth=0)
        s.map("Stop.TButton",
              background=[("active", C["stop_hi"]), ("pressed", C["stop_hi"])])

        s.configure("Treeview", background="white", fieldbackground="white",
                    foreground=C["ink"], bordercolor=C["line"],
                    lightcolor=C["line"], darkcolor=C["line"], rowheight=26,
                    font=self.fonts["base"])
        s.map("Treeview", background=[("selected", C["accent"])],
              foreground=[("selected", "white")])
        s.configure("Treeview.Heading", background="#DAE1E7", foreground=C["ink"],
                    font=self.fonts["bold"], relief="flat", padding=(6, 5))
        s.map("Treeview.Heading", background=[("active", "#CBD5DD")])

    def _card(self, parent, row, title):
        outer = tk.Frame(parent, bg=C["panel"], highlightthickness=1,
                         highlightbackground=C["line"], highlightcolor=C["line"])
        outer.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        inner = ttk.Frame(outer, style="Card.TFrame", padding=(12, 10))
        inner.pack(fill="x")
        ttk.Label(inner, text=title, style="CardTitle.TLabel"
                  ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 6))
        return inner

    # -------------------------------------------------------------- UI
    def _build_ui(self):
        self.recorder.stop()
        if self.donate is not None:
            self.donate.close()
            self.donate = None
        if self.frm is not None:
            self.frm.destroy()
        self.root.title(self.t("title"))

        frm = ttk.Frame(self.root, padding=14)
        frm.grid()
        frm.columnconfigure(0, weight=1)
        self.frm = frm

        # Header: app name + language
        head = ttk.Frame(frm)
        head.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        head.columnconfigure(0, weight=1)
        ttk.Label(head, text=self.t("title"), style="Title.TLabel"
                  ).grid(row=0, column=0, sticky="w")
        ttk.Label(head, text=self.t("language"), style="Muted.TLabel"
                  ).grid(row=0, column=1, padx=(0, 6))
        self.lang_box = ttk.Combobox(
            head, values=list(LANG_NAMES.values()), state="readonly", width=10)
        self.lang_box.set(LANG_NAMES[self.lang])
        self.lang_box.grid(row=0, column=2)
        self.lang_box.bind("<<ComboboxSelected>>", self._on_lang)

        # Three pages
        self.nb = nb = ttk.Notebook(frm)
        nb.grid(row=1, column=0, sticky="ew")
        page1 = ttk.Frame(nb, padding=(0, 12, 0, 0))
        page2 = ttk.Frame(nb, padding=(0, 12, 0, 0))
        page3 = ttk.Frame(nb, padding=(0, 12, 0, 0))
        for page in (page1, page2, page3):
            page.columnconfigure(0, weight=1)
        nb.add(page1, text=self.t("tab_simple"))
        nb.add(page2, text=self.t("tab_seq"))
        nb.add(page3, text=self.t("tab_macro"))
        self._build_simple(page1)
        self._build_sequence(page2)
        self._build_macro(page3)
        nb.select(self.tab_index)
        nb.bind("<<NotebookTabChanged>>", self._on_tab)

        self._build_position(frm, 2)
        self._apply_tab_layout()

        # Start / stop + status pill
        self.btn = ttk.Button(
            frm, text=self.t("stop" if self.running else "start"),
            style="Stop.TButton" if self.running else "Start.TButton",
            command=self.toggle)
        self.btn.grid(row=3, column=0, sticky="ew")
        self.pill = tk.Label(frm, textvariable=self.status, font=self.fonts["small"],
                             padx=12, pady=7, anchor="w", justify="left",
                             wraplength=WRAP)
        self.pill.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        if DONATE_LINKS or DONATE_CRYPTO:
            ttk.Button(frm, text="\u2615  " + self.t("coffee"), style="Link.TButton",
                       cursor="hand2", command=self._open_donate
                       ).grid(row=5, column=0, pady=(8, 0))
        self.set_status(self.status_state[0], **self.status_state[1])

        self._refresh_simple()
        self._refresh_steps()
        self._refresh_macro()
        self._sync_record_ui()

    # ---- page 1: simple ----
    def _build_simple(self, page):
        # Action kind: 2 x 2 segmented control
        act = self._card(page, 0, self.t("action_frame"))
        for i, kind in enumerate(ACTION_KINDS):
            ttk.Radiobutton(act, text=self.t("act_" + kind), value=kind,
                            variable=self.simple_mode, style="Seg.Toolbutton",
                            command=self._refresh_simple
                            ).grid(row=1 + i // 2, column=i % 2, sticky="ew",
                                   padx=1, pady=1)
        act.columnconfigure(0, weight=1)
        act.columnconfigure(1, weight=1)
        self.hint_lbl = ttk.Label(act, style="Hint.TLabel", wraplength=WRAP,
                                  justify="left")
        self.hint_lbl.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

        # Target: a mouse button or a key
        tgt = self._card(page, 1, self.t("target_frame"))
        tgt.columnconfigure(0, weight=1)

        self.mouse_target = ttk.Frame(tgt, style="Card.TFrame")
        self.mouse_target.columnconfigure(0, weight=1)
        ttk.Label(self.mouse_target, text=self.t("mouse_button_label"),
                  style="Card.TLabel").grid(row=0, column=0, sticky="w")
        self.button_box = ttk.Combobox(
            self.mouse_target, state="readonly",
            values=[self.t("btn_" + k) for k in BUTTON_CHOICES])
        self.button_box.current(BUTTON_CHOICES.index(self.button_key))
        self.button_box.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        self.button_box.bind("<<ComboboxSelected>>", self._on_button_selected)

        self.key_target = ttk.Frame(tgt, style="Card.TFrame")
        self.key_target.columnconfigure(0, weight=1)
        ttk.Label(self.key_target, text=self.t("keys_label"),
                  style="Card.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Entry(self.key_target, textvariable=self.key_var
                  ).grid(row=1, column=0, sticky="ew", pady=(2, 0))
        self.record_btn = ttk.Button(
            self.key_target, text=self.t("record_key"), width=24,
            style="Quiet.TButton", command=self._record_simple_key)
        self.record_btn.grid(row=1, column=1, padx=(8, 0), pady=(2, 0))

        # Timing
        tim = self._card(page, 2, self.t("timing_frame"))
        tim.columnconfigure(0, weight=1)

        def row(r, text, var):
            lbl = ttk.Label(tim, text=text, style="Card.TLabel")
            ent = ttk.Entry(tim, textvariable=var, width=10)
            lbl.grid(row=r, column=0, sticky="w", pady=2)
            ent.grid(row=r, column=1, sticky="e", pady=2)
            return [lbl, ent]

        # Click: how often, and for how long. Hold: just how long to hold.
        self.click_rows = row(1, self.t("interval"), self.interval_var) \
            + row(2, self.t("total"), self.total_var)
        self.hold_rows = row(1, self.t("hold_for"), self.hold_for_var)

    def _refresh_simple(self):
        device, style = self.simple_mode.get().split("_")
        if device == "mouse":
            self.key_target.grid_remove()
            self.mouse_target.grid(row=1, column=0, columnspan=4, sticky="ew")
        else:
            self.mouse_target.grid_remove()
            self.key_target.grid(row=1, column=0, columnspan=4, sticky="ew")
        self.hint_lbl.configure(text=self.t("hint_hold" if style == "hold"
                                            else "hint_click"))
        shown, hidden = ((self.hold_rows, self.click_rows) if style == "hold"
                         else (self.click_rows, self.hold_rows))
        for w in hidden:
            w.grid_remove()
        for w in shown:
            w.grid()
        self._refresh_position()

    def _on_button_selected(self, _event=None):
        idx = self.button_box.current()
        if idx >= 0:
            self.button_key = BUTTON_CHOICES[idx]

    def _record_simple_key(self):
        if self.capturing:
            self.recorder.stop()
            return
        self.root.focus_set()               # so Space/Enter don't click the button
        self.record_btn.configure(text=self.t("recording_key"))
        self.recorder.start(on_name=self._simple_key_recorded,
                            on_end=self._simple_record_ended)

    def _simple_key_recorded(self, name):
        self.key_var.set(name)
        self.set_status("st_recorded", key=name)

    def _simple_record_ended(self):
        try:
            self.record_btn.configure(text=self.t("record_key"))
        except tk.TclError:
            pass

    # ---- page 2: sequence ----
    def _build_sequence(self, page):
        box = self._card(page, 0, self.t("steps_frame"))
        box.columnconfigure(0, weight=1)

        cols = ("start", "action", "target", "delay", "dur")
        heads = (self.t("col_start"), self.t("col_action"), self.t("col_target"),
                 self.t("col_delay"), self.t("col_dur"))
        widths = (80, 130, 90, 90, 80)
        anchors = ("w", "w", "w", "e", "e")
        self.tree = ttk.Treeview(box, columns=cols, show="headings", height=5,
                                 selectmode="browse")
        for c, h, w, a in zip(cols, heads, widths, anchors):
            self.tree.heading(c, text=h, anchor=a)
            self.tree.column(c, width=w, minwidth=40, anchor=a, stretch=False)
        sb = ttk.Scrollbar(box, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.grid(row=1, column=0, sticky="ew")
        sb.grid(row=1, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._on_tree_select())
        self.tree.bind("<Double-1>", self._on_tree_double)
        self.tree.bind("<Delete>", lambda _e: self._delete_step())

        bar = ttk.Frame(box, style="Card.TFrame")
        bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.add_btn = ttk.Button(bar, text=self.t("btn_add"), style="Quiet.TButton",
                                  command=self._add_step)
        self.edit_btn = ttk.Button(bar, text=self.t("btn_edit"), style="Quiet.TButton",
                                   command=self._edit_step)
        self.del_btn = ttk.Button(bar, text=self.t("btn_delete"), style="Quiet.TButton",
                                  command=self._delete_step)
        self.down_btn = ttk.Button(bar, text="↓", width=3, style="Quiet.TButton",
                                   command=lambda: self._move_step(1))
        self.up_btn = ttk.Button(bar, text="↑", width=3, style="Quiet.TButton",
                                 command=lambda: self._move_step(-1))
        self.add_btn.pack(side="left")
        self.edit_btn.pack(side="left", padx=(6, 0))
        self.del_btn.pack(side="left", padx=(6, 0))
        self.down_btn.pack(side="right")
        self.up_btn.pack(side="right", padx=(0, 6))

        self.seq_hint_lbl = ttk.Label(box, style="Hint.TLabel", wraplength=WRAP,
                                      justify="left")
        self.seq_hint_lbl.grid(row=3, column=0, columnspan=2, sticky="w",
                               pady=(8, 0))

        opt = self._card(page, 1, self.t("repeat_frame"))
        opt.columnconfigure(0, weight=1)
        for i, (label, var) in enumerate([
            (self.t("repeats"), self.repeats_var),
            (self.t("pause"), self.pause_var),
        ]):
            ttk.Label(opt, text=label, style="Card.TLabel"
                      ).grid(row=i + 1, column=0, sticky="w", pady=2)
            ttk.Entry(opt, textvariable=var, width=10
                      ).grid(row=i + 1, column=1, sticky="e", pady=2)

    def _step_row(self, i, s):
        if s["kind"].startswith("mouse"):
            target = self.t("btn_" + s["target"])
        else:
            target = s["target"]
        start = "—" if i == 0 else self.t("start_" + s["start"] + "_short")
        return (start, self.t("act_" + s["kind"]), target,
                fmt_ms(s["delay"]), fmt_ms(s["duration"]))

    def _selected_index(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def _refresh_steps(self, select="keep"):
        if select == "keep":
            select = self._selected_index()
        self.tree.delete(*self.tree.get_children())
        for i, s in enumerate(self.steps):
            self.tree.insert("", "end", iid=str(i), values=self._step_row(i, s))
        if select is not None and 0 <= select < len(self.steps):
            self.tree.selection_set(str(select))
            self.tree.see(str(select))
        self.seq_hint_lbl.configure(
            text=self.t("seq_hint" if self.steps else "seq_empty"))
        self._on_tree_select()
        self._refresh_position()

    def _on_tree_select(self):
        idx = self._selected_index()
        has = idx is not None
        self.edit_btn.state(["!disabled"] if has else ["disabled"])
        self.del_btn.state(["!disabled"] if has else ["disabled"])
        self.up_btn.state(["!disabled"] if has and idx > 0 else ["disabled"])
        self.down_btn.state(
            ["!disabled"] if has and idx < len(self.steps) - 1 else ["disabled"])

    def _on_tree_double(self, event):
        if self.tree.identify_row(event.y):
            self._edit_step()

    def _add_step(self):
        idx = self._selected_index()
        pos = idx + 1 if idx is not None else len(self.steps)
        dlg = StepDialog(self, None, first=(pos == 0))
        if dlg.result:
            self.steps.insert(pos, dlg.result)
            self._refresh_steps(select=pos)

    def _edit_step(self):
        idx = self._selected_index()
        if idx is None:
            return
        dlg = StepDialog(self, self.steps[idx], first=(idx == 0))
        if dlg.result:
            self.steps[idx] = dlg.result
            self._refresh_steps(select=idx)

    def _delete_step(self):
        idx = self._selected_index()
        if idx is None:
            return
        del self.steps[idx]
        self._refresh_steps(select=min(idx, len(self.steps) - 1) if self.steps else None)

    def _move_step(self, d):
        idx = self._selected_index()
        if idx is None:
            return
        new = idx + d
        if 0 <= new < len(self.steps):
            self.steps[idx], self.steps[new] = self.steps[new], self.steps[idx]
            self._refresh_steps(select=new)

    # ---- shared: position ----
    def _build_position(self, parent, row):
        pos = self._card(parent, row, self.t("pos_frame"))
        pos.columnconfigure(4, weight=1)
        chk = ttk.Checkbutton(pos, text=self.t("fixed_chk"), variable=self.use_fixed,
                              style="Card.TCheckbutton")
        chk.grid(row=1, column=0, columnspan=5, sticky="w")
        lx = ttk.Label(pos, text="X", style="Card.TLabel")
        ex = ttk.Entry(pos, textvariable=self.x_var, width=7)
        ly = ttk.Label(pos, text="Y", style="Card.TLabel")
        ey = ttk.Entry(pos, textvariable=self.y_var, width=7)
        cap = ttk.Button(pos, text=self.t("capture_btn"), style="Quiet.TButton",
                         command=self.capture_delayed)
        lx.grid(row=2, column=0, sticky="w", pady=(6, 0))
        ex.grid(row=2, column=1, padx=(6, 14), pady=(6, 0))
        ly.grid(row=2, column=2, sticky="w", pady=(6, 0))
        ey.grid(row=2, column=3, padx=(6, 14), pady=(6, 0))
        cap.grid(row=2, column=4, sticky="ew", pady=(6, 0))
        self.pos_widgets = [chk, lx, ex, ly, ey, cap]
        self.pos_card = pos.master          # the whole card, hidden on the Recording tab

    def _position_relevant(self) -> bool:
        """Coordinates only matter when the current page does mouse actions."""
        if self.tab_index == 2:
            return False                    # a recording carries its own coordinates
        if self.tab_index == 1:
            return any(s["kind"].startswith("mouse") for s in self.steps)
        return self.simple_mode.get().startswith("mouse")

    def _refresh_position(self):
        flag = ["!disabled"] if self._position_relevant() else ["disabled"]
        for w in self.pos_widgets:
            w.state(flag)
        self._update_marker()

    def _on_tab(self, _event=None):
        try:
            self.tab_index = self.nb.index("current")
        except tk.TclError:
            return
        self._apply_tab_layout()
        self._refresh_position()

    def _apply_tab_layout(self):
        if self.tab_index == 2:
            self.pos_card.grid_remove()
        else:
            self.pos_card.grid()

    # ------------------------------------------------------- position capture
    def capture_position(self):
        if self.capturing:
            return
        x, y = self.mouse_ctl.position
        self.x_var.set(str(int(x)))
        self.y_var.set(str(int(y)))
        self.use_fixed.set(True)
        self.set_status("st_captured", x=int(x), y=int(y))

    def capture_delayed(self):
        self.set_status("st_countdown")
        self.root.after(3000, self.capture_position)

    def _coords_chosen(self):
        if (self.x_var.get().strip() or self.y_var.get().strip()) \
                and not self.use_fixed.get():
            self.use_fixed.set(True)

    def _update_marker(self):
        """Show the dot at X, Y while it is relevant and the coordinates are valid."""
        visible = self.use_fixed.get() and self._position_relevant()
        # Where the dot can't be click-through it would swallow the clicks,
        # so it stays hidden while a run is active.
        if visible and self.active and not self.marker.click_through:
            visible = False
        x = y = 0
        if visible:
            try:
                x, y = int(self.x_var.get()), int(self.y_var.get())
            except ValueError:
                visible = False
        if visible:
            self.marker.show(x, y)
        else:
            self.marker.hide()

    # ---- page 3: recording ----
    def _build_macro(self, page):
        rec = self._card(page, 0, self.t("macro_frame"))
        rec.columnconfigure(0, weight=1)
        self.rec_btn = ttk.Button(rec, style="Quiet.TButton", command=self.toggle_record)
        self.rec_btn.grid(row=1, column=0, sticky="ew")
        ttk.Checkbutton(rec, text=self.t("macro_move_chk"), variable=self.macro_moves_var,
                        style="Card.TCheckbutton"
                        ).grid(row=2, column=0, sticky="w", pady=(8, 0))

        box = self._card(page, 1, self.t("macro_list_frame"))
        box.columnconfigure(0, weight=1)
        cols = ("no", "time", "event", "detail")
        heads = (self.t("col_no"), self.t("col_time"), self.t("col_event"),
                 self.t("col_detail"))
        widths = (46, 66, 140, 200)
        anchors = ("e", "e", "w", "w")
        self.macro_tree = ttk.Treeview(box, columns=cols, show="headings", height=5,
                                       selectmode="browse")
        for c, h, w, a in zip(cols, heads, widths, anchors):
            self.macro_tree.heading(c, text=h, anchor=a)
            self.macro_tree.column(c, width=w, minwidth=40, anchor=a, stretch=False)
        sb = ttk.Scrollbar(box, orient="vertical", command=self.macro_tree.yview)
        self.macro_tree.configure(yscrollcommand=sb.set)
        self.macro_tree.grid(row=1, column=0, sticky="ew")
        sb.grid(row=1, column=1, sticky="ns")
        bar = ttk.Frame(box, style="Card.TFrame")
        bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        bar.columnconfigure(0, weight=1)
        self.macro_info = ttk.Label(bar, style="Hint.TLabel")
        self.macro_info.grid(row=0, column=0, sticky="w")
        self.clear_btn = ttk.Button(bar, text=self.t("macro_clear"), style="Quiet.TButton",
                                    command=self._clear_macro)
        self.clear_btn.grid(row=0, column=1, sticky="e")

        play = self._card(page, 2, self.t("macro_play_frame"))
        for i, (label, var) in enumerate([
            (self.t("macro_repeats"), self.macro_repeats_var),
            (self.t("macro_speed"), self.macro_speed_var),
            (self.t("macro_pause"), self.macro_pause_var),
        ]):
            ttk.Label(play, text=label, style="Card.TLabel"
                      ).grid(row=1, column=2 * i, sticky="w", padx=(0 if i == 0 else 12, 4))
            ttk.Entry(play, textvariable=var, width=5
                      ).grid(row=2, column=2 * i, sticky="w", padx=(0 if i == 0 else 12, 4),
                             pady=(2, 0))

    def _macro_detail(self, ev) -> str:
        kind = ev["type"]
        if kind.startswith("key"):
            return ev["key"]
        where = f"({ev['x']}, {ev['y']})"
        if kind == "move":
            return where
        if kind == "scroll":
            parts = []
            if ev["dy"]:
                parts.append(f"{self.t('scroll_up' if ev['dy'] > 0 else 'scroll_down')}"
                             f" x{abs(ev['dy'])}")
            if ev["dx"]:
                parts.append(f"{self.t('scroll_right' if ev['dx'] > 0 else 'scroll_left')}"
                             f" x{abs(ev['dx'])}")
            return ", ".join(parts + [where])
        return f"{self.t('btn_' + ev['button'])}  {where}"

    def _refresh_macro(self):
        events = self.macro.events
        self.macro_tree.delete(*self.macro_tree.get_children())
        for i, ev in enumerate(events):
            self.macro_tree.insert("", "end", iid=str(i), values=(
                i + 1, f"{ev['t']:.2f}", self.t("ev_" + ev["type"]),
                self._macro_detail(ev)))
        if events:
            self.macro_info.configure(text=self.t(
                "macro_summary", n=len(events), s=f"{events[-1]['t']:.1f}"))
        else:
            self.macro_info.configure(text=self.t("macro_empty"))

    def _sync_record_ui(self):
        rec = self.macro.recording
        self.rec_btn.configure(text=self.t("macro_rec_stop" if rec else "macro_rec_start"),
                               style="Stop.TButton" if rec else "Quiet.TButton")
        self.rec_btn.state(["disabled"] if self.running else ["!disabled"])
        self.btn.state(["disabled"] if rec else ["!disabled"])
        busy = rec or self.running or not self.macro.events
        self.clear_btn.state(["disabled"] if busy else ["!disabled"])

    def toggle_record(self):
        if self.macro.recording:
            self.stop_record()
            return
        if self.running or self.capturing or self.modal:
            return
        self._update_rect()
        self.nb.select(2)                      # F9 may come from another page
        self.macro.start(self.macro_moves_var.get())
        self._sync_record_ui()
        self._rec_tick()

    def stop_record(self):
        if not self.macro.recording:
            return
        if self._rec_tick_id is not None:
            try:
                self.root.after_cancel(self._rec_tick_id)
            except tk.TclError:
                pass
            self._rec_tick_id = None
        events = self.macro.stop()
        limit = self.macro.limit_hit
        self._refresh_macro()
        self._sync_record_ui()
        if limit:
            self.set_status("st_rec_limit", n=MACRO_MAX_EVENTS)
        elif events:
            self.set_status("st_rec_done", n=len(events), s=f"{events[-1]['t']:.1f}")
        else:
            self.set_status("st_rec_empty")

    def _rec_tick(self):
        if not self.macro.recording:
            return
        self.set_status("st_recording", n=len(self.macro.events))
        self._rec_tick_id = self.root.after(200, self._rec_tick)

    def _clear_macro(self):
        if self.macro.recording or self.running:
            return
        self.macro.events = []
        self._refresh_macro()
        self._sync_record_ui()
        self.set_status("st_idle")

    def _key_from_name(self, name):
        vk = re.fullmatch(r"vk(\d+)", name)
        if vk:
            return KeyCode.from_vk(int(vk.group(1)))
        if len(name) == 1:
            return name
        return Key.__members__.get(name)

    def _read_macro(self):
        if not self.macro.events:
            raise ValueError(self.t("err_macro_empty"))
        repeats = int(round(self.num(self.macro_repeats_var.get())))
        speed = self.num(self.macro_speed_var.get())
        if speed <= 0:
            raise ValueError(self.t("err_speed"))
        pause = self.num(self.macro_pause_var.get()) / 1000.0
        steps = []
        for ev in self.macro.events:
            st = dict(ev)
            if ev["type"].startswith("mouse"):
                st["obj"] = MOUSE_BUTTONS[ev["button"]]
            elif ev["type"].startswith("key"):
                st["obj"] = self._key_from_name(ev["key"])
                if st["obj"] is None:
                    continue                    # a key this system can't press
            steps.append(st)
        if not steps:
            raise ValueError(self.t("err_macro_empty"))
        return {"type": "macro", "steps": steps, "repeats": repeats,
                "speed": speed, "pause": pause}

    # ------------------------------------------------------------- run control
    def toggle(self):
        if self.running:
            self.stop()
        elif not (self.capturing or self.modal or self.macro.recording):
            self.start()

    def parse_keys(self, text: str):
        """'w, shift, ctrl+c, vk87' -> ([pynput keys], [names as typed])."""
        tokens = []
        for chunk in re.split(r"[,\s]+", text.strip()):
            if not chunk:
                continue
            if len(chunk) > 1 and "+" in chunk:
                tokens += [p for p in chunk.split("+") if p]
            else:
                tokens.append(chunk)

        keys, names = [], []
        for tok in tokens:
            low = tok.lower()
            if low in RESERVED_KEYS:
                raise ValueError(self.t("err_key_reserved"))
            vk = re.fullmatch(r"vk(\d+)", low)
            if vk:
                obj = KeyCode.from_vk(int(vk.group(1)))
            elif len(tok) == 1:
                obj = low
            else:
                obj = Key.__members__.get(low)
                if obj is None:
                    raise ValueError(self.t("err_key_unknown", name=tok))
            if obj not in keys:
                keys.append(obj)
                names.append(tok)
        return keys, names

    def _read_pos(self):
        if self.use_fixed.get() and self._position_relevant():
            try:
                return int(self.x_var.get()), int(self.y_var.get())
            except ValueError:
                raise ValueError(self.t("err_coords"))
        return None

    def _read_simple(self):
        device, style = self.simple_mode.get().split("_")
        if style == "hold":
            total, hold, interval = self.num(self.hold_for_var.get()), 0.0, 0.0
        else:
            total = self.num(self.total_var.get())
            hold = CLICK_PRESS_S
            interval = self.num(self.interval_var.get()) / 1000.0
        pos = self._read_pos()
        if device == "mouse":
            ctl, targets = self.mouse_ctl, [MOUSE_BUTTONS[self.button_key]]
            buttons, key_names = [self.button_key], []
        else:
            keys, key_names = self.parse_keys(self.key_var.get())
            if not keys:
                raise ValueError(self.t("err_key_empty"))
            ctl, targets, buttons, pos = self.kb_ctl, keys, [], None
        return {"type": "simple", "style": style, "ctl": ctl, "targets": targets,
                "pos": pos, "hold": hold, "interval": interval, "total": total,
                "buttons": buttons, "key_names": key_names}

    def _read_sequence(self):
        if not self.steps:
            raise ValueError(self.t("err_seq_empty"))
        repeats = int(round(self.num(self.repeats_var.get())))
        pause = self.num(self.pause_var.get()) / 1000.0
        pos = self._read_pos()

        # A step set to "with" joins the group of the step above it; its delay
        # counts from the moment that step starts. "After" opens a new group.
        groups, prev_offset = [], 0.0
        for i, s in enumerate(self.steps):
            is_mouse = s["kind"].startswith("mouse")
            if is_mouse:
                ctl, targets = self.mouse_ctl, [MOUSE_BUTTONS[s["target"]]]
            else:
                ctl = self.kb_ctl
                targets, _ = self.parse_keys(s["target"])
            delay = s["delay"] / 1000.0
            if i == 0 or s["start"] == "after":
                groups.append([])
                offset = delay
            else:
                offset = prev_offset + delay
            prev_offset = offset
            groups[-1].append({
                "ctl": ctl, "targets": targets,
                "pos": pos if is_mouse else None,
                "offset": offset, "duration": s["duration"] / 1000.0,
            })
        return {"type": "seq", "groups": groups, "repeats": repeats, "pause": pause}

    def start(self):
        if self.macro.recording:
            return
        try:
            if self.tab_index == 2:
                cfg = self._read_macro()
            elif self.tab_index == 1:
                cfg = self._read_sequence()
            else:
                cfg = self._read_simple()
        except ValueError as e:
            messagebox.showerror(self.t("err_title"), str(e), parent=self.root)
            return
        self.run_id += 1
        cfg["run_id"] = self.run_id
        self.stop_event.clear()
        self.click_count = 0
        self.active = True
        self._update_marker()
        self.worker = threading.Thread(target=self._run, args=(cfg,), daemon=True)
        self.worker.start()
        self.btn.configure(text=self.t("stop"), style="Stop.TButton")
        self._sync_record_ui()
        if cfg["type"] == "macro":
            self.set_status("st_macro_running", n=1)
        elif cfg["type"] == "seq":
            self.set_status("st_seq_running", n=1)
        elif cfg["style"] == "hold":
            self.set_status("st_holding", buttons=cfg["buttons"],
                            keys=cfg["key_names"])
        else:
            self.set_status("st_running")

    def stop(self):
        self.stop_event.set()

    def _finished(self, cfg, elapsed):
        if cfg["run_id"] != self.run_id:     # a newer run already took over
            return
        self.active = False
        self._update_marker()
        self.btn.configure(text=self.t("start"), style="Start.TButton")
        self._sync_record_ui()
        if cfg["type"] == "macro":
            self.set_status("st_macro_done", n=self.click_count)
        elif cfg["type"] == "seq":
            self.set_status("st_seq_done", n=self.click_count)
        elif cfg["style"] == "hold":
            self.set_status("st_released", s=f"{elapsed:.1f}")
        else:
            self.set_status("st_stopped", n=self.click_count)

    def _seq_progress(self, run_id, n):
        if run_id == self.run_id and self.active:
            self.set_status("st_seq_running", n=n)

    # ----------------------------------------------------------------- worker
    def _hold_targets(self, ctl, targets, duration, pos):
        """Press all targets together, keep them down for `duration` seconds
        (None = until stopped), then release them in reverse order."""
        mine = []
        try:
            with self.input_lock:
                if pos:
                    self.mouse_ctl.position = pos
                for target in targets:
                    ctl.press(target)
                    mine.append(target)
                    self.held.add(ctl, target)
            self.stop_event.wait(duration)
        finally:
            for target in reversed(mine):
                try:
                    ctl.release(target)
                except Exception:
                    pass
                self.held.discard(ctl, target)

    def _run_simple(self, cfg):
        started = time.monotonic()
        ctl, targets, pos = cfg["ctl"], cfg["targets"], cfg["pos"]
        if cfg["style"] == "hold":
            # until stopped, or until the run time ends (0 = forever)
            self._hold_targets(ctl, targets, cfg["total"] or None, pos)
            return
        while not self.stop_event.is_set():
            if cfg["total"] and time.monotonic() - started >= cfg["total"]:
                break
            self._hold_targets(ctl, targets, cfg["hold"], pos)
            self.click_count += 1
            self.stop_event.wait(max(cfg["interval"], 0.001))

    def _step_thread(self, step):
        try:
            if self.stop_event.wait(step["offset"]):
                return
            self._hold_targets(step["ctl"], step["targets"], step["duration"],
                               step["pos"])
        except Exception:
            self.stop_event.set()            # a failed press halts everything
            raise

    def _run_group(self, group):
        if len(group) == 1:
            self._step_thread(group[0])
            return
        threads = [threading.Thread(target=self._step_thread, args=(s,), daemon=True)
                   for s in group]
        for th in threads:
            th.start()
        for th in threads:
            th.join()

    def _run_sequence(self, cfg):
        rounds = 0
        while not self.stop_event.is_set():
            if cfg["repeats"] and rounds >= cfg["repeats"]:
                break
            if rounds:
                self.post(self._seq_progress, cfg["run_id"], rounds + 1)
            for group in cfg["groups"]:
                if self.stop_event.is_set():
                    break
                self._run_group(group)
            if self.stop_event.is_set():
                break
            rounds += 1
            self.click_count = rounds
            if cfg["repeats"] and rounds >= cfg["repeats"]:
                break
            self.stop_event.wait(max(cfg["pause"], 0.001))

    def _macro_progress(self, run_id, rnd, idx):
        if run_id != self.run_id or not self.active:
            return
        self.set_status("st_macro_running", n=rnd)
        try:
            self.macro_tree.selection_set(str(idx))
            self.macro_tree.see(str(idx))
        except tk.TclError:
            pass

    def _play_event(self, st):
        kind, obj = st["type"], st.get("obj")
        with self.input_lock:
            if kind in ("move", "mouse_down", "mouse_up", "scroll"):
                self.mouse_ctl.position = (st["x"], st["y"])
            if kind == "mouse_down":
                self.mouse_ctl.press(obj)
                self.held.add(self.mouse_ctl, obj)
            elif kind == "mouse_up":
                self.mouse_ctl.release(obj)
                self.held.discard(self.mouse_ctl, obj)
            elif kind == "scroll":
                self.mouse_ctl.scroll(st["dx"], st["dy"])
            elif kind == "key_down":
                self.kb_ctl.press(obj)
                self.held.add(self.kb_ctl, obj)
            elif kind == "key_up":
                self.kb_ctl.release(obj)
                self.held.discard(self.kb_ctl, obj)

    def _run_macro(self, cfg):
        steps, speed, run_id = cfg["steps"], cfg["speed"], cfg["run_id"]
        rounds = 0
        while not self.stop_event.is_set():
            base = time.monotonic()
            last_post = 0.0
            for i, st in enumerate(steps):
                wait = base + st["t"] / speed - time.monotonic()
                if wait > 0 and self.stop_event.wait(wait):
                    break
                if self.stop_event.is_set():
                    break
                self._play_event(st)
                now = time.monotonic()
                if now - last_post > 0.05 or i == len(steps) - 1:
                    last_post = now
                    self.post(self._macro_progress, run_id, rounds + 1, i)
            else:
                rounds += 1
                self.click_count = rounds
                if cfg["repeats"] and rounds >= cfg["repeats"]:
                    break
                self.stop_event.wait(max(cfg["pause"], 0.001))
                continue
            break                                # stopped in the middle of a round

    def _run(self, cfg):
        started = time.monotonic()
        try:
            if cfg["type"] == "macro":
                self._run_macro(cfg)
            elif cfg["type"] == "seq":
                self._run_sequence(cfg)
            else:
                self._run_simple(cfg)
        finally:
            self.held.release_all()          # never leave anything stuck down
            self.post(self._finished, cfg, time.monotonic() - started)

    def on_close(self):
        self.stop_event.set()
        if self._drain_id is not None:
            try:
                self.root.after_cancel(self._drain_id)
            except tk.TclError:
                pass
        self.recorder.stop()
        if self._rec_tick_id is not None:
            try:
                self.root.after_cancel(self._rec_tick_id)
            except tk.TclError:
                pass
        self.macro.stop()
        if self.worker and self.worker.is_alive():
            self.worker.join(timeout=1.0)    # let it release held inputs
        self.held.release_all()
        self.hotkeys.stop()
        self.marker.destroy()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    AutoClicker(root)
    root.mainloop()
