import re
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any


def normalize_text(value: str | None) -> str:
    """
    Normaliza texto para comparación general:
    - elimina tildes
    - pasa a mayúsculas
    - colapsa espacios
    """
    if not value:
        return ""

    normalized = unicodedata.normalize("NFD", str(value))
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    normalized = normalized.upper()
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized


def normalize_text_keep_case(value: str | None) -> str:
    """
    Normaliza texto preservando mayúsculas/minúsculas.
    """
    if not value:
        return ""

    normalized = unicodedata.normalize("NFKC", str(value))
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def only_digits(value: str | None) -> str:
    """
    Devuelve solo los dígitos de una cadena.
    """
    if not value:
        return ""
    return re.sub(r"\D", "", str(value))


def safe_strip(value: Any) -> str:
    """
    Convierte a string y aplica strip de forma segura.
    """
    if value is None:
        return ""
    return str(value).strip()


def is_empty(value: Any) -> bool:
    """
    Determina si un valor debe considerarse vacío.
    """
    return value in ("", None, [], {}, ())


def coalesce(*values: Any) -> Any:
    """
    Devuelve el primer valor no vacío/no nulo.
    """
    for value in values:
        if not is_empty(value):
            return value
    return None


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Convierte a float de forma tolerante.

    Soporta formatos como:
    - 1234.56
    - 1.234,56
    - $ 1.234,56
    """
    if value in (None, "", False):
        return default

    text = str(value).strip()
    text = text.replace("$", "").replace("ARS", "").replace("USD", "").replace(" ", "")

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(".", "").replace(",", ".")

    try:
        return float(text)
    except Exception:
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    Convierte a int de forma tolerante.
    """
    if value in (None, "", False):
        return default

    try:
        return int(float(str(value).strip()))
    except Exception:
        return default


def safe_date_to_iso(value: date | datetime | None) -> str | None:
    """
    Convierte date/datetime a ISO string.
    """
    if value is None:
        return None
    return value.isoformat()


def truncate_text(value: str | None, max_length: int = 100, suffix: str = "...") -> str:
    """
    Recorta texto largo para logs o vistas resumidas.
    """
    if not value:
        return ""

    value = str(value)
    if len(value) <= max_length:
        return value

    return value[: max_length - len(suffix)] + suffix


def ensure_list(value: Any) -> list:
    """
    Garantiza que el resultado sea lista.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def unique_preserve_order(values: list[Any]) -> list[Any]:
    """
    Elimina duplicados preservando el orden.
    """
    seen = set()
    result = []

    for value in values:
        key = str(value)
        if key not in seen:
            seen.add(key)
            result.append(value)

    return result


def path_to_str(path: str | Path | None) -> str:
    """
    Convierte Path o string a string.
    """
    if path is None:
        return ""
    return str(path)


def build_timestamp(fmt: str = "%Y%m%d_%H%M%S") -> str:
    """
    Devuelve timestamp de uso general.
    """
    return datetime.now().strftime(fmt)