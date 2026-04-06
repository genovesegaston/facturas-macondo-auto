"""
Patrones reutilizables orientados a comprobantes ARCA.
"""

COPY_MARKERS = [
    "ORIGINAL",
    "DUPLICADO",
    "TRIPLICADO",
]

DATE_PATTERNS = {
    "DD/MM/YYYY": r"\b\d{2}/\d{2}/\d{4}\b",
    "DD-MM-YYYY": r"\b\d{2}-\d{2}-\d{4}\b",
    "DD-MMMM-YYYY": r"\b\d{2}-[A-Za-zÁÉÍÓÚáéíóúñÑ]+-\d{4}\b",
}

CUIT_PATTERNS = [
    r"\b\d{2}-\d{8}-\d\b",
    r"\b\d{11}\b",
]

ARCA_DOC_HEADER_PATTERNS = [
    r"\b([ABCM])\s+FACTURA\b",
    r"\b([ABCM])\s+NOTA\s+DE\s+CR[EÉ]DITO\b",
    r"\b([ABCM])\s+NOTA\s+DE\s+D[EÉ]BITO\b",
]

POINT_OF_SALE_AND_NUMBER_PATTERNS = [
    r"Punto de Venta:\s*(\d{1,5})\s*Comp\.\s*Nro:\s*(\d{1,8})",
    r"(\d{4,5})\s*-\s*(\d{6,8})",
]

CAE_PATTERNS = [
    r"CAE\s*N[°º:]*\s*(\d{8,20})",
    r"CAE\s*:\s*(\d{8,20})",
]

CAE_DUE_DATE_PATTERNS = [
    r"Fecha de Vto\. de CAE:\s*([\d/\-A-Za-zÁÉÍÓÚáéíóúñÑ]+)",
]

AMOUNT_LABEL_PATTERNS = {
    "subtotal": [
        r"Subtotal",
        r"Importe Neto Gravado",
    ],
    "iva_21": [r"IVA\s*21%?"],
    "iva_10_5": [r"IVA\s*10[,\.\s]?5%?"],
    "iva_27": [r"IVA\s*27%?"],
    "iva_5": [r"IVA\s*5%?"],
    "iva_2_5": [r"IVA\s*2[,\.\s]?5%?"],
    "percepciones": [
        r"Importe Otros Tributos",
        r"Percepc(?:i[oó]n|iones)",
    ],
    "total": [r"Importe Total"],
}

PRODUCT_BLOCK_START_PATTERNS = [
    r"Código Producto / Servicio",
]

PRODUCT_BLOCK_END_PATTERNS = [
    r"CAE\s*N[°º:]?",
    r"Fecha de Vto\. de CAE",
    r"Comprobante Autorizado",
]