import sys
import bcrypt
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLineEdit, QPushButton, QMessageBox
)

# Şifre doğrulama fonksiyonu
def sifre_dogrula(girilen_sifre, kayitli_hash):
    return bcrypt.checkpw(girilen_sifre.encode(), kayitli_hash)

# Sahte veritabanı sınıfı
class SahteVeritabani:
    def __init__(self):
        # Anahtar: kullanıcı adı, Değer: hash'lenmiş şifre
        self.kullanicilar = {
            "admin": bcrypt.hashpw("123456".encode(), bcrypt.gensalt()),
            "necati": bcrypt.hashpw("sifre123".encode(), bcrypt.gensalt())
        }

    def kullanici_getir(self, kullanici_adi):
        sifre_hash = self.kullanicilar.get(kullanici_adi)
        if sifre_hash:
            return (kullanici_adi, sifre_hash)
        return None

# Giriş ekranı sınıfı
class GirisEkrani(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Giriş Yap")
        self.setFixedSize(300, 150)

        self.kullanici_input = QLineEdit()
        self.kullanici_input.setPlaceholderText("Kullanıcı Adı")

        self.sifre_input = QLineEdit()
        self.sifre_input.setPlaceholderText("Şifre")
        self.sifre_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.giris_btn = QPushButton("Giriş")
        self.giris_btn.clicked.connect(self.giris_kontrol)

        layout = QVBoxLayout()
        layout.addWidget(self.kullanici_input)
        layout.addWidget(self.sifre_input)
        layout.addWidget(self.giris_btn)
        self.setLayout(layout)

    def giris_kontrol(self):
        kullanici = self.kullanici_input.text()
        sifre = self.sifre_input.text()

        kayit = self.db.kullanici_getir(kullanici)
        print("Kayıt:", kayit)  # DEBUG

        if kayit and sifre_dogrula(sifre, kayit[1]):
            print("Giriş başarılı")  # DEBUG
            QMessageBox.information(self, "Başarılı", "Giriş başarılı!")
            self.accept()
        else:
            print("Giriş başarısız")  # DEBUG
            QMessageBox.warning(self, "Hatalı Giriş", "Kullanıcı adı veya şifre yanlış.")

# Uygulama başlat
if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = SahteVeritabani()
    giris = GirisEkrani(db)
    if giris.exec():
        print("✅ Kullanıcı giriş yaptı.")
    else:
        print("❌ Giriş iptal edildi.")
    sys.exit(0)

