import re
from dataclasses import dataclass

from parsers.field_patterns import AMOUNT_LABEL_PATTERNS


@dataclass
class ParsedAmountResult:
    value: float
    raw_value: str = ""
    success: bool = False
    error_message: str = ""

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "raw_value": self.raw_value,
            "success": self.success,
            "error_message": self.error_message,
        }


@dataclass
class ParsedAmountsBundle:
    subtotal: float = 0.0
    iva_21: float = 0.0
    iva_10_5: float = 0.0
    iva_27: float = 0.0
    iva_5: float = 0.0
    iva_2_5: float = 0.0
    iva_otros: float = 0.0
    iva_total: float = 0.0
    percepciones: float = 0.0
    total: float = 0.0

    def recalculate_iva_total(self) -> float:
        self.iva_total = (
            self.iva_21
            + self.iva_10_5
            + self.iva_27
            + self.iva_5
            + self.iva_2_5
            + self.iva_otros
        )
        return self.iva_total

    def to_dict(self) -> dict:
        return {
            "subtotal": self.subtotal,
            "iva_21": self.iva_21,
            "iva_10_5": self.iva_10_5,
            "iva_27": self.iva_27,
            "iva_5": self.iva_5,
            "iva_2_5": self.iva_2_5,
            "iva_otros": self.iva_otros,
            "iva_total": self.iva_total,
            "percepciones": self.percepciones,
            "total": self.total,
        }


def normalize_amount_string(raw_value: str) -> str:
    if not raw_value:
        return ""

    value = raw_value.strip()
    value = value.replace("$", "").replace("ARS", "").replace("USD", "")
    value = value.replace(" ", "")

    if "," in value and "." in value:
        if value.rfind(",") > value.rfind("."):
            value = value.replace(".", "").replace(",", ".")
        else:
            value = value.replace(",", "")
    elif "," in value:
        value = value.replace(".", "").replace(",", ".")

    return value.strip()


def parse_amount(raw_value: str) -> ParsedAmountResult:
    if not raw_value:
        return ParsedAmountResult(value=0.0, raw_value="", success=False, error_message="Cadena vacía.")

    try:
        normalized = normalize_amount_string(raw_value)
        value = float(normalized)
        return ParsedAmountResult(value=value, raw_value=raw_value, success=True, error_message="")
    except Exception as exc:
        return ParsedAmountResult(
            value=0.0,
            raw_value=raw_value,
            success=False,
            error_message=f"No se pudo parsear importe: {exc}",
        )


def find_amount_by_label(text: str, label_pattern: str) -> ParsedAmountResult:
    if not text:
        return ParsedAmountResult(value=0.0, raw_value="", success=False, error_message="Texto vacío.")

    pattern = rf"{label_pattern}[^\d]{{0,25}}\$?\s*([\d\.,]+)"
    match = re.search(pattern, text, re.IGNORECASE)

    if not match:
        return ParsedAmountResult(
            value=0.0,
            raw_value="",
            success=False,
            error_message="No se encontró importe para la etiqueta.",
        )

    return parse_amount(match.group(1))


def find_amount_by_any_label(text: str, label_patterns: list[str]) -> ParsedAmountResult:
    for label in label_patterns:
        result = find_amount_by_label(text, label)
        if result.success:
            return result
    return ParsedAmountResult(
        value=0.0,
        raw_value="",
        success=False,
        error_message="No se encontró importe para ninguna etiqueta.",
    )


def extract_invoice_amounts(text: str) -> ParsedAmountsBundle:
    amounts = ParsedAmountsBundle()

    subtotal_result = find_amount_by_any_label(text, AMOUNT_LABEL_PATTERNS["subtotal"])
    iva_21_result = find_amount_by_any_label(text, AMOUNT_LABEL_PATTERNS["iva_21"])
    iva_10_5_result = find_amount_by_any_label(text, AMOUNT_LABEL_PATTERNS["iva_10_5"])
    iva_27_result = find_amount_by_any_label(text, AMOUNT_LABEL_PATTERNS["iva_27"])
    iva_5_result = find_amount_by_any_label(text, AMOUNT_LABEL_PATTERNS["iva_5"])
    iva_2_5_result = find_amount_by_any_label(text, AMOUNT_LABEL_PATTERNS["iva_2_5"])
    percepciones_result = find_amount_by_any_label(text, AMOUNT_LABEL_PATTERNS["percepciones"])
    total_result = find_amount_by_any_label(text, AMOUNT_LABEL_PATTERNS["total"])

    amounts.subtotal = subtotal_result.value if subtotal_result.success else 0.0
    amounts.iva_21 = iva_21_result.value if iva_21_result.success else 0.0
    amounts.iva_10_5 = iva_10_5_result.value if iva_10_5_result.success else 0.0
    amounts.iva_27 = iva_27_result.value if iva_27_result.success else 0.0
    amounts.iva_5 = iva_5_result.value if iva_5_result.success else 0.0
    amounts.iva_2_5 = iva_2_5_result.value if iva_2_5_result.success else 0.0
    amounts.percepciones = percepciones_result.value if percepciones_result.success else 0.0
    amounts.total = total_result.value if total_result.success else 0.0

    amounts.recalculate_iva_total()
    return amounts