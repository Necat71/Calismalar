
import sqlite3
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem
import datetime


def add_poz_from_lineEdit(dialog_instance):
    """
    lineEdit_ilave'ye girilen poz numarasını veritabanından çekerek tabloya ekler.
    Bu fonksiyon, ProjeYonetimDialog sınıfının bir örneğini (self) bekler.
    """
    if not hasattr(dialog_instance, "lineEdit_ilave"):
        QMessageBox.critical(dialog_instance, "UI Hatası", "lineEdit_ilave bulunamadı.")
        return

    Poz_No_to_add = dialog_instance.lineEdit_ilave.text().strip()
    if not Poz_No_to_add:
        QMessageBox.warning(
            dialog_instance, "Eksik Bilgi", "Lütfen bir poz numarası girin."
        )
        return

    # Poz numarasının zaten tabloda olup olmadığını kontrol et
    for row in range(dialog_instance.tableWidget.rowCount()):
        item = dialog_instance.tableWidget.item(row, 0)  # Poz No sütunu 0. indekste
        if item and item.text() == Poz_No_to_add:
            QMessageBox.information(
                dialog_instance,
                "Poz Mevcut",
                f"'{Poz_No_to_add}' poz numarası tabloda zaten mevcut.",
            )
            dialog_instance.lineEdit_ilave.clear()
            return

    # Veritabanından poz bilgilerini çek - BURADA DEĞİŞİKLİK YAPILDI
    try:
        # 'poz_sablonu' yerine 'pozlar' tablosunu kullanıyoruz
        dialog_instance.db.cursor.execute(
            "SELECT * FROM pozlar WHERE Poz_No = ?", (Poz_No_to_add,)
        )
        poz_data_db = dialog_instance.db.cursor.fetchone()

        if not poz_data_db:
            QMessageBox.warning(
                dialog_instance,
                "Poz Bulunamadı",
                f"'{Poz_No_to_add}' poz numarası 'pozlar' tablosunda bulunamadı.",
            )
            dialog_instance.lineEdit_ilave.clear()
            return

        # Sütun isimlerini veritabanından çekerek daha sağlam hale getirebiliriz
        # 'poz_sablonu' yerine 'pozlar' tablosunun bilgilerini çekiyoruz
        dialog_instance.db.cursor.execute("PRAGMA table_info(pozlar);")
        db_cols_info = dialog_instance.db.cursor.fetchall()
        db_column_names = [col[1] for col in db_cols_info]

        # Varsayılan olarak poz_sablonu'ndaki gibi 'Poz_No', 'Poz_Açıklaması', 'olcu_birimi', 'Birim_Fiyat' olduğunu varsayıyoruz.
        poz_object = {
            "no": poz_data_db[db_column_names.index("Poz_No")],
            "tanim": poz_data_db[db_column_names.index("Poz_Açıklaması")],
            "birim": poz_data_db[db_column_names.index("Ölçü_Birimi")],
            "bedel": poz_data_db[db_column_names.index("Birim_Fiyat")],
        }

        # Yeni satır için tabloya eklenecek veriler (sütun sırasına göre)
        data_to_add = [
            poz_object["no"],
            poz_object["tanim"],
            poz_object["birim"],
            poz_object["bedel"],  # Rayiç Bedeli
            "",  # Kullanılan Proje Adı (boş)
            "",  # Kullanıldığı Tarih (boş)
            "",  # Tedarikçi (boş)
            0.0,  # Alış Bedeli (varsayılan 0.0)
            "",  # Yeni Proje Adı (poz_ekle tarafından doldurulacak)
            "",  # Yeni Proje Tarihi (poz_ekle tarafından doldurulacak)
            0.0,  # Alınacak Miktar (varsayılan 0.0)
            "",  # Yeni Tedarikçi (boş)
            0.0,  # Teklife Esas Bedel (varsayılan 0.0)
            0.0,  # Teklif Esas İşçilik (varsayılan 0.0)
            0.0,  # Teklif Toplam Tutarı (hesaplanacak)
            0.0,  # Malzeme Gerçek Bedeli (varsayılan 0.0)
            0.0,  # İşçilik Gerçek Bedeli (varsayılan 0.0)
            0.0,  # Proje Son Maliyet (hesaplanacak)
            0.0,  # Teklif Maliyet Farkı (hesaplanacak)
        ]

        # Arşiv bilgisi boş olarak başlatılabilir
        arsiv_info = {
            "Kullanıldığı_Proje": "",
            "Kullanıldığı_Tarih": "",
            "Tedarikçi": "",
            "Alış_Fiyatı": 0.0,
        }

        # dialog_instance'ın kendi poz_ekle metodunu çağır
        dialog_instance.poz_ekle(poz_object, data_to_add, arsiv_info)
        dialog_instance.lineEdit_ilave.clear()  # Poz ekledikten sonra lineEdit'i temizle
        QMessageBox.information(
            dialog_instance,
            "Poz Eklendi",
            f"'{Poz_No_to_add}' poz numarası tabloya eklendi.",
        )

    except sqlite3.Error as e:
        QMessageBox.critical(
            dialog_instance,
            "Veritabanı Hatası",
            f"Poz bilgisi çekilirken hata oluştu: {e}",
        )
    except Exception as e:
        QMessageBox.critical(
            dialog_instance, "Hata", f"Poz eklenirken beklenmeyen bir hata oluştu: {e}"
        )
