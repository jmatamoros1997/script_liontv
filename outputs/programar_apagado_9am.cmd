@echo off
setlocal
set "TASK_NAME=ApagadoDiario9AM"

REM Programa un apagado diario a las 09:00, con un aviso de 60 segundos.
schtasks.exe /Create /TN "%TASK_NAME%" /TR "shutdown.exe /s /f /t 60 /c \"Apagado programado en 60 segundos\"" /SC DAILY /ST 09:00 /RL HIGHEST /F
if errorlevel 1 (
  echo No se pudo crear la tarea. Ejecuta este archivo como administrador.
  pause
  exit /b 1
)

echo.
echo Listo. El equipo se apagara todos los dias a las 9:00 a. m.
echo Para cancelar un apagado que ya inicio: shutdown.exe /a
pause
