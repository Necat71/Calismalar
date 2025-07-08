from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_PozSecimDialog(object):
    def setupUi(self, PozSecimDialog):
        PozSecimDialog.setObjectName("PozSecimDialog")
        PozSecimDialog.resize(1400, 950)
        PozSecimDialog.setMinimumSize(QtCore.QSize(1400, 950))
        PozSecimDialog.setWindowTitle("Poz Seçim Ekranı")

        # Stil dosyası (koyu tema + zebra çizgili tablo)
        PozSecimDialog.setStyleSheet("""
            QDialog {
                background-color: #21202e;
                color: #f3f3f3;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
            }

            QLabel#dialogHeaderLabel {
                font-size: 28px;
                font-weight: bold;
                color: #e6f7ff;
                padding-bottom: 10px;
                margin-bottom: 15px;
            }

           QLineEdit {
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 8px 10px;
                font-size: 14px;
                background-color: white;
                color: black;  /* Yazı rengi */
            }

            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                margin: 2px;
                border-radius: 8px;
                transition: background-color 0.4s;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton#pushButton_ekle {
                background-color: #28a745;
            }
            QPushButton#pushButton_ekle:hover {
                background-color: #218838;
            }
            QPushButton#pushButton_iptal {
                background-color: #dc3545;
            }
            QPushButton#pushButton_iptal:hover {
                background-color: #c82333;
            }

            QTableView {
                background-color: #2a2a3c;
                alternate-background-color: #2f2f45;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 8px;
                selection-background-color: #444c5e;
                selection-color: #ffffff;
                gridline-color: #444;
            }

            QHeaderView::section {
                background-color: #3a3a4a;
                color: #f3f3f3;
                padding: 8px;
                border: 1px solid #555555;
                font-weight: bold;
            }

            QTableView::item {
                padding: 5px;
            }

            QTableView::item:selected {
                background-color: #505c70;
                color: #ffffff;
            }

            QTableView::item:hover {
                background-color: #3c3c5a;
            }
        """)

        # Ana layout
        self.verticalLayout = QtWidgets.QVBoxLayout(PozSecimDialog)
        self.verticalLayout.setContentsMargins(30, 30, 30, 30)
        self.verticalLayout.setSpacing(15)

        # Başlık
        self.dialogHeaderLabel = QtWidgets.QLabel(PozSecimDialog)
        self.dialogHeaderLabel.setObjectName("dialogHeaderLabel")
        self.dialogHeaderLabel.setText("Poz Seçimi ve Yönetimi")
        self.dialogHeaderLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.verticalLayout.addWidget(self.dialogHeaderLabel)

        # Arama Alanı
        self.searchLayout = QtWidgets.QHBoxLayout()
        self.searchLabel = QtWidgets.QLabel(PozSecimDialog)
        self.searchLabel.setText("Poz No veya Açıklama Ara:")
        self.searchLayout.addWidget(self.searchLabel)

        self.lineEdit_pozno = QtWidgets.QLineEdit(PozSecimDialog)
        self.lineEdit_pozno.setPlaceholderText("Poz numarası veya açıklama girin...")
        self.searchLayout.addWidget(self.lineEdit_pozno)

        self.pushButton_ara = QtWidgets.QPushButton("Ara", PozSecimDialog)
        self.searchLayout.addWidget(self.pushButton_ara)
        self.verticalLayout.addLayout(self.searchLayout)

        # Zebra çizgili tablo görünümü
        self.tableView = QtWidgets.QTableView(PozSecimDialog)
        self.tableView.setAlternatingRowColors(True)  # Zebra özelliği aktif
        self.verticalLayout.addWidget(self.tableView)

        # Butonlar
        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.buttonLayout.setSpacing(15)
        self.buttonLayout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        self.pushButton_excel_yukle = QtWidgets.QPushButton("Excel'den Poz Yükle", PozSecimDialog)
        self.buttonLayout.addWidget(self.pushButton_excel_yukle)

        spacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.buttonLayout.addItem(spacer)

        self.pushButton_ekle = QtWidgets.QPushButton("Seçilenleri Ekle", PozSecimDialog)
        self.pushButton_ekle.setObjectName("pushButton_ekle")
        self.buttonLayout.addWidget(self.pushButton_ekle)

        self.pushButton_iptal = QtWidgets.QPushButton("İptal", PozSecimDialog)
        self.pushButton_iptal.setObjectName("pushButton_iptal")
        self.buttonLayout.addWidget(self.pushButton_iptal)

        self.verticalLayout.addLayout(self.buttonLayout)

        QtCore.QMetaObject.connectSlotsByName(PozSecimDialog)

    def retranslateUi(self, PozSecimDialog):
        pass

