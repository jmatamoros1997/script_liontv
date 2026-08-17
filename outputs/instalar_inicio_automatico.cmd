@echo off
setlocal
set "BASE=%~dp0"
set "PYTHON=%BASE%.venv\Scripts\python.exe"
set "SCRIPT=%BASE%whatsapp_estados.py"
set "TASK_NAME=WhatsAppEstadosAutomaticos"
set "TASK_TIME=08:30"

if not exist "%PYTHON%" (
  echo No se encontro el entorno virtual: "%PYTHON%"
  echo Ejecuta primero la instalacion indicada en LEEME.md.
  pause
  exit /b 1
)

schtasks.exe /Create /TN "%TASK_NAME%" /TR "\"%PYTHON%\" \"%SCRIPT%\" --diario" /SC DAILY /ST %TASK_TIME% /RL LIMITED /IT /F
if errorlevel 1 (
  echo No se pudo crear la tarea programada.
  pause
  exit /b 1
)

echo.
echo Listo. Windows iniciara el publicador una vez al dia a las %TASK_TIME%.
echo El publicador termina despues de completar la programacion de ese dia.
pause
