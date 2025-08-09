# This class defines a PyQt6 UI for managing project details and includes various widgets like labels,
# line edits, buttons, and a table widget.
from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_ProjeDialog(object):
    def setupUi(self, ProjeDialog):
        ProjeDialog.setObjectName("ProjeDialog")
        ProjeDialog.resize(1920, 980)
        ProjeDialog.setMinimumSize(QtCore.QSize(1500, 900))
        ProjeDialog.setWindowTitle("Proje Yönetimi")

        ProjeDialog.setStyleSheet(
            """
            QDialog {
                background-color: #21202e;
                color: #f3f3f3;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
            }
            QLabel#dialogHeaderLabel {
                font-size: 20px;
                font-weight: bold;
                color: #f3f3f3;
                padding-bottom: 10px;
                margin-bottom: 15px;
            }
            QLabel.summaryLabel {
                font-size: 14px;
                font-weight: bold;
                color: #f3f3f3;
                padding: 5px;
                border: 1px solid #444c5e;
                border-radius: 5px;
                background-color: #2a2a3c;
                margin-top: 10px;
                min-width: 200px;
                text-align: center;
            }
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 8px 10px;
                font-size: 12px;
                background-color: white;
                max-width: 400px;
                color: black;
            }
            
            
            
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                margin: 2px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #0056b3; }
            QPushButton#pushButton_kaydet { background-color: #28a745; }
            QPushButton#pushButton_kaydet:hover { background-color: #218838; }
            QPushButton#pushButton_arsivle { background-color: #ffc107; color: #333; }
            QPushButton#pushButton_arsivle:hover { background-color: #e0a800; }
            QPushButton#pushButton_kapat { background-color: #dc3545; }
            QPushButton#pushButton_kapat:hover { background-color: #c82333; }
            QPushButton#pushButton_teklif_olustur { background-color: #17a2b8; }
            QPushButton#pushButton_teklif_olustur:hover { background-color: #138496; }
            QPushButton#pushButton_ilave { background-color: #6f42c1; }
            QPushButton#pushButton_ilave:hover { background-color: #5a2e9b; } 
            
        """
        )

        self.verticalLayout = QtWidgets.QVBoxLayout(ProjeDialog)
        self.verticalLayout.setContentsMargins(30, 30, 30, 30)
        self.verticalLayout.setSpacing(15)

        self.dialogHeaderLabel = QtWidgets.QLabel(ProjeDialog)
        self.dialogHeaderLabel.setObjectName("dialogHeaderLabel")
        self.dialogHeaderLabel.setText("Proje Detayları ve Yönetimi")
        self.dialogHeaderLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.verticalLayout.addWidget(self.dialogHeaderLabel)

        self.projectInfoLayout = QtWidgets.QGridLayout()
        self.projectInfoLayout.setHorizontalSpacing(0)
        self.projectInfoLayout.setVerticalSpacing(10)

        self.projeAdiRowLayout = QtWidgets.QHBoxLayout()
        self.label_projeadi = QtWidgets.QLabel(ProjeDialog)
        self.label_projeadi.setText("Proje Adı:")
        self.label_projeadi.setFixedWidth(100)
        self.projeAdiRowLayout.addWidget(self.label_projeadi)

        self.lineEdit_projeadi = QtWidgets.QLineEdit(ProjeDialog)
        self.lineEdit_projeadi.setObjectName("lineEdit_projeadi")
        self.lineEdit_projeadi.setPlaceholderText("Proje adını girin...")
        self.lineEdit_projeadi.setFixedWidth(350)
        self.lineEdit_projeadi.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.projeAdiRowLayout.addWidget(self.lineEdit_projeadi)
        self.projeAdiRowLayout.addStretch(1)

        self.projectInfoLayout.addLayout(self.projeAdiRowLayout, 0, 0, 1, 2)

        self.projeAyiRowLayout = QtWidgets.QHBoxLayout()
        self.label_projeayi = QtWidgets.QLabel(ProjeDialog)
        self.label_projeayi.setText("Proje Ayı/Yılı):")
        self.label_projeayi.setFixedWidth(100)
        self.projeAyiRowLayout.addWidget(self.label_projeayi)


        self.lineEdit_projeayi = QtWidgets.QLineEdit(ProjeDialog)
        self.lineEdit_projeayi.setObjectName("lineEdit_projeayi")
        self.lineEdit_projeayi.setPlaceholderText("Örn: 2023/12")
        self.lineEdit_projeayi.setFixedWidth(350)
        self.lineEdit_projeayi.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.projeAyiRowLayout.addWidget(self.lineEdit_projeayi)
        self.projeAyiRowLayout.addStretch(1)

        self.projectInfoLayout.addLayout(self.projeAyiRowLayout, 1, 0, 1, 2)

        self.costDifferenceLayout = QtWidgets.QHBoxLayout()
        self.costDifferenceLayout.setSpacing(20)
        self.costDifferenceLayout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        self.label_fark_yaklasik_teklif = QtWidgets.QLabel(ProjeDialog)
        self.label_fark_yaklasik_teklif.setObjectName("label_fark_yaklasik_teklif")
        self.label_fark_yaklasik_teklif.setText(
            "Kırım Oranı (%0.00)"
        )  # Bu satır güncellendi
        self.label_fark_yaklasik_teklif.setProperty("class", "summaryLabel")
        self.costDifferenceLayout.addWidget(self.label_fark_yaklasik_teklif)

        self.label_fark_teklif_gercek = QtWidgets.QLabel(ProjeDialog)
        self.label_fark_teklif_gercek.setObjectName("label_fark_teklif_gercek")
        self.label_fark_teklif_gercek.setText(
            "Teklif - Gerçek Maliyet Farkı: 0.00 TL (%0.00)"
        )
        self.label_fark_teklif_gercek.setProperty("class", "summaryLabel")
        self.costDifferenceLayout.addWidget(self.label_fark_teklif_gercek)

        self.projectInfoLayout.addLayout(self.costDifferenceLayout, 1, 2, 1, 1)
        self.verticalLayout.addLayout(self.projectInfoLayout)

        self.tabWidget = QtWidgets.QTabWidget(ProjeDialog)
        self.tabWidget.setObjectName("tabWidget")
        self.tabWidget.setStyleSheet(
            """
            QTableWidget {
                background: #23223c; 
                color: #ffffff;
                border-radius: 8px;
            }
            QTableWidget::item:focus {
                outline: none;
                border: none;
            }
        """
        )

        self.tab_proje = QtWidgets.QWidget()
        self.tab_proje.setObjectName("tab_proje")
        self.tabWidget.addTab(self.tab_proje, "Proje Detayları")

        self.tab_poz = QtWidgets.QWidget()
        self.tab_poz.setObjectName("tab_poz")
        self.tabWidget.addTab(self.tab_poz, "Poz Yönetimi")

        # Poz Yönetimi sekmesine layout ekle
        self.tabPozLayout = QtWidgets.QVBoxLayout(self.tab_poz)
        self.tabPozLayout.setContentsMargins(10, 10, 10, 10)
        self.tabPozLayout.setSpacing(10)

        # Örnek bir tablo widget'ı ekle
        self.tableWidget_poz = QtWidgets.QTableWidget(self.tab_poz)
        self.tableWidget_poz.setColumnCount(3)
        self.tableWidget_poz.setHorizontalHeaderLabels(["Poz No", "Açıklama", "Miktar"])
        self.tableWidget_poz.setAlternatingRowColors(True)
        self.tableWidget_poz.setStyleSheet(
            """
            QTableWidget {
                background-color: #2a2a3c;
                color: white;
                border-radius: 8px;
            }
        """
        )

        self.tabPozLayout.addWidget(self.tableWidget_poz)
        self.tabProjectLayout = QtWidgets.QVBoxLayout(self.tab_proje)
        self.tabProjectLayout.setContentsMargins(10, 10, 10, 10)
        self.tabProjectLayout.setSpacing(10)

        self.tableWidget = QtWidgets.QTableWidget(self.tab_proje)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setStyleSheet(
            """
            QTableWidget {
                gridline-color: #888888;
            }
        """
        )

        self.tabProjectLayout.addWidget(self.tableWidget)
        self.verticalLayout.addWidget(self.tabWidget)
        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.buttonLayout.setSpacing(15)
        self.buttonLayout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.pushButton_ilave = QtWidgets.QPushButton(ProjeDialog)
        self.pushButton_ilave.setObjectName("pushButton_ilave")
        self.pushButton_ilave.setText("Poz Ekle")
        # İlave Bilgi Alanı (Poz Ekle butonunun yanına)
        self.label_ilave = QtWidgets.QLabel(ProjeDialog)
        self.label_ilave.setText("Poz Numarası:")
        self.label_ilave.setFixedWidth(100)
        self.buttonLayout.addWidget(self.label_ilave)

        self.lineEdit_ilave = QtWidgets.QLineEdit(ProjeDialog)
        self.lineEdit_ilave.setObjectName("lineEdit_ilave")
        self.lineEdit_ilave.setPlaceholderText("Eklemek istediğiniz numarayı girin")
        self.lineEdit_ilave.setFixedWidth(100)
        self.lineEdit_ilave.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.buttonLayout.addWidget(self.lineEdit_ilave)

        self.buttonLayout.addWidget(self.pushButton_ilave)
        self.pushButton_teklif_olustur = QtWidgets.QPushButton(ProjeDialog)
        self.pushButton_teklif_olustur.setObjectName("pushButton_teklif_olustur")
        self.pushButton_teklif_olustur.setText("Teklif Oluştur (Excel)")
        self.buttonLayout.addWidget(self.pushButton_teklif_olustur)
        self.pushButton_arsivle = QtWidgets.QPushButton(ProjeDialog)
        self.pushButton_arsivle.setObjectName("pushButton_arsivle")
        self.pushButton_arsivle.setText("Projeyi Arşivle")
        self.buttonLayout.addWidget(self.pushButton_arsivle)
        self.pushButton_kaydet = QtWidgets.QPushButton(ProjeDialog)
        self.pushButton_kaydet.setObjectName("pushButton_kaydet")
        self.pushButton_kaydet.setText("Kaydet")
        self.buttonLayout.addWidget(self.pushButton_kaydet)
        self.pushButton_kapat = QtWidgets.QPushButton(ProjeDialog)
        self.pushButton_kapat.setObjectName("pushButton_kapat")
        self.pushButton_kapat.setText("Kapat")
        self.buttonLayout.addWidget(self.pushButton_kapat)

        self.verticalLayout.addLayout(self.buttonLayout)

        QtCore.QMetaObject.connectSlotsByName(ProjeDialog)

    def retranslateUi(self, ProjeDialog):
        pass
