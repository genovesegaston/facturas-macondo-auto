from dataclasses import dataclass
from typing import Iterable

from models.invoice_data import InvoiceData


@dataclass
class DuplicateValidationResult:
    """
    Resultado de validación de duplicado.
    """
    duplicate_key: str = ""
    duplicate_detected: bool = False
    duplicate_reference: str = ""
    error_message: str = ""

    def to_dict(self) -> dict:
        return {
            "duplicate_key": self.duplicate_key,
            "duplicate_detected": self.duplicate_detected,
            "duplicate_reference": self.duplicate_reference,
            "error_message": self.error_message,
        }


def build_duplicate_key(invoice: InvoiceData) -> str:
    """
    Construye la clave de duplicado definida para el negocio:

    punto_venta + numero_comprobante + cae
    """
    punto_venta = (invoice.punto_venta or "").strip()
    numero = (invoice.numero_comprobante or "").strip()
    cae = (invoice.cae or "").strip()

    return f"{punto_venta}-{numero}-{cae}"


def is_duplicate_key_complete(invoice: InvoiceData) -> bool:
    """
    Verifica si la clave de duplicado tiene todos los componentes necesarios.
    """
    return bool(
        (invoice.punto_venta or "").strip()
        and (invoice.numero_comprobante or "").strip()
        and (invoice.cae or "").strip()
    )


def validate_duplicate_against_keys(
    invoice: InvoiceData,
    existing_keys: Iterable[str],
) -> DuplicateValidationResult:
    """
    Valida duplicado contra una colección simple de claves existentes.
    """
    try:
        duplicate_key = build_duplicate_key(invoice)

        if not is_duplicate_key_complete(invoice):
            return DuplicateValidationResult(
                duplicate_key=duplicate_key,
                duplicate_detected=False,
                duplicate_reference="",
                error_message="No se puede validar duplicado: faltan componentes de la clave.",
            )

        existing_keys_set = {str(key).strip() for key in existing_keys if str(key).strip()}
        detected = duplicate_key in existing_keys_set

        return DuplicateValidationResult(
            duplicate_key=duplicate_key,
            duplicate_detected=detected,
            duplicate_reference=duplicate_key if detected else "",
            error_message="",
        )

    except Exception as exc:
        return DuplicateValidationResult(
            duplicate_key="",
            duplicate_detected=False,
            duplicate_reference="",
            error_message=f"Error al validar duplicado: {exc}",
        )


def validate_duplicate_against_records(
    invoice: InvoiceData,
    existing_records: Iterable[dict],
    key_field: str = "clave_duplicado",
    reference_field: str = "document_id",
) -> DuplicateValidationResult:
    """
    Valida duplicado contra una colección de registros tipo dict.

    Cada registro puede venir, por ejemplo, de:
    - Excel
    - Google Sheets
    - cache local
    - JSON
    """
    try:
        duplicate_key = build_duplicate_key(invoice)

        if not is_duplicate_key_complete(invoice):
            return DuplicateValidationResult(
                duplicate_key=duplicate_key,
                duplicate_detected=False,
                duplicate_reference="",
                error_message="No se puede validar duplicado: faltan componentes de la clave.",
            )

        for record in existing_records:
            record_key = str(record.get(key_field, "")).strip()
            if record_key == duplicate_key:
                reference = str(record.get(reference_field, "")).strip() or duplicate_key
                return DuplicateValidationResult(
                    duplicate_key=duplicate_key,
                    duplicate_detected=True,
                    duplicate_reference=reference,
                    error_message="",
                )

        return DuplicateValidationResult(
            duplicate_key=duplicate_key,
            duplicate_detected=False,
            duplicate_reference="",
            error_message="",
        )

    except Exception as exc:
        return DuplicateValidationResult(
            duplicate_key="",
            duplicate_detected=False,
            duplicate_reference="",
            error_message=f"Error al validar duplicado contra registros: {exc}",
        )


def enrich_invoice_with_duplicate_validation(
    invoice: InvoiceData,
    existing_keys: Iterable[str] | None = None,
    existing_records: Iterable[dict] | None = None,
    key_field: str = "clave_duplicado",
    reference_field: str = "document_id",
) -> tuple[InvoiceData, DuplicateValidationResult]:
    """
    Ejecuta validación de duplicado y actualiza el InvoiceData.

    Prioridad:
    1. existing_records
    2. existing_keys
    """
    if existing_records is not None:
        result = validate_duplicate_against_records(
            invoice=invoice,
            existing_records=existing_records,
            key_field=key_field,
            reference_field=reference_field,
        )
    else:
        result = validate_duplicate_against_keys(
            invoice=invoice,
            existing_keys=existing_keys or [],
        )

    invoice.clave_duplicado = result.duplicate_key
    invoice.posible_duplicado = result.duplicate_detected
    invoice.fila_duplicada_referencia = result.duplicate_reference

    if result.duplicate_detected:
        current_note = invoice.observacion_sistema.strip()
        extra_note = f"Posible duplicado detectado: {result.duplicate_reference}"
        invoice.observacion_sistema = (
            f"{current_note} | {extra_note}".strip(" |")
            if current_note
            else extra_note
        )

    return invoice, result