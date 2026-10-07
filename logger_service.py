"""
GTÜ OBS Proliz Botu - Gelişmiş Loglama ve Hata Teşhis Servisi (Logger & Diagnostic Service)
Çift kanallı loglama (GUI Konsolu + Dosya), tam traceback kaydı ve hata anı otomatik ekran görüntüsü alır.
"""

import datetime
import os
import sys
import traceback


class ProlizLogger:
    def __init__(self, logs_dir="logs", gui_callback=None):
        self.logs_dir = os.path.abspath(logs_dir)
        self.gui_callback = gui_callback
        os.makedirs(self.logs_dir, exist_ok=True)

        session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file_path = os.path.join(self.logs_dir, f"proliz_bot_{session_id}.log")
        self.session_id = session_id

        # Dosya başlığını yaz
        with open(self.log_file_path, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write(f"GTU PROLIZ DERS KAYIT BOTU - SEANS LOG KAYDI\n")
            f.write(f"Oturum Başlangıcı: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}\n")
            f.write(f"Python Sürümü: {sys.version}\n")
            f.write(f"İşletim Sistemi: {sys.platform}\n")
            f.write("=" * 70 + "\n\n")

    def _format_message(self, message, level="INFO", component="SYSTEM"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        return f"[{timestamp}] [{level:<7}] [{component:<10}] {message}"

    def log(self, message, level="INFO", component="BOT"):
        """Hem dosyaya hem de GUI'ye log yazar."""
        formatted_line = self._format_message(message, level, component)

        # 1. Dosyaya yaz
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(formatted_line + "\n")
        except Exception:
            pass

        # 2. GUI konsoluna gönder (varsa)
        if self.gui_callback:
            try:
                gui_time = datetime.datetime.now().strftime("%H:%M:%S")
                gui_line = f"[{gui_time}] [{level}] {message}"
                self.gui_callback(gui_line, level)
            except Exception:
                pass

        # 3. Standart çıktıya bas (Terminal/CMD)
        try:
            print(formatted_line)
        except Exception:
            pass

    def info(self, msg, comp="BOT"):
        self.log(msg, level="INFO", component=comp)

    def success(self, msg, comp="BOT"):
        self.log(msg, level="SUCCESS", component=comp)

    def warn(self, msg, comp="BOT"):
        self.log(msg, level="WARN", component=comp)

    def error(self, msg, comp="BOT"):
        self.log(msg, level="ERROR", component=comp)

    def debug(self, msg, comp="BOT"):
        self.log(msg, level="DEBUG", component=comp)

    def capture_diagnostic(self, driver, context_msg, exc=None):
        """
        Bir hata anında sistemin durumunun (URL, frame, sayfa başlığı,
        tam traceback ve ekran görüntüsü) anlık fotoğrafını çeker.
        """
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        screenshot_path = os.path.join(self.logs_dir, f"error_{now_str}.png")

        diag_report = []
        diag_report.append("\n" + "!" * 70)
        diag_report.append(f"🚨 HATA TEŞHİS RAPORU - {context_msg}")
        diag_report.append(f"Zaman: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")

        # Selenium Durum Bilgileri
        if driver is not None:
            try:
                diag_report.append(f"Aktif URL: {driver.current_url}")
                diag_report.append(f"Sayfa Başlığı: {driver.title}")
                diag_report.append(f"Açık Pencere Sayısı: {len(driver.window_handles)}")

                # Ekran görüntüsü al
                driver.save_screenshot(screenshot_path)
                diag_report.append(f"Hata Ekran Görüntüsü Kaydedildi: {screenshot_path}")
            except Exception as d_err:
                diag_report.append(f"WebDriver durum bilgisi alınırken hata: {d_err}")

        # Traceback Bilgisi
        if exc is not None:
            diag_report.append(f"Hata Tipi: {type(exc).__name__}")
            diag_report.append(f"Hata Mesajı: {str(exc)}")
            tb_str = traceback.format_exc()
            diag_report.append("Traceback Detayları:\n" + tb_str)
        else:
            diag_report.append("Belirtilen bir Exception nesnesi yok.")

        diag_report.append("!" * 70 + "\n")
        full_diag_text = "\n".join(diag_report)

        # Dosyaya ayrıntılı teşhisi yaz
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(full_diag_text + "\n")
        except Exception:
            pass

        # GUI'ye özet hata bildirimi bas
        self.error(f"HATA: {context_msg} (Detaylar: {os.path.basename(self.log_file_path)})", comp="DIAG")
        if os.path.exists(screenshot_path):
            self.warn(f"Hata anı ekran görüntüsü kaydedildi: {os.path.basename(screenshot_path)}", comp="DIAG")

        return {
            "screenshot_path": screenshot_path if os.path.exists(screenshot_path) else None,
            "log_file": self.log_file_path,
            "full_diag": full_diag_text,
        }
