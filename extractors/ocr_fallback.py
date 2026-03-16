import pytesseract
from pdf2image import convert_from_path

from core.config import TESSERACT_CMD, POPPLER_PATH, OCR_LANGUAGE, OCR_DPI
from models.document import Document


def extract_text_with_ocr(
    document: Document,
    tesseract_cmd: str | None = None,
    poppler_path: str | None = None,
    lang: str | None = None,
    dpi: int | None = None,
) -> str:
    """
    Extrae texto de un PDF usando OCR como fallback.

    Si no se reciben parámetros, usa la configuración central del proyecto.
    """
    if not document.exists:
        raise FileNotFoundError(f"El archivo no existe: {document.file_path}")

    if not document.is_pdf:
        raise ValueError(f"El archivo no es un PDF válido: {document.file_path}")

    tesseract_cmd = tesseract_cmd or TESSERACT_CMD
    poppler_path = poppler_path or POPPLER_PATH
    lang = lang or OCR_LANGUAGE
    dpi = dpi or OCR_DPI

    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    images = convert_from_path(
        document.file_path,
        dpi=dpi,
        poppler_path=poppler_path,
    )

    text_parts: list[str] = []

    for image in images:
        page_text = pytesseract.image_to_string(image, lang=lang) or ""
        if page_text.strip():
            text_parts.append(page_text)

    full_text = "\n".join(text_parts).strip()
    return full_text


def enrich_document_with_ocr_text(
    document: Document,
    tesseract_cmd: str | None = None,
    poppler_path: str | None = None,
    lang: str | None = None,
    dpi: int | None = None,
) -> Document:
    """
    Ejecuta OCR sobre el PDF y actualiza el objeto Document.
    """
    try:
        ocr_text = extract_text_with_ocr(
            document=document,
            tesseract_cmd=tesseract_cmd,
            poppler_path=poppler_path,
            lang=lang,
            dpi=dpi,
        )

        document.set_raw_text(ocr_text)
        document.mark_as_scanned(True)

        if ocr_text.strip():
            document.mark_status("ocr_extracted")
        else:
            document.mark_status("error", "OCR ejecutado pero no devolvió texto utilizable.")

        return document

    except Exception as exc:
        document.set_raw_text("")
        document.mark_as_scanned(True)
        document.mark_status("error", f"Error en OCR fallback: {exc}")
        return document