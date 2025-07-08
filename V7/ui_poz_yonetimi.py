# This file defines the UI for the PozYonetimDuzenleSilDialog using PyQt6 widgets.
# It is designed to be compatible with the poz_yonetimi.py logic.

from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_PozYonetimiDialog(object):
    def setupUi(self, PozYonetimiDialog):
        # Ana diyalog penceresi ayarları
        PozYonetimiDialog.setObjectName("PozYonetimiDialog")
        PozYonetimiDialog.resize(1400, 900)  # Daha geniş bir pencere boyutu
        PozYonetimiDialog.setMinimumSize(QtCore.QSize(800, 900))
        PozYonetimiDialog.setWindowTitle("Poz Yönetimi (Ekle / Düzenle / Sil)")

        # Modern ve profesyonel stil için CSS
        PozYonetimiDialog.setStyleSheet(
            """
            QDialog {
                background-color: #21202e;
                color: #f3f3f3;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 2px;
            }
            
            QLabel#dialogHeaderLabel {
                font-size: 20px;
                font-weight: bold;
                color: #f1c40f;
                padding-bottom: 10px;
                margin-bottom: 15px;
            }
        
            
            QGroupBox {
                border: 1px solid #d3d3d3;
                border-radius: 8px;
                margin-top: 20px;
                padding-top: 15px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center; /* Başlığı ortaya al */
                padding: 0 10px;
                background-color: #e0e0e0;
                border-radius: 5px;
                font-weight: bold;
                color: #34495e;
            }
            QLineEdit {
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 8px 10px;
                font-size: 12px;
                color: black;
                font-weight: bold;
                background-color: white;
                
                
            }
            QLineEdit:focus {
                border: 2px solid #f1c40f;  /* Altın sarısı */
                background-color: #fcf3cf;  /* Açık altın arka plan */
            }

            
            
            
            QLineEdit:read-only {
                background-color: #e9ecef; /* Salt okunur alanlar için farklı arka plan */
                color: #666;
                font-size: 12px;
            }
            QPushButton {
                background-color: #007bff; /* Mavi tonları */
                color: white;
                border: none;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                margin: 2px;
                border-radius: 8px;
                transition-duration: 0.4s;
            }
            QPushButton:hover {
                background-color: #0056b3; /* Hover rengi */
            }
            QPushButton#pushButton_ekle {
                background-color: #28a745; /* Yeşil ekle butonu */
            }
            QPushButton#pushButton_ekle:hover {
                background-color: #218838;
            }
            QPushButton#pushButton_kaydet {
                background-color: #17a2b8; /* Teklif oluştur gibi */
            }
            QPushButton#pushButton_kaydet:hover {
                background-color: #138496;
            }
            QPushButton#pushButton_duzenle {
                background-color: #ffc107; /* Sarı düzenle butonu */
                color: #333;
            }
            QPushButton#pushButton_duzenle:hover {
                background-color: #e0a800;
            }
            QPushButton#pushButton_sil {
                background-color: #dc3545; /* Kırmızı sil butonu */
            }
            QPushButton#pushButton_sil:hover {
                background-color: #c82333;
            }
            QPushButton#pushButton_temizle {
                background-color: #6c757d; /* Gri temizle butonu */
            }
            QPushButton#pushButton_temizle:hover {
                background-color: #545b62;
            }
            QPushButton#pushButton_excel_import {
                background-color: #20c997; /* Teal import butonu */
            }
            QPushButton#pushButton_excel_import:hover {
                background-color: #17a2b8;
            }
            QPushButton#pushButton_kapat {
                background-color: #6f42c1; /* Mor kapat butonu */
            }
            QPushButton#pushButton_kapat:hover {
                background-color: #5a2e9b;
            }
            QTableView {
                border: 1px solid #d3d3d3;
                border-radius: 8px;
                background-color: white;
                selection-background-color: #e0f2f7; /* Açık mavi seçim */
                gridline-color: #888888; /* Çizgi rengi daha belirgin bir gri yapıldı */
                color: black; /* Yazı rengi siyah yapıldı */
            }
            QHeaderView::section {
                background-color: #e9ecef; /* Açık gri başlık */
                padding: 8px;
                border: 1px solid #d3d3d3;
                font-weight: bold;
                color: #555;
            }
            QTableView::item {
                padding: 5px;
            }
            QTableView::item:selected {
                color: #333; /* Seçili metin rengi */
            }
            QLabel#label_uyari { /* Uyarı etiketi için stil */
                color: red;
                font-weight: bold;
                margin-top: 5px;
                font-size: 24px
            }
        """
        )

        # Ana layout: Dikey Kutular
        self.verticalLayout = QtWidgets.QVBoxLayout(PozYonetimiDialog)
        self.verticalLayout.setContentsMargins(10, 10, 10, 10)
        self.verticalLayout.setSpacing(10)
        self.verticalLayout.setObjectName("verticalLayout")

        # Başlık Label
        self.dialogHeaderLabel = QtWidgets.QLabel(PozYonetimiDialog)
        self.dialogHeaderLabel.setObjectName("dialogHeaderLabel")
        self.dialogHeaderLabel.setText("POZ YÖNETİMİ")
        self.dialogHeaderLabel.setMaximumHeight(50)

        self.dialogHeaderLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.verticalLayout.addWidget(self.dialogHeaderLabel)


        # Giriş Alanları Grubu
        self.inputGroupBox = QtWidgets.QGroupBox(PozYonetimiDialog)
        self.inputGroupBox.setObjectName("inputGroupBox")
        #self.inputGroupBox.setTitle("Poz Bilgileri Girişi")
        self.inputLayout = QtWidgets.QGridLayout(self.inputGroupBox)
        self.inputLayout.setContentsMargins(10, 10, 10, 10)
        self.inputLayout.setSpacing(10)

        self.label_pozNo = QtWidgets.QLabel(self.inputGroupBox)
        self.label_pozNo.setText("Poz No:")
        self.inputLayout.addWidget(self.label_pozNo, 0, 0)

        self.lineEdit_pozNo = QtWidgets.QLineEdit(self.inputGroupBox)
        self.lineEdit_pozNo.setObjectName("lineEdit_pozNo")
        self.lineEdit_pozNo.setPlaceholderText("Poz numarasını girin (Örn: 01.001)")
        self.inputLayout.addWidget(self.lineEdit_pozNo, 0, 1)

        self.label_pozAciklamasi = QtWidgets.QLabel(self.inputGroupBox)
        self.label_pozAciklamasi.setText("Poz Açıklaması:")
        self.inputLayout.addWidget(self.label_pozAciklamasi, 1, 0)
        self.lineEdit_pozAciklamasi = QtWidgets.QLineEdit(self.inputGroupBox)
        self.lineEdit_pozAciklamasi.setObjectName("lineEdit_pozAciklamasi")
        self.lineEdit_pozAciklamasi.setPlaceholderText("Pozun açıklamasını girin")
        self.inputLayout.addWidget(self.lineEdit_pozAciklamasi, 1, 1)

        self.label_olcuBirimi = QtWidgets.QLabel(self.inputGroupBox)
        self.label_olcuBirimi.setText("Ölçü Birimi:")
        self.inputLayout.addWidget(self.label_olcuBirimi, 2, 0)
        self.lineEdit_olcuBirimi = QtWidgets.QLineEdit(self.inputGroupBox)
        self.lineEdit_olcuBirimi.setObjectName("lineEdit_olcuBirimi")
        self.lineEdit_olcuBirimi.setPlaceholderText(
            "Birim girin (Örn: Adet, Metre, Kg)"
        )
        self.inputLayout.addWidget(self.lineEdit_olcuBirimi, 2, 1)

        self.label_rayicBedeli = QtWidgets.QLabel(self.inputGroupBox)
        self.label_rayicBedeli.setText("Birim Fiyat:")
        self.inputLayout.addWidget(self.label_rayicBedeli, 3, 0)
        self.lineEdit_rayicBedeli = QtWidgets.QLineEdit(self.inputGroupBox)
        self.lineEdit_rayicBedeli.setObjectName("lineEdit_rayicBedeli")
        self.lineEdit_rayicBedeli.setPlaceholderText("Birim fiyatı girin (Örn: 123.45)")
        self.inputLayout.addWidget(self.lineEdit_rayicBedeli, 3, 1)

        self.label_uyari = QtWidgets.QLabel(self.inputGroupBox)  # Yeni uyarı etiketi
        self.label_uyari.setObjectName("label_uyari")
        self.label_uyari.setText("")  # Başlangıçta boş
        self.inputLayout.addWidget(self.label_uyari, 4, 0, 1, 2)  # İki sütunu kaplasın

        self.verticalLayout.addWidget(self.inputGroupBox)

        # Butonlar Grubu (Ekle, Kaydet, Düzenle, Sil, Temizle, Excel Import)
        self.actionButtonsLayout = QtWidgets.QHBoxLayout()
        self.actionButtonsLayout.setSpacing(10)
        self.actionButtonsLayout.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignCenter
        )  # Ortaya hizala

        self.pushButton_ekle = QtWidgets.QPushButton(PozYonetimiDialog)
        self.pushButton_ekle.setObjectName("pushButton_ekle")
        self.pushButton_ekle.setText("Yeni Poz Ekle")
        self.actionButtonsLayout.addWidget(self.pushButton_ekle)

        self.pushButton_kaydet = QtWidgets.QPushButton(PozYonetimiDialog)
        self.pushButton_kaydet.setObjectName("pushButton_kaydet")
        self.pushButton_kaydet.setText("Kaydet")
        self.actionButtonsLayout.addWidget(self.pushButton_kaydet)

        self.pushButton_duzenle = QtWidgets.QPushButton(PozYonetimiDialog)
        self.pushButton_duzenle.setObjectName("pushButton_duzenle")
        self.pushButton_duzenle.setText("Pozu Düzenle")
        self.actionButtonsLayout.addWidget(self.pushButton_duzenle)

        self.pushButton_sil = QtWidgets.QPushButton(PozYonetimiDialog)
        self.pushButton_sil.setObjectName("pushButton_sil")
        self.pushButton_sil.setText("Pozu Sil")
        self.actionButtonsLayout.addWidget(self.pushButton_sil)

        self.pushButton_temizle = QtWidgets.QPushButton(PozYonetimiDialog)
        self.pushButton_temizle.setObjectName("pushButton_temizle")
        self.pushButton_temizle.setText("Temizle")
        self.actionButtonsLayout.addWidget(self.pushButton_temizle)

        self.pushButton_excel_import = QtWidgets.QPushButton(PozYonetimiDialog)
        self.pushButton_excel_import.setObjectName("pushButton_excel_import")
        self.pushButton_excel_import.setText("Excel'den İçe Aktar")
        self.actionButtonsLayout.addWidget(self.pushButton_excel_import)

        self.verticalLayout.addLayout(self.actionButtonsLayout)

        # Tablo Görünümü
        self.tableWidget = QtWidgets.QTableWidget(PozYonetimiDialog)
        self.tableWidget.setObjectName("tableWidget")
        self.verticalLayout.addWidget(self.tableWidget)

        # Kapat Butonu
        self.pushButton_kapat = QtWidgets.QPushButton(PozYonetimiDialog)
        self.pushButton_kapat.setObjectName("pushButton_kapat")
        self.pushButton_kapat.setText("Kapat")
        self.verticalLayout.addWidget(
            self.pushButton_kapat, alignment=QtCore.Qt.AlignmentFlag.AlignRight
        )  # Sağa hizala

        QtCore.QMetaObject.connectSlotsByName(PozYonetimiDialog)

    def retranslateUi(self, PozYonetimiDialog):
        _translate = QtCore.QCoreApplication.translate
        # Bu metod normalde Designer tarafından otomatik doldurulur.
        # Metinleri doğrudan yukarıdaki setupUi içinde setText ile belirttik.
        pass
