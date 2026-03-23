@echo off
echo Limpiando builds anteriores...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo Construyendo el ejecutable...
pyinstaller --noconfirm --onefile --windowed --add-data "C:\Users\ARuiz\AppData\Local\Programs\Python\Python313\Lib\site-packages\customtkinter;customtkinter/" "generador_contratos.py"

echo.
echo Movimiendo el ejecutable a la carpeta principal...
move /y "dist\generador_contratos.exe" "generador_contratos.exe"

echo Limpiando carpetas temporales de compilación...
rmdir /s /q "build"
rmdir /s /q "dist"
del /f /q "generador_contratos.spec"

echo.
echo Proceso finalizado. El ejecutable 'generador_contratos.exe' ya está listo en la carpeta principal.
pause
