from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

from models.document import Document
from models.invoice_data import InvoiceData
from models.validation_result import ValidationResult


@dataclass
class BatchResult:
    """
    Representa el resultado de una ejecución masiva del sistema.

    Un batch agrupa:
    - documentos recibidos
    - facturas extraídas
    - resultados de validación
    - métricas de procesamiento
    - errores resumidos
    """

    batch_id: str
    started_at: datetime

    finished_at: Optional[datetime] = None

    total_files: int = 0
    processed_files: int = 0
    successful_files: int = 0
    error_files: int = 0

    documents: list[Document] = field(default_factory=list)
    invoices: list[InvoiceData] = field(default_factory=list)
    validation_results: list[ValidationResult] = field(default_factory=list)

    export_path: str = ""
    errors_summary: list[str] = field(default_factory=list)

    def add_document(self, document: Document) -> None:
        self.documents.append(document)
        self.total_files = len(self.documents)

    def add_invoice(self, invoice: InvoiceData) -> None:
        self.invoices.append(invoice)

    def add_validation_result(self, result: ValidationResult) -> None:
        self.validation_results.append(result)

    def add_error(self, message: str) -> None:
        if message:
            self.errors_summary.append(message)
            self.error_files += 1

    def increment_processed(self) -> None:
        self.processed_files += 1

    def increment_successful(self) -> None:
        self.successful_files += 1

    def finish(self) -> None:
        """
        Marca el batch como finalizado.
        """
        self.finished_at = datetime.now()

    @property
    def pending_files(self) -> int:
        return max(self.total_files - self.processed_files, 0)

    @property
    def success_rate(self) -> float:
        if self.total_files == 0:
            return 0.0
        return round((self.successful_files / self.total_files) * 100, 2)

    def recalculate_metrics(self) -> None:
        """
        Recalcula métricas generales del batch a partir del estado actual.
        Útil cuando los elementos fueron agregados manualmente o por distintos servicios.
        """
        self.total_files = len(self.documents)
        self.processed_files = len(self.validation_results)

        successful = 0
        errors = 0

        for result in self.validation_results:
            if result.is_valid:
                successful += 1
            else:
                errors += 1

        self.successful_files = successful
        self.error_files = errors

    def to_dict(self) -> dict:
        """
        Convierte el batch a un diccionario serializable.
        """
        return {
            "batch_id": self.batch_id,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "successful_files": self.successful_files,
            "error_files": self.error_files,
            "pending_files": self.pending_files,
            "success_rate": self.success_rate,
            "documents": [doc.to_dict() for doc in self.documents],
            "invoices": [inv.to_dict() for inv in self.invoices],
            "validation_results": [res.to_dict() for res in self.validation_results],
            "export_path": self.export_path,
            "errors_summary": self.errors_summary,
        }

    def to_summary_dict(self) -> dict:
        """
        Devuelve un resumen liviano del batch para mostrar en UI,
        logs o reportes rápidos.
        """
        return {
            "batch_id": self.batch_id,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else "",
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "successful_files": self.successful_files,
            "error_files": self.error_files,
            "pending_files": self.pending_files,
            "success_rate": self.success_rate,
            "export_path": self.export_path,
        }