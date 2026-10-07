"""
Proliz (GTÜ OBS) Modern Masaüstü Kontrol Arayüzü (GUI) v2.3
Yıllara göre kategorize edilmiş müfredat (1., 2., 3., 4. Sınıf sekmeleri),
spesifik Kontenjan Takipçisi (Sniper) paneli, canlı log akışı ve uzaktan Telegram yönetimi.
"""

import datetime
import json
import os
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import curriculum_data
from logger_service import ProlizLogger

try:
    from proliz_engine import ProlizEngine
except ModuleNotFoundError:
    ProlizEngine = None

try:
    from quota_watcher import QuotaWatcher
except ModuleNotFoundError:
    QuotaWatcher = None


CONFIG_FILE = "config.json"


class ProlizBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GTÜ OBS Proliz Ders Kayıt Botu 2026 - v2.2")
        self.root.geometry("1180x780")
        self.root.minsize(1050, 700)

        # Koyu Tema Renk Paleti (Obsidian Dark & Cyber Accents)
        self.colors = {
            "bg": "#0B0F19",
            "panel": "#111827",
            "panel_border": "#1F2937",
            "card": "#1E293B",
            "card_hover": "#334155",
            "accent": "#00D2D3",
            "accent_hover": "#00ECEC",
            "success": "#10B981",
            "warn": "#F59E0B",
            "danger": "#EF4444",
            "text": "#F8FAFC",
            "text_muted": "#94A3B8",
            "highlight": "#38BDF8",
        }

        self.root.configure(bg=self.colors["bg"])
        self.engine = None
        self.engine_thread = None
        self.quota_watcher = None

        # Konfigürasyonu Yükle
        self.config = self.load_config()

        # Merkezi Loglama ve Teşhis Servisi
        self.logger = ProlizLogger(gui_callback=self.append_log)

        # Müfredat Verilerini Hazırla
        self.class_trees = {}
        self.search_vars = {}

        # Arayüzü Kur
        self.setup_styles()
        self.setup_ui()

        # Kaydedilmiş Ders Planı ve Sniper Listesini Yükle
        self.refresh_selected_table()
        self.refresh_sniper_table()
        self.update_totals()

        # Telegram Bildirim Servisi
        self.telegram = None
        self.init_telegram_service()

    # ----------------------------------------------------
    # STİLLER VE TEMA
    # ----------------------------------------------------
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "TNotebook",
            background=self.colors["bg"],
            borderwidth=0,
        )
        style.configure(
            "TNotebook.Tab",
            background=self.colors["panel"],
            foreground=self.colors["text"],
            padding=[16, 8],
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.colors["accent"]), ("active", self.colors["panel_border"])],
            foreground=[("selected", "#0D1117"), ("active", "#FFFFFF")],
        )

        style.configure(
            "Treeview",
            background=self.colors["card"],
            foreground=self.colors["text"],
            fieldbackground=self.colors["card"],
            rowheight=26,
            font=("Segoe UI", 9),
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background=self.colors["panel"],
            foreground=self.colors["text"],
            font=("Segoe UI", 9, "bold"),
            relief="flat",
        )
        style.map(
            "Treeview",
            background=[("selected", self.colors["accent"])],
            foreground=[("selected", "#0D1117")],
        )

    # ----------------------------------------------------
    # KONFİGÜRASYON YÖNETİMİ
    # ----------------------------------------------------
    def load_config(self):
        default_config = {
            "tc": "",
            "sifre": "",
            "target_time": "08:29:55",
            "wait_target_time": True,
            "headless": False,
            "telegram_token": "",
            "telegram_chat_id": "",
            "telegram_enabled": False,
            "telegram_listener_enabled": False,
            "auto_finalize": False,
            "quota_watch_enabled": False,
            "quota_watch_interval_minutes": 10,
            "timeout_short": 5,
            "timeout_medium": 15,
            "timeout_long": 30,
            "custom_courses": [],
            "sniper_courses": [],
            "selected_courses": [],
        }

        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    for k, v in loaded.items():
                        default_config[k] = v
            except Exception:
                pass
        return default_config

    def save_config_action(self, silent=False):
        if hasattr(self, "tc_var"):
            self.config["tc"] = self.tc_var.get().strip()
            self.config["sifre"] = self.sifre_var.get().strip()
            self.config["target_time"] = self.time_var.get().strip()
            self.config["wait_target_time"] = self.wait_time_var.get()
            self.config["headless"] = self.headless_var.get()
            self.config["auto_finalize"] = self.auto_finalize_var.get()
            self.config["quota_watch_enabled"] = self.quota_watch_var.get()
            try:
                self.config["quota_watch_interval_minutes"] = int(self.quota_interval_var.get().strip())
            except Exception:
                self.config["quota_watch_interval_minutes"] = 10

            self.config["telegram_token"] = self.tg_token_var.get().strip()
            self.config["telegram_chat_id"] = self.tg_chat_id_var.get().strip()
            self.config["telegram_enabled"] = self.tg_enabled_var.get()
            self.config["telegram_listener_enabled"] = self.tg_listener_var.get()

        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            if not silent:
                messagebox.showinfo("Başarılı", "Tüm ayarlar config.json dosyasına güvenle kaydedildi!")
        except Exception as e:
            if not silent:
                messagebox.showerror("Hata", f"Ayarlar kaydedilemedi: {e}")

    # ----------------------------------------------------
    # ANA ARAYÜZ İSKELETİ
    # ----------------------------------------------------
    def setup_ui(self):
        topbar = tk.Frame(self.root, bg=self.colors["panel"], height=52)
        topbar.pack(fill="x", side="top")

        title_lbl = tk.Label(
            topbar,
            text="GTÜ OBS PROLIZ OTOMATIK DERS KAYIT BOTU",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["accent"],
            bg=self.colors["panel"],
        )
        title_lbl.pack(side="left", padx=20, pady=12)

        self.status_badge = tk.Label(
            topbar,
            text="DURUM: BEKLİYOR",
            font=("Segoe UI", 9, "bold"),
            fg="#FFFFFF",
            bg=self.colors["panel_border"],
            padx=12,
            pady=4,
        )
        self.status_badge.pack(side="right", padx=20)

        # 3 Ana Sekme
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=8)

        self.tab_plan = tk.Frame(self.notebook, bg=self.colors["bg"])
        self.tab_credentials = tk.Frame(self.notebook, bg=self.colors["bg"])
        self.tab_logs = tk.Frame(self.notebook, bg=self.colors["bg"])

        self.notebook.add(self.tab_plan, text=" 📚 Müfredat & Ders Planı ")
        self.notebook.add(self.tab_credentials, text=" ⚙️ Giriş & Zaman Ayarları ")
        self.notebook.add(self.tab_logs, text=" 🖥️ Canlı Terminal & Kontrol ")

        self.setup_tab_plan()
        self.setup_tab_credentials()
        self.setup_tab_logs()

    # ----------------------------------------------------
    # SEKME 1: MÜFREDAT (YILLARA GÖRE) VE DERS SEÇİMİ
    # ----------------------------------------------------
    def setup_tab_plan(self):
        paned = tk.PanedWindow(self.tab_plan, orient="horizontal", bg=self.colors["bg"], bd=0, sashwidth=4)
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        # SOL: Yıllara Göre Kategorize Edilmiş Müfredat Paneli
        left_frame = tk.Frame(paned, bg=self.colors["panel"], bd=1, relief="solid")
        paned.add(left_frame, minsize=480, stretch="always")

        header_l = tk.Frame(left_frame, bg=self.colors["panel"])
        header_l.pack(fill="x", padx=12, pady=8)
        tk.Label(
            header_l,
            text="2026 GTÜ Bilgisayar Müh. Müfredat Kataloğu",
            font=("Segoe UI", 11, "bold"),
            fg=self.colors["text"],
            bg=self.colors["panel"],
        ).pack(side="left")

        # Alt Sekmeli Sınıf Kataloğu
        self.curriculum_notebook = ttk.Notebook(left_frame)
        self.curriculum_notebook.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        classes = [
            ("1. Sınıf Dersleri", "🥇 1. Sınıf"),
            ("2. Sınıf Dersleri", "🥈 2. Sınıf"),
            ("3. Sınıf Dersleri", "🥉 3. Sınıf"),
            ("4. Sınıf Dersleri", "🎓 4. Sınıf & Seçmeli"),
        ]

        for class_key, tab_title in classes:
            c_tab = tk.Frame(self.curriculum_notebook, bg=self.colors["card"])
            self.curriculum_notebook.add(c_tab, text=f" {tab_title} ")
            self.setup_class_tab_content(c_tab, class_key)

        # Özel Dersler Sekmesi
        custom_tab = tk.Frame(self.curriculum_notebook, bg=self.colors["card"])
        self.curriculum_notebook.add(custom_tab, text=" ✨ Özel Dersler ")
        self.setup_class_tab_content(custom_tab, "Özel Dersler")

        # Sol Alt Eylem Butonları
        l_actions = tk.Frame(left_frame, bg=self.colors["panel"])
        l_actions.pack(fill="x", padx=10, pady=8)

        tk.Button(
            l_actions,
            text="➕ Kayıt Planına Ekle",
            command=self.add_active_course_to_plan,
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["accent"],
            fg="#0D1117",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            l_actions,
            text="🎯 Kontenjan Sniper'a Ekle",
            command=self.add_active_course_to_sniper,
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["warn"],
            fg="#0D1117",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
        ).pack(side="left", padx=6)

        tk.Button(
            l_actions,
            text="✨ Özel / Müfredat Dışı Ders Ekle",
            command=self.prompt_custom_course_dialog,
            font=("Segoe UI", 9),
            bg=self.colors["card"],
            fg=self.colors["text"],
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
        ).pack(side="right")

        # SAĞ: Kayıt Planı ve Spesifik Kontenjan Takipçisi (Sniper)
        right_frame = tk.Frame(paned, bg=self.colors["bg"])
        paned.add(right_frame, minsize=520, stretch="always")

        # Sağ Üst: Kayıt Planı
        plan_card = tk.Frame(right_frame, bg=self.colors["panel"], bd=1, relief="solid")
        plan_card.pack(fill="both", expand=True, pady=(0, 8))

        r_header = tk.Frame(plan_card, bg=self.colors["panel"])
        r_header.pack(fill="x", padx=12, pady=6)
        tk.Label(
            r_header,
            text="📋 Ders Kayıt Planı (Seçilen Dersler)",
            font=("Segoe UI", 11, "bold"),
            fg=self.colors["text"],
            bg=self.colors["panel"],
        ).pack(side="left")

        tk.Button(
            r_header,
            text="⚡ Hazır Planımı Yükle",
            command=self.load_preset_plan,
            font=("Segoe UI", 8, "bold"),
            bg=self.colors["accent"],
            fg="#0D1117",
            relief="flat",
            padx=8,
            pady=2,
            cursor="hand2",
        ).pack(side="right")

        self.sel_tree = ttk.Treeview(
            plan_card,
            columns=("no", "sinif", "kod", "sube", "akts", "kredi"),
            show="headings",
            selectmode="browse",
            height=6,
        )
        self.sel_tree.heading("no", text="#")
        self.sel_tree.heading("sinif", text="Sınıf")
        self.sel_tree.heading("kod", text="Ders Kodu")
        self.sel_tree.heading("sube", text="Şube / Alt Tercihler")
        self.sel_tree.heading("akts", text="AKTS")
        self.sel_tree.heading("kredi", text="Kredi")

        self.sel_tree.column("no", width=28, anchor="center")
        self.sel_tree.column("sinif", width=80, anchor="center")
        self.sel_tree.column("kod", width=90, anchor="w")
        self.sel_tree.column("sube", width=180, anchor="w")
        self.sel_tree.column("akts", width=45, anchor="center")
        self.sel_tree.column("kredi", width=45, anchor="center")
        self.sel_tree.pack(fill="both", expand=True, padx=10, pady=4)

        # Plan Kontrolleri & Toplamlar
        r_bottom = tk.Frame(plan_card, bg=self.colors["panel"])
        r_bottom.pack(fill="x", padx=10, pady=6)

        self.totals_lbl = tk.Label(
            r_bottom,
            text="Toplam AKTS: 0  |  Toplam Kredi: 0  |  Ders Sayısı: 0",
            font=("Segoe UI", 9, "bold"),
            fg=self.colors["accent"],
            bg=self.colors["panel"],
        )
        self.totals_lbl.pack(side="left")

        tk.Button(
            r_bottom,
            text="❌ Sil",
            command=self.remove_from_plan,
            font=("Segoe UI", 8),
            bg=self.colors["danger"],
            fg="#FFFFFF",
            relief="flat",
            padx=8,
        ).pack(side="right", padx=3)
        tk.Button(
            r_bottom,
            text="⬇️ Aşağı",
            command=self.move_down,
            font=("Segoe UI", 8),
            bg=self.colors["card"],
            fg=self.colors["text"],
            relief="flat",
            padx=6,
        ).pack(side="right", padx=3)
        tk.Button(
            r_bottom,
            text="⬆️ Yukarı",
            command=self.move_up,
            font=("Segoe UI", 8),
            bg=self.colors["card"],
            fg=self.colors["text"],
            relief="flat",
            padx=6,
        ).pack(side="right", padx=3)

        # Sağ Alt: SPESİFİK KONTENJAN SNIPER LİSTESİ
        sniper_card = tk.Frame(right_frame, bg=self.colors["panel"], bd=1, relief="solid")
        sniper_card.pack(fill="both", expand=True)

        sn_header = tk.Frame(sniper_card, bg=self.colors["panel"])
        sn_header.pack(fill="x", padx=12, pady=6)
        tk.Label(
            sn_header,
            text="🎯 Kontenjan Takipçisi (Sniper) Listesi",
            font=("Segoe UI", 11, "bold"),
            fg=self.colors["warn"],
            bg=self.colors["panel"],
        ).pack(side="left")

        tk.Label(
            sn_header,
            text="(10 dakikada bir otomatik yer arar)",
            font=("Segoe UI", 8),
            fg=self.colors["text_muted"],
            bg=self.colors["panel"],
        ).pack(side="left", padx=8)

        self.sniper_tree = ttk.Treeview(
            sniper_card,
            columns=("kod", "ad", "sinif", "sube", "swap"),
            show="headings",
            selectmode="browse",
            height=5,
        )
        self.sniper_tree.heading("kod", text="Ders Kodu")
        self.sniper_tree.heading("ad", text="Ders Adı")
        self.sniper_tree.heading("sinif", text="Sınıf")
        self.sniper_tree.heading("sube", text="Şube / Alt Ders")
        self.sniper_tree.heading("swap", text="Silinecek Ders (Takas / Swap)")

        self.sniper_tree.column("kod", width=75, anchor="center")
        self.sniper_tree.column("ad", width=130, anchor="w")
        self.sniper_tree.column("sinif", width=80, anchor="center")
        self.sniper_tree.column("sube", width=140, anchor="w")
        self.sniper_tree.column("swap", width=110, anchor="center")
        self.sniper_tree.pack(fill="both", expand=True, padx=10, pady=4)

        sn_bottom = tk.Frame(sniper_card, bg=self.colors["panel"])
        sn_bottom.pack(fill="x", padx=10, pady=6)

        tk.Button(
            sn_bottom,
            text="🎯 Sniper'ı Başlat",
            command=self.start_standalone_sniper,
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["warn"],
            fg="#0D1117",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
        ).pack(side="left", padx=(0, 4))

        tk.Button(
            sn_bottom,
            text="⚡ Anlık Kontrol",
            command=self.trigger_check_now_gui,
            font=("Segoe UI", 8, "bold"),
            bg=self.colors["card"],
            fg=self.colors["accent"],
            relief="flat",
            padx=8,
            pady=4,
            cursor="hand2",
        ).pack(side="left", padx=4)

        tk.Button(
            sn_bottom,
            text="🔄 Takas Dersi Belirle",
            command=self.prompt_set_swap_dialog,
            font=("Segoe UI", 8, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"],
            relief="flat",
            padx=8,
            pady=4,
            cursor="hand2",
        ).pack(side="left", padx=4)

        tk.Button(
            sn_bottom,
            text="❌ Çıkar",
            command=self.remove_from_sniper,
            font=("Segoe UI", 8),
            bg=self.colors["danger"],
            fg="#FFFFFF",
            relief="flat",
            padx=8,
        ).pack(side="right")

    def setup_class_tab_content(self, parent_tab, class_key):
        """Her sınıf sekmesine özel filtreleme ve Treeview ekler."""
        search_frame = tk.Frame(parent_tab, bg=self.colors["card"])
        search_frame.pack(fill="x", padx=6, pady=4)

        tk.Label(search_frame, text="🔍 Ara:", font=("Segoe UI", 8), fg=self.colors["text_muted"], bg=self.colors["card"]).pack(side="left", padx=4)
        s_var = tk.StringVar()
        self.search_vars[class_key] = s_var
        s_entry = tk.Entry(
            search_frame,
            textvariable=s_var,
            font=("Segoe UI", 9),
            bg=self.colors["panel"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
        )
        s_entry.pack(side="left", fill="x", expand=True, padx=4)

        tree = ttk.Treeview(
            parent_tab,
            columns=("kod", "ad", "akts", "kredi", "tip"),
            show="headings",
            selectmode="browse",
        )
        tree.heading("kod", text="Ders Kodu")
        tree.heading("ad", text="Ders Adı")
        tree.heading("akts", text="AKTS")
        tree.heading("kredi", text="Kredi")
        tree.heading("tip", text="Tip")

        tree.column("kod", width=80, anchor="center")
        tree.column("ad", width=210, anchor="w")
        tree.column("akts", width=42, anchor="center")
        tree.column("kredi", width=42, anchor="center")
        tree.column("tip", width=90, anchor="center")

        tree_scroll = ttk.Scrollbar(parent_tab, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=tree_scroll.set)

        tree.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=4)
        tree_scroll.pack(side="right", fill="y", padx=(0, 6), pady=4)

        self.class_trees[class_key] = tree
        s_var.trace_add("write", lambda *args, ck=class_key: self.filter_class_tree(ck))
        self.populate_class_tree(class_key)

    def populate_class_tree(self, class_key):
        """Müfredat derslerini ilgili sınıf tablosuna doldurur."""
        tree = self.class_trees.get(class_key)
        if not tree:
            return
        tree.delete(*tree.get_children())

        courses = []
        if class_key == "Özel Dersler":
            courses = self.config.get("custom_courses", [])
        elif class_key in curriculum_data.CURRICULUM_SEMESTERS:
            for donem, d_list in curriculum_data.CURRICULUM_SEMESTERS[class_key].items():
                for c in d_list:
                    item = dict(c)
                    item["sinif"] = class_key
                    courses.append(item)

        for c in courses:
            tree.insert(
                "",
                "end",
                values=(c.get("kod", ""), c.get("ad", ""), c.get("akts", 0), c.get("kredi", 0), c.get("tip", "Zorunlu")),
            )

    def filter_class_tree(self, class_key):
        tree = self.class_trees.get(class_key)
        s_text = self.search_vars.get(class_key, tk.StringVar()).get().strip().lower()
        self.populate_class_tree(class_key)
        if not s_text:
            return

        for child in list(tree.get_children()):
            vals = tree.item(child, "values")
            if s_text not in str(vals[0]).lower() and s_text not in str(vals[1]).lower():
                tree.delete(child)

    def get_active_selected_course(self):
        """Kullanıcının aktif müfredat sekmesinde seçtiği dersi döndürür."""
        curr_idx = self.curriculum_notebook.index(self.curriculum_notebook.select())
        tab_names = ["1. Sınıf Dersleri", "2. Sınıf Dersleri", "3. Sınıf Dersleri", "4. Sınıf Dersleri", "Özel Dersler"]
        if curr_idx >= len(tab_names):
            return None

        class_key = tab_names[curr_idx]
        tree = self.class_trees.get(class_key)
        if not tree:
            return None

        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Lütfen önce soldaki tablodan bir ders seçin!")
            return None

        vals = tree.item(sel[0], "values")
        kod = vals[0]
        ad = vals[1]
        akts = int(vals[2]) if vals[2] else 0
        kredi = int(vals[3]) if vals[3] else 0
        tip = vals[4]

        # Seçmeli ders alt şubeleri
        sub_choices = [kod]
        if "Seçmeli" in tip or "Elective" in kod or kod in curriculum_data.ELECTIVE_GROUPS:
            sub_choices = self.prompt_sub_course_dialog(kod)
            if not sub_choices:
                return None

        sinif_adi = class_key if class_key != "Özel Dersler" else "4. Sınıf Dersleri"
        return {
            "sinif": sinif_adi,
            "kod": kod,
            "ad": ad,
            "akts": akts,
            "kredi": kredi,
            "tip": tip,
            "sub_choices": sub_choices,
        }

    def add_active_course_to_plan(self):
        course = self.get_active_selected_course()
        if not course:
            return

        for c in self.config.setdefault("selected_courses", []):
            if c.get("kod") == course["kod"]:
                messagebox.showinfo("Bilgi", f"'{course['kod']}' zaten kayıt planınızda mevcut!")
                return

        self.config["selected_courses"].append(course)
        self.refresh_selected_table()
        self.update_totals()
        self.save_config_action(silent=True)

    def add_active_course_to_sniper(self):
        course = self.get_active_selected_course()
        if not course:
            return

        for sc in self.config.setdefault("sniper_courses", []):
            if sc.get("kod") == course["kod"]:
                messagebox.showinfo("Bilgi", f"'{course['kod']}' zaten Kontenjan Sniper listesinde!")
                return

        self.config["sniper_courses"].append(course)
        self.refresh_sniper_table()
        self.save_config_action(silent=True)
        messagebox.showinfo("Başarılı", f"🎯 '{course['kod']}' Kontenjan Sniper listesine eklendi!")

    def prompt_sub_course_dialog(self, slot_code):
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Seçmeli Ders Tercihi: {slot_code}")
        dialog.geometry("600x480")
        dialog.configure(bg=self.colors["bg"])
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(
            dialog,
            text=f"'{slot_code}' İçin Açılmasını / Seçilmesini İstediğiniz Dersler",
            font=("Segoe UI", 11, "bold"),
            fg=self.colors["accent"],
            bg=self.colors["bg"],
        ).pack(padx=16, pady=(12, 4), anchor="w")

        tk.Label(
            dialog,
            text="Tercih sırasına göre şubeleri seçin (Kontenjan açıldığında ilk açık olan kapılır):",
            font=("Segoe UI", 9),
            fg=self.colors["text_muted"],
            bg=self.colors["bg"],
        ).pack(padx=16, pady=(0, 8), anchor="w")

        alt_dersler = curriculum_data.ELECTIVE_GROUPS.get(slot_code, [])
        list_frame = tk.Frame(dialog, bg=self.colors["panel"])
        list_frame.pack(fill="both", expand=True, padx=16, pady=4)

        sub_listbox = tk.Listbox(
            list_frame,
            selectmode="extended",
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=("Segoe UI", 10),
            borderwidth=0,
            highlightthickness=0,
        )
        sub_listbox.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        for d in alt_dersler:
            sub_listbox.insert("end", f"{d['kod']} - {d['ad']}")

        selected_result = []

        def on_confirm():
            idxs = sub_listbox.curselection()
            if not idxs:
                messagebox.showwarning("Uyarı", "Lütfen en az 1 tercih seçin!", parent=dialog)
                return
            for idx in idxs:
                selected_result.append(alt_dersler[idx]["kod"])
            dialog.destroy()

        tk.Button(
            dialog,
            text="Seçimi Onayla",
            command=on_confirm,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["success"],
            fg="#FFFFFF",
            relief="flat",
            padx=16,
            pady=6,
        ).pack(pady=10)

        self.root.wait_window(dialog)
        return selected_result

    def prompt_custom_course_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Özel / Manuel Ders Ekle")
        dialog.geometry("520x450")
        dialog.configure(bg=self.colors["bg"])
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="✨ Yeni / Müfredat Dışı Ders Tanımla",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["accent"],
            bg=self.colors["bg"],
        ).pack(padx=20, pady=(15, 10), anchor="w")

        form = tk.Frame(dialog, bg=self.colors["panel"], bd=1, relief="solid")
        form.pack(fill="x", padx=20, pady=10)

        # Ders Kodu
        tk.Label(form, text="Ders Kodu (Örn: MATH 215):", font=("Segoe UI", 9, "bold"), fg=self.colors["text"], bg=self.colors["panel"]).grid(row=0, column=0, sticky="w", padx=15, pady=6)
        kod_var = tk.StringVar()
        tk.Entry(form, textvariable=kod_var, font=("Segoe UI", 10), bg=self.colors["card"], fg=self.colors["text"], relief="flat", width=22).grid(row=0, column=1, sticky="w", padx=10, pady=6)

        # Ders Adı
        tk.Label(form, text="Ders Adı:", font=("Segoe UI", 9, "bold"), fg=self.colors["text"], bg=self.colors["panel"]).grid(row=1, column=0, sticky="w", padx=15, pady=6)
        ad_var = tk.StringVar()
        tk.Entry(form, textvariable=ad_var, font=("Segoe UI", 10), bg=self.colors["card"], fg=self.colors["text"], relief="flat", width=22).grid(row=1, column=1, sticky="w", padx=10, pady=6)

        # Sınıf Sekmesi
        tk.Label(form, text="Sınıf Sekmesi (OBS):", font=("Segoe UI", 9, "bold"), fg=self.colors["text"], bg=self.colors["panel"]).grid(row=2, column=0, sticky="w", padx=15, pady=6)
        sinif_var = tk.StringVar(value="4. Sınıf Dersleri")
        ttk.Combobox(form, textvariable=sinif_var, values=["1. Sınıf Dersleri", "2. Sınıf Dersleri", "3. Sınıf Dersleri", "4. Sınıf Dersleri"], state="readonly", width=20).grid(row=2, column=1, sticky="w", padx=10, pady=6)

        # Alt Tercihler
        tk.Label(form, text="Alt Tercihler / Şubeler:\n(Virgülle ayırın)", font=("Segoe UI", 9, "bold"), fg=self.colors["text"], bg=self.colors["panel"]).grid(row=3, column=0, sticky="nw", padx=15, pady=6)
        sub_var = tk.StringVar()
        tk.Entry(form, textvariable=sub_var, font=("Segoe UI", 10), bg=self.colors["card"], fg=self.colors["text"], relief="flat", width=22).grid(row=3, column=1, sticky="w", padx=10, pady=6)

        def on_save():
            kod = kod_var.get().strip().upper()
            ad = ad_var.get().strip() or kod
            if not kod:
                messagebox.showwarning("Uyarı", "Ders Kodu boş olamaz!", parent=dialog)
                return
            raw_sub = sub_var.get().strip()
            sub_choices = [s.strip() for s in raw_sub.split(",") if s.strip()] if raw_sub else [kod]

            new_c = {
                "kod": kod,
                "ad": ad,
                "sinif": sinif_var.get(),
                "akts": 5,
                "kredi": 3,
                "tip": "Özel / Saydırma",
                "sub_choices": sub_choices,
            }
            self.config.setdefault("custom_courses", []).append(new_c)
            self.populate_class_tree("Özel Dersler")
            self.config.setdefault("selected_courses", []).append(new_c)
            self.refresh_selected_table()
            self.update_totals()
            self.save_config_action(silent=True)
            messagebox.showinfo("Başarılı", f"'{kod}' dersi plana eklendi!", parent=dialog)
            dialog.destroy()

        tk.Button(dialog, text="Müfredata ve Plana Ekle", command=on_save, font=("Segoe UI", 10, "bold"), bg=self.colors["success"], fg="#FFFFFF", relief="flat", padx=14, pady=6).pack(pady=12)

    def refresh_selected_table(self):
        self.sel_tree.delete(*self.sel_tree.get_children())
        for i, c in enumerate(self.config.get("selected_courses", []), 1):
            sub_str = ", ".join(c.get("sub_choices", [c.get("kod", "")]))
            self.sel_tree.insert(
                "", "end",
                values=(i, c.get("sinif", ""), c.get("kod", ""), sub_str, c.get("akts", 0), c.get("kredi", 0)),
            )

    def refresh_sniper_table(self):
        self.sniper_tree.delete(*self.sniper_tree.get_children())
        for sc in self.config.get("sniper_courses", []):
            sub_str = ", ".join(sc.get("sub_choices", [sc.get("kod", "")]))
            swap_str = sc.get("swap_course", "-") or "-"
            self.sniper_tree.insert(
                "", "end",
                values=(sc.get("kod", ""), sc.get("ad", ""), sc.get("sinif", ""), sub_str, swap_str),
            )

    def prompt_set_swap_dialog(self):
        """Seçilen sniper dersi için kontenjan açıldığında silinecek takas dersini ayarlar."""
        sel = self.sniper_tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Lütfen önce Sniper tablosundan bir ders seçin!")
            return
        kod = self.sniper_tree.item(sel[0], "values")[0]

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Takas Kuralı Belirle: {kod}")
        dialog.geometry("480x300")
        dialog.configure(bg=self.colors["bg"])
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(
            dialog,
            text=f"🔄 '{kod}' Açıldığında Silinecek Ders",
            font=("Segoe UI", 11, "bold"),
            fg=self.colors["warn"],
            bg=self.colors["bg"],
        ).pack(padx=16, pady=(15, 6), anchor="w")

        tk.Label(
            dialog,
            text="Bu dersin kontenjanı boşaldığında OBS'den otomatik silinmesini istediğiniz kurban dersi seçin:",
            font=("Segoe UI", 9),
            fg=self.colors["text_muted"],
            bg=self.colors["bg"],
            wraplength=440,
            justify="left"
        ).pack(padx=16, pady=(0, 10), anchor="w")

        plan_codes = [c.get("kod") for c in self.config.get("selected_courses", [])]
        swap_var = tk.StringVar()

        f = tk.Frame(dialog, bg=self.colors["panel"], bd=1, relief="solid")
        f.pack(fill="x", padx=16, pady=6, ipady=8, ipadx=8)

        tk.Label(f, text="Silinecek Ders:", font=("Segoe UI", 9, "bold"), fg=self.colors["text"], bg=self.colors["panel"]).grid(row=0, column=0, padx=8, pady=4, sticky="w")
        combo = ttk.Combobox(f, textvariable=swap_var, values=plan_codes, font=("Segoe UI", 10), width=22)
        combo.grid(row=0, column=1, padx=8, pady=4, sticky="w")
        if plan_codes:
            combo.set(plan_codes[0])

        def on_confirm():
            val = swap_var.get().strip().upper()
            if not val:
                messagebox.showwarning("Uyarı", "Lütfen silinecek dersi seçin veya yazın!", parent=dialog)
                return
            for sc in self.config.get("sniper_courses", []):
                if sc.get("kod") == kod:
                    sc["swap_course"] = val
                    break
            self.refresh_sniper_table()
            self.save_config_action(silent=True)
            messagebox.showinfo("Başarılı", f"'{kod}' açıldığında '{val}' silinecek şekilde takas kuralı tanımlandı!", parent=dialog)
            dialog.destroy()

        tk.Button(dialog, text="Takas Kuralını Kaydet", command=on_confirm, font=("Segoe UI", 10, "bold"), bg=self.colors["success"], fg="#FFFFFF", relief="flat", padx=16, pady=6).pack(pady=15)

    def trigger_check_now_gui(self):
        """GUI üzerinden anlık kontenjan taramasını tetikler."""
        if self.quota_watcher and self.quota_watcher.is_running:
            self.quota_watcher.check_now()
            self.append_log("⚡ Anlık kontenjan taraması tetiklendi.", "INFO")
        elif self.engine and getattr(self.engine, "driver", None):
            self.start_standalone_sniper()
        else:
            messagebox.showinfo("Bilgi", "Oturum açık değil. Önce '🎯 Sniper'ı Başlat' veya '🚀 Savaşı Başlat' ile motoru çalıştırın.")

    def remove_from_plan(self):
        selected = self.sel_tree.selection()
        if not selected:
            return
        idx = int(self.sel_tree.item(selected[0], "values")[0]) - 1
        self.config["selected_courses"].pop(idx)
        self.refresh_selected_table()
        self.update_totals()
        self.save_config_action(silent=True)

    def remove_from_sniper(self):
        selected = self.sniper_tree.selection()
        if not selected:
            return
        kod = self.sniper_tree.item(selected[0], "values")[0]
        self.config["sniper_courses"] = [sc for sc in self.config.get("sniper_courses", []) if sc.get("kod") != kod]
        self.refresh_sniper_table()
        self.save_config_action(silent=True)

    def move_up(self):
        selected = self.sel_tree.selection()
        if not selected:
            return
        idx = int(self.sel_tree.item(selected[0], "values")[0]) - 1
        if idx > 0:
            courses = self.config["selected_courses"]
            courses[idx], courses[idx - 1] = courses[idx - 1], courses[idx]
            self.refresh_selected_table()
            self.sel_tree.selection_set(self.sel_tree.get_children()[idx - 1])
            self.save_config_action(silent=True)

    def move_down(self):
        selected = self.sel_tree.selection()
        if not selected:
            return
        idx = int(self.sel_tree.item(selected[0], "values")[0]) - 1
        courses = self.config["selected_courses"]
        if idx < len(courses) - 1:
            courses[idx], courses[idx + 1] = courses[idx + 1], courses[idx]
            self.refresh_selected_table()
            self.sel_tree.selection_set(self.sel_tree.get_children()[idx + 1])
            self.save_config_action(silent=True)

    def update_totals(self):
        courses = self.config.get("selected_courses", [])
        total_akts = sum(c.get("akts", 0) for c in courses)
        total_kredi = sum(c.get("kredi", 0) for c in courses)
        akts_status = "  ⚠️ (35 AKTS Sınırı Aşıldı!)" if total_akts > 35 else ""
        self.totals_lbl.configure(
            text=f"📊 Toplam AKTS: {total_akts} / 35  |  Kredi: {total_kredi}  |  Ders: {len(courses)}{akts_status}",
            fg=self.colors["danger"] if total_akts > 35 else self.colors["accent"]
        )

    def load_preset_plan(self):
        preset = [
            {"sinif": "2. Sınıf Dersleri", "kod": "CSE 231", "ad": "Circuits and Electronics", "akts": 6, "kredi": 5, "tip": "Zorunlu", "sub_choices": ["CSE 231"]},
            {"sinif": "2. Sınıf Dersleri", "kod": "NonTElec3[0-1]", "ad": "Non-Technical Elective I", "akts": 3, "kredi": 2, "tip": "Seçmeli (Non-Tech)", "sub_choices": ["GTU 110", "ENG 250", "BUS 403"]},
            {"sinif": "3. Sınıf Dersleri", "kod": "CSE 331", "ad": "Computer Organization", "akts": 6, "kredi": 4, "tip": "Zorunlu", "sub_choices": ["CSE 331"]},
            {"sinif": "3. Sınıf Dersleri", "kod": "CSE 355", "ad": "Numerical Analysis in Computer Engineering", "akts": 8, "kredi": 4, "tip": "Zorunlu", "sub_choices": ["CSE 355"]},
            {"sinif": "3. Sınıf Dersleri", "kod": "CSE 396", "ad": "Computer Engineering Project", "akts": 5, "kredi": 3, "tip": "Zorunlu", "sub_choices": ["CSE 396"]},
            {"sinif": "4. Sınıf Dersleri", "kod": "DElec7[0-3]", "ad": "Departmental Elective I", "akts": 6, "kredi": 3, "tip": "Seçmeli", "sub_choices": ["CSE 426", "CSE 476", "CSE 464"]},
        ]
        self.config["selected_courses"] = preset
        self.refresh_selected_table()
        self.update_totals()
        self.save_config_action(silent=True)
        messagebox.showinfo("Başarılı", "Fotoğraftaki güncel ders planınız başarıyla yüklendi!")

    # ----------------------------------------------------
    # SEKME 2: GİRİŞ, ZAMAN VE TELEGRAM AYARLARI
    # ----------------------------------------------------
    def setup_tab_credentials(self):
        container = tk.Frame(self.tab_credentials, bg=self.colors["bg"])
        container.pack(fill="both", expand=True, padx=30, pady=15)

        # Kart 1: e-Devlet Bilgileri
        card1 = tk.Frame(container, bg=self.colors["panel"], bd=1, relief="solid")
        card1.pack(fill="x", pady=6, ipady=8, ipadx=12)

        tk.Label(card1, text="🔑 e-Devlet Kimlik Bilgileri", font=("Segoe UI", 11, "bold"), fg=self.colors["text"], bg=self.colors["panel"]).grid(row=0, column=0, columnspan=3, sticky="w", padx=16, pady=(6, 10))

        tk.Label(card1, text="T.C. Kimlik No:", font=("Segoe UI", 9), fg=self.colors["text_muted"], bg=self.colors["panel"]).grid(row=1, column=0, sticky="w", padx=16, pady=4)
        self.tc_var = tk.StringVar(value=self.config.get("tc", ""))
        tk.Entry(card1, textvariable=self.tc_var, font=("Segoe UI", 10), width=24, bg=self.colors["card"], fg=self.colors["text"], insertbackground=self.colors["text"], relief="flat").grid(row=1, column=1, sticky="w", padx=8, pady=4)

        tk.Label(card1, text="e-Devlet Şifresi:", font=("Segoe UI", 9), fg=self.colors["text_muted"], bg=self.colors["panel"]).grid(row=2, column=0, sticky="w", padx=16, pady=4)
        self.sifre_var = tk.StringVar(value=self.config.get("sifre", ""))
        self.sifre_entry = tk.Entry(card1, textvariable=self.sifre_var, font=("Segoe UI", 10), width=24, bg=self.colors["card"], fg=self.colors["text"], insertbackground=self.colors["text"], show="*", relief="flat")
        self.sifre_entry.grid(row=2, column=1, sticky="w", padx=8, pady=4)

        self.show_pw_var = tk.BooleanVar(value=False)
        tk.Checkbutton(card1, text="Göster", variable=self.show_pw_var, command=self.toggle_password, bg=self.colors["panel"], fg=self.colors["text"], selectcolor=self.colors["card"], activebackground=self.colors["panel"]).grid(row=2, column=2, sticky="w", padx=6)

        # Kart 2: Zaman & Kesinleştirme Seçenekleri
        card2 = tk.Frame(container, bg=self.colors["panel"], bd=1, relief="solid")
        card2.pack(fill="x", pady=6, ipady=8, ipadx=12)

        tk.Label(card2, text="⏰ Zamanlayıcı ve Otomasyon Seçenekleri", font=("Segoe UI", 11, "bold"), fg=self.colors["text"], bg=self.colors["panel"]).grid(row=0, column=0, columnspan=3, sticky="w", padx=16, pady=(6, 8))

        tk.Label(card2, text="Hedef Başlama Saati:", font=("Segoe UI", 9), fg=self.colors["text_muted"], bg=self.colors["panel"]).grid(row=1, column=0, sticky="w", padx=16, pady=4)
        self.time_var = tk.StringVar(value=self.config.get("target_time", "08:29:55"))
        tk.Entry(card2, textvariable=self.time_var, font=("Segoe UI", 10), width=12, bg=self.colors["card"], fg=self.colors["text"], insertbackground=self.colors["text"], relief="flat").grid(row=1, column=1, sticky="w", padx=8, pady=4)

        self.wait_time_var = tk.BooleanVar(value=self.config.get("wait_target_time", True))
        tk.Checkbutton(card2, text="Belirlenen Saate Kadar Bekle ve Oturumu Canlı Tut", variable=self.wait_time_var, font=("Segoe UI", 9), bg=self.colors["panel"], fg=self.colors["text"], selectcolor=self.colors["card"], activebackground=self.colors["panel"]).grid(row=1, column=2, sticky="w", padx=8)

        self.auto_finalize_var = tk.BooleanVar(value=self.config.get("auto_finalize", False))
        tk.Checkbutton(card2, text="⚡ Otomatik Kesinleştir (Kontrol Et sonrası 'Evet' onayını da kendi versin)", variable=self.auto_finalize_var, font=("Segoe UI", 9, "bold"), fg=self.colors["accent"], bg=self.colors["panel"], selectcolor=self.colors["card"], activebackground=self.colors["panel"]).grid(row=2, column=0, columnspan=3, sticky="w", padx=16, pady=4)

        self.quota_watch_var = tk.BooleanVar(value=self.config.get("quota_watch_enabled", False))
        tk.Checkbutton(card2, text="🎯 10 Dakikalık Kontenjan Takipçisi (Sniper):", variable=self.quota_watch_var, font=("Segoe UI", 9), fg=self.colors["warn"], bg=self.colors["panel"], selectcolor=self.colors["card"], activebackground=self.colors["panel"]).grid(row=3, column=0, columnspan=2, sticky="w", padx=16, pady=4)

        interval_f = tk.Frame(card2, bg=self.colors["panel"])
        interval_f.grid(row=3, column=2, sticky="w", padx=8)
        self.quota_interval_var = tk.StringVar(value=str(self.config.get("quota_watch_interval_minutes", 10)))
        tk.Entry(interval_f, textvariable=self.quota_interval_var, width=4, font=("Segoe UI", 9), bg=self.colors["card"], fg=self.colors["text"], relief="flat").pack(side="left")
        tk.Label(interval_f, text=" dakikada bir kontrol et", font=("Segoe UI", 9), fg=self.colors["text_muted"], bg=self.colors["panel"]).pack(side="left")

        self.headless_var = tk.BooleanVar(value=self.config.get("headless", False))
        tk.Checkbutton(card2, text="Arka Planda Gizli Çalıştır (Headless)", variable=self.headless_var, font=("Segoe UI", 8), bg=self.colors["panel"], fg=self.colors["text_muted"], selectcolor=self.colors["card"], activebackground=self.colors["panel"]).grid(row=4, column=0, columnspan=2, sticky="w", padx=16, pady=2)

        # Kart 3: Telegram Uzaktan Yönetim
        card3 = tk.Frame(container, bg=self.colors["panel"], bd=1, relief="solid")
        card3.pack(fill="x", pady=6, ipady=8, ipadx=12)

        tk.Label(card3, text="📱 Telegram Bildirim & Uzaktan Kontrol", font=("Segoe UI", 11, "bold"), fg=self.colors["text"], bg=self.colors["panel"]).grid(row=0, column=0, columnspan=3, sticky="w", padx=16, pady=(6, 8))

        tk.Label(card3, text="Bot Token:", font=("Segoe UI", 9), fg=self.colors["text_muted"], bg=self.colors["panel"]).grid(row=1, column=0, sticky="w", padx=16, pady=4)
        self.tg_token_var = tk.StringVar(value=self.config.get("telegram_token", ""))
        tk.Entry(card3, textvariable=self.tg_token_var, font=("Segoe UI", 9), width=34, bg=self.colors["card"], fg=self.colors["text"], insertbackground=self.colors["text"], relief="flat").grid(row=1, column=1, sticky="w", padx=8, pady=4)

        tk.Label(card3, text="Chat ID:", font=("Segoe UI", 9), fg=self.colors["text_muted"], bg=self.colors["panel"]).grid(row=2, column=0, sticky="w", padx=16, pady=4)
        self.tg_chat_id_var = tk.StringVar(value=self.config.get("telegram_chat_id", ""))
        tk.Entry(card3, textvariable=self.tg_chat_id_var, font=("Segoe UI", 9), width=20, bg=self.colors["card"], fg=self.colors["text"], insertbackground=self.colors["text"], relief="flat").grid(row=2, column=1, sticky="w", padx=8, pady=4)

        self.tg_test_btn = tk.Button(
            card3,
            text="📲 Test Bildirimi Gönder",
            command=self.test_telegram_action,
            font=("Segoe UI", 8, "bold"),
            bg=self.colors["accent"],
            fg="#0D1117",
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
        )
        self.tg_test_btn.grid(row=2, column=2, sticky="w", padx=10)

        self.tg_enabled_var = tk.BooleanVar(value=self.config.get("telegram_enabled", True))
        tk.Checkbutton(card3, text="Telegram Bildirimlerini Etkinleştir", variable=self.tg_enabled_var, font=("Segoe UI", 9), bg=self.colors["panel"], fg=self.colors["text"], selectcolor=self.colors["card"], activebackground=self.colors["panel"]).grid(row=3, column=0, columnspan=2, sticky="w", padx=16, pady=3)

        self.tg_listener_var = tk.BooleanVar(value=self.config.get("telegram_listener_enabled", True))
        tk.Checkbutton(card3, text="🤖 Uzaktan Komut Dinleyicisini Aç (/baslat, /durum, /kontenjan)", variable=self.tg_listener_var, font=("Segoe UI", 9), fg=self.colors["accent"], bg=self.colors["panel"], selectcolor=self.colors["card"], activebackground=self.colors["panel"]).grid(row=4, column=0, columnspan=2, sticky="w", padx=16, pady=3)

        tk.Button(container, text="💾 TÜM AYARLARI KAYDET", command=self.save_config_action, font=("Segoe UI", 10, "bold"), bg=self.colors["success"], fg="#FFFFFF", relief="flat", padx=20, pady=6, cursor="hand2").pack(pady=10)

    def toggle_password(self):
        self.sifre_entry.configure(show="" if self.show_pw_var.get() else "*")

    # ----------------------------------------------------
    # SEKME 3: CANLI TERMİNAL & ÇALIŞTIRMA KONTROLÜ
    # ----------------------------------------------------
    def setup_tab_logs(self):
        container = tk.Frame(self.tab_logs, bg=self.colors["bg"])
        container.pack(fill="both", expand=True, padx=15, pady=10)

        action_bar = tk.Frame(container, bg=self.colors["panel"], bd=1, relief="solid")
        action_bar.pack(fill="x", pady=(0, 10), ipady=8, ipadx=10)

        self.start_btn = tk.Button(
            action_bar,
            text="🚀 SAVAŞI BAŞLAT (Dersleri Kaydet)",
            command=self.start_bot_thread,
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["success"],
            fg="#FFFFFF",
            relief="flat",
            padx=16,
            pady=6,
            cursor="hand2",
        )
        self.start_btn.pack(side="left", padx=8)

        self.sniper_btn = tk.Button(
            action_bar,
            text="🎯 KONTENJAN SNIPER'I BAŞLAT",
            command=self.start_standalone_sniper,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["warn"],
            fg="#0D1117",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
        )
        self.sniper_btn.pack(side="left", padx=8)

        self.test_login_btn = tk.Button(
            action_bar,
            text="🔑 Sadece Giriş Yap & Bekle",
            command=self.start_test_login_thread,
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["card"],
            fg=self.colors["text"],
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
        )
        self.test_login_btn.pack(side="left", padx=6)

        self.check_now_btn = tk.Button(
            action_bar,
            text="⚡ Anlık Kontrol Et",
            command=self.trigger_check_now_gui,
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["card"],
            fg=self.colors["accent"],
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
        )
        self.check_now_btn.pack(side="left", padx=6)

        self.ss_btn = tk.Button(
            action_bar,
            text="📸 Canlı Ekran (SS)",
            command=self.capture_screenshot_gui,
            font=("Segoe UI", 9, "bold"),
            bg=self.colors["card"],
            fg=self.colors["highlight"],
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
        )
        self.ss_btn.pack(side="left", padx=6)

        self.stop_btn = tk.Button(
            action_bar,
            text="🛑 DURDUR",
            command=self.stop_bot,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["danger"],
            fg="#FFFFFF",
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            state="disabled",
        )
        self.stop_btn.pack(side="right", padx=8)

        log_frame = tk.Frame(container, bg=self.colors["panel"], bd=1, relief="solid")
        log_frame.pack(fill="both", expand=True)

        header_frame = tk.Frame(log_frame, bg=self.colors["panel"])
        header_frame.pack(fill="x", padx=12, pady=6)
        tk.Label(header_frame, text="🟢 Canlı Bot Konsol Logları", font=("Segoe UI", 10, "bold"), fg=self.colors["text"], bg=self.colors["panel"]).pack(side="left")

        tk.Button(header_frame, text="Temizle", command=self.clear_logs, font=("Segoe UI", 8), bg=self.colors["card"], fg=self.colors["text_muted"], relief="flat", padx=6).pack(side="right")
        tk.Button(header_frame, text="📂 Log Klasörünü Aç", command=self.open_logs_folder, font=("Segoe UI", 8, "bold"), bg=self.colors["card"], fg=self.colors["accent"], relief="flat", padx=8).pack(side="right", padx=(0, 6))

        self.log_text = tk.Text(log_frame, bg="#05080C", fg="#C9D1D9", font=("Consolas", 10), borderwidth=0, padx=10, pady=10)
        self.log_text.pack(fill="both", expand=True, side="left")

        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=log_scroll.set)

        self.log_text.tag_configure("INFO", foreground="#58A6FF")
        self.log_text.tag_configure("SUCCESS", foreground="#3FB950")
        self.log_text.tag_configure("WARN", foreground="#D29922")
        self.log_text.tag_configure("ERROR", foreground="#F85149")
        self.log_text.tag_configure("DEBUG", foreground="#8B949E")
        self.log_text.tag_configure("DIAG", foreground="#F0883E")

    def capture_screenshot_gui(self):
        """Arayüzden anlık OBS ekran görüntüsü alır ve kaydeder."""
        if not self.engine or not getattr(self.engine, "driver", None):
            messagebox.showwarning("Uyarı", "Tarayıcı şu an açık değil!")
            return
        path = self.engine.get_screenshot()
        if path and os.path.exists(path):
            self.append_log(f"📸 Ekran görüntüsü başarıyla kaydedildi: {path}", "SUCCESS")
            try:
                os.startfile(path)
            except Exception:
                pass
        else:
            self.append_log("Ekran görüntüsü alınamadı.", "ERROR")

    def open_logs_folder(self):
        try:
            logs_dir = getattr(self.logger, "logs_dir", os.path.abspath("logs"))
            os.makedirs(logs_dir, exist_ok=True)
            os.startfile(logs_dir)
        except Exception as e:
            messagebox.showerror("Hata", f"Log klasörü açılamadı: {e}")

    def append_log(self, text, level="INFO"):
        def _log():
            if hasattr(self, "log_text") and self.log_text.winfo_exists():
                self.log_text.insert("end", text + "\n", level)
                self.log_text.see("end")
        if hasattr(self, "root") and self.root:
            self.root.after(0, _log)

    def set_gui_status(self, status_text):
        def _status():
            self.status_badge.configure(text=f"DURUM: {status_text.upper()}")
            if "BAŞARILI" in status_text.upper() or "TAMAMLANDI" in status_text.upper():
                self.status_badge.configure(bg=self.colors["success"])
            elif "HATA" in status_text.upper():
                self.status_badge.configure(bg=self.colors["danger"])
            elif "SEÇİLİYOR" in status_text.upper() or "BEKLENİYOR" in status_text.upper():
                self.status_badge.configure(bg=self.colors["warn"])
            else:
                self.status_badge.configure(bg=self.colors["panel_border"])
        self.root.after(0, _status)

    def clear_logs(self):
        self.log_text.delete("1.0", "end")

    # ----------------------------------------------------
    # BOT & THREAD YÖNETİMİ
    # ----------------------------------------------------
    def start_bot_thread(self):
        self.save_config_action(silent=True)
        if not self.config.get("tc") or not self.config.get("sifre"):
            messagebox.showerror("Hata", "Lütfen Giriş Ayarları sekmesinden T.C. Kimlik No ve Şifrenizi girin!")
            self.notebook.select(self.tab_credentials)
            return

        if not self.config.get("selected_courses"):
            messagebox.showwarning("Uyarı", "Ders listeniz boş! Soldaki tablodan ders ekleyin veya 'Hazır Planımı Yükle'ye basın.")
            self.notebook.select(self.tab_plan)
            return

        self.notebook.select(self.tab_logs)
        self.start_btn.configure(state="disabled")
        self.sniper_btn.configure(state="disabled")
        self.test_login_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        self.engine = ProlizEngine(self.config, log_cb=self.append_log, status_cb=self.set_gui_status, logger=self.logger)
        self.engine_thread = threading.Thread(target=self._run_engine_worker, daemon=True)
        self.engine_thread.start()

    def start_standalone_sniper(self):
        """Kullanıcının belirlediği spesifik dersleri doğrudan bağımsız olarak tarar."""
        self.save_config_action(silent=True)
        sniper_list = self.config.get("sniper_courses", [])
        if not sniper_list:
            messagebox.showwarning(
                "Uyarı",
                "Kontenjan Sniper listeniz boş!\n\nLütfen soldaki tablodan istediğiniz dersi seçip "
                "'🎯 Kontenjan Sniper'a Ekle' butonuna basın."
            )
            self.notebook.select(self.tab_plan)
            return

        self.notebook.select(self.tab_logs)
        self.start_btn.configure(state="disabled")
        self.sniper_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        if not self.engine:
            self.engine = ProlizEngine(self.config, log_cb=self.append_log, status_cb=self.set_gui_status, logger=self.logger)

        interval = self.config.get("quota_watch_interval_minutes", 10)
        self.quota_watcher = QuotaWatcher(
            self.engine,
            interval_minutes=interval,
            telegram_service=self.telegram,
            log_cb=self.append_log,
            status_cb=self.set_gui_status,
        )
        self.quota_watcher.set_watch_courses(sniper_list)
        self.quota_watcher.start_standalone()
        self.append_log(f"🎯 Kontenjan Sniper modu başlatıldı! ({len(sniper_list)} adet ders izleniyor)", "SUCCESS")

    def start_test_login_thread(self):
        self.save_config_action(silent=True)
        if not self.config.get("tc") or not self.config.get("sifre"):
            messagebox.showerror("Hata", "Lütfen T.C. Kimlik No ve e-Devlet Şifrenizi girin!")
            return

        self.notebook.select(self.tab_logs)
        self.start_btn.configure(state="disabled")
        self.sniper_btn.configure(state="disabled")
        self.test_login_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        test_conf = dict(self.config)
        test_conf["wait_target_time"] = False
        self.engine = ProlizEngine(test_conf, log_cb=self.append_log, status_cb=self.set_gui_status, logger=self.logger)

        def worker():
            try:
                self.engine.init_driver()
                giris_ok = self.engine.login_edevlet()
                if giris_ok:
                    self.append_log("Test girişi tamamlandı. Tarayıcı aktif açık bırakıldı.", "SUCCESS")
                    self.set_gui_status("Test Girişi Hazır")
                else:
                    self.append_log("Test girişi başarısız oldu. Log dosyasını inceleyin.", "ERROR")
                    self.set_gui_status("Giriş Başarısız")
            except Exception as e:
                self.append_log(f"Giriş testi hatası: {e}", "ERROR")
                if hasattr(self.engine, "logger"):
                    self.engine.logger.capture_diagnostic(
                        getattr(self.engine, "driver", None), "Test girişi hatası", e
                    )
            finally:
                self.root.after(0, lambda: self.start_btn.configure(state="normal"))
                self.root.after(0, lambda: self.sniper_btn.configure(state="normal"))
                self.root.after(0, lambda: self.test_login_btn.configure(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    def _run_engine_worker(self):
        try:
            self.engine.run()
        finally:
            self.root.after(0, lambda: self.start_btn.configure(state="normal"))
            self.root.after(0, lambda: self.sniper_btn.configure(state="normal"))
            self.root.after(0, lambda: self.test_login_btn.configure(state="normal"))
            self.root.after(0, lambda: self.stop_btn.configure(state="disabled"))

    def stop_bot(self):
        if self.engine:
            self.engine.stop()
        if self.quota_watcher:
            self.quota_watcher.stop()

    # ----------------------------------------------------
    # TELEGRAM ENTEGRASYONU
    # ----------------------------------------------------
    def init_telegram_service(self):
        token = self.config.get("telegram_token", "")
        chat_id = self.config.get("telegram_chat_id", "")
        if self.config.get("telegram_enabled", True) and token and chat_id:
            from telegram_service import TelegramService
            self.telegram = TelegramService(token=token, chat_id=chat_id, log_cb=self.append_log)
            self.telegram.register_command("durum", self._tg_cmd_status)
            self.telegram.register_command("baslat", self._tg_cmd_start)
            self.telegram.register_command("durdur", self._tg_cmd_stop)
            self.telegram.register_command("saat", self._tg_cmd_time)
            self.telegram.register_command("mufredat", self._tg_cmd_curriculum)
            self.telegram.register_command("altdersler", self._tg_cmd_subcourses)
            self.telegram.register_command("altders", self._tg_cmd_subcourses)
            self.telegram.register_command("secimler", self._tg_cmd_subcourses)
            self.telegram.register_command("plan", self._tg_cmd_plan)
            self.telegram.register_command("dersler", self._tg_cmd_plan)
            self.telegram.register_command("ekle", self._tg_cmd_add)
            self.telegram.register_command("sil", self._tg_cmd_remove)
            self.telegram.register_command("obs_sil", self._tg_cmd_obs_drop)
            self.telegram.register_command("kontrol", self._tg_cmd_check_now)
            self.telegram.register_command("kontenjan", self._tg_cmd_quota)
            self.telegram.register_command("kesinlestir", self._tg_cmd_finalize)
            self.telegram.register_command("ss", self._tg_cmd_screenshot)
            self.telegram.register_command("ekran", self._tg_cmd_screenshot)

            if self.config.get("telegram_listener_enabled", True):
                self.telegram.start_listener()

    def test_telegram_action(self):
        token = self.tg_token_var.get().strip()
        chat_id = self.tg_chat_id_var.get().strip()
        if not token or not chat_id:
            messagebox.showwarning("Uyarı", "Lütfen Token ve Chat ID alanlarını doldurun!")
            return

        self.save_config_action(silent=True)
        from telegram_service import TelegramService
        tg = TelegramService(token=token, chat_id=chat_id, log_cb=self.append_log)
        self.append_log("Telegram bağlantısı test ediliyor (SSL güvenli)...", "INFO")

        def _test():
            ok = tg.test_connection()
            if ok:
                self.append_log("✅ Telegram test mesajı başarıyla telefonunuza iletildi!", "SUCCESS")
                messagebox.showinfo("Başarılı", "Telegram test mesajı başarıyla iletildi! Telefonunuzu kontrol edin.")
            else:
                err_det = getattr(tg, "last_error", "Bilinmeyen hata")
                self.append_log(f"❌ Telegram testi başarısız: {err_det}", "ERROR")
                messagebox.showerror(
                    "Bağlantı Hatası",
                    f"Telegram mesajı gönderilemedi!\n\nHata Ayrıntısı:\n{err_det}\n\n"
                    "Lütfen Token ve Chat ID bilgilerinizi kontrol edin veya internet bağlantınızı doğrulayın."
                )

        threading.Thread(target=_test, daemon=True).start()

    def _tg_cmd_status(self, args):
        status = "Boşta"
        if self.engine and self.engine.is_running:
            status = "Ders Kaydı Çalışıyor"
        elif self.quota_watcher and self.quota_watcher.is_running:
            status = "Kontenjan Sniper Devrede (10 dk bir tarıyor)"

        selected = self.config.get("selected_courses", [])
        snipers = self.config.get("sniper_courses", [])
        total_akts = sum(c.get("akts", 0) for c in selected)
        total_kredi = sum(c.get("kredi", 0) for c in selected)

        msg = (
            f"📊 <b>GTÜ OBS Bot v2.3 Durumu:</b>\n\n"
            f"• <b>Durum:</b> {status}\n"
            f"• <b>Hedef Saat:</b> <code>{self.config.get('target_time')}</code>\n"
            f"• <b>Kayıt Planı:</b> {len(selected)} ders ({total_akts}/35 AKTS, {total_kredi} Kredi)\n"
            f"• <b>Sniper Takibi:</b> {len(snipers)} ders\n"
            f"• <b>Otomatik Kesinleştirme:</b> {'Açık ✅' if self.config.get('auto_finalize') else 'Kapalı ⏸️'}\n"
            f"• <b>Oturum:</b> {'Tarayıcı Açık 🌐' if (self.engine and getattr(self.engine, 'driver', None)) else 'Kapalı'}"
        )
        return msg

    def _tg_cmd_start(self, args):
        if self.engine and self.engine.is_running:
            return "⚠️ Bot zaten şu anda çalışıyor!"
        self.root.after(0, self.start_bot_thread)
        return "🚀 <b>Ders kayıt savaşı uzaktan başlatıldı!</b>"

    def _tg_cmd_stop(self, args):
        self.root.after(0, self.stop_bot)
        return "🛑 <b>Bot işlemi uzaktan durduruldu.</b>"

    def _tg_cmd_time(self, args):
        if args:
            raw = args[0].strip()
            parts = raw.split(":")
            if len(parts) in (2, 3) and all(p.isdigit() for p in parts):
                if len(parts) == 2:
                    raw = f"{raw}:00"
                self.config["target_time"] = raw
                if hasattr(self, "time_var"):
                    self.root.after(0, lambda: self.time_var.set(raw))
                self.save_config_action(silent=True)
                return f"⏰ <b>Hedef başlama saati güncellendi:</b> <code>{raw}</code>"
            return "⚠️ Geçersiz format! Örnek kullanım: <code>/saat 08:29:55</code>"
        curr = self.config.get("target_time", "08:29:55")
        return f"⏰ <b>Mevcut Hedef Saat:</b> <code>{curr}</code>\nDeğiştirmek için: <code>/saat 08:29:55</code>"

    def _tg_cmd_curriculum(self, args):
        inline_kb = {
            "inline_keyboard": [
                [{"text": "🥇 1. Sınıf", "callback_data": "/mufredat 1"}, {"text": "🥈 2. Sınıf", "callback_data": "/mufredat 2"}],
                [{"text": "🥉 3. Sınıf", "callback_data": "/mufredat 3"}, {"text": "🎓 4. Sınıf", "callback_data": "/mufredat 4"}],
                [{"text": "🔍 Seçmeli Alt Dersler (GTU110 vb.)", "callback_data": "/altdersler"}]
            ]
        }

        if not args:
            text = (
                "📚 <b>GTÜ Bilgisayar Mühendisliği Müfredat Kataloğu</b>\n\n"
                "Aşağıdaki butonlara tıklayarak istediğiniz sınıfın derslerini veya "
                "seçmeli ders alt havuzlarını tek tıkla görüntüleyebilirsiniz:"
            )
            return text, inline_kb

        arg = args[0].strip()
        key_map = {
            "1": "1. Sınıf Dersleri",
            "2": "2. Sınıf Dersleri",
            "3": "3. Sınıf Dersleri",
            "4": "4. Sınıf Dersleri",
        }
        class_key = key_map.get(arg)
        if not class_key or class_key not in curriculum_data.CURRICULUM_SEMESTERS:
            return "⚠️ Lütfen geçerli bir sınıf numarası seçin (1, 2, 3 veya 4).", inline_kb

        lines = [f"🎓 <b>GTÜ {class_key} Kataloğu:</b>\n"]
        for donem, d_list in curriculum_data.CURRICULUM_SEMESTERS[class_key].items():
            lines.append(f"📌 <b>{donem}:</b>")
            for d in d_list:
                tip = "🟢" if "Zorunlu" in d.get("tip", "") else "🟡"
                lines.append(f"{tip} <code>{d['kod']}</code> - {d['ad']} ({d['akts']} AKTS)")
            lines.append("")

        lines.append("💡 <i>Sınıf değiştirmek veya alt dersleri görmek için butonları kullanabilirsiniz:</i>")
        return "\n".join(lines), inline_kb

    def _tg_cmd_subcourses(self, args):
        """Seçmeli havuzlarının alt derslerini kategorize ederek gösterir."""
        arg = args[0].lower().strip() if args else ""

        inline_kb = {
            "inline_keyboard": [
                [{"text": "🌐 Genel / Sosyal Seçmeliler", "callback_data": "/altdersler genel"}],
                [{"text": "⚡ Teknik Seçmeliler", "callback_data": "/altdersler teknik"}],
                [{"text": "💻 Bölüm Seçmelileri (CSE 4XX)", "callback_data": "/altdersler bolum"}],
                [{"text": "📋 Tüm Alt Dersler (Özet)", "callback_data": "/altdersler hepsi"}],
            ]
        }

        if arg in ("genel", "sosyal", "nontech"):
            lines = [
                "🌐 <b>Genel / Sosyal Seçmeli Havuzu (NonTElec, FElec, GenTelec):</b>\n",
                "<i>OBS'de NonTElec3, NonTElec5, FElec4, GenTelec8 gibi derslerin altından seçilir:</i>\n"
            ]
            for c in curriculum_data.OBS_GENERAL_SUBCOURSES:
                lines.append(f"• <code>{c['kod']}</code> — {c['ad']} ({c['akts']} AKTS, {c['kredi']} Kredi)")
            lines.append("\n💡 <b>Hızlı Ekleme Örnekleri:</b>")
            lines.append("<code>/ekle NonTElec3 GTU110</code>")
            lines.append("<code>/ekle NonTElec3 ENG250</code>")
            lines.append("<code>/ekle GenTelec8 PES140</code>")
            return "\n".join(lines), inline_kb

        elif arg in ("teknik", "muhendislik", "telec"):
            lines = [
                "⚡ <b>Teknik Seçmeli Havuzu (TElec6, MultiElec6):</b>\n",
                "<i>OBS'de 3. ve 4. sınıf teknik seçmeli slotlarından seçilir:</i>\n"
            ]
            for c in curriculum_data.OBS_TECHNICAL_SUBCOURSES:
                lines.append(f"• <code>{c['kod']}</code> — {c['ad']} ({c['akts']} AKTS, {c['kredi']} Kredi)")
            lines.append("\n💡 <b>Hızlı Ekleme Örnekleri:</b>")
            lines.append("<code>/ekle TElec6 ELEC334</code>")
            lines.append("<code>/ekle MultiElec6 GTU110</code>")
            return "\n".join(lines), inline_kb

        elif arg in ("bolum", "cse", "delec"):
            lines = [
                "💻 <b>Bölüm Seçmeli Havuzu (DElec7, DElec8 — CSE 4XX):</b>\n",
                "<i>OBS'de 4. sınıf bölüm seçmeli (DElec) slotlarından seçilir:</i>\n"
            ]
            for c in curriculum_data.OBS_DEPARTMENTAL_SUBCOURSES:
                lines.append(f"• <code>{c['kod']}</code> — {c['ad']} ({c['akts']} AKTS, {c['kredi']} Kredi)")
            lines.append("\n💡 <b>Hızlı Ekleme Örnekleri:</b>")
            lines.append("<code>/ekle DElec7 CSE481</code> (Yapay Zeka)")
            lines.append("<code>/ekle DElec7 CSE455</code> (Machine Learning)")
            lines.append("<code>/ekle DElec8 CSE414</code> (Veritabanı)")
            return "\n".join(lines), inline_kb

        elif arg == "hepsi":
            lines = ["📋 <b>Tüm Seçmeli Alt Dersler Kataloğu:</b>\n"]
            lines.append("🌐 <b>Genel/Sosyal:</b>")
            lines.append(", ".join(f"<code>{c['kod']}</code>" for c in curriculum_data.OBS_GENERAL_SUBCOURSES))
            lines.append("\n⚡ <b>Teknik Seçmeliler:</b>")
            lines.append(", ".join(f"<code>{c['kod']}</code>" for c in curriculum_data.OBS_TECHNICAL_SUBCOURSES))
            lines.append("\n💻 <b>Bölüm Seçmelileri (CSE 4XX):</b>")
            lines.append(", ".join(f"<code>{c['kod']}</code>" for c in curriculum_data.OBS_DEPARTMENTAL_SUBCOURSES))
            lines.append("\n<i>Detaylı listeyi görmek için yukarıdaki butonlardan kategori seçebilirsiniz.</i>")
            return "\n".join(lines), inline_kb

        # Default menü
        text = (
            "🔍 <b>Seçmeli Derslerin Alt Dersleri (OBS Havuzları)</b>\n\n"
            "OBS sisteminde seçmeli derslerin (NonTElec, FElec, GenTelec, DElec) "
            "altında açılan tüm dersleri aşağıdan kategori seçerek görebilirsiniz:\n\n"
            "1. 🌐 <b>Genel / Sosyal Seçmeliler</b> (GTU110, GTU101, ENG250, PES140, BUS403...)\n"
            "2. ⚡ <b>Teknik Seçmeliler</b> (ELEC334, BENG451, ENVE315...)\n"
            "3. 💻 <b>Bölüm Seçmelileri (CSE 4XX)</b> (CSE481 Yapay Zeka, CSE455, CSE414...)\n\n"
            "👇 <i>İncelemek istediğiniz grubu seçin:</i>"
        )
        return text, inline_kb

    def _tg_cmd_plan(self, args):
        courses = self.config.get("selected_courses", [])
        if not courses:
            return "📋 Kayıt planınızda henüz ders yok. <code>/ekle [kod]</code> ile ders ekleyebilirsiniz."
        total_akts = sum(c.get("akts", 0) for c in courses)
        total_kredi = sum(c.get("kredi", 0) for c in courses)
        res = [
            "📋 <b>Ders Kayıt Planınız (Seçilen Dersler):</b>\n",
            f"🎯 <b>Toplam:</b> {total_akts}/35 AKTS  |  {total_kredi} Kredi  |  {len(courses)} Ders\n"
        ]
        for i, c in enumerate(courses, 1):
            sub_str = ", ".join(c.get("sub_choices", [c.get("kod", "")]))
            res.append(f"{i}. <b>{c.get('kod')}</b> — {c.get('ad', '')}\n   ↳ Şube/Alt Tercih: <code>{sub_str}</code> | {c.get('akts', 0)} AKTS")
        return "\n".join(res)

    def _tg_cmd_add(self, args):
        if not args:
            return "⚠️ Kullanım: <code>/ekle [Ders_Kodu] [Alt_Ders(opsiyonel)]</code>\nÖrnek: <code>/ekle CSE231</code> veya <code>/ekle NonTElec3 GTU110</code>"

        target_code = args[0].strip().upper()
        sub_choice = args[1].strip().upper() if len(args) > 1 else target_code

        found_course = None
        found_class = "2. Sınıf Dersleri"

        for c_key, semesters in curriculum_data.CURRICULUM_SEMESTERS.items():
            for d_list in semesters.values():
                for c in d_list:
                    c_norm = c["kod"].upper().replace(" ", "")
                    if target_code.replace(" ", "") in c_norm or c_norm in target_code.replace(" ", ""):
                        found_course = dict(c)
                        found_class = c_key
                        break
                if found_course:
                    break
            if found_course:
                break

        if not found_course:
            found_course = {
                "kod": target_code,
                "ad": target_code,
                "sinif": "2. Sınıf Dersleri",
                "akts": 5,
                "kredi": 3,
                "tip": "Seçmeli",
                "sub_choices": [sub_choice],
            }
        else:
            found_course["sinif"] = found_class
            found_course["sub_choices"] = [sub_choice]

        for existing in self.config.get("selected_courses", []):
            if existing.get("kod") == found_course["kod"]:
                return f"⚠️ <code>{found_course['kod']}</code> zaten kayıt planınızda mevcut!"

        self.config.setdefault("selected_courses", []).append(found_course)
        self.root.after(0, self.refresh_selected_table)
        self.root.after(0, self.update_totals)
        self.save_config_action(silent=True)

        tot_akts = sum(c.get('akts', 0) for c in self.config['selected_courses'])
        return (
            f"✅ <b>Ders Planına Eklendi!</b>\n\n"
            f"📚 <b>Ders:</b> <code>{found_course['kod']}</code> ({found_course.get('ad')})\n"
            f"🎯 <b>Alt Tercih:</b> <code>{sub_choice}</code>\n"
            f"🏫 <b>Sınıf Sekmesi:</b> {found_course['sinif']}\n"
            f"📊 <b>Yeni Toplam:</b> {tot_akts}/35 AKTS"
        )

    def _tg_cmd_remove(self, args):
        if not args:
            return "⚠️ Kullanım: <code>/sil [Ders_Kodu]</code>\nÖrnek: <code>/sil CSE231</code>"

        target = args[0].strip().upper().replace(" ", "")
        courses = self.config.get("selected_courses", [])
        before_len = len(courses)
        self.config["selected_courses"] = [
            c for c in courses if target not in c.get("kod", "").upper().replace(" ", "")
        ]

        if len(self.config["selected_courses"]) < before_len:
            self.root.after(0, self.refresh_selected_table)
            self.root.after(0, self.update_totals)
            self.save_config_action(silent=True)
            return f"✅ <code>{args[0]}</code> dersi kayıt planınızdan çıkarıldı."
        return f"⚠️ <code>{args[0]}</code> kayıt planınızda bulunamadı."

    def _tg_cmd_obs_drop(self, args):
        if not args:
            return "⚠️ Kullanım: <code>/obs_sil [Ders_Kodu]</code>\nÖrnek: <code>/obs_sil CSE231</code>"

        target_code = args[0].strip().upper()
        if not self.engine or not getattr(self.engine, "driver", None):
            return "⚠️ OBS tarayıcısı şu an aktif değil! Önce <code>/baslat</code> veya arayüzden test girişini başlatın."

        def _drop_worker():
            self.append_log(f"Telegram talebiyle [{target_code}] OBS'den siliniyor...", "WARN")
            ok = self.engine.drop_course(target_code)
            if ok:
                self.telegram.send_message(f"🎉 <b>[OBS Silme Başarılı]</b> <code>{target_code}</code> OBS sisteminden silindi!")
            else:
                self.telegram.send_message(f"❌ <b>[OBS Silme Başarısız]</b> <code>{target_code}</code> silinemedi veya tabloda bulunamadı.")

        threading.Thread(target=_drop_worker, daemon=True).start()
        return f"🗑️ <code>{target_code}</code> için OBS üzerinden ders silme işlemi arka planda başlatıldı..."

    def _tg_cmd_check_now(self, args):
        if self.quota_watcher and self.quota_watcher.is_running:
            self.quota_watcher.check_now()
            return "⚡ <b>Anlık kontenjan kontrolü tetiklendi!</b> Sonuçlar terminale ve buraya iletilecektir."
        elif self.engine and getattr(self.engine, "driver", None):
            self.root.after(0, self.start_standalone_sniper)
            return "🎯 Kontenjan Sniper başlatıldı ve anlık kontrol tetiklendi."
        return "⚠️ Tarayıcı aktif değil. Lütfen arayüzden giriş yapın veya botu başlatın."

    def _tg_cmd_finalize(self, args):
        if args:
            val = args[0].lower() in ("ac", "aktif", "1", "true", "on", "evet")
            self.config["auto_finalize"] = val
            if hasattr(self, "auto_finalize_var"):
                self.root.after(0, lambda: self.auto_finalize_var.set(val))
            self.save_config_action(silent=True)
            st = "Açık ✅" if val else "Kapalı ⏸️"
            return f"🔒 Otomatik kesinleştirme: <b>{st}</b> olarak ayarlandı."
        curr = "Açık ✅" if self.config.get("auto_finalize") else "Kapalı ⏸️"
        return f"🔒 Otomatik kesinleştirme: <b>{curr}</b>\nDeğiştirmek için: <code>/kesinlestir ac</code> veya <code>/kesinlestir kapat</code>"

    def _tg_cmd_screenshot(self, args):
        if not self.engine or not getattr(self.engine, "driver", None):
            return "⚠️ Tarayıcı şu an açık değil."

        def _ss_worker():
            ss_path = self.engine.get_screenshot()
            if ss_path and os.path.exists(ss_path):
                self.telegram.send_photo(
                    ss_path,
                    caption=f"📸 <b>Canlı GTÜ OBS Ekran Görüntüsü</b>\n🕒 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            else:
                self.telegram.send_message("❌ Ekran görüntüsü alınamadı.")

        threading.Thread(target=_ss_worker, daemon=True).start()
        return "📸 Ekran görüntüsü alınıyor, birazdan iletilecektir..."

    def _tg_cmd_quota(self, args):
        snipers = self.config.get("sniper_courses", [])
        if args and args[0].lower() in ("baslat", "start"):
            self.root.after(0, self.start_standalone_sniper)
            return "🎯 <b>Kontenjan Sniper uzaktan başlatıldı!</b>"
        elif args and args[0].lower() in ("durdur", "stop"):
            self.root.after(0, self.stop_bot)
            return "🛑 Kontenjan Sniper durduruldu."
        elif args and args[0].lower() == "ekle" and len(args) > 1:
            kod = args[1].strip().upper()
            swap = args[2].strip().upper() if len(args) > 2 else ""
            item = {
                "kod": kod,
                "ad": kod,
                "sinif": "2. Sınıf Dersleri",
                "sub_choices": [kod],
                "swap_course": swap,
            }
            self.config.setdefault("sniper_courses", []).append(item)
            self.root.after(0, self.refresh_sniper_table)
            self.save_config_action(silent=True)
            sw_txt = f" (Açılırsa silinecek ders: <code>{swap}</code>)" if swap else ""
            return f"🎯 <code>{kod}</code> Sniper listesine eklendi!{sw_txt}"
        elif args and args[0].lower() == "sil" and len(args) > 1:
            kod = args[1].strip().upper()
            self.config["sniper_courses"] = [sc for sc in snipers if sc.get("kod") != kod]
            self.root.after(0, self.refresh_sniper_table)
            self.save_config_action(silent=True)
            return f"❌ <code>{kod}</code> Sniper listesinden çıkarıldı."

        active = self.quota_watcher and self.quota_watcher.is_running
        status_txt = "Aktif (10 dk bir taranıyor)" if active else "Durdurulmuş"
        lines = [f"🎯 <b>Kontenjan Sniper Durumu:</b> {status_txt}\n"]
        if snipers:
            lines.append("📋 <b>İzlenen Dersler:</b>")
            for s in snipers:
                sw = f" ➔ [Sil: <code>{s.get('swap_course')}</code>]" if s.get("swap_course") else ""
                lines.append(f"• <code>{s.get('kod')}</code>{sw}")
        else:
            lines.append("<i>Listenizde henüz ders yok.</i>")

        lines.append("\n<b>Kullanabileceğiniz Komutlar:</b>")
        lines.append("• <code>/kontenjan baslat</code> : Sniper'ı başlat")
        lines.append("• <code>/kontenjan durdur</code> : Sniper'ı durdur")
        lines.append("• <code>/kontenjan ekle [kod] [swap]</code> : Ders ekle")
        lines.append("• <code>/kontenjan sil [kod]</code> : Ders çıkar")
        lines.append("• <code>/kontrol</code> : Anlık hemen kontrol et")
        return "\n".join(lines)
