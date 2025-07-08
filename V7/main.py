import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from database import DatabaseManager
from giris_ekrani import GirisEkrani
from kayit_ekrani import KayitEkrani
from giris_formu import GirisFormu
from utils.merkez import merkezle


def main():
    app = QApplication(sys.argv)

    # Uygulama genel stili
    app.setStyleSheet("""
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
        QLabel {
            color: #f0f0f0;
        }
    """)

    db = DatabaseManager("data/sirket.db")

    while True:
        giris_dlg = GirisEkrani(db)
        merkezle(giris_dlg)
        sonuc = giris_dlg.exec()

        if sonuc == giris_dlg.DialogCode.Accepted:
            window = GirisFormu(db)
            window.show()
            merkezle(window)
            sys.exit(app.exec())

        elif getattr(giris_dlg, "kayit_istegi", False):
            kayit_dlg = KayitEkrani(db)
            merkezle(kayit_dlg)
            if kayit_dlg.exec() == kayit_dlg.DialogCode.Accepted:
                QMessageBox.information(None, "Kayıt Başarılı", "Şimdi giriş yapabilirsiniz.")
                continue
            else:
                continue

        else:
            break

    sys.exit(0)


if __name__ == "__main__":
    main()
