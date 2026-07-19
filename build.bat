@echo off
echo Installing requirements...
pip install -r requirements.txt

echo Installing PyInstaller...
pip install pyinstaller

echo Installing Playwright browsers...
playwright install chromium

echo Building the executable...
REM --noconsole hides the console window
REM --onedir creates a folder containing the exe and its dependencies (better for Playwright)
REM --add-data includes the routers_config.json file
pyinstaller --noconfirm --onedir --windowed --add-data "routers_config.json;." --add-data "Npcap-installer.exe;." main.py

echo Build finished! Check the 'dist/main' folder for the executable.
pause
