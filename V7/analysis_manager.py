

import pandas as pd
from PyQt6.QtWidgets import (
    QMessageBox,
)  # UI elementlerine bağımlı olmak istemiyorsak bunu kaldırıp, sadece loglama yapabiliriz
import traceback  # Hata takibi için




class AnalysisManager:
    """
    Uygulamanın çeşitli analiz fonksiyonlarını yöneten sınıf.
    Veritabanı erişimi ve veri çekme fonksiyonları için callback'ler alır.
    """

    def __init__(
        self,
        db_instance,
        get_project_data_func,
        get_arsiv_data_func,
        parent_widget=None,
    ):
        self.db = db_instance
        self._get_common_project_data = get_project_data_func
        self._get_arsiv_data_for_analysis = get_arsiv_data_func
        self.parent_widget = (
            parent_widget  # QMessageBox'lar için parent belirtmek gerekirse
        )

    def _show_message(self, title, message, icon=QMessageBox.Icon.Information, e=None):
        """Genel bir mesaj kutusu göstermek için yardımcı metod."""
        msg_box = QMessageBox(self.parent_widget)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.exec()
        if e:
            print(f"Hata [{title}]: {e}")
            traceback.print_exc()

    def run_teklif_maliyet_analizi(self):
        """Teklif Maliyet Farkı Analizi'ni çalıştırır ve raporunu sadece proje bazında gösterir."""
        df_project = self._get_common_project_data()
        if df_project.empty:
            self._show_message(
                "Bilgi",
                "Analiz için proje verisi bulunamadı.",
                QMessageBox.Icon.Information,
            )
            return

        required_cols = [
            "Poz_No",
            "Teklif_Maliyeti",
            "Gerçek_Maliyet",
            "Proje_Tablo_Adı",
        ]
        if not all(col in df_project.columns for col in required_cols):
            self._show_message(
                "Veri Hatası",
                f"Teklif/Maliyet Analizi için gerekli sütunlar ({', '.join(required_cols)}) bulunamadı. Lütfen veritabanı şemasını ve proje verilerini kontrol edin.",
                QMessageBox.icon.warning,
            )
            return

        try:  # Try bloğu burada başlamalı
            results = Teklif_Maliyet_Analizi(df_project.copy())

            custom_dfs = {
                "Genel Özet": pd.DataFrame(
                    {
                        "Tüm Projeler Toplam Fark": [results["toplam_fark"]],
                        "Tüm Projeler Sapma Yüzdesi (%)": [
                            results["genel_sapma_yuzdesi"]
                        ],
                    }
                ),
                "Proje Bazlı Özet": results["proje_bazli_ozet"],
            }

            pdf_path = create_excel_report(
                "Teklif ve Gerçek Maliyet Analizi",
                [],  # content_list boş bırakıldı, custom_dataframes kullanılıyor
                suggested_filename="Teklif_Maliyet_Analizi_Raporu.xlsx",
                parent_window=self.parent_widget,  # UI'dan gelen parent_widget'ı buraya ilettik
                custom_dataframes=custom_dfs,
            )

            if pdf_path:
                self._show_message(
                    "Analiz Tamamlandı",
                    f"Rapor oluşturuldu:\n{pdf_path}",
                    QMessageBox.Icon.Information,
                )
            else:
                self._show_message(
                    "Rapor Oluşturulamadı",
                    "Teklif Maliyet Analizi raporu oluşturulamadı.",
                    QMessageBox.Warning,
                )

        except KeyError as e:
            self._show_message(
                "Veri veya Anahtar Hatası",
                f"Analiz sonuçlarında beklenen anahtar bulunamadı: '{e}'. Lütfen Teklif_Maliyet_Analizi.py dosyasını kontrol edin.",
                QMessageBox.Warning,
                e,
            )
        except ValueError as e:
            self._show_message(
                "Sayısal Dönüşüm Hatası",
                f"Veri işlenirken sayısal dönüşüm hatası oluştu: {e}. Verilerde geçersiz karakterler olabilir.",
                QMessageBox.Warning,
                e,
            )
        except Exception as e:
            self._show_message(
                "Genel Analiz Hatası",
                f"Beklenmeyen bir hata oluştu: {e}",
                QMessageBox.icon.warning,
                e,
            )

    def run_kar_zarar_analizi(self):
        """Kar/Zarar Analizi'ni çalıştırır ve raporunu oluşturur."""
        df_project = self._get_common_project_data()
        if df_project.empty:
            self._show_message(
                "Bilgi",
                "Analiz için proje verisi bulunamadı.",
                QMessageBox.Icon.Information,
            )
            return

        required_cols_for_kar_zarar = [
            "Proje_Tablo_Adı",
            "Poz_No",
            "Teklif_Maliyeti",
            "Gerçek_Maliyet",
        ]
        if not all(col in df_project.columns for col in required_cols_for_kar_zarar):
            self._show_message(
                "Veri Hatası",
                f"Kar-Zarar Analizi için gerekli sütunlar ({', '.join(required_cols_for_kar_zarar)}) bulunamadı. Lütfen veritabanı şemasını ve proje verilerini kontrol edin.",
                QMessageBox.Warning,
            )
            return

        try:
            results = Kar_Zarar_Analizi(df_project.copy())

            custom_dfs = {
                "Genel Kar-Zarar Ozeti": pd.DataFrame(
                    {"Toplam Kar/Zarar": [results["toplam_kar_zarar"]]}
                ),
                "Poz Bazli Kar-Zarar": results["poz_bazli_kar_zarar"],
            }

            if not results["en_karli_poz"].empty:
                custom_dfs["En Karli Poz"] = results["en_karli_poz"][
                    ["Proje_Tablo_Adı", "Poz_No", "Poz_Açıklaması", "Kar_Zarar"]
                ]
            if not results["en_zararli_poz"].empty:
                custom_dfs["En Zararli Poz"] = results["en_zararli_poz"][
                    ["Proje_Tablo_Adı", "Poz_No", "Poz_Açıklaması", "Kar_Zarar"]
                ]

            pdf_path = create_excel_report(
                "Kar-Zarar Analizi",
                [],
                suggested_filename="Kar_Zarar_Analizi_Raporu.xlsx",
                parent_window=self.parent_widget,
                custom_dataframes=custom_dfs,
            )

            if pdf_path:
                self._show_message(
                    "Analiz Tamamlandı",
                    f"Rapor oluşturuldu:\n{pdf_path}",
                    QMessageBox.Icon.Information,
                )
            else:
                self._show_message(
                    "Rapor Oluşturulamadı",
                    "Kar-Zarar Analizi raporu oluşturulamadı.",
                    QMessageBox.Warning,
                )

        except KeyError as e:
            self._show_message(
                "Veri veya Anahtar Hatası",
                f"Kar-Zarar Analizi sırasında hata oluştu: '{e}'. Lütfen Kar_Zarar_Analizi.py dosyasını veya veri sütunlarını kontrol edin.",
                QMessageBox.Warning,
                e,
            )
        except ValueError as e:
            self._show_message(
                "Sayısal Dönüşüm Hatası",
                f"Kar-Zarar Analizi sırasında sayısal dönüşüm hatası oluştu: {e}. Verilerde geçersiz karakterler olabilir.",
                QMessageBox.Warning,
                e,
            )
        except Exception as e:
            self._show_message(
                "Analiz Hatası",
                f"Kar-Zarar Analizi sırasında beklenmeyen hata oluştu: {e}",
                QMessageBox.Warning,
                e,
            )

    def run_risk_analysis(self):
        df_project = self._get_common_project_data()
        if df_project.empty:
            self._show_message(
                "Bilgi",
                "Analiz için proje verisi bulunamadı.",
                QMessageBox.Icon.Information,
            )
            return

        # Eğer df_project'te 'teklif_maliyet_farki' yoksa oluşturalım:
        if "teklif_maliyet_farki" not in df_project.columns:
            df_project["teklif_maliyet_farki"] = (
                df_project["Gerçek_Maliyet"] - df_project["Teklif_Maliyeti"]
            )

        required_cols = [
            "Poz_No",
            "Teklif_Maliyeti",
            "Gerçek_Maliyeti",
            "teklif_maliyet_farki",
        ]
        if not all(col in df_project.columns for col in required_cols):
            self._show_message(
                "Veri Hatası",
                f"Risk Analizi için gerekli sütunlar ({', '.join(required_cols)}) bulunamadı.",
                QMessageBox.Warning,
            )
            return

        try:
            results = analyze_risk_areas(df_project.copy())

            custom_dfs = {}
            if not results["riskli_pozlar"].empty:
                custom_dfs["Riskli Pozlar"] = results["riskli_pozlar"]

            pdf_path = create_excel_report(
                "Risk Analizi",
                [],
                suggested_filename="Risk_Analizi_Raporu.xlsx",
                parent_window=self.parent_widget,
                custom_dataframes=custom_dfs,
            )

            if pdf_path:
                self._show_message(
                    "Analiz Tamamlandı",
                    f"Risk Analizi başarıyla tamamlandı. Rapor kaydedildi:\n{pdf_path}",
                    QMessageBox.Icon.Information,
                )
            else:
                self._show_message(
                    "Rapor Oluşturulamadı",
                    "Risk Analizi raporu oluşturulamadı.",
                    QMessageBox.Warning,
                )

        except Exception as e:
            self._show_message(
                "Analiz Hatası",
                f"Risk Analizi sırasında hata oluştu: {e}",
                QMessageBox.Warning,
                e,
            )

    def run_supplier_performance_analysis(self):
        df_arsiv = self._get_arsiv_data_for_analysis()
        if df_arsiv.empty:
            self._show_message(
                "Bilgi",
                "Analiz için arşiv verisi bulunamadı.",
                QMessageBox.Icon.Information,
            )
            return

        required_cols_map = {
            "Tedarikçi": "yeni_tedarikci",
            "Alış_Fiyatı": "alis_bedeli",
            "Miktar": "alinacak_miktar",
        }

        df_arsiv_renamed = df_arsiv.rename(columns=required_cols_map)

        if not all(
            col in df_arsiv_renamed.columns for col in required_cols_map.values()
        ):
            self._show_message(
                "Veri Hatası",
                f"Tedarikçi Performans Analizi için gerekli sütunlar ({', '.join(required_cols_map.keys())}) bulunamadı veya dönüştürülemedi.",
                QMessageBox.Warning,
            )
            return

        try:
            results = analyze_supplier_performance(df_arsiv_renamed.copy())

            custom_dfs = {
                "Tedarikci Ozeti": results["supplier_summary"],
                "En Iyi Tedarikciler": results["best_suppliers"],
                "En Kotu Tedarikciler": results["worst_suppliers"],
            }

            pdf_path = create_excel_report(
                "Tedarikçi Performans Analizi",
                [],
                suggested_filename="Tedarikci_Performans_Analizi_Raporu.xlsx",
                parent_window=self.parent_widget,
                custom_dataframes=custom_dfs,
            )

            if pdf_path:
                self._show_message(
                    "Analiz Tamamlandı",
                    f"Tedarikçi Performans Analizi başarıyla tamamlandı. Rapor kaydedildi:\n{pdf_path}",
                    QMessageBox.Icon.Information,
                )
            else:
                self._show_message(
                    "Rapor Oluşturulamadı",
                    "Tedarikçi Performans Analizi raporu oluşturulamadı.",
                    QMessageBox.Warning,
                )
        except Exception as e:
            self._show_message(
                "Analiz Hatası",
                f"Tedarikçi Performans Analizi sırasında hata oluştu: {e}",
                QMessageBox.Warning,
                e,
            )

    def run_historical_price_analysis(self):
        df_arsiv = self._get_arsiv_data_for_analysis()
        if df_arsiv.empty:
            self._show_message(
                "Bilgi",
                "Analiz için arşiv verisi bulunamadı.",
                QMessageBox.Icon.Information,
            )
            return

        required_cols_map = {
            "Poz_No": "poz_no",
            "Kullanıldığı_Tarih": "kullanildigi_tarih",
            "Alış_Fiyatı": "alis_bedeli",
        }

        df_arsiv_renamed = df_arsiv.rename(columns=required_cols_map)

        if not all(
            col in df_arsiv_renamed.columns for col in required_cols_map.values()
        ):
            self._show_message(
                "Veri Hatası",
                f"Tarihsel Fiyat Analizi için gerekli sütunlar ({', '.join(required_cols_map.keys())}) bulunamadı veya dönüştürülemedi.",
                QMessageBox.Warning,
            )
            return

        try:
            results = analyze_historical_prices(df_arsiv_renamed.copy())

            custom_dfs = {
                "Son Alis Fiyatlari": results["latest_prices"],
                "Fiyat Artisleri": results["price_increases"],
                "Fiyat Dususleri": results["price_decreases"],
            }

            pdf_path = create_excel_report(
                "Tarihsel Fiyat Analizi",
                [],
                suggested_filename="Tarihsel_Fiyat_Analizi_Raporu.xlsx",
                parent_window=self.parent_widget,
                custom_dataframes=custom_dfs,
            )

            if pdf_path:
                self._show_message(
                    "Analiz Tamamlandı",
                    f"Tarihsel Fiyat Analizi başarıyla tamamlandı. Rapor kaydedildi:\n{pdf_path}",
                    QMessageBox.Icon.Information,
                )
            else:
                self._show_message(
                    "Rapor Oluşturulamadı",
                    "Tarihsel Fiyat Analizi raporu oluşturulamadı.",
                    QMessageBox.Warning,
                )
        except Exception as e:
            self._show_message(
                "Analiz Hatası",
                f"Tarihsel Fiyat Analizi sırasında hata oluştu: {e}",
                QMessageBox.Warning,
                e,
            )

    def run_poz_usage_analysis(self):
        df_project = self._get_common_project_data()
        if df_project.empty:
            self._show_message(
                "Bilgi",
                "Analiz için proje verisi bulunamadı.",
                QMessageBox.Icon.Information,
            )
            return

        if not all(col in df_project.columns for col in ["Poz_No", "Proje_Tablo_Adı"]):
            self._show_message(
                "Veri Hatası",
                f"Poz Kullanım Analizi için gerekli sütunlar (Poz_No, Proje_Tablo_Adı) bulunamadı.",
                QMessageBox.Warning,
            )
            return

        try:
            self.db.cursor.execute("SELECT Poz_No, Poz_Açıklaması FROM pozlar")
            poz_desc_data = self.db.cursor.fetchall()
            poz_desc_df = pd.DataFrame(
                poz_desc_data, columns=["Poz_No", "Poz_Açıklaması"]
            )
        except Exception as e:
            self._show_message(
                "Veritabanı Hatası",
                f"Poz açıklamaları çekilirken hata oluştu: {e}. Analiz açıklamasız devam edecek.",
                QMessageBox.Warning,
                e,
            )
            poz_desc_df = pd.DataFrame(
                columns=["Poz_No", "Poz_Açıklaması"]
            )  # Boş DataFrame oluştur

        df_merged = pd.merge(df_project, poz_desc_df, on="Poz_No", how="left")
        df_merged["Poz_Açıklaması"].fillna("Açıklama Yok", inplace=True)

        df_usage = df_merged.rename(
            columns={
                "Poz_No": "poz_no",
                "Poz_Açıklaması": "poz_aciklamasi",
                "Proje_Tablo_Adı": "yeni_proje_adi",
            }
        )

        if not all(
            col in df_usage.columns
            for col in ["poz_no", "poz_aciklamasi", "yeni_proje_adi"]
        ):
            self._show_message(
                "Veri Hatası",
                f"Poz Kullanım Analizi için gerekli sütunlar (poz_no, poz_aciklamasi, yeni_proje_adi) bulunamadı veya dönüştürülemedi.",
                QMessageBox.Warning,
            )
            return

        try:
            results = analyze_poz_usage(df_usage.copy())

            custom_dfs = {
                "Poz Kullanim Sikligi": results["poz_kullanim_sikligi"],
                "En Sik Kullanilan Pozlar": results["en_sik_kullanilan_pozlar"],
                "Poz Proje Eslesmesi": results["poz_proje_eslesmesi"],
            }

            pdf_path = create_excel_report(
                "Poz Kullanım Analizi",
                [],
                suggested_filename="Poz_Kullanim_Analizi_Raporu.xlsx",
                parent_window=self.parent_widget,
                custom_dataframes=custom_dfs,
            )

            if pdf_path:
                self._show_message(
                    "Analiz Tamamlandı",
                    f"Poz Kullanım Analizi başarıyla tamamlandı. Rapor kaydedildi:\n{pdf_path}",
                    QMessageBox.Icon.Information,
                )
            else:
                self._show_message(
                    "Rapor Oluşturulamadı",
                    "Poz Kullanım Analizi raporu oluşturulamadı.",
                    QMessageBox.Warning,
                )
        except Exception as e:
            self._show_message(
                "Analiz Hatası",
                f"Poz Kullanım Analizi sırasında hata oluştu: {e}",
                QMessageBox.Warning,
                e,
            )

    def run_project_comparison_analysis(self):
        df_project = self._get_common_project_data()
        if df_project.empty:
            self._show_message(
                "Bilgi",
                "Analiz için proje verisi bulunamadı.",
                QMessageBox.Icon.Information,
            )
            return

        if not all(
            col in df_project.columns
            for col in ["Teklif_Maliyeti", "Gerçek_Maliyet", "Proje_Tablo_Adı"]
        ):
            self._show_message(
                "Veri Hatası",
                f"Proje Karşılaştırma Analizi için gerekli sütunlar (Teklif_Maliyeti, Gerçek_Maliyet, Proje_Tablo_Adı) bulunamadı.",
                QMessageBox.Warning,
            )
            return

        df_grouped_project = (
            df_project.groupby("Proje_Tablo_Adı")
            .agg(
                teklif_toplam_tutari=("Teklif_Maliyeti", "sum"),
                proje_son_maliyet=("Gerçek_Maliyet", "sum"),
            )
            .reset_index()
        )

        df_grouped_project["teklif_maliyet_farki"] = (
            df_grouped_project["proje_son_maliyet"]
            - df_grouped_project["teklif_toplam_tutari"]
        )

        df_grouped_project.rename(
            columns={"Proje_Tablo_Adı": "yeni_proje_adi"}, inplace=True
        )

        if df_grouped_project.empty:
            self._show_message(
                "Veri Yok",
                "Proje Karşılaştırma Analizi için toplu proje verisi bulunamadı.",
                QMessageBox.Warning,
            )
            return

        try:
            results = compare_projects(df_grouped_project.copy())

            custom_dfs = {"Proje Ozeti ve Sapma": results["project_summary"]}

            pdf_path = create_excel_report(
                "Proje Karşılaştırma Analizi",
                [],
                suggested_filename="Proje_Karsilastirma_Analizi_Raporu.xlsx",
                parent_window=self.parent_widget,
                custom_dataframes=custom_dfs,
            )

            if pdf_path:
                self._show_message(
                    "Analiz Tamamlandı",
                    f"Proje Karşılaştırma Analizi başarıyla tamamlandı. Rapor kaydedildi:\n{pdf_path}",
                    QMessageBox.Icon.Information,
                )
            else:
                self._show_message(
                    "Rapor Oluşturulamadı",
                    "Proje Karşılaştırma Analizi raporu oluşturulamadı.",
                    QMessageBox.Warning,
                )
        except Exception as e:
            self._show_message(
                "Analiz Hatası",
                f"Proje Karşılaştırma Analizi sırasında hata oluştu: {e}",
                QMessageBox.Warning,
                e,
            )

    def run_poz_maliyet_analizi(self):
        """Birim Maliyet Analizi'ni çalıştırır ve raporunu oluşturur."""
        df_project = self._get_common_project_data()
        if df_project.empty:
            self._show_message(
                "Bilgi",
                "Analiz için proje verisi bulunamadı.",
                QMessageBox.Icon.Information,
            )
            return

        required_cols_for_unit_cost = [
            "Proje_Tablo_Adı",
            "Poz_No",
            "Poz_Açıklaması",
            "Alınacak_Miktar",
            "Teklif_Fiyat",
            "Gerçek_Fiyat",
            "Teklif_Maliyeti",
            "Gerçek_Maliyet",
        ]

        missing_cols = [
            col for col in required_cols_for_unit_cost if col not in df_project.columns
        ]
        if missing_cols:
            self._show_message(
                "Veri Hatası",
                f"Birim Maliyet Analizi için gerekli sütunlar eksik: '{', '.join(missing_cols)}'. "
                f"Lütfen veritabanı şemasını ve veri çekme metodunu (get_project_cost_data_for_table) kontrol edin.",
                QMessageBox.Warning,
            )
            return

        try:
            results = Poz_Maliyet_Analizi(df_project.copy())

            custom_dfs = {
                "Genel Birim Maliyet Ozeti": pd.DataFrame(
                    {
                        "Ortalama Birim Fiyat Farki": [
                            results["genel_ortalama_birim_fiyat_farki"]
                        ]
                    }
                ),
                "Poz Bazli Birim Maliyet Analizi": results["poz_bazli_birim_analiz"],
                "Birim Fiyat Fark Tablosu": results["birim_fiyat_farki_tablosu"],
            }

            pdf_path = create_excel_report(
                "Birim Maliyet Analizi",
                [],
                suggested_filename="Poz_Maliyet_Analizi_Raporu.xlsx",
                parent_window=self.parent_widget,
                custom_dataframes=custom_dfs,
            )

            if pdf_path:
                self._show_message(
                    "Analiz Tamamlandı",
                    f"Rapor oluşturuldu:\n{pdf_path}",
                    QMessageBox.Icon.Information,
                )
            else:
                self._show_message(
                    "Rapor Oluşturulamadı",
                    "Birim Maliyet Analizi raporu oluşturulamadı.",
                    QMessageBox.Warning,
                )

        except KeyError as e:
            self._show_message(
                "Veri veya Anahtar Hatası",
                f"Birim Maliyet Analizi sırasında hata oluştu: '{e}'. Lütfen Poz_Maliyet_Analizi.py dosyasını veya veri sütunlarını kontrol edin.",
                QMessageBox.Critical,
                e,
            )
        except ZeroDivisionError as e:
            self._show_message(
                "Sıfıra Bölme Hatası",
                f"Birim Maliyet Analizi sırasında sıfıra bölme hatası oluştu: {e}. 'Alınacak_Miktar' sütununda sıfır değerler bulunuyor olabilir.",
                QMessageBox.Critical,
                e,
            )
        except ValueError as e:
            self._show_message(
                "Sayısal Dönüşüm Hatası",
                f"Birim Maliyet Analizi sırasında sayısal dönüşüm hatası oluştu: {e}. Verilerde geçersiz karakterler olabilir.",
                QMessageBox.Critical,
                e,
            )
        except Exception as e:
            self._show_message(
                "Analiz Hatası",
                f"Birim Maliyet Analizi sırasında beklenmeyen hata oluştu: {e}",
                QMessageBox.Warning,
                e,
            )
