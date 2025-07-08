from PyQt6.QtWidgets import QApplication

def merkezle(pencere):
    ekran = QApplication.primaryScreen().availableGeometry()
    geo = pencere.frameGeometry()
    x = ekran.center().x() - geo.width() // 2
    y = ekran.center().y() - geo.height() // 2
    pencere.move(x, y)
