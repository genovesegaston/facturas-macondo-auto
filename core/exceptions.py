class FacturasMacondoError(Exception):
    """
    Excepción base del proyecto.
    """
    default_message = "Error general en facturas-macondo-auto."

    def __init__(self, message: str | None = None):
        super().__init__(message or self.default_message)


# =========================
# Documentos / archivos
# =========================

class DocumentError(FacturasMacondoError):
    default_message = "Error relacionado con el documento."


class InvalidDocumentError(DocumentError):
    default_message = "El documento no es válido."


class DocumentNotFoundError(DocumentError):
    default_message = "El documento no fue encontrado."


class UnsupportedFileTypeError(DocumentError):
    default_message = "El tipo de archivo no es soportado."


# =========================
# Extractores
# =========================

class ExtractionError(FacturasMacondoError):
    default_message = "Error durante la extracción de texto."


class PDFDetectionError(ExtractionError):
    default_message = "Error al detectar características del PDF."


class PDFTextExtractionError(ExtractionError):
    default_message = "Error al extraer texto del PDF."


class OCRExtractionError(ExtractionError):
    default_message = "Error durante OCR fallback."


class TextCleaningError(ExtractionError):
    default_message = "Error durante la limpieza del texto extraído."


# =========================
# Parsing
# =========================

class ParsingError(FacturasMacondoError):
    default_message = "Error durante el parsing del documento."


class DateParsingError(ParsingError):
    default_message = "Error al parsear fecha."


class AmountParsingError(ParsingError):
    default_message = "Error al parsear importe."


class CuitParsingError(ParsingError):
    default_message = "Error al parsear CUIT."


class ReceiverParsingError(ParsingError):
    default_message = "Error al parsear receptor."


class InvoiceParsingError(ParsingError):
    default_message = "Error al parsear factura o nota."


# =========================
# Validación
# =========================

class ValidationError(FacturasMacondoError):
    default_message = "Error durante la validación."


class AmountValidationError(ValidationError):
    default_message = "Error al validar importes."


class ReceiverValidationError(ValidationError):
    default_message = "Error al validar receptor."


class DuplicateValidationError(ValidationError):
    default_message = "Error al validar duplicados."


class ConfidenceCalculationError(ValidationError):
    default_message = "Error al calcular confianza."


class BusinessRulesError(ValidationError):
    default_message = "Error al evaluar reglas de negocio."


class InvoiceValidationError(ValidationError):
    default_message = "Error durante la validación integral del documento."


# =========================
# Servicios
# =========================

class ServiceError(FacturasMacondoError):
    default_message = "Error en un servicio del sistema."


class ProcessingServiceError(ServiceError):
    default_message = "Error en el procesamiento del documento."


class BatchServiceError(ServiceError):
    default_message = "Error en el procesamiento del lote."


class ReviewServiceError(ServiceError):
    default_message = "Error en el servicio de revisión."


class ExportServiceError(ServiceError):
    default_message = "Error en el servicio de exportación."


class SheetsServiceError(ServiceError):
    default_message = "Error en el servicio de Google Sheets."


# =========================
# Integraciones
# =========================

class IntegrationError(FacturasMacondoError):
    default_message = "Error de integración externa."


class GoogleAuthError(IntegrationError):
    default_message = "Error de autenticación con Google."


class GoogleSheetsError(IntegrationError):
    default_message = "Error en operación con Google Sheets."


class ExcelExportError(IntegrationError):
    default_message = "Error al exportar a Excel."