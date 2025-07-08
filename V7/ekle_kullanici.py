from database import DatabaseManager
from utils.sifreleme import sifre_hashle
from config import DB_FILE

# Veritabanı bağlantısı
db = DatabaseManager(str(DB_FILE))

# Örnek kullanıcı bilgileri
kullanici_adi = "admin"
email = "admin@example.com"
sifre = "123456"

# Şifreyi hash'le
sifre_hash = sifre_hashle(sifre)

# Kullanıcıyı ekle
try:
    db.kullanici_ekle(kullanici_adi, email, sifre_hash)
    print("✅ Kullanıcı başarıyla eklendi.")
except Exception as e:
    print(f"⚠️ Kullanıcı eklenemedi: {e}")

