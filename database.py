import sqlite3
import os
import sys
from datetime import datetime
from PyQt6.QtWidgets import QMessageBox
import traceback
import pandas as pd


class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Veritabanına bağlanır veya hata durumunda uygulamadan çıkar."""
        try:
            db_dir = os.path.dirname(self.db_path)
            if not os.path.exists(db_dir):
                os.makedirs(db_dir)

            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            print(f"DEBUG: Veritabanına başarıyla bağlanıldı: {self.db_path}")
        except sqlite3.Error as e:
            QMessageBox.critical(
                None, "Veritabanı Bağlantı Hatası", f"Veritabanına bağlanılamadı: {e}"
            )
            print(f"DEBUG: Veritabanı bağlantı hatası: {e}")
            sys.exit(1)

    def _create_tables(self):
        """Gerekli veritabanı tablolarını oluşturur."""
        try:
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS pozlar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Poz_No TEXT NOT NULL UNIQUE,
                    Poz_Açıklaması TEXT,
                    Ölçü_Birimi TEXT,
                    Birim_Fiyat REAL
                )
            """
            )

            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS arsiv_detay (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Poz_No TEXT NOT NULL,
                    Poz_Açıklaması TEXT,
                    Kullanıldığı_Proje TEXT,
                    Kullanıldığı_Tarih TEXT,
                    Tedarikçi TEXT,
                    Alış_Fiyatı REAL,
                    FOREIGN KEY (Poz_No) REFERENCES pozlar(Poz_No)
                )
            """
            )

            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS proje_sablonu (
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
                )
            """
            )

            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS projeler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proje_adi TEXT NOT NULL UNIQUE
                )
                """
            )

            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cekler (
                    cek_no      TEXT PRIMARY KEY,
                    kesilme_trh TEXT,
                    vade        TEXT NOT NULL,
                    tutar       REAL NOT NULL,
                    alici       TEXT,
                    banka       TEXT,
                    resim_yolu  TEXT
                )
            """
            )
            self.cursor.execute(
                """
                CREATE TABLE  IF NOT EXISTS personel (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ad TEXT,
                    soyad TEXT,
                    telefon TEXT,
                    adres TEXT,
                    cinsiyet TEXT,
                    dogum_tarihi TEXT,
                    email TEXT,
                    email_sifre TEXT,
                    sifre_hash TEXT,
                    pozisyon TEXT,
                    baslangic_tarihi TEXT,
                    ayrilma_tarihi TEXT
                )
            """
            )

            try:
                self.cursor.execute("ALTER TABLE cekler ADD COLUMN resim_yolu TEXT;")
            except sqlite3.OperationalError as e:
                if "duplicate column name: resim_yolu" in str(e):
                    print("DEBUG: 'resim_yolu' sütunu zaten mevcut.")
                else:
                    raise e

            self.conn.commit()
            print("DEBUG: Tablolar başarıyla oluşturuldu veya zaten mevcut.")
        except sqlite3.Error as e:
            QMessageBox.critical(
                None,
                "Veritabanı Tablo Oluşturma Hatası",
                f"Tablolar oluşturulamadı: {e}",
            )
            print(f"DEBUG: Tablo oluşturma hatası: {e}")
            traceback.print_exc()
            sys.exit(1)

    def close_connection(self):
        """Veritabanı bağlantısını kapatır."""
        if self.conn:
            self.conn.close()
            print("DEBUG: Veritabanı bağlantısı kapatıldı.")

    def get_connection(self):
        """Veritabanı bağlantı nesnesini döndürür."""
        return self.conn

    def get_cursor(self):
        """Veritabanı imleç nesnesini döndürür."""
        return self.cursor

    def add_poz(self, Poz_No, Poz_Açıklaması, Ölçü_Birimi, Birim_Fiyat):
        """Yeni bir poz kaydı ekler."""
        try:
            self.cursor.execute(
                "INSERT INTO pozlar (Poz_No, Poz_Açıklaması, Ölçü_Birimi, Birim_Fiyat) VALUES (?, ?, ?, ?)",
                (Poz_No, Poz_Açıklaması, Ölçü_Birimi, Birim_Fiyat),
            )
            self.conn.commit()
            print(f"DEBUG: Poz '{Poz_No}' başarıyla eklendi.")
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(
                None,
                "Kayıt Hatası",
                f"'{Poz_No}' poz numarası zaten mevcut. Lütfen farklı bir numara girin.",
            )
            print(f"DEBUG: Poz '{Poz_No}' zaten mevcut hatası.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(
                None,
                "Veritabanı Hatası",
                f"Poz eklenirken beklenmeyen bir hata oluştu: {e}",
            )
            print(f"DEBUG: Poz ekleme hatası: {e}")
            traceback.print_exc()
            return False

    def update_poz(self, poz_id, Poz_No, Poz_Açıklaması, Ölçü_Birimi, Birim_Fiyat):
        """Mevcut bir poz kaydını günceller."""
        try:
            self.cursor.execute(
                "UPDATE pozlar SET Poz_No=?, Poz_Açıklaması=?, Ölçü_Birimi=?, Birim_Fiyat=? WHERE id=?",
                (Poz_No, Poz_Açıklaması, Ölçü_Birimi, Birim_Fiyat, poz_id),
            )
            self.conn.commit()
            print(f"DEBUG: Poz ID '{poz_id}' başarıyla güncellendi.")
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(
                None,
                "Güncelleme Hatası",
                f"'{Poz_No}' poz numarası zaten mevcut. Lütfen farklı bir numara girin.",
            )
            print(f"DEBUG: Poz '{Poz_No}' güncelleme - zaten mevcut hatası.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(
                None,
                "Veritabanı Hatası",
                f"Poz güncellenirken beklenmeyen bir hata oluştu: {e}",
            )
            print(f"DEBUG: Poz güncelleme hatası: {e}")
            traceback.print_exc()
            return False

    def delete_poz(self, poz_id):
        """Belirtilen ID'ye sahip poz kaydını siler."""
        try:
            self.cursor.execute("DELETE FROM pozlar WHERE id=?", (poz_id,))
            self.conn.commit()
            print(f"DEBUG: Poz ID '{poz_id}' başarıyla silindi.")
            return True
        except sqlite3.Error as e:
            QMessageBox.critical(
                None,
                "Veritabanı Hatası",
                f"Poz silinirken beklenmeyen bir hata oluştu: {e}",
            )
            print(f"DEBUG: Poz silme hatası: {e}")
            traceback.print_exc()
            return False

    def get_poz_by_no(self, Poz_No):
        """Poz numarasını kullanarak poz bilgisini getirir."""
        self.cursor.execute(
            "SELECT id, Poz_No, Poz_Açıklaması, Ölçü_Birimi, Birim_Fiyat FROM pozlar WHERE Poz_No=?",
            (Poz_No,),
        )
        return self.cursor.fetchone()

    def get_all_pozlar(self):
        """Tüm poz kayıtlarını getirir."""
        self.cursor.execute(
            "SELECT id, Poz_No, Poz_Açıklaması, Ölçü_Birimi, Birim_Fiyat FROM pozlar ORDER BY Poz_No ASC"
        )
        return self.cursor.fetchall()

    def add_arsiv_entry(
        self, Poz_No, Kullanıldığı_Proje, Kullanıldığı_Tarih, Tedarikçi, Alış_Fiyatı
    ):
        """Yeni bir arşiv girişi ekler."""
        try:
            poz_info = self.get_poz_by_no(Poz_No)
            if not poz_info:
                QMessageBox.warning(
                    None,
                    "Veri Hatası",
                    f"Poz '{Poz_No}' bulunamadı. Arşiv girişi eklenemedi.",
                )
                return False
            poz_aciklamasi = poz_info[2]

            self.cursor.execute(
                "INSERT INTO arsiv_detay (Poz_No, Poz_Açıklaması, Kullanıldığı_Proje, Kullanıldığı_Tarih, Tedarikçi, Alış_Fiyatı) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    Poz_No,
                    poz_aciklamasi,
                    Kullanıldığı_Proje,
                    Kullanıldığı_Tarih,
                    Tedarikçi,
                    Alış_Fiyatı,
                ),
            )
            self.conn.commit()
            print(f"DEBUG: Arşiv girişi poz '{Poz_No}' için başarıyla eklendi.")
            return True
        except sqlite3.Error as e:
            QMessageBox.critical(
                None, "Veritabanı Hatası", f"Arşiv girişi eklenirken hata oluştu: {e}"
            )
            print(f"DEBUG: Arşiv girişi ekleme hatası: {e}")
            traceback.print_exc()
            return False

    def get_highest_Alış_Fiyatı_from_arsiv(self, Poz_No):
        """
        Belirtilen Poz_No için arşivdeki en yüksek alış bedeline sahip kaydın tüm detaylarını getirir.
        """
        try:
            self.cursor.execute(
                """
                SELECT Kullanıldığı_Proje, Kullanıldığı_Tarih, Tedarikçi, Alış_Fiyatı
                FROM arsiv_detay
                WHERE Poz_No = ?
                ORDER BY Alış_Fiyatı DESC
                LIMIT 1
            """,
                (Poz_No,),
            )

            result = self.cursor.fetchone()

            if result:
                arsiv_data = {
                    "Kullanıldığı_Proje": result[0],
                    "Kullanıldığı_Tarih": result[1],
                    "Tedarikçi": result[2],
                    "Alış_Fiyatı": result[3],
                }
                print(
                    f"DEBUG: Poz '{Poz_No}' için arşivde en yüksek alış bedeli detayları bulundu: {arsiv_data}"
                )
                return arsiv_data
            else:
                print(
                    f"DEBUG: Poz '{Poz_No}' için arşivde en yüksek alış bedeli bulunamadı."
                )
                return {}
        except sqlite3.Error as e:
            QMessageBox.critical(
                None,
                "Veritabanı Sorgu Hatası",
                f"Poz '{Poz_No}' için arşiv bilgisi sorgulanırken hata oluştu: {e}",
            )
            print(f"DEBUG: get_highest_Alış_Fiyatı_from_arsiv hatası: {e}")
            traceback.print_exc()
            return {}

    def save_project_entry(self, poz_info, project_entry, arsiv_info, table_name):
        """
        Proje tablosuna yeni bir poz kaydı ekler veya mevcut bir poz kaydını günceller.
        """
        try:
            columns = [
                "Poz_No",
                "Poz_Açıklaması",
                "Ölçü_Birimi",
                "Birim_Fiyat",
                "Kullanıldığı_Proje",
                "Kullanıldığı_Tarih",
                "Tedarikçi",
                "Alış_Fiyatı",
                "Yeni_Proje_Adı",
                "Yeni_Proje_Tarihi",
                "Yeni_Tedarikçi",
                "Metraj",
                "Yaklaşık_İşçilik",
                "Yaklaşık_Maliyet",
                "Teklif_Fiyat",
                "Teklif_İşçilik",
                "Teklif_Maliyet",
                "Gerçek_Fiyat",
                "Gerçek_İşçilik",
                "Gerçek_Maliyet",
            ]

            values = [
                poz_info.get("no"),
                poz_info.get("tanim"),
                poz_info.get("birim"),
                poz_info.get("bedel"),
                arsiv_info.get("Kullanıldığı_Proje"),
                arsiv_info.get("Kullanıldığı_Tarih"),
                arsiv_info.get("Tedarikçi"),
                arsiv_info.get("Alış_Fiyatı"),
                project_entry.get("Yeni_Proje_Adı"),
                project_entry.get("Yeni_Proje_Tarihi"),
                project_entry.get("Yeni_Tedarikçi"),
                project_entry.get("Metraj"),
                project_entry.get("Yaklaşık_İşçilik"),
                project_entry.get("Yaklaşık_Maliyet"),
                project_entry.get("Teklif_Fiyat"),
                project_entry.get("Teklif_İşçilik"),
                project_entry.get("Teklif_Maliyet"),
                project_entry.get("Gerçek_Fiyat"),
                project_entry.get("Gerçek_İşçilik"),
                project_entry.get("Gerçek_Maliyet"),
            ]

            cols_str = ", ".join(columns)
            placeholders = ", ".join(["?" for _ in columns])

            update_set_parts = []
            update_values_for_set = []
            for i, col in enumerate(columns):
                if col != "Poz_No":
                    update_set_parts.append(f"{col} = ?")
                    update_values_for_set.append(values[i])

            update_set_str = ", ".join(update_set_parts)

            sql = f"""
            INSERT INTO {table_name} ({cols_str})
            VALUES ({placeholders})
            ON CONFLICT(Poz_No) DO UPDATE SET
                {update_set_str}
            WHERE Poz_No = ?;
            """
            final_values = values + update_values_for_set + [poz_info.get("no")]

            self.cursor.execute(sql, final_values)
            self.conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(f"DEBUG: Proje kaydı ekleme/güncelleme hatası (IntegrityError): {e}")
            traceback.print_exc()
            return False
        except Exception as e:
            print(f"DEBUG: Proje kaydı kaydederken genel hata: {e}")
            traceback.print_exc()
            return False

    def archive_project_data(self, project_table_name):
        """
        Belirtilen proje tablosundaki verileri arsiv_detay tablosuna taşır.
        """
        try:
            self.cursor.execute(
                f"""
                SELECT
                    Poz_No,
                    Poz_Açıklaması,
                    Yeni_Proje_Adı AS Kullanıldığı_Proje,
                    Yeni_Proje_Tarihi AS Kullanıldığı_Tarih,
                    Yeni_Tedarikçi AS Tedarikçi,
                    Gerçek_Fiyat AS Alış_Fiyatı
                FROM {project_table_name};
            """
            )
            project_rows = self.cursor.fetchall()

            if not project_rows:
                print(
                    f"DEBUG: '{project_table_name}' tablosunda arşivlenecek veri bulunamadı."
                )
                return True

            sql = """
            INSERT OR REPLACE INTO arsiv_detay (
                Poz_No,
                Poz_Açıklaması,
                Kullanıldığı_Proje,
                Kullanıldığı_Tarih,
                Tedarikçi,
                Alış_Fiyatı
            )
            VALUES (?, ?, ?, ?, ?, ?);
            """
            self.cursor.executemany(sql, project_rows)
            self.conn.commit()
            print(
                f"DEBUG: Proje '{project_table_name}' verileri arsiv_detay'a başarıyla taşındı."
            )
            return True
        except sqlite3.Error as e:
            print(f"Proje verileri arşivlenirken hata: {e}")
            traceback.print_exc()
            return False
        except Exception as e:
            print(f"Proje arşivlenirken beklenmeyen hata: {e}")
            traceback.print_exc()
            return False

    def delete_project_table(self, table_name):
        """Belirtilen proje tablosunu veritabanından siler."""
        try:
            self.cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
            self.conn.commit()
            print(f"DEBUG: Proje tablosu '{table_name}' başarıyla silindi.")
            return True
        except sqlite3.Error as e:
            print(f"Proje tablosu silinirken hata: {e}")
            traceback.print_exc()
            return False

    def get_project_table_names(self):
        """
        Veritabanındaki tüm proje tablolarının isimlerini döndürür.
        """
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            all_tables = [row[0] for row in self.cursor.fetchall()]

            system_tables = ["sqlite_sequence"]
            app_specific_tables = ["pozlar", "arsiv_detay", "proje_sablonu", "cekler"]

            project_tables = [
                table
                for table in all_tables
                if table not in system_tables and table not in app_specific_tables
            ]
            print(f"DEBUG: Bulunan proje tabloları: {project_tables}")
            return project_tables
        except sqlite3.Error as e:
            print(f"DEBUG: Proje tablosu isimleri çekilirken hata oluştu: {e}")
            traceback.print_exc()
            return []

    def get_project_cost_data_for_table(self, table_name):
        """
        Belirtilen proje tablosundan maliyet analizi için gerekli verileri çeker.
        """
        try:
            query = f"""
            SELECT
                Poz_No,
                Teklif_Maliyet,
                Gerçek_Maliyet
            FROM {table_name};
            """
            df = pd.read_sql_query(query, self.conn)
            df["Proje_Tablo_Adı"] = table_name
            return df
        except pd.io.sql.DatabaseError as e:
            print(f"DEBUG: '{table_name}' tablosundan veri çekilirken hata oluştu: {e}")
            print(f"DEBUG: Sorgu: {query}")
            traceback.print_exc()
            return pd.DataFrame()
        except Exception as e:
            print(
                f"DEBUG: '{table_name}' tablosundan veri çekilirken beklenmeyen hata: {e}"
            )
            traceback.print_exc()
            return pd.DataFrame()

    def add_cek(self, cek_no, kesilme_trh, vade, tutar, alici, banka, resim_yolu=None):
        """Yeni bir çek kaydı ekler."""
        try:
            self.cursor.execute(
                "INSERT INTO cekler (cek_no, kesilme_trh, vade, tutar, alici, banka, resim_yolu) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (cek_no, kesilme_trh, vade, tutar, alici, banka, resim_yolu),
            )
            self.conn.commit()
            print(f"DEBUG: Çek '{cek_no}' başarıyla eklendi.")
            return True
        except sqlite3.IntegrityError:
            QMessageBox.warning(
                None,
                "Kayıt Hatası",
                f"'{cek_no}' çek numarası zaten mevcut. Lütfen farklı bir numara girin.",
            )
            print(f"DEBUG: Çek '{cek_no}' zaten mevcut hatası.")
            return False
        except sqlite3.Error as e:
            QMessageBox.critical(
                None,
                "Veritabanı Hatası",
                f"Çek eklenirken beklenmeyen bir hata oluştu: {e}",
            )
            print(f"DEBUG: Çek ekleme hatası: {e}")
            traceback.print_exc()
            return False

    def delete_cek(self, cek_no):
        """Belirtilen çek numarasına sahip çeki veritabanından siler."""
        try:
            self.cursor.execute("DELETE FROM cekler WHERE cek_no = ?", (cek_no,))
            self.conn.commit()
            print(f"DEBUG: Çek '{cek_no}' başarıyla silindi.")
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            QMessageBox.critical(
                None,
                "Veritabanı Hatası",
                f"Çek silinirken beklenmeyen bir hata oluştu: {e}",
            )
            print(f"DEBUG: Çek silme hatası: {e}")
            traceback.print_exc()
            return False

    def get_all_cekler(self):
        """Tüm çek kayıtlarını veritabanından çeker."""
        try:
            self.cursor.execute(
                "SELECT cek_no, kesilme_trh, vade, tutar, alici, banka, resim_yolu FROM cekler ORDER BY vade ASC"
            )
            columns = [description[0] for description in self.cursor.description]
            rows = self.cursor.fetchall()
            cekler_data = []
            for row in rows:
                cekler_data.append(dict(zip(columns, row)))
            print(f"DEBUG: Veritabanından {len(cekler_data)} adet çek çekildi.")
            return cekler_data
        except sqlite3.Error as e:
            print(f"DEBUG: Çekler çekilirken hata oluştu: {e}")
            traceback.print_exc()
            return []

    # Yeni eklenen metotlar
    def add_project(self, proje_adi):
        """Yeni bir proje adını projeler tablosuna ekler."""
        try:
            self.cursor.execute(
                "INSERT INTO projeler (proje_adi) VALUES (?)", (proje_adi,)
            )
            self.conn.commit()
            print(f"DEBUG: Proje '{proje_adi}' başarıyla eklendi.")
            return True
        except sqlite3.IntegrityError:
            print(f"DEBUG: Proje '{proje_adi}' zaten mevcut.")
            return False
        except sqlite3.Error as e:
            print(f"DEBUG: Proje ekleme hatası: {e}")
            traceback.print_exc()
            return False

    def get_all_projects(self):
        """Projeler tablosundaki tüm proje adlarını döndürür."""
        try:
            self.cursor.execute("SELECT proje_adi FROM projeler ORDER BY proje_adi")
            rows = self.cursor.fetchall()
            proje_listesi = [row[0] for row in rows]
            print(f"DEBUG: {len(proje_listesi)} adet proje adı çekildi.")
            return proje_listesi
        except sqlite3.Error as e:
            print(f"DEBUG: Proje adları çekilirken hata oluştu: {e}")
            traceback.print_exc()
            return []

    def delete_project(self, proje_adi):
        """Belirtilen proje adını projeler tablosundan siler."""
        try:
            self.cursor.execute(
                "DELETE FROM projeler WHERE proje_adi = ?", (proje_adi,)
            )
            self.conn.commit()
            print(f"DEBUG: Proje '{proje_adi}' projeler tablosundan silindi.")
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"DEBUG: Proje silme hatası: {e}")
            traceback.print_exc()
            return False

    def kullanici_ekle(
        self,
        ad,
        soyad,
        telefon,
        adres,
        cinsiyet,
        dogum_tarihi,
        email,
        email_sifre,
        sifre_hash,
        pozisyon,
        baslangic_tarihi,
        ayrilma_tarihi,
    ):
        try:
            self.cursor.execute(
                """
                INSERT INTO personel 
                (ad, soyad, telefon, adres, cinsiyet, dogum_tarihi, email, email_sifre, sifre_hash, pozisyon, baslangic_tarihi, ayrilma_tarihi)
                
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ad,
                    soyad,
                    telefon,
                    adres,
                    cinsiyet,
                    dogum_tarihi,
                    email,
                    email_sifre,
                    sifre_hash,
                    pozisyon,
                    baslangic_tarihi,
                    ayrilma_tarihi,
                ),
            )
            self.conn.commit()
            print("Kullanıcı başarıyla eklendi.")
            return True
        except sqlite3.Error as e:
            print(f"Veritabanı hatası: {e}")
            return False

    def kullanici_getir(self, ad):
        cursor = self.conn.execute(
            "SELECT * FROM personel WHERE ad = ?",
            (ad,),
        )
        kayit = cursor.fetchone()
        print("Kayıt:", kayit)  # artık return'den önce
        return kayit
        if kayit is None:
            print("Kullanıcı bulunamadı:", ad)

    def personel_listesi_al(self):
        """Veritabanındaki tüm personel kayıtlarını listeler"""
        self.cursor.execute(
            """
            SELECT ad, soyad, telefon, adres, cinsiyet, 
            dogum_tarihi, email, pozisyon, 
            baslangic_tarihi, ayrilma_tarihi
            FROM personel
        """
        )
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
