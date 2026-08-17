#!/usr/bin/env python3
"""Publica estados programados desde WhatsApp Web.

El programa conserva la sesion en .whatsapp_profile. La primera vez abre una
ventana para escanear el codigo QR. No envia mensajes ni accede a contactos.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from datetime import date, datetime, time as clock_time
from pathlib import Path

from playwright.sync_api import BrowserContext, Page, TimeoutError as PlaywrightTimeoutError, sync_playwright
"""
Configuraciòn de carpetas de dias
"""
ROOT = Path(__file__).resolve().parent
CONFIG_FILE = ROOT / "config_estados.json"
PROFILE_DIR = ROOT / ".whatsapp_profile"
LOG_FILE = ROOT / "whatsapp_estados.log"
MEDIA_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".webm"}
WEEKDAYS = {
    "lunes": 0,
    "martes": 1,
    "miercoles": 2,
    "miércoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sabado": 5,
    "sábado": 5,
    "domingo": 6,
}


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"No existe {CONFIG_FILE.name}. Copia y edita el archivo de ejemplo.")
    data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    if not isinstance(data.get("estados"), list) or not data["estados"]:
        raise ValueError("config_estados.json debe contener una lista no vacia en 'estados'.")
    return data


def wait_for_whatsapp(page: Page) -> None:
    page.goto("https://web.whatsapp.com/", wait_until="domcontentloaded")
    print("Si aparece un codigo QR, escanealo desde WhatsApp en tu telefono.")
    # La interfaz cambia con frecuencia; el area principal aparece tras iniciar sesion.
    page.locator("#app").wait_for(state="visible", timeout=120_000)
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        if page.locator("[aria-label='Status'], [aria-label='Estados'], [title='Status'], [title='Estados']").count():
            return
        time.sleep(1)
    raise TimeoutError("No se detecto la sesion de WhatsApp Web en 3 minutos.")


def first_visible(page: Page, selector: str):
    locator = page.locator(selector)
    for index in range(locator.count()):
        item = locator.nth(index)
        if item.is_visible():
            return item
    return None


def click_first(page: Page, selector: str) -> bool:
    item = first_visible(page, selector)
    if not item:
        return False
    item.click()
    return True


def click_icon_button(page: Page, icon: str) -> bool:
    """Pulsa el ancestro clicable de un icono SVG de WhatsApp."""
    icon_locator = page.locator(f"[data-icon='{icon}']")
    for index in range(icon_locator.count()):
        candidate = icon_locator.nth(index)
        if candidate.is_visible():
            button = candidate.locator("xpath=ancestor-or-self::*[@role='button' or self::button][1]")
            if button.count():
                button.click()
                return True
    return False


def click_editor_send_button(page: Page) -> bool:
    """Encuentra el boton circular verde de envio por su ubicacion en el editor.

    Algunas compilaciones de WhatsApp no asignan aria-label ni data-icon a este
    boton. En el editor siempre es el control clicable mas a la derecha y abajo.
    """
    viewport = page.viewport_size or {"width": 1280, "height": 800}
    best = None
    best_score = -1.0
    for selector in ("button", "[role='button']"):
        controls = page.locator(selector)
        for index in range(controls.count()):
            control = controls.nth(index)
            if not control.is_visible():
                continue
            box = control.bounding_box()
            if not box:
                continue
            center_x = box["x"] + box["width"] / 2
            center_y = box["y"] + box["height"] / 2
            if center_x < viewport["width"] * 0.85 or center_y < viewport["height"] * 0.80:
                continue
            score = center_x + center_y
            if score > best_score:
                best, best_score = control, score
    if best:
        best.click()
        return True
    return False


def publish_status(page: Page, filename: Path, caption: str = "") -> None:
    if not filename.is_file():
        raise FileNotFoundError(f"No se encontro el archivo: {filename}")

    logging.info("Abriendo Estados para publicar %s", filename.name)
    status = first_visible(page, "[aria-label='Status'], [aria-label='Estados'], [title='Status'], [title='Estados']")
    if status:
        status.click()
        page.wait_for_timeout(800)
    else:
        # WhatsApp ha renombrado Estados como Novedades/Updates en algunas cuentas.
        click_icon_button(page, "status-v3") or click_icon_button(page, "status")
        page.wait_for_timeout(800)

    # En versiones recientes el area de Estados abre primero "Mi estado";
    # el input para elegir archivo solo se inserta despues de pulsar este boton.
    click_first(
        page,
        "[aria-label='Add status'], [aria-label='Añadir estado'], "
        "[title='Add status'], [title='Añadir estado'], "
        "[aria-label='My status'], [aria-label='Mi estado']",
    )
    page.wait_for_timeout(500)

    # Algunas versiones muestran despues un menu que exige seleccionar Foto y video.
    media_option = click_first(
        page,
        "[aria-label='Photo & video'], [aria-label='Foto y video'], "
        "[aria-label='Foto y vídeo'], [title='Photo & video'], "
        "[title='Foto y video'], [title='Foto y vídeo']",
    )
    if not media_option:
        # En la interfaz en espanol este control solo tiene texto visible,
        # sin aria-label ni title.
        option = page.get_by_text("Foto y video", exact=True)
        if not option.count():
            option = page.get_by_text("Foto y vídeo", exact=True)
        if option.count() and option.first.is_visible():
            option.first.click()
            media_option = True
    if not media_option:
        click_icon_button(page, "media-upload")
    page.wait_for_timeout(500)

    uploads = page.locator("input[type='file']")
    try:
        uploads.last.wait_for(state="attached", timeout=10_000)
        uploads.last.set_input_files(str(filename))
    except PlaywrightTimeoutError as exc:
        # Deja evidencia local para adaptar el script si WhatsApp cambia nuevamente.
        debug_image = ROOT / "error_whatsapp_web.png"
        page.screenshot(path=str(debug_image), full_page=True)
        raise RuntimeError(
            "No aparecio el control para elegir el archivo. Abre manualmente Estados "
            f"y verifica que tu cuenta permite crear un estado. Se guardo {debug_image.name}."
        ) from exc
    page.wait_for_timeout(1500)

    if caption:
        caption_box = first_visible(page, "[contenteditable='true'][role='textbox'], [contenteditable='true']")
        if caption_box:
            caption_box.fill(caption)

    send = first_visible(page, "[aria-label='Send'], [aria-label='Enviar'], button[aria-label='Send'], button[aria-label='Enviar']")
    if send:
        send.click()
    elif not click_icon_button(page, "send") and not click_editor_send_button(page):
        debug_image = ROOT / "error_boton_enviar.png"
        page.screenshot(path=str(debug_image), full_page=True)
        raise RuntimeError(
            "No encontre el boton Enviar. WhatsApp Web pudo haber cambiado su interfaz. "
            f"Se guardo {debug_image.name}."
        )
    page.wait_for_timeout(15000)
    logging.info("Estado publicado: %s", filename.name)


def due_datetime(item: dict, today: date) -> datetime:
    try:
        scheduled = clock_time.fromisoformat(item["hora"])
    except (KeyError, ValueError) as exc:
        raise ValueError("Cada estado debe incluir 'hora' en formato HH:MM, por ejemplo 09:30.") from exc
    return datetime.combine(today, scheduled)


def scheduled_on(item: dict, today: date) -> bool:
    """Indica si el elemento esta programado para el dia dado."""
    days = item.get("dias")
    if days is None:
        return True
    if isinstance(days, str):
        days = [days]
    if not isinstance(days, list):
        raise ValueError("'dias' debe ser un dia o una lista de dias, por ejemplo ['lunes', 'viernes'].")
    try:
        return today.weekday() in {WEEKDAYS[str(day).strip().lower()] for day in days}
    except KeyError as exc:
        valid = ", ".join(WEEKDAYS)
        raise ValueError(f"Dia no valido: {exc.args[0]}. Usa: {valid}.") from exc


def media_for_item(item: dict) -> list[Path]:
    """Obtiene un archivo concreto o todos los medios de una carpeta."""
    if item.get("archivo"):
        return [(ROOT / str(item["archivo"])).resolve()]
    if item.get("carpeta"):
        folder = (ROOT / str(item["carpeta"])).resolve()
        if not folder.is_dir():
            raise FileNotFoundError(f"No se encontro la carpeta: {folder}")
        media = sorted(
            (file for file in folder.iterdir() if file.is_file() and file.suffix.lower() in MEDIA_EXTENSIONS),
            key=lambda file: file.name.lower(),
        )
        if not media:
            raise ValueError(f"No hay imagenes o videos compatibles en: {folder}")
        return media
    raise ValueError("Cada estado debe incluir 'archivo' o 'carpeta'.")


def publish_item(page: Page, item: dict) -> None:
    files = media_for_item(item)
    pause = float(item.get("pausa_entre_archivos_segundos", 15))
    for index, media in enumerate(files):
        publish_status(page, media, str(item.get("texto", "")))
        if index < len(files) - 1:
            time.sleep(pause)


def run_once(page: Page, config: dict) -> None:
    for item in config["estados"]:
        publish_item(page, item)


def run_scheduler(page: Page, config: dict, exit_after_today: bool = False) -> None:
    completed: set[tuple[date, int]] = set()
    print("Planificador activo. Pulsa Ctrl+C para detenerlo.")
    while True:
        now = datetime.now()
        for index, item in enumerate(config["estados"]):
            key = (now.date(), index)
            if scheduled_on(item, now.date()) and key not in completed and now >= due_datetime(item, now.date()):
                try:
                    publish_item(page, item)
                    completed.add(key)
                except Exception:
                    logging.exception("No fue posible publicar el estado %s", index + 1)
        if exit_after_today:
            pending_today = any(
                scheduled_on(item, now.date()) and (now.date(), index) not in completed
                for index, item in enumerate(config["estados"])
            )
            if not pending_today:
                print("Programacion del dia terminada.")
                return
        # Evita que la memoria crezca si el programa se deja activo varios dias.
        completed = {key for key in completed if key[0] == now.date()}
        time.sleep(15)


def main() -> int:
    logging.basicConfig(filename=LOG_FILE, encoding="utf-8", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    try:
        config = load_config()
        with sync_playwright() as playwright:
            context: BrowserContext = playwright.chromium.launch_persistent_context(
                str(PROFILE_DIR), headless=False, viewport={"width": 1280, "height": 800}
            )
            page = context.pages[0] if context.pages else context.new_page()
            wait_for_whatsapp(page)
            if "--ahora" in sys.argv:
                run_once(page, config)
            else:
                run_scheduler(page, config, exit_after_today="--diario" in sys.argv)
            context.close()
    except KeyboardInterrupt:
        print("\nPlanificador detenido.")
    except (OSError, ValueError, PlaywrightTimeoutError, RuntimeError) as exc:
        logging.exception("Error")
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
