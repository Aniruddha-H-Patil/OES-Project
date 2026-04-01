# 🛡️ BOSS: Benchmark Online Smart Suite

**BOSS** is a high-integrity, secure Computer-Based Testing (CBT) platform developed in Python. Designed to emulate the National Testing Agency (NTA) interface, it provides a realistic environment for aspirants practicing for competitive exams like JEE, NEET, and MHT-CET.

---

## 🚀 Key Features
* **Real-time Authentication:** Powered by Google Firebase for secure user login and signup.
* **Image Synchronization:** Integrated with ImgBB API for automated profile and identity verification.
* **System Integrity:** Tracks IP and MAC addresses to prevent session spoofing and ensure exam decorum.
* **NTA-Style UI:** Built using Python's Tkinter to provide a familiar and stress-free examination experience.
* **Secrets-as-Code:** Implements a decoupled architecture using `.gitignore` to protect sensitive Firebase API keys and credentials.

## 🛠️ Tech Stack
* **Language:** Python 3.x
* **Database:** Firebase Realtime Database
* **GUI Framework:** Tkinter
* **Cloud Integration:** ImgBB API, Firebase Admin SDK

## 📂 Project Structure
The system is modularized into dedicated components for better maintainability:
* `auth_manager.py` & `auth_ui.py`: Handles secure user access.
* `Exam_window.py` & `Question_updater.py`: Core logic for the testing engine.
* `Result.py` & `Result_window.py`: Real-time score calculation and analytics.

## 🔒 Security First
This repository follows industry-standard security practices. Private configuration files (JSON keys, API tokens) are strictly excluded from the public version to prevent unauthorized access.

---
*Project Development Started: 25 Jan 2026*
