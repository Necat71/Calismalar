from PyQt6.QtWidgets import QDialog, QMessageBox
from utils.sifreleme import sifre_dogrula
from ui_giris_ekrani import UiGirisEkrani

class GirisEkrani(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.ui = UiGirisEkrani()
        self.setWindowTitle(self.ui.windowTitle())
        self.setFixedSize(self.ui.size())
        self.setLayout(self.ui.layout())
        self.db = db

        self.ui.giris_btn.clicked.connect(self.giris_kontrol)

    def giris_kontrol(self):
        kullanici = self.ui.kullanici_input.text()
        sifre = self.ui.sifre_input.text()

        kayit = self.db.kullanici_getir(kullanici)
        print("Kayıt:", kayit)

        if kayit:
            sifre_hash = kayit[4]
            if sifre_dogrula(sifre, sifre_hash):
                QMessageBox.information(self, "Başarılı", "Giriş başarılı!")
                self.accept()
                return

        QMessageBox.warning(self, "Hatalı Giriş", "Kullanıcı adı veya şifre yanlış.")


