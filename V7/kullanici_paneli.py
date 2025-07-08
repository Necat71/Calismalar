from PyQt6.QtWidgets import (
    QWidget, QTabWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel,
    QMessageBox, QFormLayout, QDialog
)
from PyQt6.QtCore import Qt
import bcrypt
import re
from ui_giris_formu import AnaPencere
class KullaniciYonetimPaneli(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("👥 Kullanıcı Yönetimi")
        self.setFixedSize(400, 300)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._giris_tab(), "🔐 Giriş")
        self.tabs.addTab(self._kayit_tab(), "🆕 Kayıt")
        self.tabs.addTab(self._sil_tab(), "🗑️ Sil")
        self.tabs.addTab(self._sifre_tab(), "🔁 Şifre Değiştir")

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    # 🔐 Giriş Sekmesi
    def _giris_tab(self):
        tab = QWidget()
        layout = QFormLayout()

        self.giris_kullanici = QLineEdit()
        self.giris_sifre = QLineEdit()
        self.giris_sifre.setEchoMode(QLineEdit.EchoMode.Password)

        giris_btn = QPushButton("Giriş Yap")
        giris_btn.clicked.connect(self._giris_kontrol)

        layout.addRow("Kullanıcı Adı:", self.giris_kullanici)
        layout.addRow("Şifre:", self.giris_sifre)
        layout.addRow(giris_btn)
        tab.setLayout(layout)
        return tab

    def _giris_kontrol(self):
        kullanici = self.giris_kullanici.text()
        sifre = self.giris_sifre.text()
        kayit = self.db.kullanici_getir(kullanici)
        if kayit and bcrypt.checkpw(sifre.encode(), kayit[4]):
            QMessageBox.information(self, "Başarılı", "Giriş başarılı!")
            self.accept()
        else:
            QMessageBox.warning(self, "Hatalı Giriş", "Kullanıcı adı veya şifre yanlış.")

    # 🆕 Kayıt Sekmesi
    def _kayit_tab(self):
        tab = QWidget()
        layout = QFormLayout()

        self.kayit_kullanici = QLineEdit()
        self.kayit_email = QLineEdit()
        self.kayit_sifre = QLineEdit()
        self.kayit_sifre.setEchoMode(QLineEdit.EchoMode.Password)

        kayit_btn = QPushButton("Kaydol")
        kayit_btn.clicked.connect(self._kayit_ol)

        layout.addRow("Kullanıcı Adı:", self.kayit_kullanici)
        layout.addRow("E-posta:", self.kayit_email)
        layout.addRow("Şifre:", self.kayit_sifre)
        layout.addRow(kayit_btn)
        tab.setLayout(layout)
        return tab

    def _kayit_ol(self):
        kullanici = self.kayit_kullanici.text()
        email = self.kayit_email.text()
        sifre = self.kayit_sifre.text()

        if not kullanici or not email or not sifre:
            QMessageBox.warning(self, "Eksik Bilgi", "Tüm alanları doldurun.")
            return
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            QMessageBox.warning(self, "Geçersiz E-posta", "Lütfen geçerli bir e-posta girin.")
            return
        if self.db.kullanici_getir(kullanici):
            QMessageBox.warning(self, "Hata", "Bu kullanıcı adı zaten kayıtlı.")
            return

        sifre_hash = bcrypt.hashpw(sifre.encode(), bcrypt.gensalt())
        try:
            self.db.kullanici_ekle(kullanici, email, sifre_hash)
            QMessageBox.information(self, "Başarılı", "Kayıt tamamlandı.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt sırasında hata oluştu:\n{e}")

    # 🗑️ Kullanıcı Sil Sekmesi
    def _sil_tab(self):
        tab = QWidget()
        layout = QFormLayout()

        self.sil_kullanici = QLineEdit()
        sil_btn = QPushButton("Kullanıcıyı Sil")
        sil_btn.clicked.connect(self._kullanici_sil)

        layout.addRow("Kullanıcı Adı:", self.sil_kullanici)
        layout.addRow(sil_btn)
        tab.setLayout(layout)
        return tab

    def _kullanici_sil(self):
        kullanici = self.sil_kullanici.text()
        if not kullanici:
            QMessageBox.warning(self, "Eksik Bilgi", "Kullanıcı adı girin.")
            return
        try:
            self.db.kullanici_sil(kullanici)
            QMessageBox.information(self, "Silindi", "Kullanıcı başarıyla silindi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme işlemi başarısız:\n{e}")

    # 🔁 Şifre Değiştir Sekmesi
    def _sifre_tab(self):
        tab = QWidget()
        layout = QFormLayout()

        self.sifre_kullanici = QLineEdit()
        self.yeni_sifre = QLineEdit()
        self.yeni_sifre.setEchoMode(QLineEdit.EchoMode.Password)

        sifre_btn = QPushButton("Şifreyi Güncelle")
        sifre_btn.clicked.connect(self._sifre_degistir)

        layout.addRow("Kullanıcı Adı:", self.sifre_kullanici)
        layout.addRow("Yeni Şifre:", self.yeni_sifre)
        layout.addRow(sifre_btn)
        tab.setLayout(layout)
        return tab

    def _sifre_degistir(self):
        kullanici = self.sifre_kullanici.text()
        sifre = self.yeni_sifre.text()
        if not kullanici or not sifre:
            QMessageBox.warning(self, "Eksik Bilgi", "Tüm alanları doldurun.")
            return
        sifre_hash = bcrypt.hashpw(sifre.encode(), bcrypt.gensalt())
        try:
            self.db.sifre_guncelle(kullanici, sifre_hash)
            QMessageBox.information(self, "Başarılı", "Şifre güncellendi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Şifre güncellenemedi:\n{e}")
            
            
