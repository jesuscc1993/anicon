@echo off
pyinstaller -F -i ./anicon.ico --version-file ./version.txt ./anicon.py ^
  --exclude-module matplotlib ^
  --exclude-module numpy ^
  --exclude-module pandas ^
  --exclude-module scipy ^
  --exclude-module tkinter ^
  --exclude-module unittest
