import bcrypt

def sifre_dogrula(girilen_sifre, kayitli_hash):
    if isinstance(kayitli_hash, str):
        kayitli_hash = kayitli_hash.encode()
    return bcrypt.checkpw(girilen_sifre.encode(), kayitli_hash)

