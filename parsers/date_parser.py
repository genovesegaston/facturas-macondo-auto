import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class ParsedDateResult:
    """
    Resultado de parseo de una fecha detectada en texto.
    """
    value: Optional[date]
    raw_value: str = ""
    detected_format: str = ""
    success: bool = False
    error_message: str = ""

    def to_dict(self) -> dict:
        return {
            "value": self.value.isoformat() if self.value else None,
            "raw_value": self.raw_value,
            "detected_format": self.detected_format,
            "success": self.success,
            "error_message": self.error_message,
        }


SPANISH_MONTHS = {
    "ENERO": 1,
    "FEBRERO": 2,
    "MARZO": 3,
    "ABRIL": 4,
    "MAYO": 5,
    "JUNIO": 6,
    "JULIO": 7,
    "AGOSTO": 8,
    "SEPTIEMBRE": 9,
    "SETIEMBRE": 9,
    "OCTUBRE": 10,
    "NOVIEMBRE": 11,
    "DICIEMBRE": 12,
}


def normalize_text_for_date_search(text: str) -> str:
    """
    Normaliza texto para búsqueda de fechas:
    - preserva números y separadores
    - elimina tildes
    - pasa a mayúsculas
    """
    if not text:
        return ""

    normalized = unicodedata.normalize("NFD", text)
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return normalized.upper()


def build_date(year: int, month: int, day: int, raw_value: str, detected_format: str) -> ParsedDateResult:
    """
    Construye un objeto date validando que la fecha exista.
    """
    try:
        parsed = date(year, month, day)
        return ParsedDateResult(
            value=parsed,
            raw_value=raw_value,
            detected_format=detected_format,
            success=True,
            error_message="",
        )
    except ValueError as exc:
        return ParsedDateResult(
            value=None,
            raw_value=raw_value,
            detected_format=detected_format,
            success=False,
            error_message=f"Fecha inválida: {exc}",
        )


def parse_dd_mm_yyyy(raw_value: str) -> ParsedDateResult:
    """
    Parsea fechas tipo DD/MM/YYYY.
    """
    try:
        dd, mm, yyyy = raw_value.split("/")
        return build_date(
            year=int(yyyy),
            month=int(mm),
            day=int(dd),
            raw_value=raw_value,
            detected_format="DD/MM/YYYY",
        )
    except Exception as exc:
        return ParsedDateResult(
            value=None,
            raw_value=raw_value,
            detected_format="DD/MM/YYYY",
            success=False,
            error_message=f"No se pudo parsear fecha DD/MM/YYYY: {exc}",
        )


def parse_dd_mm_yyyy_dash(raw_value: str) -> ParsedDateResult:
    """
    Parsea fechas tipo DD-MM-YYYY.
    """
    try:
        dd, mm, yyyy = raw_value.split("-")
        return build_date(
            year=int(yyyy),
            month=int(mm),
            day=int(dd),
            raw_value=raw_value,
            detected_format="DD-MM-YYYY",
        )
    except Exception as exc:
        return ParsedDateResult(
            value=None,
            raw_value=raw_value,
            detected_format="DD-MM-YYYY",
            success=False,
            error_message=f"No se pudo parsear fecha DD-MM-YYYY: {exc}",
        )


def parse_dd_mmmm_yyyy(raw_value: str) -> ParsedDateResult:
    """
    Parsea fechas tipo DD-MMMM-YYYY en español.
    Ejemplo: 05-MARZO-2026
    """
    try:
        dd, month_name, yyyy = raw_value.split("-")
        month_name = normalize_text_for_date_search(month_name).strip()
        month = SPANISH_MONTHS.get(month_name)

        if not month:
            return ParsedDateResult(
                value=None,
                raw_value=raw_value,
                detected_format="DD-MMMM-YYYY",
                success=False,
                error_message=f"Mes no reconocido: {month_name}",
            )

        return build_date(
            year=int(yyyy),
            month=month,
            day=int(dd),
            raw_value=raw_value,
            detected_format="DD-MMMM-YYYY",
        )
    except Exception as exc:
        return ParsedDateResult(
            value=None,
            raw_value=raw_value,
            detected_format="DD-MMMM-YYYY",
            success=False,
            error_message=f"No se pudo parsear fecha DD-MMMM-YYYY: {exc}",
        )


def parse_date_string(raw_value: str) -> ParsedDateResult:
    """
    Intenta parsear una fecha individual según los formatos admitidos.
    """
    if not raw_value:
        return ParsedDateResult(
            value=None,
            raw_value="",
            detected_format="",
            success=False,
            error_message="Cadena vacía.",
        )

    raw_value = raw_value.strip()

    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", raw_value):
        return parse_dd_mm_yyyy(raw_value)

    if re.fullmatch(r"\d{2}-\d{2}-\d{4}", raw_value):
        return parse_dd_mm_yyyy_dash(raw_value)

    if re.fullmatch(r"\d{2}-[A-Za-zÁÉÍÓÚáéíóúñÑ]+-\d{4}", raw_value):
        return parse_dd_mmmm_yyyy(raw_value)

    return ParsedDateResult(
        value=None,
        raw_value=raw_value,
        detected_format="",
        success=False,
        error_message="Formato de fecha no soportado.",
    )


def find_date_candidates(text: str) -> list[str]:
    """
    Busca candidatos de fecha dentro de un texto según formatos admitidos.
    """
    if not text:
        return []

    patterns = [
        r"\b\d{2}/\d{2}/\d{4}\b",
        r"\b\d{2}-\d{2}-\d{4}\b",
        r"\b\d{2}-[A-Za-zÁÉÍÓÚáéíóúñÑ]+-\d{4}\b",
    ]

    candidates: list[str] = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        candidates.extend(matches)

    # Mantener orden y evitar duplicados
    seen = set()
    unique_candidates = []
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            unique_candidates.append(candidate)

    return unique_candidates


def extract_first_valid_date(text: str) -> ParsedDateResult:
    """
    Devuelve la primera fecha válida encontrada en el texto.
    """
    candidates = find_date_candidates(text)

    for candidate in candidates:
        result = parse_date_string(candidate)
        if result.success:
            return result

    return ParsedDateResult(
        value=None,
        raw_value="",
        detected_format="",
        success=False,
        error_message="No se encontró ninguna fecha válida en el texto.",
    )