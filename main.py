import sys
from PyQt6.QtWidgets import QApplication
from bootstrapper import BootstrapperWindow

def launch_main_app():
    # Lazy import to avoid Scapy crashing on missing Npcap during bootstrap
    from app_ui import MainWindow
    global main_window
    main_window = MainWindow()
    main_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # تنسيق عصري ومريح للعين للواجهة (Modern UI / Dark Theme style)
    app.setStyleSheet('''
        QWidget {
            font-size: 15px;
            font-family: "Segoe UI", Arial, sans-serif;
            background-color: #f1f5f9;
            color: #1e293b;
        }
        QMainWindow {
            background-color: #f8fafc;
        }
        QPushButton {
            background-color: #2563eb;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #1d4ed8;
        }
        QPushButton:disabled {
            background-color: #94a3b8;
        }
        QLineEdit, QComboBox {
            padding: 10px;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            background-color: white;
        }
        QLineEdit:focus, QComboBox:focus {
            border: 1px solid #2563eb;
        }
        QListWidget {
            border: none;
            border-left: 1px solid #e2e8f0;
            background-color: #ffffff;
            padding: 10px;
        }
        QListWidget::item {
            padding: 15px 10px;
            border-radius: 8px;
            margin-bottom: 5px;
            color: #475569;
        }
        QListWidget::item:hover {
            background-color: #f1f5f9;
        }
        QListWidget::item:selected {
            background-color: #e0e7ff;
            color: #1d4ed8;
            font-weight: bold;
        }
        QGroupBox {
            font-weight: bold;
            font-size: 16px;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            margin-top: 15px;
            padding-top: 20px;
            background-color: #ffffff;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 5px;
            color: #0f172a;
        }
        QTableWidget {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
        }
        QHeaderView::section {
            background-color: #f8fafc;
            padding: 8px;
            border: none;
            border-bottom: 1px solid #e2e8f0;
            font-weight: bold;
            color: #475569;
        }
    ''')
    
    bootstrapper = BootstrapperWindow()
    bootstrapper.boot_successful.connect(launch_main_app)
    bootstrapper.show()
    
    sys.exit(app.exec())
