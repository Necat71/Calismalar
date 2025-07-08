import pandas as pd


def safe_float_conversion(value):
    """Gelen değeri güvenli bir şekilde float'a çevirir."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return 0.0
    return 0.0


def calculate_percentage_difference(actual, budget):
    """İki değer arasındaki yüzde farkını hesaplar."""
    if budget == 0:
        return 0.0
    return ((actual - budget) / budget) * 100


def get_data_as_dataframe(db_cursor, table_name):
    """Belirli bir tablodan tüm verileri Pandas DataFrame olarak çeker."""
    db_cursor.execute(f"SELECT * FROM {table_name}")
    data = db_cursor.fetchall()
    columns = [description[0] for description in db_cursor.description]
    return pd.DataFrame(data, columns=columns)
