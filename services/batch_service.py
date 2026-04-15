from dataclasses import dataclass, field
from pathlib import Path

from models.processing_log import ProcessingLog
from services.processing_service import process_batch


SUPPORTED_EXTENSIONS = {".pdf"}


@dataclass
class BatchPreparationResult:
    """
    Resultado de preparación de lote antes del procesamiento.
    """
    valid_files: list[str] = field(default_factory=list)
    invalid_files: list[str] = field(default_factory=list)
    skipped_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "valid_files": self.valid_files,
            "invalid_files": self.invalid_files,
            "skipped_files": self.skipped_files,
        }


def normalize_file_paths(file_paths: list[str | Path]) -> list[Path]:
    """
    Normaliza rutas de entrada a objetos Path.
    """
    return [Path(p) for p in file_paths]


def classify_file_paths(file_paths: list[str | Path]) -> BatchPreparationResult:
    """
    Clasifica archivos del lote según:
    - existencia
    - tipo soportado
    """
    result = BatchPreparationResult()
    normalized_paths = normalize_file_paths(file_paths)

    seen: set[str] = set()

    for path in normalized_paths:
        path_str = str(path.resolve()) if path.exists() else str(path)

        if path_str in seen:
            result.skipped_files.append(path_str)
            continue

        seen.add(path_str)

        if not path.exists() or not path.is_file():
            result.invalid_files.append(path_str)
            continue

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            result.invalid_files.append(path_str)
            continue

        result.valid_files.append(path_str)

    return result


def process_prepared_batch(
    file_paths: list[str | Path],
    existing_keys=None,
    existing_records=None,
    use_ocr_fallback: bool = True,
    tesseract_cmd: str | None = None,
    poppler_path: str | None = None,
):
    """
    Prepara y procesa un lote de archivos válidos.
    """
    prep = classify_file_paths(file_paths)

    batch, logs = process_batch(
        file_paths=prep.valid_files,
        existing_keys=existing_keys,
        existing_records=existing_records,
        use_ocr_fallback=use_ocr_fallback,
        tesseract_cmd=tesseract_cmd,
        poppler_path=poppler_path,
    )

    return prep, batch, logs


def build_batch_preparation_logs(preparation: BatchPreparationResult) -> list[ProcessingLog]:
    """
    Genera logs simples de preparación de lote.
    """
    logs: list[ProcessingLog] = []

    for path in preparation.valid_files:
        logs.append(
            ProcessingLog(
                timestamp=__import__("datetime").datetime.now(),
                level="INFO",
                event_type="BATCH_FILE_ACCEPTED",
                file_name=Path(path).name,
                file_path=path,
                message="Archivo aceptado para procesamiento.",
            )
        )

    for path in preparation.invalid_files:
        logs.append(
            ProcessingLog(
                timestamp=__import__("datetime").datetime.now(),
                level="WARNING",
                event_type="BATCH_FILE_INVALID",
                file_name=Path(path).name,
                file_path=path,
                message="Archivo inválido o no soportado.",
            )
        )

    for path in preparation.skipped_files:
        logs.append(
            ProcessingLog(
                timestamp=__import__("datetime").datetime.now(),
                level="INFO",
                event_type="BATCH_FILE_SKIPPED",
                file_name=Path(path).name,
                file_path=path,
                message="Archivo omitido por duplicación de ruta.",
            )
        )

    return logs