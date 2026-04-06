import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedCuitResult:
    """
    Resultado de parseo de un CUIT/CUIL.
    """
    value: str = ""
    raw_value: str = ""
    success: bool = False
    is_valid_checksum: bool = False
    error_message: str = ""

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "raw_value": self.raw_value,
            "success": self.success,
            "is_valid_checksum": self.is_valid_checksum,
            "error_message": self.error_message,
        }


def normalize_cuit(raw_value: str) -> str:
    """
    Elimina caracteres no numéricos y devuelve solo dígitos.
    """
    if not raw_value:
        return ""
    return re.sub(r"\D", "", raw_value)


def is_valid_cuit(cuit: str) -> bool:
    """
    Valida CUIT/CUIL argentino usando dígito verificador.

    Debe tener 11 dígitos.
    """
    cuit = normalize_cuit(cuit)

    if len(cuit) != 11 or not cuit.isdigit():
        return False

    weights = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    digits = [int(d) for d in cuit]

    acc = sum(digits[i] * weights[i] for i in range(10))
    mod = 11 - (acc % 11)

    if mod == 11:
        verifier = 0
    elif mod == 10:
        verifier = 9
    else:
        verifier = mod

    return digits[10] == verifier


def parse_cuit(raw_value: str) -> ParsedCuitResult:
    """
    Parsea y valida un CUIT/CUIL individual.
    """
    if not raw_value:
        return ParsedCuitResult(
            value="",
            raw_value="",
            success=False,
            is_valid_checksum=False,
            error_message="Cadena vacía.",
        )

    normalized = normalize_cuit(raw_value)

    if len(normalized) != 11:
        return ParsedCuitResult(
            value=normalized,
            raw_value=raw_value,
            success=False,
            is_valid_checksum=False,
            error_message="El CUIT debe tener 11 dígitos.",
        )

    checksum_ok = is_valid_cuit(normalized)

    return ParsedCuitResult(
        value=normalized,
        raw_value=raw_value,
        success=True,
        is_valid_checksum=checksum_ok,
        error_message="" if checksum_ok else "CUIT con formato válido pero dígito verificador inválido.",
    )


def find_cuit_candidates(text: str) -> list[str]:
    """
    Busca candidatos de CUIT/CUIL en un texto.

    Soporta formatos:
    - 30-70876223-3
    - 30708762233
    """
    if not text:
        return []

    patterns = [
        r"\b\d{2}-\d{8}-\d\b",
        r"\b\d{11}\b",
    ]

    candidates: list[str] = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        candidates.extend(matches)

    seen = set()
    unique_candidates = []
    for candidate in candidates:
        normalized = normalize_cuit(candidate)
        if normalized not in seen:
            seen.add(normalized)
            unique_candidates.append(candidate)

    return unique_candidates


def extract_first_valid_cuit(text: str) -> ParsedCuitResult:
    """
    Devuelve el primer CUIT válido encontrado en el texto.
    """
    candidates = find_cuit_candidates(text)

    for candidate in candidates:
        result = parse_cuit(candidate)
        if result.success and result.is_valid_checksum:
            return result

    return ParsedCuitResult(
        value="",
        raw_value="",
        success=False,
        is_valid_checksum=False,
        error_message="No se encontró ningún CUIT válido en el texto.",
    )


def extract_all_valid_cuits(text: str) -> list[ParsedCuitResult]:
    """
    Devuelve todos los CUIT válidos encontrados en el texto.
    """
    results: list[ParsedCuitResult] = []

    for candidate in find_cuit_candidates(text):
        parsed = parse_cuit(candidate)
        if parsed.success and parsed.is_valid_checksum:
            results.append(parsed)

    return results