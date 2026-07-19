# الدليل الشامل لتشفير وتوزيع تطبيق Router Admin

مرحباً بك في المرحلة النهائية. لقد قمنا بتطوير نظام متكامل ومعقد، والآن حان وقت حمايته وتوزيعه باحترافية.

---

## أولاً: حماية الكود المصدري (Source Code Obfuscation)

لحماية الكود من الهندسة العكسية (Reverse Engineering)، يمكنك الاختيار بين طريقتين احترافيتين:

### الخيار 1: استخدام PyArmor (الأسهل والأكثر مرونة)
تقوم أداة PyArmor بتشفير ملفات البايثون وتحويلها إلى أسطر برمجية مبهمة تماماً، مع إمكانية ربط تشغيل البرنامج بترخيص (License) أو فترة زمنية محددة أو حتى Hardware ID محدد.

**الخطوات:**
1. افتح موجه الأوامر (CMD) وثبت الأداة:
   ```cmd
   pip install pyarmor
   ```
2. لتشفير كافة ملفات المشروع في المجلد الحالي، نفّذ الأمر التالي:
   ```cmd
   pyarmor gen -O dist_obfuscated/ main.py app_ui.py router_manager.py hybrid_connection_engine.py router_actions_executor.py bandwidth_daemon.py security_manager.py bootstrapper.py
   ```
3. سينتج مجلد جديد اسمه `dist_obfuscated` يحتوي على ملفات البايثون المشفرة.
4. قم بنسخ ملفات JSON والإعدادات مثل `routers_config.json` و `Npcap-installer.exe` إلى هذا المجلد.
5. استبدل أمر `PyInstaller` في ملف `build.bat` ليعمل على الملفات المشفرة، على سبيل المثال:
   ```cmd
   pyinstaller --noconfirm --onedir --windowed --add-data "routers_config.json;." --add-data "Npcap-installer.exe;." dist_obfuscated/main.py
   ```

### الخيار 2: استخدام Cython (الحماية القصوى عبر تحويل الكود إلى C)
يقوم Cython بترجمة ملفات البايثون (`.py`) إلى كود لغة C، ثم تجميعه إلى مكتبات ديناميكية ثنائية (`.pyd` في ويندوز). هذه الطريقة تجعل فك الهندسة العكسية شبه مستحيل وتزيد من سرعة أداء البرنامج.

**الخطوات:**
1. تثبيت Cython وأدوات الترجمة:
   ```cmd
   pip install cython
   ```
   *(ملاحظة: تتطلب هذه العملية وجود مُجمّع C/C++ في نظام ويندوز، مثل Visual Studio Build Tools).*
2. قم بإنشاء ملف `setup.py` لإعداد الترجمة:
   ```python
   from setuptools import setup
   from Cython.Build import cythonize

   setup(
       ext_modules = cythonize([
           "app_ui.py", 
           "router_manager.py", 
           "hybrid_connection_engine.py", 
           "router_actions_executor.py", 
           "bandwidth_daemon.py", 
           "security_manager.py"
       ])
   )
   ```
3. نفّذ الأمر التالي لترجمة الملفات:
   ```cmd
   python setup.py build_ext --inplace
   ```
4. ستحصل على ملفات بامتداد `.pyd` أو `.so`. احتفظ بملف `main.py` و `bootstrapper.py` كما هم ليعملوا كنقطة دخول للتطبيق، واستخدم PyInstaller مع هذه الملفات المترجمة (`.pyd`).

---

## ثانياً: بناء واجهة التثبيت باستخدام Inno Setup

لكي يظهر التطبيق بشكل احترافي مثل برامج الشركات الكبرى (نافذة التثبيت الأنيقة، اتفاقية الاستخدام، وتحديد مسار التثبيت)، نستخدم الأداة الرائعة **Inno Setup**.

**كيفية استخدام سكريبت Inno Setup المرفق:**
1. أولاً، تأكد من أنك قمت ببناء التطبيق التنفيذي النهائي باستخدام `PyInstaller` (من خلال تشغيل ملف `build.bat`، والذي سينتج مجلداً في المسار `dist/main/`).
2. قم بتحميل وتثبيت برنامج [Inno Setup](https://jrsoftware.org/isinfo.php).
3. قم بإنشاء ملف باسم `router_admin_setup.iss` بجوار مجلد `dist` (قمت بإنشائه لك فعلياً في ملفات المشروع).
4. انقر نقراً مزدوجاً على ملف `router_admin_setup.iss` لفتحه داخل برنامج Inno Setup.
5. من الشريط العلوي في البرنامج، اضغط على زر **Compile (تجميع)** أو اختصار `Ctrl+F9`.
6. سيقوم البرنامج بضغط كل الملفات المجمعة لإنتاج ملف تثبيت نهائي واحد `RouterAdmin_v1.0_Setup.exe` داخل مجلد `Output`. هذا هو الملف الذي ستقوم بتوزيعه للعملاء أو المستخدمين.
