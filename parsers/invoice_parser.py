import re

from models.document import Document
from models.invoice_data import InvoiceData
from parsers.amount_parser import extract_invoice_amounts
from parsers.cuit_parser import extract_all_valid_cuits, normalize_cuit
from parsers.date_parser import ParsedDateResult, extract_first_valid_date, find_date_candidates, parse_date_string
from parsers.receiver_parser import EXPECTED_RECEIVER_NORMALIZED, normalize_receiver_text


def get_working_text(text: str) -> str:
    """
    En esta etapa, trabajar sobre el texto completo.
    Los PDFs ARCA suelen traer ORIGINAL / DUPLICADO / TRIPLICADO,
    pero el recorte por copia todavía no es suficientemente confiable.
    """
    return text.strip() if text else ""


def get_non_empty_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def detect_document_type_and_letter(text: str) -> tuple[str, str]:
    """
    Soporta dos casos:
    1) 'A FACTURA'
    2) líneas consecutivas:
       FACTURA
       A
    """
    if not text:
        return "", ""

    # Caso 1: encabezado conjunto
    match = re.search(r"\b([ABCM])\s+(FACTURA|NOTA\s+DE\s+CR[EÉ]DITO|NOTA\s+DE\s+D[EÉ]BITO)\b", text, re.IGNORECASE)
    if match:
        letter = match.group(1).upper()
        label = match.group(2).upper()
        if "NOTA DE CR" in label:
            return "Nota de Crédito", letter
        if "NOTA DE D" in label:
            return "Nota de Débito", letter
        return "Factura", letter

    # Caso 2: líneas separadas
    lines = get_non_empty_lines(text)
    for i, line in enumerate(lines[:-1]):
        line_up = line.upper().strip()
        next_up = lines[i + 1].upper().strip()

        if line_up in {"FACTURA", "NOTA DE CRÉDITO", "NOTA DE CREDITO", "NOTA DE DÉBITO", "NOTA DE DEBITO"}:
            if next_up in {"A", "B", "C", "M"}:
                if "CR" in line_up:
                    return "Nota de Crédito", next_up
                if "DÉBITO" in line_up or "DEBITO" in line_up:
                    return "Nota de Débito", next_up
                return "Factura", next_up

    return "", ""


def detect_point_of_sale_and_number(text: str) -> tuple[str, str]:
    """
    Soporta:
    1) misma línea
       Punto de Venta: 00002  Comp. Nro: 00000108
    2) líneas separadas
       Punto de Venta:
       Comp. Nro:
       00002
       00000108
    """
    if not text:
        return "", ""

    # Caso 1: misma línea o bloque cercano
    pattern_inline = re.search(
        r"Punto de Venta:\s*(\d{1,5})\s*Comp\.\s*Nro:\s*(\d{1,8})",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if pattern_inline:
        return pattern_inline.group(1).zfill(5), pattern_inline.group(2).zfill(8)

    lines = get_non_empty_lines(text)

    # Caso 2: buscar etiquetas y tomar siguientes valores numéricos
    for i, line in enumerate(lines):
        if "PUNTO DE VENTA" in line.upper():
            window = lines[i:i + 8]
            nums = []
            for item in window:
                if re.fullmatch(r"\d{1,8}", item):
                    nums.append(item)
            if len(nums) >= 2:
                return nums[0].zfill(5), nums[1].zfill(8)

    # Fallback: patrón clásico 00002 00000108 en bloque cercano
    fallback = re.search(r"\b(\d{1,5})\b[\s\n]+\b(\d{1,8})\b", text)
    if fallback:
        a, b = fallback.group(1), fallback.group(2)
        if len(a) <= 5 and len(b) <= 8:
            return a.zfill(5), b.zfill(8)

    return "", ""


def detect_cae(text: str) -> str:
    """
    Detecta CAE en formato ARCA.

    Casos soportados:
    1) CAE N°: 86107028004666
    2) CAE N°:
       86107028004666
    3) bloque linealizado donde primero aparece 'Fecha de Vto. de CAE'
       y luego la fecha y luego el CAE
    """
    if not text:
        return ""

    # Caso 1: mismo renglón
    match = re.search(r"CAE\s*N[°º:]?\s*[:\-]?\s*(\d{8,20})", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    lines = get_non_empty_lines(text)

    # Caso 2: dentro de una ventana posterior a la etiqueta CAE
    for i, line in enumerate(lines):
        if "CAE" in line.upper():
            window = lines[i:i + 10]
            numeric_candidates = []

            for item in window:
                m = re.fullmatch(r"\d{8,20}", item.strip())
                if m:
                    numeric_candidates.append(m.group(0))

            if numeric_candidates:
                # Si hay varios números largos, normalmente el CAE es el último
                return numeric_candidates[-1]

    # Caso 3: fallback global
    # Tomar números largos válidos y elegir el último,
    # porque en este formato el CAE suele quedar después del vto.
    global_candidates = re.findall(r"\b\d{8,20}\b", text)
    if global_candidates:
        return global_candidates[-1]

    return ""


def detect_cae_due_date(text: str) -> ParsedDateResult:
    """
    Soporta fecha en misma línea o en línea siguiente a 'Fecha de Vto. de CAE:'.
    """
    if not text:
        return ParsedDateResult(value=None, success=False, error_message="Texto vacío.")

    # misma línea
    match = re.search(r"Fecha de Vto\. de CAE:\s*([^\n\r]+)", text, re.IGNORECASE)
    if match:
        candidates = find_date_candidates(match.group(1))
        for candidate in candidates:
            parsed = parse_date_string(candidate)
            if parsed.success:
                return parsed

    # línea siguiente
    lines = get_non_empty_lines(text)
    for i, line in enumerate(lines):
        if "FECHA DE VTO. DE CAE" in line.upper():
            window = lines[i:i + 5]
            for item in window:
                candidates = find_date_candidates(item)
                for candidate in candidates:
                    parsed = parse_date_string(candidate)
                    if parsed.success:
                        return parsed

    return ParsedDateResult(
        value=None,
        success=False,
        error_message="No se encontró fecha de vencimiento de CAE.",
    )


def detect_issue_date(text: str) -> ParsedDateResult:
    """
    Regla ARCA:
    después de 'Fecha de Emisión:' aparecen varias fechas.
    Tomamos la primera fecha válida inmediatamente posterior a esa etiqueta.
    """
    if not text:
        return ParsedDateResult(value=None, success=False, error_message="Texto vacío.")

    match = re.search(r"Fecha de Emisión:\s*(.+?)CUIT:", text, re.IGNORECASE | re.DOTALL)
    if match:
        zone = match.group(1)
        candidates = find_date_candidates(zone)
        for candidate in candidates:
            parsed = parse_date_string(candidate)
            if parsed.success:
                return parsed

    # fallback general
    return extract_first_valid_date(text)


def detect_receiver_data(text: str) -> tuple[str, str, bool]:
    """
    Busca el bloque del receptor a partir de:
    'Apellido y Nombre / Razón Social:' seguido por 'CUIT:' y la razón social.
    En los ARCA analizados, MACONDO aparece en líneas cercanas al CUIT 30708762233.
    """
    if not text:
        return "", "", False

    lines = get_non_empty_lines(text)

    # Estrategia 1: buscar MACONDO y un CUIT cercano en la misma ventana
    for i, line in enumerate(lines):
        if "MACONDO" in line.upper():
            receiver_name = line.strip()
            window_start = max(0, i - 5)
            window_end = min(len(lines), i + 2)
            window = lines[window_start:window_end]

            receiver_cuit = ""
            for item in window:
                m = re.fullmatch(r"\d{11}|\d{2}-\d{8}-\d", item)
                if m:
                    normalized = normalize_cuit(m.group(0))
                    if normalized == "30708762233":
                        receiver_cuit = normalized
                        break

            normalized_name = EXPECTED_RECEIVER_NORMALIZED if "MACONDO" in receiver_name.upper() else normalize_receiver_text(receiver_name)
            is_valid = normalized_name == EXPECTED_RECEIVER_NORMALIZED
            return receiver_name, receiver_cuit, is_valid

    # Estrategia 2: buscar el CUIT de Macondo y luego la línea siguiente útil
    for i, line in enumerate(lines):
        normalized = normalize_cuit(line)
        if normalized == "30708762233":
            for nxt in lines[i:i + 4]:
                if "MACONDO" in nxt.upper():
                    return nxt.strip(), "30708762233", True

    return "", "", False


def detect_issuer_name(text: str) -> str:
    """
    En ARCA, el emisor suele aparecer en la línea siguiente a ORIGINAL/DUPLICADO/TRIPLICADO.
    """
    lines = get_non_empty_lines(text)
    if not lines:
        return ""

    for i, line in enumerate(lines):
        up = line.upper()
        if up in {"ORIGINAL", "DUPLICADO", "TRIPLICADO"}:
            for candidate in lines[i + 1:i + 6]:
                if (
                    candidate
                    and "FECHA DE EMISIÓN" not in candidate.upper()
                    and "CUIT" not in candidate.upper()
                    and not re.fullmatch(r"[\d/\-]+", candidate)
                ):
                    return candidate.strip()

    # fallback por bloque Razón Social
    for i, line in enumerate(lines):
        if line.upper().startswith("RAZÓN SOCIAL") or line.upper().startswith("RAZON SOCIAL"):
            for nxt in lines[i + 1:i + 4]:
                if nxt and "CONDICIÓN FRENTE AL IVA" not in nxt.upper() and "CONDICION FRENTE AL IVA" not in nxt.upper():
                    return nxt.strip()

    return ""


def detect_issuer_cuit(text: str, receiver_cuit: str) -> str:
    """
    Busca CUIT del emisor como CUIT válido distinto del receptor,
    priorizando la zona cercana al encabezado/emisor.
    """
    lines = get_non_empty_lines(text)

    # priorizar zona temprana del documento
    early_zone = "\n".join(lines[:40])
    cuits = extract_all_valid_cuits(early_zone)
    for cuit in cuits:
        if cuit.value != receiver_cuit:
            return cuit.value

    # fallback general
    all_cuits = extract_all_valid_cuits(text)
    for cuit in all_cuits:
        if cuit.value != receiver_cuit:
            return cuit.value

    return ""


def detect_currency(text: str) -> str:
    return "USD" if re.search(r"usd|u\$s|d[oó]lares?", text, re.IGNORECASE) else "ARS"


def detect_product_service(text: str) -> str:
    """
    Toma bloque descriptivo entre encabezado de ítems y CAE/importe total.
    """
    if not text:
        return ""

    start_match = re.search(r"Código\s+Producto\s*/\s*Servicio", text, re.IGNORECASE)
    if not start_match:
        return ""

    tail = text[start_match.end():]
    end_match = re.search(r"CAE\s*N[°º:]?|Importe Otros Tributos|Importe Total", tail, re.IGNORECASE)
    block = tail[:end_match.start()] if end_match else tail

    lines = [line.strip() for line in block.splitlines() if line.strip()]
    cleaned = []

    for line in lines:
        if re.search(r"(cantidad|u\.?\s*medida|precio unit|bonif|subtotal|alicuota|iva)", line, re.IGNORECASE):
            continue
        if re.fullmatch(r"[\d\s,.\-%$]+", line):
            continue
        cleaned.append(line)

    return " ".join(cleaned[:4]).strip()


def detect_missing_fields(invoice: InvoiceData) -> list[str]:
    missing = []

    if not invoice.tipo_comprobante:
        missing.append("tipo_comprobante")
    if not invoice.letra_comprobante:
        missing.append("letra_comprobante")
    if not invoice.punto_venta:
        missing.append("punto_venta")
    if not invoice.numero_comprobante:
        missing.append("numero_comprobante")
    if not invoice.fecha_comprobante:
        missing.append("fecha_comprobante")
    if not invoice.emisor_nombre:
        missing.append("emisor_nombre")
    if not invoice.emisor_cuit:
        missing.append("emisor_cuit")
    if not invoice.receptor_nombre_detectado:
        missing.append("receptor_nombre")
    if not invoice.receptor_cuit:
        missing.append("receptor_cuit")
    if not invoice.cae:
        missing.append("cae")
    if not invoice.total:
        missing.append("total")

    return missing


def parse_invoice_document(document: Document) -> InvoiceData:
    source_text = document.clean_text or document.text_content or ""
    working_text = get_working_text(source_text)

    invoice = InvoiceData(
        document_id=document.document_id,
        file_name=document.file_name,
        texto_extraido_ok=bool(working_text.strip()),
    )

    if not working_text.strip():
        invoice.observacion_sistema = "Documento sin texto utilizable para parsing."
        invoice.campos_faltantes = detect_missing_fields(invoice)
        return invoice

    invoice.tipo_comprobante, invoice.letra_comprobante = detect_document_type_and_letter(working_text)
    invoice.punto_venta, invoice.numero_comprobante = detect_point_of_sale_and_number(working_text)

    issue_date = detect_issue_date(working_text)
    if issue_date.success:
        invoice.fecha_comprobante = issue_date.value
        invoice.formato_fecha_detectado = issue_date.detected_format

    receiver_name, receiver_cuit, receiver_valid = detect_receiver_data(working_text)
    invoice.receptor_nombre_detectado = receiver_name
    invoice.receptor_nombre_normalizado = (
        EXPECTED_RECEIVER_NORMALIZED if receiver_valid else normalize_receiver_text(receiver_name)
    )
    invoice.receptor_cuit = receiver_cuit
    invoice.receptor_valido = receiver_valid

    invoice.emisor_nombre = detect_issuer_name(working_text)
    invoice.emisor_cuit = detect_issuer_cuit(working_text, receiver_cuit=invoice.receptor_cuit)

    invoice.cae = detect_cae(working_text)

    cae_due = detect_cae_due_date(working_text)
    if cae_due.success:
        invoice.fecha_vencimiento_cae = cae_due.value

    invoice.moneda = detect_currency(working_text)

    amounts = extract_invoice_amounts(working_text)
    invoice.subtotal = amounts.subtotal
    invoice.iva_21 = amounts.iva_21
    invoice.iva_10_5 = amounts.iva_10_5
    invoice.iva_27 = amounts.iva_27
    invoice.iva_5 = amounts.iva_5
    invoice.iva_2_5 = amounts.iva_2_5
    invoice.iva_otros = amounts.iva_otros
    invoice.iva_total = amounts.iva_total
    invoice.percepciones = amounts.percepciones
    invoice.total = amounts.total

    invoice.producto_servicio = detect_product_service(working_text)

    invoice.build_duplicate_key()
    invoice.campos_faltantes = detect_missing_fields(invoice)

    if invoice.campos_faltantes:
        invoice.observacion_sistema = "Campos faltantes detectados: " + ", ".join(invoice.campos_faltantes)

    return invoice