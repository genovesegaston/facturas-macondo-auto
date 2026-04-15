from pathlib import Path
from datetime import datetime

from core.config import (
    BASE_DIR,
    STORAGE_DIR,
    LOGS_DIR,
    TEMP_DIR,
    EXPORTS_DIR,
    SAMPLES_DIR,
    DEFAULT_EXPORT_FILENAME,
)


# =========================
# Rutas base expuestas
# =========================

PROJECT_ROOT = BASE_DIR
PROJECT_STORAGE = STORAGE_DIR
PROJECT_LOGS = LOGS_DIR
PROJECT_TEMP = TEMP_DIR
PROJECT_EXPORTS = EXPORTS_DIR
PROJECT_SAMPLES = SAMPLES_DIR


# =========================
# Helpers de directorios
# =========================

def ensure_directory(path: str | Path) -> Path:
    """
    Garantiza que exista un directorio y devuelve Path.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_project_directories() -> None:
    """
    Garantiza que existan las carpetas principales del proyecto.
    """
    for path in [
        PROJECT_STORAGE,
        PROJECT_LOGS,
        PROJECT_TEMP,
        PROJECT_EXPORTS,
        PROJECT_SAMPLES,
    ]:
        ensure_directory(path)


# =========================
# Helpers de archivos
# =========================

def build_export_file_path(
    file_name: str | None = None,
    timestamp: bool = False,
) -> Path:
    """
    Construye una ruta de exportación dentro de storage/exports.

    Parámetros:
    - file_name: nombre del archivo
    - timestamp: si True, agrega timestamp al nombre
    """
    ensure_directory(PROJECT_EXPORTS)

    if not file_name:
        file_name = DEFAULT_EXPORT_FILENAME

    file_path = Path(file_name)

    if timestamp:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = file_path.stem
        suffix = file_path.suffix or ".xlsx"
        file_name = f"{stem}_{stamp}{suffix}"

    return PROJECT_EXPORTS / file_name


def build_log_file_path(
    file_name: str = "processing.log",
    timestamp: bool = False,
) -> Path:
    """
    Construye una ruta de log dentro de storage/logs.
    """
    ensure_directory(PROJECT_LOGS)

    file_path = Path(file_name)

    if timestamp:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = file_path.stem
        suffix = file_path.suffix or ".log"
        file_name = f"{stem}_{stamp}{suffix}"

    return PROJECT_LOGS / file_name


def build_temp_file_path(
    file_name: str,
) -> Path:
    """
    Construye una ruta temporal dentro de storage/temp.
    """
    ensure_directory(PROJECT_TEMP)
    return PROJECT_TEMP / file_name


def build_sample_file_path(
    file_name: str,
) -> Path:
    """
    Construye una ruta dentro de storage/samples.
    """
    ensure_directory(PROJECT_SAMPLES)
    return PROJECT_SAMPLES / file_name