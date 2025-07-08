import sys
import sqlite3
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QMessageBox,
    QTableWidgetItem,
    QHeaderView,
    QLineEdit,
    QTableWidget,
    QFileDialog,
    QAbstractItemView,
)

from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt



try:
    import pandas as pd
except ImportError:
    QMessageBox.critical(
        None,
        "Kütüphane Hatası",
        "Pandas kütüphanesi yüklü değil. Lütfen 'pip install pandas openpyxl' komutunu çalıştırın.",
    )
    sys.exit(1)

from config import DB_FILE


from ui_poz_yonetimi import (
    Ui_PozYonetimiDialog as Ui_PozYonetimiDialog,
)  # <--- BU SATIRI EKLEYİN VE Sınıf adını kontrol edin


class PozYonetimDuzenleSilDialog(
    QDialog, Ui_PozYonetimiDialog
):  # <-- Ui_PozYonetimiPenceresi'ni buraya ekleyin
    def __init__(self, db_connection, db_cursor, parent=None):
        super().__init__(parent)
        self.conn = db_connection
        self.cursor = db_cursor

        # UI dosyasını yükle (Artık loadUi kullanmıyoruz)
        self.setupUi(self)  # <-- Bu satırı ekleyin

        self.setWindowTitle("Poz Yönetimi")  # Başlığı burada ayarlamak daha iyi

        self.is_editing = False

        self._setup_table()
        self._connect_signals()

        # İlk yüklemede tüm pozları tabloya çek
        self._load_all_pozlar_to_table_general()
        # Giriş alanlarını temizle ve salt okunur yap
        self._clear_input_fields()
        self._set_input_fields_read_only(True)

        # QDoubleValidator'ı Birim_Fiyat LineEdit'ine ekle
        self.double_validator = QDoubleValidator(0.00, 999999999.99, 2)
        self.double_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        # lineEdit_rayicBedeli'nin ui_poz_yonetimi.py dosyasında tanımlı olduğundan emin olun
        self.lineEdit_rayicBedeli.setValidator(self.double_validator)

    # Diğer metotlar olduğu gibi kalacak...
    # _setup_table, _connect_signals, _load_all_pozlar_to_table_general, vb.

    def _setup_table(self):
        # Tablo widget'ı ayarları
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setHorizontalHeaderLabels(
            ["ID", "Poz No", "Poz Açıklaması", "Ölçü Birimi", "Birim Fiyat"]
        )

        # Tablo hücrelerinin düzenlenebilirliğini ve seçim davranışını ayarla
        self.tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableWidget.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.tableWidget.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        # Kolonları yayma modu
        self.tableWidget.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        # ID sütununu gizle
        self.tableWidget.hideColumn(0)

        # Sütun başlıklarına tıklayarak sıralama
        self.tableWidget.setSortingEnabled(True)

    def _connect_signals(self):
        # Buton bağlantıları ve hata kontrolleri
        if hasattr(self, "pushButton_ekle"):
            self.pushButton_ekle.clicked.connect(self._add_poz)
        else:
            print("Uyarı: 'pushButton_ekle' butonu UI'da bulunamadı.")

        if hasattr(self, "pushButton_kaydet"):
            self.pushButton_kaydet.clicked.connect(self._save_poz)
        else:
            print("Uyarı: 'pushButton_kaydet' butonu UI'da bulunamadı.")

        if hasattr(self, "pushButton_duzenle"):
            self.pushButton_duzenle.clicked.connect(self._edit_selected_poz)
        else:
            print("Uyarı: 'pushButton_duzenle' butonu UI'da bulunamadı.")

        if hasattr(self, "pushButton_sil"):
            self.pushButton_sil.clicked.connect(self._delete_selected_poz)
        else:
            print("Uyarı: 'pushButton_sil' butonu UI'da bulunamadı.")

        if hasattr(self, "pushButton_temizle"):
            self.pushButton_temizle.clicked.connect(self._clear_input_fields)
        else:
            print("Uyarı: 'pushButton_temizle' butonu UI'da bulunamadı.")

        if hasattr(self, "pushButton_excel_import"):
            self.pushButton_excel_import.clicked.connect(self._import_from_excel)
        else:
            print("Uyarı: 'pushButton_excel_import' butonu UI'da bulunamadı.")

        if hasattr(self, "pushButton_kapat"):
            self.pushButton_kapat.clicked.connect(self.close)
        else:
            print("Uyarı: 'pushButton_kapat' butonu UI'da bulunamadı.")

        # Tablo seçim değişikliği sinyali
        if hasattr(self, "tableWidget"):
            self.tableWidget.itemSelectionChanged.connect(
                self._load_selected_poz_to_fields
            )
        else:
            print("Uyarı: 'tableWidget' UI'da bulunamadı.")

        # Poz No giriş alanı değişikliği sinyali
        if hasattr(self, "lineEdit_pozNo"):
            self.lineEdit_pozNo.textChanged.connect(self._check_poz_exists)
        else:
            print("Uyarı: 'lineEdit_pozNo' UI'da bulunamadı.")

        # Poz Açıklaması giriş alanı kontrolü
        if hasattr(self, "lineEdit_pozAciklamasi"):
            pass  # Bu alanın özel bir sinyal bağlantısı yok, sadece varlık kontrolü
        else:
            print("Uyarı: 'lineEdit_pozAciklamasi' UI'da bulunamadı.")

    def _check_poz_exists(self):
        """
        Poz numarası zaten mevcut mu diye kontrol eder.
        Kaydet butonu "Kaydet" modundayken uyarı verir.
        """
        Poz_No = self.lineEdit_pozNo.text().strip()

        if not Poz_No:
            if hasattr(self, "label_uyari"):
                self.label_uyari.setText("")
                self.label_uyari.setStyleSheet("")  # Stili temizle
            if hasattr(self, "pushButton_kaydet") and not self.is_editing:
                self.pushButton_kaydet.setEnabled(False)  # Boşken kaydetme
            return

        # Sadece "Kaydet" modundayken varlık kontrolü yap
        if self.pushButton_kaydet.text() == "Kaydet":
            self.cursor.execute(
                "SELECT COUNT(*) FROM pozlar WHERE Poz_No = ?", (Poz_No,)
            )
            count = self.cursor.fetchone()[0]

            if count > 0:
                if hasattr(self, "label_uyari"):
                    self.label_uyari.setText("Bu poz numarası zaten mevcut!")
                    self.label_uyari.setStyleSheet("color: red; font-weight: bold;")
                if hasattr(self, "pushButton_kaydet"):
                    self.pushButton_kaydet.setEnabled(
                        False
                    )  # Mevcutsa kaydetmeyi engelle
            else:
                if hasattr(self, "label_uyari"):
                    self.label_uyari.setText("Poz numarası uygun.")
                    self.label_uyari.setStyleSheet("color: green;")
                if hasattr(self, "pushButton_kaydet"):
                    self.pushButton_kaydet.setEnabled(
                        True
                    )  # Uygunsa kaydetmeyi etkinleştir
        elif self.pushButton_kaydet.text() == "Güncelle":

            if hasattr(self, "label_uyari"):
                self.label_uyari.setText("")
                self.label_uyari.setStyleSheet("")
            if hasattr(self, "pushButton_kaydet"):
                self.pushButton_kaydet.setEnabled(True)

    def _load_all_pozlar_to_table_general(self):
        """Genel olarak tüm pozları tabloya yükler."""
        self.tableWidget.setRowCount(0)
        try:
            self.cursor.execute(
                "SELECT id, Poz_No, Poz_Açıklaması, Ölçü_Birimi, Birim_Fiyat FROM pozlar ORDER BY Poz_No ASC"
            )
            rows = self.cursor.fetchall()

            poz_aciklamasi_sutun_indexi = 2 # "Poz Açıklaması" sütunu indeksi (0-indexed)

            for row_idx, row_data in enumerate(rows):
                self.tableWidget.insertRow(row_idx)
                for col_idx, data in enumerate(row_data):
                    # Sadece 'Birim_Fiyat' sütununu virgülle göster (col_idx 4)
                    # Diğer sütunları olduğu gibi bırak
                    if col_idx == 4:  # Birim_Fiyat sütunu (0-indexed)
                        item = QTableWidgetItem(str(data).replace(".", ","))
                    else:
                        item = QTableWidgetItem(str(data))

                    # "Poz Açıklaması" sütununu sola hizala, diğerlerini ortala
                    if col_idx == poz_aciklamasi_sutun_indexi:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    else:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    self.tableWidget.setItem(row_idx, col_idx, item)
            self.tableWidget.resizeColumnsToContents()
        except sqlite3.Error as e:
            QMessageBox.critical(
                self, "Veritabanı Hatası", f"Pozlar yüklenirken bir hata oluştu: {e}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Genel Hata",
                f"Pozlar yüklenirken beklenmeyen bir hata oluştu: {e}",
            )

    def _filter_table(self, text):
        """Tabloyu arama kutusundaki metne göre filtreler."""
        search_text = text.strip().lower()
        for row_idx in range(self.tableWidget.rowCount()):
            hidden = True
            for col_idx in range(self.tableWidget.columnCount()):
                item = self.tableWidget.item(row_idx, col_idx)
                if item and search_text in item.text().lower():
                    hidden = False
                    break
            self.tableWidget.setRowHidden(row_idx, hidden)

    def _add_poz(self):
        """Yeni poz ekleme modunu başlatır."""
        self._clear_input_fields()
        self._set_input_fields_read_only(False)
        self.lineEdit_pozNo.setReadOnly(False)
        self.pushButton_kaydet.setText("Kaydet")
        self.pushButton_kaydet.setEnabled(
            False
        )  # Poz No girilmeden kaydetme devre dışı
        self.lineEdit_pozNo.setFocus()
        self.is_editing = False  # Yeni poz ekleme modundayız

    def _save_poz(self):
        """Yeni poz ekler veya mevcut pozu günceller."""
        Poz_No = self.lineEdit_pozNo.text().strip()
        Poz_Açıklaması = self.lineEdit_pozAciklamasi.text().strip()
        Ölçü_Birimi = self.lineEdit_olcuBirimi.text().strip()
        Birim_Fiyat_str = self.lineEdit_rayicBedeli.text().strip()

        if not Poz_No or not Poz_Açıklaması or not Ölçü_Birimi or not Birim_Fiyat_str:
            QMessageBox.warning(
                self,
                "Eksik Bilgi",
                "Lütfen tüm zorunlu alanları doldurun: Poz No, Poz Açıklaması, Ölçü Birimi, Birim_Fiyat.",
            )
            return

        try:
            # Hem virgülü hem de noktayı ondalık ayırıcı olarak kabul et
            Birim_Fiyat = float(Birim_Fiyat_str.replace(",", "."))
        except ValueError:
            QMessageBox.warning(
                self, "Geçersiz Değer", "Birim_Fiyat geçerli bir sayı olmalıdır."
            )
            return

        self.conn.execute("BEGIN TRANSACTION")  # İşlemi başlat

        try:
            if self.pushButton_kaydet.text() == "Kaydet":
                self.cursor.execute(
                    "SELECT COUNT(*) FROM pozlar WHERE Poz_No = ?", (Poz_No,)
                )
                if self.cursor.fetchone()[0] > 0:
                    QMessageBox.warning(
                        self, "Kayıt Mevcut", "Bu poz numarası zaten mevcut."
                    )
                    self.conn.rollback()  # İşlemi geri al
                    return

                self.cursor.execute(
                    """
                    INSERT INTO pozlar (Poz_No, Poz_Açıklaması, Ölçü_Birimi, Birim_Fiyat)
                    VALUES (?, ?, ?, ?)
                """,
                    (Poz_No, Poz_Açıklaması, Ölçü_Birimi, Birim_Fiyat),
                )
                QMessageBox.information(self, "Başarılı", "Poz başarıyla eklendi.")
            else:  # Güncelleme modu
                selected_items = self.tableWidget.selectedItems()
                if not selected_items:
                    QMessageBox.warning(
                        self, "Seçim Yok", "Lütfen düzenlenecek bir poz seçin."
                    )
                    self.conn.rollback()  # İşlemi geri al
                    return
                poz_id = int(self.tableWidget.item(selected_items[0].row(), 0).text())

                self.cursor.execute(
                    """
                    UPDATE pozlar SET Poz_No = ?, Poz_Açıklaması = ?, Ölçü_Birimi = ?, Birim_Fiyat = ?
                    WHERE id = ?
                """,
                    (Poz_No, Poz_Açıklaması, Ölçü_Birimi, Birim_Fiyat, poz_id),
                )
                QMessageBox.information(self, "Başarılı", "Poz başarıyla güncellendi.")

            self.conn.commit()  # İşlemi onayla
            self._load_all_pozlar_to_table_general()
            self._clear_input_fields()
            self._set_input_fields_read_only(True)
            self.pushButton_kaydet.setText("Kaydet")
            self.lineEdit_pozNo.setReadOnly(True)
            self.pushButton_kaydet.setEnabled(
                True
            )  # Kaydet butonu default olarak etkin olsun (yeni ekleme moduna geçince tekrar devre dışı kalacak)
            self.is_editing = False  # Güncelleme modundan çıktık

        except sqlite3.IntegrityError as e:
            QMessageBox.warning(
                self,
                "Kayıt Mevcut",
                f"Bu poz numarası zaten mevcut. Lütfen farklı bir poz numarası girin. Hata: {e}",
            )
            self.conn.rollback()  # İşlemi geri al
        except sqlite3.Error as e:
            QMessageBox.critical(
                self,
                "Veritabanı Hatası",
                f"Poz kaydedilirken/güncellenirken bir hata oluştu: {e}",
            )
            self.conn.rollback()  # İşlemi geri al
        except Exception as e:
            QMessageBox.critical(
                self, "Genel Hata", f"Beklenmeyen bir hata oluştu: {e}"
            )
            self.conn.rollback()  # İşlemi geri al

    def _edit_selected_poz(self):
        """Seçilen pozu düzenleme moduna alır."""
        selected_items = self.tableWidget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Seçim Yok", "Lütfen düzenlenecek bir poz seçin.")
           
            
            return

        self._set_input_fields_read_only(False)
        self.pushButton_kaydet.setText("Güncelle")
        self.lineEdit_pozNo.setReadOnly(
            True
        )  # Poz numarası düzenleme modunda değiştirilemez
        self.pushButton_kaydet.setEnabled(True)  # Güncelleme modunda butonu etkinleştir
        self.is_editing = True  # Düzenleme modundayız
        self._load_selected_poz_to_fields()  # Seçilen pozu alanlara yükle (bu çağrı is_editing True iken readonly yapmayacak)
        if hasattr(self, "label_uyari"):
            self.label_uyari.setText("")  # Uyarı mesajını temizle
            self.label_uyari.setStyleSheet("")

    def _delete_selected_poz(self):
        """Seçilen pozu veritabanından siler."""
        selected_items = self.tableWidget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Seçim Yok", "Lütfen silinecek bir poz seçin.")
            return

        row_idx = selected_items[0].row()
        poz_id = int(self.tableWidget.item(row_idx, 0).text())
        Poz_No = self.tableWidget.item(row_idx, 1).text()

        reply = QMessageBox.question(
            self,
            "Pozu Sil",
            f"'{Poz_No}' pozunu silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.",
            QMessageBox.StandardButton.Yes | QMessageBox.QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.cursor.execute("DELETE FROM pozlar WHERE id = ?", (poz_id,))
                self.conn.commit()
                QMessageBox.information(self, "Başarılı", "Poz başarıyla silindi.")
                self._load_all_pozlar_to_table_general()
                self._clear_input_fields()
                self._set_input_fields_read_only(True)
                self.pushButton_kaydet.setText("Kaydet")
                self.lineEdit_pozNo.setReadOnly(True)
                self.pushButton_kaydet.setEnabled(True)  # Default olarak etkinleştir
                self.is_editing = False
            except sqlite3.Error as e:
                QMessageBox.critical(
                    self, "Veritabanı Hatası", f"Poz silinirken bir hata oluştu: {e}"
                )
                self.conn.rollback()

    def _clear_input_fields(self):
        """Giriş alanlarını temizler."""
        self.lineEdit_pozNo.clear()
        self.lineEdit_pozAciklamasi.clear()
        self.lineEdit_olcuBirimi.clear()
        self.lineEdit_rayicBedeli.clear()
        if hasattr(self, "label_uyari"):
            self.label_uyari.setText("")  # Uyarı mesajını da temizle
            self.label_uyari.setStyleSheet("")

    def _set_input_fields_read_only(self, read_only):
        """Giriş alanlarının salt okunur durumunu ayarlar."""
        # self.lineEdit_pozNo.setReadOnly(read_only) # Bu, _edit_selected_poz ve _add_poz tarafından yönetiliyor
        self.lineEdit_pozAciklamasi.setReadOnly(read_only)
        self.lineEdit_olcuBirimi.setReadOnly(read_only)
        self.lineEdit_rayicBedeli.setReadOnly(read_only)

    def _load_selected_poz_to_fields(self):
        """Seçilen pozu giriş alanlarına yükler."""
        selected_items = self.tableWidget.selectedItems()
        if selected_items:
            row_idx = selected_items[0].row()
            self.lineEdit_pozNo.setText(self.tableWidget.item(row_idx, 1).text())
            self.lineEdit_olcuBirimi.setText(self.tableWidget.item(row_idx, 3).text())
            self.lineEdit_pozAciklamasi.setText(
                self.tableWidget.item(row_idx, 2).text()
            )
            # Birim_Fiyat'ni virgülden noktaya çevirerek yükle, validator ile uyumlu olsun
            Birim_Fiyat_text = (
                self.tableWidget.item(row_idx, 4).text().replace(",", ".")
            )
            self.lineEdit_rayicBedeli.setText(Birim_Fiyat_text)

            # alanları salt okunur yapmamalıyız.
            if not self.is_editing:
                self._set_input_fields_read_only(True)
                self.lineEdit_pozNo.setReadOnly(True)  # Poz No da salt okunur olsun
                self.pushButton_kaydet.setText(
                    "Kaydet"
                )  # Seçili poz yüklendiğinde Kaydet moduna dön
                self.pushButton_kaydet.setEnabled(
                    True
                )  # Kaydet butonu aktif olsun (yeni ekleme için)
                if hasattr(self, "label_uyari"):
                    self.label_uyari.setText("")  # Uyarı mesajını temizle
                    self.label_uyari.setStyleSheet("")
        else:
            # Seçili öğe yoksa alanları temizle ve salt okunur yap
            self._clear_input_fields()
            self._set_input_fields_read_only(True)
            self.lineEdit_pozNo.setReadOnly(True)
            self.pushButton_kaydet.setText("Kaydet")
            self.pushButton_kaydet.setEnabled(True)
            if hasattr(self, "label_uyari"):
                self.label_uyari.setText("")
                self.label_uyari.setStyleSheet("")

    def _import_from_excel(self):
        """Excel dosyasından pozları içe aktarır."""
        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName(
            self, "Excel Dosyası Seç", "", "Excel Files (*.xlsx *.xls)"
        )

        if file_path:
            try:
                df = pd.read_excel(file_path)

                required_columns = [
                    "Poz No",
                    "Poz Açıklaması",
                    "Ölçü Birimi",
                    "Birim Fiyat",
                ]

                if not all(col in df.columns for col in required_columns):
                    QMessageBox.warning(
                        self,
                        "Hata",
                        "Excel dosyasında gerekli sütunlar bulunamadı. "
                        "Gerekli sütunlar: 'Poz No', 'Poz Açıklaması', 'Ölçü Birimi', 'Birim Fiyat'",
                    )
                    return

                imported_count = 0
                updated_count = 0
                skip_count = 0
                skipped_rows_log = []  # Atlanan satırlar için detaylı log

                # Toplu işlemler için veri listeleri
                insert_data = []
                update_data = []

                self.conn.execute("BEGIN TRANSACTION")  # İşlemi başlat

                for index, row in df.iterrows():
                    Poz_No = str(row["Poz No"]).strip()
                    Poz_Açıklaması = str(row["Poz Açıklaması"]).strip()
                    Ölçü_Birimi = str(row["Ölçü Birimi"]).strip()

                    Birim_Fiyat_raw = row["Birim Fiyat"]

                    Birim_Fiyat = 0.0  # Varsayılan değer

                    if pd.isna(Birim_Fiyat_raw) or str(Birim_Fiyat_raw).strip() == "":
                        # Boş veya NaN ise varsayılan bir değer atayabiliriz (örneğin 0.0)
                        Birim_Fiyat = 0.0
                    else:
                        try:
                            Birim_Fiyat = float(
                                str(Birim_Fiyat_raw).replace(",", ".").strip()
                            )
                        except ValueError:
                            skipped_rows_log.append(
                                f"Satır {index + 2}: 'Birim_Fiyat' geçerli bir sayı değil ('{Birim_Fiyat_raw}'). Atlandı."
                            )
                            skip_count += 1
                            continue  # Bu satırı atla

                    if not Poz_No or not Poz_Açıklaması or not Ölçü_Birimi:
                        skipped_rows_log.append(
                            f"Satır {index + 2}: Zorunlu alanlar (Poz No, Poz Açıklaması, Ölçü Birimi) boş. Atlandı."
                        )
                        skip_count += 1
                        continue

                    self.cursor.execute(
                        "SELECT id FROM pozlar WHERE Poz_No = ?", (Poz_No,)
                    )
                    existing_poz = self.cursor.fetchone()

                    if existing_poz:
                        update_data.append(
                            (Poz_Açıklaması, Ölçü_Birimi, Birim_Fiyat, existing_poz[0])
                        )
                        updated_count += 1
                    else:
                        insert_data.append(
                            (Poz_No, Poz_Açıklaması, Ölçü_Birimi, Birim_Fiyat)
                        )
                        imported_count += 1

                # Toplu ekleme ve güncelleme
                if insert_data:
                    self.cursor.executemany(
                        """
                        INSERT INTO pozlar (Poz_No, Poz_Açıklaması, Ölçü_Birimi, Birim_Fiyat)
                        VALUES (?, ?, ?, ?)
                    """,
                        insert_data,
                    )

                if update_data:
                    self.cursor.executemany(
                        """
                        UPDATE pozlar SET Poz_Açıklaması = ?, Ölçü_Birimi = ?, Birim_Fiyat = ?
                        WHERE id = ?
                    """,
                        update_data,
                    )

                self.conn.commit()  # İşlemi onayla

                summary_message = (
                    f"{imported_count} yeni poz eklendi, "
                    f"{updated_count} poz güncellendi, "
                    f"{skip_count} satır atlandı."
                )
                if skipped_rows_log:
                    summary_message += "\n\nAtlanan satır detayları:\n" + "\n".join(
                        skipped_rows_log
                    )
                    QMessageBox.warning(
                        self, "İçe Aktarma Tamamlandı (Uyarılarla)", summary_message
                    )
                else:
                    QMessageBox.information(
                        self, "İçe Aktarma Tamamlandı", summary_message
                    )

                self._load_all_pozlar_to_table_general()  # Tabloyu yenile

            except pd.errors.EmptyDataError:
                QMessageBox.warning(self, "Hata", "Seçilen Excel dosyası boş.")
                self.conn.rollback()
            except pd.errors.ParserError as e:
                QMessageBox.critical(
                    self,
                    "Hata",
                    f"Excel dosyasını ayrıştırma hatası: {e}\nDosyanın bozuk olmadığından veya doğru formatta olduğundan emin olun.",
                )
                self.conn.rollback()
            except sqlite3.Error as e:
                QMessageBox.critical(
                    self,
                    "Veritabanı Hatası",
                    f"Pozlar veritabanına kaydedilirken bir hata oluştu: {e}",
                )
                self.conn.rollback()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Genel Hata",
                    f"Excel dosyasını okurken veya işlerken beklenmeyen bir hata oluştu: {e}",
                )
                self.conn.rollback()