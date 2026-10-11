# PureClick

Free auto-clicker for Windows with a Russian / English interface. Python, Tkinter and [pynput](https://pypi.org/project/pynput/).

Бесплатный автокликер для Windows с русским и английским интерфейсом.

## Features / Возможности

- **Simple / Простой**: mouse click, mouse hold, key click, key hold. A "Record key" button captures any key you press.
- **Sequence / Последовательность**: several steps that run one after another or at the same time.
- **Recording / Запись**: record your mouse and keyboard actions, review them in a list, play them back with repeats and a speed factor.
- Optional fixed click coordinates with an on-screen dot. Without coordinates the mouse works wherever the cursor is.
- Everything pressed is released when you stop, on an error, or when you close the window.

## Hotkeys / Горячие клавиши

| Key | Action |
|-----|--------|
| F8  | Start / stop (or play the recording) |
| F6  | Capture the cursor position |
| F9  | Start / stop recording |

## Run from source / Запуск из исходников

```
pip install pynput
python autoclicker.py
```

## Build the .exe / Сборка .exe

On Windows, install Python (tick "Add python.exe to PATH"), then double-click `build_exe.bat`.
The result is `dist\PureClick.exe`.

Antivirus programs and Windows SmartScreen often flag auto-clickers that record input. This is a false positive; you can read the whole source in `autoclicker.py`.
Антивирусы и SmartScreen часто ругаются на автокликеры с записью ввода. Это ложное срабатывание, исходный код открыт.

## Support / Поддержать

The "Buy me a coffee" button inside the app opens the donation window (DonationAlerts, BTC, ETH).
