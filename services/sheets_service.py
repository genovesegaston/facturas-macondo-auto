from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

from models.batch_result import BatchResult
from models.invoice_data import InvoiceData
from models.validation_result import ValidationResult
from services.export_service import build_export_row


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@dataclass
class SheetsWriteResult:
    """
    Resultado de escritura en Google Sheets.
    """
    success: bool = False
    spreadsheet_id: str = ""
    worksheet_name: str = ""
    written_rows: int = 0
    error_message: str = ""

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "spreadsheet_id": self.spreadsheet_id,
            "worksheet_name": self.worksheet_name,
            "written_rows": self.written_rows,
            "error_message": self.error_message,
        }


def get_gspread_client(service_account_file: str | Path) -> gspread.Client:
    """
    Crea cliente autenticado de gspread a partir de una service account.
    """
    credentials = Credentials.from_service_account_file(
        str(service_account_file),
        scopes=SCOPES,
    )
    return gspread.authorize(credentials)


def open_worksheet(
    client: gspread.Client,
    spreadsheet_id: str,
    worksheet_name: str,
):
    """
    Abre una hoja específica dentro de una planilla.
    """
    spreadsheet = client.open_by_key(spreadsheet_id)
    return spreadsheet.worksheet(worksheet_name)


def ensure_headers(worksheet, headers: list[str]) -> None:
    """
    Garantiza que la primera fila tenga encabezados.
    Si la hoja está vacía, los crea.
    """
    values = worksheet.get_all_values()

    if not values:
        worksheet.append_row(headers)
        return

    first_row = values[0]
    if not first_row or all(not cell for cell in first_row):
        worksheet.update("A1", [headers])


def append_rows_to_worksheet(
    worksheet,
    rows: list[dict],
) -> int:
    """
    Inserta filas al final de la hoja.
    """
    if not rows:
        return 0

    headers = list(rows[0].keys())
    ensure_headers(worksheet, headers)

    values = []
    for row in rows:
        values.append([row.get(header, "") for header in headers])

    worksheet.append_rows(values, value_input_option="USER_ENTERED")
    return len(values)


def write_invoices_to_sheet(
    spreadsheet_id: str,
    worksheet_name: str,
    invoices: list[InvoiceData],
    validations: list[ValidationResult] | None = None,
    service_account_file: str | Path = "service_account.json",
) -> SheetsWriteResult:
    """
    Escribe invoices + validations en una hoja Google Sheets.
    """
    try:
        if validations is None:
            validations = [None] * len(invoices)

        rows = [
            build_export_row(invoice, validation)
            for invoice, validation in zip(invoices, validations)
        ]

        client = get_gspread_client(service_account_file)
        worksheet = open_worksheet(
            client=client,
            spreadsheet_id=spreadsheet_id,
            worksheet_name=worksheet_name,
        )

        written_rows = append_rows_to_worksheet(worksheet, rows)

        return SheetsWriteResult(
            success=True,
            spreadsheet_id=spreadsheet_id,
            worksheet_name=worksheet_name,
            written_rows=written_rows,
            error_message="",
        )

    except Exception as exc:
        return SheetsWriteResult(
            success=False,
            spreadsheet_id=spreadsheet_id,
            worksheet_name=worksheet_name,
            written_rows=0,
            error_message=f"Error al escribir en Google Sheets: {exc}",
        )


def write_batch_to_sheet(
    batch: BatchResult,
    spreadsheet_id: str,
    worksheet_name: str,
    service_account_file: str | Path = "service_account.json",
) -> SheetsWriteResult:
    """
    Escribe un BatchResult completo a Google Sheets.
    """
    return write_invoices_to_sheet(
        spreadsheet_id=spreadsheet_id,
        worksheet_name=worksheet_name,
        invoices=batch.invoices,
        validations=batch.validation_results,
        service_account_file=service_account_file,
    )