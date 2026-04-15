from datetime import datetime
from pathlib import Path
from uuid import uuid4

from extractors.ocr_fallback import enrich_document_with_ocr_text
from extractors.pdf_detector import enrich_document_with_pdf_detection
from extractors.pdf_text_extractor import enrich_document_with_extracted_text
from extractors.text_cleaner import enrich_document_with_clean_text
from models.batch_result import BatchResult
from models.document import Document
from models.invoice_data import InvoiceData
from models.processing_log import ProcessingLog
from models.validation_result import ValidationResult
from parsers.invoice_parser import parse_invoice_document
from validators.invoice_validator import validate_invoice


def build_log(
    level: str,
    event_type: str,
    message: str,
    document: Document | None = None,
    batch_id: str = "",
    details: dict | None = None,
) -> ProcessingLog:
    """
    Crea un evento de log estructurado.
    """
    return ProcessingLog(
        timestamp=datetime.now(),
        level=level,
        event_type=event_type,
        file_name=document.file_name if document else "",
        file_path=str(document.file_path) if document else "",
        document_id=document.document_id if document else "",
        batch_id=batch_id,
        message=message,
        details=details or {},
    )


def process_single_document(
    file_path: str | Path,
    existing_keys=None,
    existing_records=None,
    use_ocr_fallback: bool = True,
    tesseract_cmd: str | None = None,
    poppler_path: str | None = None,
) -> tuple[Document, InvoiceData, ValidationResult, list[ProcessingLog]]:
    """
    Procesa un único archivo PDF de punta a punta.
    """
    logs: list[ProcessingLog] = []
    document = Document(file_path=Path(file_path))

    logs.append(build_log("INFO", "DOCUMENT_CREATED", "Documento creado.", document=document))

    # 1. Detección PDF
    detection_result = enrich_document_with_pdf_detection(document)
    logs.append(
        build_log(
            "INFO" if not detection_result.error_message else "ERROR",
            "PDF_DETECTED",
            "Detección inicial de PDF ejecutada.",
            document=document,
            details=detection_result.to_dict(),
        )
    )

    if document.status == "error":
        invoice = InvoiceData(
            document_id=document.document_id,
            file_name=document.file_name,
            texto_extraido_ok=False,
            observacion_sistema=document.error_message,
            campos_faltantes=["documento_invalido"],
        )
        validation = ValidationResult(
            is_valid=False,
            errors=[document.error_message],
            system_notes=document.error_message,
        )
        return document, invoice, validation, logs

    # 2. Extracción de texto
    if document.has_extractable_text and not document.is_scanned:
        document = enrich_document_with_extracted_text(document)
        logs.append(
            build_log(
                "INFO" if document.status != "error" else "ERROR",
                "TEXT_EXTRACTED",
                "Extracción directa de texto ejecutada.",
                document=document,
            )
        )
    elif use_ocr_fallback:
        document = enrich_document_with_ocr_text(
            document=document,
            tesseract_cmd=tesseract_cmd,
            poppler_path=poppler_path,
        )
        logs.append(
            build_log(
                "INFO" if document.status != "error" else "ERROR",
                "OCR_EXTRACTED",
                "Extracción OCR ejecutada.",
                document=document,
            )
        )
    else:
        document.mark_status("error", "Documento sin texto extraíble y OCR deshabilitado.")
        logs.append(
            build_log(
                "ERROR",
                "TEXT_EXTRACTION_FAILED",
                "No se pudo extraer texto del documento.",
                document=document,
            )
        )

    if document.status == "error":
        invoice = InvoiceData(
            document_id=document.document_id,
            file_name=document.file_name,
            texto_extraido_ok=False,
            observacion_sistema=document.error_message,
            campos_faltantes=["texto_extraible"],
        )
        validation = ValidationResult(
            is_valid=False,
            errors=[document.error_message],
            system_notes=document.error_message,
        )
        return document, invoice, validation, logs

    # 3. Limpieza de texto
    document = enrich_document_with_clean_text(document)
    logs.append(
        build_log(
            "INFO" if document.status != "error" else "ERROR",
            "TEXT_CLEANED",
            "Limpieza de texto ejecutada.",
            document=document,
        )
    )

    if document.status == "error":
        invoice = InvoiceData(
            document_id=document.document_id,
            file_name=document.file_name,
            texto_extraido_ok=False,
            observacion_sistema=document.error_message,
            campos_faltantes=["texto_limpio"],
        )
        validation = ValidationResult(
            is_valid=False,
            errors=[document.error_message],
            system_notes=document.error_message,
        )
        return document, invoice, validation, logs

    # 4. Parsing
    invoice = parse_invoice_document(document)
    logs.append(
        build_log(
            "INFO",
            "INVOICE_PARSED",
            "Parsing de factura ejecutado.",
            document=document,
            details={"invoice_dict": invoice.to_dict()},
        )
    )

    # 5. Validación
    invoice, validation = validate_invoice(
        invoice=invoice,
        existing_keys=existing_keys,
        existing_records=existing_records,
    )
    logs.append(
        build_log(
            "INFO" if validation.is_valid else "WARNING",
            "INVOICE_VALIDATED",
            "Validación integral ejecutada.",
            document=document,
            details={"validation_dict": validation.to_dict()},
        )
    )

    return document, invoice, validation, logs


def process_batch(
    file_paths: list[str | Path],
    existing_keys=None,
    existing_records=None,
    use_ocr_fallback: bool = True,
    tesseract_cmd: str | None = None,
    poppler_path: str | None = None,
) -> tuple[BatchResult, list[ProcessingLog]]:
    """
    Procesa un lote de archivos.
    """
    batch_id = str(uuid4())
    batch = BatchResult(
        batch_id=batch_id,
        started_at=datetime.now(),
    )

    all_logs: list[ProcessingLog] = []
    all_logs.append(
        build_log(
            "INFO",
            "BATCH_STARTED",
            f"Inicio de lote con {len(file_paths)} archivo(s).",
            batch_id=batch_id,
        )
    )

    for file_path in file_paths:
        document, invoice, validation, logs = process_single_document(
            file_path=file_path,
            existing_keys=existing_keys,
            existing_records=existing_records,
            use_ocr_fallback=use_ocr_fallback,
            tesseract_cmd=tesseract_cmd,
            poppler_path=poppler_path,
        )

        batch.add_document(document)
        batch.add_invoice(invoice)
        batch.add_validation_result(validation)
        batch.increment_processed()

        if validation.is_valid:
            batch.increment_successful()
        else:
            batch.add_error(validation.system_notes or "Documento con validación no satisfactoria.")

        all_logs.extend(logs)

    batch.finish()
    batch.recalculate_metrics()

    all_logs.append(
        build_log(
            "INFO",
            "BATCH_FINISHED",
            "Lote finalizado.",
            batch_id=batch_id,
            details=batch.to_summary_dict(),
        )
    )

    return batch, all_logs