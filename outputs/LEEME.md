# Publicador programado de estados de WhatsApp

Automatiza WhatsApp Web desde tu PC. Mantiene una sesion local y publica las imagenes o videos configurados a una hora determinada. No es una API oficial: WhatsApp puede cambiar su interfaz, por lo que los selectores del script pueden requerir actualizacion.

## Instalacion (una sola vez)

En PowerShell, desde esta carpeta:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
Copy-Item config_estados.ejemplo.json config_estados.json
New-Item -ItemType Directory media
```

Coloca las fotos o videos en `media` y edita `config_estados.json`. Las horas usan el reloj local de Windows en formato de 24 horas (`HH:MM`). Para publicar todo el contenido de una carpeta, usa `"carpeta": "media"`; se procesa en orden alfabético. `pausa_entre_archivos_segundos` define la espera entre publicaciones.

Para usar una carpeta diferente por dia de la semana, agrega `"dias"` a cada elemento. Puede ser un texto (`"lunes"`) o una lista (`["lunes", "viernes"]`). Consulta `config_semanal.ejemplo.json` como plantilla. Los dias validos son lunes, martes, miercoles, jueves, viernes, sabado y domingo.

## Uso

Para probar y publicar todo de inmediato:

```powershell
.\.venv\Scripts\python.exe .\whatsapp_estados.py --ahora
```

Para dejarlo esperando los horarios:

```powershell
.\.venv\Scripts\python.exe .\whatsapp_estados.py
```

En el primer inicio se abre Chromium: vincula WhatsApp Web escaneando el QR desde el teléfono. Mantén abierta esa ventana y el PC encendido mientras el planificador está activo. El historial de sesión se guarda en `.whatsapp_profile`; no lo compartas.

Para que se ejecute al iniciar sesión en Windows, crea una tarea en el Programador de tareas que lance el segundo comando anterior, con esta carpeta como directorio de inicio.

## Inicio automatico y dia de la semana

El script toma automaticamente el dia actual del reloj de Windows. Cada bloque con `dias` solo se ejecuta cuando coincide con ese dia; por ejemplo, una entrada con `"dias": "lunes"` solo publica los lunes.

Para instalar el inicio automatico, haz doble clic en `instalar_inicio_automatico.cmd`. Crea la tarea de Windows `WhatsAppEstadosAutomaticos`, que se ejecuta una vez al dia a las 08:30, espera las horas de `config_estados.json` y termina al completar el dia. El PC debe estar encendido y con tu sesion abierta; no uses `--ahora` en esa tarea.

## Notas

- Usa únicamente una cuenta propia y material para el que tengas autorización.
- Revisa `whatsapp_estados.log` si una publicación falla.
- Si WhatsApp Web cambia el diseño, el programa puede no localizar el botón de publicar; vuelve a probar con `--ahora` antes de dejarlo programado.
