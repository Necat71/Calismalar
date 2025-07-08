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
                None,
                "Veritabanı Hatası",
                f"Arşiv girişi eklenirken hata oluştu: {e}"
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
            ]

            # Dinamik tablo adı ile sorguyu hazırla
            placeholders = ", ".join(["?"] * len(columns))
            column_names = ", ".join(columns)
            update_set = ", ".join([f"{col}=?" for col in columns])

            # Poz_No'ya göre varlığını kontrol et
            self.cursor.execute(
                f"SELECT Poz_No FROM {table_name} WHERE Poz_No=?", (poz_info.get("no"),)
            )
            existing_poz = self.cursor.fetchone()

            if existing_poz:
                # Güncelleme
                self.cursor.execute(
                    f"UPDATE {table_name} SET {update_set} WHERE Poz_No=?",
                    values + [poz_info.get("no")],
                )
                print(
                    f"DEBUG: '{table_name}' tablosunda Poz '{poz_info.get('no')}' güncellendi."
                )
            else:
                # Ekleme
                self.cursor.execute(
                    f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})",
                    values,
                )
                print(
                    f"DEBUG: '{table_name}' tablosuna Poz '{poz_info.get('no')}' eklendi."
                )

            self.conn.commit()
            return True
        except sqlite3.Error as e:
            QMessageBox.critical(
                None, "Veritabanı Hatası", f"Proje girişi kaydedilirken hata oluştu: {e}"
            )
            print(f"DEBUG: Proje girişi kaydetme hatası: {e}")
            traceback.print_exc()
            return False

    def get_project_table_names(self):
        """Veritabanındaki tüm proje tablosu adlarını döndürür."""
        try:
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'proje_%'"
            )
            tables = self.cursor.fetchall()
            return [table[0] for table in tables]
        except sqlite3.Error as e:
            QMessageBox.critical(
                None, "Veritabanı Hatası", f"Proje tabloları alınamadı: {e}"
            )
            print(f"DEBUG: Proje tablo adlarını alma hatası: {e}")
            return []

    def get_project_cost_data_for_table(self, table_name):
        """Belirtilen proje tablosundan maliyet verilerini çeker ve DataFrame olarak döndürür."""
        try:
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql_query(query, self.conn)
            print(f"DEBUG: '{table_name}' tablosundan {len(df)} satır veri çekildi.")
            return df
        except pd.io.sql.DatabaseError as e:
            QMessageBox.warning(
                None,
                "Veri Okuma Hatası",
                f"'{table_name}' tablosu okunurken hata oluştu veya tablo bulunamadı: {e}",
            )
            print(f"DEBUG: get_project_cost_data_for_table hatası: {e}")
            return pd.DataFrame()
        except Exception as e:
            QMessageBox.critical(
                None,
                "Beklenmeyen Hata",
                f"'{table_name}' tablosu verileri alınırken beklenmeyen bir hata oluştu: {e}",
            )
            print(f"DEBUG: get_project_cost_data_for_table beklenmeyen hata: {e}")
            traceback.print_exc()
            return pd.DataFrame()
            
    # database.py dosyası içinde, DatabaseManager sınıfının altında:

    def delete_project_table(self, table_name):
        """Belirtilen proje tablosunu veritabanından siler."""
        try:
            self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.conn.commit()
            print(f"DEBUG: Tablo '{table_name}' başarıyla silindi (veritabanı komutu).")

            # --- EKLENECEK KOD BAŞLANGICI ---
            # Tablonun gerçekten silinip silinmediğini kontrol et
            self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            exists = self.cursor.fetchone()
            if exists:
                print(f"DEBUG HATA: Tablo '{table_name}' silindiği bilgisine rağmen hala veritabanında mevcut.")
                return False  # Silinmediği için False döndür
            else:
                print(f"DEBUG: Tablo '{table_name}' veritabanından BAŞARILI BİR ŞEKİLDE silindiği doğrulandı.")
            # --- EKLENECEK KOD SONU ---

            return True
        except sqlite3.Error as e:
            QMessageBox.critical(
                None, "Veritabanı Hatası", f"Proje tablosu silinirken hata oluştu: {e}"
            )
            print(f"DEBUG: Proje tablosu silinirken hata: {e}")
            traceback.print_exc()
            return False
        except Exception as e:
            QMessageBox.critical(
                None, "Beklenmeyen Hata", f"Proje tablosu silinirken beklenmeyen bir hata oluştu: {e}"
            )
            print(f"DEBUG: Proje tablosu silinirken beklenmeyen bir hata oluştu: {e}")
            traceback.print_exc()
            return False

    def add_cek(self, cek_no, kesilme_trh, vade, tutar, alici, banka, resim_yolu):
        """Çek bilgilerini cekler tablosuna ekler."""
        try:
            self.cursor.execute(
                """
                INSERT INTO cekler (cek_no, kesilme_trh, vade, tutar, alici, banka, resim_yolu)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (cek_no, kesilme_trh, vade, tutar, alici, banka, resim_yolu)
            )
            self.conn.commit()
            print(f"Çek {cek_no} başarıyla veritabanına eklendi.")
            return True
        except Exception as e:
            print(f"Çek eklenirken hata oluştu: {e}")
            traceback.print_exc()
            return False

    def get_all_cekler(self):
        """Veritabanındaki tüm çekleri döndürür."""
        try:
            self.cursor.execute("SELECT cek_no, kesilme_trh, vade, tutar, alici, banka, resim_yolu FROM cekler")
            rows = self.cursor.fetchall()
            ceks_data = []
            for row in rows:
                ceks_data.append({
                    "cek_no": row[0],
                    "kesilme_trh": datetime.strptime(row[1], "%Y-%m-%d").date() if isinstance(row[1], str) else row[1],
                    "vade": datetime.strptime(row[2], "%Y-%m-%d").date() if isinstance(row[2], str) else row[2],
                    "tutar": row[3],
                    "alici": row[4],
                    "banka": row[5],
                    "resim": row[6],
                    "uyarildi": False  # Bu alan veritabanında tutulmayıp kod tarafında yönetilir
                })
            return ceks_data
        except Exception as e:
            print(f"Çekler çekilirken hata oluştu: {e}")
            traceback.print_exc()
            return []

    def delete_cek(self, cek_no):
        """Belirtilen çek numarasıyla çeki veritabanından siler."""
        try:
            self.cursor.execute("DELETE FROM cekler WHERE cek_no = ?", (cek_no,))
            self.conn.commit()
            print(f"Çek {cek_no} başarıyla veritabanından silindi.")
            return True
        except Exception as e:
            print(f"Çek silinirken hata oluştu: {e}")
            traceback.print_exc()
            return False
            
    def get_all_cekler(self):
        """Tüm çek kayıtlarını veritabanından çeker."""
        try:
            self.cursor.execute("SELECT cek_no, kesilme_trh, vade, tutar, alici, banka, resim_yolu FROM cekler ORDER BY vade ASC")
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
            
    def kullanici_ekle(self, kullanici_adi, email, sifre_hash, email_sifre=None):
        self.conn.execute(
            "INSERT INTO kullanicilar_tablosu (kullanici_adi, email, email_sifre, sifre_hash) VALUES (?, ?, ?, ?)",
            (kullanici_adi, email, email_sifre, sifre_hash),
        )
        self.conn.commit()

    def kullanici_dogrula(self, kullanici_adi, sifre_hash):
        self.cursor.execute(
            "SELECT * FROM kullanicilar_tablosu WHERE kullanici_adi=? AND sifre_hash=?",
            (kullanici_adi, sifre_hash),
        )
        return self.cursor.fetchone()

    def get_user_email_sifre(self, kullanici_adi):
        self.cursor.execute(
            "SELECT email_sifre FROM kullanicilar_tablosu WHERE kullanici_adi=?",
            (kullanici_adi,),
        )
        result = self.cursor.fetchone()
        return result[0] if result else None

    def update_user_email_sifre(self, kullanici_adi, yeni_sifre):
        self.cursor.execute(
            "UPDATE kullanicilar_tablosu SET email_sifre = ? WHERE kullanici_adi = ?",
            (yeni_sifre, kullanici_adi),
        )
        self.conn.commit()
        
    def kullanici_ekle(self, kullanici_adi, email, sifre_hash, email_sifre=None):
        self.conn.execute(
            "INSERT INTO kullanicilar_tablosu (kullanici_adi, email, email_sifre, sifre_hash) VALUES (?, ?, ?, ?)",
            (kullanici_adi, email, email_sifre, sifre_hash)
        )
        self.conn.commit()

    def kullanici_getir(self, kullanici_adi):
        cursor = self.conn.execute("SELECT * FROM kullanicilar_tablosu WHERE kullanici_adi = ?", (kullanici_adi,))
        # Aşağıdaki print ifadesi orijinal dosyada yanlış girintilenmişti, eğer amaçlandıysa metodun mantığının bir parçası olmalıydı.
        # Bu düzeltme için, hata ayıklama amacıyla metodun bir parçası olduğu varsayılmaktadır.
        kayit = cursor.fetchone()
        print("Kayıt:", kayit)
        return kayit
