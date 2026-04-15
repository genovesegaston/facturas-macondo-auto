from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from models.invoice_data import InvoiceData
from models.processing_log import ProcessingLog
from models.validation_result import ValidationResult


REVIEWABLE_FIELDS = [
    "tipo_comprobante",
    "letra_comprobante",
    "punto_venta",
    "numero_comprobante",
    "fecha_comprobante",
    "emisor_nombre",
    "emisor_cuit",
    "receptor_nombre_detectado",
    "receptor_nombre_normalizado",
    "receptor_cuit",
    "receptor_valido",
    "cae",
    "fecha_vencimiento_cae",
    "moneda",
    "subtotal",
    "iva_21",
    "iva_10_5",
    "iva_27",
    "iva_5",
    "iva_2_5",
    "iva_otros",
    "iva_total",
    "percepciones",
    "total",
    "producto_servicio",
    "confianza_extraccion",
    "observacion_sistema",
    "observacion_usuario",
]


@dataclass
class ReviewItem:
    """
    Representa un documento listo para revisión humana.
    """
    document_id: str
    file_name: str
    review_required: bool
    review_reasons: list[str] = field(default_factory=list)
    invoice_data: dict = field(default_factory=dict)
    validation_data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "file_name": self.file_name,
            "review_required": self.review_required,
            "review_reasons": self.review_reasons,
            "invoice_data": self.invoice_data,
            "validation_data": self.validation_data,
        }


@dataclass
class ReviewChange:
    """
    Representa un cambio manual aplicado sobre un campo.
    """
    field_name: str
    old_value: Any
    new_value: Any
    changed_at: datetime
    changed_by: str = ""

    def to_dict(self) -> dict:
        return {
            "field_name": self.field_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "changed_at": self.changed_at.isoformat(),
            "changed_by": self.changed_by,
        }


def needs_manual_review(invoice: InvoiceData, validation: ValidationResult) -> tuple[bool, list[str]]:
    """
    Determina si un documento requiere revisión manual.
    """
    reasons: list[str] = []

    if not validation.is_valid:
        reasons.append("La validación integral no fue satisfactoria.")

    if validation.missing_fields:
        reasons.append("Existen campos faltantes.")

    if validation.duplicate_detected:
        reasons.append("Se detectó posible duplicado.")

    if validation.confidence_level == "Baja":
        reasons.append("La confianza de extracción es baja.")

    if invoice.observacion_sistema:
        reasons.append("Existen observaciones del sistema.")

    return len(reasons) > 0, reasons


def build_review_item(invoice: InvoiceData, validation: ValidationResult) -> ReviewItem:
    """
    Construye un ítem de revisión a partir de InvoiceData + ValidationResult.
    """
    review_required, review_reasons = needs_manual_review(invoice, validation)

    return ReviewItem(
        document_id=invoice.document_id,
        file_name=invoice.file_name,
        review_required=review_required,
        review_reasons=review_reasons,
        invoice_data=invoice.to_dict(),
        validation_data=validation.to_dict(),
    )


def build_review_items(
    invoices: list[InvoiceData],
    validations: list[ValidationResult],
) -> list[ReviewItem]:
    """
    Construye una lista de ítems de revisión.
    """
    items: list[ReviewItem] = []

    for invoice, validation in zip(invoices, validations):
        items.append(build_review_item(invoice, validation))

    return items


def apply_manual_changes(
    invoice: InvoiceData,
    changes: dict[str, Any],
    changed_by: str = "",
) -> tuple[InvoiceData, list[ReviewChange]]:
    """
    Aplica cambios manuales permitidos sobre InvoiceData.
    """
    applied_changes: list[ReviewChange] = []

    for field_name, new_value in changes.items():
        if field_name not in REVIEWABLE_FIELDS:
            continue

        if not hasattr(invoice, field_name):
            continue

        old_value = getattr(invoice, field_name)

        if old_value != new_value:
            setattr(invoice, field_name, new_value)

            applied_changes.append(
                ReviewChange(
                    field_name=field_name,
                    old_value=old_value,
                    new_value=new_value,
                    changed_at=datetime.now(),
                    changed_by=changed_by,
                )
            )

    return invoice, applied_changes


def append_review_note(invoice: InvoiceData, note: str) -> InvoiceData:
    """
    Agrega una observación manual del usuario.
    """
    note = (note or "").strip()
    if not note:
        return invoice

    current = (invoice.observacion_usuario or "").strip()

    if current:
        invoice.observacion_usuario = f"{current} | {note}"
    else:
        invoice.observacion_usuario = note

    return invoice


def build_review_logs(
    invoice: InvoiceData,
    changes: list[ReviewChange],
) -> list[ProcessingLog]:
    """
    Genera logs estructurados de revisión manual.
    """
    logs: list[ProcessingLog] = []

    for change in changes:
        logs.append(
            ProcessingLog(
                timestamp=change.changed_at,
                level="INFO",
                event_type="MANUAL_REVIEW_CHANGE",
                file_name=invoice.file_name,
                document_id=invoice.document_id,
                message=f"Cambio manual en campo '{change.field_name}'.",
                details=change.to_dict(),
                user=change.changed_by,
            )
        )

    return logs