import json
import logging
import time
import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HybridConnectionEngine:
    """
    محرك اتصال هجين (Hybrid Connection Engine) يقرأ نوع المصادقة من ملف routers_config.json
    ويستخدم requests للسرعة أو Playwright للراوترات المعقدة التي تتطلب تنفيذ JavaScript.
    """
    def __init__(self, ip, username, password, config_path="routers_config.json"):
        self.ip = ip
        self.username = username
        self.password = password
        self.base_url = f"http://{self.ip}"
        self.config_path = config_path
        self.config = self._load_config()
        
        # إنشاء جلسة requests للحفاظ على الـ Cookies بعد استخراجها
        self.session = requests.Session()
        
        self.playwright = None
        self.browser = None

    def _load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"ملف التكوين {self.config_path} غير موجود.")
            return {}
        except json.JSONDecodeError as e:
            logging.error(f"خطأ في قراءة ملف JSON: {str(e)}")
            return {}

    def connect(self, router_id):
        """
        يبدأ الاتصال بالراوتر بناءً على إعداداته في ملف JSON.
        يُرجع كائن requests.Session يحتوي على جلسة الاتصال النشطة.
        """
        router_config = self.config.get("routers", {}).get(router_id)
        if not router_config:
            raise ValueError(f"معرف الراوتر '{router_id}' غير موجود في الإعدادات.")

        auth_type = router_config.get("login", {}).get("auth_type", "Playwright_Required")
        logging.info(f"جاري محاولة الاتصال بـ {router_id} عبر طريقة: {auth_type}")

        if auth_type in ["Basic", "POST_Simple"]:
            return self._connect_with_requests(router_config)
        else:
            # استخدام Playwright للأنواع المعقدة (Playwright_Required, POST_MD5, POST_SHA256)
            return self._connect_with_playwright(router_config)

    def _connect_with_requests(self, router_config):
        """
        طريقة سريعة للراوترات القديمة أو البسيطة باستخدام requests
        """
        login_url = self.base_url + router_config["login"].get("login_url", "/")
        auth_type = router_config["login"].get("auth_type")

        try:
            if auth_type == "Basic":
                self.session.auth = (self.username, self.password)
                response = self.session.get(login_url, timeout=10)
                response.raise_for_status()
                logging.info("تم الاتصال بنجاح باستخدام Requests (Basic Auth).")
                return self.session

            elif auth_type == "POST_Simple":
                payload = {"username": self.username, "password": self.password}
                response = self.session.post(login_url, data=payload, timeout=10)
                response.raise_for_status()
                
                # تحقق بسيط من نجاح الدخول (حسب الرد أو إعادة التوجيه)
                if "login" in response.url.lower() or "error" in response.text.lower():
                    raise PermissionError("فشل تسجيل الدخول، تحقق من البيانات.")
                
                logging.info("تم الاتصال بنجاح باستخدام Requests (POST_Simple).")
                return self.session

        except requests.RequestException as e:
            logging.error(f"فشل الاتصال باستخدام Requests: {str(e)}")
            raise ConnectionError(f"تعذر الاتصال بالراوتر: {str(e)}")

    def _connect_with_playwright(self, router_config):
        """
        طريقة قوية باستخدام Playwright للتعامل مع JavaScript، التشفير داخل المتصفح،
        والحقول المخفية. يتم استخراج الـ Cookies ونقلها إلى requests.Session.
        """
        login_path = router_config["login"].get("login_url", "/")
        login_url = self.base_url + login_path
        selectors = router_config.get("playwright_fallback_selectors", {})

        # استخدام محددات من ملف JSON أو قيم افتراضية ذكية
        user_selector = selectors.get("username_input") or "input[type='text'], input[id*='user'], input[id*='name']"
        pass_selector = selectors.get("password_input") or "input[type='password'], input[id*='pass'], input[id*='pwd']"
        btn_selector = selectors.get("login_button") or "button[type='submit'], input[type='submit'], button[id*='login']"
        error_selector = selectors.get("error_message")

        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=True)
            context = self.browser.new_context(ignore_https_errors=True)
            page = context.new_page()

            logging.info(f"فتح صفحة الراوتر: {login_url}")
            # مقاومة للأخطاء (Fault-Tolerant): التعامل مع بطء تحميل الصفحة
            page.goto(login_url, timeout=30000, wait_until="domcontentloaded")
            
            # ننتظر حتى تصبح الشبكة هادئة قليلاً
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightTimeoutError:
                logging.warning("تأخر هدوء الشبكة (Network Idle)، جاري الاستمرار...")

            # تعبئة حقل اسم المستخدم (إن وجد، بعض الراوترات تطلب كلمة المرور فقط)
            if user_selector:
                user_field = page.locator(user_selector).first
                if user_field.is_visible(timeout=5000):
                    user_field.fill(self.username)
                    time.sleep(0.5) # مهلة بسيطة لضمان تفعيل أحداث الـ JS (JS Events)

            # تعبئة حقل كلمة المرور
            pass_field = page.locator(pass_selector).first
            if pass_field.is_visible(timeout=5000):
                pass_field.fill(self.password)
                time.sleep(0.5)

            # الضغط على زر الدخول
            btn_field = page.locator(btn_selector).first
            if btn_field.is_visible(timeout=5000):
                logging.info("الضغط على زر تسجيل الدخول...")
                btn_field.click()
            else:
                logging.info("لم يتم العثور على زر تسجيل الدخول، محاولة الضغط على Enter...")
                pass_field.press("Enter")

            # انتظار نتيجة تسجيل الدخول (إما تحميل صفحة جديدة أو ظهور خطأ AJAX)
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except PlaywrightTimeoutError:
                pass 

            # التحقق من وجود رسالة خطأ
            if error_selector:
                err_loc = page.locator(error_selector).first
                if err_loc.is_visible(timeout=2000):
                    error_text = err_loc.inner_text().strip()
                    raise PermissionError(f"بيانات الدخول غير صحيحة: {error_text}")
            else:
                # تحقق بديل في حال عدم وجود error_selector محدد
                page_text = page.content().lower()
                if any(x in page_text for x in ["incorrect", "wrong", "invalid", "خطأ", "غير صحيح"]) and pass_field.is_visible():
                    raise PermissionError("بيانات الدخول غير صحيحة.")

            # استخراج الـ Cookies الخاصة بالجلسة
            logging.info("تم تسجيل الدخول بنجاح. جاري استخراج جلسة الاتصال (Cookies)...")
            cookies = context.cookies()
            
            # تنظيف أي Cookies قديمة في الجلسة ونقل الجديدة
            self.session.cookies.clear()
            for cookie in cookies:
                self.session.cookies.set(
                    cookie['name'], 
                    cookie['value'], 
                    domain=cookie['domain'], 
                    path=cookie['path']
                )

            logging.info(f"تم استخراج {len(cookies)} Cookies وإضافتها لمحرك الاتصال.")

            # إغلاق المتصفح الخفي لتوفير موارد الجهاز
            self._cleanup_playwright()
            
            # إرجاع كائن الـ requests.Session لتستخدمه باقي أجزاء التطبيق للطلبات السريعة
            return self.session

        except Exception as e:
            self._cleanup_playwright()
            logging.error(f"حدث خطأ أثناء الاتصال باستخدام Playwright: {str(e)}")
            raise

    def _cleanup_playwright(self):
        """تحرير موارد المتصفح"""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass
        finally:
            self.browser = None
            self.playwright = None

# ==========================================
# مثال لتجربة الكود بشكل مستقل
# ==========================================
if __name__ == "__main__":
    try:
        # مثال: محاولة الاتصال براوتر ZTE (الذي يتطلب Playwright)
        engine = HybridConnectionEngine("192.168.1.1", "admin", "admin", "routers_config.json")
        
        # استدعاء دالة الاتصال مع تمرير معرف الراوتر (Key) من ملف الـ JSON
        session = engine.connect("ZTE_ZXHN_H168N")
        
        print("====== نجاح ======")
        print("تم الحصول على جلسة اتصال نشطة (Session) يمكن استخدامها للطلبات اللاحقة بسرعة:")
        print(session.cookies.get_dict())
        
    except Exception as ex:
        print(f"فشل: {ex}")
