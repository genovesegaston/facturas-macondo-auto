import re
import unicodedata

from models.document import Document


def normalize_unicode_text(text: str) -> str:
    """
    Normaliza caracteres unicode problemáticos sin eliminar acentos.
    """
    if not text:
        return ""
    return unicodedata.normalize("NFKC", text)


def normalize_line_breaks(text: str) -> str:
    """
    Unifica saltos de línea Windows/Unix/Mac.
    """
    if not text:
        return ""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def remove_non_printable_chars(text: str) -> str:
    """
    Elimina caracteres no imprimibles, preservando saltos de línea y tabulaciones.
    """
    if not text:
        return ""
    return "".join(
        ch for ch in text
        if ch.isprintable() or ch in ("\n", "\t")
    )


def collapse_horizontal_whitespace(text: str) -> str:
    """
    Reduce espacios y tabulaciones repetidas dentro de líneas.
    """
    if not text:
        return ""
    lines = text.split("\n")
    cleaned_lines = [re.sub(r"[ \t]+", " ", line).strip() for line in lines]
    return "\n".join(cleaned_lines)


def collapse_excess_blank_lines(text: str, max_blank_lines: int = 1) -> str:
    """
    Reduce bloques de líneas en blanco consecutivas.
    """
    if not text:
        return ""

    lines = text.split("\n")
    result: list[str] = []
    blank_count = 0

    for line in lines:
        if line.strip() == "":
            blank_count += 1
            if blank_count <= max_blank_lines:
                result.append("")
        else:
            blank_count = 0
            result.append(line)

    return "\n".join(result).strip()


def clean_extracted_text(text: str) -> str:
    """
    Aplica la limpieza base al texto extraído.

    Orden:
    1. normalización unicode
    2. normalización de saltos de línea
    3. eliminación de caracteres no imprimibles
    4. reducción de espacios horizontales
    5. reducción de líneas en blanco excesivas
    """
    if not text:
        return ""

    text = normalize_unicode_text(text)
    text = normalize_line_breaks(text)
    text = remove_non_printable_chars(text)
    text = collapse_horizontal_whitespace(text)
    text = collapse_excess_blank_lines(text)

    return text.strip()


def enrich_document_with_clean_text(document: Document) -> Document:
    """
    Limpia el texto extraído del documento y actualiza clean_text.

    Requiere que document.text_content ya tenga contenido bruto.
    """
    try:
        clean_text = clean_extracted_text(document.text_content)
        document.set_clean_text(clean_text)

        if clean_text:
            document.mark_status("cleaned")
        else:
            document.mark_status("error", "El texto limpio quedó vacío.")

        return document

    except Exception as exc:
        document.set_clean_text("")
        document.mark_status("error", f"Error al limpiar texto extraído: {exc}")
        return document