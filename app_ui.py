import sys
import sqlite3
import csv
import logging
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QStackedWidget, QListWidget, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QComboBox, QMessageBox, QGroupBox, QFileDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from router_manager import RouterManager
from hybrid_connection_engine import HybridConnectionEngine
from router_actions_executor import RouterActionsExecutor
from bandwidth_daemon import BandwidthDaemon

class WorkerThread(QThread):
    """
    خيط (Thread) مخصص لتشغيل المهام التي تستغرق وقتاً طويلاً
    في الخلفية حتى لا تتجمد واجهة المستخدم.
    """
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("مدير الراوتر المحلي - Local Router Manager")
        self.resize(900, 600)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.router = None
        self.engine = None
        self.executor = None
        self.daemon = None
        self.current_router_id = None
        self.db_path = "bandwidth.db"

        # الواجهة الرئيسية
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        
        # القائمة الجانبية
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(220)
        self.sidebar.addItem("تسجيل الدخول")
        self.sidebar.addItem("إعدادات الواي فاي")
        self.sidebar.addItem("الأجهزة المتصلة")
        self.sidebar.addItem("التحكم في السرعات")
        self.sidebar.currentRowChanged.connect(self.switch_page)
        self.main_layout.addWidget(self.sidebar)

        # صفحات التطبيق
        self.pages = QStackedWidget()
        self.main_layout.addWidget(self.pages)

        self.setup_login_page()
        self.setup_wifi_page()
        self.setup_devices_page()
        self.setup_qos_page()

        self.sidebar.setCurrentRow(0)

        # QTimer لتحديث استهلاك الأجهزة (Real-Time Updates)
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.refresh_usage_data)
        
        # QTimer لنظام الإصلاح الذاتي (Self-Healing)
        self.health_timer = QTimer(self)
        self.health_timer.timeout.connect(self.check_connection_health)

    def switch_page(self, index):
        if index != 0 and not self.router:
            QMessageBox.warning(self, "تنبيه", "يجب تسجيل الدخول للراوتر أولاً")
            self.sidebar.setCurrentRow(0)
            return
        
        self.pages.setCurrentIndex(index)
        
        # إذا انتقل لصفحة الأجهزة وتم تسجيل الدخول، فقم بالفحص تلقائياً
        if index == 2 and self.router: 
            self.scan_devices()

    # ==========================
    # صفحة تسجيل الدخول
    # ==========================
    def setup_login_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addStretch()
        
        group_box = QGroupBox("بيانات اتصال الراوتر")
        group_layout = QVBoxLayout(group_box)
        group_layout.setSpacing(15)
        
        self.ip_input = QLineEdit("192.168.1.1")
        self.ip_input.setPlaceholderText("عنوان IP الافتراضي")
        group_layout.addWidget(QLabel("عنوان IP:"))
        group_layout.addWidget(self.ip_input)
        
        self.user_input = QLineEdit("admin")
        group_layout.addWidget(QLabel("اسم المستخدم:"))
        group_layout.addWidget(self.user_input)
        
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        group_layout.addWidget(QLabel("كلمة المرور:"))
        group_layout.addWidget(self.pass_input)
        
        self.router_combo = QComboBox()
        self.router_combo.addItems(["ZTE_ZXHN_H168N", "Huawei_DG8045", "TPLink_Archer_VR600"])
        group_layout.addWidget(QLabel("اختر نوع الراوتر:"))
        group_layout.addWidget(self.router_combo)
        
        self.login_btn = QPushButton("تسجيل الدخول")
        self.login_btn.setMinimumHeight(40)
        self.login_btn.clicked.connect(self.do_login)
        group_layout.addWidget(self.login_btn)
        
        layout.addWidget(group_box)
        layout.addStretch()
        self.pages.addWidget(page)

    def do_login(self, silent=False):
        ip = self.ip_input.text()
        user = self.user_input.text()
        pwd = self.pass_input.text()
        router_id = self.router_combo.currentText()
        
        if not silent:
            self.login_btn.setEnabled(False)
            self.login_btn.setText("جاري الاتصال...")
        
        self.current_router_id = router_id
        # استخدام RouterManager القديم للفحص (Backward Compatibility)
        self.router = RouterManager(ip, user, pwd)
        
        def login_task():
            # دمج المعمارية الجديدة (Hybrid Engine + Executor)
            self.engine = HybridConnectionEngine(ip, user, pwd)
            session = self.engine.connect(router_id)
            self.executor = RouterActionsExecutor(ip, session, router_id)
            # وتهيئة RouterManager القديم لدعم الدوال التي لم نكتبها في Executor (مثل الفحص)
            self.router.login()
            return True

        self.worker = WorkerThread(login_task)
        if not silent:
            self.worker.finished.connect(self.on_login_success)
            self.worker.error.connect(self.on_login_error)
        else:
            self.worker.finished.connect(self.on_silent_login_success)
            self.worker.error.connect(self.on_silent_login_error)
        self.worker.start()

    def on_login_success(self, result):
        self.login_btn.setEnabled(True)
        self.login_btn.setText("تسجيل الدخول")
        if result:
            QMessageBox.information(self, "نجاح", f"تم تسجيل الدخول بنجاح عبر المحرك الهجين!")
            
            # تشغيل الـ Daemon
            if not self.daemon:
                self.daemon = BandwidthDaemon(router_executor=self.executor)
                self.daemon.start()
                
            # تشغيل المؤقتات (Timers)
            self.update_timer.start(5000) # تحديث كل 5 ثواني
            self.health_timer.start(30000) # فحص الاتصال كل 30 ثانية
            
            self.sidebar.setCurrentRow(1) # الانتقال لصفحة الواي فاي
    
    def on_login_error(self, err):
        self.login_btn.setEnabled(True)
        self.login_btn.setText("تسجيل الدخول")
        self.router = None
        self.executor = None
        QMessageBox.critical(self, "خطأ في الاتصال", f"فشل تسجيل الدخول:\n{err}")

    # ==========================
    # نظام الإصلاح الذاتي (Self-Healing)
    # ==========================
    def check_connection_health(self):
        if not self.executor:
            return
            
        def ping_router():
            try:
                # محاولة طلب بسيط للراوتر للتحقق من الاتصال
                resp = self.executor.session.get(self.executor.base_url, timeout=5)
                # إذا رد الراوتر بطلب تسجيل الدخول، يعني فقدان الجلسة
                if "login" in resp.url.lower() or resp.status_code in [401, 403]:
                    return False
                return True
            except Exception:
                return False
                
        self.health_worker = WorkerThread(ping_router)
        self.health_worker.finished.connect(self.on_health_check_done)
        self.health_worker.start()

    def on_health_check_done(self, is_healthy):
        if not is_healthy:
            logging.warning("Self-Healing: تم اكتشاف فقدان الاتصال. جاري إعادة تسجيل الدخول بصمت...")
            self.do_login(silent=True)

    def on_silent_login_success(self, result):
        logging.info("Self-Healing: تم استعادة الاتصال بنجاح في الخلفية.")
        if self.daemon and self.executor:
            self.daemon.router_executor = self.executor

    def on_silent_login_error(self, err):
        logging.error(f"Self-Healing: فشل استعادة الاتصال - {err}")

    # ==========================
    # صفحة الواي فاي
    # ==========================
    def setup_wifi_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        group_box = QGroupBox("إعدادات شبكة الـ WLAN")
        group_layout = QVBoxLayout(group_box)
        group_layout.setSpacing(15)
        
        self.ssid_input = QLineEdit()
        self.ssid_input.setPlaceholderText("اكتب اسم الشبكة الجديد")
        group_layout.addWidget(QLabel("اسم الشبكة (SSID):"))
        group_layout.addWidget(self.ssid_input)
        
        self.wifi_pass_input = QLineEdit()
        self.wifi_pass_input.setPlaceholderText("اكتب كلمة المرور الجديدة")
        group_layout.addWidget(QLabel("كلمة المرور الجديدة:"))
        group_layout.addWidget(self.wifi_pass_input)
        
        self.wifi_mode = QComboBox()
        self.wifi_mode.addItems(["802.11b/g/n (ينصح به للمحمول القديم والجديد)", "802.11b/g", "802.11n (سرعة عالية فقط)"])
        group_layout.addWidget(QLabel("وضع الشبكة:"))
        group_layout.addWidget(self.wifi_mode)
        
        self.save_wifi_btn = QPushButton("حفظ الإعدادات")
        self.save_wifi_btn.setMinimumHeight(40)
        self.save_wifi_btn.clicked.connect(self.do_save_wifi)
        group_layout.addWidget(self.save_wifi_btn)
        
        layout.addWidget(group_box)
        layout.addStretch()
        self.pages.addWidget(page)

    def do_save_wifi(self):
        ssid = self.ssid_input.text()
        pwd = self.wifi_pass_input.text()
        mode_text = self.wifi_mode.currentText()
        mode = mode_text.split(" ")[0] # أخذ القيمة الأولى فقط
        
        self.save_wifi_btn.setEnabled(False)
        self.save_wifi_btn.setText("جاري إرسال الإعدادات...")
        
        def save_all():
            if ssid: self.router.change_ssid(ssid)
            if pwd: self.router.change_wlan_password(pwd)
            if mode: self.router.change_network_mode(mode)
            return True
            
        self.wifi_worker = WorkerThread(save_all)
        self.wifi_worker.finished.connect(lambda res: self.on_task_done(self.save_wifi_btn, "حفظ الإعدادات"))
        self.wifi_worker.error.connect(lambda err: self.on_task_error(err, self.save_wifi_btn, "حفظ الإعدادات"))
        self.wifi_worker.start()

    # ==========================
    # صفحة الأجهزة المتصلة
    # ==========================
    def setup_devices_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        top_layout = QHBoxLayout()
        self.scan_btn = QPushButton("فحص الشبكة وتحديث القائمة")
        self.scan_btn.setMinimumHeight(40)
        self.scan_btn.clicked.connect(self.scan_devices)
        top_layout.addWidget(self.scan_btn)
        
        self.export_btn = QPushButton("تصدير إلى Excel (CSV)")
        self.export_btn.setMinimumHeight(40)
        self.export_btn.setStyleSheet("background-color: #10b981;") # لون أخضر
        self.export_btn.clicked.connect(self.export_to_excel)
        top_layout.addWidget(self.export_btn)
        
        layout.addLayout(top_layout)
        
        self.devices_table = QTableWidget(0, 5)
        self.devices_table.setHorizontalHeaderLabels(["اسم الجهاز", "عنوان IP", "عنوان MAC Address", "النوع", "الاستهلاك (GB)"])
        self.devices_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.devices_table)
        
        self.pages.addWidget(page)

    def refresh_usage_data(self):
        """تحديث جدول الأجهزة بالاستهلاك الفعلي من قاعدة البيانات"""
        if self.pages.currentIndex() != 2:
            return # تحديث الجدول فقط إذا كان المستخدم في صفحة الأجهزة
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT mac_address, bytes_used FROM device_usage')
                usage_map = {row[0]: row[1] for row in cursor.fetchall()}
                
                # تحديث الخلية الخامسة (Index 4) في كل صف
                for row in range(self.devices_table.rowCount()):
                    mac_item = self.devices_table.item(row, 2)
                    if mac_item:
                        mac = mac_item.text()
                        bytes_used = usage_map.get(mac, 0)
                        gb_used = bytes_used / (1024 ** 3)
                        self.devices_table.setItem(row, 4, QTableWidgetItem(f"{gb_used:.3f} GB"))
        except Exception as e:
            logging.error(f"خطأ في تحديث الاستهلاك: {str(e)}")

    def export_to_excel(self):
        if self.devices_table.rowCount() == 0:
            QMessageBox.warning(self, "تنبيه", "لا توجد بيانات للتصدير.")
            return
            
        path, _ = QFileDialog.getSaveFileName(self, "حفظ التقرير", "Router_Usage_Report.csv", "CSV Files (*.csv)")
        if not path:
            return
            
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["اسم الجهاز", "عنوان IP", "عنوان MAC Address", "النوع", "الاستهلاك (GB)"])
                for row in range(self.devices_table.rowCount()):
                    row_data = []
                    for col in range(5):
                        item = self.devices_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "نجاح", f"تم التصدير بنجاح إلى:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء التصدير:\n{str(e)}")

    def scan_devices(self):
        if not self.router: return
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("جاري الفحص والقراءة من الراوتر...")
        
        self.scan_worker = WorkerThread(self.router.get_connected_devices)
        self.scan_worker.finished.connect(self.on_scan_done)
        self.scan_worker.error.connect(lambda err: self.on_task_error(err, self.scan_btn, "فحص الشبكة وتحديث القائمة"))
        self.scan_worker.start()

    def on_scan_done(self, devices):
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("فحص الشبكة وتحديث القائمة")
        
        self.devices_table.setRowCount(0)
        self.mac_combo.clear() # تحديث قائمة الماك أدرس في صفحة السرعات
        self.mac_combo.addItem("-- اختر جهازاً --", "")
        
        for i, dev in enumerate(devices):
            self.devices_table.insertRow(i)
            self.devices_table.setItem(i, 0, QTableWidgetItem(dev.get("hostname", "مجهول")))
            self.devices_table.setItem(i, 1, QTableWidgetItem(dev.get("ip", "")))
            self.devices_table.setItem(i, 2, QTableWidgetItem(dev.get("mac", "")))
            self.devices_table.setItem(i, 3, QTableWidgetItem(dev.get("type", "")))
            self.devices_table.setItem(i, 4, QTableWidgetItem("0.000 GB")) # القيمة المبدئية
            
            self.mac_combo.addItem(f"{dev.get('hostname')} ({dev.get('mac')})", dev.get("mac"))

    # ==========================
    # صفحة التحكم في السرعات
    # ==========================
    def setup_qos_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        group_box = QGroupBox("التحكم في السرعات (QoS) وحظر الاستهلاك (Quota)")
        group_layout = QVBoxLayout(group_box)
        group_layout.setSpacing(15)
        
        self.mac_combo = QComboBox()
        group_layout.addWidget(QLabel("اختر الجهاز (يتم جلبه من قائمة الفحص):"))
        group_layout.addWidget(self.mac_combo)
        
        self.speed_input = QLineEdit()
        self.speed_input.setPlaceholderText("مثال: 512 (لتعيين نصف ميجا) أو اتركه فارغاً")
        group_layout.addWidget(QLabel("السرعة القصوى (Kbps):"))
        group_layout.addWidget(self.speed_input)
        
        self.quota_input = QLineEdit()
        self.quota_input.setPlaceholderText("الحد الأقصى بالجيجابايت (مثال: 10)")
        group_layout.addWidget(QLabel("حد الاستهلاك ليتم الحظر تلقائياً (جيجابايت):"))
        group_layout.addWidget(self.quota_input)
        
        self.save_qos_btn = QPushButton("تطبيق وتفعيل المراقبة")
        self.save_qos_btn.setMinimumHeight(40)
        self.save_qos_btn.clicked.connect(self.do_save_qos)
        group_layout.addWidget(self.save_qos_btn)
        
        layout.addWidget(group_box)
        layout.addStretch()
        self.pages.addWidget(page)

    def do_save_qos(self):
        mac = self.mac_combo.currentData()
        if not mac:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار جهاز أولاً. قم بعمل فحص للشبكة إذا كانت القائمة فارغة.")
            return
            
        speed = self.speed_input.text()
        quota = self.quota_input.text()
        
        self.save_qos_btn.setEnabled(False)
        self.save_qos_btn.setText("جاري تطبيق الإعدادات...")
        
        def save_qos_logic():
            if speed and self.executor:
                # نستخدم الـ executor إذا كان يدعم هذه الدالة (في هذا المثال نستخدم router للتبسيط)
                self.router.set_qos_limit(mac, speed)
            if quota and self.daemon:
                # نستخدم الـ Daemon المطور
                self.daemon.set_quota(mac, float(quota))
            return True
            
        self.qos_worker = WorkerThread(save_qos_logic)
        self.qos_worker.finished.connect(lambda res: self.on_task_done(self.save_qos_btn, "تطبيق وتفعيل المراقبة"))
        self.qos_worker.error.connect(lambda err: self.on_task_error(err, self.save_qos_btn, "تطبيق وتفعيل المراقبة"))
        self.qos_worker.start()

    # ==========================
    # دوال مساعدة عامة
    # ==========================
    def on_task_done(self, btn, text):
        btn.setEnabled(True)
        btn.setText(text)
        QMessageBox.information(self, "نجاح", "تم تنفيذ العملية بنجاح!")

    def on_task_error(self, err, btn, text):
        btn.setEnabled(True)
        btn.setText(text)
        QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء التنفيذ:\n{err}")
        
    def closeEvent(self, event):
        # التأكد من إغلاق المتصفح الخفي الخاص بـ Playwright عند إغلاق البرنامج
        if self.daemon:
            self.daemon.stop()
        if self.router:
            self.router.stop_browser()
        if self.engine:
            self.engine._cleanup_playwright()
        event.accept()

