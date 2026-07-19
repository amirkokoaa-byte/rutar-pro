import json
import logging
import time
from bs4 import BeautifulSoup
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RouterActionsExecutor:
    """
    فئة مسؤولة عن تنفيذ إجراءات الواجهة الرسومية (تغيير اسم الشبكة، كلمة المرور، حظر الأجهزة)
    باستخدام جلسة الاتصال (Session) من المحرك الهجين (HybridConnectionEngine).
    تقوم بقراءة المسارات من ملف JSON وتستخدم BeautifulSoup للتحقق من نجاح العملية.
    """
    def __init__(self, ip, session, router_id, config_path="routers_config.json"):
        self.ip = ip
        self.base_url = f"http://{self.ip}"
        self.session = session
        self.router_id = router_id
        self.config_path = config_path
        self.config = self._load_config()
        self.router_config = self.config.get("routers", {}).get(self.router_id, {})
        self.endpoints = self.router_config.get("endpoints", {})
        
    def _load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"خطأ في قراءة ملف التكوين: {str(e)}")
            return {}

    def _execute_with_retry(self, method, url, data=None, max_retries=3, delay=2):
        """
        ينفذ الطلب مع استراتيجية إعادة المحاولة (Retry Mechanism) في حال فشل الاستجابة أو انقطاع الاتصال.
        """
        for attempt in range(1, max_retries + 1):
            try:
                logging.info(f"محاولة ({attempt}/{max_retries}) للاتصال بالمسار: {url}")
                if method.upper() == "POST":
                    # إرسال البيانات (Payload)
                    response = self.session.post(url, data=data, timeout=15)
                else:
                    response = self.session.get(url, timeout=15)
                    
                response.raise_for_status()
                return response
                
            except requests.RequestException as e:
                logging.warning(f"فشل في المحاولة {attempt}: {str(e)}")
                if attempt == max_retries:
                    logging.error("تم استنفاد جميع محاولات الاتصال.")
                    raise ConnectionError(f"فشل الاتصال بالراوتر بعد {max_retries} محاولات.")
                time.sleep(delay)
                
        return None

    def _verify_success_with_bs4(self, html_content):
        """
        يستخدم تقنية DOM Parsing عبر BeautifulSoup للتأكد من ظهور رسالة النجاح
        أو عدم وجود رسائل خطأ في الصفحة المُرجعة من الراوتر.
        """
        if not html_content:
            return False
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # استخراج النصوص من الصفحة
        page_text = soup.get_text().lower()
        
        # كلمات دلالية تدل على نجاح العملية
        success_keywords = ["success", "saved", "applied", "نجاح", "تم الحفظ", "successfully"]
        # كلمات تدل على خطأ
        error_keywords = ["error", "fail", "invalid", "خطأ", "فشل", "غير صالح"]
        
        # بعض الراوترات لا ترجع رسالة نجاح واضحة، لكن تعود لصفحة الإعدادات بدون أخطاء.
        # لذا، نبحث أولاً عن أي أخطاء.
        for err in error_keywords:
            if err in page_text:
                logging.warning(f"تم العثور على رسالة خطأ في الصفحة: {err}")
                return False
                
        # البحث عن رسائل النجاح
        for succ in success_keywords:
            if succ in page_text:
                return True
                
        # إذا لم نجد لا خطأ ولا نجاح، قد يكون الطلب نجح وتم إعادة التوجيه للصفحة الأساسية
        # نعتبرها ناجحة مبدئياً طالما لم يظهر خطأ. في الواقع العملي، يمكن فحص عناصر DOM محددة (مثل ID للرسالة).
        success_divs = soup.find_all(lambda tag: tag.name == "div" and "success" in tag.get("class", []))
        if success_divs:
            return True
            
        return True

    def change_ssid(self, new_ssid):
        """
        يرسل طلب لتغيير اسم شبكة الواي فاي (SSID)
        """
        endpoint = self.endpoints.get("wlan_endpoint")
        if not endpoint:
            return False, "لم يتم العثور على مسار إعدادات الواي فاي في ملف الإعدادات."
            
        # ملاحظة: إذا كان الراوتر يستخدم token ديناميكي (مثل TP-Link)، يجب استبدال {token} بالقيمة الفعلية
        url = self.base_url + endpoint
        
        # الهيكل التخيلي للبيانات (يختلف حسب كل راوتر، في المشروع الفعلي سيتم جلبه من JSON)
        payload = {
            "ssid_name": new_ssid,
            "action": "apply"
        }
        
        try:
            logging.info(f"إرسال طلب تغيير اسم الشبكة إلى: {new_ssid}")
            response = self._execute_with_retry("POST", url, data=payload)
            
            if self._verify_success_with_bs4(response.text):
                return True, "تم تغيير اسم الشبكة بنجاح."
            else:
                return False, "فشل تغيير الاسم، ظهرت رسالة خطأ في الراوتر."
                
        except Exception as e:
            return False, f"حدث خطأ استثنائي أثناء العملية: {str(e)}"

    def change_wlan_password(self, new_password):
        """
        يرسل طلب لتغيير كلمة مرور الواي فاي (WLAN Password)
        """
        endpoint = self.endpoints.get("wlan_endpoint")
        if not endpoint:
            return False, "لم يتم العثور على مسار إعدادات الواي فاي."
            
        url = self.base_url + endpoint
        
        payload = {
            "wpa_passphrase": new_password,
            "action": "apply"
        }
        
        try:
            logging.info("إرسال طلب تغيير كلمة مرور الواي فاي...")
            response = self._execute_with_retry("POST", url, data=payload)
            
            if self._verify_success_with_bs4(response.text):
                return True, "تم تغيير كلمة المرور بنجاح."
            else:
                return False, "لم تظهر رسالة تأكيد الحفظ في صفحة الراوتر."
                
        except Exception as e:
            return False, f"حدث خطأ أثناء العملية: {str(e)}"

    def block_mac_address(self, mac_address):
        """
        يرسل طلب لحظر جهاز معين باستخدام الـ MAC Address عبر تقنية MAC Filter
        """
        endpoint = self.endpoints.get("mac_filter_endpoint")
        if not endpoint:
            return False, "لم يتم العثور على مسار حظر الأجهزة في الإعدادات."
            
        url = self.base_url + endpoint
        
        payload = {
            "add_mac": mac_address,
            "filter_mode": "blacklist",
            "action": "add"
        }
        
        try:
            logging.info(f"إرسال طلب حظر الماك أدرس: {mac_address}")
            response = self._execute_with_retry("POST", url, data=payload)
            
            if self._verify_success_with_bs4(response.text):
                return True, f"تم حظر الجهاز ذو الماك ({mac_address}) بنجاح."
            else:
                return False, "تعذر تأكيد عملية الحظر من صفحة الراوتر."
                
        except Exception as e:
            return False, f"خطأ أثناء عملية الحظر: {str(e)}"

# ==========================================
# مثال لتجربة الكود بشكل مستقل
# ==========================================
if __name__ == "__main__":
    from hybrid_connection_engine import HybridConnectionEngine
    
    # 1. الاتصال بالراوتر أولاً عبر المحرك الهجين للحصول على الجلسة
    print("جاري الاتصال بالراوتر...")
    try:
        engine = HybridConnectionEngine("192.168.1.1", "admin", "admin")
        session = engine.connect("ZTE_ZXHN_H168N")
        
        # 2. إنشاء منفذ الأوامر وتمرير الجلسة النشطة إليه
        executor = RouterActionsExecutor("192.168.1.1", session, "ZTE_ZXHN_H168N")
        
        # 3. تنفيذ أمر التغيير
        print("جاري تغيير اسم الشبكة...")
        success, message = executor.change_ssid("My_New_WiFi_Network")
        
        print(f"النتيجة: {success} - {message}")
        
    except Exception as ex:
        print(f"حدث خطأ: {ex}")
