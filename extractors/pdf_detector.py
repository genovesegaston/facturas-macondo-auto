from dataclasses import dataclass

import fitz  # PyMuPDF

from models.document import Document


@dataclass
class PDFDetectionResult:
    """
    Resultado técnico de inspección inicial de un PDF.
    """

    exists: bool
    is_pdf: bool
    page_count: int
    has_text: bool
    text_length: int
    is_likely_scanned: bool
    error_message: str = ""

    def to_dict(self) -> dict:
        return {
            "exists": self.exists,
            "is_pdf": self.is_pdf,
            "page_count": self.page_count,
            "has_text": self.has_text,
            "text_length": self.text_length,
            "is_likely_scanned": self.is_likely_scanned,
            "error_message": self.error_message,
        }


def detect_pdf_characteristics(document: Document) -> PDFDetectionResult:
    """
    Inspecciona un documento PDF y determina características técnicas básicas.

    Reglas iniciales:
    - si no existe o no es PDF, se informa en el resultado
    - si el texto total extraído es muy bajo, se considera probablemente escaneado
    """
    if not document.exists:
        return PDFDetectionResult(
            exists=False,
            is_pdf=False,
            page_count=0,
            has_text=False,
            text_length=0,
            is_likely_scanned=False,
            error_message="El archivo no existe en disco.",
        )

    if not document.is_pdf:
        return PDFDetectionResult(
            exists=True,
            is_pdf=False,
            page_count=0,
            has_text=False,
            text_length=0,
            is_likely_scanned=False,
            error_message="El archivo no tiene extensión PDF.",
        )

    try:
        pdf = fitz.open(document.file_path)

        page_count = len(pdf)
        full_text_parts: list[str] = []

        for page in pdf:
            page_text = page.get_text("text") or ""
            if page_text.strip():
                full_text_parts.append(page_text)

        pdf.close()

        full_text = "\n".join(full_text_parts).strip()
        text_length = len(full_text)
        has_text = text_length > 0

        # Heurística inicial:
        # si no hay texto o hay muy poco texto, probablemente sea escaneado
        is_likely_scanned = not has_text or text_length < 50

        return PDFDetectionResult(
            exists=True,
            is_pdf=True,
            page_count=page_count,
            has_text=has_text,
            text_length=text_length,
            is_likely_scanned=is_likely_scanned,
            error_message="",
        )

    except Exception as exc:
        return PDFDetectionResult(
            exists=True,
            is_pdf=True,
            page_count=0,
            has_text=False,
            text_length=0,
            is_likely_scanned=False,
            error_message=f"Error al inspeccionar PDF: {exc}",
        )


def enrich_document_with_pdf_detection(document: Document) -> PDFDetectionResult:
    """
    Ejecuta la detección técnica y actualiza el modelo Document con los resultados.
    """
    result = detect_pdf_characteristics(document)

    if result.error_message:
        document.mark_status("error", result.error_message)
        return result

    document.has_extractable_text = result.has_text
    document.mark_as_scanned(result.is_likely_scanned)
    document.mark_status("loaded")

    return result