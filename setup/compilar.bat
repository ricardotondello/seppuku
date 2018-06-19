
rem remove os arquivos temporarios
del /s /q D:\dsv\GIT\Seppuku\setup\__pycache__\*
del /s /q D:\dsv\GIT\Seppuku\setup\build\*
del /s /q D:\dsv\GIT\Seppuku\setup\dist\*
del /s /q D:\dsv\GIT\Seppuku\setup\seppuku.spec


rem gera o executavel do python
pyinstaller --onefile ..\seppuku.py


rem compila o instalador
"C:\Program Files (x86)\Inno Setup 5\Compil32.exe" /cc .\setup.iss
rem compil32 /cc "D:\dsv\GIT\Seppuku\Python\setup\setup.iss"

