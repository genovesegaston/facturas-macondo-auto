import re
import unicodedata
from dataclasses import dataclass


EXPECTED_RECEIVER_NORMALIZED = "MACONDO SRL"


@dataclass
class ParsedReceiverResult:
    """
    Resultado de detección y normalización del receptor.
    """
    detected_value: str = ""
    normalized_value: str = ""
    is_valid: bool = False
    success: bool = False
    error_message: str = ""

    def to_dict(self) -> dict:
        return {
            "detected_value": self.detected_value,
            "normalized_value": self.normalized_value,
            "is_valid": self.is_valid,
            "success": self.success,
            "error_message": self.error_message,
        }


def normalize_receiver_text(value: str) -> str:
    """
    Normaliza una razón social para comparación.

    Reglas:
    - elimina tildes
    - convierte a mayúsculas
    - elimina puntos
    - colapsa espacios
    """
    if not value:
        return ""

    normalized = unicodedata.normalize("NFD", value)
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    normalized = normalized.upper()
    normalized = normalized.replace(".", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized


def is_expected_receiver(value: str) -> bool:
    """
    Determina si una cadena corresponde al receptor esperado.
    """
    normalized = normalize_receiver_text(value)

    if "MACONDO" in normalized and "SRL" in normalized:
        return True

    return normalized == EXPECTED_RECEIVER_NORMALIZED


def find_receiver_candidates(text: str) -> list[str]:
    """
    Busca candidatos de receptor dentro del texto.
    """
    if not text:
        return []

    patterns = [
        r"macondo\s*s\.?\s*r\.?\s*l\.?",
        r"macondo\s+srl",
    ]

    candidates: list[str] = []
    for pattern in patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        candidates.extend(matches)

    seen = set()
    unique_candidates = []
    for candidate in candidates:
        normalized = normalize_receiver_text(candidate)
        if normalized not in seen:
            seen.add(normalized)
            unique_candidates.append(candidate)

    return unique_candidates


def parse_receiver(raw_value: str) -> ParsedReceiverResult:
    """
    Parsea y normaliza un receptor individual.
    """
    if not raw_value:
        return ParsedReceiverResult(
            detected_value="",
            normalized_value="",
            is_valid=False,
            success=False,
            error_message="Cadena vacía.",
        )

    normalized = normalize_receiver_text(raw_value)
    valid = is_expected_receiver(raw_value)

    return ParsedReceiverResult(
        detected_value=raw_value,
        normalized_value=EXPECTED_RECEIVER_NORMALIZED if valid else normalized,
        is_valid=valid,
        success=True,
        error_message="",
    )


def extract_receiver_from_text(text: str) -> ParsedReceiverResult:
    """
    Devuelve el primer receptor compatible encontrado en el texto.
    """
    candidates = find_receiver_candidates(text)

    for candidate in candidates:
        result = parse_receiver(candidate)
        if result.success:
            return result

    return ParsedReceiverResult(
        detected_value="",
        normalized_value="",
        is_valid=False,
        success=False,
        error_message="No se encontró un receptor reconocible en el texto.",
    )