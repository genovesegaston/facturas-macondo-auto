from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Optional


@dataclass
class InvoiceData:
    document_id: str = ""
    file_name: str = ""

    tipo_comprobante: str = ""
    letra_comprobante: str = ""
    punto_venta: str = ""
    numero_comprobante: str = ""

    fecha_comprobante: Optional[date] = None
    formato_fecha_detectado: str = ""

    emisor_nombre: str = ""
    emisor_cuit: str = ""

    receptor_nombre_detectado: str = ""
    receptor_nombre_normalizado: str = ""
    receptor_cuit: str = ""
    receptor_valido: bool = False

    cae: str = ""
    fecha_vencimiento_cae: Optional[date] = None

    moneda: str = "ARS"

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

    producto_servicio: str = ""

    texto_extraido_ok: bool = False
    campos_faltantes: list[str] = field(default_factory=list)

    validacion_importes: bool = False
    diferencia_redondeo: float = 0.0

    posible_duplicado: bool = False
    clave_duplicado: str = ""
    fila_duplicada_referencia: str = ""

    confianza_extraccion: str = ""
    observacion_sistema: str = ""
    observacion_usuario: str = ""

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

    def build_duplicate_key(self) -> str:
        self.clave_duplicado = f"{self.punto_venta}-{self.numero_comprobante}-{self.cae}"
        return self.clave_duplicado

    def to_dict(self) -> dict:
        data = asdict(self)
        data["fecha_comprobante"] = (
            self.fecha_comprobante.isoformat() if self.fecha_comprobante else None
        )
        data["fecha_vencimiento_cae"] = (
            self.fecha_vencimiento_cae.isoformat() if self.fecha_vencimiento_cae else None
        )
        return data

    def to_row_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "file_name": self.file_name,
            "tipo_comprobante": self.tipo_comprobante,
            "letra_comprobante": self.letra_comprobante,
            "punto_venta": self.punto_venta,
            "numero_comprobante": self.numero_comprobante,
            "fecha_comprobante": self.fecha_comprobante.isoformat() if self.fecha_comprobante else "",
            "formato_fecha_detectado": self.formato_fecha_detectado,
            "emisor_nombre": self.emisor_nombre,
            "emisor_cuit": self.emisor_cuit,
            "receptor_nombre_detectado": self.receptor_nombre_detectado,
            "receptor_nombre_normalizado": self.receptor_nombre_normalizado,
            "receptor_cuit": self.receptor_cuit,
            "receptor_valido": self.receptor_valido,
            "cae": self.cae,
            "fecha_vencimiento_cae": self.fecha_vencimiento_cae.isoformat() if self.fecha_vencimiento_cae else "",
            "moneda": self.moneda,
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
            "producto_servicio": self.producto_servicio,
            "texto_extraido_ok": self.texto_extraido_ok,
            "campos_faltantes": ", ".join(self.campos_faltantes),
            "validacion_importes": self.validacion_importes,
            "diferencia_redondeo": self.diferencia_redondeo,
            "posible_duplicado": self.posible_duplicado,
            "clave_duplicado": self.clave_duplicado,
            "fila_duplicada_referencia": self.fila_duplicada_referencia,
            "confianza_extraccion": self.confianza_extraccion,
            "observacion_sistema": self.observacion_sistema,
            "observacion_usuario": self.observacion_usuario,
        }