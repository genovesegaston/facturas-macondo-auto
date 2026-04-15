from dataclasses import dataclass
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials


DEFAULT_GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@dataclass
class GoogleAuthResult:
    """
    Resultado simple de autenticación Google.
    """
    success: bool
    credentials_path: str = ""
    scopes: list[str] | None = None
    error_message: str = ""

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "credentials_path": self.credentials_path,
            "scopes": self.scopes or [],
            "error_message": self.error_message,
        }


def validate_service_account_file(service_account_file: str | Path) -> Path:
    """
    Valida que exista el archivo de credenciales.
    """
    path = Path(service_account_file)

    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo de credenciales: {path}")

    if not path.is_file():
        raise ValueError(f"La ruta de credenciales no es un archivo válido: {path}")

    if path.suffix.lower() != ".json":
        raise ValueError(f"El archivo de credenciales debe ser .json: {path}")

    return path


def load_google_credentials(
    service_account_file: str | Path,
    scopes: list[str] | None = None,
) -> Credentials:
    """
    Carga credenciales Google desde service account.
    """
    path = validate_service_account_file(service_account_file)
    scopes = scopes or DEFAULT_GOOGLE_SCOPES

    return Credentials.from_service_account_file(
        str(path),
        scopes=scopes,
    )


def build_gspread_client(
    service_account_file: str | Path,
    scopes: list[str] | None = None,
) -> gspread.Client:
    """
    Construye cliente autenticado de gspread.
    """
    credentials = load_google_credentials(
        service_account_file=service_account_file,
        scopes=scopes,
    )
    return gspread.authorize(credentials)


def test_google_auth(
    service_account_file: str | Path,
    scopes: list[str] | None = None,
) -> GoogleAuthResult:
    """
    Prueba que el archivo de credenciales sea utilizable.
    """
    try:
        path = validate_service_account_file(service_account_file)
        scopes = scopes or DEFAULT_GOOGLE_SCOPES
        _ = load_google_credentials(path, scopes=scopes)

        return GoogleAuthResult(
            success=True,
            credentials_path=str(path),
            scopes=scopes,
            error_message="",
        )

    except Exception as exc:
        return GoogleAuthResult(
            success=False,
            credentials_path=str(service_account_file),
            scopes=scopes or DEFAULT_GOOGLE_SCOPES,
            error_message=f"Error de autenticación Google: {exc}",
        )