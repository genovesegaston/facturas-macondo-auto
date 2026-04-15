from dataclasses import dataclass, field

from models.invoice_data import InvoiceData


# =========================
# Parámetros de negocio MVP
# =========================

DEFAULT_ROUNDING_TOLERANCE = 1.0

EXPECTED_RECEIVER_NAME = "MACONDO SRL"
EXPECTED_RECEIVER_CUIT = "30708762233"

CRITICAL_FIELDS = [
    "tipo_comprobante",
    "letra_comprobante",
    "punto_venta",
    "numero_comprobante",
    "fecha_comprobante",
    "emisor_nombre",
    "emisor_cuit",
    "receptor_nombre_detectado",
    "receptor_cuit",
    "cae",
    "fecha_vencimiento_cae",
    "subtotal",
    "iva_total",
    "total",
]

SECONDARY_FIELDS = [
    "producto_servicio",
    "moneda",
]

REVIEW_BLOCKING_FIELDS = [
    "tipo_comprobante",
    "punto_venta",
    "numero_comprobante",
    "fecha_comprobante",
    "emisor_cuit",
    "receptor_cuit",
    "cae",
    "total",
]


@dataclass
class BusinessRulesEvaluation:
    """
    Resultado de evaluación de reglas de negocio del MVP.
    """
    missing_critical_fields: list[str] = field(default_factory=list)
    missing_secondary_fields: list[str] = field(default_factory=list)

    has_blocking_missing_fields: bool = False
    requires_manual_review: bool = False
    can_be_auto_approved: bool = False

    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "missing_critical_fields": self.missing_critical_fields,
            "missing_secondary_fields": self.missing_secondary_fields,
            "has_blocking_missing_fields": self.has_blocking_missing_fields,
            "requires_manual_review": self.requires_manual_review,
            "can_be_auto_approved": self.can_be_auto_approved,
            "reasons": self.reasons,
        }


def _is_missing(value) -> bool:
    """
    Regla general de faltante.
    """
    return value in ("", None, [], False)


def get_missing_critical_fields(invoice: InvoiceData) -> list[str]:
    """
    Devuelve campos críticos faltantes.
    """
    missing = []
    for field_name in CRITICAL_FIELDS:
        value = getattr(invoice, field_name, None)

        # Para importes, 0 puede ser válido en algunos casos,
        # pero subtotal/iva_total/total no deberían faltar como dato.
        if field_name in {"subtotal", "iva_total", "total"}:
            if value is None:
                missing.append(field_name)
            continue

        if _is_missing(value):
            missing.append(field_name)

    return missing


def get_missing_secondary_fields(invoice: InvoiceData) -> list[str]:
    """
    Devuelve campos secundarios faltantes.
    """
    missing = []
    for field_name in SECONDARY_FIELDS:
        value = getattr(invoice, field_name, None)
        if _is_missing(value):
            missing.append(field_name)
    return missing


def has_blocking_missing_fields(invoice: InvoiceData) -> bool:
    """
    Determina si hay faltantes que bloquean la aprobación.
    """
    for field_name in REVIEW_BLOCKING_FIELDS:
        value = getattr(invoice, field_name, None)
        if _is_missing(value):
            return True
    return False


def requires_manual_review(invoice: InvoiceData) -> tuple[bool, list[str]]:
    """
    Determina si el documento requiere revisión manual.

    Reglas MVP:
    - faltantes bloqueantes
    - importes inválidos
    - receptor inválido
    - posible duplicado
    - confianza baja o vacía
    """
    reasons: list[str] = []

    if has_blocking_missing_fields(invoice):
        reasons.append("Tiene campos bloqueantes faltantes.")

    if not invoice.validacion_importes:
        reasons.append("Los importes no fueron validados correctamente.")

    if not invoice.receptor_valido:
        reasons.append("El receptor no fue validado correctamente.")

    if invoice.posible_duplicado:
        reasons.append("Existe un posible duplicado.")

    if invoice.confianza_extraccion in ("", "Baja"):
        reasons.append("La confianza de extracción es baja o no fue calculada.")

    return len(reasons) > 0, reasons


def can_be_auto_approved(invoice: InvoiceData) -> tuple[bool, list[str]]:
    """
    Determina si el documento puede considerarse apto para aprobación automática.

    Regla MVP:
    - sin faltantes bloqueantes
    - importes válidos
    - receptor válido
    - no duplicado
    - confianza alta o media
    """
    reasons: list[str] = []

    if has_blocking_missing_fields(invoice):
        reasons.append("Tiene campos bloqueantes faltantes.")

    if not invoice.validacion_importes:
        reasons.append("Importes inconsistentes.")

    if not invoice.receptor_valido:
        reasons.append("Receptor inválido.")

    if invoice.posible_duplicado:
        reasons.append("Posible duplicado detectado.")

    if invoice.confianza_extraccion not in ("Alta", "Media"):
        reasons.append("La confianza de extracción no es suficiente.")

    return len(reasons) == 0, reasons


def evaluate_business_rules(invoice: InvoiceData) -> BusinessRulesEvaluation:
    """
    Evalúa reglas de negocio del MVP y devuelve un resultado consolidado.
    """
    missing_critical = get_missing_critical_fields(invoice)
    missing_secondary = get_missing_secondary_fields(invoice)

    blocking = has_blocking_missing_fields(invoice)
    review_required, review_reasons = requires_manual_review(invoice)
    auto_approved, auto_reasons = can_be_auto_approved(invoice)

    reasons = []
    reasons.extend(review_reasons)

    # Evitar duplicados de texto entre review y auto_approval
    for reason in auto_reasons:
        if reason not in reasons:
            reasons.append(reason)

    return BusinessRulesEvaluation(
        missing_critical_fields=missing_critical,
        missing_secondary_fields=missing_secondary,
        has_blocking_missing_fields=blocking,
        requires_manual_review=review_required,
        can_be_auto_approved=auto_approved,
        reasons=reasons,
    )