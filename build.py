import subprocess
import sys


APP_NAME = "QRCodeGenerator"


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
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
