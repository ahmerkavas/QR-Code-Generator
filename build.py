import subprocess
import sys
from pathlib import Path


APP_NAME = "QRCodeGenerator"
APP_ICON_PATH = Path("assets/app.ico")


def main():
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        "--name",
        APP_NAME,
        "main.py",
    ]
    if APP_ICON_PATH.exists():
        command.insert(-1, f"--icon={APP_ICON_PATH}")

    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
