import sys
import os
import pandas as pd
from pathlib import Path

from PyQt6.QtWidgets import (QMainWindow, QApplication, QMessageBox,
                            QDialog, QLabel, QWidget)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from config import DB_FILE

from poz_yonetimi import PozYonetimDuzenleSilDialog
from poz_secim import PozSecimDialog
from proje import ProjeYonetimDialog

from report_utils import create_excel_report
from ui_giris_formu import AnaPencere
from database import DatabaseManager


class GirisFormu(QMainWindow):

    def __init__(self, db_instance, parent=None):
        super().__init__(parent)
        self.db = db_instance  # db_instance'ı self.db olarak sakla
        self.ui = AnaPencere(self.db)  # Burayı güncelledik: db_instance'ı AnaPencere'ye gönder
        self.setCentralWidget(self.ui)  # Bu satırı ekle

        # self.ui.setupUi(self)
        # self.ui.db = self.db # Bu satıra artık gerek yok, çünkü __init__ ile geçiliyor
        self._connect_signals()
        self._populate_project_combobox()

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def _connect_signals(self):
        sidebar_button_map = {
            "🏗️  Proje Oluştur": self._open_project_creation_workflow,
            "💼  Poz Yönetimi": self._open_poz_yonetimi_dialog,
            "🚪  Çıkış": self.close
        }

        if hasattr(self.ui, 'sidebar_buttons'):
            for btn in self.ui.sidebar_buttons:
                if btn.text() in sidebar_button_map:
                    btn.clicked.connect(sidebar_button_map[btn.text()])

        analysis_button_map = {
            "Maliyet Fark Analizi": self._run_Teklif_Maliyet_Analizi,
            "Kar/Zarar Analizi": self._Kar_Zarar_Analizi,
            "Birim Maliyet Analizi": self._run_unit_cost_analysis,
            "Tedarikçi Analizi": self._run_supplier_performance_analysis,
            "Fiyat Analizi": self._run_historical_price_analysis,
            "Poz Kullanım Analizi": self._run_poz_usage_analysis,
            "Proje Karşılaştırma": self._run_project_comparison_analysis,
            "Risk Analizi": self._run_risk_analysis
        }

        if hasattr(self.ui, 'analysisCard') and hasattr(self.ui, 'analysisLayout'):
            for i in range(self.ui.analysisLayout.count()):
                item = self.ui.analysisLayout.itemAt(i)
                if item and item.widget() and isinstance(item.widget(), QWidget):
                    btn = item.widget()
                    if btn.text() in analysis_button_map:
                        btn.clicked.connect(analysis_button_map[btn.text()])

        if hasattr(self.ui, "btn_proje_sec"):
            try:
                self.ui.btn_proje_sec.clicked.disconnect()
            except TypeError:
                pass
            self.ui.btn_proje_sec.clicked.connect(self._open_existing_project)
            
    def _populate_project_combobox(self):
        if hasattr(self.ui, "comboBox_projeler"):
            self.ui.comboBox_projeler.clear()
            try:
                all_table_names = self.db.get_project_table_names()
                # "proje" ile başlayan tablo adlarını filtrele
                filtered = [name for name in all_table_names if name.lower().startswith("proje")]
                if filtered:
                    self.ui.comboBox_projeler.addItems(sorted(filtered))
                else:
                    self.ui.comboBox_projeler.addItem("Kayıtlı Proje Bulunamadı")
            except Exception as e:
                QMessageBox.critical(self, "DB Hatası", f"Tablolar alınamadı: {e}")
                self.ui.comboBox_projeler.addItem("Hata Oluştu")
    
    def _open_existing_project(self):
        if hasattr(self.ui, "comboBox_projeler") and self.ui.comboBox_projeler.count() > 0:
            selected = self.ui.comboBox_projeler.currentText()
            if selected in ["Kayıtlı Proje Bulunamadı", "Hata Oluştu"]:
                QMessageBox.information(self, "Bilgi", "Geçerli bir proje seçilmedi.")
                return
            try:
                dialog = ProjeYonetimDialog(self.db, self)
                dialog.set_project_table_name(selected)
                dialog.load_project_data(selected)
                dialog.exec()
            except Exception as e:
                QMessageBox.critical(self, "Proje Açma Hatası", str(e))

    def _open_poz_yonetimi_dialog(self):
        if self.db.conn and self.db.cursor:
            dialog = PozYonetimDuzenleSilDialog(self.db.conn, self.db.cursor, self)
            dialog.exec()

    def _open_project_creation_workflow(self):
        print("AnaPencere: _open_project_creation_workflow çağrıldı.")

        if not (self.db.conn and self.db.cursor):
            QMessageBox.critical(
                self, "Veritabanı Hatası", "Veritabanı bağlantısı yok."
            )
            print("AnaPencere: Veritabanı bağlantısı yok, işlem iptal edildi.")
            return

        dialog = PozSecimDialog(self.db.conn, self.db.cursor, str(DB_FILE), self)
        print("AnaPencere: PozSecimDialog oluşturuldu. exec() bekleniyor...")

        dialog_result = dialog.exec()

        print(
            f"AnaPencere: PozSecimDialog kapandı. Sonuç: {dialog_result} (Accepted: {QDialog.DialogCode.Accepted}, Rejected: {QDialog.DialogCode.Rejected})"
        )

        if dialog_result == QDialog.DialogCode.Accepted:
            pozlar = dialog.secilen_pozlari_al()
            if pozlar:
                print("AnaPencere: Pozlar seçildi, ProjeYonetimDialog başlatılıyor.")
                proje_dialog = ProjeYonetimDialog(self.db, self)
                for poz in pozlar:
                    Poz_No = poz["no"]
                    arsiv = self.db.get_highest_Alış_Fiyatı_from_arsiv(Poz_No)
                    data = [
                        poz["no"],
                        poz["tanim"],
                        poz["birim"],
                        poz["bedel"],
                        arsiv.get("Kullanıldığı_Proje", ""),
                        arsiv.get("Kullanıldığı_Tarih", ""),
                        arsiv.get("Tedarikçi", ""),
                        str(arsiv.get("Alış_Fiyatı", 0.0)),
                    ]
                    proje_dialog.poz_ekle(poz, data, arsiv)
                proje_dialog.exec()
                print("AnaPencere: ProjeYonetimDialog kapandı.")
            else:
                QMessageBox.information(self, "Bilgi", "Poz seçilmedi.")
                print("AnaPencere: Hiç poz seçilmedi.")
        else:
            QMessageBox.information(self, "Bilgi", "Poz seçimi iptal edildi.")
            print("AnaPencere: Poz seçimi iptal edildi mesajı gösterildi.")

        print("AnaPencere: _open_project_creation_workflow tamamlandı.")

    def closeEvent(self, event):
        """Ana pencere kapandığında çağrılır."""
        print("AnaPencere: closeEvent triggered. Uygulama kapatılıyor...")
        super().closeEvent(event)

    # --- Analiz Fonksiyonları ---
    def _get_common_project_data(self):
        try:
            project_table_names = self.db.get_project_table_names()

            if not project_table_names:
                QMessageBox.warning(
                    self,
                    "Veri Yok",
                    "Analiz için veritabanında hiç proje tablosu bulunamadı.",
                )
                return pd.DataFrame()

            all_projects_combined_df = pd.DataFrame()

            for table_name in project_table_names:
                project_df = self.db.get_project_cost_data_for_table(table_name)
                if not project_df.empty:
                    all_projects_combined_df = pd.concat(
                        [all_projects_combined_df, project_df], ignore_index=True
                    )
                else:
                    print(
                        f"Uyarı: '{table_name}' tablosundan geçerli maliyet verisi çekilemedi veya tablo boş."
                    )

            if all_projects_combined_df.empty:
                QMessageBox.warning(
                    self,
                    "Veri Yok",
                    "Analiz için tüm proje tablolarından yeterli veri toplanamadı.",
                )
                return pd.DataFrame()

            return all_projects_combined_df

        except Exception as e:
            QMessageBox.critical(
                self, "Veritabanı Hatası", f"Ortak proje verileri çekilemedi: {e}"
            )
            return pd.DataFrame()
    
    def _run_Teklif_Maliyet_Analizi(self):
        # Tüm proje tablo adlarını al
        all_table_names = self.db.get_project_table_names()
        # Sadece "proje" ile başlayan tablo adlarını filtrele
        project_table_names = [name for name in all_table_names if name.lower().startswith("proje")]

        if not project_table_names:
            QMessageBox.information(self, "Analiz Yok", "Analiz edilecek 'proje' ile başlayan tablo bulunamadı.")
            return

        all_project_analysis_results = []

        for table_name in sorted(project_table_names):
            df_project = self.db.get_project_cost_data_for_table(table_name)

            if df_project.empty:
                QMessageBox.warning(self, "Veri Eksik", f"'{table_name}' tablosu için veri bulunamadı veya eksik.")
                continue

            required_cols = {"Poz_No", "Teklif_Maliyet", "Gerçek_Maliyet"}
            if not required_cols.issubset(df_project.columns):
                QMessageBox.critical(
                    self,
                    "Veri Hatası",
                    f"'{table_name}' tablosunda gerekli sütunlar eksik: {', '.join(required_cols)}",
                )
                continue

            try:
                # Teklif_Maliyet ve Gerçek_Maliyet sütunlarını sayısal tiplere dönüştür
                df_project["Teklif_Maliyet"] = pd.to_numeric(df_project["Teklif_Maliyet"], errors="coerce").fillna(0)
                df_project["Gerçek_Maliyet"] = pd.to_numeric(df_project["Gerçek_Maliyet"], errors="coerce").fillna(0)

                # Genel toplamları hesapla
                toplam_teklif_maliyeti = df_project["Teklif_Maliyet"].sum()
                toplam_gercek_maliyet = df_project["Gerçek_Maliyet"].sum()
                toplam_fark = toplam_gercek_maliyet - toplam_teklif_maliyeti

                # Genel sapma yüzdesini hesapla
                if toplam_teklif_maliyeti != 0:
                    genel_sapma_yuzdesi = (toplam_fark / toplam_teklif_maliyeti) * 100
                else:
                    genel_sapma_yuzdesi = 0.0

                all_project_analysis_results.append({
                    "Proje Adı": table_name,
                    "Toplam Teklif Maliyeti": toplam_teklif_maliyeti,
                    "Toplam Gerçekleşen Maliyet": toplam_gercek_maliyet,
                    "Toplam Maliyet Farkı": toplam_fark,
                    "Sapma Yüzdesi (%)": genel_sapma_yuzdesi,
                })

            except ValueError as e:
                QMessageBox.critical(self, "İşleme Hatası", f"'{table_name}' tablosunda sayısal dönüşüm hatası: {e}")
                continue
            except Exception as e:
                QMessageBox.critical(self, "Analiz Hatası", f"'{table_name}' tablosu analiz edilirken beklenmeyen hata oluştu: {e}")
                continue

        if not all_project_analysis_results:
            QMessageBox.information(self, "Analiz Yok", "Hiçbir proje için başarılı analiz yapılamadı.")
            return

        # Tüm proje analiz sonuçlarını tek bir DataFrame'de topla
        overall_summary_df = pd.DataFrame(all_project_analysis_results)
        custom_dfs = {
            "Genel Proje Maliyet Farkları": overall_summary_df
        }

        try:
            pdf_path = create_excel_report(
                "Genel Proje Maliyet Fark Analizi",
                [],  # İçerik listesi boş bırakılabilir, çünkü tüm veriler custom_dfs içinde
                suggested_filename="Genel_Proje_Maliyet_Fark_Analizi.xlsx",
                parent_window=self,
                custom_dataframes=custom_dfs,
            )
            if pdf_path:
                QMessageBox.information(
                    self, "Analiz Tamamlandı", f"Rapor oluşturuldu:\n{pdf_path}"
                )
            else:
                QMessageBox.warning(
                    self, "Rapor Oluşturulamadı", "Genel Proje Maliyet Fark Analizi raporu oluşturulamadı.",
                )
        except Exception as e:
            QMessageBox.critical(self, "Rapor Oluşturma Hatası", f"Excel raporu oluşturulurken hata oluştu: {e}")

    def _Kar_Zarar_Analizi(self):
        df_project = self._get_common_project_data()
        if df_project.empty:
            return

        required_cols = [
            "Poz_No",
            "Poz_Açıklaması",
            "teklif_toplam_tutari",
            "proje_son_maliyet",
        ]
        if not all(col in df_project.columns for col in required_cols):
            QMessageBox.critical(
                self,
                "Veri Hatası",
                "Kar/Zarar analizi için gerekli sütunlar (Poz_Açıklaması, teklif_toplam_tutari, proje_son_maliyet) bulunamadı.",
            )
            return

        try:
            # Sütunları sayısal tiplere dönüştür, hataları NaN yap
            df_project["teklif_toplam_tutari"] = pd.to_numeric(
                df_project["teklif_toplam_tutari"], errors="coerce"
            ).fillna(0)
            df_project["proje_son_maliyet"] = pd.to_numeric(
                df_project["proje_son_maliyet"], errors="coerce"
            ).fillna(0)

            df_project["kar_zarar"] = (
                df_project["teklif_toplam_tutari"] - df_project["proje_son_maliyet"]
            )

            toplam_kar_zarar = df_project["kar_zarar"].sum()
            en_karli_poz = df_project.loc[df_project["kar_zarar"].idxmax()]
            en_zararli_poz = df_project.loc[df_project["kar_zarar"].idxmin()]

            results = {
                "toplam_kar_zarar": toplam_kar_zarar,
                "en_karli_poz": en_karli_poz,
                "en_zararli_poz": en_zararli_poz,
                "detayli_kar_zarar": df_project[
                    ["Poz_No", "Poz_Açıklaması", "teklif_toplam_tutari", "proje_son_maliyet", "kar_zarar"]
                ],
            }

            content = []
            content.append(f"Toplam Kar/Zarar: {results['toplam_kar_zarar']:.2f} TL\n")

            if (
                results["en_karli_poz"] is not None
                and not results["en_karli_poz"].empty
            ):
                content.append(
                    f"En Karlı Poz: {results['en_karli_poz']['Poz_No']} ({results['en_karli_poz']['kar_zarar']:.2f} TL kar)\n"
                )
            if (
                results["en_zararli_poz"] is not None
                and not results["en_zararli_poz"].empty
            ):
                content.append(
                    f"En Zararlı Poz: {results['en_zararli_poz']['Poz_No']} ({results['en_zararli_poz']['kar_zarar']:.2f} TL zarar)\n"
                )

            output_file = "Kar_Zarar_Analizi.xlsx"
            pdf_path = create_excel_report(
                "Kar/Zarar Analizi", content, output_file, custom_dataframes={"Detaylı Kar/Zarar": results["detayli_kar_zarar"]}
            )

            QMessageBox.information(
                self,
                "Kar/Zarar Analizi",
                f"Analiz başarıyla tamamlandı. Rapor kaydedildi:\\n{pdf_path}",
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Analiz Hatası",
                f"Kar/Zarar analizi çalıştırılırken veya rapor oluşturulurken hata oluştu: {e}",
            )

    def _run_unit_cost_analysis(self):
        df_project = self._get_common_project_data()
        if df_project.empty:
            return

        required_cols = {"Poz_No", "Ölçü_Birimi", "Metraj", "Gerçek_Maliyet"}
        if not all(col in df_project.columns for col in required_cols):
            QMessageBox.critical(
                self,
                "Veri Hatası",
                "Birim Maliyet analizi için gerekli sütunlar (Poz_No, Ölçü_Birimi, Metraj, Gerçek_Maliyet) bulunamadı.",
            )
            return

        try:
            df_project["Metraj"] = pd.to_numeric(
                df_project["Metraj"], errors="coerce"
            ).fillna(0)
            df_project["Gerçek_Maliyet"] = pd.to_numeric(
                df_project["Gerçek_Maliyet"], errors="coerce"
            ).fillna(0)

            # Birim maliyeti hesapla
            df_project["Birim_Maliyet"] = df_project.apply(
                lambda row: (
                    row["Gerçek_Maliyet"] / row["Metraj"]
                    if row["Metraj"] != 0
                    else 0.0
                ),
                axis=1,
            )

            # Analiz sonuçlarını DataFrame'e dönüştür
            analysis_results = df_project[
                ["Poz_No", "Ölçü_Birimi", "Metraj", "Gerçek_Maliyet", "Birim_Maliyet"]
            ].copy()

            content = [
                "Birim Maliyet Analizi Sonuçları:",
                analysis_results.to_string(index=False),
            ]
            output_file = "Birim_Maliyet_Analizi.xlsx"
            pdf_path = create_excel_report(
                "Birim Maliyet Analizi",
                content,
                output_file,
                custom_dataframes={"Birim_Maliyetler": analysis_results},
            )

            QMessageBox.information(
                self,
                "Birim Maliyet Analizi",
                f"Analiz başarıyla tamamlandı. Rapor kaydedildi:\\n{pdf_path}",
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Analiz Hatası",
                f"Birim Maliyet analizi çalıştırılırken veya rapor oluşturulurken hata oluştu: {e}",
            )

    def _run_supplier_performance_analysis(self):
        df_project = self._get_common_project_data()
        if df_project.empty:
            return

        required_cols = {"Tedarikçi", "Alış_Fiyatı", "Poz_No"}
        if not all(col in df_project.columns for col in required_cols):
            QMessageBox.critical(
                self,
                "Veri Hatası",
                "Tedarikçi Performans analizi için gerekli sütunlar (Tedarikçi, Alış_Fiyatı, Poz_No) bulunamadı.",
            )
            return

        try:
            df_project["Alış_Fiyatı"] = pd.to_numeric(
                df_project["Alış_Fiyatı"], errors="coerce"
            ).fillna(0)

            # Tedarikçi bazında ortalama alış fiyatı ve işlem sayısını hesapla
            supplier_performance = (
                df_project.groupby("Tedarikçi")
                .agg(
                    ortalama_alis_fiyati=("Alış_Fiyatı", "mean"),
                    islem_sayisi=("Poz_No", "count"),
                )
                .reset_index()
            )
            supplier_performance = supplier_performance.sort_values(
                by="ortalama_alis_fiyati"
            ).round(2)

            content = [
                "Tedarikçi Performans Analizi Sonuçları (Ortalama Alış Fiyatına Göre Sıralanmıştır):",
                supplier_performance.to_string(index=False),
            ]
            output_file = "Tedarikci_Performans_Analizi.xlsx"
            pdf_path = create_excel_report(
                "Tedarikçi Performans Analizi",
                content,
                output_file,
                custom_dataframes={"Tedarikçi_Performans": supplier_performance},
            )

            QMessageBox.information(
                self,
                "Tedarikçi Performans Analizi",
                f"Analiz başarıyla tamamlandı. Rapor kaydedildi:\\n{pdf_path}",
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Analiz Hatası",
                f"Tedarikçi Performans analizi çalıştırılırken veya rapor oluşturulurken hata oluştu: {e}",
            )

    def _run_historical_price_analysis(self):
        # Bu analiz için verileri `arsiv_detay` tablosundan çekmek daha mantıklı.
        # Bu kısım eksikse veya farklı bir veri yapısı gerekiyorsa,
        # DatabaseManager'a ilgili metotların eklenmesi gerekir.
        QMessageBox.information(
            self,
            "Bilgi",
            "Bu analiz için gerekli veritabanı yapısı veya çekme metodu henüz tanımlı değil.",
        )

    def _run_poz_usage_analysis(self):
        df_project = self._get_common_project_data()
        if df_project.empty:
            return

        required_cols = {"Poz_No", "Poz_Açıklaması"}
        if not all(col in df_project.columns for col in required_cols):
            QMessageBox.critical(
                self,
                "Veri Hatası",
                "Poz Kullanım analizi için gerekli sütunlar (Poz_No, Poz_Açıklaması) bulunamadı.",
            )
            return

        try:
            # Pozların kullanım sıklığını hesapla
            poz_usage = (
                df_project.groupby(["Poz_No", "Poz_Açıklaması"])
                .size()
                .reset_index(name="Kullanım_Sayısı")
            )
            poz_usage = poz_usage.sort_values(
                by="Kullanım_Sayısı", ascending=False
            ).round(2)

            content = [
                "Poz Kullanım Analizi Sonuçları (En Çok Kullanılandan En Aza):",
                poz_usage.to_string(index=False),
            ]
            output_file = "Poz_Kullanim_Analizi.xlsx"
            pdf_path = create_excel_report(
                "Poz Kullanım Analizi",
                content,
                output_file,
                custom_dataframes={"Poz_Kullanım": poz_usage},
            )

            QMessageBox.information(
                self,
                "Poz Kullanım Analizi",
                f"Analiz başarıyla tamamlandı. Rapor kaydedildi:\\n{pdf_path}",
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Analiz Hatası",
                f"Poz Kullanım analizi çalıştırılırken veya rapor oluşturulurken hata oluştu: {e}",
            )

    def _run_project_comparison_analysis(self):
        # Bu analiz için UI'dan karşılaştırılacak projelerin seçilmesi gerekir.
        # Bu kısım eksikse veya farklı bir veri yapısı gerekiyorsa,
        # DatabaseManager'a ilgili metotların eklenmesi gerekir.
        QMessageBox.information(
            self,
            "Bilgi",
            "Bu analiz için karşılaştırılacak projelerin seçimi veya gerekli veritabanı metodu henüz tanımlı değil.",
        )

    def _run_risk_analysis(self):
        df_project = self._get_common_project_data()
        if df_project.empty:
            return

        required_cols = {"Poz_No", "Gerçek_Maliyet", "Teklif_Maliyet"}
        if not all(col in df_project.columns for col in required_cols):
            QMessageBox.critical(
                self,
                "Veri Hatası",
                "Risk analizi için gerekli sütunlar (Poz_No, Gerçek_Maliyet, Teklif_Maliyet) bulunamadı.",
            )
            return

        try:
            df_project["Gerçek_Maliyet"] = pd.to_numeric(
                df_project["Gerçek_Maliyet"], errors="coerce"
            ).fillna(0)
            df_project["Teklif_Maliyet"] = pd.to_numeric(
                df_project["Teklif_Maliyet"], errors="coerce"
            ).fillna(0)

            # Maliyet sapmasını hesapla
            df_project["Maliyet_Sapması"] = (
                df_project["Gerçek_Maliyet"] - df_project["Teklif_Maliyet"]
            )

            # Yüksek riskli pozları belirle (örneğin, sapma belirli bir eşiğin üzerindeyse)
            risk_esigi = (
                df_project["Teklif_Maliyet"].sum() * 0.05
            )  # Toplam teklif maliyetinin %5'i
            riskli_pozlar = df_project[
                df_project["Maliyet_Sapması"] > risk_esigi
            ].sort_values(by="Maliyet_Sapması", ascending=False)

            results = {
                "riskli_pozlar": riskli_pozlar[
                    ["Poz_No", "Maliyet_Sapması", "Teklif_Maliyet", "Gerçek_Maliyet"]
                ]
            }

            content = []
            if not results["riskli_pozlar"].empty:
                content.append("Yüksek riskli pozlar (Maliyet Sapmasına Göre):")
                content.append(results["riskli_pozlar"].head().to_string())
            else:
                content.append("Yüksek riskli poz bulunamadı.")

            output_file = "Risk_Analizi.xlsx"
            pdf_path = create_excel_report(
                "Risk Analizi",
                content,
                output_file,
                custom_dataframes={"Riskli Pozlar": results["riskli_pozlar"]},
            )
            QMessageBox.information(
                self,
                "Risk Analizi",
                f"Analiz başarıyla tamamlandı. Rapor kaydedildi:\\n{pdf_path}",
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Analiz Hatası",
                f"Risk analizi çalıştırılırken veya rapor oluşturulurken hata oluştu: {e}",
            )
