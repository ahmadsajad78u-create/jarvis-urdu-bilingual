#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JARVIS EXPERT AI SYSTEM - MAIN CORE
All Features: Voice Control, App Launcher, Knowledge Base, Automation
Urdu + English Bilingual Support
"""

import os
import re
import json
import time
import datetime
import webbrowser
import subprocess
import ctypes
import winreg
from pathlib import Path

try:
    import speech_recognition as sr
    import pyttsx3
except Exception as e:
    print(f"ERROR: Missing dependencies!\n{e}")
    print("\nFix: Run this in Command Prompt:")
    print("pip install SpeechRecognition pyttsx3 pyaudio")
    exit(1)


class JarvisExpertCore:
    def __init__(self):
        print("=" * 60)
        print("JARVIS EXPERT AI - INITIALIZING")
        print("=" * 60)
        
        self.root = Path(__file__).parent
        self.kb_path = self.root / "knowledge_base"
        self.logs_path = self.root / "logs"
        self.logs_path.mkdir(exist_ok=True)
        
        # Speech Recognition & TTS Setup
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 170)
        self.engine.setProperty("volume", 1.0)
        
        self.running = True
        self.command_history = []
        self.app_cache = self.scan_installed_apps()
        self.knowledge_base = self.load_knowledge_base()
        
        print(f"[+] Detected {len(self.app_cache)} installed applications")
        print(f"[+] Loaded knowledge base: {len(self.knowledge_base)} topics")
        print("[+] JARVIS initialization complete!\n")

    def load_knowledge_base(self):
        kb = {}
        if self.kb_path.exists():
            for file in self.kb_path.glob("*.json"):
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        kb.update(data)
                        print(f"[+] Loaded: {file.name}")
                except Exception as e:
                    print(f"[-] Error loading {file.name}: {e}")
        return kb

    def scan_installed_apps(self):
        """Auto-detect all installed applications"""
        apps = set()
        print("\n[*] Scanning for installed applications...")
        
        # Common Program Files locations
        locations = [
            os.environ.get("ProgramFiles", r"C:\Program Files"),
            os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
            os.path.expanduser("~\\AppData\\Local\\Programs"),
        ]
        
        for location in locations:
            if os.path.exists(location):
                try:
                    for root, dirs, files in os.walk(location):
                        for file in files:
                            if file.endswith((".exe", ".lnk")):
                                app_name = file.replace(".exe", "").replace(".lnk", "")
                                apps.add(app_name.lower())
                except Exception:
                    pass
        
        # Registry scan
        try:
            for hive, subkey in [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"),
            ]:
                try:
                    with winreg.OpenKey(hive, subkey) as key:
                        i = 0
                        while i < 2000:
                            try:
                                sub = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, sub) as k:
                                    try:
                                        name, _ = winreg.QueryValueEx(k, "DisplayName")
                                        if name:
                                            apps.add(name.lower())
                                    except Exception:
                                        pass
                                i += 1
                            except Exception:
                                break
                except Exception:
                    pass
        except Exception:
            pass
        
        return sorted(list(apps))

    def speak(self, text):
        print(f"\\nJARVIS: {text}\n")
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"[!] TTS Error: {e}")

    def listen(self, timeout=10):
        """Advanced listening with error handling"""
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("[Listening...]")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=7)
            
            text = self.recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("[!] Could not understand audio")
            return ""
        except sr.RequestError as e:
            print(f"[!] API Error: {e}")
            return ""
        except Exception as e:
            print(f"[!] Listening Error: {e}")
            return ""

    def detect_language(self, text):
        """Auto-detect Urdu or English"""
        if re.search(r"[\u0600-\u06FF]", text):
            return "urdu"
        return "english"

    def normalize(self, text):
        return text.lower().strip()

    def find_app(self, app_name):
        """Find installed application"""
        query = self.normalize(app_name)
        for app in self.app_cache:
            if query in app or app in query:
                return app
        return None

    def open_app(self, app_name):
        """Open application by name"""
        found = self.find_app(app_name)
        if found:
            try:
                os.system(f"start {found}")
                return f"{app_name} is opening."
            except Exception as e:
                return f"Could not open {app_name}: {e}"
        return f"{app_name} is not installed."

    def rag_query(self, query):
        """RAG: Retrieval-Augmented Generation from Knowledge Base"""
        query_lower = self.normalize(query)
        for key, value in self.knowledge_base.items():
            if query_lower in self.normalize(key):
                if isinstance(value, dict):
                    return f"Knowledge: {str(value)[:200]}..."
                return f"Found: {str(value)[:200]}..."
        return None

    def handle_command(self, text):
        """Main command processing"""
        c = self.normalize(text)
        lang = self.detect_language(text)
        
        # Log command
        self.command_history.append({
            "time": datetime.datetime.now().isoformat(),
            "command": text,
            "language": lang
        })
        
        # ===== SYSTEM CONTROL =====
        if any(word in c for word in ["shutdown", "band karo", "band", "shut"]):
            subprocess.run(["shutdown", "/s", "/t", "5"], check=False)
            return "Computer will shutdown in 5 seconds."
        
        if any(word in c for word in ["restart", "reboot", "dobara", "دوبارہ"]):
            subprocess.run(["shutdown", "/r", "/t", "5"], check=False)
            return "Computer will restart in 5 seconds."
        
        if "lock" in c or "قفل" in text:
            ctypes.windll.user32.LockWorkStation()
            return "Screen is locked."
        
        if "sleep" in c or "سو" in text:
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            return "Computer is going to sleep."
        
        # ===== TIME & DATE =====
        if "time" in c or "وقت" in text or "waqt" in c:
            now = datetime.datetime.now().strftime("%I:%M %p")
            return f"The time is {now}"
        
        if "date" in c or "تاریخ" in text or "tarikh" in c:
            today = datetime.datetime.now().strftime("%A, %B %d, %Y")
            return f"Today is {today}"
        
        # ===== BROWSER & URLs =====
        if "youtube" in c or "یوٹیوب" in text:
            webbrowser.open("https://www.youtube.com")
            return "YouTube is opening."
        
        if "chrome" in c or "کروم" in text:
            os.system("start chrome")
            return "Chrome is opening."
        
        if "edge" in c or "ایج" in text:
            os.system("start msedge")
            return "Microsoft Edge is opening."
        
        if "google" in c:
            webbrowser.open("https://www.google.com")
            return "Google is opening."
        
        # ===== FILE MANAGEMENT =====
        if "documents" in c or "دستاویزات" in text:
            os.startfile(os.path.expanduser("~\\Documents"))
            return "Documents folder is opening."
        
        if "downloads" in c or "ڈاؤن لوڈ" in text:
            os.startfile(os.path.expanduser("~\\Downloads"))
            return "Downloads folder is opening."
        
        if "desktop" in c or "ڈیسک ٹاپ" in text:
            os.startfile(os.path.expanduser("~\\Desktop"))
            return "Desktop is opening."
        
        # ===== APP LAUNCHER =====
        if "filmora" in c or "فلمورا" in text:
            return self.open_app("filmora")
        
        if "notepad" in c:
            os.system("notepad")
            return "Notepad is opening."
        
        if "calculator" in c or "کیلکولیٹر" in text:
            os.system("calc")
            return "Calculator is opening."
        
        # Generic app open
        if any(word in c for word in ["open", "launch", "start", "کھولو", "شروع"]):
            for app in self.app_cache[:20]:  # Check top 20 apps
                if self.normalize(app) in c:
                    return self.open_app(app)
        
        # ===== KNOWLEDGE BASE / RAG =====
        rag_result = self.rag_query(text)
        if rag_result:
            return rag_result
        
        # ===== GREETINGS =====
        if lang == "urdu":
            if any(word in text for word in ["ہیلو", "السلام", "سلام", "hi", "hello"]):
                return "ہیلو! میں JARVIS ہوں، آپ کی مدد کے لیے تیار ہوں۔"
            if "بند" in text or "exit" in c:
                self.running = False
                return "JARVIS بند ہو رہا ہے۔"
            if "کون ہو" in text:
                return "میں JARVIS ہوں، آپ کا اردو اور انگریزی معاون۔ میرے پاس CCNA, CCNP, اور نیٹ ورک کی معلومات ہے۔"
            return "میں نے آپ کی بات سنی۔ براہ کرم ہدایت دیں کہ آپ کیا کرنا چاہتے ہیں۔"
        
        else:  # English
            if any(word in c for word in ["hello", "hi"]):
                return "Hello! I am JARVIS Expert AI. How can I help you?"
            if "exit" in c or "bye" in c:
                self.running = False
                return "Goodbye!"
            if "who are you" in c:
                return "I am JARVIS, your Expert AI assistant. I have CCNA, CCNP, Islamic, and Networking knowledge."
            return "I heard you. Please tell me what you want me to do."

    def run(self):
        """Main JARVIS loop"""
        self.speak("JARVIS Expert AI is online.")
        self.speak("I can speak Urdu and English.")
        self.speak("I know about CCNA, CCNP, Networking, and Islamic topics.")
        self.speak("Ready to help you!")
        
        while self.running:
            try:
                command = self.listen()
                if not command:
                    continue
                
                response = self.handle_command(command)
                if response:
                    self.speak(response)
            
            except KeyboardInterrupt:
                self.speak("Shutting down JARVIS.")
                break
            except Exception as e:
                print(f"[!] Error: {e}")
                self.speak("An error occurred. Please try again.")


def main():
    try:
        jarvis = JarvisExpertCore()
        jarvis.run()
    except KeyboardInterrupt:
        print("\n[JARVIS] Stopped by user")
    except Exception as e:
        print(f"[JARVIS] Critical Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
