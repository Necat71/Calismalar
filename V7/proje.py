from frozen_table_module import FrozenTableWidget, FrozenTableModel

from poz_ekleme_module import add_poz_from_lineEdit
from excel_export_module import _generate_excel_output
import sys
import sqlite3
from PyQt6.QtWidgets import (
    QDialog,
    QMessageBox,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QApplication,
    QAbstractItemView,
    QMenu,
    QTabWidget,
)
from PyQt6.QtGui import QAction

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence
from config import DB_FILE

import re
import datetime
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
import os
from ui_proje import Ui_ProjeDialog


class ProjeYonetimDialog(QDialog, Ui_ProjeDialog):

    def __init__(self, db_instance, parent=None):
        super().__init__(parent)
        self.db = db_instance
        self.parent_window = parent
        self.project_table_name = None
        self.original_poz_data = {}
        self.arsiv_data_for_rows = {}

        try:
            self.setupUi(self)
        except Exception as e:
            QMessageBox.critical(
                self,
                "UI Kurulum Hatası",
                f"UI bileşenleri kurulurken bir hata oluştu: {e}",
            )
            sys.exit(1)

        if not hasattr(self, "tableWidget"):
            QMessageBox.critical(
                self, "UI Hatası", "UI tasarımında 'tableWidget' bulunamadı."
            )
            sys.exit(1)

        parent_layout = self.tableWidget.parentWidget().layout()
        if not parent_layout:
            QMessageBox.critical(
                self, "UI Hatası", "tableWidget'ın bir üst düzeni (layout) yok."
            )
            sys.exit(1)

        self.frozen_column_count = 4

        self.frozen_wrapper_widget = FrozenTableWidget(
            self.tableWidget, self.frozen_column_count, self
        )

        old_index = parent_layout.indexOf(self.tableWidget)
        if old_index != -1:
            parent_layout.removeWidget(self.tableWidget)
            parent_layout.insertWidget(old_index, self.frozen_wrapper_widget)
        else:
            parent_layout.addWidget(self.frozen_wrapper_widget)

        self._setup_table()
        self._enable_keyboard_navigation()
        self._connect_signals()
        self._update_total_cost_difference()

        self.frozen_wrapper_widget.frozen_view.setModel(
            FrozenTableModel(self.tableWidget.model(),
                             self.frozen_column_count, self)
        )

        self.frozen_wrapper_widget.frozen_view.verticalHeader().hide()

        self.tableWidget.verticalHeader().sectionResized.connect(
            lambda logicalIndex, oldSize, newSize: self.frozen_wrapper_widget.frozen_view.setRowHeight(
                logicalIndex, newSize
            )
        )
        for i in range(self.tableWidget.rowCount()):
            self.frozen_wrapper_widget.frozen_view.setRowHeight(
                i, self.tableWidget.rowHeight(i)
            )

        self.frozen_wrapper_widget.adjust_frozen_column_widths()

        self._update_total_Birim_Fiyat()
        self._update_total_Teklif_Maliyeti()

    def _setup_table(self):
        """TableWidget'ın başlangıç ayarlarını yapar."""
        headers = [
            "Poz No",
            "Poz Açıklaması",
            "Ölçü Birimi",
            "Birim Fiyat",
            "Kullanıldığı Proje",
            "Kullanıldığı Tarih",
            "Tedarikçi",
            "Alış Fiyatı",
            "Yeni Proje Adı",
            "Yeni Proje Tarihi",
            "Yeni Tedarikçi",
            "Metraj",
            "Yaklaşık İşçilik",
            "Yaklaşık Maliyet",
            "Teklif Fiyat",
            "Teklif İşçilik",
            "Teklif Maliyet",
            "Gerçek Fiyat",
            "Gerçek İşçilik",
            "Gerçek Maliyet",
        ]
        self.tableWidget.setColumnCount(len(headers))
        self.tableWidget.setHorizontalHeaderLabels(headers)

        ui_column_widths = [
            100,
            250,
            95,
            95,
            200,
            120,
            200,
            110,
            250,
            120,
            120,
            110,
            110,
            120,
            110,
            110,
            110,
            110,
            110,
            110,
        ]

        for col, width in enumerate(ui_column_widths):
            self.tableWidget.setColumnWidth(col, width)

        # Yeni Proje Adı sütununu gizle (indeks 8)
        self.tableWidget.hideColumn(8)
        self.tableWidget.hideColumn(9)
        self.tableWidget.hideColumn(4)
        self.editable_columns = {
            "Yeni Proje Adı": 8,
            "Yeni Proje Tarihi": 9,
            "Yeni Tedarikçi": 10,
            "Metraj": 11,
            "Yaklaşık İşçilik": 12,
            "Teklif Fiyat": 14,
            "Teklif İşçilik": 15,
            "Gerçek Fiyat": 17,
            "Gerçek İşçilik": 18,
        }

        self.numeric_columns_indexes = [
            11,
            12,
            14,
            15,
            17,
            18,
        ]

        self.non_editable_calculated_columns = [
            13,
            16,
            19,
        ]

        self.pasteable_columns = list(self.editable_columns.values())

    def _connect_signals(self):
        """UI elementlerinin sinyallerini slotlara bağlar."""
        if hasattr(self, "pushButton_kaydet"):
            self.pushButton_kaydet.clicked.connect(self._kaydet)
        else:
            print("Uyarı: 'pushButton_kaydet' butonu bulunamadı.")

        if hasattr(self, "tableWidget"):
            self.tableWidget.itemChanged.connect(self._on_item_changed)
            self.tableWidget.setContextMenuPolicy(
                Qt.ContextMenuPolicy.CustomContextMenu
            )
            self.tableWidget.customContextMenuRequested.connect(
                self._show_context_menu)

        if hasattr(self, "pushButton_arsivle"):
            self.pushButton_arsivle.clicked.connect(self._arsivle_proje)
        else:
            print("Uyarı: 'pushButton_arsivle' butonu bulunamadı.")

        if hasattr(self, "pushButton_kapat"):
            self.pushButton_kapat.clicked.connect(self.close)
        else:
            print("Uyarı: 'pushButton_kapat' butonu bulunamadı.")

        if hasattr(self, "lineEdit_projeadi"):
            self.lineEdit_projeadi.textChanged.connect(
                self._update_project_names_in_table
            )
        else:
            print("Uyarı: 'lineEdit_projeadi' bulunamadı.")

        if hasattr(self, "pushButton_teklif_olustur"):
            self.pushButton_teklif_olustur.clicked.connect(
                lambda: _generate_excel_output(
                    dialog_instance=self,
                    project_name=(
                        self.lineEdit_projeadi.text()
                        if hasattr(self, "lineEdit_projeadi")
                        else ""
                    ),
                )
            )
        else:
            print("Uyarı: 'pushButton_teklif_olustur' butonu bulunamadı.")

        if hasattr(self, "pushButton_ilave"):
            self.pushButton_ilave.clicked.connect(
                lambda: add_poz_from_lineEdit(self))
        else:
            print("Uyarı: 'pushButton_ilave' butonu bulunamadı.")

        # proje.py dosyasında, _connect_signals metodu içinde
        if hasattr(self, "pushButton_ihale_alindi"):
            self.pushButton_ihale_alindi.clicked.connect(
                self._on_ihale_alindi_clicked)
        else:
            print("Uyarı: 'pushButton_ihale_alindi' butonu bulunamadı.")

    def set_project_table_name(self, name):
        """Diyalogun hangi proje tablosuyla çalışacağını ayarlar ve lineEdit_projeadi'yi günceller."""
        self.project_table_name = name
        if hasattr(self, "lineEdit_projeadi"):
            # "proje_" ön eki kaldırılır
            clean_name = name.replace("proje_", "")
            # "_YYYYAA" desenini arar
            match = re.search(r"(_\d{6})$", clean_name)
            if match:
                # \YYYYAA kısmı ayrılır
                clean_name = clean_name[: match.start()]
                if hasattr(self, "lineEdit_projeayi"):
                    self.lineEdit_projeayi.setText(
                        match.group(1).replace("_", "")
                    )  # Ay/Yıl bilgisi lineEdit_projeayi'ye set edilir
            self.lineEdit_projeadi.setText(
                clean_name.replace("_", " ").title()
            )  # Temizlenmiş proje adı lineEdit_projeadi'ye set edilir

    def load_project_data(self, table_name):
        """Belirtilen proje tablosundan verileri yükler ve tableWidget'a doldurur."""
        try:
            self.db.cursor.execute(f"SELECT * FROM {table_name}")
            rows = self.db.cursor.fetchall()

            if not rows:
                QMessageBox.information(
                    self,
                    "Bilgi",
                    f"'{table_name}' tablosunda yüklenecek veri bulunamadı.",
                )
                self.tableWidget.setRowCount(0)
                self._update_total_cost_difference()

                # Etiketlerin başlangıç durumlarını ayarla
                if hasattr(self, "label_rayic_toplam"):
                    self.label_rayic_toplam.setText(
                        "Yaklaşık Maliyet Toplamı: 0.00 TL")
                if hasattr(self, "label_Teklif_Maliyeti"):
                    self.label_Teklif_Maliyeti.setText(
                        "Teklif Maliyeti Toplamı: 0.00 TL"
                    )
                if hasattr(self, "label_gercek_maliyet_toplam"):  # Yeni etiket için
                    self.label_gercek_maliyet_toplam.setText(
                        "Gerçek Maliyet Toplamı: 0.00 TL"
                    )
                if hasattr(self, "label_fark_yaklasik_teklif"):
                    self.label_fark_yaklasik_teklif.setText(
                        "Yaklaşık - Teklif Maliyet Farkı: 0.00 TL (Kırım Oranı: %0.00)"
                    )
                if hasattr(self, "label_fark_teklif_gercek"):
                    self.label_fark_teklif_gercek.setText(
                        "Teklif - Gerçek Maliyet Farkı: 0.00 TL (Fark Oranı: %0.00)"
                    )
                return

            self.tableWidget.setRowCount(0)
            self.original_poz_data = {}
            self.arsiv_data_for_rows = {}

            self.tableWidget.blockSignals(True)
            self.db.cursor.execute(f"PRAGMA table_info({table_name});")
            cols_info = self.db.cursor.fetchall()
            db_column_names = [col[1] for col in cols_info]

            col_map = {
                "Poz_No": 0,
                "Poz_Açıklaması": 1,
                "Ölçü_Birimi": 2,
                "Birim_Fiyat": 3,
                "Kullanıldığı_Proje": 4,
                "Kullanıldığı_Tarih": 5,
                "Tedarikçi": 6,
                "Alış_Fiyatı": 7,
                "Yeni_Proje_Adı": 8,
                "Yeni_Proje_Tarihi": 9,
                "Yeni_Tedarikçi": 10,
                "Metraj": 11,
                "Yaklaşık_İşçilik": 12,
                "Yaklaşık_Maliyet": 13,
                "Teklif_Fiyat": 14,
                "Teklif_İşçilik": 15,
                "Teklif_Maliyet": 16,
                "Gerçek_Fiyat": 17,
                "Gerçek_İşçilik": 18,
                "Gerçek_Maliyet": 19,
            }

            for row_idx, row_data in enumerate(rows):
                self.tableWidget.insertRow(row_idx)

                self.original_poz_data[row_idx] = {
                    "no": row_data[db_column_names.index("Poz_No")],
                    "tanim": row_data[db_column_names.index("Poz_Açıklaması")],
                    "birim": row_data[db_column_names.index("Ölçü_Birimi")],
                    "bedel": row_data[db_column_names.index("Birim_Fiyat")],
                }
                self.arsiv_data_for_rows[row_idx] = {
                    "Kullanıldığı_Proje": row_data[
                        db_column_names.index("Kullanıldığı_Proje")
                    ],
                    "Kullanıldığı_Tarih": row_data[
                        db_column_names.index("Kullanıldığı_Tarih")
                    ],
                    "Tedarikçi": row_data[db_column_names.index("Tedarikçi")],
                    "Alış_Fiyatı": row_data[db_column_names.index("Alış_Fiyatı")],
                }

                for db_col_name, ui_col_idx in col_map.items():
                    try:
                        db_col_idx = db_column_names.index(db_col_name)
                        value = row_data[db_col_idx]

                        if isinstance(value, (int, float)):
                            item = QTableWidgetItem(
                                self._format_number_for_display(value)
                            )
                        else:
                            item = QTableWidgetItem(str(value))

                        if (
                            ui_col_idx not in self.editable_columns.values()
                            or ui_col_idx in self.non_editable_calculated_columns
                        ):
                            item.setFlags(item.flags() & ~
                                          Qt.ItemFlag.ItemIsEditable)

                        self.tableWidget.setItem(row_idx, ui_col_idx, item)
                    except ValueError:
                        item = QTableWidgetItem("")
                        if (
                            ui_col_idx not in self.editable_columns.values()
                            or ui_col_idx in self.non_editable_calculated_columns
                        ):
                            item.setFlags(item.flags() & ~
                                          Qt.ItemFlag.ItemIsEditable)
                        self.tableWidget.setItem(row_idx, ui_col_idx, item)
                    except KeyError:
                        item = QTableWidgetItem("")
                        if (
                            ui_col_idx not in self.editable_columns.values()
                            or ui_col_idx in self.non_editable_calculated_columns
                        ):
                            item.setFlags(item.flags() & ~
                                          Qt.ItemFlag.ItemIsEditable)
                        self.tableWidget.setItem(row_idx, ui_col_idx, item)

            self.tableWidget.blockSignals(False)

            # !!! YENİ EKLEME: Tablo yüklendikten sonra her satır için hesaplamaları güncelle !!!
            for row_idx in range(self.tableWidget.rowCount()):
                self._update_calculations(row_idx)
            # !!! YENİ EKLEME BİTTİ !!!

            self._update_total_cost_difference()
            self._update_total_Birim_Fiyat()
            self._update_total_Teklif_Maliyeti()

        except sqlite3.Error as e:
            QMessageBox.critical(
                self,
                "Veritabanı Hatası",
                f"Proje verileri yüklenirken hata oluştu: {e}",
            )
            self.tableWidget.blockSignals(False)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Genel Hata",
                f"Proje yüklenirken beklenmeyen bir hata oluştu: {e}",
            )
            self.tableWidget.blockSignals(False)

    def poz_ekle(self, poz_object, data_to_add, arsiv_info):
        """
        Seçilen pozları Proje Yönetimi tablosuna ekler.
        """
        row_position = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row_position)

        self.original_poz_data[row_position] = poz_object
        self.arsiv_data_for_rows[row_position] = arsiv_info

        self.tableWidget.blockSignals(True)

        full_data_to_add = list(data_to_add)

        while len(full_data_to_add) < 20:
            full_data_to_add.append("")

        formatted_data_to_add = []
        for col, data in enumerate(full_data_to_add):
            if col in [3, 7, 11, 12, 14, 15, 17, 18]:
                value = self._get_float_value_from_string(str(data))
                formatted_data_to_add.append(
                    self._format_number_for_display(value))
            elif col in self.non_editable_calculated_columns:
                formatted_data_to_add.append("")
            else:
                formatted_data_to_add.append(str(data))

        for col, data in enumerate(formatted_data_to_add):
            item = QTableWidgetItem(str(data))

            if (
                col not in self.editable_columns.values()
                or col in self.non_editable_calculated_columns
            ):
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            self.tableWidget.setItem(row_position, col, item)

        Yeni_Proje_Tarihi_col_idx = self.editable_columns.get(
            "Yeni Proje Tarihi")
        if Yeni_Proje_Tarihi_col_idx is not None:
            date_item = self.tableWidget.item(
                row_position, Yeni_Proje_Tarihi_col_idx)
            if date_item is None:
                date_item = QTableWidgetItem()
                self.tableWidget.setItem(
                    row_position, Yeni_Proje_Tarihi_col_idx, date_item
                )
            date_item.setText(datetime.date.today().strftime("%d-%m-%Y"))

        proje_adi_col_idx = self.editable_columns.get("Yeni Proje Adı")
        if proje_adi_col_idx is not None and hasattr(self, "lineEdit_projeadi"):
            project_name = self.lineEdit_projeadi.text()
            if project_name:
                item = self.tableWidget.item(row_position, proje_adi_col_idx)
                if item is None:
                    item = QTableWidgetItem()
                    self.tableWidget.setItem(
                        row_position, proje_adi_col_idx, item)
                item.setText(project_name)

        self.tableWidget.blockSignals(False)

        self._update_calculations(row_position)
        self._update_total_cost_difference()
        self._update_total_Birim_Fiyat()
        self._update_total_Teklif_Maliyeti()

    def _on_item_changed(self, item):
        """Tablodaki bir hücre değeri değiştiğinde hesaplamaları günceller."""
        row = item.row()
        col = item.column()

        if col in self.non_editable_calculated_columns:
            return

        self.tableWidget.blockSignals(True)

        if col in self.numeric_columns_indexes:
            value = self._get_float_value(item)
            item.setText(self._format_number_for_display(value))
            self._update_calculations(row)

            if col == 3:
                self._update_total_Birim_Fiyat()
            elif col == self.editable_columns.get("Teklif Fiyat"):
                self._update_total_Teklif_Maliyeti()

        elif col == self.editable_columns["Yeni Proje Tarihi"]:
            date_text = item.text().strip()
            try:
                datetime.datetime.strptime(date_text, "%d-%m-%Y")
            except ValueError:
                item.setText(datetime.date.today().strftime("%d-%m-%Y"))

        self.tableWidget.blockSignals(False)
        self._update_total_cost_difference()

    def _update_calculations(self, row):
        """Belirtilen satırdaki hesaplanan sütunları günceller."""
        self.tableWidget.blockSignals(True)

        poz_no_item = self.tableWidget.item(row, 0)
        poz_no = poz_no_item.text() if poz_no_item else "GEÇİCİ_POZ"

        Birim_Fiyat_item = self.tableWidget.item(row, 3)
        Metraj_item = self.tableWidget.item(
            row, self.editable_columns["Metraj"])

        Yaklasik_Iscilik_item = self.tableWidget.item(
            row, self.editable_columns["Yaklaşık İşçilik"]
        )
        Teklif_Fiyat_item = self.tableWidget.item(
            row, self.editable_columns["Teklif Fiyat"]
        )
        Teklif_İşçilik_item = self.tableWidget.item(
            row, self.editable_columns["Teklif İşçilik"]
        )
        Gerçek_Fiyat_item = self.tableWidget.item(
            row, self.editable_columns["Gerçek Fiyat"]
        )
        Gerçek_İşçilik_item = self.tableWidget.item(
            row, self.editable_columns["Gerçek İşçilik"]
        )

        birim_fiyat = self._get_float_value(Birim_Fiyat_item)
        metraj = self._get_float_value(Metraj_item)
        yaklasik_iscilik = self._get_float_value(Yaklasik_Iscilik_item)
        teklif_fiyat = self._get_float_value(Teklif_Fiyat_item)
        teklif_işçilik = self._get_float_value(Teklif_İşçilik_item)
        gercek_fiyat = self._get_float_value(Gerçek_Fiyat_item)
        gercek_işçilik = self._get_float_value(Gerçek_İşçilik_item)

        yaklasik_maliyet = (birim_fiyat * metraj) + yaklasik_iscilik
        teklif_maliyeti = (teklif_fiyat * metraj) + teklif_işçilik
        gercek_maliyet = (gercek_fiyat * metraj) + gercek_işçilik

        # Bu iki değer sadece anlık satır bazında hesaplandığı için burada kullanılmıyor
        # yaklasik_teklif_maliyeti_fark = yaklasik_maliyet - teklif_maliyeti
        # teklif_gercek_maliyet_fark = teklif_maliyeti - gercek_maliyet

        item_yaklasik_maliyet = self.tableWidget.item(row, 13)
        if item_yaklasik_maliyet is None:
            item_yaklasik_maliyet = QTableWidgetItem()
            self.tableWidget.setItem(row, 13, item_yaklasik_maliyet)
        item_yaklasik_maliyet.setText(
            self._format_number_for_display(yaklasik_maliyet))

        item_teklif_maliyeti = self.tableWidget.item(row, 16)
        if item_teklif_maliyeti is None:
            item_teklif_maliyeti = QTableWidgetItem()
            self.tableWidget.setItem(row, 16, item_teklif_maliyeti)
        item_teklif_maliyeti.setText(
            self._format_number_for_display(teklif_maliyeti))

        item_gercek_maliyet = self.tableWidget.item(row, 19)
        if item_gercek_maliyet is None:
            item_gercek_maliyet = QTableWidgetItem()
            self.tableWidget.setItem(row, 19, item_gercek_maliyet)
        item_gercek_maliyet.setText(
            self._format_number_for_display(gercek_maliyet))

        self.tableWidget.blockSignals(False)

        # Bu kısımlar, toplamlar güncellendiği için burada tekrarlı değil,
        # ancak eğer sadece tek bir satır değiştiğinde genel toplamın anında güncellenmesi isteniyorsa kalabilir.
        # En verimlisi _update_total_cost_difference'ın sonunda çağrılmasıdır.
        self._update_total_cost_difference()
        self._update_total_Birim_Fiyat()
        self._update_total_Teklif_Maliyeti()

    def _get_float_value(self, item):
        """QTableWidgetItem'dan float değeri güvenli bir şekilde alır."""
        if item is None or not item.text():
            return 0.0
        return self._get_float_value_from_string(item.text())

    def _get_float_value_from_string(self, text_value):
        """String'den float değeri güvenli bir şekilde alır."""
        try:
            text = text_value.replace(".", "").replace(",", ".") # Hem binlik ayırıcı noktayı, hem de ondalık virgülü düzelt
            return float(text)
        except ValueError:
            return 0.0

    def _format_number_for_display(self, value):
        """Sayıyı binlik ayırıcılarla ve iki ondalık basamakla biçimlendirir."""
        # Sayıyı önce iki ondalık basamakla biçimlendir (nokta ile)
        formatted_value = f"{value:,.2f}"

        # formatted_with_commas = f"{value:,.2f}" # Bu satır gereksiz

        integer_part, decimal_part = f"{value:.2f}".split('.')

        # Tam kısmı binlik ayırıcılarla formatla
        new_integer_part = []
        n = len(integer_part)
        for i, digit in enumerate(integer_part):
            new_integer_part.append(digit)
            if (n - 1 - i) % 3 == 0 and (n - 1 - i) != 0:
                new_integer_part.append('.')

        return "".join(new_integer_part) + "," + decimal_part

    def _clean_table_name(self, name):
        """Veritabanı tablo adı için geçersiz karakterleri temizler."""
        name = name.strip().lower()
        name = (
            name.replace("ç", "c")
            .replace("ğ", "g")
            .replace("ı", "i")
            .replace("ö", "o")
            .replace("ş", "s")
            .replace("ü", "u")
        )
        name = re.sub(r"[^a-z0-9_]", "_", name)
        name = re.sub(r"_{2,}", "_", name)
        name = name.strip("_")
        return name

    def _create_project_table_copy(self):
        """
        proje_sablonu tablosunun yapısını kopyalayarak yeni bir proje tablosu oluşturur.
        Bu metod, yalnızca yeni bir proje oluşturulurken çağrılmalıdır.
        poz_no'nun yeni projede de PRIMARY KEY olmasını sağlar.
        """
        proje_adi = self.lineEdit_projeadi.text().strip()
        proje_ayi = self.lineEdit_projeayi.text().strip()

        if not proje_adi or not proje_ayi:
            QMessageBox.warning(
                self, "Giriş Eksik", "Lütfen Proje Adı ve Proje Ayı/Yılı girin."
            )
            return None

        new_project_table_name = self._clean_table_name(
            f"proje_{proje_adi}_{proje_ayi}"
        )

        try:
            self.db.get_cursor().execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{
                    new_project_table_name}';"
            )
            if self.db.get_cursor().fetchone():
                QMessageBox.information(
                    self,
                    "Proje Mevcut",
                    f"'{new_project_table_name}' adında bir proje zaten mevcut. Mevcut proje yüklenecek.",
                )
                return new_project_table_name
            else:
                create_table_sql = f"""
                CREATE TABLE {new_project_table_name} (
                    Poz_No TEXT PRIMARY KEY,
                    Poz_Açıklaması TEXT,
                    Ölçü_Birimi TEXT,
                    Birim_Fiyat REAL,
                    Kullanıldığı_Proje TEXT,
                    Kullanıldığı_Tarih TEXT,
                    Tedarikçi TEXT,
                    Alış_Fiyatı REAL,
                    Yeni_Proje_Adı TEXT,
                    Yeni_Proje_Tarihi TEXT,
                    Yeni_Tedarikçi TEXT,
                    Metraj REAL,
                    Yaklaşık_İşçilik REAL,
                    Yaklaşık_Maliyet REAL,
                    Teklif_Fiyat REAL,
                    Teklif_İşçilik REAL,
                    Teklif_Maliyet REAL,
                    Gerçek_Fiyat REAL,
                    Gerçek_İşçilik REAL,
                    Gerçek_Maliyet REAL
                );
                """

                self.db.get_cursor().execute(create_table_sql)
                self.db.get_connection().commit()
                QMessageBox.information(
                    self,
                    "Proje Oluşturuldu",
                    f"Yeni proje '{new_project_table_name.replace('proje_', '').replace(
                        '_', ' ').title()}' başarıyla oluşturuldu.",
                )
                return new_project_table_name
        except sqlite3.Error as e:
            QMessageBox.critical(
                self, "Tablo Oluşturma Hatası", f"Proje tablosu oluşturulamadı: {
                    e}"
            )
            return None

    def _kaydet(self):
        """
        Tablodaki verileri mevcut proje tablosuna kaydeder/günceller.
        PDF çıktısı artık kaydetme işleminden sonra otomatik değil, 'Teklif Oluştur' butonuna basıldığında alınacak.
        """
        if self.project_table_name is None:
            self.project_table_name = self._create_project_table_copy()
            if self.project_table_name is None:
                return

        if self.tableWidget.rowCount() == 0:
            QMessageBox.information(
                self, "Bilgi", "Kaydedilecek veri bulunmuyor.")
            return

        kaydedilecek_veriler = []
        for row in range(self.tableWidget.rowCount()):
            current_poz_no = (
                self.tableWidget.item(row, 0).text()
                if self.tableWidget.item(row, 0)
                else "N/A"
            )
            if current_poz_no == "N/A":
                QMessageBox.warning(
                    self,
                    "Hata",
                    f"Satır {row+1}'deki Poz No bulunamadı. Kayıt atlandı.",
                )
                continue

            poz_info = self.original_poz_data.get(row, {})
            if "no" not in poz_info:
                poz_info["no"] = current_poz_no
            arsiv_info = self.arsiv_data_for_rows.get(row, {})

            project_entry = {
                "Yeni_Proje_Adı": (
                    self.tableWidget.item(
                        row, self.editable_columns["Yeni Proje Adı"]
                    ).text()
                    if self.tableWidget.item(
                        row, self.editable_columns["Yeni Proje Adı"]
                    )
                    else ""
                ),
                "Yeni_Proje_Tarihi": (
                    self.tableWidget.item(
                        row, self.editable_columns["Yeni Proje Tarihi"]
                    ).text()
                    if self.tableWidget.item(
                        row, self.editable_columns["Yeni Proje Tarihi"]
                    )
                    else ""
                ),
                "Yeni_Tedarikçi": (
                    self.tableWidget.item(
                        row, self.editable_columns["Yeni Tedarikçi"]
                    ).text()
                    if self.tableWidget.item(
                        row, self.editable_columns["Yeni Tedarikçi"]
                    )
                    else ""
                ),
                "Metraj": self._get_float_value(
                    self.tableWidget.item(row, self.editable_columns["Metraj"])
                ),
                "Yaklaşık_İşçilik": self._get_float_value(
                    self.tableWidget.item(
                        row, self.editable_columns["Yaklaşık İşçilik"]
                    )
                ),
                "Yaklaşık_Maliyet": self._get_float_value(
                    self.tableWidget.item(row, 13)
                ),
                "Teklif_Fiyat": self._get_float_value(
                    self.tableWidget.item(
                        row, self.editable_columns["Teklif Fiyat"])
                ),
                "Teklif_İşçilik": self._get_float_value(
                    self.tableWidget.item(
                        row, self.editable_columns["Teklif İşçilik"])
                ),
                "Teklif_Maliyet": self._get_float_value(self.tableWidget.item(row, 16)),
                "Gerçek_Fiyat": self._get_float_value(
                    self.tableWidget.item(
                        row, self.editable_columns["Gerçek Fiyat"])
                ),
                "Gerçek_İşçilik": self._get_float_value(
                    self.tableWidget.item(
                        row, self.editable_columns["Gerçek İşçilik"])
                ),
                "Gerçek_Maliyet": self._get_float_value(self.tableWidget.item(row, 19)),
            }
            kaydedilecek_veriler.append((poz_info, project_entry, arsiv_info))

        try:
            self.db.get_connection().execute("BEGIN TRANSACTION")
            basarili_kayit_sayisi = 0 # Düzeltildi: basarili_kayit_sayilari -> basarili_kayit_sayisi
            for poz_info, project_entry, arsiv_info in kaydedilecek_veriler:
                poz_no = poz_info["no"]
                try:
                    self.db.get_cursor().execute(
                        f"""
                        INSERT OR REPLACE INTO {self.project_table_name} (
                            Poz_No,
                            Poz_Açıklaması,
                            Ölçü_Birimi,
                            Birim_Fiyat,
                            Kullanıldığı_Proje,
                            Kullanıldığı_Tarih,
                            Tedarikçi,
                            Alış_Fiyatı,
                            Yeni_Proje_Adı,
                            Yeni_Proje_Tarihi,
                            Yeni_Tedarikçi,
                            Metraj,
                            Yaklaşık_İşçilik,
                            Yaklaşık_Maliyet,
                            Teklif_Fiyat,
                            Teklif_İşçilik,
                            Teklif_Maliyet,
                            Gerçek_Fiyat,
                            Gerçek_İşçilik,
                            Gerçek_Maliyet
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            poz_no,
                            poz_info.get("tanim", ""),
                            poz_info.get("birim", ""),
                            poz_info.get("bedel", 0.0),
                            arsiv_info.get("Kullanıldığı_Proje", ""),
                            arsiv_info.get("Kullanıldığı_Tarih", ""),
                            arsiv_info.get("Tedarikçi", ""),
                            arsiv_info.get("Alış_Fiyatı", 0.0),
                            project_entry.get("Yeni_Proje_Adı", ""),
                            project_entry.get("Yeni_Proje_Tarihi", ""),
                            project_entry.get("Yeni_Tedarikçi", ""),
                            project_entry.get("Metraj", 0.0),
                            project_entry.get("Yaklaşık_İşçilik", 0.0),
                            project_entry.get("Yaklaşık_Maliyet", 0.0),
                            project_entry.get("Teklif_Fiyat", 0.0),
                            project_entry.get("Teklif_İşçilik", 0.0),
                            project_entry.get("Teklif_Maliyet", 0.0),
                            project_entry.get("Gerçek_Fiyat", 0.0),
                            project_entry.get("Gerçek_İşçilik", 0.0),
                            project_entry.get("Gerçek_Maliyet", 0.0),
                        ),
                    )
                    basarili_kayit_sayisi += 1
                except sqlite3.Error as e:
                    QMessageBox.warning(
                        self,
                        "Veritabanı Kayıt Hatası",
                        f"Poz No '{
                            poz_no}' için veri kaydedilirken hata oluştu: {e}",
                    )
                    self.db.get_connection().rollback()
                    return
            self.db.get_connection().commit()
            QMessageBox.information(
                self,
                "Kaydetme Başarılı",
                f"{basarili_kayit_sayisi} adet poz başarıyla kaydedildi/güncellendi.", # Düzeltildi: basarili_kayit_sayilari -> basarili_kayit_sayisi
            )
        except sqlite3.Error as e:
            QMessageBox.critical(
                self,
                "Veritabanı Hatası",
                f"Veri kaydedilirken işlem hatası oluştu: {e}",
            )
            self.db.get_connection().rollback()
        except Exception as e:
            QMessageBox.critical(
                self, "Genel Hata", f"Beklenmeyen bir hata oluştu: {e}"
            )
            self.db.get_connection().rollback()

    def _update_total_cost_difference(self):
        """Yaklaşık Maliyet Toplamı, Teklif Maliyeti Toplamı ve Gerçek Maliyet Toplamı arasındaki
        farkları hesaplayarak ilgili UI elemanlarını günceller."""

        # Toplamları sıfırla
        yaklasik_maliyet_toplam = 0.0
        teklif_maliyeti_toplam = 0.0
        gercek_maliyet_toplam = 0.0

        # Tablodaki tüm satırları dolaşarak maliyet değerlerini topla
        for row in range(self.tableWidget.rowCount()):
            # Yaklaşık Maliyet sütunu
            yaklasik_maliyet_toplam += self._get_float_value(
                self.tableWidget.item(row, 13))
            # Teklif Maliyeti sütunu
            teklif_maliyeti_toplam += self._get_float_value(
                self.tableWidget.item(row, 16))
            # Gerçek Maliyet sütunu
            gercek_maliyet_toplam += self._get_float_value(
                self.tableWidget.item(row, 19))

        # Toplam değerleri ilgili label'lara yazdır
        self._update_label_if_exists("label_rayic_toplam",
                                     f"Yaklaşık Maliyet Toplamı: {self._format_number_for_display(yaklasik_maliyet_toplam)} TL")

        self._update_label_if_exists("label_Teklif_Maliyeti",
                                     f"Teklif Maliyeti Toplamı: {self._format_number_for_display(teklif_maliyeti_toplam)} TL")

        self._update_label_if_exists("label_gercek_maliyet_toplam",
                                     f"Gerçek Maliyet Toplamı: {self._format_number_for_display(gercek_maliyet_toplam)} TL")

        # Yaklaşık Maliyet ile Teklif Maliyeti arasındaki fark ve yüzde
        fark_yaklasik_teklif, yuzde_fark_yaklasik_teklif = self._calculate_difference(
            yaklasik_maliyet_toplam, teklif_maliyeti_toplam)

        self._update_label_if_exists(
            "label_fark_yaklasik_teklif",
            f"Yaklaşık - Teklif Maliyet Farkı: {self._format_number_for_display(fark_yaklasik_teklif)} TL (Kırım Oranı: %{yuzde_fark_yaklasik_teklif:,.2f})",
            fark_yaklasik_teklif
        )

        # Teklif Maliyeti ile Gerçek Maliyet arasındaki fark ve yüzde
        fark_teklif_gercek, yuzde_fark_teklif_gercek = self._calculate_difference(
            teklif_maliyeti_toplam, gercek_maliyet_toplam)

        self._update_label_if_exists(
            "label_fark_teklif_gercek",
            f"Teklif - Gerçek Maliyet Farkı: {self._format_number_for_display(fark_teklif_gercek)} TL (Fark Oranı: %{yuzde_fark_teklif_gercek:,.2f})",
            fark_teklif_gercek
        )

    # Yardımcı fonksiyonlar (class'a eklenmeli)

    def _update_label_if_exists(self, label_name, text, value=None):
        """Varsa label'ı günceller ve renk ayarı yapar."""
        if hasattr(self, label_name):
            label = getattr(self, label_name)
            label.setText(text)
            if value is not None:
                self._set_label_color(label, value)


    def _calculate_difference(self, value1, value2):
        """İki değer arasındaki farkı ve yüzde farkı hesaplar."""
        difference = value1 - value2
        percentage = (difference / value1 * 100) if value1 != 0 else 0.0
        return difference, percentage

    def _set_label_color(self, label, value):
        """Bir QLabel'in rengini değerine göre ayarlar."""
        if value < 0:
            label.setStyleSheet("color: red;")
        elif value > 0:
            label.setStyleSheet("color: green;")
        else:
            label.setStyleSheet("color: white;")

    def _update_total_Birim_Fiyat(self):
        """Toplam Birim Fiyatı günceller."""
        total_birim_fiyat = 0.0
        for row in range(self.tableWidget.rowCount()):
            item_birim_fiyat = self.tableWidget.item(row, 3)
            total_birim_fiyat += self._get_float_value(item_birim_fiyat)
        if hasattr(self, "label_toplam_birim_fiyat"):
            self.label_toplam_birim_fiyat.setText(
                f"Toplam Birim Fiyat: {
                    self._format_number_for_display(total_birim_fiyat)} TL"
            )

    def _update_total_Teklif_Maliyeti(self):
        """Toplam Teklif Maliyetini günceller."""
        total_teklif_maliyeti = 0.0
        for row in range(self.tableWidget.rowCount()):
            item_teklif_maliyeti = self.tableWidget.item(row, 16)
            total_teklif_maliyeti += self._get_float_value(
                item_teklif_maliyeti)
        if hasattr(self, "label_toplam_teklif_maliyeti"):
            self.label_toplam_teklif_maliyeti.setText(
                f"Toplam Teklif Maliyeti: {
                    self._format_number_for_display(total_teklif_maliyeti)} TL"
            )

    def _enable_keyboard_navigation(self):
        """TableWidget'ta klavye navigasyonunu ve kopyala/yapıştırı etkinleştirir."""
        self.tableWidget.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectItems
        )
        self.tableWidget.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )

        copy_action = QAction("Kopyala", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self._copy_selected_cells)
        self.addAction(copy_action)

        paste_action = QAction("Yapıştır", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self._paste_cells)
        self.addAction(paste_action)

    def _copy_selected_cells(self):
        """Seçili hücrelerin içeriğini panoya kopyalar."""
        selected_ranges = self.tableWidget.selectedRanges()
        if not selected_ranges:
            return

        # Sadece ilk seçili aralığı işleyelim
        selected_range = selected_ranges[0]
        min_row = selected_range.topRow()
        max_row = selected_range.bottomRow()
        min_col = selected_range.leftColumn()
        max_col = selected_range.rightColumn()

        clipboard_text = []
        for row in range(min_row, max_row + 1):
            row_data = []
            for col in range(min_col, max_col + 1):
                item = self.tableWidget.item(row, col)
                if item:
                    row_data.append(item.text())
                else:
                    row_data.append("")
            clipboard_text.append("\t".join(row_data))

        QApplication.clipboard().setText("\n".join(clipboard_text))

    def _paste_cells(self):
        """Panodaki veriyi seçili hücrelere yapıştırır."""
        clipboard_text = QApplication.clipboard().text()
        if not clipboard_text:
            return

        selected_items = self.tableWidget.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self, "Uyarı", "Lütfen yapıştırmak için bir hücre seçin."
            )
            return

        start_row = selected_items[0].row()
        start_col = selected_items[0].column()

        rows_data = [row.split("\t") for row in clipboard_text.splitlines()]

        self.tableWidget.blockSignals(True)
        try:
            for r_offset, row_data in enumerate(rows_data):
                for c_offset, cell_value in enumerate(row_data):
                    target_row = start_row + r_offset
                    target_col = start_col + c_offset

                    if (
                        target_row < self.tableWidget.rowCount()
                        and target_col < self.tableWidget.columnCount()
                    ):
                        # Sadece düzenlenebilir sütunlara yapıştırma yap
                        if target_col in self.pasteable_columns:
                            item = self.tableWidget.item(
                                target_row, target_col)
                            if item is None:
                                item = QTableWidgetItem()
                                self.tableWidget.setItem(
                                    target_row, target_col, item)
                            item.setText(cell_value)
                            # Yapıştırılan hücrenin ait olduğu satırın hesaplamalarını güncelle
                            self._update_calculations(target_row)
                        else:
                            print(
                                f"DEBUG: Sütun {
                                    target_col} yapıştırılabilir değil. Değer atlandı: {cell_value}"
                            )
                    else:
                        print(
                            f"DEBUG: Hedef hücre ({target_row}, {
                                target_col}) tablo sınırları dışında. Değer atlandı: {cell_value}"
                        )
        finally:
            self.tableWidget.blockSignals(False)
            self._update_total_cost_difference()
            self._update_total_Birim_Fiyat()
            self._update_total_Teklif_Maliyeti()

    def _show_context_menu(self, position):
        """TableWidget'ta sağ tık menüsünü gösterir."""
        menu = QMenu()

        insert_row_action = menu.addAction("Satır Ekle")
        delete_row_action = menu.addAction("Satır Sil")
        menu.addSeparator()  # Ayırıcı ekleyelim
        copy_action = menu.addAction("Kopyala")
        paste_action = menu.addAction("Yapıştır")

        action = menu.exec(self.tableWidget.mapToGlobal(position))

        if action == insert_row_action:
            self._insert_row()
        elif action == delete_row_action:
            self._delete_selected_rows()
        elif action == copy_action:
            self._copy_selected_cells()
        elif action == paste_action:
            self._paste_cells()

    def _insert_row(self):
        """TableWidget'a yeni bir boş satır ekler."""
        current_row = self.tableWidget.currentRow()
        if current_row == -1:
            current_row = self.tableWidget.rowCount()
        else:
            current_row += 1
        self.tableWidget.insertRow(current_row)

        # Yeni eklenen satır için varsayılan değerleri ayarla
        for col_idx in range(self.tableWidget.columnCount()):
            item = QTableWidgetItem("")
            # Hesaplanan sütunlar ve poz bilgileri sütunları düzenlenemez olmalı
            if (
                col_idx not in self.editable_columns.values()
                or col_idx in self.non_editable_calculated_columns
            ):
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tableWidget.setItem(current_row, col_idx, item)

        # Yeni Proje Tarihi sütununa bugünün tarihini otomatik olarak ekle
        yeni_proje_tarihi_col_idx = self.editable_columns.get(
            "Yeni Proje Tarihi")
        if yeni_proje_tarihi_col_idx is not None:
            date_item = self.tableWidget.item(
                current_row, yeni_proje_tarihi_col_idx)
            if date_item is None:
                date_item = QTableWidgetItem()
                self.tableWidget.setItem(
                    current_row, yeni_proje_tarihi_col_idx, date_item
                )
            date_item.setText(datetime.date.today().strftime("%d-%m-%Y"))

        # Yeni Proje Adı sütununa mevcut proje adını otomatik olarak ekle
        proje_adi_col_idx = self.editable_columns.get("Yeni Proje Adı")
        if proje_adi_col_idx is not None and hasattr(self, "lineEdit_projeadi"):
            project_name = self.lineEdit_projeadi.text()
            if project_name:
                item = self.tableWidget.item(current_row, proje_adi_col_idx)
                if item is None:
                    item = QTableWidgetItem()
                    self.tableWidget.setItem(
                        current_row, proje_adi_col_idx, item)
                item.setText(project_name)

        # Yeni eklenen satır için original_poz_data ve arsiv_data_for_rows'u başlat
        self.original_poz_data[current_row] = {
            "no": "",
            "tanim": "",
            "birim": "",
            "bedel": 0.0,
        }
        self.arsiv_data_for_rows[current_row] = {
            "Kullanıldığı_Proje": "",
            "Kullanıldığı_Tarih": "",
            "Tedarikçi": "",
            "Alış_Fiyatı": 0.0,
        }

        # Tablo satır sayısını ve donmuş görünümü güncelle
        self.frozen_wrapper_widget.frozen_view.setRowHeight(
            current_row, self.tableWidget.rowHeight(current_row)
        )
        self.tableWidget.setCurrentCell(current_row, 0)
        self._update_total_cost_difference()

    def _delete_selected_rows(self):
        """Seçili satırları TableWidget'tan siler."""
        selected_rows = sorted(
            list(set(index.row()
                     for index in self.tableWidget.selectedIndexes())),
            reverse=True,
        )
        if not selected_rows:
            QMessageBox.warning(
                self, "Uyarı", "Lütfen silmek için satır seçin.")
            return

        reply = QMessageBox.question(
            self,
            "Satır Sil",
            f"{len(selected_rows)} adet satırı silmek istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            for row in selected_rows:
                self.tableWidget.removeRow(row)
                if row in self.original_poz_data:
                    del self.original_poz_data[row]
                if row in self.arsiv_data_for_rows:
                    del self.arsiv_data_for_rows[row]

            # Silme işleminden sonra dictionary'leri yeniden indeksle
            new_original_poz_data = {}
            new_arsiv_data_for_rows = {}
            # Güncel satırları al
            current_row_count = self.tableWidget.rowCount()
            for i in range(current_row_count):
                # eski indeks yerine, orijinal poz data anahtarlarını bulup, yeni indekslerle eşleştir
                # Bu kısım biraz karmaşıklaşabilir, basitleştirmek için mevcut verileri direkt okuyup yeniden oluşturmak daha sağlam.
                # Ancak burada orijinal poz data ve arsiv data tutulduğu için yeniden indeksleme yapalım:
                # Silinen satırların altında kalan satırların indeksleri değiştiği için bu düzeltme gerekli.
                # Bu yaklaşım, silme işlemi sonrası indeks kaymalarını düzeltir.
                for old_idx in sorted(self.original_poz_data.keys()):
                    if old_idx >= row and old_idx not in selected_rows: # Silinen satırın üstündekiler aynı kalır, altındakilerin indeksi azalır.
                        new_key = old_idx - selected_rows.count(x for x in selected_rows if x < old_idx)
                        if new_key >= 0 and new_key < current_row_count: # Sadece geçerli aralıktaki indeksleri ekle
                            new_original_poz_data[new_key] = self.original_poz_data[old_idx]
                            new_arsiv_data_for_rows[new_key] = self.arsiv_data_for_rows[old_idx]

            self.original_poz_data = new_original_poz_data
            self.arsiv_data_for_rows = new_arsiv_data_for_rows


            QMessageBox.information(
                self,
                "Satır Silindi",
                f"{len(selected_rows)} adet satır başarıyla silindi.",
            )
            self._update_total_cost_difference()

    def _update_project_names_in_table(self, text):
        """lineEdit_projeadi değiştiğinde tabloda "Yeni Proje Adı" sütununu günceller."""
        proje_adi_col_idx = self.editable_columns.get("Yeni Proje Adı")
        if proje_adi_col_idx is not None:
            self.tableWidget.blockSignals(True)
            for row in range(self.tableWidget.rowCount()):
                item = self.tableWidget.item(row, proje_adi_col_idx)
                if item is None:
                    item = QTableWidgetItem()
                    self.tableWidget.setItem(row, proje_adi_col_idx, item)
                item.setText(text)
            self.tableWidget.blockSignals(False)

    def _arsivle_proje(self):
        """Mevcut projeyi arşivler ve tabloyu temizler."""
        if self.project_table_name is None:
            QMessageBox.information(
                self, "Bilgi", "Arşivlenecek aktif bir proje bulunmuyor."
            )
            return

        # Kullanıcıya onay sorusu
        reply = QMessageBox.question(
            self,
            "Proje Arşivleme",
            f"'{self.project_table_name.replace('proje_', '').replace('_', ' ').title(
            )}' projesini arşivlemek istediğinizden emin misiniz? Bu işlem projeyi yeni verilerle arşivleyecektir.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.db.archive_project_data(self.project_table_name)

                if success:
                    QMessageBox.information(
                        self,
                        "Proje Arşivlendi",
                        f"'{self.project_table_name.replace('proje_', '').replace('_', ' ').title(
                        )}' projesi başarıyla arşivlendi. Tablo temizlenecek ve kapatılacak.",
                    )
                    self.tableWidget.setRowCount(0)
                    self.project_table_name = None
                    self.close()
                else:
                    QMessageBox.critical(
                        self,
                        "Arşivleme Hatası",
                        "Proje arşivlenirken bir hata oluştu. Detaylar için konsolu kontrol edin.",
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Genel Hata",
                    f"Proje arşivlenirken beklenmeyen bir hata oluştu: {e}",
                )
                
                
                
    
