import pyqrcode


url = input("Enter url to generate: ")

qr_code = pyqrcode.create(url)
qr_code.svg('qrcode.svg', scale=6)
