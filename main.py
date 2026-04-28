import sys
from io import BytesIO
from pathlib import Path

import qrcode
import qrcode.constants
from PIL import Image, ImageColor, ImageOps
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QCursor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QDialog,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


APP_NAME = "QR Code Generator"
APP_VERSION = "1.0.0"
APP_ICON_PATH = Path("assets/app.ico")

# The UI uses friendly size labels, while generation uses target pixel dimensions.
SIZE_OPTIONS = {
    "Small": 240,
    "Medium": 360,
    "Large": 520,
}

QR_BORDER_MODULES = 4

# Map user-facing error correction names to qrcode's constants.
ERROR_CORRECTION_OPTIONS = {
    "Low": qrcode.constants.ERROR_CORRECT_L,
    "Medium": qrcode.constants.ERROR_CORRECT_M,
    "Quartile": qrcode.constants.ERROR_CORRECT_Q,
    "High": qrcode.constants.ERROR_CORRECT_H,
}


def resource_path(relative_path):
    # PyInstaller extracts bundled files to sys._MEIPASS; development uses the repo path.
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).resolve().parent
    return base_path / relative_path


class QRCodeWindow(QMainWindow):
    def __init__(self, app_icon=None):
        super().__init__()

        self.qr_image = None
        self.svg_data = None
        self.logo_path = None
        self.foreground_color = QColor("#000000")
        self.last_non_black_foreground_color = QColor("#333333")
        self.background_color = QColor("#ffffff")

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        if app_icon is not None and not app_icon.isNull():
            self.setWindowIcon(app_icon)
        self.setMinimumSize(860, 560)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter text or a URL")
        self.input_field.textChanged.connect(self.regenerate_from_settings)

        self.generate_button = QPushButton("Generate")
        self.generate_button.clicked.connect(self.generate_qr)

        self.clear_button = QPushButton("Clear / Reset")
        self.clear_button.clicked.connect(self.clear_form)

        self.foreground_button = QPushButton("Choose foreground")
        self.foreground_button.clicked.connect(self.choose_foreground_color)

        self.background_button = QPushButton("Choose background")
        self.background_button.clicked.connect(self.choose_background_color)

        self.size_selector = QComboBox()
        self.size_selector.addItems(SIZE_OPTIONS.keys())
        self.size_selector.setCurrentText("Medium")
        self.size_selector.currentTextChanged.connect(self.regenerate_from_settings)

        self.error_selector = QComboBox()
        self.error_selector.addItems(ERROR_CORRECTION_OPTIONS.keys())
        self.error_selector.setCurrentText("Medium")
        self.error_selector.currentTextChanged.connect(self.regenerate_from_settings)

        self.error_info_label = QLabel("i")
        self.error_info_label.setAlignment(Qt.AlignCenter)
        self.error_info_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.error_info_label.setFixedSize(20, 20)
        self.error_info_label.setStyleSheet(
            "QLabel { color: #90a4ae; font-weight: 700; border: 1px solid #78909c; "
            "border-radius: 10px; }"
            "QLabel:hover { color: #ffffff; background: #1976d2; border-color: #1976d2; }"
        )
        self.error_info_label.setToolTip(
            "Error correction controls how much damage a QR code can tolerate and still be scanned.\n"
            "Higher levels make the QR more robust but denser.\n"
            "Use High when adding a logo."
        )

        self.choose_logo_button = QPushButton("Choose logo")
        self.choose_logo_button.clicked.connect(self.choose_logo)

        self.remove_logo_button = QPushButton("Remove logo")
        self.remove_logo_button.clicked.connect(self.remove_logo)
        self.remove_logo_button.setEnabled(False)

        self.logo_label = QLabel("No logo selected")
        self.logo_label.setWordWrap(True)

        self.preview_label = QLabel("Enter text or a URL to generate a QR code.")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(380, 380)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_label.setStyleSheet(
            "QLabel { background: #ffffff; border: 1px solid #d0d0d0; color: #666666; }"
        )

        self.message_label = QLabel("")
        self.message_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.message_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.message_label.setWordWrap(True)

        self.save_png_button = QPushButton("Save as PNG")
        self.save_png_button.clicked.connect(self.save_png)
        self.save_png_button.setEnabled(False)
        self.save_png_button.setMinimumHeight(34)
        self.save_png_button.setMinimumWidth(118)

        self.save_svg_button = QPushButton("Save as SVG")
        self.save_svg_button.clicked.connect(self.save_svg)
        self.save_svg_button.setEnabled(False)
        self.save_svg_button.setMinimumHeight(34)
        self.save_svg_button.setMinimumWidth(118)

        self.export_note_label = QLabel(
            "Note: SVG export does not include logos. Use PNG for QR codes with logos."
        )
        self.export_note_label.setWordWrap(True)
        self.export_note_label.setStyleSheet("QLabel { color: #78909c; font-size: 11px; }")

        self.build_layout()
        self.update_color_buttons()

    def build_layout(self):
        # The left panel groups settings; the right panel keeps preview/export controls together.
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(18)

        input_group = QGroupBox("Content")
        input_layout = QVBoxLayout()
        input_layout.setSpacing(10)
        input_layout.addWidget(self.input_field)

        input_buttons = QHBoxLayout()
        input_buttons.setSpacing(8)
        input_buttons.addWidget(self.generate_button)
        input_buttons.addWidget(self.clear_button)
        input_layout.addLayout(input_buttons)
        input_group.setLayout(input_layout)

        colors_group = QGroupBox("Colors")
        color_form = QFormLayout()
        color_form.setVerticalSpacing(12)
        color_form.addRow("Foreground", self.foreground_button)
        color_form.addRow("Background", self.background_button)
        colors_group.setLayout(color_form)

        size_group = QGroupBox("QR Size")
        size_layout = QFormLayout()
        size_layout.setVerticalSpacing(12)
        size_layout.addRow("QR size", self.size_selector)
        size_group.setLayout(size_layout)

        error_group = QGroupBox("Error Correction")
        error_group_layout = QFormLayout()
        error_group_layout.setVerticalSpacing(12)
        error_layout = QHBoxLayout()
        error_layout.setContentsMargins(0, 0, 0, 0)
        error_layout.setSpacing(8)
        error_layout.addWidget(self.error_selector)
        error_layout.addWidget(self.error_info_label)
        error_group_layout.addRow("Error correction", error_layout)
        error_group.setLayout(error_group_layout)

        logo_buttons = QHBoxLayout()
        logo_buttons.setSpacing(8)
        logo_buttons.addWidget(self.choose_logo_button)
        logo_buttons.addWidget(self.remove_logo_button)

        logo_group = QGroupBox("Logo")
        logo_layout = QVBoxLayout()
        logo_layout.setSpacing(10)
        logo_layout.addLayout(logo_buttons)
        logo_layout.addWidget(self.logo_label)
        logo_group.setLayout(logo_layout)

        settings_layout.addWidget(input_group)
        settings_layout.addWidget(colors_group)
        settings_layout.addWidget(size_group)
        settings_layout.addWidget(logo_group)
        settings_layout.addWidget(error_group)
        settings_layout.addStretch()
        settings_group.setLayout(settings_layout)
        settings_group.setMaximumWidth(330)

        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        preview_layout.addWidget(self.preview_label)

        preview_footer_layout = QHBoxLayout()
        preview_footer_layout.setSpacing(10)
        preview_footer_layout.addWidget(self.message_label, 1)
        preview_footer_layout.addWidget(self.save_png_button)
        preview_footer_layout.addWidget(self.save_svg_button)
        preview_layout.addLayout(preview_footer_layout)
        preview_layout.addWidget(self.export_note_label)
        preview_group.setLayout(preview_layout)

        divider = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setFrameShadow(QFrame.Sunken)

        main_layout = QHBoxLayout()
        main_layout.addWidget(settings_group)
        main_layout.addWidget(divider)
        main_layout.addWidget(preview_group, 1)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def generate_qr(self):
        self.rebuild_qr(show_empty_error=True)

    def regenerate_from_settings(self, *_args):
        self.rebuild_qr(show_empty_error=False)

    def rebuild_qr(self, show_empty_error):
        # All input and settings changes flow through this method so preview/export stay in sync.
        text = self.input_field.text().strip()
        if not text:
            self.clear_generated_qr()
            self.preview_label.setText("Enter text or a URL to generate a QR code.")
            if show_empty_error:
                self.set_message("Input cannot be empty.", error=True)
            else:
                self.set_message("")
            return

        qr = self.create_qr(text)
        self.qr_image = self.create_png_image(qr)
        self.svg_data = self.create_svg(qr)
        self.update_preview()
        self.set_message("QR code generated.")
        self.set_save_buttons_enabled(True)

    def create_qr(self, text):
        # Estimate the matrix first so the selected size changes the generated image canvas.
        target_size = SIZE_OPTIONS[self.size_selector.currentText()]
        module_count = self.estimate_module_count(text)
        box_size = max(1, target_size // module_count)

        qr = qrcode.QRCode(
            error_correction=ERROR_CORRECTION_OPTIONS[self.error_selector.currentText()],
            box_size=box_size,
            border=QR_BORDER_MODULES,
        )
        qr.add_data(text)
        qr.make(fit=True)
        return qr

    def estimate_module_count(self, text):
        # Error correction can change QR density, so size calculation must use current settings.
        qr = qrcode.QRCode(
            error_correction=ERROR_CORRECTION_OPTIONS[self.error_selector.currentText()],
            box_size=1,
            border=QR_BORDER_MODULES,
        )
        qr.add_data(text)
        qr.make(fit=True)
        return len(qr.get_matrix())

    def create_png_image(self, qr):
        # PNG output includes colors and the optional centered logo.
        image = qr.make_image(
            fill_color=self.foreground_color.name(),
            back_color=self.background_color.name(),
        )
        if hasattr(image, "get_image"):
            image = image.get_image()
        image = image.convert("RGBA")

        if self.logo_path:
            image = self.add_logo(image)

        return image.convert("RGB")

    def add_logo(self, image):
        # Keep the logo compact and pad it with the QR background color for scan reliability.
        logo = Image.open(self.logo_path).convert("RGBA")
        max_logo_size = max(36, int(min(image.size) * 0.22))
        logo = ImageOps.contain(
            logo,
            (max_logo_size, max_logo_size),
            Image.Resampling.LANCZOS,
        )

        padding = max(6, int(max_logo_size * 0.08))
        background = ImageColor.getcolor(self.background_color.name(), "RGBA")
        logo_box = Image.new(
            "RGBA",
            (logo.width + padding * 2, logo.height + padding * 2),
            background,
        )
        logo_box.paste(logo, (padding, padding), logo)

        x = (image.width - logo_box.width) // 2
        y = (image.height - logo_box.height) // 2
        image.alpha_composite(logo_box, (x, y))
        return image

    def update_preview(self):
        if self.qr_image is None:
            return

        # Load the generated PNG bytes into Qt so the preview matches exported PNG output.
        buffer = BytesIO()
        self.qr_image.save(buffer, "PNG")

        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue(), "PNG")
        preview_size = self.preview_label.size()

        if pixmap.width() > preview_size.width() or pixmap.height() > preview_size.height():
            pixmap = pixmap.scaled(
                preview_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )

        self.preview_label.setPixmap(pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_preview()

    def create_svg(self, qr):
        # SVG export mirrors the QR modules and colors, but intentionally excludes embedded logos.
        matrix = qr.get_matrix()
        box_size = qr.box_size
        module_count = len(matrix)
        total_size = module_count * box_size
        foreground = self.foreground_color.name()
        background = self.background_color.name()

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            (
                f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'width="{total_size}" height="{total_size}" '
                f'viewBox="0 0 {total_size} {total_size}">'
            ),
            f'<rect width="100%" height="100%" fill="{background}"/>',
        ]

        for row_index, row in enumerate(matrix):
            y = row_index * box_size
            for column_index, filled in enumerate(row):
                if filled:
                    x = column_index * box_size
                    lines.append(
                        f'<rect x="{x}" y="{y}" width="{box_size}" '
                        f'height="{box_size}" fill="{foreground}"/>'
                    )

        lines.append("</svg>")
        return "\n".join(lines).encode("utf-8")

    def choose_foreground_color(self):
        dialog_color = self.foreground_color
        if dialog_color.name().lower() == "#000000":
            # Avoid pure black as the dialog seed so the advanced palette starts with visible value.
            dialog_color = self.last_non_black_foreground_color

        dialog = QColorDialog(dialog_color, self)
        dialog.setWindowTitle("Choose foreground color")

        if dialog.exec() == QDialog.Accepted:
            selected_color = dialog.selectedColor()
            if not selected_color.isValid():
                return

            self.foreground_color = QColor(selected_color.name())
            if self.foreground_color.name().lower() != "#000000":
                self.last_non_black_foreground_color = QColor(self.foreground_color.name())
            self.update_color_buttons()
            self.generate_qr()

    def choose_background_color(self):
        color = QColorDialog.getColor(self.background_color, self, "Choose background color")
        if color.isValid():
            self.background_color = color
            self.update_color_buttons()
            self.regenerate_from_settings()

    def update_color_buttons(self):
        self.style_color_button(self.foreground_button, self.foreground_color)
        self.style_color_button(self.background_button, self.background_color)

    def style_color_button(self, button, color):
        button.setText(color.name().upper())
        button.setStyleSheet(
            f"QPushButton {{ background-color: {color.name()}; color: {self.text_color_for(color)}; }}"
        )

    def text_color_for(self, color):
        brightness = (color.red() * 299 + color.green() * 587 + color.blue() * 114) / 1000
        return "#000000" if brightness > 140 else "#ffffff"

    def choose_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Logo Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)",
        )
        if not file_path:
            return

        self.logo_path = file_path
        self.logo_label.setText(Path(file_path).name)
        self.remove_logo_button.setEnabled(True)
        self.error_selector.setCurrentText("High")
        self.regenerate_from_settings()

    def remove_logo(self):
        self.logo_path = None
        self.logo_label.setText("No logo selected")
        self.remove_logo_button.setEnabled(False)
        self.regenerate_from_settings()

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

        if self.logo_path:
            self.set_message(f"Saved SVG without embedded logo: {file_path}")
        else:
            self.set_message(f"Saved SVG: {file_path}")

    def clear_form(self):
        self.input_field.blockSignals(True)
        self.input_field.clear()
        self.input_field.blockSignals(False)

        self.foreground_color = QColor("#000000")
        self.background_color = QColor("#ffffff")
        self.size_selector.setCurrentText("Medium")
        self.error_selector.setCurrentText("Medium")
        self.logo_path = None
        self.logo_label.setText("No logo selected")
        self.remove_logo_button.setEnabled(False)
        self.update_color_buttons()
        self.clear_generated_qr()
        self.preview_label.setText("Enter text or a URL to generate a QR code.")
        self.set_message("")

    def clear_generated_qr(self):
        self.qr_image = None
        self.svg_data = None
        self.preview_label.clear()
        self.set_save_buttons_enabled(False)

    def set_save_buttons_enabled(self, enabled):
        self.save_png_button.setEnabled(enabled)
        self.save_svg_button.setEnabled(enabled)

    def set_message(self, message, error=False):
        color = "#b00020" if error else "#1b5e20"
        self.message_label.setStyleSheet(
            f"QLabel {{ color: {color}; font-size: 15px; font-weight: 600; }}"
        )
        self.message_label.setText(message)

def main():
    app = QApplication(sys.argv)
    # Set the icon on both QApplication and the window for development and packaged builds.
    app_icon_path = resource_path(APP_ICON_PATH)
    app_icon = QIcon(str(app_icon_path)) if app_icon_path.exists() else QIcon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    window = QRCodeWindow(app_icon)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
