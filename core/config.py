from pathlib import Path


# =========================
# Proyecto
# =========================

PROJECT_NAME = "facturas-macondo-auto"
PROJECT_VERSION = "0.1.0"


# =========================
# Base paths
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
LOGS_DIR = STORAGE_DIR / "logs"
TEMP_DIR = STORAGE_DIR / "temp"
EXPORTS_DIR = STORAGE_DIR / "exports"
SAMPLES_DIR = STORAGE_DIR / "samples"


# =========================
# OCR / PDF
# =========================
# Trazabilidad acordada previamente:
# estas rutas quedan centralizadas aquí y NO deben hardcodearse en otros módulos.

TESSERACT_CMD = r"C:\Program Files\Tesseract-OCRC\tesseract.exe"
POPPLER_PATH = r"C:\poppler\Library\bin"
OCR_LANGUAGE = "spa"
OCR_DPI = 300
USE_OCR_FALLBACK = True


# =========================
# Validación de negocio
# =========================

ROUNDING_TOLERANCE = 1.0
EXPECTED_RECEIVER_NAME = "MACONDO SRL"
EXPECTED_RECEIVER_CUIT = "30708762233"


# =========================
# Google Sheets / Google Auth
# =========================

SERVICE_ACCOUNT_FILE = BASE_DIR / "service_account.json"
DEFAULT_SPREADSHEET_ID = ""
DEFAULT_WORKSHEET_NAME = "FACTURAS"


# =========================
# Exportación
# =========================

DEFAULT_EXPORT_FILENAME = "resultado_procesamiento.xlsx"
DEFAULT_EXPORT_PATH = EXPORTS_DIR / DEFAULT_EXPORT_FILENAME
DEFAULT_EXPORT_SHEET_NAME = "Resultados"


# =========================
# Procesamiento
# =========================

SUPPORTED_EXTENSIONS = {".pdf"}
DEFAULT_BATCH_CREATE_MISSING_SHEET = True


# =========================
# Helpers
# =========================

def ensure_storage_directories() -> None:
    """
    Garantiza que existan las carpetas base del proyecto.
    """
    for path in [STORAGE_DIR, LOGS_DIR, TEMP_DIR, EXPORTS_DIR, SAMPLES_DIR]:
        path.mkdir(parents=True, exist_ok=True)