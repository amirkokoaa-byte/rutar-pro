import subprocess
import base64
import hashlib
from cryptography.fernet import Fernet
import platform
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SecurityManager:
    """
    فئة مسؤولة عن التشفير وفك التشفير (Ai Lam3y Security Standard).
    تستخدم الـ Hardware ID لتوليد مفتاح تشفير فريد لكل جهاز،
    مما يمنع نقل قاعدة البيانات وقراءتها على أجهزة أخرى.
    """
    def __init__(self):
        self.key = self._generate_hardware_key()
        self.cipher_suite = Fernet(self.key)

    def _get_hardware_id(self):
        """
        يستخرج المعرف الفريد للجهاز (Hardware ID).
        يدعم أنظمة Windows و Linux/Mac.
        """
        system = platform.system()
        try:
            if system == "Windows":
                # استخدام wmic لاستخراج الـ UUID الخاص باللوحة الأم في ويندوز
                command = "wmic csproduct get uuid"
                # إخفاء النافذة السوداء في ويندوز
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                result = subprocess.check_output(command, shell=True, text=True, startupinfo=startupinfo)
                hw_id = result.split('\n')[1].strip()
                if hw_id:
                    return hw_id
            elif system == "Linux":
                # قراءة الـ machine-id في أنظمة لينكس
                with open("/etc/machine-id", "r") as f:
                    return f.read().strip()
            elif system == "Darwin":
                # استخراج الـ UUID في نظام الماك
                command = "ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID"
                result = subprocess.check_output(command, shell=True, text=True)
                hw_id = result.split('"')[3]
                if hw_id:
                    return hw_id
        except Exception as e:
            logging.warning(f"تعذر استخراج الـ Hardware ID بالطرق الأساسية: {str(e)}")
        
        # كطريقة بديلة (Fallback) إذا فشلت الطرق السابقة، نستخدم الـ MAC Address
        import uuid
        logging.info("استخدام MAC Address كبديل للـ Hardware ID")
        return str(uuid.getnode())

    def _generate_hardware_key(self):
        """
        يولد مفتاح تشفير Fernet (32 bytes url-safe base64-encoded) 
        بناءً على الـ Hardware ID الخاص بالجهاز.
        """
        hw_id = self._get_hardware_id()
        
        # نستخدم SHA256 لضمان طول ثابت ثم نشفره بـ Base64 ليتوافق مع متطلبات Fernet
        hasher = hashlib.sha256()
        hasher.update(hw_id.encode('utf-8'))
        
        # Fernet يتطلب مفتاحاً بصيغة 32 بايت (urlsafe_b64encode)
        return base64.urlsafe_b64encode(hasher.digest())

    def encrypt_password(self, plain_password):
        """تشفير كلمة المرور"""
        if not plain_password:
            return ""
        encrypted_bytes = self.cipher_suite.encrypt(plain_password.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')

    def decrypt_password(self, encrypted_password):
        """فك تشفير كلمة المرور"""
        if not encrypted_password:
            return ""
        try:
            decrypted_bytes = self.cipher_suite.decrypt(encrypted_password.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception:
            # قد يحدث خطأ إذا تم نقل الملف لجهاز آخر ذو Hardware ID مختلف
            logging.error("فشل فك التشفير. قد يكون الملف مرتبطاً بجهاز آخر (Hardware ID Mismatch).")
            raise ValueError("فشل فك التشفير. لا يمكن قراءة كلمات المرور على جهاز مختلف.")

# ==========================================
# مثال للتجربة بشكل مستقل
# ==========================================
if __name__ == "__main__":
    try:
        security = SecurityManager()
        print("تم توليد مفتاح التشفير المرتبط بالهاردوير بنجاح.")
        
        original_password = "SuperSecretRouterPassword123!"
        print(f"الكلمة الأصلية: {original_password}")
        
        encrypted = security.encrypt_password(original_password)
        print(f"الكلمة المشفرة: {encrypted}")
        
        decrypted = security.decrypt_password(encrypted)
        print(f"الكلمة بعد فك التشفير: {decrypted}")
        
        assert original_password == decrypted
        print("التشفير وفك التشفير يعملان بكفاءة!")
    except Exception as ex:
        print(f"حدث خطأ: {ex}")
