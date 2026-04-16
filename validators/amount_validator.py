from dataclasses import dataclass

from core.config import ROUNDING_TOLERANCE
from models.invoice_data import InvoiceData


DEFAULT_ROUNDING_TOLERANCE = ROUNDING_TOLERANCE


@dataclass
class AmountValidationResult:
    """
    Resultado de validación numérica de importes.
    """
    expected_total: float = 0.0
    detected_total: float = 0.0
    difference: float = 0.0
    is_valid: bool = False
    tolerance_used: float = DEFAULT_ROUNDING_TOLERANCE
    error_message: str = ""

    def to_dict(self) -> dict:
        return {
            "expected_total": self.expected_total,
            "detected_total": self.detected_total,
            "difference": self.difference,
            "is_valid": self.is_valid,
            "tolerance_used": self.tolerance_used,
            "error_message": self.error_message,
        }


def calculate_expected_total(invoice: InvoiceData) -> float:
    """
    Calcula el total esperado según la lógica del negocio:

    total esperado = subtotal + iva_total + percepciones
    """
    return round(
        float(invoice.subtotal)
        + float(invoice.iva_total)
        + float(invoice.percepciones),
        2,
    )


def calculate_rounding_difference(invoice: InvoiceData) -> float:
    """
    Calcula la diferencia absoluta entre el total esperado y el total detectado.
    """
    expected_total = calculate_expected_total(invoice)
    detected_total = round(float(invoice.total), 2)
    return round(abs(expected_total - detected_total), 2)


def validate_amounts(
    invoice: InvoiceData,
    tolerance: float = DEFAULT_ROUNDING_TOLERANCE,
) -> AmountValidationResult:
    """
    Valida consistencia de importes con tolerancia de redondeo.

    Reglas:
    - total esperado = subtotal + iva_total + percepciones
    - si la diferencia absoluta es <= tolerance, se considera válido
    """
    try:
        expected_total = calculate_expected_total(invoice)
        detected_total = round(float(invoice.total), 2)
        difference = round(abs(expected_total - detected_total), 2)
        is_valid = difference <= tolerance

        return AmountValidationResult(
            expected_total=expected_total,
            detected_total=detected_total,
            difference=difference,
            is_valid=is_valid,
            tolerance_used=tolerance,
            error_message="" if is_valid else "La diferencia excede la tolerancia permitida.",
        )

    except Exception as exc:
        return AmountValidationResult(
            expected_total=0.0,
            detected_total=0.0,
            difference=0.0,
            is_valid=False,
            tolerance_used=tolerance,
            error_message=f"Error al validar importes: {exc}",
        )


def enrich_invoice_with_amount_validation(
    invoice: InvoiceData,
    tolerance: float = DEFAULT_ROUNDING_TOLERANCE,
) -> tuple[InvoiceData, AmountValidationResult]:
    """
    Ejecuta validación de importes y actualiza el InvoiceData.
    """
    result = validate_amounts(invoice, tolerance=tolerance)

    invoice.validacion_importes = result.is_valid
    invoice.diferencia_redondeo = result.difference

    return invoice, result