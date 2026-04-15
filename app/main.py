from pathlib import Path

from core.config import (
    DEFAULT_EXPORT_SHEET_NAME,
    TESSERACT_CMD,
    POPPLER_PATH,
    USE_OCR_FALLBACK,
    ensure_storage_directories,
)
from core.paths import build_export_file_path
from services.batch_service import process_prepared_batch
from services.export_service import export_batch_to_excel


def print_section(title: str) -> None:
    print("\n" + "=" * 10 + f" {title} " + "=" * 10)


def print_batch_summary(batch) -> None:
    print_section("BATCH SUMMARY")
    summary = batch.to_summary_dict()
    for key, value in summary.items():
        print(f"{key}: {value}")


def print_invoices(batch) -> None:
    print_section("INVOICES")
    for idx, invoice in enumerate(batch.invoices, start=1):
        print(f"\n--- Invoice #{idx} ---")
        print(invoice.to_dict())


def print_validations(batch) -> None:
    print_section("VALIDATIONS")
    for idx, validation in enumerate(batch.validation_results, start=1):
        print(f"\n--- Validation #{idx} ---")
        print(validation.to_dict())


def print_logs(logs) -> None:
    print_section("LOGS")
    for log in logs:
        print(log.to_console_line())


def run_pipeline(
    file_paths: list[str],
    export_excel: bool = True,
) -> None:
    """
    Ejecuta el pipeline completo de punta a punta.
    """
    ensure_storage_directories()

    prep, batch, logs = process_prepared_batch(
        file_paths=file_paths,
        use_ocr_fallback=USE_OCR_FALLBACK,
        tesseract_cmd=TESSERACT_CMD,
        poppler_path=POPPLER_PATH,
    )

    print_section("BATCH PREPARATION")
    print(prep.to_dict())

    print_batch_summary(batch)
    print_invoices(batch)
    print_validations(batch)
    print_logs(logs)

    if export_excel:
        export_path = build_export_file_path("resultado_pipeline.xlsx", timestamp=True)
        export_result = export_batch_to_excel(
            batch=batch,
            export_path=export_path,
            sheet_name=DEFAULT_EXPORT_SHEET_NAME,
        )

        print_section("EXPORT RESULT")
        print(export_result.to_dict())


def main() -> None:
    """
    Punto de entrada inicial del proyecto.

    En esta etapa MVP se cargan manualmente rutas locales.
    Más adelante esto será reemplazado por:
    - selección múltiple desde UI
    - drag and drop
    - configuración dinámica
    """
    sample_files = [
        r"C:\Users\franc\OneDrive\Escritorio\facturas-macondo-auto\storage\samples\ejemplo.pdf",
        r"C:\Users\franc\OneDrive\Escritorio\facturas-macondo-auto\storage\samples\ejemplonc.pdf",
    ]

    run_pipeline(
        file_paths=sample_files,
        export_excel=True,
    )


if __name__ == "__main__":
    main()