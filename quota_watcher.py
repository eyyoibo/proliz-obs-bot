"""
GTÜ OBS Proliz Botu - Kontenjan Avcısı (Quota Watcher & Sniper) v2.2
Kullanıcının belirlediği spesifik dersleri 10 dakikada bir tarar,
yer açıldığı (Tükendi ibaresi kalktığı veya Saydır butonu aktifleştiği) anda
şubeyi ekler, pop-up savunmasını çalıştırır ve Telegram'a anlık bildirim atar.
"""

import datetime
import threading
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class QuotaWatcher:
    def __init__(self, engine, interval_minutes=10, telegram_service=None, log_cb=None, status_cb=None):
        self.engine = engine
        self.interval_seconds = max(60, int(interval_minutes * 60))
        self.telegram = telegram_service
        self.log_cb = log_cb or print
        self.status_cb = status_cb or (lambda s: None)
        self.is_running = False
        self.stop_requested = False
        self.watcher_thread = None
        self.watch_courses = []
        self.next_check_timestamp = 0

    def log(self, msg, level="INFO"):
        if self.engine and hasattr(self.engine, "log"):
            self.engine.log(msg, level=level, component="SNIPER")
        elif self.log_cb:
            self.log_cb(f"[Kontenjan Avcısı] {msg}", level)

    def set_watch_courses(self, courses):
        """Takip edilecek spesifik dersleri ayarlar."""
        self.watch_courses = list(courses)

    def start(self):
        """Kontenjan takip döngüsünü ayrı bir thread'de başlatır."""
        if self.is_running:
            return
        if not self.watch_courses:
            self.log("Takip edilecek ders listesi boş! Lütfen 'Kontenjan Sniper' listesine ders ekleyin.", "WARN")
            return

        self.is_running = True
        self.stop_requested = False
        self.watcher_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.watcher_thread.start()
        self.log(f"🎯 Kontenjan avcısı devrede! Her {self.interval_seconds // 60} dakikada bir kontrol edilecek.", "SUCCESS")
        if self.telegram:
            ders_isimleri = ", ".join(c.get("kod", "") for c in self.watch_courses)
            self.telegram.send_message(
                f"🎯 <b>Kontenjan Takipçisi (Sniper) Başlatıldı!</b>\n\n"
                f"📋 <b>İzlenen Dersler:</b> {ders_isimleri}\n"
                f"⏱️ <b>Kontrol Aralığı:</b> {self.interval_seconds // 60} dakikada bir\n"
                f"Kontenjan açıldığı anda otomatik kapılacak ve haber verilecektir."
            )

    def start_standalone(self):
        """Eğer tarayıcı açık değilse giriş yaparak bağımsız sniper modunu başlatır."""
        def _standalone_worker():
            try:
                if not self.engine.driver:
                    self.engine.init_driver()
                    if not self.engine.login_edevlet():
                        self.log("Giriş yapılamadığı için Kontenjan Sniper başlatılamadı.", "ERROR")
                        return

                self.engine.navigate_to_ders_kayit()
                self.engine.dismiss_iframe_announcement()
                self.start()
            except Exception as e:
                self.log(f"Bağımsız sniper başlatma hatası: {e}", "ERROR")

        threading.Thread(target=_standalone_worker, daemon=True).start()

    def stop(self):
        """Takip döngüsünü durdurur."""
        self.stop_requested = True
        self.is_running = False
        self.log("Kontenjan takipçisi durduruldu.", "INFO")
        if self.telegram:
            self.telegram.send_message("🛑 <b>Kontenjan Takipçisi Durduruldu.</b>")

    def _run_loop(self):
        """Periyodik tarama döngüsü."""
        while not self.stop_requested and self.watch_courses:
            self.log("Kontenjan taraması başlatılıyor...", "INFO")
            self.status_cb("Kontenjanlar Taranıyor...")

            try:
                self._check_all_watch_courses()
            except Exception as e:
                self.log(f"Tarama sırasında hata: {e}", "ERROR")
                if self.engine and hasattr(self.engine, "logger"):
                    self.engine.logger.capture_diagnostic(
                        getattr(self.engine, "driver", None), "Kontenjan tarama döngüsü hatası", e
                    )

            if not self.watch_courses:
                self.log("🎉 Tüm takip edilen derslerin kontenjanı yakalandı ve eklendi!", "SUCCESS")
                self.status_cb("Tüm Kontenjanlar Eklendi")
                break

            # Sonraki kontrol zamanı
            self.next_check_timestamp = time.time() + self.interval_seconds
            self.log(
                f"Sonraki kontrol {self.interval_seconds // 60} dakika sonra: "
                f"{datetime.datetime.fromtimestamp(self.next_check_timestamp).strftime('%H:%M:%S')}",
                "INFO"
            )

            while time.time() < self.next_check_timestamp and not self.stop_requested:
                time.sleep(10)
                if self.engine and hasattr(self.engine, "session_keep_alive"):
                    self.engine.session_keep_alive()
                    if hasattr(self.engine, "handle_popups_and_announcements"):
                        self.engine.handle_popups_and_announcements()

        self.is_running = False

    def check_now(self):
        """10 dakikalık periyodu beklemeden tüm kontenjanları anında kontrol eder."""
        self.log("⚡ Kullanıcı talebiyle anlık kontenjan kontrolü başlatılıyor...", "INFO")
        threading.Thread(target=self._check_all_watch_courses, daemon=True).start()

    def _check_all_watch_courses(self):
        """Listedeki her bir ders için şube kontenjanlarını kontrol eder ve takas yapar."""
        driver = getattr(self.engine, "driver", None)
        if not driver:
            self.log("WebDriver aktif değil! Oturum açılmamış olabilir.", "ERROR")
            return

        self.engine.handle_popups_and_announcements()
        if not self.engine.switch_to_course_frame():
            self.log("IFRAME1 çerçevesine geçilemedi, tarama erteleniyor.", "WARN")
            return

        eklenenler = []

        for course in list(self.watch_courses):
            if self.stop_requested:
                break

            kod = course.get("kod", "").strip()
            sinif = course.get("sinif", "2. Sınıf Dersleri")
            swap_c = course.get("swap_course", "").strip()

            self.log(f"[{kod}] için şube kontenjanları taranıyor (Sekme: {sinif})...", "INFO")
            if not self.engine.select_class_tab(sinif):
                continue
            time.sleep(0.4)

            # Eğer takas edilecek (kurban) bir ders tanımlanmışsa
            if swap_c:
                self.log(f"  ↳ Takas Kuralı: [{kod}] açılırsa [{swap_c}] silinecek.", "INFO")

                # Kontenjanı kontrol etmek için ders modalını aç ve dene
                eklendi = self.engine.add_course_with_branches(course)

                # Eğer AKTS aşımı veya yer olmaması nedeniyle eklenemediyse ama kontenjan varsa
                if not eklendi:
                    # Kurban dersi OBS'den silmeyi dene
                    self.log(f"🔄 Takas başlatılıyor: [{swap_c}] OBS'den siliniyor...", "WARN")
                    silindi = self.engine.drop_course(swap_c)
                    if silindi:
                        time.sleep(0.6)
                        self.log(f"[{swap_c}] silindi, şimdi hedef ders [{kod}] ekleniyor...", "INFO")
                        self.engine.select_class_tab(sinif)
                        time.sleep(0.3)
                        eklendi = self.engine.add_course_with_branches(course)
                        if not eklendi:
                            self.log(f"⚠️ [{kod}] eklenemedi! Kurban ders [{swap_c}] silinmişti.", "ERROR")

                if eklendi:
                    self.log(f"🚨 KONTENJAN YAKALANDI VE TAKAS EDİLDİ: [{swap_c}] ➔ [{kod}]", "SUCCESS")
                    eklenenler.append(course)
                    if self.telegram:
                        self.telegram.send_message(
                            f"🚨 <b>KONTENJAN YAKALANDI VE TAKAS EDİLDİ!</b>\n\n"
                            f"❌ <b>Silinen Ders:</b> <code>{swap_c}</code>\n"
                            f"✅ <b>Eklenen Yeni Ders:</b> <code>{kod}</code>\n"
                            f"🕒 <b>Saat:</b> {datetime.datetime.now().strftime('%H:%M:%S')}\n"
                            f"Kayıt listeniz başarıyla güncellendi!"
                        )
            else:
                # Standart ekleme
                eklendi = self.engine.add_course_with_branches(course)
                if eklendi:
                    self.log(f"🚨 KONTENJAN YAKALANDI VE EKLENDİ: [{kod}]", "SUCCESS")
                    eklenenler.append(course)
                    if self.telegram:
                        self.telegram.send_message(
                            f"🚨 <b>KONTENJAN YAKALANDI VE EKLENDİ!</b>\n\n"
                            f"📚 <b>Ders:</b> <code>{kod}</code>\n"
                            f"🕒 <b>Saat:</b> {datetime.datetime.now().strftime('%H:%M:%S')}\n"
                            f"Ders listenize başarıyla eklendi!"
                        )

        for eklenen in eklenenler:
            if eklenen in self.watch_courses:
                self.watch_courses.remove(eklenen)

        if eklenenler:
            self.log("Yeni kontenjanlar eklendi, 'Kontrol Et' işlemi yapılıyor...", "INFO")
            self.engine.perform_kontrol_et()
            if self.engine.config.get("auto_finalize", False):
                self.engine.perform_kesinlestir()
