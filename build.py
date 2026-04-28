import subprocess
import sys
from pathlib import Path


APP_NAME = "QRCodeGenerator"
APP_ICON_PATH = Path("assets/app.ico")
APP_ICON_DATA = "assets/app.ico;assets"


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
        command.insert(-1, f"--add-data={APP_ICON_DATA}")

    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
