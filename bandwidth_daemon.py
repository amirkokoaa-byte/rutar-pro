import sqlite3
import threading
import time
import logging
from collections import defaultdict
from scapy.all import sniff, IP, Ether
import psutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BandwidthDaemon:
    """
    خدمة تعمل في الخلفية (Daemon) لمراقبة استهلاك الأجهزة (Bandwidth)
    تقوم بحفظ البيانات بشكل دوري في SQLite، وتقوم بحظر الماك أدرس عبر الراوتر
    إذا تجاوز الاستهلاك الحصة (Quota) المحددة.
    تم التصميم ليكون خفيفاً على المعالج (Low CPU Usage).
    """
    def __init__(self, router_executor, db_path="bandwidth.db", flush_interval=10):
        self.router_executor = router_executor
        self.db_path = db_path
        self.flush_interval = flush_interval
        
        # مخزن مؤقت للاستهلاك في الذاكرة لتقليل عمليات الكتابة على القرص (Mac -> Bytes)
        self.usage_buffer = defaultdict(int)
        self.lock = threading.Lock()
        
        # تخزين الحصص (Quotas) في الذاكرة لسرعة الوصول (Mac -> Quota in Bytes)
        self.quotas = {}
        self.blocked_macs = set()
        
        self.is_running = False
        self._init_db()
        self._load_quotas_and_usage()

    def _init_db(self):
        """إنشاء قاعدة البيانات وجدول الاستهلاك إذا لم يكن موجوداً"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS device_usage (
                    mac_address TEXT PRIMARY KEY,
                    bytes_used INTEGER DEFAULT 0,
                    quota_bytes INTEGER DEFAULT 0,
                    is_blocked BOOLEAN DEFAULT 0
                )
            ''')
            conn.commit()

    def _load_quotas_and_usage(self):
        """تحميل إعدادات الحصص والأجهزة المحظورة من قاعدة البيانات"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT mac_address, bytes_used, quota_bytes, is_blocked FROM device_usage')
            for row in cursor.fetchall():
                mac, used, quota, blocked = row
                if quota > 0:
                    self.quotas[mac] = quota
                if blocked:
                    self.blocked_macs.add(mac)

    def set_quota(self, mac_address, quota_gb):
        """تحديد الحد الأقصى للاستهلاك لجهاز معين بالجيجابايت"""
        quota_bytes = int(float(quota_gb) * 1024 * 1024 * 1024)
        self.quotas[mac_address] = quota_bytes
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO device_usage (mac_address, quota_bytes) 
                VALUES (?, ?) 
                ON CONFLICT(mac_address) DO UPDATE SET quota_bytes=?
            ''', (mac_address, quota_bytes, quota_bytes))
            conn.commit()
        logging.info(f"تم تعيين الحد الأقصى {quota_gb} GB للجهاز {mac_address}")

    def process_packet(self, packet):
        """دالة معالجة الحزم (Callback) تستدعى مع كل حزمة جديدة"""
        if not self.is_running:
            return
            
        # نستخدم طبقة الـ Ethernet لمعرفة الماك أدرس (MAC Address)
        if Ether in packet and IP in packet:
            src_mac = packet[Ether].src
            dst_mac = packet[Ether].dst
            pkt_len = len(packet)
            
            with self.lock:
                # تحديث استهلاك المرسل والمستقبل محلياً
                # في الشبكات المحلية، الماك أدرس الخاص بالراوتر سيكون طرفاً في أغلب الحزم
                self.usage_buffer[src_mac] += pkt_len
                self.usage_buffer[dst_mac] += pkt_len

    def flush_to_db(self):
        """كتابة الاستهلاك المتراكم في قاعدة البيانات كل فترة زمنية وتطبيق قواعد الحظر"""
        while self.is_running:
            time.sleep(self.flush_interval)
            
            with self.lock:
                if not self.usage_buffer:
                    continue
                # أخذ نسخة من البيانات وتفريغ المخزن المؤقت (لتجنب إعاقة الخيط الخاص بـ Scapy)
                buffer_copy = dict(self.usage_buffer)
                self.usage_buffer.clear()
                
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for mac, add_bytes in buffer_copy.items():
                    # إضافة الاستهلاك التراكمي
                    cursor.execute('''
                        INSERT INTO device_usage (mac_address, bytes_used) 
                        VALUES (?, ?) 
                        ON CONFLICT(mac_address) DO UPDATE SET bytes_used = bytes_used + ?
                    ''', (mac, add_bytes, add_bytes))
                    
                    # قراءة الاستهلاك الكلي بعد التحديث للتحقق من الحصة (Quota)
                    cursor.execute('SELECT bytes_used FROM device_usage WHERE mac_address = ?', (mac,))
                    row = cursor.fetchone()
                    if row:
                        total_used = row[0]
                    else:
                        continue
                    
                    # التحقق من تجاوز الحصة المسموحة
                    if mac in self.quotas and mac not in self.blocked_macs:
                        if total_used >= self.quotas[mac]:
                            logging.warning(f"تجاوز الجهاز {mac} الحد المسموح به! جاري الحظر...")
                            
                            # استدعاء الدالة من RouterActionsExecutor لحظر الجهاز عبر صفحة الراوتر
                            if self.router_executor:
                                success, msg = self.router_executor.block_mac_address(mac)
                                if success:
                                    self.blocked_macs.add(mac)
                                    cursor.execute('UPDATE device_usage SET is_blocked = 1 WHERE mac_address = ?', (mac,))
                                    logging.info(f"تم حظر الجهاز {mac} بنجاح.")
                                else:
                                    logging.error(f"فشل حظر الجهاز {mac}: {msg}")
                                    
                conn.commit()

    def start(self):
        """تشغيل خدمة المراقبة في الخلفية"""
        if self.is_running:
            return
            
        self.is_running = True
        
        # 1. تشغيل خيط تحديث قاعدة البيانات
        self.db_thread = threading.Thread(target=self.flush_to_db, daemon=True)
        self.db_thread.start()
        
        # 2. تشغيل Sniffer في خيط منفصل (Network Packet Sniffing)
        self.sniff_thread = threading.Thread(target=self._run_sniffer, daemon=True)
        self.sniff_thread.start()
        logging.info("تم تشغيل خدمة مراقبة الاستهلاك في الخلفية (Daemon Started).")

    def _run_sniffer(self):
        """بدء عملية التقاط الحزم من كارت الشبكة"""
        # نستخدم store=False لتقليل استهلاك الذاكرة وعدم حفظ الحزم في قائمة
        # نستخدم filter="ip" لتجاهل الحزم غير المرتبطة بالإنترنت لتقليل الضغط على المعالج
        logging.info("بدء الالتقاط (Sniffing) للشبكة المحلية...")
        sniff(prn=self.process_packet, store=False, filter="ip")
        
    def stop(self):
        """إيقاف خدمة المراقبة"""
        self.is_running = False
        logging.info("تم إيقاف خدمة مراقبة الاستهلاك.")

# ==========================================
# مثال للتجربة بشكل مستقل
# ==========================================
if __name__ == "__main__":
    # كائن وهمي بديل للمحرك لاختبار اللوجيك الداخلي
    class DummyRouterExecutor:
        def block_mac_address(self, mac):
            print(f"--> [MOCK] تنفيذ أمر حظر الماك {mac} على الراوتر...")
            return True, "تم الحظر وهمياً"

    executor = DummyRouterExecutor()
    daemon = BandwidthDaemon(router_executor=executor, flush_interval=5)
    
    # تحديد حصة قليلة جداً لتجربة الحظر السريع (1 ميجابايت للتجربة = 0.001 جيجا)
    test_mac = "00:11:22:33:44:55"
    daemon.set_quota(test_mac, 0.001) 
    
    daemon.start()
    
    try:
        print("الخدمة تعمل في الخلفية. يمكنك تصفح الإنترنت لزيادة الترافيك...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        daemon.stop()
        print("تم إيقاف البرنامج.")
