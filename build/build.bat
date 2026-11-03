@echo off
REM Run on Windows, inside the project's virtualenv, to produce the .exe.
pip install -r ..\requirements.txt
pyinstaller build.spec
echo Done. Find SalliBaba.exe in dist\SalliBaba\
