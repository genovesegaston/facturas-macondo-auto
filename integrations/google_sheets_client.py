from dataclasses import dataclass
from typing import Any

import gspread

from integrations.google_auth import build_gspread_client


@dataclass
class GoogleSheetsClientResult:
    """
    Resultado simple de operación sobre Google Sheets.
    """
    success: bool
    spreadsheet_id: str = ""
    worksheet_name: str = ""
    affected_rows: int = 0
    error_message: str = ""

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "spreadsheet_id": self.spreadsheet_id,
            "worksheet_name": self.worksheet_name,
            "affected_rows": self.affected_rows,
            "error_message": self.error_message,
        }


def get_client(service_account_file: str = "service_account.json") -> gspread.Client:
    """
    Devuelve cliente autenticado de gspread.
    """
    return build_gspread_client(service_account_file)


def open_spreadsheet(client: gspread.Client, spreadsheet_id: str):
    """
    Abre una planilla por ID.
    """
    return client.open_by_key(spreadsheet_id)


def get_worksheet(client: gspread.Client, spreadsheet_id: str, worksheet_name: str):
    """
    Obtiene una hoja existente.
    """
    spreadsheet = open_spreadsheet(client, spreadsheet_id)
    return spreadsheet.worksheet(worksheet_name)


def get_or_create_worksheet(
    client: gspread.Client,
    spreadsheet_id: str,
    worksheet_name: str,
    rows: int = 1000,
    cols: int = 100,
):
    """
    Obtiene una hoja si existe, o la crea si no existe.
    """
    spreadsheet = open_spreadsheet(client, spreadsheet_id)

    try:
        return spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=worksheet_name, rows=rows, cols=cols)


def get_headers(worksheet) -> list[str]:
    """
    Devuelve la primera fila como encabezados.
    """
    values = worksheet.get_all_values()
    if not values:
        return []
    return values[0]


def ensure_headers(worksheet, headers: list[str]) -> None:
    """
    Garantiza que la hoja tenga encabezados en la primera fila.
    """
    existing_headers = get_headers(worksheet)

    if not existing_headers:
        worksheet.update("A1", [headers])
        return

    # si la fila existe pero está vacía
    if all(not str(cell).strip() for cell in existing_headers):
        worksheet.update("A1", [headers])


def append_rows(worksheet, rows: list[dict]) -> int:
    """
    Inserta filas al final de la hoja usando el orden de encabezados.
    Si la hoja no tiene encabezados, usa las claves de la primera fila.
    """
    if not rows:
        return 0

    headers = get_headers(worksheet)
    if not headers:
        headers = list(rows[0].keys())
        ensure_headers(worksheet, headers)

    values = []
    for row in rows:
        values.append([row.get(header, "") for header in headers])

    worksheet.append_rows(values, value_input_option="USER_ENTERED")
    return len(values)


def get_all_records(worksheet) -> list[dict[str, Any]]:
    """
    Devuelve todos los registros de la hoja como lista de diccionarios.
    """
    return worksheet.get_all_records()


def get_existing_duplicate_keys(
    worksheet,
    key_field: str = "clave_duplicado",
) -> list[str]:
    """
    Devuelve las claves de duplicado ya existentes en la hoja.
    """
    records = get_all_records(worksheet)
    keys: list[str] = []

    for record in records:
        value = str(record.get(key_field, "")).strip()
        if value:
            keys.append(value)

    return keys


def write_rows_to_sheet(
    spreadsheet_id: str,
    worksheet_name: str,
    rows: list[dict],
    service_account_file: str = "service_account.json",
    create_if_missing: bool = True,
) -> GoogleSheetsClientResult:
    """
    Escribe filas en una hoja de Google Sheets.
    """
    try:
        client = get_client(service_account_file)

        if create_if_missing:
            worksheet = get_or_create_worksheet(client, spreadsheet_id, worksheet_name)
        else:
            worksheet = get_worksheet(client, spreadsheet_id, worksheet_name)

        affected_rows = append_rows(worksheet, rows)

        return GoogleSheetsClientResult(
            success=True,
            spreadsheet_id=spreadsheet_id,
            worksheet_name=worksheet_name,
            affected_rows=affected_rows,
            error_message="",
        )

    except Exception as exc:
        return GoogleSheetsClientResult(
            success=False,
            spreadsheet_id=spreadsheet_id,
            worksheet_name=worksheet_name,
            affected_rows=0,
            error_message=f"Error al escribir filas en Google Sheets: {exc}",
        )