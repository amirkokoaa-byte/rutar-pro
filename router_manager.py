from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import logging
import time
import threading

class RouterManager:
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.base_url = f"http://{self.ip}"
        self.playwright = None
        self.browser = None
        self.page = None

    def _start_browser(self):
        """يبدأ تشغيل المتصفح في الخلفية إذا لم يكن يعمل بالفعل"""
        if not self.playwright:
            self.playwright = sync_playwright().start()
            # نستخدم المتصفح في وضع مخفي (Headless) حتى لا يظهر للمستخدم
            self.browser = self.playwright.chromium.launch(headless=True)
            self.page = self.browser.new_page()

    def stop_browser(self):
        """يغلق المتصفح ويحرر الموارد"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
            
    def login(self):
        """
        محاولة تسجيل الدخول لصفحة الراوتر.
        نستخدم Playwright لأنه يتعامل بسهولة مع صفحات الراوتر التي تستخدم JavaScript
        لتشفير كلمة المرور قبل الإرسال (مثل راوترات ZTE الحديثة).
        """
        self._start_browser()
        
        try:
            # الانتقال لصفحة الراوتر
            self.page.goto(self.base_url, timeout=15000)
            self.page.wait_for_load_state("networkidle")
            
            # البحث عن حقول إدخال اسم المستخدم وكلمة المرور
            # هذه المحددات (Selectors) عامة وتغطي أغلب راوترات WE/Vodafone/Etisalat/Orange
            user_input = self.page.locator("input[type='text'], input[id*='user'], input[id*='name']").first
            pass_input = self.page.locator("input[type='password'], input[id*='pass'], input[id*='pwd']").first
            
            if user_input.is_visible() and pass_input.is_visible():
                user_input.fill(self.username)
                pass_input.fill(self.password)
                
                # الضغط على زر الدخول (Enter)
                pass_input.press("Enter")
                
                # ننتظر قليلاً لمعرفة نتيجة تسجيل الدخول (سواء بتحميل صفحة جديدة أو ظهور خطأ)
                try:
                    self.page.wait_for_load_state("networkidle", timeout=5000)
                except PlaywrightTimeoutError:
                    pass # بعض الراوترات لا تقوم بتحديث كامل للصفحة (AJAX)
                
                # التحقق من وجود رسائل خطأ شائعة في الصفحة
                page_text = self.page.content().lower()
                error_keywords = ["incorrect", "wrong", "invalid", "fail", "خطأ", "غير صحيح"]
                if any(keyword in page_text for keyword in error_keywords) and pass_input.is_visible():
                    raise ValueError("بيانات الدخول خاطئة (Invalid username or password)")
                    
            return True
            
        except PlaywrightTimeoutError:
            raise ConnectionError(f"انتهى وقت الاتصال. تأكد من أن الـ IP صحيح ({self.ip}) وأنك متصل بالشبكة.")
        except ValueError as ve:
            raise ve
        except Exception as e:
            raise ConnectionError(f"فشل الاتصال بالراوتر بسبب خطأ غير متوقع: {str(e)}")
            
    def detect_router_model(self):
        """
        التعرف على نوع الراوتر (ZTE أم Huawei) بناءً على محتوى الصفحة بعد تسجيل الدخول.
        """
        if not self.page:
            raise RuntimeError("يجب تسجيل الدخول أولاً قبل محاولة التعرف على الموديل")
            
        try:
            page_content = self.page.content().lower()
            title = self.page.title().lower()
            
            # علامات تشير إلى أن الراوتر Huawei
            huawei_indicators = ["huawei", "echolife", "hg531", "hg532", "hg630", "hg633", "dg8045"]
            if any(indicator in page_content or indicator in title for indicator in huawei_indicators):
                return "Huawei"
                
            # علامات تشير إلى أن الراوتر ZTE
            zte_indicators = ["zte", "zxhn", "h168n", "h188a"]
            if any(indicator in page_content or indicator in title for indicator in zte_indicators):
                return "ZTE"
                
            # في حال كانت الواجهة مخصصة بالكامل لمزود الخدمة (مثل WE) ولا يظهر اسم المصنع
            if "te data" in page_content or "we" in title or "vodafone" in title or "orange" in title:
                return "Unknown (Custom ISP Firmware)"
                
            return "Unknown"
            
        except Exception as e:
            logging.error(f"حدث خطأ أثناء محاولة التعرف على الراوتر: {str(e)}")
            return "Unknown"

    def get_connected_devices(self):
        """
        تقوم هذه الدالة بقراءة الأجهزة المتصلة (DHCP Client List / WLAN Clients) من صفحة الراوتر.
        نظراً لاختلاف واجهات الراوترات (ZTE, Huawei)، هذه الدالة تحتوي على هيكل عام
        يمكن توسيعه ليشمل مسارات محددة لكل نوع.
        """
        if not self.page:
            raise RuntimeError("يجب تسجيل الدخول أولاً قبل محاولة قراءة الأجهزة")
            
        devices = []
        model = self.detect_router_model()
        
        try:
            # هنا نقوم بمحاكاة منطق استخراج البيانات الفعلي (سيختلف حسب كل موديل)
            if model == "ZTE":
                # مثال تخيلي لمسار صفحة الأجهزة في راوترات ZTE
                # self.page.goto(f"{self.base_url}/html/network/lan/dhcp_client.htm")
                # rows = self.page.locator("table#dhcp_list tr").all()
                pass
            elif model == "Huawei":
                # مثال تخيلي لمسار صفحة الأجهزة في راوترات Huawei
                # self.page.goto(f"{self.base_url}/html/status/devinfo.asp")
                pass
                
            # سنقوم بإرجاع بيانات وهمية (Mock Data) للتوضيح
            # في التطبيق الحقيقي، سيتم استخراج هذه البيانات عن طريق BeautifulSoup أو Playwright Locators
            return [
                {"hostname": "Desktop-PC", "ip": "192.168.1.5", "mac": "00:1A:2B:3C:4D:5E", "type": "pc"},
                {"hostname": "iPhone-13", "ip": "192.168.1.12", "mac": "A1:B2:C3:D4:E5:F6", "type": "phone"},
                {"hostname": "Smart-TV", "ip": "192.168.1.20", "mac": "11:22:33:44:55:66", "type": "tv"},
                {"hostname": "Galaxy-S21", "ip": "192.168.1.15", "mac": "5A:4B:3C:2D:1E:0F", "type": "phone"}
            ]
            
        except Exception as e:
            logging.error(f"خطأ أثناء استخراج قائمة الأجهزة: {str(e)}")
            return []

    def change_ssid(self, new_ssid):
        """
        تغيير اسم شبكة الواي فاي (SSID)
        """
        if not self.page:
            raise RuntimeError("يجب تسجيل الدخول أولاً قبل محاولة تعديل الإعدادات")
            
        model = self.detect_router_model()
        logging.info(f"جاري محاولة تغيير اسم الشبكة إلى '{new_ssid}' لراوتر نوع {model}")
        
        try:
            if model == "ZTE":
                # مثال تخيلي لتغيير الاسم في راوترات ZTE
                # self.page.goto(f"{self.base_url}/html/network/wlan/wlan_basic.htm")
                # self.page.fill("input#ssid_name", new_ssid)
                # self.page.click("input#apply_button")
                pass
            elif model == "Huawei":
                # مثال تخيلي لتغيير الاسم في راوترات Huawei
                # self.page.goto(f"{self.base_url}/html/basic/wlan.asp")
                # self.page.fill("input#ESSID", new_ssid)
                # self.page.click("button#Submit")
                pass
            return True
        except Exception as e:
            logging.error(f"خطأ أثناء تغيير اسم الشبكة: {str(e)}")
            return False

    def change_wlan_password(self, new_password):
        """
        تغيير كلمة مرور شبكة الواي فاي
        """
        if not self.page:
            raise RuntimeError("يجب تسجيل الدخول أولاً قبل محاولة تعديل الإعدادات")
            
        model = self.detect_router_model()
        logging.info(f"جاري محاولة تغيير كلمة مرور الواي فاي لراوتر نوع {model}")
        
        try:
            if model == "ZTE":
                # self.page.goto(f"{self.base_url}/html/network/wlan/wlan_security.htm")
                # self.page.fill("input#wpa_passphrase", new_password)
                # self.page.click("input#apply_button")
                pass
            elif model == "Huawei":
                # self.page.goto(f"{self.base_url}/html/basic/wlan.asp")
                # self.page.fill("input#WPA_PSK", new_password)
                # self.page.click("button#Submit")
                pass
            return True
        except Exception as e:
            logging.error(f"خطأ أثناء تغيير كلمة المرور: {str(e)}")
            return False

    def change_network_mode(self, mode):
        """
        تغيير وضع الشبكة (مثلاً 802.11b/g/n) لتحديد السرعة والنطاق
        """
        if not self.page:
            raise RuntimeError("يجب تسجيل الدخول أولاً قبل محاولة تعديل الإعدادات")
            
        model = self.detect_router_model()
        logging.info(f"جاري محاولة تغيير وضع الشبكة إلى '{mode}' لراوتر نوع {model}")
        
        try:
            if model == "ZTE":
                # self.page.goto(f"{self.base_url}/html/network/wlan/wlan_basic.htm")
                # self.page.select_option("select#network_mode", mode)
                # self.page.click("input#apply_button")
                pass
            elif model == "Huawei":
                # self.page.goto(f"{self.base_url}/html/basic/wlan.asp")
                # self.page.select_option("select#NetworkMode", mode)
                # self.page.click("button#Submit")
                pass
            return True
        except Exception as e:
            logging.error(f"خطأ أثناء تغيير وضع الشبكة: {str(e)}")
            return False

    def set_qos_limit(self, mac_address, speed_limit_kbps):
        """
        تحديد السرعة القصوى لجهاز معين باستخدام إعدادات الـ QoS (Quality of Service) أو Bandwidth Control.
        """
        if not self.page:
            raise RuntimeError("يجب تسجيل الدخول أولاً قبل تعديل إعدادات السرعة")
            
        model = self.detect_router_model()
        logging.info(f"تعيين حد سرعة {speed_limit_kbps} Kbps للجهاز {mac_address} على راوتر {model}")
        
        try:
            if model == "ZTE":
                # مثال للـ QoS في ZTE
                # self.page.goto(f"{self.base_url}/html/network/qos/qos_classification.htm")
                # إدخال الماك أدرس والسرعة المطلوبة وحفظ الإعدادات
                pass
            elif model == "Huawei":
                # مثال لـ Bandwidth Control في Huawei
                # self.page.goto(f"{self.base_url}/html/advanced/bandwidth.asp")
                pass
            return True
        except Exception as e:
            logging.error(f"خطأ أثناء تحديد السرعة: {str(e)}")
            return False

    def block_mac_address(self, mac_address):
        """
        حظر جهاز معين من الاتصال بالشبكة باستخدام MAC Filter.
        """
        if not self.page:
            raise RuntimeError("يجب تسجيل الدخول أولاً قبل حظر الأجهزة")
            
        model = self.detect_router_model()
        logging.info(f"حظر الماك أدرس {mac_address} على راوتر {model}")
        
        try:
            if model == "ZTE":
                # self.page.goto(f"{self.base_url}/html/network/wlan/mac_filter.htm")
                # إضافة الماك لقائمة الحظر Blacklist
                pass
            elif model == "Huawei":
                # self.page.goto(f"{self.base_url}/html/advanced/macfilter.asp")
                pass
            return True
        except Exception as e:
            logging.error(f"خطأ أثناء حظر الجهاز: {str(e)}")
            return False

    def get_device_usage(self, mac_address):
        """
        قراءة استهلاك البيانات (Bytes/Packets) لجهاز معين من صفحة الإحصائيات (Statistics).
        تستخدم هذه الدالة لمراقبة الجيجات المستهلكة.
        """
        if not self.page:
            return 0.0
            
        try:
            # سنقوم بإرجاع قيمة وهمية للاستهلاك بالجيجابايت بغرض التوضيح
            # في الحقيقة يجب قراءة القيم من جدول الـ Statistics في الراوتر بناءً على الـ MAC/IP
            logging.info(f"قراءة استهلاك الجهاز {mac_address}...")
            return 1.5  # 1.5 GB استهلاك كقيمة وهمية
        except Exception as e:
            logging.error(f"خطأ أثناء قراءة استهلاك الجهاز: {str(e)}")
            return 0.0

    def monitor_quota_thread(self, mac_address, quota_limit_gb):
        """
        دالة تعمل في الخلفية لمراقبة استهلاك جهاز معين، وتقوم بحظره إذا تجاوز الباقة (Quota).
        """
        logging.info(f"بدء مراقبة الجهاز {mac_address} للحد الأقصى {quota_limit_gb} جيجابايت...")
        
        def monitor_task():
            # يجب تسجيل الدخول ضمن هذا الخيط (Thread) إذا كان المتصفح يعمل في سياق مختلف
            # أو استخدام الجلسة الحالية بحذر إذا كانت Thread-Safe
            while True:
                try:
                    usage_gb = self.get_device_usage(mac_address)
                    logging.info(f"الاستهلاك الحالي للجهاز {mac_address}: {usage_gb} GB")
                    
                    if usage_gb >= float(quota_limit_gb):
                        logging.warning(f"الجهاز {mac_address} تجاوز الحد المسموح به ({quota_limit_gb} GB)! جاري الحظر...")
                        self.block_mac_address(mac_address)
                        break  # إيقاف المراقبة بعد الحظر
                        
                    # الانتظار 5 دقائق قبل الفحص التالي
                    time.sleep(300)
                    
                except Exception as e:
                    logging.error(f"خطأ في خيط المراقبة: {str(e)}")
                    break

        # تشغيل الدالة في Thread منفصل لعدم تجميد واجهة المستخدم
        thread = threading.Thread(target=monitor_task, daemon=True)
        thread.start()
        return thread
            
    # دعم استخدام الـ Context Manager لضمان إغلاق المتصفح تلقائياً
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_browser()

# ==========================================
# مثال على كيفية الاستخدام للبرمجة لاحقاً:
# ==========================================
if __name__ == "__main__":
    # هذا الكود لن يعمل إلا إذا تم تشغيله كسكربت منفصل محلياً
    try:
        print("جاري محاولة الاتصال بالراوتر...")
        # استخدام with لضمان إغلاق المتصفح بعد الانتهاء
        with RouterManager("192.168.1.1", "admin", "admin") as router:
            if router.login():
                print("تم تسجيل الدخول بنجاح!")
                model = router.detect_router_model()
                print(f"تم التعرف على نوع الراوتر: {model}")
                
    except ValueError as e:
        print(f"خطأ في بيانات الدخول: {e}")
    except ConnectionError as e:
        print(f"خطأ في الاتصال: {e}")
    except Exception as e:
        print(f"خطأ عام: {e}")
