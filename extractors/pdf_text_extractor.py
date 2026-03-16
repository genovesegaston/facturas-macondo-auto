import fitz  # PyMuPDF

from models.document import Document


def extract_text_from_pdf(document: Document) -> str:
    """
    Extrae el texto bruto de un PDF digital y lo devuelve como string.

    Reglas:
    - requiere que el archivo exista
    - requiere que sea PDF
    - concatena el texto de todas las páginas
    - no limpia ni normaliza en profundidad
    """
    if not document.exists:
        raise FileNotFoundError(f"El archivo no existe: {document.file_path}")

    if not document.is_pdf:
        raise ValueError(f"El archivo no es un PDF válido: {document.file_path}")

    pdf = fitz.open(document.file_path)
    text_parts: list[str] = []

    try:
        for page in pdf:
            page_text = page.get_text("text") or ""
            if page_text:
                text_parts.append(page_text)
    finally:
        pdf.close()

    full_text = "\n".join(text_parts).strip()
    return full_text


def enrich_document_with_extracted_text(document: Document) -> Document:
    """
    Extrae el texto del PDF y actualiza el objeto Document.

    Actualizaciones:
    - text_content
    - has_extractable_text
    - status
    - error_message si falla
    """
    try:
        extracted_text = extract_text_from_pdf(document)
        document.set_raw_text(extracted_text)

        if extracted_text.strip():
            document.mark_status("extracted")
        else:
            document.mark_status("error", "No se pudo extraer texto del PDF.")

        return document

    except Exception as exc:
        document.set_raw_text("")
        document.mark_status("error", f"Error al extraer texto del PDF: {exc}")
        return document