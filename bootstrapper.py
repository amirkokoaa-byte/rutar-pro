import sys
import os
import subprocess
import platform
import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                             QProgressBar, QMessageBox, QPushButton)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BootstrapperThread(QThread):
    progress = pyqtSignal(str, int)
    finished = pyqtSignal(bool, str)
    action_required = pyqtSignal(str, str) 

    def run(self):
        try:
            self.progress.emit("جاري التحقق من متطلبات المتصفح (Playwright)...", 10)
            if not self._check_playwright_installed():
                self.progress.emit("جاري تحميل متصفح Chromium في الخلفية (قد يستغرق بعض الوقت)...", 20)
                self._install_playwright()
            
            self.progress.emit("تم التحقق من متصفح Chromium بنجاح.", 50)
            
            if platform.system() == "Windows":
                self.progress.emit("جاري التحقق من محرك فحص الشبكة (Npcap)...", 60)
                if not self._check_npcap_installed():
                    self.progress.emit("مطلوب تثبيت Npcap. في انتظار تدخل المستخدم...", 70)
                    self.action_required.emit("npcap", "Npcap-installer.exe")
                    return 
                    
            self.progress.emit("جميع المتطلبات متوفرة! جاري تشغيل التطبيق...", 100)
            self.finished.emit(True, "")
            
        except Exception as e:
            self.finished.emit(False, str(e))

    def _check_playwright_installed(self):
        try:
            cache_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "ms-playwright")
            if platform.system() == "Linux":
                cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "ms-playwright")
            elif platform.system() == "Darwin":
                cache_dir = os.path.join(os.path.expanduser("~"), "Library", "Caches", "ms-playwright")
                
            if os.path.exists(cache_dir):
                for folder in os.listdir(cache_dir):
                    if folder.startswith("chromium"):
                        return True
            return False
        except Exception as e:
            logging.error(f"Error checking playwright: {e}")
            return False

    def _install_playwright(self):
        startupinfo = None
        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            subprocess.check_call(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                startupinfo=startupinfo
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"فشل تثبيت متصفح Chromium: {str(e)}")

    def _check_npcap_installed(self):
        paths = [
            os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "Npcap"),
            os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Npcap"),
            os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Npcap")
        ]
        return any(os.path.exists(path) for path in paths)


class BootstrapperWindow(QWidget):
    boot_successful = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("تجهيز بيئة العمل - Router Admin")
        self.setFixedSize(500, 250)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        self.status_label = QLabel("جاري تهيئة التطبيق لأول مرة...")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        self.install_npcap_btn = QPushButton("تثبيت Npcap الآن")
        self.install_npcap_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb; color: white; padding: 10px; 
                border-radius: 6px; font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        self.install_npcap_btn.hide()
        self.install_npcap_btn.clicked.connect(self.launch_npcap_installer)
        layout.addWidget(self.install_npcap_btn)
        
        self.npcap_installer_path = ""
        
        self.start_bootstrapping()

    def start_bootstrapping(self):
        self.install_npcap_btn.hide()
        self.thread = BootstrapperThread()
        self.thread.progress.connect(self.update_progress)
        self.thread.action_required.connect(self.handle_action_required)
        self.thread.finished.connect(self.on_finished)
        self.thread.start()

    def update_progress(self, text, value):
        self.status_label.setText(text)
        self.progress_bar.setValue(value)

    def handle_action_required(self, action_type, path):
        if action_type == "npcap":
            self.npcap_installer_path = path
            self.status_label.setText("مكتبة الفحص (Scapy) تتطلب Npcap لتعمل. يرجى تثبيت Npcap للاستمرار.")
            self.install_npcap_btn.show()

    def launch_npcap_installer(self):
        # We need to make sure the base path is robust (PyInstaller bundle or standard execution)
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.join(base_path, self.npcap_installer_path)

        if not os.path.exists(full_path):
            QMessageBox.warning(self, "ملف مفقود", f"ملف التثبيت {full_path} غير موجود بجانب البرنامج. يرجى تحميله وتثبيته يدوياً.")
            self.install_npcap_btn.setText("إعادة المحاولة بعد التثبيت")
            self.install_npcap_btn.clicked.disconnect()
            self.install_npcap_btn.clicked.connect(self.start_bootstrapping)
            return
            
        try:
            self.status_label.setText("جاري تشغيل مثبت Npcap... الرجاء إكمال التثبيت ثم اضغط إعادة المحاولة.")
            if platform.system() == "Windows":
                os.startfile(full_path)
            else:
                subprocess.Popen([full_path])
                
            self.install_npcap_btn.setText("إعادة المحاولة بعد التثبيت")
            self.install_npcap_btn.clicked.disconnect()
            self.install_npcap_btn.clicked.connect(self.start_bootstrapping)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء محاولة تشغيل المثبت: {e}")

    def on_finished(self, success, error_msg):
        if success:
            self.boot_successful.emit()
            self.close()
        else:
            QMessageBox.critical(self, "خطأ فادح", f"فشل تجهيز بيئة العمل:\n{error_msg}")
            sys.exit(1)
