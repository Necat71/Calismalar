from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QMessageBox
import bcrypt

class KayitEkrani(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Kayıt Ol")
        self.setFixedSize(300, 200)

        self.kullanici_input = QLineEdit()
        self.kullanici_input.setPlaceholderText("Kullanıcı Adı")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("E-posta")

        self.sifre_input = QLineEdit()
        self.sifre_input.setPlaceholderText("Şifre")
        self.sifre_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.kayit_btn = QPushButton("Kaydol")
        self.kayit_btn.clicked.connect(self.kayit_ol)

        layout = QVBoxLayout()
        layout.addWidget(self.kullanici_input)
        layout.addWidget(self.email_input)
        layout.addWidget(self.sifre_input)
        layout.addWidget(self.kayit_btn)
        self.setLayout(layout)

    def kayit_ol(self):
        kullanici = self.kullanici_input.text()
        email = self.email_input.text()
        sifre = self.sifre_input.text()

        if not kullanici or not email or not sifre:
            QMessageBox.warning(self, "Eksik Bilgi", "Lütfen tüm alanları doldurun.")
            return

        sifre_hash = bcrypt.hashpw(sifre.encode(), bcrypt.gensalt())

        try:
            self.db.kullanici_ekle(kullanici, email, sifre_hash)
            QMessageBox.information(self, "Başarılı", "Kayıt tamamlandı!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt sırasında hata oluştu:\n{e}")
