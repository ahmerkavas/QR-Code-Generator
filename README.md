# QR Code Generator

A simple PySide6 desktop application for generating QR codes from text or URLs.

## Features

- Enter text or a URL.
- Generate a live QR preview inside the app.
- Save the generated QR code as PNG.
- Save the generated QR code as SVG.
- Shows a validation error when the input is empty.

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Run

```powershell
python main.py
```

## Build

Install the dependencies first, then build a Windows executable with PyInstaller:

```powershell
pyinstaller --onefile --windowed --name QRCodeGenerator main.py
```

The executable will be created under `dist/`.

## Notes

The app does not overwrite `qrcode.svg` automatically. QR files are written only when you choose a save location from the Save buttons.
