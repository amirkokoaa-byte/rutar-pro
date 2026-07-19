[Setup]
; =======================================================
; Router Admin V1.0 - Inno Setup Configuration Script
; Developed by Amir Lamay
; =======================================================

; معلومات التطبيق الأساسية
AppName=Router Admin
AppVersion=1.0
AppPublisher=Amir Lamay
AppPublisherURL=https://github.com/AmirLamay
AppCopyright=Copyright (C) 2026 Developed by Amir Lamay

; مسار التثبيت الافتراضي (في مجلد Program Files)
DefaultDirName={autopf}\Router Admin
; اسم مجلد اختصارات قائمة ابدأ
DefaultGroupName=Router Admin

; مسار واسم ملف المثبت النهائي (Setup File)
OutputDir=Output
OutputBaseFilename=RouterAdmin_v1.0_Setup

; الأيقونة الخاصة ببرنامج التثبيت (تأكد من توفير ملف icon.ico وإزالة الفاصلة المنقوطة لتفعيله)
; SetupIconFile=icon.ico

; ضغط عالٍ لتقليل حجم ملف التثبيت وتجميع كافة المتطلبات
Compression=lzma2/ultra64
SolidCompression=yes

; يحتاج التطبيق إلى صلاحيات المدير (Admin) لتمكين تثبيت Npcap لاحقاً أو تعديل جدار الحماية
PrivilegesRequired=admin

[Languages]
; دعم اللغات لواجهة التثبيت (اللغة الإنجليزية بشكل افتراضي مع توفر قوالب معرّبة)
Name: "english"; MessagesFile: "compiler:Default.isl"
; Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"

[Tasks]
; خيار لإنشاء اختصار على سطح المكتب
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; -----------------------------------------------------------------------------------------
; تضمين مجلد التطبيق المجمع بالكامل (الذي تم إنشاؤه عبر PyInstaller --onedir)
; تأكد أن مجلد dist/main موجود بجوار هذا السكريبت عند عمل Compile.
; -----------------------------------------------------------------------------------------
Source: "dist\main\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; تضمين ملف Npcap Installer (إذا أردت تثبيته يدوياً أو تركه للتطبيق ليتعامل معه)
Source: "Npcap-installer.exe"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
; إنشاء اختصار التطبيق في قائمة ابدأ (Start Menu)
Name: "{group}\Router Admin"; Filename: "{app}\main.exe"
; إنشاء اختصار لإلغاء التثبيت في قائمة ابدأ
Name: "{group}\{cm:UninstallProgram,Router Admin}"; Filename: "{uninstallexe}"
; إنشاء اختصار على سطح المكتب إذا اختار المستخدم تفعيل الخيار
Name: "{autodesktop}\Router Admin"; Filename: "{app}\main.exe"; Tasks: desktopicon

[Run]
; عرض خيار لتشغيل التطبيق بمجرد انتهاء التثبيت
Filename: "{app}\main.exe"; Description: "{cm:LaunchProgram,Router Admin}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; حذف الملفات المؤقتة التي قد ينشئها التطبيق أثناء العمل ولم تكن جزءاً من التثبيت
Type: filesandordirs; Name: "{app}\__pycache__"
Type: files; Name: "{app}\bandwidth.db"
Type: filesandordirs; Name: "{app}\playwright_browsers"
