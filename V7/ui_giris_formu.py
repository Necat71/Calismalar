import sys
import os
import pytz
import requests
from datetime import datetime
from datetime import datetime, timedelta
from PyQt6 import QtCore, QtGui, QtWidgets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class AnaPencere(QtWidgets.QWidget):

    def __init__(self, db_instance=None):  # db_instance parametresini ekledik
        super().__init__()
        self.db = db_instance  # Veritabanı yöneticisini sakla
        self.setWindowTitle("Proje Yönetim ve Analiz")
        self.setGeometry(80, 30, 1500, 900)
        self.setMinimumWidth(1500)  # Genişliği 1200 piksel olarak ayarlayabilirsiniz
        self.setMinimumHeight(900)  # Örneğin 800 piksel denenebilir
        
        self.setStyleSheet("""
            QWidget {
                background-color: #21202e;
                color: #f3f3f3;
                font-family: 'Segoe UI', Arial, sans-serif;
                
            
            }
            QFrame#sidebar {
                background-color: #1a1925;
                border-radius: 18px;
                margin-top: 16px;
                margin-bottom: 16px;
            }
            QFrame#headerBar {
                background-color: #282740;
                border-radius: 18px;
            }
            QLabel#titleLabel {
                font-size: 28px;
                font-weight: bold;
                color: #4fc3f7;
                letter-spacing: 2px;
            }
            QPushButton {
                background-color: #26253a;
                border: 2px solid #4fc3f7;
                border-radius: 12px;
                padding: 5px 5px;
                font-size: 13px;
                color: #b0efff;
                margin-top: 4px;
                margin-bottom: 4px;
                transition: all 0.2s;
                max-width: 400px;
            }
            QPushButton:hover {
                background-color: #008cff;
                color: #ffffff;
                border: 2px solid #ffffff;
            }
            QLabel#profileLabel {
                color: #ffffff;
                font-size: 17px;
                font-weight: 600;
                background: #008cff;
                border-radius: 28px;
                padding: 12px 24px;
            }
            QComboBox {
                background-color: #26253a;
                border: 2px solid #4fc3f7;
                border-radius: 12px;
                padding: 8px;
                font-size: 15px;
                color: #b0efff;
                min-width: 200px;
            }
            QComboBox:hover {
                background-color: #008cff;
                color: #fff;
                border: 2px solid #ffffff;
            }
            QComboBox QAbstractItemView {
                background-color: #26253a;
                color: #b0efff;
                selection-background-color: #008cff;
            }
            QFrame#card {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3a3b5c, stop:1 #23223c);
                border-radius: 24px;
                padding: 24px;
            }
            QLabel#cardTitle {
                color: #72fff7;
                font-size: 22px;
                font-weight: bold;
            }
            QLabel#notification {
                color: #ffffff;
                font-size: 16px;
                background: #f1c40f;
                border-radius: 10px;
                padding: 5px 18px;
            }
            QGroupBox {
                font-size: 20px;
                color: #4fc3f7;
                border: 2px solid #4fc3f7;
                border-radius: 12px;
                margin-top: 12px;
                padding: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit {
                background-color: #282740;
                border: 1px solid #4fc3f7;
                border-radius: 8px;
                padding: 8px 15px;
                color: #f3f3f3;
                font-size: 13px;
            }
            QDateEdit {
                background-color: #282740;
                border: 1px solid #4fc3f7;
                border-radius: 8px;
                padding: 8px 15px;
                color: #f3f3f3;
                font-size: 13px;
                qproperty-calendarPopup: true;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #4fc3f7;
                border-left-style: solid;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }
            QTableWidget {
                background: #23223c;
                color: #ffffff;
                border-radius: 8px;
            }
            QTableWidget::item:focus {
                outline: none;
                border: none;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QScrollBar:vertical {
                border: none;
                background: #3b3a5d;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #4fc3f7;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        self.cekler = []
        self.setupUi()
        self.load_ceks_from_db()  # Çekleri veritabanından yükle
        self.start_cek_timer()

    def setupUi(self):
        mainLayout = QtWidgets.QHBoxLayout(self)
        mainLayout.setContentsMargins(12, 12, 12, 12)
        mainLayout.setSpacing(12)

        # --- Sidebar (Sol Panel) ---
        self.sidebar = QtWidgets.QFrame()
        self.sidebar.setObjectName("sidebar")
        sidebarLayout = QtWidgets.QVBoxLayout(self.sidebar)
        sidebarLayout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        sidebarLayout.setSpacing(14)

        # Profil Alanı
        self.profileLabel = QtWidgets.QLabel("👤 Yönetici", self.sidebar)
        self.profileLabel.setObjectName("profileLabel")
        sidebarLayout.addWidget(self.profileLabel)

        # Proje Listesi Combobox
        self.comboBox_projeler = QtWidgets.QComboBox()
        self.comboBox_projeler.addItems([
            "Şeyran Residence",
            "Mavi Gökyüzü Sitesi",
            "Elit Konut Projesi",
            "Yeşil Vadi Rezidans",
            "Lüks Bahçe Evleri"
        ])
        self.comboBox_projeler.setCurrentIndex(-1)  # Başlangıçta seçili olmasın
        self.comboBox_projeler.currentIndexChanged.connect(self.proje_secildi)
        sidebarLayout.addWidget(self.comboBox_projeler)

        # Proje Seç ve Sil Butonları (Yan yana)
        proje_button_layout = QtWidgets.QHBoxLayout()
        proje_button_layout.setSpacing(8)  # Butonlar arası boşluk

        self.btn_proje_sec = QtWidgets.QPushButton("Proje Seç")
        self.btn_proje_sec.setStyleSheet("""
            QPushButton {
                background-color: #26253a;
                border: 2px solid #4CAF50;
                color: #b0efff;
            }
            QPushButton:hover {
                background-color: #4CAF50;
                color: #fff;
            }
        """)
        proje_button_layout.addWidget(self.btn_proje_sec)
        self.btn_proje_sil = QtWidgets.QPushButton("Proje Sil")
        self.btn_proje_sil.clicked.connect(self.proje_sil)  
        
        self.btn_proje_sil.setStyleSheet("""
            QPushButton {
                background-color: #26253a;
                border: 2px solid #f44336;
                color: #b0efff;
            }
            QPushButton:hover {
                background-color: #f44336;
                color: #fff;
            }
        """)
        proje_button_layout.addWidget(self.btn_proje_sil)
        sidebarLayout.addLayout(proje_button_layout)

        # Sidebar Butonları
        buttons = [
            ("🏗️  Proje Oluştur", "Proje oluştur"),
            ("💼  Poz Yönetimi", "Pozları yönetin"),
            ("📈  Analizler", "Projeleriniz üzerinde analiz yapın"),
            ("🚪  Çıkış", "Uygulamadan çık")
        ]
        self.sidebar_buttons = []
        for text, tooltip in buttons:
            btn = QtWidgets.QPushButton(text)
            btn.setToolTip(tooltip)
            sidebarLayout.addWidget(btn)
            self.sidebar_buttons.append(btn)

        self.sidebar_buttons[2].clicked.connect(lambda: self.analysisCard.setVisible(not self.analysisCard.isVisible()))
      
        # Çek Takip Panelini Aç/Kapat Butonu
        self.toggleCekButton = QtWidgets.QPushButton("Çek Panelini Aç/Kapat")
        self.toggleCekButton.clicked.connect(self.toggle_cek_panel)
        sidebarLayout.addWidget(self.toggleCekButton)

        # Analiz Kartı
        self.analysisCard = QtWidgets.QFrame(self.sidebar)
        self.analysisCard.setObjectName("card")
        self.analysisLayout = QtWidgets.QVBoxLayout(self.analysisCard)
        self.analysisLayout.setSpacing(8)

        for text in [
            "Maliyet Fark Analizi", "Kar/Zarar Analizi", "Birim Maliyet Analizi",
            "Tedarikçi Analizi", "Fiyat Analizi", "Poz Kullanım Analizi",
            "Proje Karşılaştırma", "Risk Analizi"
        ]:
            btn = QtWidgets.QPushButton(text, self.analysisCard)
            self.analysisLayout.addWidget(btn)

        self.analysisCard.setVisible(False)  # Başlangıçta gizli
        sidebarLayout.addWidget(self.analysisCard)

        sidebarLayout.addStretch()

        # --- Right Panel (Sağ Panel) ---
        rightPanel = QtWidgets.QVBoxLayout()
        rightPanel.setSpacing(18)

        # Header bar (Sağ panelin üstünde)
        self.headerBar = QtWidgets.QFrame()
        self.headerBar.setObjectName("headerBar")
        self.headerBar.setMinimumHeight(80)
        self.headerBar.setMaximumHeight(80)
            
        headerLayout = QtWidgets.QHBoxLayout(self.headerBar)
        headerLayout.setContentsMargins(8, 8, 8, 8)

        headerLayout.addStretch()  # Sol boşluk
        self.titleLabel = QtWidgets.QLabel("⭐ PROJE YÖNETİM VE ANALİZ SİSTEMİ")
        self.titleLabel.setObjectName("titleLabel")
        self.titleLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        headerLayout.addWidget(self.titleLabel)
        headerLayout.addStretch()  # Sağ boşluk
        rightPanel.addWidget(self.headerBar)

        # Dashboard Kartları
        self.cardsFrame = QtWidgets.QFrame()
        self.cardsFrame.setObjectName("card")
        cardsLayout = QtWidgets.QGridLayout(self.cardsFrame)
        cards = [
            ("📊 Proje Durumu", "Devam eden projelerinizin genel durumu burada özetlenir."),
            ("🔍 Son Analizler", "En son yapılan analizlerin kısa özeti."),
            ("👷 Takım Üyeleri", "Projede çalışan ekip üyeleri ve iletişim bilgileri."),
            ("💡 Notlar & Hatırlatıcılar", "Yaklaşan Önemli Günler")
        ]
        for i, (title, desc) in enumerate(cards):
            card = QtWidgets.QFrame()
            card.setObjectName("card")
            vbox = QtWidgets.QVBoxLayout(card)
            cardTitle = QtWidgets.QLabel(title)
            cardTitle.setObjectName("cardTitle")
            cardDesc = QtWidgets.QLabel(desc)
            cardDesc.setWordWrap(True)
            vbox.addWidget(cardTitle)
            vbox.addWidget(cardDesc)
            cardsLayout.addWidget(card, i // 2, i % 2)
        rightPanel.addWidget(self.cardsFrame)

        # --- Çek Takip Paneli ---
        self.groupCek = QtWidgets.QGroupBox("Çek Takip Paneli")
        self.groupCek.setStyleSheet("""
            QGroupBox {
                font-size: 20px;
                font-weight: bold;
                color: #FFD700;
                border: 2px solid #4fc3f7;
                border-radius: 12px;
                margin-top: 40px;
                padding: 8px;
                background-color: #1e1e1e; /* Koyu arka plan */
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                text-shadow: 1px 1px 2px black; /* Gölge efekti */
            }
        """)
        cekLayout = QtWidgets.QVBoxLayout(self.groupCek)
        formLayout = QtWidgets.QGridLayout()

        # Satır 0
        formLayout.addWidget(QtWidgets.QLabel("Çek No:"), 0, 0, QtCore.Qt.AlignmentFlag.AlignRight)
        self.inputCekNo = QtWidgets.QLineEdit()
        self.inputCekNo.setPlaceholderText("Çek Numarası")
        formLayout.addWidget(self.inputCekNo, 0, 1)

        formLayout.addWidget(QtWidgets.QLabel("Kesilme Trh:"), 0, 2, QtCore.Qt.AlignmentFlag.AlignRight)
        self.inputKesilmeTrh = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self.inputKesilmeTrh.setCalendarPopup(True)
        self.inputKesilmeTrh.setDisplayFormat("dd-MM-yyyy")
        formLayout.addWidget(self.inputKesilmeTrh, 0, 3)

        # Satır 1
        formLayout.addWidget(QtWidgets.QLabel("Vade:"), 1, 0, QtCore.Qt.AlignmentFlag.AlignRight)
        self.inputVade = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self.inputVade.setCalendarPopup(True)
        self.inputVade.setDisplayFormat("dd-MM-yyyy")
        formLayout.addWidget(self.inputVade, 1, 1)

        formLayout.addWidget(QtWidgets.QLabel("Tutar:"), 1, 2, QtCore.Qt.AlignmentFlag.AlignRight)
        self.inputTutar = QtWidgets.QLineEdit()
        self.inputTutar.setPlaceholderText("Çek Tutarı (₺)")
        self.inputTutar.setValidator(QtGui.QDoubleValidator(0.0, 1000000.0, 2))
        formLayout.addWidget(self.inputTutar, 1, 3)

        # Satır 2
        formLayout.addWidget(QtWidgets.QLabel("Alıcı:"), 2, 0, QtCore.Qt.AlignmentFlag.AlignRight)
        self.inputAlici = QtWidgets.QLineEdit()
        self.inputAlici.setPlaceholderText("Alıcı Adı")
        formLayout.addWidget(self.inputAlici, 2, 1)

        formLayout.addWidget(QtWidgets.QLabel("Banka:"), 2, 2, QtCore.Qt.AlignmentFlag.AlignRight)
        self.inputBanka = QtWidgets.QLineEdit()
        self.inputBanka.setPlaceholderText("Banka Adı")
        formLayout.addWidget(self.inputBanka, 2, 3)

        # Satır 3
        formLayout.addWidget(QtWidgets.QLabel("Resim:"), 3, 0, QtCore.Qt.AlignmentFlag.AlignRight)
        resimLayout = QtWidgets.QHBoxLayout()
        self.btnResimSec = QtWidgets.QPushButton("Resim Seç")
        self.btnResimSec.clicked.connect(self.resim_sec)
        self.labelResimYolu = QtWidgets.QLabel("Resim Seçilmedi")
        self.labelResimYolu.setStyleSheet("color: #ccc;")
        resimLayout.addWidget(self.btnResimSec)
        resimLayout.addWidget(self.labelResimYolu)
        formLayout.addLayout(resimLayout, 3, 1, 1, 3)  # 1 satır, 3 sütun kapla

        cekLayout.addLayout(formLayout)

        # Çek Ekle, Sil, Temizle Butonları
        buttonLayout = QtWidgets.QHBoxLayout()
        self.btnCekEkle = QtWidgets.QPushButton("Çek Ekle")
        self.btnCekEkle.clicked.connect(self.cek_ekle)
        self.btnCekSil = QtWidgets.QPushButton("Çek Sil")
        self.btnCekSil.clicked.connect(self.cek_sil)
        self.btnCekTemizle = QtWidgets.QPushButton("Temizle")
        self.btnCekTemizle.clicked.connect(self.clear_inputs)

        buttonLayout.addWidget(self.btnCekEkle)
        buttonLayout.addWidget(self.btnCekSil)
        buttonLayout.addWidget(self.btnCekTemizle)
        cekLayout.addLayout(buttonLayout)

        # Çek Tablosu
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Çek No", "Kesilme Tarihi", "Vade", "Tutar", "Alıcı", "Banka", "Resim", "Durum"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        cekLayout.addWidget(self.table)
        
        self.groupCek.setVisible(False)  # Başlangıçta gizli
        rightPanel.addWidget(self.groupCek)

        mainLayout.addWidget(self.sidebar, 1)  # Sidebar'a esneklik katsayısı
        mainLayout.addLayout(rightPanel, 4)  # Sağ panele daha fazla esneklik

        self.resimYolu = ""  # Resim yolunu saklamak için

    def load_ceks_from_db(self):
        if self.db:
            self.cekler = self.db.get_all_cekler()
            self.populate_cek_table()
        else:
            QtWidgets.QMessageBox.warning(self, "Veritabanı Hatası", "Veritabanı bağlantısı mevcut değil.")

    # ui_giris_formu.py dosyasındaki populate_cek_table metodu
    def populate_cek_table(self):
        self.table.setRowCount(0)  # Mevcut satırları temizle
        for row, cek in enumerate(self.cekler):
            self.table.insertRow(row)

            # cek_no için
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(cek["cek_no"]))

            # kesilme_trh için
            # Veritabanında tarihlerin hangi formatta saklandığına bağlı olarak %Y-%m-%d kısmını ayarlamanız gerekebilir.
            # Genellikle "YYYY-MM-DD" formatında saklanır.
            try:
                # Metin tarihi datetime nesnesine dönüştür
                kesilme_tarihi_obj = datetime.strptime(cek["kesilme_trh"], "%Y-%m-%d")
                # İstenen formatta (GG-AA-YYYY) metne çevirip tabloya ekle
                self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(kesilme_tarihi_obj.strftime("%d-%m-%Y")))
            except ValueError:
                # Eğer tarih formatı beklenen gibi değilse veya doğrudan kullanılabilecek formatta ise
                # hata oluştuğunda orijinal metni kullan
                self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(cek["kesilme_trh"]))

            # vade için (kesilme_trh ile aynı mantık)
            try:
                vade_tarihi_obj = datetime.strptime(cek["vade"], "%Y-%m-%d")
                self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(vade_tarihi_obj.strftime("%d-%m-%Y")))
            except ValueError:
                self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(cek["vade"]))

            # tutar için
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(cek["tutar"])))

            # alici için
            self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(cek["alici"]))

            # banka için
            self.table.setItem(row, 5, QtWidgets.QTableWidgetItem(cek["banka"]))

            # resim_yolu için
            if cek["resim_yolu"]:
                self.table.setItem(row, 6, QtWidgets.QTableWidgetItem(cek["resim_yolu"]))
            else:
                self.table.setItem(row, 6, QtWidgets.QTableWidgetItem("Yok"))

    def toggle_cek_panel(self):
        self.groupCek.setVisible(not self.groupCek.isVisible())

    def resim_sec(self):
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Resim Seç", "", "Resim Dosyaları (*.png *.jpg *.jpeg *.gif)"
        )
        if filePath:
            self.resimYolu = filePath
            self.labelResimYolu.setText(os.path.basename(filePath))

    def resim_goster(self, resim_yolu):
        if resim_yolu and os.path.exists(resim_yolu):
            pixmap = QtGui.QPixmap(resim_yolu)
            if pixmap.isNull():
                QtWidgets.QMessageBox.warning(self, "Hata", "Resim yüklenemedi.")
                return

            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Çek Resmi")
            dialog.setMinimumSize(400, 300)
            layout = QtWidgets.QVBoxLayout(dialog)
            
            label = QtWidgets.QLabel()
            label.setPixmap(pixmap.scaled(dialog.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation))
            label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
            dialog.exec()
        else:
            QtWidgets.QMessageBox.warning(self, "Hata", "Resim yolu geçersiz veya resim bulunamadı.")
            
    def cek_ekle(self):
        cek_no = self.inputCekNo.text()
        kesilme_trh = self.inputKesilmeTrh.date().toPyDate()
        vade = self.inputVade.date().toPyDate()
        tutar = self.inputTutar.text()
        alici = self.inputAlici.text()
        banka = self.inputBanka.text()
        resim = self.resimYolu

        if not (cek_no and tutar and alici and banka):
            QtWidgets.QMessageBox.warning(self, "Eksik Bilgi", "Tüm alanları doldurun!")
            return

        if self.db and self.db.add_cek(cek_no, kesilme_trh.strftime("%Y-%m-%d"), vade.strftime("%Y-%m-%d"), tutar, alici, banka, resim):
            # Veritabanına başarıyla eklendikten sonra UI'ı ve dahili listeyi güncelle
            QtWidgets.QMessageBox.information(self, "Başarılı", "Çek başarıyla eklendi.")
            self.load_ceks_from_db()  # Veritabanından çekleri yeniden yükle ve tabloyu güncelle
            self.clear_inputs()
        else:
            QtWidgets.QMessageBox.critical(self, "Hata", "Çek eklenirken bir hata oluştu.")

    def cek_sil(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            cek_no_item = self.table.item(selected_row, 0)
            if cek_no_item:
                cek_no_to_delete = cek_no_item.text()
                confirm = QtWidgets.QMessageBox.question(
                    self,
                    "Onay",
                    f"'{cek_no_to_delete}' numaralı çeki silmek istediğinize emin misiniz?",
                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                    QtWidgets.QMessageBox.StandardButton.No
                )
                if confirm == QtWidgets.QMessageBox.StandardButton.Yes:
                    if self.db and self.db.delete_cek(cek_no_to_delete):
                        QtWidgets.QMessageBox.information(self, "Başarılı", "Çek başarıyla silindi.")
                        self.load_ceks_from_db()  # Veritabanından çekleri yeniden yükle ve tabloyu güncelle
                    else:
                        QtWidgets.QMessageBox.critical(self, "Hata", "Çek silinirken bir hata oluştu.")
            else:
                QtWidgets.QMessageBox.warning(self, "Uyarı", "Seçili satırda çek numarası bulunamadı.")
        else:
            QtWidgets.QMessageBox.warning(self, "Uyarı", "Silmek için bir çek seçiniz.")

    def clear_inputs(self):
        self.inputCekNo.clear()
        self.inputKesilmeTrh.setDate(QtCore.QDate.currentDate())
        self.inputVade.setDate(QtCore.QDate.currentDate())
        self.inputTutar.clear()
        self.inputAlici.clear()
        self.inputBanka.clear()
        self.resimYolu = ""
        self.labelResimYolu.setText("Resim Seçilmedi")
        
    def start_cek_timer(self):
        self.cek_timer = QtCore.QTimer(self)
        self.cek_timer.timeout.connect(self.check_cek_vade)
        self.cek_timer.start(60000)  # Her 1 dakikada bir kontrol et (60000 ms)

    def check_cek_vade(self):
        bugun = datetime.now().date()
        for i in range(self.table.rowCount()):
            vade_str = self.table.item(i, 2).text()  # Vade sütunu
            cek_no = self.table.item(i, 0).text()  # Çek No sütunu

            try:
                vade = datetime.strptime(vade_str, "%d-%m-%Y").date()
                kalan_gun = (vade - bugun).days
                durum_item = self.table.item(i, 7)  # Durum sütunu
                
                # 'cekler' listesindeki ilgili çekin 'uyarildi' durumunu bul ve güncelle
                cek_obj = next((c for c in self.cekler if c["cek_no"] == cek_no), None)

                if kalan_gun <= 0:
                    if durum_item.text() != "Vadesi Geçti":
                        durum_item.setText("Vadesi Geçti")
                        durum_item.setForeground(QtGui.QColor("red"))
                        if cek_obj and not cek_obj.get("uyarildi_vade_gecti", False):
                            self.send_email_notification("Vadesi Geçen Çek Uyarısı", f"Çek No: {cek_no}, Vade: {vade_str} - Vadesi geçti!")
                            cek_obj["uyarildi_vade_gecti"] = True  # Uyarıldı olarak işaretle
                            print(f"DEBUG: Çek {cek_no} için 'Vadesi Geçti' uyarısı gönderildi.")
                elif kalan_gun <= 3:
                    if durum_item.text() != f"{kalan_gun} Gün Kaldı":
                        durum_item.setText(f"{kalan_gun} Gün Kaldı")
                        durum_item.setForeground(QtGui.QColor("orange"))
                        if cek_obj and not cek_obj.get("uyarildi_kalan_gun", False):
                            self.send_email_notification("Yaklaşan Çek Vadesi Uyarısı", f"Çek No: {cek_no}, Vade: {vade_str} - Vadeye {kalan_gun} gün kaldı!")
                            cek_obj["uyarildi_kalan_gun"] = True  # Uyarıldı olarak işaretle
                            print(f"DEBUG: Çek {cek_no} için '{kalan_gun} Gün Kaldı' uyarısı gönderildi.")
                else:
                    if durum_item.text() != "Takipte":
                        durum_item.setText("Takipte")
                        durum_item.setForeground(QtGui.QColor("white"))
                        if cek_obj:
                            cek_obj["uyarildi_vade_gecti"] = False
                            cek_obj["uyarildi_kalan_gun"] = False
            except ValueError:
                print(f"DEBUG: Geçersiz tarih formatı: {vade_str} (Çek No: {cek_no})")
            except Exception as e:
                print(f"DEBUG: Çek vade kontrolü sırasında hata: {e}")

    def send_email_notification(self, subject, body):
        try:
            # Buradaki e-posta bilgileri ve şifre dinamik olarak alınmalı veya güvenli bir şekilde saklanmalıdır.
            # Örneğin, bir konfigürasyon dosyasından veya veritabanından çekilebilir.
            # Şimdilik örnek olarak sabit değerler kullanılmıştır.
            sender_email = "your_email@example.com"  # Kendi e-posta adresinizi girin
            sender_password = "your_email_password"  # Kendi e-posta şifrenizi girin (UYARI: Gerçek uygulamada güvenli yöntemler kullanılmalı)
            receiver_email = "recipient_email@example.com"  # Alıcı e-posta adresini girin

            if not all([sender_email, sender_password, receiver_email]):
                QtWidgets.QMessageBox.warning(self, "E-posta Hatası", "E-posta gönderici/alıcı bilgileri eksik veya şifre tanımlı değil.")
                return

            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = receiver_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP_SSL("smtp.example.com", 465)  # E-posta sağlayıcınıza göre değiştirin (örn: smtp.gmail.com)
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            server.quit()
            print("DEBUG: E-posta bildirimi başarıyla gönderildi.")
        except Exception as e:
            print(f"DEBUG: E-posta gönderilirken hata oluştu: {e}")
            QtWidgets.QMessageBox.critical(self, "E-posta Gönderme Hatası", f"E-posta gönderilirken hata oluştu: {e}")

    def proje_secildi(self, index):
        selected_project = self.comboBox_projeler.currentText()
        #@QtWidgets.QMessageBox.information(
        #    self, "Proje Seçimi", f"Seçilen Proje: {selected_project}"
        #)

    def proje_sil(self):
        selected_project = self.comboBox_projeler.currentText()
        if not selected_project:
            QtWidgets.QMessageBox.warning(self, "Uyarı", "Lütfen silmek istediğiniz bir proje seçin.")
            return
        
        if selected_project in ["Kayıtlı Proje Bulunamadı", "Hata Oluştu"]:
            QtWidgets.QMessageBox.information(self, "Bilgi", "Geçersiz bir proje seçimi yaptınız.")
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            "Proje Sil Onayı",
            f"'{selected_project}' projesini silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            try:
                # Proje adını tablo adına dönüştür (örneğin boşlukları alt çizgi ile değiştir)
                table_name = (
                    "proje_" + selected_project.lower()
                    .replace(" ", "_")
                    .replace("ş", "s").replace("ç", "c")
                    .replace("ı", "i").replace("ğ", "g")
                    .replace("ö", "o").replace("ü", "u")
                )
                
                # Veritabanından silme işlemi (eğer db varsa)
                if hasattr(self, 'db') and self.db is not None:
                    success = self.db.delete_project_table(table_name)
                    if not success:
                        raise Exception("Veritabanı silme işlemi başarısız oldu")
                
                # Combobox'tan kaldır
                current_index = self.comboBox_projeler.currentIndex()
                self.comboBox_projeler.removeItem(current_index)
                
                # Başarı mesajı
                QtWidgets.QMessageBox.information(
                    self,
                    "Başarılı",
                    f"'{selected_project}' projesi başarıyla silindi."
                )
                
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Hata",
                    f"Proje silinirken bir hata oluştu:\n{str(e)}"
                )


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    window = AnaPencere()  # ModernDashboard() yerine AnaPencere() olmalı
    window.show()
    sys.exit(app.exec())
