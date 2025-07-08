import sys
from PyQt6.QtWidgets import QApplication
from database import DatabaseManager
from kayit_ekrani import KayitEkrani

if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = DatabaseManager("data/sirket.db")
    pencere = KayitEkrani(db)
    pencere.exec()
