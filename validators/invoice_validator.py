from collections.abc import Iterable

from models.invoice_data import InvoiceData
from models.validation_result import ValidationResult
from validators.amount_validator import enrich_invoice_with_amount_validation
from validators.business_rules import (
    DEFAULT_ROUNDING_TOLERANCE,
    EXPECTED_RECEIVER_CUIT,
    EXPECTED_RECEIVER_NAME,
    evaluate_business_rules,
)
from validators.confidence_calculator import enrich_invoice_with_confidence
from validators.duplicate_validator import enrich_invoice_with_duplicate_validation
from validators.receiver_validator import enrich_invoice_with_receiver_validation


def build_validation_result(
    invoice: InvoiceData,
    business_eval,
    amount_result,
    receiver_result,
    duplicate_result,
    confidence_result,
) -> ValidationResult:
    """
    Consolida los resultados de validación en un ValidationResult.
    """
    result = ValidationResult()

    # Faltantes
    for field_name in business_eval.missing_critical_fields:
        result.add_missing_field(field_name)

    # Validaciones base
    result.receiver_valid = receiver_result.is_valid
    result.amounts_valid = amount_result.is_valid
    result.rounding_difference = amount_result.difference

    # Duplicados
    result.duplicate_detected = duplicate_result.duplicate_detected
    result.duplicate_reference = duplicate_result.duplicate_reference
    result.duplicate_key = duplicate_result.duplicate_key

    # Confianza
    result.confidence_level = confidence_result.confidence_level

    # Warnings y errors
    if business_eval.missing_secondary_fields:
        result.add_warning(
            "Campos secundarios faltantes: "
            + ", ".join(business_eval.missing_secondary_fields)
        )

    for reason in business_eval.reasons:
        # Reglas prácticas:
        # - faltantes bloqueantes, receptor inválido o importes inválidos => error
        # - duplicado o confianza baja/media => warning/revisión
        reason_lower = reason.lower()

        if (
            "bloqueantes" in reason_lower
            or "importes" in reason_lower
            or "receptor" in reason_lower
        ):
            result.add_error(reason)
        else:
            result.add_warning(reason)

    if duplicate_result.duplicate_detected:
        result.add_warning(
            f"Posible duplicado detectado: {duplicate_result.duplicate_reference or duplicate_result.duplicate_key}"
        )

    if confidence_result.confidence_level == "Baja":
        result.add_warning("Confianza de extracción baja.")

    result.build_system_notes()
    result.evaluate_validity()

    return result


def validate_invoice(
    invoice: InvoiceData,
    existing_keys: Iterable[str] | None = None,
    existing_records: Iterable[dict] | None = None,
    rounding_tolerance: float = DEFAULT_ROUNDING_TOLERANCE,
    expected_receiver_name: str = EXPECTED_RECEIVER_NAME,
    expected_receiver_cuit: str = EXPECTED_RECEIVER_CUIT,
) -> tuple[InvoiceData, ValidationResult]:
    """
    Ejecuta validación integral de una factura/nota ya parseada.

    Orden:
    1. Importes
    2. Receptor
    3. Duplicados
    4. Confianza
    5. Reglas de negocio
    6. Consolidación final en ValidationResult
    """
    # 1. Importes
    invoice, amount_result = enrich_invoice_with_amount_validation(
        invoice=invoice,
        tolerance=rounding_tolerance,
    )

    # 2. Receptor
    invoice, receiver_result = enrich_invoice_with_receiver_validation(
        invoice=invoice,
        expected_name=expected_receiver_name,
        expected_cuit=expected_receiver_cuit,
    )

    # 3. Duplicados
    invoice, duplicate_result = enrich_invoice_with_duplicate_validation(
        invoice=invoice,
        existing_keys=existing_keys,
        existing_records=existing_records,
    )

    # 4. Confianza (usa estado actual del invoice)
    invoice, confidence_result = enrich_invoice_with_confidence(invoice)

    # 5. Reglas de negocio
    business_eval = evaluate_business_rules(invoice)

    # 6. Consolidación final
    validation_result = build_validation_result(
        invoice=invoice,
        business_eval=business_eval,
        amount_result=amount_result,
        receiver_result=receiver_result,
        duplicate_result=duplicate_result,
        confidence_result=confidence_result,
    )

    # Reflejar observaciones consolidadas en invoice
    if validation_result.system_notes:
        current_note = invoice.observacion_sistema.strip()
        invoice.observacion_sistema = (
            f"{current_note} | {validation_result.system_notes}".strip(" |")
            if current_note
            else validation_result.system_notes
        )

    return invoice, validation_result