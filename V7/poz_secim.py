import sys
import sqlite3
import pandas as pd
from typing import List, Dict, Optional
from pathlib import Path
import re

from PyQt6.QtWidgets import (
    QDialog,
    QTableView,
    QHeaderView,
    QMessageBox,
    QStyledItemDelegate,
    QStyleOptionButton,
    QStyle,
    QApplication,
    QFileDialog,
    QProgressDialog,
)
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QSortFilterProxyModel, QThread, QObject
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from ui_poz_secim import Ui_PozSecimDialog

from config import get_config
cfg = get_config()
UI_PATHS = cfg["UI_PATHS"]
DB_FILE = cfg["DB_FILE"]



class CheckBoxDelegate(QStyledItemDelegate):
    """Özelleştirilmiş checkbox delegate sınıfı"""

    def paint(self, painter, option, index):
        value = index.data(Qt.ItemDataRole.CheckStateRole)
        if value is None:
            value = Qt.CheckState.Unchecked

        opt = QStyleOptionButton()
        opt.state |= QStyle.StateFlag.State_Enabled

        if value == Qt.CheckState.Checked:
            opt.state |= QStyle.StateFlag.State_On

        opt.rect = self.getCheckBoxRect(option)

        QApplication.style().drawControl(
            QStyle.ControlElement.CE_CheckBox, opt, painter
        )

    def editorEvent(self, event, model, option, index):
        if event.type() == event.Type.MouseButtonRelease and index.column() == 4:
            source_index = model.mapToSource(index)
            current = source_index.data(Qt.ItemDataRole.CheckStateRole)
            new_state = (
                Qt.CheckState.Unchecked
                if current == Qt.CheckState.Checked
                else Qt.CheckState.Checked
            )
            model.sourceModel().setData(
                source_index, new_state, Qt.ItemDataRole.CheckStateRole
            )
            return True
        return False

    def getCheckBoxRect(self, option):
        checkbox_rect = QApplication.style().subElementRect(
            QStyle.SubElement.SE_CheckBoxIndicator, QStyleOptionButton(), None
        )
        x = option.rect.x() + (option.rect.width() - checkbox_rect.width()) / 2
        y = option.rect.y() + (option.rect.height() - checkbox_rect.height()) / 2
        return QRect(int(x), int(y), checkbox_rect.width(), checkbox_rect.height())


class PozFilterProxyModel(QSortFilterProxyModel):
    def filterAcceptsRow(self, source_row, source_parent):
        filter_text = self.filterRegularExpression().pattern()
        if not filter_text:
            return True

        Poz_No_index = self.sourceModel().index(source_row, 0, source_parent)
        Poz_No = self.sourceModel().data(Poz_No_index)

        Poz_Açıklaması_index = self.sourceModel().index(source_row, 1, source_parent)
        Poz_Açıklaması = self.sourceModel().data(Poz_Açıklaması_index)

        if Poz_No and re.search(filter_text, Poz_No, re.IGNORECASE):
            return True
        if Poz_Açıklaması and re.search(filter_text, Poz_Açıklaması, re.IGNORECASE):
            return True

        return False


# --- Yeni Worker Sınıfı ---
class PozLoaderWorker(QObject):
    finished = pyqtSignal(
        list, str
    )  # Veri listesi ve işlem türü ('initial' veya 'excel')
    error = pyqtSignal(str)  # Hata mesajı
    progress = pyqtSignal(int, int)  # Mevcut/Toplam ilerleme

    def __init__(
        self,
        db_path: str,
        operation_type: str,
        excel_poz_nos: Optional[List[str]] = None,
    ):
        super().__init__()
        self.db_path = db_path
        self.operation_type = operation_type
        self.excel_poz_nos = excel_poz_nos
        self._is_running = True  # Worker'ın çalışıp çalışmadığını izlemek için bayrak
        print(
            f"PozLoaderWorker: __init__ - db_path: {self.db_path}, operation_type: {self.operation_type}, excel_poz_nos (first 5): {self.excel_poz_nos[:5] if self.excel_poz_nos else 'None'}"
        )

    def stop(self):
        """Worker'ı durdurma isteği gönderir."""
        self._is_running = False
        print("PozLoaderWorker: Stop requested.")

    def run(self):
        print(
            f"PozLoaderWorker: run() started for operation_type: {self.operation_type}"
        )
        try:
            # Worker kendi veritabanı bağlantısını kuruyor, bu çoklu thread ortamı için en güvenli yoldur.
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if self.operation_type == "initial":
                sql = """SELECT id, Poz_No, Poz_Açıklaması, Ölçü_Birimi, Birim_Fiyat
                             FROM pozlar ORDER BY Poz_No"""
                cursor.execute(sql)
            elif self.operation_type == "excel":
                if not self.excel_poz_nos:
                    self.error.emit("Excel poz numaraları boş.")
                    print("PozLoaderWorker: Hata - Excel poz numaraları boş.")
                    return

                # SQL sorgusunu hazırlarken IN operatörü için yer tutucuları oluşturma
                placeholders = ",".join("?" * len(self.excel_poz_nos))
                sql = f"""SELECT id, Poz_No, Poz_Açıklaması, Ölçü_Birimi, Birim_Fiyat
                              FROM pozlar WHERE Poz_No IN ({placeholders})"""
                print(f"PozLoaderWorker: Excel sorgusu hazırlanıyor: {sql}")
                print(
                    f"PozLoaderWorker: Sorgu parametreleri (ilk 5): {self.excel_poz_nos[:5]}"
                )
                cursor.execute(sql, self.excel_poz_nos)
            else:
                self.error.emit("Geçersiz işlem türü.")
                print(
                    f"PozLoaderWorker: Hata - Geçersiz işlem türü: {self.operation_type}"
                )
                return

            rows = cursor.fetchall()
            conn.close()  # İşlem bitince bağlantıyı kapat
            print(f"PozLoaderWorker: {len(rows)} satır veritabanından çekildi.")

            # Sadece worker henüz durdurulmamışsa finished sinyalini emit et
            if self._is_running:
                self.finished.emit(rows, self.operation_type)
                print(
                    f"PozLoaderWorker: finished sinyali emit edildi, operation_type: {self.operation_type}"
                )

        except sqlite3.Error as e:
            self.error.emit(f"Veritabanı hatası: {e}")
            print(f"PozLoaderWorker: Veritabanı hatası: {e}")
        except Exception as e:
            self.error.emit(f"Beklenmedik hata: {e}")
            print(f"PozLoaderWorker: Beklenmedik hata: {e}")
        finally:
            # İşlem bittiğinde veya hata oluştuğunda thread'i durdurma bayrağını resetle
            self._is_running = False
            print("PozLoaderWorker: run() tamamlandı.")


from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QProgressDialog,
    QMessageBox,
    QApplication,
    QTableView,
    QHeaderView,
)


class PozSecimDialog(QDialog):
    def __init__(self, db_connection, db_cursor, db_path, parent=None):
        super().__init__(parent)
        self.ui = Ui_PozSecimDialog()
        self.ui.setupUi(self)

        self.db_connection = db_connection
        self.db_cursor = db_cursor
        self.db_path = db_path
        self.worker_thread = None
        self.worker = None
        self.progress_dialog = None
        self.secilen_pozlari = []

        self._setup_ui()
        self._connect_signals()

        self.base_model = QStandardItemModel(0, 6)
        self.proxy_model = PozFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.base_model)

        self.ui.tableView.setModel(self.proxy_model)
        self.ui.tableView.setItemDelegateForColumn(4, CheckBoxDelegate())
        self.ui.tableView.setColumnHidden(5, True)

        self._load_initial_data_async()

    def _setup_ui(self):
        self.setWindowTitle("Poz Seçimi")

        self.resize(1000, 600)
        self.ui.tableView.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.ui.tableView.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.ui.tableView.setSortingEnabled(True)

    def _connect_signals(self):
        self.ui.pushButton_ara.clicked.connect(self._filtrele)
        self.ui.pushButton_ekle.clicked.connect(self._secilenleri_ekle)
        self.ui.pushButton_iptal.clicked.connect(self.reject)
        self.ui.lineEdit_pozno.textChanged.connect(self._filtrele)
        self.ui.pushButton_excel_yukle.clicked.connect(self._excel_den_poz_yukle_async)

    def _load_initial_data_async(self):
        self._terminate_worker_thread()
        self.progress_dialog = QProgressDialog("Pozlar yükleniyor...", None, 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.progress_dialog.setWindowTitle("Yükleniyor...")
        self.progress_dialog.show()

        self.worker_thread = QThread()
        self.worker = PozLoaderWorker(self.db_path, "initial")
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._handle_initial_load_finished)
        self.worker.error.connect(self._handle_worker_error)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker.finished.connect(self.worker.deleteLater)

        self.worker_thread.start()

    def _handle_initial_load_finished(self, rows: list, operation_type: str):
        if self.progress_dialog:
            self.progress_dialog.close()

        self.base_model.clear()
        self.base_model.setHorizontalHeaderLabels(
            [
                "Poz No",
                "Poz Açıklaması",
                "Ölçü Birimi",
                "Rayiç Bedeli",
                "Seçim",
                "Poz ID",
            ]
        )
        self.base_model.blockSignals(True)
        for idx, row in enumerate(rows):
            self._add_row_to_base_model(idx, row)
        self.base_model.blockSignals(False)
        self.base_model.layoutChanged.emit()

    def _add_row_to_base_model(self, row_idx: int, row_data: tuple):
        self.base_model.setItem(row_idx, 0, QStandardItem(str(row_data[1])))
        self.base_model.setItem(row_idx, 1, QStandardItem(str(row_data[2])))
        self.base_model.setItem(row_idx, 2, QStandardItem(str(row_data[3])))
        self.base_model.setItem(
            row_idx, 3, QStandardItem(str(row_data[4]).replace(".", ","))
        )

        checkbox_item = QStandardItem()
        checkbox_item.setCheckable(True)
        checkbox_item.setCheckState(Qt.CheckState.Unchecked)
        self.base_model.setItem(row_idx, 4, checkbox_item)

        poz_id_item = QStandardItem(str(row_data[0]))
        self.base_model.setItem(row_idx, 5, poz_id_item)

    def _filtrele(self):
        text = self.ui.lineEdit_pozno.text().strip()
        self.proxy_model.setFilterRegularExpression(text)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

    def _tumunu_kaldir_tum_modellerde(self):
        if not self.base_model or self.base_model.rowCount() == 0:
            return

        self.base_model.blockSignals(True)
        for row in range(self.base_model.rowCount()):
            item = self.base_model.item(row, 4)
            if item and item.isCheckable():
                item.setCheckState(Qt.CheckState.Unchecked)
        self.base_model.blockSignals(False)
        self.base_model.layoutChanged.emit()

    def _secilenleri_ekle(self):
        self.secilen_pozlari = []

        if not self.base_model or self.base_model.rowCount() == 0:
            QMessageBox.warning(self, "Uyarı", "Yüklü poz bulunmuyor.")
            return

        for row in range(self.base_model.rowCount()):
            checkbox = self.base_model.item(row, 4)
            if checkbox and checkbox.checkState() == Qt.CheckState.Checked:
                try:
                    poz = {
                        "id": int(self.base_model.item(row, 5).text()),
                        "no": self.base_model.item(row, 0).text(),
                        "tanim": self.base_model.item(row, 1).text(),
                        "birim": self.base_model.item(row, 2).text(),
                        "bedel": float(
                            self.base_model.item(row, 3).text().replace(",", ".")
                        ),
                    }
                    self.secilen_pozlari.append(poz)
                except Exception as e:
                    QMessageBox.warning(self, "Veri Hatası", f"Satır {row + 1}: {e}")
                    continue

        if not self.secilen_pozlari:
            QMessageBox.warning(self, "Uyarı", "Lütfen en az bir poz seçiniz!")
            return

        self.accept()

    def _excel_den_poz_yukle_async(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Excel Dosyası Seç",
            "",
            "Excel Dosyaları (*.xlsx *.xls);;Tüm Dosyalar (*)",
        )

        if not file_name:
            return

        self._terminate_worker_thread()

        try:
            df = pd.read_excel(file_name, engine="openpyxl")
            if "Poz No" not in df.columns:
                raise ValueError("Excel dosyasında 'Poz No' sütunu bulunamadı.")
            excel_poz_nos = df["Poz No"].astype(str).tolist()

            if not excel_poz_nos:
                QMessageBox.information(self, "Bilgi", "Poz numarası bulunamadı.")
                return

            self.progress_dialog = QProgressDialog("Yükleniyor...", None, 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
            self.progress_dialog.setWindowTitle("Yükleniyor...")
            self.progress_dialog.show()

            self.worker_thread = QThread()
            self.worker = PozLoaderWorker(self.db_path, "excel", excel_poz_nos)
            self.worker.moveToThread(self.worker_thread)

            self.worker_thread.started.connect(self.worker.run)
            self.worker.finished.connect(self._handle_excel_load_finished)
            self.worker.error.connect(self._handle_worker_error)
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)
            self.worker.finished.connect(self.worker.deleteLater)

            self.worker_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Excel yükleme hatası: {e}")

    def _handle_excel_load_finished(self, rows: list, operation_type: str):
        if self.progress_dialog:
            self.progress_dialog.close()

        if not rows:
            QMessageBox.information(self, "Bilgi", "Veri bulunamadı.")
            self.proxy_model.setFilterRegularExpression("")
            return

        self._tumunu_kaldir_tum_modellerde()
        poz_nos_set = {str(row[1]) for row in rows}

        selected_count = 0
        self.base_model.blockSignals(True)
        for row_idx in range(self.base_model.rowCount()):
            poz_no_item = self.base_model.item(row_idx, 0)
            if poz_no_item and poz_no_item.text() in poz_nos_set:
                checkbox_item = self.base_model.item(row_idx, 4)
                if checkbox_item and checkbox_item.isCheckable():
                    checkbox_item.setCheckState(Qt.CheckState.Checked)
                    selected_count += 1
        self.base_model.blockSignals(False)
        self.base_model.layoutChanged.emit()

        filter_regex = "|".join([f"^{re.escape(pn)}$" for pn in poz_nos_set])
        self.proxy_model.setFilterRegularExpression(filter_regex)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        QMessageBox.information(
            self, "Başarılı", f"{selected_count} poz yüklendi ve işaretlendi."
        )

    def _handle_worker_error(self, message: str):
        if self.progress_dialog:
            self.progress_dialog.close()
        QMessageBox.critical(self, "Hata", message)

    def _terminate_worker_thread(self):
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker.stop()
            self.worker_thread.quit()
            self.worker_thread.wait(2000)
            if self.worker_thread.isRunning():
                self.worker_thread.terminate()
                self.worker_thread.wait()

    def reject(self):
        self._terminate_worker_thread()
        super().reject()

    def accept(self):
        self._terminate_worker_thread()
        super().accept()

    def closeEvent(self, event):
        super().closeEvent(event)

    def secilen_pozlari_al(self) -> List[Dict]:
        return self.secilen_pozlari


# Ana uygulama bloğu
if __name__ == "__main__":
    app = QApplication(sys.argv)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    dialog = PozSecimDialog(conn, cursor, DB_FILE)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        selected = dialog.secilen_pozlari_al()
        print("\nSeçilen Pozlar:")
        for poz in selected:
            print(
                f"ID: {poz['id']}, No: {poz['no']}, Tanım: {poz['tanim']}, Birim: {poz['birim']}, Bedel: {poz['bedel']}"
            )
    else:
        print("Poz seçimi iptal edildi.")

    conn.close()
    sys.exit(app.exec())
