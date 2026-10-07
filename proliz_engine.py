"""
Proliz (GTÜ OBS) Selenium Çekirdek Motoru v2.2
Özel 'Duyuru' kapatma (Fotoğraf 1), 'Bu derse saydır(Alttan)' butonu algılama (Fotoğraf 2),
UpdatePanel kararlılığı, matematik bot koruması ve otomatik kesinleştirme.
"""

import datetime
import os
import re
import time
import winsound
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoAlertPresentException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from logger_service import ProlizLogger
from telegram_service import TelegramService


class ProlizEngine:
    def __init__(self, config, log_cb=None, status_cb=None, logger=None):
        self.config = config
        self.log_cb = log_cb or print
        self.status_cb = status_cb or (lambda s: None)
        self.driver = None
        self.is_running = False
        self.stop_requested = False
        self.full_quota_courses = []

        # Zaman aşımı ayarları
        self.timeout_short = self.config.get("timeout_short", 5)
        self.timeout_medium = self.config.get("timeout_medium", 15)
        self.timeout_long = self.config.get("timeout_long", 30)

        # Loglama & Teşhis Servisi
        self.logger = logger or ProlizLogger(gui_callback=self.log_cb)

        # Telegram Bildirim Servisi
        token = self.config.get("telegram_token")
        chat_id = self.config.get("telegram_chat_id")
        if self.config.get("telegram_enabled", True) and token and chat_id:
            self.telegram = TelegramService(token=token, chat_id=chat_id, log_cb=self.log)
        else:
            self.telegram = None

    def log(self, message, level="INFO", component="ENGINE"):
        """Merkezi logger üzerinden hem dosyaya hem GUI'ye yazar."""
        self.logger.log(message, level=level, component=component)

    def set_status(self, status_text):
        """Arayüz durum etiketini günceller."""
        self.status_cb(status_text)

    def stop(self):
        """Çalışmayı güvenle durdurur."""
        self.stop_requested = True
        self.log("Durdurma talebi alındı. Tarayıcı kontrolü kullanıcıya bırakılıyor...", "WARN")
        self.set_status("Durduruldu / Kullanıcıda")

    def init_driver(self):
        """Selenium WebDriver'ı anti-detection bayraklarıyla başlatır."""
        self.log("Chrome WebDriver hazırlanıyor...", "INFO")
        self.set_status("Tarayıcı Başlatılıyor")

        options = webdriver.ChromeOptions()
        if not self.config.get("headless", False):
            options.add_argument("--start-maximized")
        else:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")

        # Bot algılama önleme bayrakları
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option(
            "prefs",
            {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
            },
        )

        try:
            self.driver = webdriver.Chrome(options=options)
            self.log("Chrome WebDriver başarıyla açıldı.", "SUCCESS")
        except Exception as e:
            self.logger.capture_diagnostic(None, "Chrome WebDriver başlatılamadı!", e)
            raise e

    def dismiss_iframe_announcement(self):
        """
        IFRAME1 veya index.aspx içindeki açılış Duyuru penceresini
        hızlı ve güvenli şekilde kapatır (ders modallarına dokunmaz).
        """
        try:
            res = self.driver.execute_script(
                """
                var closed = false;
                // 1. SweetAlert2 Duyuru modalı kontrolü (başlığı 'Duyuru' olan)
                var swalContainer = document.querySelector('.swal2-container');
                if (swalContainer) {
                    var title = swalContainer.querySelector('#swal2-title, .swal2-title');
                    if (title && title.innerText.includes('Duyuru')) {
                        var confirmBtn = swalContainer.querySelector('button.swal2-confirm, button.swal2-close');
                        if (confirmBtn) {
                            confirmBtn.click();
                            closed = true;
                        }
                    }
                }
                // 2. Iframe içi announcementPanel kapatma
                var annPanel = document.getElementById('announcementPanel');
                if (annPanel && annPanel.style.display !== 'none') {
                    var closeIcon = annPanel.querySelector('.close-icon, [onclick*="announcementPanel"]');
                    if (closeIcon) closeIcon.click();
                    else annPanel.style.display = 'none';
                    closed = true;
                }
                return closed;
                """
            )
            if res:
                self.log("📢 Açılış 'Duyuru' penceresi kapatıldı.", "INFO")
                return True
        except Exception:
            pass
        return False


    def handle_popups_and_announcements(self):
        """OBS sistemindeki tüm pop-up ve uyarıları (dış pencere ve iframe) temizler."""
        if not self.driver:
            return

        # Tek sekme koruma kontrolü (AlertTab.aspx)
        try:
            curr_url = self.driver.current_url.lower()
            if "alerttab.aspx" in curr_url:
                warn_msg = (
                    "🚨 DİKKAT: Proliz Tek Sekme Koruması tetiklendi (AlertTab.aspx)!\n"
                    "OBS başka bir sekmede veya cihazda açık olabilir."
                )
                self.log(warn_msg, "ERROR")
                if self.telegram:
                    self.telegram.send_message(f"⚠️ {warn_msg}")
        except Exception:
            pass

        # 1. Yerel JS Alert / Confirm kontrolü
        try:
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            self.log(f"Yerel tarayıcı uyarısı yakalandı: '{alert_text}', onaylanıyor...", "WARN")
            alert.accept()
            time.sleep(0.2)
        except NoAlertPresentException:
            pass
        except Exception:
            pass

        # 2. Üst penceredeki SweetAlert2 ve Oturum Modalı kontrolü
        try:
            self.driver.switch_to.default_content()

            # Oturum dolma modalı (#modalExpire)
            expire_btns = self.driver.find_elements(By.ID, "btnExtend")
            for eb in expire_btns:
                if eb.is_displayed():
                    self.driver.execute_script("arguments[0].click();", eb)
                    self.log("Oturum uzatma uyarısı (#modalExpire) onaylandı.", "SUCCESS")
                    time.sleep(0.2)

            # SweetAlert2
            swal_buttons = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'swal2-container')]//button[contains(@class, 'swal2-confirm') or contains(@class, 'swal2-close') or contains(., 'Tamam') or contains(., 'Kapat')]"
            )
            for s_btn in swal_buttons:
                if s_btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", s_btn)
                    self.log("Dış ekrandaki SweetAlert uyarısı kapatıldı.", "INFO")
                    time.sleep(0.2)

            self.driver.execute_script(
                "try { if (window.top && window.top.Swal && typeof window.top.Swal.close === 'function') window.top.Swal.close(); } catch(e) {}"
            )

            # UtModal
            ut_close_btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'UtModal-root') or contains(@id, 'UtModal')]//button[contains(@class, 'UtModal-closeBtn')]"
            )
            for ut_btn in ut_close_btns:
                if ut_btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", ut_btn)
                    time.sleep(0.2)

        except Exception as e:
            self.log(f"Pop-up kontrolü uyarısı: {e}", "DEBUG")

        # 3. Iframe içine geçip iframe pop-up'ını da kontrol et
        try:
            self.driver.switch_to.default_content()
            iframes = self.driver.find_elements(By.ID, "IFRAME1")
            if iframes and iframes[0].is_displayed():
                self.driver.switch_to.frame("IFRAME1")
                self.dismiss_iframe_announcement()
        except Exception:
            pass
        finally:
            try:
                self.driver.switch_to.default_content()
            except Exception:
                pass

    def login_edevlet(self):
        """e-Devlet üzerinden GTÜ OBS sistemine güvenli giriş yapar."""
        tc = self.config.get("tc", "")
        sifre = self.config.get("sifre", "")

        if not tc or not sifre:
            self.log("T.C. Kimlik No veya Şifre boş! Lütfen 'Giriş Ayarları' sekmesinden doldurun.", "ERROR")
            return False

        self.set_status("e-Devlet Girişi Yapılıyor")
        self.log("OBS giriş sayfasına yönlendiriliyor (https://obs.gtu.edu.tr/oibs/std/login.aspx)...", "INFO")
        self.driver.get("https://obs.gtu.edu.tr/oibs/std/login.aspx")
        wait = WebDriverWait(self.driver, self.timeout_medium)

        try:
            edevlet_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[contains(., 'E-Devlet İle Giriş') or contains(@id, 'Edevlet') or contains(@href, 'edevlet')]")
                )
            )
            self.driver.execute_script("arguments[0].click();", edevlet_btn)
            self.log("e-Devlet butonuna basıldı. Türkiye.gov.tr kapısı bekleniyor...", "INFO")

            WebDriverWait(self.driver, self.timeout_medium).until(EC.url_contains("turkiye.gov.tr"))

            tc_input = wait.until(EC.presence_of_element_located((By.ID, "tridField")))
            sifre_input = self.driver.find_element(By.ID, "egpField")
            giris_btn = self.driver.find_element(
                By.XPATH, "//form[@id='loginForm']//button[contains(., 'Giriş Yap')]"
            )

            tc_input.clear()
            for ch in tc:
                tc_input.send_keys(ch)
                time.sleep(0.015)

            sifre_input.clear()
            for ch in sifre:
                sifre_input.send_keys(ch)
                time.sleep(0.015)

            self.driver.execute_script("arguments[0].click();", giris_btn)
            self.log("Giriş bilgileri e-Devlet sistemine iletildi...", "INFO")

            try:
                onayla_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Onayla')]"))
                )
                self.driver.execute_script("arguments[0].click();", onayla_btn)
                self.log("e-Devlet OAuth2 yetkilendirme onaylandı.", "SUCCESS")
            except Exception:
                pass

            WebDriverWait(self.driver, self.timeout_long).until(
                lambda d: "index.aspx" in d.current_url.lower()
                or len(d.find_elements(By.ID, "topbar")) > 0
                or len(d.find_elements(By.ID, "sidebar")) > 0
            )

            self.log("🎉 GTÜ OBS Sistemine başarıyla giriş yapıldı!", "SUCCESS")
            self.set_status("Giriş Başarılı - Oturum Aktif")
            self.handle_popups_and_announcements()
            return True

        except Exception as e:
            self.logger.capture_diagnostic(self.driver, "e-Devlet giriş sürecinde hata oluştu", e)
            self.set_status("Giriş Hatası")
            return False

    def session_keep_alive(self):
        """Oturumun düşmesini önlemek için prolizSessionExtend fonksiyonunu tetikler."""
        try:
            self.driver.switch_to.default_content()
            self.driver.execute_script(
                "try { if (typeof prolizSessionExtend === 'function') prolizSessionExtend(); } catch(e){}"
            )
            chips = self.driver.find_elements(By.ID, "prolizSessionChip")
            if chips and chips[0].is_displayed():
                self.driver.execute_script("arguments[0].click();", chips[0])
        except Exception:
            pass

    def wait_for_target_time(self):
        """Kullanıcının belirlediği hedef saati bekler."""
        hedef_str = self.config.get("target_time", "08:29:58")
        if not self.config.get("wait_target_time", False):
            self.log("Zamanlayıcı pasif. Ders kayıt işlemleri hemen başlatılıyor...", "INFO")
            return True

        try:
            parts = [int(p) for p in hedef_str.split(":")]
            target_h = parts[0]
            target_m = parts[1]
            target_s = parts[2] if len(parts) > 2 else 0
        except Exception:
            self.log(f"Geçersiz saat formatı ({hedef_str}), hemen devam ediliyor.", "WARN")
            return True

        self.log(f"⏳ Hedef Saat Bekleniyor: {hedef_str}", "INFO")
        self.set_status(f"Saat Bekleniyor ({hedef_str})")

        last_keep_alive = time.time()
        while not self.stop_requested:
            now = datetime.datetime.now()
            today_target = now.replace(hour=target_h, minute=target_m, second=target_s, microsecond=0)

            if now >= today_target:
                self.log(f"🚀 Hedef saate ulaşıldı: {now.strftime('%H:%M:%S')}. Ders Kaydı Başlatılıyor!", "SUCCESS")
                break

            kalan_saniye = (today_target - now).total_seconds()
            if time.time() - last_keep_alive > 40:
                self.session_keep_alive()
                self.handle_popups_and_announcements()
                last_keep_alive = time.time()

            if int(kalan_saniye) % 10 == 0 or kalan_saniye <= 5:
                self.set_status(f"Kalan Süre: {int(kalan_saniye)} sn")

            if kalan_saniye <= 1:
                time.sleep(0.02)
            else:
                time.sleep(0.4)

        return not self.stop_requested

    def navigate_to_ders_kayit(self):
        """Sol menüden 'Ders ve Dönem İşlemleri' -> 'Ders Kayıt' yolunu açar."""
        self.set_status("Ders Kayıt Sayfasına Gidiliyor")
        self.log("Sol menüden 'Ders Kayıt' ekranına yönlendiriliyor...", "INFO")

        try:
            self.driver.switch_to.default_content()
            self.handle_popups_and_announcements()
            wait = WebDriverWait(self.driver, self.timeout_medium)

            menu_groups = self.driver.find_elements(
                By.XPATH,
                "//li[contains(@class, 'has-treeview') and .//p[contains(text(), 'Ders ve Dönem İşlemleri')]]"
            )

            if menu_groups:
                group_li = menu_groups[0]
                classes = group_li.get_attribute("class") or ""
                if "menu-open" not in classes:
                    toggle_btn = group_li.find_element(
                        By.XPATH, ".//a[contains(@class, 'menu-group-toggle')] | .//a[1]"
                    )
                    self.driver.execute_script("arguments[0].click();", toggle_btn)
                    self.log("'Ders ve Dönem İşlemleri' menü grubu açıldı.", "INFO")
                    time.sleep(0.3)

            kayit_links = wait.until(
                EC.presence_of_all_elements_located((
                    By.XPATH,
                    "//a[.//p[contains(text(), 'Ders Kayıt')]] | //a[contains(@onclick, 'Ders Kayıt') or contains(., 'Ders Kayıt')]"
                ))
            )
            kayit_btn = [k for k in kayit_links if "Ekle/Bırak" not in k.text][0]
            self.driver.execute_script("arguments[0].click();", kayit_btn)
            self.log("'Ders Kayıt' bağlantısına tıklandı. IFRAME1 yükleniyor...", "INFO")

            time.sleep(1.2)
            self.handle_popups_and_announcements()
            return True

        except Exception as e:
            self.logger.capture_diagnostic(self.driver, "Ders Kayıt menüsüne yönlendirme başarısız", e)
            return False

    def switch_to_course_frame(self):
        """Ders kayıt formunun çalıştığı ana içerik çerçevesine (IFRAME1) geçer ve duyuruları kapatır."""
        try:
            self.driver.switch_to.default_content()
            wait = WebDriverWait(self.driver, self.timeout_medium)
            iframe = wait.until(EC.presence_of_element_located((By.ID, "IFRAME1")))
            self.driver.switch_to.frame(iframe)

            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            # Fotoğraf 1'deki açılış 'Duyuru' penceresini kesin kapat
            self.dismiss_iframe_announcement()

            # Kayıt onay durumu kontrolü
            try:
                page_text = self.driver.page_source
                if "Öğrenci Onay Durumu: Kesinleştirildi" in page_text or "Kesinleştirildi" in page_text:
                    self.log("ℹ️ Sistemde 'Öğrenci Onay Durumu: Kesinleştirildi' görünüyor.", "INFO")
            except Exception:
                pass

            return True
        except Exception as e:
            self.logger.capture_diagnostic(self.driver, "IFRAME1 çerçevesine geçiş yapılamadı", e)
            return False

    def select_class_tab(self, sinif_adi):
        """1., 2., 3., 4. Sınıf sekmesine hızlı JS ile tıklar."""
        try:
            self.switch_to_course_frame()
            clicked = self.driver.execute_script(
                """
                var sinif = arguments[0].trim();
                var prefix = sinif.split(' ')[0]; // örn '2.' veya '4.'
                var tabs = document.querySelectorAll('a, button, li a, [role="tab"]');
                for (var t of tabs) {
                    var txt = (t.innerText || '').trim();
                    if (txt.includes(sinif) || (txt.includes(prefix) && txt.includes('Sınıf'))) {
                        t.scrollIntoView({ behavior: 'instant', block: 'nearest' });
                        t.click();
                        return true;
                    }
                }
                return false;
                """,
                sinif_adi
            )
            if clicked:
                self.log(f"'{sinif_adi}' sekmesi seçildi.", "INFO")
                time.sleep(0.3)
                return True
        except Exception as e:
            self.log(f"Sekme seçim hatası ({sinif_adi}): {e}", "DEBUG")
        return False

    def close_modal(self):
        """Açık olan ders/şube/saydırma modalını güvenle kapatır."""
        try:
            self.driver.execute_script(
                """
                var closeSelectors = [
                    'div.modal.show button.close',
                    'div.modal.show [data-dismiss="modal"]',
                    'div.modal.show button:has-text("Kapat")',
                    'div.modal.show button:has-text("Vazgeç")',
                    '.UtModal-closeBtn',
                    '#btnKapat'
                ];
                var modals = document.querySelectorAll('div.modal.show, div.modal[style*="display: block"], div.UtModal-root');
                for (var m of modals) {
                    var btn = m.querySelector('button.close, [data-dismiss="modal"], .UtModal-closeBtn, #btnKapat');
                    if (!btn) {
                        var btns = m.querySelectorAll('button, a');
                        for (var b of btns) {
                            var t = (b.innerText || '').toLowerCase();
                            if (t.includes('kapat') || t.includes('vazgeç')) { btn = b; break; }
                        }
                    }
                    if (btn) { btn.click(); break; }
                }
                """
            )
        except Exception:
            pass

    def solve_math_captcha_if_present(self):
        """Proliz bot doğrulama matematik sorusunu anlık JS ile çözer (0.005 sn)."""
        try:
            res = self.driver.execute_script(
                r"""
                var bodyText = document.body ? document.body.innerText : '';
                var m = bodyText.match(/(\d+)\s*([\+\-\*])\s*(\d+)\s*=\s*\?/);
                if (!m) {
                    var els = document.querySelectorAll('label, span, div, td, b, strong');
                    for (var el of els) {
                        var sm = (el.innerText || '').match(/(\d+)\s*([\+\-\*])\s*(\d+)\s*=\s*\?/);
                        if (sm) { m = sm; break; }
                    }
                }
                if (m) {
                    var n1 = parseInt(m[1]), op = m[2], n2 = parseInt(m[3]);
                    var ans = (op === '+') ? (n1 + n2) : (op === '-') ? (n1 - n2) : (n1 * n2);
                    var inp = document.querySelector('input[id*="txtAns"], input[id*="Captcha"], input[id*="txtIslem"], input.swal2-input, input[placeholder="?"]');
                    if (!inp) {
                        var inps = document.querySelectorAll('input[type="text"]');
                        for (var i of inps) {
                            if (i.offsetParent !== null && (i.id.includes('Ans') || i.id.includes('Islem') || (i.style.width && parseInt(i.style.width) <= 60))) {
                                inp = i;
                                break;
                            }
                        }
                    }
                    if (inp) {
                        inp.value = ans;
                        inp.dispatchEvent(new Event('input', { bubbles: true }));
                        inp.dispatchEvent(new Event('change', { bubbles: true }));
                        return { solved: true, n1: n1, op: op, n2: n2, ans: ans };
                    }
                }
                return { solved: false };
                """
            )
            if res and res.get("solved"):
                n1 = res.get("n1")
                op = res.get("op")
                n2 = res.get("n2")
                ans = res.get("ans")
                self.log(f"🛡️ [Bot Koruması] Matematik sorusu çözüldü: {n1} {op} {n2} = {ans}", "WARN")
                self.log(f"Matematik yanıtı ({ans}) yazıldı.", "SUCCESS")
                return True
        except Exception as e:
            self.log(f"Matematik kontrolü: {e}", "DEBUG")
        return False

    def find_course_row_and_click_plus(self, course_item):
        """
        #grdMufDers tablosunda aranan dersi nokta atışı bulur ve '+' butonuna tıklar.
        Güz'de bulunamazsa otomatik olarak 'Tümü' filtresine geçer.
        CSE495 gibi farklı dersleri ASLA tıklamaz (cells[1] kod doğrulaması yapar).
        """
        target_code = course_item.get("kod", "").strip()
        target_name = course_item.get("ad", "").strip()
        code_root = re.sub(r'\[.*?\]', '', target_code).strip()

        self.switch_to_course_frame()

        for attempt in range(2):
            res = self.driver.execute_script(
                """
                var targetCode = arguments[0].toLowerCase().replace(/[^a-z0-9]/g, '');
                var targetRoot = arguments[1].toLowerCase().replace(/[^a-z0-9]/g, '');
                var targetName = arguments[2].toLowerCase().replace(/[^a-z0-9]/g, '');

                var table = document.getElementById('grdMufDers') || document.querySelector('table[id*="grdMufDers"]');
                if (!table) {
                    // Fallback genel tablo arama
                    var tables = document.querySelectorAll('table.ProlizMGrid, table');
                    for (var t of tables) {
                        if (t.id !== 'grdDersKayit' && t.id !== 'grdDersler') {
                            table = t;
                            break;
                        }
                    }
                }
                if (!table) return { status: 'no_table' };

                var rows = table.querySelectorAll('tr');
                var foundRow = null;

                for (var i = 0; i < rows.length; i++) {
                    var r = rows[i];
                    var cells = r.cells;
                    if (!cells || cells.length < 3) continue;

                    // cells[1]: Ders Kodu (örn: CSE495, DElec7[0-3], GenTelec8[0-1], NonTElec3[0-1])
                    var cCode = (cells[1].innerText || '').toLowerCase().replace(/[^a-z0-9]/g, '');
                    // cells[2]: Ders Adı (örn: Graduation Project I, General Technical Elective II)
                    var cName = (cells[2].innerText || '').toLowerCase().replace(/[^a-z0-9]/g, '');

                    // Tam veya kök kod eşleşmesi (CSE495 gibi farklı dersler ASLA eşleşmez!)
                    if (cCode === targetCode || (targetRoot.length >= 5 && cCode === targetRoot)) {
                        foundRow = r;
                        break;
                    }
                    if (cCode.includes(targetCode) || (targetRoot.length >= 6 && cCode.includes(targetRoot))) {
                        foundRow = r;
                        break;
                    }
                    if (targetName.length >= 6 && cName.includes(targetName)) {
                        foundRow = r;
                        break;
                    }
                }

                if (!foundRow) return { status: 'not_found' };

                // cells[0] içindeki '+' butonu
                var btn = foundRow.cells[0].querySelector('a, button, input[type="image"]') ||
                          foundRow.querySelector('a[id*="btnEkle"], a.btn, button');

                if (!btn) return { status: 'no_button', code: foundRow.cells[1].innerText.trim() };

                foundRow.scrollIntoView({ behavior: 'instant', block: 'center' });
                btn.click();
                return {
                    status: 'clicked',
                    code: foundRow.cells[1].innerText.trim(),
                    name: foundRow.cells[2].innerText.trim()
                };
                """,
                target_code, code_root, target_name
            )

            if res and res.get("status") == "clicked":
                self.log(f"🎯 [{res.get('code')}] '{res.get('name')}' dersinin '+' butonuna basıldı!", "SUCCESS")
                return True

            if attempt == 0:
                # İlk denemede bulunamadıysa 'Tümü' radyo butonunu seç
                tumu_clicked = self.driver.execute_script(
                    """
                    var r = document.getElementById('cmbDonemTip_2') ||
                            document.querySelector('input[name*="DonemTip"][value="-1"]') ||
                            document.querySelector('input[name*="DonemTip_2"]');
                    var lbl = document.querySelector('label[for="cmbDonemTip_2"]') ||
                              document.querySelector('label[for*="DonemTip_2"]');

                    if (!lbl) {
                        var allLabels = document.querySelectorAll('label, td, span');
                        for (var l of allLabels) {
                            if (l.innerText && l.innerText.trim() === 'Tümü') {
                                lbl = l;
                                break;
                            }
                        }
                    }

                    if (r && !r.checked) {
                        r.click();
                        r.checked = true;
                        r.dispatchEvent(new Event('change', { bubbles: true }));
                        if (lbl) lbl.click();
                        return true;
                    } else if (lbl) {
                        lbl.click();
                        return true;
                    }
                    return false;
                    """
                )
                if tumu_clicked:
                    self.log("Ders varsayılan yarıyılda görünmedi, 'Tümü' radyo butonu seçildi. Tablonun güncellenmesi bekleniyor...", "INFO")
                    time.sleep(1.0)

        return False

    def _is_any_modal_open(self):
        """Herhangi bir ders/şube modalının (UtModal dahil) açık veya yükleniyor olup olmadığını kontrol eder."""
        try:
            return self.driver.execute_script(
                """
                var docs = [];
                function scan(win) {
                    try {
                        if (!win || !win.document || docs.includes(win.document)) return;
                        docs.push(win.document);
                        var iframes = win.document.querySelectorAll('iframe, frame');
                        for (var i = 0; i < iframes.length; i++) {
                            try {
                                var cwin = iframes[i].contentWindow;
                                if (cwin) scan(cwin);
                            } catch(e) {}
                        }
                    } catch(e) {}
                }
                try { scan(window.top); } catch(e) {}
                try { scan(window); } catch(e) {}

                for (var d of docs) {
                    var m = d.getElementById('UtModal') || d.querySelector('.UtModal-root, div.modal.show, div.modal[style*="display: block"]');
                    if (m) {
                        var style = d.defaultView ? d.defaultView.getComputedStyle(m) : m.style;
                        var isVis = (m.offsetParent !== null || m.classList.contains('show') || (style && style.display !== 'none' && style.visibility !== 'hidden'));
                        if (isVis) return true;
                    }
                }
                return false;
                """
            )
        except Exception:
            return False

    def _check_and_click_saydir(self, ders_kodu):
        """
        Fotoğraf 2'deki 'Gruplu Ders Seçim veya Saydırma Metodu' modalını kontrol eder ve tıklar.
        Tüm iframe'leri (UtModal_frame dahil) özyinelemeli tarar.
        CRITICAL: Ana ekrandaki 'Alttan Dersleri Göster' butonuna ASLA dokunmaz!
        """
        try:
            res = self.driver.execute_script(
                """
                var docs = [];
                function scan(win) {
                    try {
                        if (!win || !win.document || docs.includes(win.document)) return;
                        docs.push(win.document);
                        var iframes = win.document.querySelectorAll('iframe, frame');
                        for (var i = 0; i < iframes.length; i++) {
                            try {
                                var cwin = iframes[i].contentWindow;
                                if (cwin) scan(cwin);
                            } catch(e) {}
                        }
                    } catch(e) {}
                }
                try { scan(window.top); } catch(e) {}
                try { scan(window); } catch(e) {}

                for (var d of docs) {
                    var bodyText = (d.body ? d.body.innerText : '').toLowerCase();
                    var isSaydirPage = bodyText.includes('gruplu ders') || bodyText.includes('saydırma') || bodyText.includes('saydirma');

                    var btns = d.querySelectorAll('button, a, input[type="button"], input[type="submit"], [role="button"]');
                    for (var b of btns) {
                        var t = (b.innerText || b.value || '').trim();
                        if (!t) continue;
                        if (b.id === 'btnAlttanGoster' || t.toLowerCase().includes('alttan dersleri göster')) continue;

                        var tLow = t.toLowerCase();
                        if (tLow.includes('saydır') || tLow.includes('saydir') || (isSaydirPage && tLow.includes('alttan') && !tLow.includes('göster'))) {
                            b.scrollIntoView({ behavior: 'instant', block: 'center' });
                            b.click();
                            return { clicked: true, text: t };
                        }
                    }
                }
                return { clicked: false };
                """
            )
            if res and res.get("clicked"):
                btn_txt = res.get("text") or "Bu derse saydır(Alttan)"
                self.log(f"🎯 FOTOĞRAF 2 YAKALANDI: '{btn_txt}' butonuna basıldı!", "SUCCESS")
                time.sleep(0.6)
                self.solve_math_captcha_if_present()
                return True
        except Exception as e:
            self.log(f"Saydırma kontrolü uyarısı: {e}", "DEBUG")
        return False

    def _handle_grd_dersler_modal(self, ders_kodu, alt_tercihler):
        """
        #grdDersler tablosunu (iç içe iframe ve UtModal dahil) hızlı JS ile tarar
        ve seçmeli alt dersi (örn: GTU110) ekler.
        Döner:
          "added": Ders başarıyla ekle butonuna basıldı ve gerekliyse saydırma yapıldı.
          "error": OBS sunucusu hata verdi (örn: AKTS aşımı).
          "waiting_content": Modal açık ama tablo içeriği henüz yükleniyor.
          "not_found": Modal açık değil veya bu modal grdDersler değil.
        """
        try:
            res = self.driver.execute_script(
                """
                var targets = arguments[0];

                var docs = [];
                function scan(win) {
                    try {
                        if (!win || !win.document || docs.includes(win.document)) return;
                        docs.push(win.document);
                        var iframes = win.document.querySelectorAll('iframe, frame');
                        for (var i = 0; i < iframes.length; i++) {
                            try {
                                var cwin = iframes[i].contentWindow;
                                if (cwin) scan(cwin);
                            } catch(e) {}
                        }
                    } catch(e) {}
                }
                try { scan(window.top); } catch(e) {}
                try { scan(window); } catch(e) {}

                var targetDoc = null;
                var grid = null;

                for (var d of docs) {
                    var g = d.getElementById('grdDersler') || d.querySelector('table[id*="grdDersler"]');
                    if (g) {
                        targetDoc = d;
                        grid = g;
                        break;
                    }
                }

                // Eğer grid henüz bulunamadıysa ama UtModal açıksa, yükleniyor olabilir
                if (!grid) {
                    for (var d2 of docs) {
                        var ut = d2.getElementById('UtModal') || d2.querySelector('.UtModal-root');
                        if (ut) {
                            var style = d2.defaultView ? d2.defaultView.getComputedStyle(ut) : ut.style;
                            if (ut.offsetParent !== null || (style && style.display !== 'none')) {
                                return { status: 'waiting_content' };
                            }
                        }
                    }
                    return { status: 'not_found' };
                }

                // Sunucu hata mesajı kontrolü (lblSonuc)
                var errSpan = targetDoc.getElementById('lblSonuc');
                if (errSpan && errSpan.innerText.includes('HATA')) {
                    return { status: 'error', error: errSpan.innerText.trim() };
                }

                // "Tüm Dersleri Listele" butonu varsa tıkla
                var showAllBtn = targetDoc.getElementById('btnShowAll') || targetDoc.querySelector('a[id*="btnShowAll"], button[id*="btnShowAll"]');
                if (showAllBtn && showAllBtn.offsetParent !== null && !showAllBtn.dataset.clicked) {
                    showAllBtn.dataset.clicked = 'true';
                    showAllBtn.click();
                    return { status: 'clicked_show_all' };
                }

                // Tablo satırlarını tara
                var rows = grid.querySelectorAll('tr');
                for (var i = 0; i < rows.length; i++) {
                    var r = rows[i];
                    var cells = r.cells;
                    if (!cells || cells.length < 5) continue;

                    // cells[3]: Ders Kod (örn: GTU110)
                    // cells[4]: Ders Adı (örn: Scientific and Technological Activities)
                    var code = (cells[3].innerText || '').toLowerCase().replace(/[^a-z0-9]/g, '');
                    var name = (cells[4].innerText || '').toLowerCase().replace(/[^a-z0-9]/g, '');

                    for (var t of targets) {
                        var tNorm = t.toLowerCase().replace(/[^a-z0-9]/g, '');
                        if (code === tNorm || code.includes(tNorm) || tNorm.includes(code) || (tNorm.length >= 6 && name.includes(tNorm))) {
                            var btn = cells[1].querySelector('a, button, input') || r.querySelector('a[id*="btnEkle"], a.btn, button');
                            if (btn) {
                                btn.click();
                                return {
                                    status: 'clicked',
                                    code: cells[3].innerText.trim(),
                                    name: cells[4].innerText.trim()
                                };
                            }
                        }
                    }
                }

                // Sonraki sayfa kontrolü
                var nextBtn = targetDoc.getElementById('grdDersler_btnNext') || targetDoc.querySelector('a[id*="btnNext"], a[title*="Sonraki"]');
                if (nextBtn && nextBtn.offsetParent !== null && !nextBtn.className.includes('aspNetDisabled')) {
                    nextBtn.click();
                    return { status: 'next_page' };
                }

                return { status: 'waiting_content' };
                """,
                alt_tercihler
            )

            if not res:
                return "not_found"

            status = res.get("status")
            if status == "clicked":
                added_code = res.get("code")
                added_name = res.get("name")
                self.log(f"  -> 🎉 [{added_code}] '{added_name}' alt dersi için ekle (+) butonuna basıldı!", "SUCCESS")

                # Fotoğraf 2: Saydırma ekranı veya doğrudan ekleme akıllı izleme döngüsü (maks 4.5 sn)
                saydir_clicked = False
                start_wait = time.time()
                while time.time() - start_wait < 4.5:
                    time.sleep(0.35)
                    if self._check_and_click_saydir(f"{ders_kodu} -> {added_code}"):
                        saydir_clicked = True
                        self.log(f"  -> 🎯 [{added_code}] alttan saydırma işlemi tamamlandı!", "SUCCESS")
                        time.sleep(0.8)
                        break
                    # Modal kendiliğinden kapandıysa doğrudan eklenmiştir
                    if not self._is_any_modal_open():
                        break

                if self.telegram:
                    status_tag = "Ders Saydırıldı" if saydir_clicked else "Alt Ders Eklendi"
                    self.telegram.send_message(f"✅ <b>[{status_tag}]</b> <code>{ders_kodu}</code> ({added_code}) listenize eklendi.")

                self.solve_math_captcha_if_present()
                time.sleep(0.4)
                self.close_modal()
                return "added"

            elif status == "clicked_show_all":
                self.log("'Tüm Dersleri Listele' butonuna tıklandı, tablo bekleniyor...", "INFO")
                time.sleep(0.5)
                return "waiting_content"

            elif status == "next_page":
                self.log("Alt ders bu sayfada bulunamadı, sonraki sayfaya geçiliyor...", "INFO")
                time.sleep(0.6)
                return "waiting_content"

            elif status == "error":
                err_text = res.get("error")
                self.log(f"⚠️ OBS SİSTEM UYARISI: {err_text}", "ERROR")
                if self.telegram:
                    self.telegram.send_message(f"⚠️ <b>[OBS Ders Ekleme Hatası]</b>\n<code>{err_text}</code>")
                return "error"

            elif status == "waiting_content":
                return "waiting_content"

            return "not_found"

        except Exception as e:
            self.log(f"grdDersler modal işleme hatası: {e}", "DEBUG")
            return "not_found"

    def _handle_standard_branch_modal(self, ders_kodu, alt_tercihler):
        """Standart şube seçimi (Açık şubeler, Tükendi kontrolü)."""
        try:
            res = self.driver.execute_script(
                """
                var modals = document.querySelectorAll('div.modal.show, div.modal[style*="display: block"]');
                for (var m of modals) {
                    if (m.id === 'grdDerslerModal' || m.id === 'UtModal' || m.classList.contains('UtModal-root')) continue;
                    var rows = m.querySelectorAll('tr');
                    for (var r of rows) {
                        var t = r.innerText || '';
                        if (t.includes('Tükendi') || t.includes('Dolu')) continue;
                        var btn = r.querySelector('a, button, input[type="button"]');
                        if (btn) {
                            btn.click();
                            return { clicked: true };
                        }
                    }
                }
                return { clicked: false };
                """
            )
            if res and res.get("clicked"):
                self.log(f"  -> [{ders_kodu}] şubesi seçildi ve eklendi.", "SUCCESS")
                time.sleep(0.4)
                self._check_and_click_saydir(ders_kodu)
                self.solve_math_captcha_if_present()
                self.close_modal()
                return True
        except Exception as e:
            self.log(f"Standart şube modal hatası: {e}", "DEBUG")
        return False

    def add_course_with_branches(self, course_item):
        """
        Ders ve şube seçer:
        1. find_course_row_and_click_plus ile #grdMufDers'teki doğru satırın '+' butonuna basar.
        2. Modalların açılmasını bekler (akıllı polling - maks 6.0 sn):
           - Seçmeli alt ders modalı (#grdDersler, UtModal_frame) açıldıysa _handle_grd_dersler_modal çalışır.
           - Gruplu/Saydırma modalı açıldıysa _check_and_click_saydir çalışır.
           - Standart şube modalı açıldıysa _handle_standard_branch_modal çalışır.
        """
        ders_kodu = course_item.get("kod", "").strip()
        alt_tercihler = course_item.get("sub_choices", [])
        if not alt_tercihler:
            alt_tercihler = [ders_kodu]

        self.log(f"[{ders_kodu}] aranıyor... Tercih sırası: {alt_tercihler}", "INFO")
        self.set_status(f"Seçiliyor: {ders_kodu}")

        try:
            self.switch_to_course_frame()
            clicked = self.find_course_row_and_click_plus(course_item)
            if not clicked:
                self.log(f"[{ders_kodu}] dersi bu sınıf sekmesinde bulunamadı!", "WARN")
                return False

            # Tıklama sonrası yanıt bekleme (akıllı polling - maks 6.0 saniye)
            start_poll = time.time()
            modal_detected = False

            while time.time() - start_poll < 6.0:
                # 1. Seçmeli alt ders modalı (#grdDersler, UtModal_frame) kontrolü
                res = self._handle_grd_dersler_modal(ders_kodu, alt_tercihler)
                if res == "added":
                    return True
                elif res == "error":
                    self.close_modal()
                    return False
                elif res == "waiting_content":
                    modal_detected = True
                    time.sleep(0.3)
                    continue

                # 2. Saydırma modalı (Fotoğraf 2) kontrolü
                if self._check_and_click_saydir(ders_kodu):
                    return True

                # 3. Standart şube modalı kontrolü
                if self._handle_standard_branch_modal(ders_kodu, alt_tercihler):
                    return True

                # Modal henüz açılıyor mu?
                if self._is_any_modal_open():
                    modal_detected = True
                    time.sleep(0.2)
                    continue

                time.sleep(0.1)

            # Eğer bir modal açılmış ama aranan ders eklenememişse
            if modal_detected:
                self.log(f"⚠️ [{ders_kodu}] için modal açıldı ancak alt dersler ({alt_tercihler}) seçilemedi!", "WARN")
                self.close_modal()
                return False

            # Modal hiç açılmadıysa doğrudan eklenen tek şubeli ders olabilir
            self.solve_math_captcha_if_present()
            return True

        except Exception as e:
            self.logger.capture_diagnostic(self.driver, f"[{ders_kodu}] dersi seçiminde hata", e)
            self.close_modal()
            return False

    def drop_course(self, course_code):
        """
        'Seçilen Dersler' (#grdDersKayit) tablosundan belirtilen dersi bulup çöp kutusuna basarak siler.
        'Emin misiniz?' yerel confirm uyarısını ve SweetAlert onayını otomatik verir.
        """
        c_code_clean = course_code.strip()
        self.log(f"🗑️ [{c_code_clean}] dersi OBS'den siliniyor...", "WARN")
        self.set_status(f"Ders Siliniyor: {c_code_clean}")

        try:
            self.switch_to_course_frame()

            # 1. Native confirm diyalogunu otomatik onaylayacak şekilde override et
            self.driver.execute_script(
                """
                window.confirm = function() { return true; };
                try { if (window.top) window.top.confirm = function() { return true; }; } catch(e) {}
                """
            )

            # 2. #grdDersKayit tablosunda dersi bul ve sil butonuna bas
            res = self.driver.execute_script(
                """
                var target = arguments[0].toLowerCase().replace(/[^a-z0-9]/g, '');
                var table = document.getElementById('grdDersKayit') ||
                            document.querySelector('table[id*="grdDersKayit"], table[id*="Seçilen"]');
                if (!table) {
                    var tables = document.querySelectorAll('table');
                    for (var t of tables) {
                        if (t.innerText && (t.innerText.includes('Seçilen Dersler') || t.innerText.includes('Toplam Kredi'))) {
                            table = t;
                            break;
                        }
                    }
                }
                if (!table) return { status: 'no_table' };

                var rows = table.querySelectorAll('tr');
                for (var i = 0; i < rows.length; i++) {
                    var r = rows[i];
                    var cells = r.cells;
                    if (!cells || cells.length < 3) continue;

                    // cells[2]: Ders Kodu (örn: CSE231, GTU110)
                    var cCode = (cells[2].innerText || '').toLowerCase().replace(/[^a-z0-9]/g, '');

                    if (cCode === target || cCode.includes(target) || target.includes(cCode)) {
                        // cells[0] içindeki çöp kutusu (sil) butonu
                        var btn = cells[0].querySelector('a, button, input, img, i') ||
                                  r.querySelector('a[id*="btnSil"], a[title*="Sil"], .fa-trash, input[value*="Sil"]');
                        if (btn) {
                            var clickable = btn.closest('a') || btn.closest('button') || btn;
                            clickable.scrollIntoView({ behavior: 'instant', block: 'center' });
                            clickable.click();
                            return { status: 'clicked', code: cells[2].innerText.trim() };
                        }
                    }
                }
                return { status: 'not_found' };
                """,
                c_code_clean
            )

            if not res or res.get("status") != "clicked":
                self.log(f"⚠️ [{c_code_clean}] dersi Seçilen Dersler tablosunda bulunamadı!", "WARN")
                return False

            self.log(f"[{c_code_clean}] için çöp kutusu butonuna tıklandı. Onay bekleniyor...", "INFO")
            time.sleep(0.4)

            # 3. Native browser alert/confirm varsa kabul et
            try:
                alert = self.driver.switch_to.alert
                alert.accept()
                self.log("Native tarayıcı onay uyarısı kabul edildi.", "INFO")
                time.sleep(0.3)
            except Exception:
                pass

            # 4. SweetAlert2 / Modal onay butonunu kontrol et ve tıkla
            self.driver.execute_script(
                """
                var swalConfirm = document.querySelector('button.swal2-confirm, button.swal2-styled');
                if (swalConfirm) swalConfirm.click();
                try {
                    if (window.top && window.top.document) {
                        var topSwal = window.top.document.querySelector('button.swal2-confirm, button.swal2-styled');
                        if (topSwal) topSwal.click();
                    }
                } catch(e) {}
                """
            )
            time.sleep(0.6)

            # 5. Matematik sorusu çıkmışsa çöz
            self.solve_math_captcha_if_present()

            self.log(f"🎉 [{c_code_clean}] dersi başarıyla silindi.", "SUCCESS")
            if self.telegram:
                self.telegram.send_message(f"🗑️ <b>[Ders Silindi]</b> <code>{c_code_clean}</code> OBS listenizden kaldırıldı.")

            return True

        except Exception as e:
            self.log(f"Ders silme hatası ({c_code_clean}): {e}", "ERROR")
            return False

    def get_screenshot(self, save_path=None):
        """Tarayıcının anlık ekran görüntüsünü alır ve dosya yolunu döndürür."""
        if not self.driver:
            return None
        try:
            path = save_path or os.path.abspath("kayit_sonuc.png")
            self.driver.save_screenshot(path)
            return path
        except Exception as e:
            self.log(f"Ekran görüntüsü alma hatası: {e}", "ERROR")
            return None

    def perform_kontrol_et(self):
        """'Kontrol Et' butonuna hızlı JS ile basar ve matematik korumasını çözer."""
        self.set_status("Ders Kaydı Kontrol Ediliyor")
        self.log("Tüm ders seçimleri bitti. 'Kontrol Et' butonuna basılıyor...", "INFO")

        try:
            self.switch_to_course_frame()
            clicked = self.driver.execute_script(
                """
                var btn = document.getElementById('btnKontrolEt') ||
                          document.querySelector('a[id*="btnKontrolEt"], button[id*="btnKontrolEt"], input[value="Kontrol Et"]');
                if (btn) {
                    btn.scrollIntoView({ behavior: 'instant', block: 'center' });
                    btn.click();
                    return true;
                }
                return false;
                """
            )
            if not clicked:
                self.log("'Kontrol Et' butonu ekranda bulunamadı!", "WARN")
                return False

            self.log("'Kontrol Et' butonuna basıldı. Sistem kontrol yanıtı bekleniyor...", "INFO")
            time.sleep(0.5)

            self.solve_math_captcha_if_present()
            self.handle_popups_and_announcements()

            try:
                winsound.Beep(1200, 300)
                winsound.Beep(1600, 200)
            except Exception:
                pass

            self.log("=" * 60, "SUCCESS")
            self.log("DERSLER SEÇİLDİ VE 'KONTROL ET' İŞLEMİ TAMAMLANDI!", "SUCCESS")
            self.log("Kesinleştirme kontrolü için tarayıcı açık tutuluyor.", "SUCCESS")
            self.log("=" * 60, "SUCCESS")
            self.set_status("KONTROL TAMAMLANDI")

            if self.telegram:
                self.telegram.send_message("🔍 <b>[Kontrol Et Başarılı]</b> Ders seçimleri tamamlandı ve kontrol edildi.")

            return True

        except Exception as e:
            self.logger.capture_diagnostic(self.driver, "'Kontrol Et' aşamasında hata", e)
            return False

    def perform_kesinlestir(self):
        """'Kesinleştir' butonuna hızlı JS ile basar, SweetAlert onayını verir ve Telegram'a ekran görüntüsü iletir."""
        self.set_status("Ders Kaydı Kesinleştiriliyor")
        self.log("Otomatik Kesinleştirme aktif! 'Kesinleştir' butonu aranıyor...", "WARN")

        try:
            self.switch_to_course_frame()
            # Kesinleştirme yanındaki matematik sorusunu çöz
            self.solve_math_captcha_if_present()

            clicked = self.driver.execute_script(
                """
                var btn = document.getElementById('btnKesinlestir') ||
                          document.querySelector('a[id*="btnKesinles"], button[id*="btnKesinles"], input[value*="Kesinle"]');
                if (!btn) {
                    var all = document.querySelectorAll('a, button, input[type="button"]');
                    for (var b of all) {
                        var t = (b.innerText || b.value || '').trim();
                        if (t.includes('Kesinleştir') || t.includes('Kesinlestir')) {
                            btn = b;
                            break;
                        }
                    }
                }
                if (btn) {
                    btn.scrollIntoView({ behavior: 'instant', block: 'center' });
                    btn.click();
                    return true;
                }
                return false;
                """
            )
            if not clicked:
                self.log("'Kesinleştir' butonu ekranda bulunamadı!", "WARN")
                return False

            self.log("'Kesinleştir' butonuna basıldı. Onay modalı (SweetAlert) bekleniyor...", "INFO")
            time.sleep(0.6)

            # SweetAlert 'Evet' / 'Onayla' butonuna tıkla (önce iframe içinde)
            confirmed = self.driver.execute_script(
                """
                var btn = document.querySelector('button.swal2-confirm, button.swal2-styled');
                if (!btn) {
                    var btns = document.querySelectorAll('button');
                    for (var b of btns) {
                        var t = b.innerText || '';
                        if (t.includes('Evet') || t.includes('Onayla')) {
                            btn = b;
                            break;
                        }
                    }
                }
                if (btn) {
                    btn.click();
                    return true;
                }
                return false;
                """
            )

            # Eğer iframe içinde bulunamadıysa ana pencereye geçip dene
            if not confirmed:
                try:
                    self.driver.switch_to.default_content()
                    self.driver.execute_script(
                        """
                        var btn = document.querySelector('button.swal2-confirm, button.swal2-styled');
                        if (btn) btn.click();
                        """
                    )
                except Exception:
                    pass

            time.sleep(1.0)
            self.log("🎉 DERS KAYDI BAŞARIYLA KESİNLEŞTİRİLDİ!", "SUCCESS")
            self.set_status("KESİNLEŞTİRME TAMAMLANDI")

            try:
                screenshot_path = os.path.abspath("kayit_sonuc.png")
                self.driver.save_screenshot(screenshot_path)
                if self.telegram:
                    self.telegram.send_photo(
                        screenshot_path,
                        caption="🎉 <b>GTÜ OBS Ders Kaydınız Başarıyla Kesinleştirildi!</b>\n"
                                f"🕒 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
            except Exception as ss_err:
                self.log(f"Ekran görüntüsü iletim hatası: {ss_err}", "DEBUG")

            return True

        except Exception as e:
            self.logger.capture_diagnostic(self.driver, "Kesinleştirme aşamasında hata", e)
            return False

    def run(self):
        """Ana bot işlem akışı."""
        self.is_running = True
        self.stop_requested = False
        self.full_quota_courses = []

        if self.telegram:
            self.telegram.send_message(
                "🚀 <b>GTÜ Proliz Ders Kayıt Botu Başlatıldı!</b>\n\n"
                f"⏰ <b>Hedef Başlama Saati:</b> {self.config.get('target_time')}\n"
                f"📚 <b>Seçilen Ders Sayısı:</b> {len(self.config.get('selected_courses', []))}\n"
                f"🔒 <b>Otomatik Kesinleştirme:</b> {'Açık ✅' if self.config.get('auto_finalize', False) else 'Kapalı ⏸️'}"
            )

        try:
            # 1. WebDriver'ı Başlat
            self.init_driver()
            if self.stop_requested:
                return

            # 2. e-Devlet ile Giriş Yap
            if not self.login_edevlet():
                self.log("Giriş yapılamadığı için bot durduruldu.", "ERROR")
                if self.telegram:
                    self.telegram.send_message("❌ e-Devlet girişi başarısız oldu, bot durduruldu.")
                return

            # 3. Zamanlayıcıyı Bekle
            if not self.wait_for_target_time():
                return

            # 4. Ders Kayıt Menüsüne Git
            if not self.navigate_to_ders_kayit():
                self.log("Ders Kayıt ekranına ulaşılamadı!", "ERROR")
                if self.telegram:
                    self.telegram.send_message("❌ Ders Kayıt ekranına ulaşılamadı!")
                return

            # 5. Açılış Duyurularını Temizle
            self.handle_popups_and_announcements()

            # 6. IFRAME1 Çerçevesine Geç ve Fotoğraf 1'deki Duyuruyu Kesin Kapat
            if not self.switch_to_course_frame():
                self.log("Ders kayıt çerçevesine (IFRAME1) geçilemedi!", "ERROR")
                return

            # 7. Seçilen Dersleri Sınıf Sınıf Sırayla Ekle
            ders_plani = self.config.get("selected_courses", [])
            self.log(f"Toplam {len(ders_plani)} adet ders için seçim döngüsü başlatılıyor...", "INFO")
            self.set_status("Dersler Seçiliyor...")

            eklenen_ders_sayisi = 0

            for item in ders_plani:
                if self.stop_requested:
                    break

                sinif = item.get("sinif", "2. Sınıf Dersleri")
                kod = item.get("kod", "")

                self.log(f"--- [{sinif}] Sekmesine Geçiliyor ---", "INFO")
                self.select_class_tab(sinif)
                time.sleep(0.3)

                eklendi = self.add_course_with_branches(item)
                if eklendi:
                    eklenen_ders_sayisi += 1
                time.sleep(0.4)

            # 8. 'Kontrol Et' Butonuna Bas
            if not self.stop_requested:
                kontrol_ok = self.perform_kontrol_et()

                # 9. Otomatik Kesinleştirme (Safeguard Koruması: 0 ders eklendiyse kesinleştirme yapma!)
                if kontrol_ok and self.config.get("auto_finalize", False):
                    if eklenen_ders_sayisi > 0 or len(ders_plani) == 0:
                        self.perform_kesinlestir()
                    else:
                        warn_msg = (
                            "⚠️ GÜVENLİK KİLİDİ: Planlanan derslerden hiçbiri eklenemediği için "
                            "kesinleştirme butonuna basılmadı. Tarayıcınız oturumu korumak için açık bırakıldı."
                        )
                        self.log(warn_msg, "WARN")
                        if self.telegram:
                            self.telegram.send_message(f"⚠️ <b>[Kesinleştirme İptal Edildi]</b>\n{warn_msg}")

                # 10. Kontenjan Takipçisi (Sniper) Devri
                if self.config.get("quota_watch_enabled", False):
                    sniper_list = self.config.get("sniper_courses", []) or self.full_quota_courses
                    if sniper_list:
                        self.log("Kontenjan Takipçisi (Sniper) devralıyor...", "INFO")
                        from quota_watcher import QuotaWatcher
                        interval = self.config.get("quota_watch_interval_minutes", 10)
                        self.quota_watcher = QuotaWatcher(
                            self,
                            interval_minutes=interval,
                            telegram_service=self.telegram,
                            log_cb=self.log,
                            status_cb=self.set_status
                        )
                        self.quota_watcher.set_watch_courses(sniper_list)
                        self.quota_watcher.start()

        except Exception as e:
            self.logger.capture_diagnostic(self.driver, "Kritik Motor Çalışma Hatası", e)
            self.set_status("Hata ile Durdu")
            if self.telegram:
                self.telegram.send_message(f"❌ <b>Kritik Motor Hatası:</b> {e}")
        finally:
            self.is_running = False
            self.log("Bot döngüsü tamamlandı. Tarayıcı açık bırakıldı, oturumunuz korunuyor.", "INFO")
