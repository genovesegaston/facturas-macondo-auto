from enum import Enum


class StrEnum(str, Enum):
    """
    Base enum que se comporta como string.
    """

    def __str__(self) -> str:
        return str(self.value)


class DocumentStatus(StrEnum):
    PENDING = "pending"
    LOADED = "loaded"
    EXTRACTED = "extracted"
    OCR_EXTRACTED = "ocr_extracted"
    CLEANED = "cleaned"
    PARSED = "parsed"
    VALIDATED = "validated"
    ERROR = "error"


class ConfidenceLevel(StrEnum):
    HIGH = "Alta"
    MEDIUM = "Media"
    LOW = "Baja"


class LogLevel(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class DocumentType(StrEnum):
    FACTURA = "Factura"
    NOTA_CREDITO = "Nota de Crédito"
    NOTA_DEBITO = "Nota de Débito"


class DocumentLetter(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    M = "M"


class ArcaCopyType(StrEnum):
    ORIGINAL = "ORIGINAL"
    DUPLICADO = "DUPLICADO"
    TRIPLICADO = "TRIPLICADO"