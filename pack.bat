echo delete cache
del /f /s /q dist\*
echo start make
pyinstaller main.py --hidden-import PySide2.QtXml -F --hidden-import openpyxl
echo start copy
copy client.ui dist\
copy run.bat dist\