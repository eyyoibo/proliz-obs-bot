# Proliz OBS Automation & Quota Sniper Bot

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Selenium](https://img.shields.io/badge/Selenium-4.x-43B02A.svg?logo=selenium&logoColor=white)](https://www.selenium.dev/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6.svg?logo=windows&logoColor=white)](https://microsoft.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A high-performance desktop automation and real-time quota sniper tool designed to eliminate server overload delays, quota contention, and registration stress during university course enrollment periods on **Proliz Student Information System (OBS)** platforms.

---

## 🌟 Key Features

- 🖥️ **Modern Desktop GUI**: Sleek dark-theme interface with real-time status indicators, interactive course selection table, and integrated live session logging.
- ⏱️ **Millisecond Precision Countdown & Auto-Trigger**: Synchronizes with enrollment open times (e.g., exactly `08:30:00.000`) to log in and select courses with sub-second precision, far outperforming manual browser actions.
- 🎯 **Background Quota Watcher & Sniper**: Actively monitors full or waitlisted courses in background worker threads; snipes newly freed quotas within microseconds and commits registration.
- 🤖 **Fully Integrated Telegram Bot**:
  - Delivers instant push notifications to your mobile device upon successful enrollments or quota changes.
  - Supports bi-directional command processing and interactive keyboard buttons for remote monitoring and control on the go.
- 🧩 **Smart Captcha Solver**: Resolves Proliz arithmetic verification questions via fast DOM evaluation in under 5 milliseconds.
- 🔒 **Zero-Leak / Privacy-First Architecture**: Your student ID and passwords stay strictly on your local machine and are never transmitted to any external server.

---

## 🏗️ System Architecture

```text
                                  +-----------------------+
                                  |   Desktop GUI (Tk)    |
                                  +-----------+-----------+
                                              |
                   +--------------------------+--------------------------+
                   |                                                     |
       +-----------v-----------+                             +-----------v-----------+
       |   Proliz Web Engine   |                             |    Telegram Service   |
       |  (Selenium WebDriver) |                             |     (Bot API Client)  |
       +-----------+-----------+                             +-----------+-----------+
                   |                                                     |
       +-----------v-----------+                             +-----------v-----------+
       | OBS Auth & Enrollment |                             | Mobile Alerts &       |
       | Quota Sniper Engine   |                             | Remote Command Server |
       +-----------------------+                             +-----------------------+
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10 or higher
- Google Chrome browser
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

### 2. Launching the App
* **Windows (One-Click):** Double-click `baslat.bat` (automatically detects the virtual environment and installs missing packages).
* **Terminal / CLI:**
  ```bash
  python main.py
  ```

---

## 📱 Telegram Bot Setup & Configuration Guide

You can connect a free Telegram bot in under 2 minutes to receive live alerts and remotely trigger or monitor actions from your phone:

### Step 1: Create a Bot via @BotFather
1. Open the Telegram app and search for `@BotFather` (official verified account with the blue checkmark).
2. Send `/start`, then send `/newbot`.
3. Enter a display name for your bot (e.g., `OBS Enrollment Bot`).
4. Enter a unique username ending in `_bot` (e.g., `my_obs_enrollment_bot`).
5. BotFather will provide an **HTTP API Token** formatted like:
   ```text
   1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ_1234567
   ```
   Copy this token.

### Step 2: Retrieve Your Chat ID
1. Open your newly created bot in Telegram and send `/start` (this gives the bot permission to send you messages).
2. In Telegram search, open `@userinfobot` or `@RawDataBot` and start the conversation.
3. The bot will reply with your profile metadata. Copy the numerical ID next to `Id:` (e.g., `123456789`).

### Step 3: Configure Credentials
You can configure your bot using either method:
- **Method A (Desktop GUI):** Open the application, navigate to the **Telegram Settings** tab. Paste your Token and Chat ID, then click **"Send Test Notification"**. When you receive the test alert on your phone, you are connected!
- **Method B (Config File):** Copy `config.example.json` to `config.json` and fill in your values:
  ```json
  {
      "telegram_token": "YOUR_TELEGRAM_BOT_TOKEN_HERE",
      "telegram_chat_id": "YOUR_CHAT_ID_HERE",
      "telegram_enabled": true,
      "telegram_listener_enabled": true
  }
  ```

### 📲 Remote Telegram Commands
While the application is running, you can send messages to your bot from anywhere:
- `/durum` / `📊 Durum` : Displays real-time status, countdown timer, ECTS credits, and active monitors.
- `/baslat` / `🚀 Başlat` : Triggers course registration immediately without waiting for the scheduled timer.
- `/durdur` / `🛑 Durdur` : Safely stops active automation and background monitoring loops.
- `📋 Plan` : Lists currently selected courses in your registration queue.
- `📸 Ekran (SS)` : Captures and sends an instant screenshot of the OBS portal.
- `⚡ Anlık Kontrol` : Runs an immediate quota check across all watched courses.
- `/yardim` : Displays the full interactive command and parameter help menu.

---

## 📁 Repository Structure

```text
proliz-obs-bot/
├── bot.py                  # Core automation routines & lifecycle loop
├── proliz_engine.py        # Proliz OBS DOM interaction & Selenium engine
├── quota_watcher.py        # Background quota poller and sniper service
├── telegram_service.py     # Bi-directional Telegram notification & command handler
├── logger_service.py       # Colorized terminal & file logging service
├── curriculum_data.py      # Department course catalog & curriculum models
├── gui.py                  # Modern dark-theme desktop control dashboard
├── main.py                 # Application entry point
├── baslat.bat              # One-click Windows startup script
├── requirements.txt        # Python dependency manifest
├── config.example.json     # Safe configuration template
└── README.md
```

---

## 🔒 Security & Disclaimer

- This project is developed strictly for educational, research, and personal workflow automation purposes.
- Credentials, passwords, and API keys are stored solely on your local computer and used only within your local Chrome session. They are never sent to external servers or third-party APIs.
- Keep your `config.json` safe and never publish or commit your personal credentials to version control.

---

## 👤 Author
- **İbrahim Halil Doğan** ([@eyyoibo](https://github.com/eyyoibo))