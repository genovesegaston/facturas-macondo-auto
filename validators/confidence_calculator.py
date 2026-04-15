from dataclasses import dataclass, field

from models.invoice_data import InvoiceData


CONFIDENCE_HIGH = "Alta"
CONFIDENCE_MEDIUM = "Media"
CONFIDENCE_LOW = "Baja"


@dataclass
class ConfidenceResult:
    """
    Resultado del cálculo de confianza de extracción.
    """
    confidence_level: str = CONFIDENCE_LOW
    score: float = 0.0
    factors: list[str] = field(default_factory=list)
    error_message: str = ""

    def to_dict(self) -> dict:
        return {
            "confidence_level": self.confidence_level,
            "score": self.score,
            "factors": self.factors,
            "error_message": self.error_message,
        }


def calculate_confidence_score(invoice: InvoiceData) -> ConfidenceResult:
    """
    Calcula score de confianza a partir de completitud y consistencia.

    Regla inicial de puntaje:
    - base 0
    - se suman puntos por campos críticos detectados
    - se restan puntos por faltantes y observaciones críticas
    - el score final se acota entre 0 y 100
    """
    try:
        score = 0.0
        factors: list[str] = []

        # Campos críticos
        critical_fields = {
            "tipo_comprobante": invoice.tipo_comprobante,
            "letra_comprobante": invoice.letra_comprobante,
            "punto_venta": invoice.punto_venta,
            "numero_comprobante": invoice.numero_comprobante,
            "fecha_comprobante": invoice.fecha_comprobante,
            "emisor_nombre": invoice.emisor_nombre,
            "emisor_cuit": invoice.emisor_cuit,
            "receptor_nombre_detectado": invoice.receptor_nombre_detectado,
            "receptor_cuit": invoice.receptor_cuit,
            "cae": invoice.cae,
            "fecha_vencimiento_cae": invoice.fecha_vencimiento_cae,
            "subtotal": invoice.subtotal,
            "iva_total": invoice.iva_total,
            "total": invoice.total,
        }

        for field_name, value in critical_fields.items():
            if value not in ("", None, 0, 0.0, False, []):
                score += 6
                factors.append(f"Campo crítico detectado: {field_name}")

        # Campos importantes no críticos
        optional_fields = {
            "producto_servicio": invoice.producto_servicio,
            "moneda": invoice.moneda,
        }

        for field_name, value in optional_fields.items():
            if value not in ("", None, False, []):
                score += 2
                factors.append(f"Campo complementario detectado: {field_name}")

        # Validaciones positivas
        if invoice.texto_extraido_ok:
            score += 8
            factors.append("Texto extraído correctamente")

        if invoice.receptor_valido:
            score += 8
            factors.append("Receptor validado")

        if invoice.validacion_importes:
            score += 10
            factors.append("Importes consistentes")

        # Penalizaciones
        if invoice.campos_faltantes:
            penalty = min(len(invoice.campos_faltantes) * 5, 30)
            score -= penalty
            factors.append(f"Penalización por campos faltantes: -{penalty}")

        if invoice.posible_duplicado:
            score -= 15
            factors.append("Penalización por posible duplicado: -15")

        if invoice.diferencia_redondeo > 1:
            score -= 10
            factors.append("Penalización por diferencia de redondeo significativa: -10")

        if invoice.observacion_sistema:
            score -= 5
            factors.append("Penalización por observaciones del sistema: -5")

        # Acotar score
        score = max(0.0, min(round(score, 2), 100.0))

        # Mapear score a nivel
        if score >= 80:
            confidence_level = CONFIDENCE_HIGH
        elif score >= 50:
            confidence_level = CONFIDENCE_MEDIUM
        else:
            confidence_level = CONFIDENCE_LOW

        return ConfidenceResult(
            confidence_level=confidence_level,
            score=score,
            factors=factors,
            error_message="",
        )

    except Exception as exc:
        return ConfidenceResult(
            confidence_level=CONFIDENCE_LOW,
            score=0.0,
            factors=[],
            error_message=f"Error al calcular confianza: {exc}",
        )


def enrich_invoice_with_confidence(invoice: InvoiceData) -> tuple[InvoiceData, ConfidenceResult]:
    """
    Calcula confianza y actualiza InvoiceData.
    """
    result = calculate_confidence_score(invoice)
    invoice.confianza_extraccion = result.confidence_level
    return invoice, result