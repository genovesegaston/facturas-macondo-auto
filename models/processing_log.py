from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


@dataclass
class ProcessingLog:
    """
    Representa un evento estructurado de log del sistema.

    Se utilizará para:
    - trazabilidad del procesamiento
    - debugging
    - auditoría técnica
    - historial por lote o por documento
    """

    timestamp: datetime
    level: str
    event_type: str

    file_name: str = ""
    file_path: str = ""
    document_id: str = ""
    batch_id: str = ""

    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    user: str = ""

    def to_dict(self) -> dict:
        """
        Convierte el log a un diccionario serializable.
        """
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    def to_console_line(self) -> str:
        """
        Devuelve una representación compacta para impresión en consola.
        """
        return (
            f"[{self.timestamp.isoformat()}] "
            f"[{self.level}] "
            f"[{self.event_type}] "
            f"{self.message}"
        )

    def to_summary_dict(self) -> dict:
        """
        Devuelve un resumen liviano del evento.
        """
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "event_type": self.event_type,
            "file_name": self.file_name,
            "document_id": self.document_id,
            "batch_id": self.batch_id,
            "message": self.message,
            "user": self.user,
        }