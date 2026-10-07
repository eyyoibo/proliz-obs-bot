"""
GTÜ OBS Proliz Botu - Telegram Bildirim ve Uzaktan Yönetim Servisi
Python standart urllib kütüphanesi ve Windows uyumlu SSL bağlamı kullanır.
"""

import io
import json
import mimetypes
import os
import ssl
import threading
import time
import urllib.parse
import urllib.request
import uuid


# Kullanıcının telefonunda sürekli görünen sabit hızlı işlem butonları
DEFAULT_KEYBOARD = {
    "keyboard": [
        [{"text": "📊 Durum"}, {"text": "🚀 Başlat"}, {"text": "🛑 Durdur"}],
        [{"text": "📋 Plan"}, {"text": "📸 Ekran (SS)"}, {"text": "⚡ Anlık Kontrol"}],
        [{"text": "📚 Müfredat"}, {"text": "🔍 Alt Dersler"}, {"text": "🎯 Kontenjan"}],
    ],
    "resize_keyboard": True,
    "is_persistent": True,
    "input_field_placeholder": "Komut seçin veya butonlara dokunun...",
}


class TelegramService:
    def __init__(self, token=None, chat_id=None, log_cb=None):
        self.token = token.strip() if token else ""
        self.chat_id = str(chat_id).strip() if chat_id else ""
        self.log_cb = log_cb or print
        self.polling_active = False
        self.polling_thread = None
        self.last_update_id = 0
        self.command_handlers = {}
        self.last_error = ""

        # Windows Python SSL sertifika doğrulama kilitlenmelerini önleyen bağlam
        try:
            self.ssl_context = ssl._create_unverified_context()
        except AttributeError:
            self.ssl_context = ssl.create_default_context()
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE

    def is_configured(self):
        return bool(self.token and self.chat_id)

    def log(self, msg, level="INFO"):
        if self.log_cb:
            self.log_cb(f"[Telegram] {msg}", level)

    def send_message(self, text, parse_mode="HTML", reply_markup=None):
        """Belirtilen chat_id'ye metin mesajı gönderir (opsiyonel Reply / Inline Keyboard ile)."""
        if not self.is_configured():
            self.last_error = "Bot Token veya Chat ID eksik!"
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }

        # reply_markup mantığı: Eğer açıkça False verilmediyse ve boş değilse klavye ekle
        if reply_markup is False:
            pass
        elif reply_markup is not None:
            payload["reply_markup"] = json.dumps(reply_markup)
        else:
            payload["reply_markup"] = json.dumps(DEFAULT_KEYBOARD)

        try:
            data = urllib.parse.urlencode(payload).encode("utf-8")
            req = urllib.request.Request(
                url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            with urllib.request.urlopen(req, timeout=12, context=self.ssl_context) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                ok = res_data.get("ok", False)
                if not ok:
                    self.last_error = res_data.get("description", "Bilinmeyen API hatası")
                    self.log(f"API Yanıtı Başarısız: {self.last_error}", "WARN")
                return ok
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="ignore")
            if "chat not found" in err_body.lower():
                self.last_error = (
                    f"HTTP {he.code}: Chat bulunamadı! Lütfen Telegram uygulamasından botunuza (@iboobsbot) "
                    "giderek bir kez /start (Başlat) butonuna basın."
                )
            else:
                self.last_error = f"HTTP {he.code}: {err_body}"
            self.log(f"Telegram HTTP Hatası: {self.last_error}", "ERROR")
            return False
        except Exception as e:
            self.last_error = str(e)
            self.log(f"Mesaj gönderme hatası: {e}", "ERROR")
            return False

    def answer_callback_query(self, callback_query_id, text=None):
        """Inline buton tıklamasındaki yükleniyor animasyonunu anında sonlandırır."""
        if not self.is_configured() or not callback_query_id:
            return False
        url = f"https://api.telegram.org/bot{self.token}/answerCallbackQuery"
        payload = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        try:
            data = urllib.parse.urlencode(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
            with urllib.request.urlopen(req, timeout=5, context=self.ssl_context) as resp:
                return True
        except Exception:
            return False

    def set_my_commands(self):
        """Telegram uygulamasındaki yerel '/' komut listesini otomatik kaydeder."""
        if not self.is_configured():
            return False
        url = f"https://api.telegram.org/bot{self.token}/setMyCommands"
        commands = [
            {"command": "durum", "description": "📊 Bot durumu, oturum ve AKTS"},
            {"command": "baslat", "description": "🚀 Ders kaydını uzaktan başlat"},
            {"command": "durdur", "description": "🛑 İşlemi güvenle durdur"},
            {"command": "plan", "description": "📋 Kayıt planındaki dersler"},
            {"command": "ss", "description": "📸 Canlı OBS ekran görüntüsü al"},
            {"command": "kontrol", "description": "⚡ Kontenjanları anında tara"},
            {"command": "altdersler", "description": "🔍 Seçmeli alt dersler kataloğu (GTU110 vb.)"},
            {"command": "mufredat", "description": "📚 Sınıf bazlı müfredat listesi"},
            {"command": "kontenjan", "description": "🎯 Sniper listesi ve takibi"},
            {"command": "saat", "description": "⏰ Hedef saati gör / ayarla"},
            {"command": "yardim", "description": "❓ Tüm komutları ve rehberi göster"}
        ]
        try:
            body = json.dumps({"commands": commands}).encode("utf-8")
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=8, context=self.ssl_context) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                if res.get("ok"):
                    self.log("Telegram yerel '/' komut menüsü senkronize edildi.", "SUCCESS")
                    return True
        except Exception as e:
            self.log(f"setMyCommands uyarısı: {e}", "DEBUG")
        return False

    @staticmethod
    def normalize_text_command(text):
        """Buton yazılarını ve emojili komutları standart komut adına dönüştürür."""
        clean = text.strip()
        mapping = {
            "📊 durum": "/durum",
            "durum": "/durum",
            "🚀 başlat": "/baslat",
            "🚀 baslat": "/baslat",
            "baslat": "/baslat",
            "🛑 durdur": "/durdur",
            "durdur": "/durdur",
            "📋 plan": "/plan",
            "📋 planım": "/plan",
            "plan": "/plan",
            "dersler": "/plan",
            "📸 ekran (ss)": "/ss",
            "📸 canlı ekran (ss)": "/ss",
            "📸 ss": "/ss",
            "ekran": "/ss",
            "ss": "/ss",
            "⚡ anlık kontrol": "/kontrol",
            "⚡ kontrol": "/kontrol",
            "kontrol": "/kontrol",
            "📚 müfredat": "/mufredat",
            "📚 mufredat": "/mufredat",
            "müfredat": "/mufredat",
            "mufredat": "/mufredat",
            "🔍 alt dersler": "/altdersler",
            "alt dersler": "/altdersler",
            "altdersler": "/altdersler",
            "altders": "/altdersler",
            "seçimler": "/altdersler",
            "secimler": "/altdersler",
            "🎯 kontenjan": "/kontenjan",
            "kontenjan": "/kontenjan",
            "sniper": "/kontenjan",
            "❓ yardım": "/yardim",
            "yardım": "/yardim",
            "yardim": "/yardim",
            "help": "/yardim",
        }
        low = clean.lower()
        for k, v in mapping.items():
            if low == k:
                return v
            elif low.startswith(k + " "):
                rem = clean[len(k):].strip()
                return f"{v} {rem}".strip()
        return clean

    def send_photo(self, photo_path_or_bytes, caption=""):
        """Telegram'a fotoğraf / ekran görüntüsü gönderir."""
        if not self.is_configured():
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendPhoto"
        boundary = uuid.uuid4().hex

        try:
            if isinstance(photo_path_or_bytes, str):
                if not os.path.exists(photo_path_or_bytes):
                    return False
                with open(photo_path_or_bytes, "rb") as f:
                    photo_bytes = f.read()
                filename = os.path.basename(photo_path_or_bytes)
            else:
                photo_bytes = photo_path_or_bytes
                filename = "screenshot.png"

            body = io.BytesIO()
            # chat_id alanı
            body.write(f"--{boundary}\r\n".encode("utf-8"))
            body.write(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{self.chat_id}\r\n'.encode("utf-8"))

            # caption alanı
            if caption:
                body.write(f"--{boundary}\r\n".encode("utf-8"))
                body.write(f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'.encode("utf-8"))

            # photo alanı
            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            body.write(f"--{boundary}\r\n".encode("utf-8"))
            body.write(
                f'Content-Disposition: form-data; name="photo"; filename="{filename}"\r\nContent-Type: {content_type}\r\n\r\n'.encode("utf-8")
            )
            body.write(photo_bytes)
            body.write(f"\r\n--{boundary}--\r\n".encode("utf-8"))

            req = urllib.request.Request(
                url,
                data=body.getvalue(),
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            )
            with urllib.request.urlopen(req, timeout=25, context=self.ssl_context) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                return res_data.get("ok", False)
        except Exception as e:
            self.log(f"Fotoğraf gönderme hatası: {e}", "ERROR")
            return False

    def test_connection(self):
        """Bağlantıyı test etmek için kullanıcıya anlık bildirim gönderir."""
        test_msg = (
            "🚀 <b>GTÜ OBS Proliz Botu v2.3 Bağlantısı Başarılı!</b>\n\n"
            "✅ Telegram bildirim ve uzaktan yönetim servisi aktif edildi.\n"
            "💡 <i>Aşağıdaki hazır butonlara tek tıkla dokunarak işlem yapabilirsiniz.</i>\n\n"
            "📱 <b>Hızlı Kısayol Butonları Eklendi:</b>\n"
            "• <code>📊 Durum</code> — Botun durumu ve canlı oturum\n"
            "• <code>🚀 Başlat</code> — Ders kaydını uzaktan hemen başlat\n"
            "• <code>🛑 Durdur</code> — İşlemi güvenle durdur\n"
            "• <code>📋 Plan</code> — Kayıt planındaki dersleri listele\n"
            "• <code>📸 Ekran (SS)</code> — Canlı ekran görüntüsü al ve gönder\n"
            "• <code>⚡ Anlık Kontrol</code> — Kontenjanları hemen anlık kontrol et\n"
            "• <code>🔍 Alt Dersler</code> — Seçmeli alt ders havuzunu incele (GTU110 vb.)\n"
            "• <code>📚 Müfredat</code> — Sınıf bazlı müfredatı listele\n"
            "• <code>🎯 Kontenjan</code> — Sniper takip listesi ve takas"
        )
        return self.send_message(test_msg)

    def register_command(self, command, handler_func):
        """Telegram'dan gelen komutları bir fonksiyona bağlar."""
        cmd = command.lower().strip()
        if not cmd.startswith("/"):
            cmd = "/" + cmd
        self.command_handlers[cmd] = handler_func

    def start_listener(self):
        """Arka planda Telegram komutlarını dinlemeye başlar."""
        if self.polling_active:
            return
        if not self.is_configured():
            self.log("Telegram Token veya Chat ID eksik, dinleyici başlatılamadı.", "WARN")
            return

        # Yerel '/' komut listesini Telegram'a kaydet
        threading.Thread(target=self.set_my_commands, daemon=True).start()

        self.polling_active = True
        self.polling_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.polling_thread.start()
        self.log("Telegram uzaktan komut dinleyicisi başlatıldı.", "SUCCESS")

        # Kullanıcının telefonundaki klavyenin altına butonları anında gönder
        def _send_welcome():
            time.sleep(1.2)
            welcome_text = (
                "🤖 <b>GTÜ Proliz Bot v2.3 Uzaktan Yönetim Aktif!</b>\n\n"
                "📱 <b>Hızlı butonlar klavyenizin altına yüklendi.</b>\n"
                "Aşağıdaki butonlara tek tıkla dokunarak ders kaydını ve botu yönetebilirsiniz.\n\n"
                "💡 <i>Eğer butonlar gizlenirse metin kutusunun sağındaki <b>dört kare (⊞)</b> simgesine dokunabilirsiniz.</i>"
            )
            self.send_message(welcome_text)

        threading.Thread(target=_send_welcome, daemon=True).start()

    def stop_listener(self):
        """Dinleyiciyi durdurur."""
        self.polling_active = False
        self.log("Telegram uzaktan komut dinleyicisi durduruldu.", "INFO")

    def _poll_loop(self):
        """Telegram getUpdates döngüsü (Mesajlar + Inline Butonlar / Callback Query)."""
        try:
            init_url = f"https://api.telegram.org/bot{self.token}/getUpdates?offset=-1"
            with urllib.request.urlopen(init_url, timeout=10, context=self.ssl_context) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                results = data.get("result", [])
                if results:
                    self.last_update_id = results[-1].get("update_id", 0) + 1
        except Exception:
            pass

        while self.polling_active:
            try:
                url = f"https://api.telegram.org/bot{self.token}/getUpdates?offset={self.last_update_id}&timeout=5"
                with urllib.request.urlopen(url, timeout=12, context=self.ssl_context) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if not data.get("ok", False):
                        time.sleep(2)
                        continue

                    for update in data.get("result", []):
                        self.last_update_id = update.get("update_id", 0) + 1

                        # 1. Inline Buton Tıklaması (Callback Query)
                        callback_query = update.get("callback_query")
                        if callback_query:
                            from_id = str(callback_query.get("from", {}).get("id", ""))
                            if from_id == self.chat_id:
                                cq_id = callback_query.get("id")
                                self.answer_callback_query(cq_id)
                                raw_text = callback_query.get("data", "").strip()
                            else:
                                continue
                        else:
                            msg = update.get("message", {})
                            from_id = str(msg.get("from", {}).get("id", ""))
                            if from_id != self.chat_id:
                                continue
                            raw_text = msg.get("text", "").strip()

                        if not raw_text:
                            continue

                        # Buton ve komut normalizasyonu
                        norm_text = self.normalize_text_command(raw_text)
                        cmd = norm_text.split()[0].lower()
                        args = norm_text.split()[1:]

                        if not cmd.startswith("/"):
                            cmd = "/" + cmd

                        self.log(f"Telegram'dan komut alındı: '{raw_text}' -> [{cmd} {args}]", "INFO")

                        if cmd in self.command_handlers:
                            try:
                                reply = self.command_handlers[cmd](args)
                                if reply:
                                    if isinstance(reply, tuple):
                                        text_resp, markup = reply
                                        self.send_message(text_resp, reply_markup=markup)
                                    elif isinstance(reply, str):
                                        self.send_message(reply)
                            except Exception as handler_err:
                                self.log(f"Komut işleme hatası ({cmd}): {handler_err}", "ERROR")
                                self.send_message(f"⚠️ Komut işlenirken hata oluştu: {handler_err}")
                        elif cmd in ("/yardim", "/help", "/start"):
                            help_msg = (
                                "🤖 <b>GTÜ Proliz Bot v2.3 Komut ve Kısayol Menüsü</b>\n\n"
                                "💡 <i>Aşağıdaki hazır butonlara tek tıkla dokunarak işlem yapabilirsiniz.</i>\n\n"
                                "📊 <b>Hızlı Kısayollar:</b>\n"
                                "• <code>📊 Durum</code> : Bot çalışma durumu, sayaç ve AKTS\n"
                                "• <code>🚀 Başlat</code> : Ders kaydını uzaktan hemen başlatır\n"
                                "• <code>🛑 Durdur</code> : Çalışan işlemi güvenle durdurur\n"
                                "• <code>📋 Plan</code> : Kayıt planındaki dersleri listeler\n"
                                "• <code>📸 Ekran (SS)</code> : OBS ekran görüntüsünü gönderir\n"
                                "• <code>⚡ Anlık Kontrol</code> : Kontenjanları anında tarar\n"
                                "• <code>🔍 Alt Dersler</code> : Seçmeli alt dersler havuzu (GTU110 vb.)\n"
                                "• <code>📚 Müfredat</code> : Sınıf bazlı ders kataloğu\n"
                                "• <code>🎯 Kontenjan</code> : Sniper takip listesi ve takas\n\n"
                                "⚙️ <b>Parametreli Komutlar:</b>\n"
                                "• <code>/saat [HH:MM:SS]</code> : Hedef saati gör veya ayarla\n"
                                "• <code>/ekle [kod] [alt_ders]</code> : Plana ders ekle\n"
                                "• <code>/sil [kod]</code> : Plandan ders çıkar\n"
                                "• <code>/obs_sil [kod]</code> : OBS'den kayıtlı dersi sil (🗑️)\n"
                                "• <code>/kontenjan ekle [kod] [swap]</code> : Sniper'a kurban ders ile ekle\n"
                                "• <code>/kesinlestir [ac|kapat]</code> : Otomatik kesinleştirmeyi yönet"
                            )
                            self.send_message(help_msg)
                        else:
                            self.send_message(
                                f"❓ Bilinmeyen komut: <code>{cmd}</code>.\n"
                                "Aşağıdaki butonlara tıklayabilir veya <code>/yardim</code> yazabilirsiniz."
                            )

            except Exception:
                time.sleep(3)

            time.sleep(1)
