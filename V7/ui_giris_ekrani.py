from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout
)
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtCore import Qt


class UiGirisEkrani(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔐 Giriş Paneli")
        self.setFixedSize(360, 240)
        self.setStyleSheet(self._stil_olustur())
        self._arayuz_olustur()

    def _arayuz_olustur(self):
        # Başlık
        baslik = QLabel("Kullanıcı Girişi")
        baslik.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        baslik.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Giriş alanları
        self.kullanici_input = QLineEdit()
        self.kullanici_input.setPlaceholderText("👤 Kullanıcı Adı")

        self.sifre_input = QLineEdit()
        self.sifre_input.setPlaceholderText("🔒 Şifre")
        self.sifre_input.setEchoMode(QLineEdit.EchoMode.Password)

        # Giriş butonu
        self.giris_btn = QPushButton("Giriş Yap")
        self.giris_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # Yerleşim
        layout = QVBoxLayout()
        layout.addWidget(baslik)
        layout.addSpacing(10)
        layout.addWidget(self.kullanici_input)
        layout.addWidget(self.sifre_input)
        layout.addSpacing(10)
        layout.addWidget(self.giris_btn)
        layout.setContentsMargins(40, 30, 40, 30)
        self.setLayout(layout)

    def _stil_olustur(self):
        return """
        QWidget {
            background-color: #1e1e2f;
            color: #f0f0f0;
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
        }
        QLineEdit {
            background-color: #2c2c3c;
            border: 1px solid #444;
            border-radius: 6px;
            padding: 8px;
        }
        QLineEdit:focus {
            border: 1px solid #6c63ff;
            background-color: #2f2f45;
        }
        QPushButton {
            background-color: #6c63ff;
            border: none;
            border-radius: 6px;
            padding: 10px;
            color: white;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #7a72ff;
        }
        QPushButton:pressed {
            background-color: #5a52e0;
        }
        """
