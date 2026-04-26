import sys
from io import BytesIO

import qrcode
import qrcode.image.svg
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class QRCodeWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.qr_image = None
        self.svg_data = None

        self.setWindowTitle("QR Code Generator")
        self.setMinimumSize(520, 560)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter text or a URL")
        self.input_field.textChanged.connect(self.generate_qr)

        self.generate_button = QPushButton("Generate")
        self.generate_button.clicked.connect(self.generate_qr)

        self.preview_label = QLabel("Enter text or a URL to generate a QR code.")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(320, 320)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_label.setStyleSheet(
            "QLabel { background: #ffffff; border: 1px solid #d0d0d0; color: #666666; }"
        )

        self.message_label = QLabel("")
        self.message_label.setWordWrap(True)

        self.save_png_button = QPushButton("Save as PNG")
        self.save_png_button.clicked.connect(self.save_png)
        self.save_png_button.setEnabled(False)

        self.save_svg_button = QPushButton("Save as SVG")
        self.save_svg_button.clicked.connect(self.save_svg)
        self.save_svg_button.setEnabled(False)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.generate_button)

        save_layout = QHBoxLayout()
        save_layout.addWidget(self.save_png_button)
        save_layout.addWidget(self.save_svg_button)

        layout = QVBoxLayout()
        layout.addLayout(input_layout)
        layout.addWidget(self.preview_label)
        layout.addWidget(self.message_label)
        layout.addLayout(save_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def generate_qr(self):
        text = self.input_field.text().strip()
        if not text:
            self.qr_image = None
            self.svg_data = None
            self.preview_label.clear()
            self.preview_label.setText("Enter text or a URL to generate a QR code.")
            self.set_message("Input cannot be empty.", error=True)
            self.set_save_buttons_enabled(False)
            return

        self.qr_image = self.create_png_image(text)
        self.svg_data = self.create_svg(text)
        self.update_preview()
        self.set_message("QR code generated.")
        self.set_save_buttons_enabled(True)

    def create_png_image(self, text):
        image = qrcode.make(text)
        if hasattr(image, "get_image"):
            image = image.get_image()
        return image.convert("RGB")

    def update_preview(self):
        if self.qr_image is None:
            return

        buffer = BytesIO()
        self.qr_image.save(buffer, "PNG")

        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue(), "PNG")
        scaled_pixmap = pixmap.scaled(
            self.preview_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_preview()

    def create_svg(self, text):
        factory = qrcode.image.svg.SvgImage
        qr = qrcode.QRCode(image_factory=factory)
        qr.add_data(text)
        qr.make(fit=True)

        buffer = BytesIO()
        qr.make_image().save(buffer)
        return buffer.getvalue()

    def save_png(self):
        if self.qr_image is None:
            self.set_message("Generate a QR code before saving.", error=True)
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save QR Code as PNG",
            "qr-code.png",
            "PNG Image (*.png)",
        )
        if not file_path:
            return

        if not file_path.lower().endswith(".png"):
            file_path += ".png"

        self.qr_image.save(file_path, "PNG")
        self.set_message(f"Saved PNG: {file_path}")

    def save_svg(self):
        if self.svg_data is None:
            self.set_message("Generate a QR code before saving.", error=True)
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save QR Code as SVG",
            "qr-code.svg",
            "SVG Image (*.svg)",
        )
        if not file_path:
            return

        if not file_path.lower().endswith(".svg"):
            file_path += ".svg"

        with open(file_path, "wb") as file:
            file.write(self.svg_data)
        self.set_message(f"Saved SVG: {file_path}")

    def set_save_buttons_enabled(self, enabled):
        self.save_png_button.setEnabled(enabled)
        self.save_svg_button.setEnabled(enabled)

    def set_message(self, message, error=False):
        color = "#b00020" if error else "#1b5e20"
        self.message_label.setStyleSheet(f"QLabel {{ color: {color}; }}")
        self.message_label.setText(message)


def main():
    app = QApplication(sys.argv)
    window = QRCodeWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
