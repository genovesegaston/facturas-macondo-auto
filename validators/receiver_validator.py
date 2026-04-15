from dataclasses import dataclass

from models.invoice_data import InvoiceData
from parsers.receiver_parser import EXPECTED_RECEIVER_NORMALIZED, normalize_receiver_text


DEFAULT_EXPECTED_RECEIVER_CUIT = "30708762233"


@dataclass
class ReceiverValidationResult:
    """
    Resultado de validación del receptor.
    """
    detected_name: str = ""
    normalized_name: str = ""
    expected_name: str = EXPECTED_RECEIVER_NORMALIZED

    detected_cuit: str = ""
    expected_cuit: str = DEFAULT_EXPECTED_RECEIVER_CUIT

    name_valid: bool = False
    cuit_valid: bool = False
    is_valid: bool = False

    error_message: str = ""

    def to_dict(self) -> dict:
        return {
            "detected_name": self.detected_name,
            "normalized_name": self.normalized_name,
            "expected_name": self.expected_name,
            "detected_cuit": self.detected_cuit,
            "expected_cuit": self.expected_cuit,
            "name_valid": self.name_valid,
            "cuit_valid": self.cuit_valid,
            "is_valid": self.is_valid,
            "error_message": self.error_message,
        }


def validate_receiver_name(
    invoice: InvoiceData,
    expected_name: str = EXPECTED_RECEIVER_NORMALIZED,
) -> bool:
    """
    Valida nombre del receptor normalizado.
    """
    detected = invoice.receptor_nombre_normalizado or normalize_receiver_text(invoice.receptor_nombre_detectado)
    expected = normalize_receiver_text(expected_name)

    if not detected:
        return False

    # Flexibilidad para variantes de Macondo
    if "MACONDO" in detected and "SRL" in detected:
        return True

    return detected == expected


def validate_receiver_cuit(
    invoice: InvoiceData,
    expected_cuit: str = DEFAULT_EXPECTED_RECEIVER_CUIT,
) -> bool:
    """
    Valida CUIT del receptor si existe.
    """
    detected = (invoice.receptor_cuit or "").strip()
    expected = (expected_cuit or "").strip()

    if not detected or not expected:
        return False

    return detected == expected


def validate_receiver(
    invoice: InvoiceData,
    expected_name: str = EXPECTED_RECEIVER_NORMALIZED,
    expected_cuit: str = DEFAULT_EXPECTED_RECEIVER_CUIT,
) -> ReceiverValidationResult:
    """
    Valida integralmente el receptor.

    Regla actual:
    - el nombre debe ser válido
    - si hay CUIT esperado, también debe coincidir
    """
    try:
        normalized_name = invoice.receptor_nombre_normalizado or normalize_receiver_text(invoice.receptor_nombre_detectado)

        name_valid = validate_receiver_name(invoice, expected_name=expected_name)
        cuit_valid = validate_receiver_cuit(invoice, expected_cuit=expected_cuit)

        # En este proyecto, el receptor correcto idealmente valida por nombre y CUIT
        is_valid = name_valid and cuit_valid

        error_parts = []
        if not name_valid:
            error_parts.append("Nombre del receptor no válido.")
        if not cuit_valid:
            error_parts.append("CUIT del receptor no válido.")

        return ReceiverValidationResult(
            detected_name=invoice.receptor_nombre_detectado,
            normalized_name=normalized_name,
            expected_name=expected_name,
            detected_cuit=invoice.receptor_cuit,
            expected_cuit=expected_cuit,
            name_valid=name_valid,
            cuit_valid=cuit_valid,
            is_valid=is_valid,
            error_message=" ".join(error_parts),
        )

    except Exception as exc:
        return ReceiverValidationResult(
            detected_name=invoice.receptor_nombre_detectado,
            normalized_name=invoice.receptor_nombre_normalizado,
            expected_name=expected_name,
            detected_cuit=invoice.receptor_cuit,
            expected_cuit=expected_cuit,
            name_valid=False,
            cuit_valid=False,
            is_valid=False,
            error_message=f"Error al validar receptor: {exc}",
        )


def enrich_invoice_with_receiver_validation(
    invoice: InvoiceData,
    expected_name: str = EXPECTED_RECEIVER_NORMALIZED,
    expected_cuit: str = DEFAULT_EXPECTED_RECEIVER_CUIT,
) -> tuple[InvoiceData, ReceiverValidationResult]:
    """
    Ejecuta validación de receptor y actualiza el InvoiceData.
    """
    result = validate_receiver(
        invoice=invoice,
        expected_name=expected_name,
        expected_cuit=expected_cuit,
    )

    invoice.receptor_valido = result.is_valid

    if not result.is_valid:
        current_note = invoice.observacion_sistema.strip()
        extra_note = result.error_message.strip()
        if extra_note:
            invoice.observacion_sistema = (
                f"{current_note} | {extra_note}".strip(" |")
                if current_note
                else extra_note
            )

    return invoice, result