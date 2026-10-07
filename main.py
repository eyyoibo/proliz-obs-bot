"""
GTÜ Proliz Ders Kayıt Botu - Ana Giriş Noktası
Modern Grafik Arayüzü (GUI) başlatır.
"""

import sys
import tkinter as tk
from gui import ProlizBotGUI

def main():
    print("=" * 60)
    print("GTÜ Proliz Ders Kayıt Botu Başlatılıyor...")
    print("Müfredat: 2026 Bilgisayar Mühendisliği Güncel Öğretim Planı")
    print("=" * 60)
    
    root = tk.Tk()
    app = ProlizBotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
