"""
Consulta vehiculo en RUNT con Playwright + OCR CRNN/CTC.
Basado en Modelo/Extraer_info_sufi 5.py
"""

from __future__ import annotations

import logging
import os
import random
import re
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

import cv2
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

from .ocr.inference import predict_captcha
from .runt_messages import CAPTCHA_RESPONSES
from . import runt_xpaths as xp

log = logging.getLogger(__name__)

RUNT_URL = "https://www.runt.gov.co/consultaCiudadana/#/consultaVehiculo"
MAX_RETRIES = int(os.getenv("CAPTCHA_MAX_RETRIES", "5"))

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/115.0.1901.203 Safari/537.36",
]

VEHICLE_FIELDS = [
    "Placa",
    "Marca",
    "Modelo",
    "Chasis",
    "Cilindraje",
    "Tipo Combustible",
    "Linea",
    "Color",
    "Motor",
    "VIN",
    "Fecha Matricula",
    "Autoridad",
    "identificacion Acreedor Garantia",
    "Acreedor Garantia",
    "Fecha de Inicio Garantia",
    "Patrimonio Autonomo Garantia",
    "Confecámaras Garantia",
]


@dataclass
class PlateResult:
    placa: str
    documento_id: str | int
    cod_id: int
    success: bool
    data: dict = field(default_factory=dict)
    error: str | None = None
    elapsed_seconds: float | None = None


def _random_wait(lo: float = 2.0, hi: float = 4.0) -> None:
    time.sleep(random.uniform(lo, hi))


def _normalize_doc_id(cod_id: int, doc_id: str | int) -> str:
    doc = str(doc_id)
    if cod_id == 2 and len(doc) > 6:
        doc = re.sub(r"^30*", "", doc)
    return doc


def _launch_browser(playwright):
    edge_path = os.getenv("EDGE_EXECUTABLE_PATH")
    kwargs = {"headless": os.getenv("HEADLESS", "true").lower() != "false"}
    if edge_path and Path(edge_path).exists():
        return playwright.chromium.launch(executable_path=edge_path, **kwargs)
    return playwright.chromium.launch(**kwargs)


def _extract_attribute(page, xpath: str, name: str, values: list[str]) -> bool:
    for attempt in range(2):
        try:
            loc = page.locator(f"xpath={xpath}")
            loc.wait_for(state="visible", timeout=30000)
            loc.scroll_into_view_if_needed()
            values.append(loc.inner_text().strip())
            return True
        except PlaywrightTimeout:
            log.warning("Atributo '%s' no visible (intento %s)", name, attempt + 1)
            time.sleep(1)
        except Exception as exc:
            log.warning("Error extrayendo '%s': %s", name, exc)
            break
    return False


def _extract_garantia(page, values: list[str]) -> None:
    header_xpath = (
        "/html/body/host-runt-root/app-layout/app-theme-runt2/mat-sidenav-container/"
        "mat-sidenav-content/div/ng-component/div/div/div[2]/div[16]/"
        "cyrconsultavehiculo-garantias/mat-accordion/mat-expansion-panel/"
        "mat-expansion-panel-header"
    )
    try:
        page.locator(f"xpath={header_xpath}").scroll_into_view_if_needed()
        time.sleep(1)
        page.click(f"xpath={header_xpath}")
        time.sleep(1)
        tabla = page.get_by_role("region", name="Garantías a Favor De").get_by_role("table")
        tabla.wait_for(state="visible", timeout=10000)
        filas = tabla.locator(".mat-row").all()
        if not filas:
            values.extend([""] * 5)
            return
        celdas = filas[0].locator(".mat-cell").all()
        values.extend(c.inner_text().strip() for c in celdas)
    except PlaywrightTimeout:
        values.extend([""] * 5)


def _parse_vehicle_data(raw: list[str]) -> dict:
    padded = (raw + [""] * len(VEHICLE_FIELDS))[: len(VEHICLE_FIELDS)]
    return dict(zip(VEHICLE_FIELDS, padded))


def _clean_modal_text(text: str) -> str:
    for token in ("Resultado Consulta", "Aceptar", "×", "\n"):
        text = text.replace(token, "")
    return text.strip()


def scrape_plate(cod_id: int, documento_id: str | int, placa: str) -> PlateResult:
    """Consulta una placa en RUNT. Reintenta si el captcha falla."""
    placa = str(placa).strip().upper()
    doc = _normalize_doc_id(int(cod_id), documento_id)
    last_error: str | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        log.info("RUNT placa=%s doc=%s intento=%s/%s", placa, doc, attempt, MAX_RETRIES)
        try:
            result = _scrape_once(int(cod_id), doc, placa)
            if result.success or not result.error or "Captcha" not in (result.error or ""):
                return result
            last_error = result.error
        except PlaywrightTimeout:
            last_error = "Timeout al cargar la pagina RUNT"
            log.error(last_error)
        except Exception as exc:
            last_error = str(exc)
            log.exception("Error en scraping placa %s", placa)
            if "ERR_CONNECTION_TIMED_OUT" in str(exc):
                time.sleep(int(os.getenv("CONNECTION_TIMEOUT_WAIT", "60")))

    return PlateResult(
        placa=placa,
        documento_id=doc,
        cod_id=int(cod_id),
        success=False,
        error=last_error or "Maximo de reintentos de captcha",
    )


def _scrape_once(cod_id: int, doc: str, placa: str) -> PlateResult:
    start = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        captcha_path = Path(tmp) / "captcha.png"
        with sync_playwright() as p:
            browser = _launch_browser(p)
            context = browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
            )
            page = context.new_page()
            try:
                page.goto(RUNT_URL, timeout=60000)
                _random_wait(4, 8)

                page.fill('xpath=//*[@id="mat-input-0"]', placa)
                _random_wait()
                page.click("id=mat-select-4")
                page.wait_for_selector("mat-option", timeout=20000)
                options = page.locator("mat-option").all()
                idx = {1: 1, 2: 2, 3: 3}.get(cod_id, 1)
                if idx < len(options):
                    options[idx].click()

                page.fill('xpath=//*[@id="mat-input-1"]', doc)
                _random_wait()

                page.wait_for_selector("//img[contains(@src,'base64')]", state="visible", timeout=120000)
                captcha_el = page.locator("//img[contains(@src,'base64')]")
                captcha_el.scroll_into_view_if_needed()
                captcha_el.screenshot(path=str(captcha_path))

                img = cv2.imread(str(captcha_path), cv2.IMREAD_GRAYSCALE)
                text_captcha = predict_captcha(img)
                log.info("Captcha predicho: %s", text_captcha)

                page.fill('xpath=//*[@id="mat-input-2"]', text_captcha)
                page.keyboard.press("Enter")

                try:
                    modal = page.wait_for_selector(
                        "#swal2-html-container", state="visible", timeout=4000
                    )
                    msg = _clean_modal_text(modal.inner_text())
                    if msg in CAPTCHA_RESPONSES:
                        caso = CAPTCHA_RESPONSES[msg]
                        if caso.get("retry"):
                            return PlateResult(
                                placa=placa,
                                documento_id=doc,
                                cod_id=cod_id,
                                success=False,
                                error=caso["message"],
                            )
                        return PlateResult(
                            placa=placa,
                            documento_id=doc,
                            cod_id=cod_id,
                            success=False,
                            data={"runt_message": msg},
                            error=caso["message"],
                            elapsed_seconds=time.time() - start,
                        )
                except PlaywrightTimeout:
                    pass

                raw: list[str] = []
                attrs = [
                    ("placa", xp.PLACA_XPATH),
                    ("marca", xp.MARCA_XPATH),
                    ("modelo", xp.MODELO_XPATH),
                    ("chasis", xp.CHASIS_XPATH),
                    ("cilindraje", xp.CILINDRAJE_XPATH),
                    ("tipo_combustible", xp.TIPO_COMBUSTIBLE_XPATH),
                    ("linea", xp.LINEA_XPATH),
                    ("color", xp.COLOR_XPATH),
                    ("motor", xp.MOTOR_XPATH),
                    ("vin", xp.VIN_XPATH),
                    ("fecha_matricula", xp.FECHA_MATRICULA_XPATH),
                    ("autoridad", xp.AUTORIDAD_XPATH),
                ]
                extraction_failed = False
                for name, xpath in attrs:
                    if not _extract_attribute(page, xpath, name, raw):
                        extraction_failed = True

                _extract_garantia(page, raw)
                data = _parse_vehicle_data(raw)

                if extraction_failed:
                    return PlateResult(
                        placa=placa,
                        documento_id=doc,
                        cod_id=cod_id,
                        success=False,
                        data=data,
                        error="No se pudieron extraer todos los atributos",
                        elapsed_seconds=time.time() - start,
                    )

                return PlateResult(
                    placa=placa,
                    documento_id=doc,
                    cod_id=cod_id,
                    success=True,
                    data=data,
                    elapsed_seconds=time.time() - start,
                )
            finally:
                try:
                    page.close()
                    context.close()
                    browser.close()
                except Exception:
                    pass
