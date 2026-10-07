import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ==========================================
# 🔑 KULLANICI BİLGİLERİ (config.json veya UI üzerinden sağlanır)
# ==========================================
EDEVLET_TC = ""
EDEVLET_SIFRE = ""

# Bot algılama önlemleri ve şifre kaydetme pop-up'ını kapatma tercihleri
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_experimental_option(
    "prefs",
    {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
    },
)

driver = webdriver.Chrome(options=options)

try:
  driver.get("https://obs.gtu.edu.tr/oibs/std/login.aspx")
  wait = WebDriverWait(driver, 15)

  print("Giriş sayfasına ulaşıldı, e-Devlet ile giriş butonuna basılıyor...")

  edevlet_btn = wait.until(
      EC.element_to_be_clickable(
          (By.XPATH, "//a[contains(., 'E-Devlet İle Giriş')]")
      )
  )
  driver.execute_script("arguments[0].click();", edevlet_btn)


  # e-Devlet Giriş ve OAuth2 Onay Fonksiyonu
  def e_devlet_giris_yap():
    try:
      print("e-Devlet sayfasına geçiş bekleniyor...")
      WebDriverWait(driver, 15).until(EC.url_contains("turkiye.gov.tr"))

      tc_input = wait.until(EC.presence_of_element_located((By.ID, "tridField")))
      sifre_input = driver.find_element(By.ID, "egpField")
      giris_btn = driver.find_element(
          By.XPATH, "//form[@id='loginForm']//button[contains(., 'Giriş Yap')]"
      )

      for karakter in EDEVLET_TC:
        tc_input.send_keys(karakter)
        time.sleep(0.05)

      sifre_input.clear()
      for karakter in EDEVLET_SIFRE:
        sifre_input.send_keys(karakter)
        time.sleep(0.05)

      driver.execute_script("arguments[0].click();", giris_btn)
      print("e-Devlet giriş bilgileri gönderildi.")

      try:
        onayla_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Onayla')]")
            )
        )
        driver.execute_script("arguments[0].click();", onayla_btn)
        print("Onay ekranı otomatik onaylandı.")
      except Exception:
        print("Onay ekranı çıkmadı, muhtemelen zaten onaylıydı.")

    except Exception as e:
      print(f"Hata: {e}, URL: {driver.current_url}")
      driver.save_screenshot("edevlet_hata4.png")
      with open("edevlet_hata4.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
      print("Hata teşhisi için ekran görüntüsü ve HTML kaydedildi.")


  e_devlet_giris_yap()


  # Güvenli Menü Navigasyon Fonksiyonu (. kullanılarak nested span sorunları çözüldü)
  def menuye_git():
    """Ders ve Dönem İşlemleri -> Ders Kayıt menüsüne gider.

    Başarılıysa True döner.
    """
    try:
      ders_donem_menu = WebDriverWait(driver, 10).until(
          EC.element_to_be_clickable(
              (By.XPATH, "//a[contains(., 'Ders ve Dönem İşlemleri')]")
          )
      )
      driver.execute_script("arguments[0].click();", ders_donem_menu)
      time.sleep(0.6)

      ders_kayit_link = WebDriverWait(driver, 10).until(
          EC.element_to_be_clickable(
              (By.XPATH, "//a[contains(., 'Ders Kayıt')]")
          )
      )
      driver.execute_script("arguments[0].click();", ders_kayit_link)
      time.sleep(1.0)
      return True
    except Exception as err:
      print(f"Menü navigasyon hatası: {err}")
      driver.save_screenshot("menu_hata.png")
      with open("menu_hata.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
      return False


  # İlk Navigasyon
  print("Ders kayıt sayfasına otomatik geçiş yapılıyor...")
  if not menuye_git():
    input(
        "Ders kayıt sayfasındaysanız terminale geri dönüp ENTER tuşuna basın..."
    )

  # Saat 08:30 Bekleme ve Canlı Takip Döngüsü
  print(
      "Saat 08:30:00 bekleniyor... Sistem açılana kadar kontrollü takip"
      " yapılıyor."
  )
  son_refresh = time.time()
  while True:
    simdiki_zaman = datetime.datetime.now()

    if (
        simdiki_zaman.hour == 8
        and simdiki_zaman.minute >= 30
        or simdiki_zaman.hour > 8
    ):
      try:
        test_btn = driver.find_element(
            By.XPATH,
            "//tr[.//td[contains(., 'CSE')]]//button |"
            " //tr[.//td[contains(., 'CSE')]]//a",
        )
        if test_btn.is_displayed():
          print(
              "Ders kayıt ekranı ve artı butonları aktifleşti! Savaş"
              " başlatılıyor."
          )
          break
      except Exception:
        pass

      if time.time() - son_refresh > 2.5:
        print("Dersler henüz açılmadı, sayfa yenilenip menü açılıyor...")
        driver.refresh()
        time.sleep(1.5)
        menuye_git()
        son_refresh = time.time()

    elif time.time() - son_refresh > 30:
      driver.refresh()
      time.sleep(1.5)
      if menuye_git():
        print("Oturum taze tutuluyor (Periyodik F5).")
      son_refresh = time.time()

    time.sleep(0.5)

  # Ders Planı
  ders_plani = {
      "2. Sınıf Dersleri": ["CSE 231", "Non-Technical Elective I"],
      "3. Sınıf Dersleri": ["CSE 331", "CSE 355", "CSE 396"],
      "4. Sınıf Dersleri": ["DElec7"],
  }

  loop_wait = WebDriverWait(driver, 2)


  # Ders ve şube seçen esnek fonksiyon
  def ders_ve_sube_sec(ders_kodu):
    try:
      temiz_kod = ders_kodu.replace(" ", "")
      row_xpath = f"//tr[.//td[contains(translate(., ' ', ''), '{temiz_kod}')]]"
      plus_btn = driver.find_element(
          By.XPATH, f"{row_xpath}//button | {row_xpath}//a"
      )
      driver.execute_script("arguments[0].click();", plus_btn)
      time.sleep(0.5)

      arama_kriterleri = []
      if temiz_kod == "Non-TechnicalElectiveI":
        arama_kriterleri = ["GTU110", "ScientificandTechnologicalActivities"]
      elif temiz_kod == "DElec7":
        arama_kriterleri = [
            "CSE426",
            "IntroductiontoSymbolicComputation",
            "CSE476",
            "MobileCommunicationNetworks",
        ]
      else:
        arama_kriterleri = [temiz_kod]

      for sayfa in range(1, 5):
        try:
          for kriter in arama_kriterleri:
            try:
              sube_plus_btn = driver.find_element(
                  By.XPATH,
                  "//div[contains(@class, 'modal') or contains(@class,"
                  f" 'popup') or contains(@style, 'display: block')]//tr[.//td[contains(translate(., ' ', ''), '{kriter}')]]//button |"
                  " //div[contains(@class, 'modal') or contains(@class,"
                  f" 'popup')]//tr[.//td[contains(translate(., ' ', ''), '{kriter}')]]//a",
              )
              driver.execute_script("arguments[0].click();", sube_plus_btn)
              print(f"{ders_kodu} başarıyla eklendi.")
              time.sleep(0.3)
              return True
            except Exception:
              continue

          sonraki_sayfa_btn = driver.find_element(
              By.XPATH,
              "//div[contains(@class, 'modal') or contains(@class,"
              " 'popup')]//button[contains(., '>') or contains(@class,"
              " 'next')] | //div[contains(@class, 'modal') or"
              " contains(@class, 'popup')]//a[contains(., '>')]",
          )
          driver.execute_script("arguments[0].click();", sonraki_sayfa_btn)
          time.sleep(0.4)
        except Exception:
          break

      return True
    except Exception as err:
      print(f"{ders_kodu} seçilirken hata oluştu: {err}")
      return False


  while True:
    try:
      # Oturum düşme kontrolü
      if (
          "login.aspx" in driver.current_url.lower()
          or "giris.turkiye.gov.tr" in driver.current_url.lower()
          or len(driver.find_elements(By.ID, "tridField")) > 0
      ):
        print("[!] Oturum düştü, tekrar giriş yapılıyor...")
        if "giris.turkiye.gov.tr" in driver.current_url.lower():
          e_devlet_giris_yap()
        else:
          driver.get("https://obs.gtu.edu.tr/oibs/std/login.aspx")
          edevlet_btn = wait.until(
              EC.element_to_be_clickable(
                  (By.XPATH, "//a[contains(., 'E-Devlet İle Giriş')]")
              )
          )
          driver.execute_script("arguments[0].click();", edevlet_btn)
          e_devlet_giris_yap()
        time.sleep(2)
        continue

      # Hata/uyarı pencerelerini kapatma
      try:
        hata_tamam_btn = driver.find_element(
            By.XPATH,
            "//button[contains(., 'Tamam') or contains(., 'Kapat') or"
            " contains(., 'OK')]",
        )
        if hata_tamam_btn.is_displayed():
          driver.execute_script("arguments[0].click();", hata_tamam_btn)
          time.sleep(0.2)
      except Exception:
        pass

      for sinif_adi, dersler in ders_plani.items():
        try:
          tab_btn = driver.find_element(
              By.XPATH,
              f"//button[contains(., '{sinif_adi}')] |"
              f" //a[contains(., '{sinif_adi}')]",
          )
          driver.execute_script("arguments[0].click();", tab_btn)
          time.sleep(0.2)
        except Exception:
          pass

        for ders_kodu in dersler:
          ders_ve_sube_sec(ders_kodu)

      try:
        tab_btn = driver.find_element(
            By.XPATH,
            "//button[contains(., '4. Sınıf Dersleri')] |"
            " //a[contains(., '4. Sınıf Dersleri')]",
        )
        driver.execute_script("arguments[0].click();", tab_btn)
        time.sleep(0.2)
      except Exception:
        pass

      if not ders_ve_sube_sec("DElec7"):
        time.sleep(0.3)
        continue

      # Kontrol aşaması
      try:
        kontrol_btn = loop_wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[contains(., 'Kontrol Et')]")
            )
        )
        driver.execute_script("arguments[0].click();", kontrol_btn)
        print("Kontrol Et butonuna basıldı.")

        tamam_btn = loop_wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//button[contains(., 'Tamam') or contains(.,'Onay') or"
                    " contains(., 'Kapat')]",
                )
            )
        )
        driver.execute_script("arguments[0].click();", tamam_btn)
        print(
            "Kontrol başarıyla tamamlandı! Kesinleştirme adımı senin kontrolün"
            " için size bırakıldı."
        )
        break

      except Exception as err:
        print(f"Kontrol aşamasında hata: {err}")

      time.sleep(0.3)

    except Exception as err:
      print(f"Ana döngü hatası: {err}")
      time.sleep(0.3)

except Exception as e:
  print(f"Kritik genel hata: {e}")

finally:
  print(
      "Bot kontrol aşamasında durdu. Kesinleştirme butonuna manuel"
      " basabilirsiniz."
  )