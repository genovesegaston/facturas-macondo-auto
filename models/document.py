from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4


@dataclass
class Document:
    """
    Representa un documento fuente que ingresa al sistema antes de ser parseado.

    Este modelo almacena:
    - información básica del archivo
    - estado técnico del procesamiento
    - texto extraído y texto limpio
    - indicadores de detección sobre el PDF
    - metadatos temporales del flujo
    """

    file_path: Path
    source_type: str = "local"

    document_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None

    file_name: str = field(init=False)
    extension: str = field(init=False)
    file_size: int = field(init=False, default=0)

    mime_type: str = ""
    text_content: str = ""
    clean_text: str = ""

    is_pdf: bool = field(init=False, default=False)
    is_scanned: bool = False
    has_extractable_text: bool = False

    status: str = "pending"
    error_message: str = ""

    def __post_init__(self) -> None:
        self.file_path = Path(self.file_path)
        self.file_name = self.file_path.name
        self.extension = self.file_path.suffix.lower()
        self.is_pdf = self.extension == ".pdf"

        if self.file_path.exists() and self.file_path.is_file():
            self.file_size = self.file_path.stat().st_size
        else:
            self.file_size = 0

    @property
    def exists(self) -> bool:
        """Indica si el archivo existe físicamente en disco."""
        return self.file_path.exists() and self.file_path.is_file()

    @property
    def stem(self) -> str:
        """Nombre del archivo sin extensión."""
        return self.file_path.stem

    @property
    def parent_dir(self) -> Path:
        """Directorio padre del archivo."""
        return self.file_path.parent

    def set_raw_text(self, text: Optional[str]) -> None:
        """Guarda el texto extraído bruto."""
        self.text_content = text or ""
        self.has_extractable_text = bool(self.text_content.strip())

    def set_clean_text(self, text: Optional[str]) -> None:
        """Guarda el texto limpio/normalizado."""
        self.clean_text = text or ""

    def mark_as_scanned(self, value: bool = True) -> None:
        """Marca el documento como escaneado."""
        self.is_scanned = value

    def mark_status(self, status: str, error_message: str = "") -> None:
        """
        Actualiza el estado del documento y opcionalmente el mensaje de error.

        Ejemplos de estados:
        - pending
        - loaded
        - extracted
        - parsed
        - validated
        - error
        """
        self.status = status
        self.error_message = error_message
        self.processed_at = datetime.now()

    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario serializable."""
        return {
            "document_id": self.document_id,
            "file_path": str(self.file_path),
            "file_name": self.file_name,
            "extension": self.extension,
            "file_size": self.file_size,
            "source_type": self.source_type,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "mime_type": self.mime_type,
            "text_content": self.text_content,
            "clean_text": self.clean_text,
            "is_pdf": self.is_pdf,
            "is_scanned": self.is_scanned,
            "has_extractable_text": self.has_extractable_text,
            "status": self.status,
            "error_message": self.error_message,
        }