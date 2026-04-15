# =========================
# Tipos de comprobante
# =========================

DOCUMENT_TYPE_FACTURA = "Factura"
DOCUMENT_TYPE_NOTA_CREDITO = "Nota de Crédito"
DOCUMENT_TYPE_NOTA_DEBITO = "Nota de Débito"

DOCUMENT_TYPES = {
    DOCUMENT_TYPE_FACTURA,
    DOCUMENT_TYPE_NOTA_CREDITO,
    DOCUMENT_TYPE_NOTA_DEBITO,
}


# =========================
# Letras de comprobante
# =========================

LETTER_A = "A"
LETTER_B = "B"
LETTER_C = "C"
LETTER_M = "M"

DOCUMENT_LETTERS = {
    LETTER_A,
    LETTER_B,
    LETTER_C,
    LETTER_M,
}


# =========================
# Niveles de confianza
# =========================

CONFIDENCE_HIGH = "Alta"
CONFIDENCE_MEDIUM = "Media"
CONFIDENCE_LOW = "Baja"

CONFIDENCE_LEVELS = {
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_LOW,
}


# =========================
# Estados de procesamiento documento
# =========================

STATUS_PENDING = "pending"
STATUS_LOADED = "loaded"
STATUS_EXTRACTED = "extracted"
STATUS_OCR_EXTRACTED = "ocr_extracted"
STATUS_CLEANED = "cleaned"
STATUS_PARSED = "parsed"
STATUS_VALIDATED = "validated"
STATUS_ERROR = "error"

DOCUMENT_STATUSES = {
    STATUS_PENDING,
    STATUS_LOADED,
    STATUS_EXTRACTED,
    STATUS_OCR_EXTRACTED,
    STATUS_CLEANED,
    STATUS_PARSED,
    STATUS_VALIDATED,
    STATUS_ERROR,
}


# =========================
# Eventos de procesamiento
# =========================

EVENT_DOCUMENT_CREATED = "DOCUMENT_CREATED"
EVENT_PDF_DETECTED = "PDF_DETECTED"
EVENT_TEXT_EXTRACTED = "TEXT_EXTRACTED"
EVENT_OCR_EXTRACTED = "OCR_EXTRACTED"
EVENT_TEXT_CLEANED = "TEXT_CLEANED"
EVENT_INVOICE_PARSED = "INVOICE_PARSED"
EVENT_INVOICE_VALIDATED = "INVOICE_VALIDATED"
EVENT_BATCH_STARTED = "BATCH_STARTED"
EVENT_BATCH_FINISHED = "BATCH_FINISHED"
EVENT_BATCH_FILE_ACCEPTED = "BATCH_FILE_ACCEPTED"
EVENT_BATCH_FILE_INVALID = "BATCH_FILE_INVALID"
EVENT_BATCH_FILE_SKIPPED = "BATCH_FILE_SKIPPED"
EVENT_MANUAL_REVIEW_CHANGE = "MANUAL_REVIEW_CHANGE"


# =========================
# Severidades de log
# =========================

LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"

LOG_LEVELS = {
    LOG_LEVEL_INFO,
    LOG_LEVEL_WARNING,
    LOG_LEVEL_ERROR,
}


# =========================
# Nombres de hojas Google Sheets / Excel
# =========================

SHEET_FACTURAS = "FACTURAS"
SHEET_PARAMETROS = "PARAMETROS"
SHEET_LOG = "LOG"
SHEET_ERRORES = "ERRORES"
SHEET_CONTROL = "CONTROL"
SHEET_RESULTADOS = "Resultados"


# =========================
# Campos críticos del negocio
# =========================

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


# =========================
# Copias ARCA
# =========================

ARCA_COPY_ORIGINAL = "ORIGINAL"
ARCA_COPY_DUPLICADO = "DUPLICADO"
ARCA_COPY_TRIPLICADO = "TRIPLICADO"

ARCA_COPY_MARKERS = [
    ARCA_COPY_ORIGINAL,
    ARCA_COPY_DUPLICADO,
    ARCA_COPY_TRIPLICADO,
]