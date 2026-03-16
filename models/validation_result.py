from dataclasses import dataclass, field, asdict


@dataclass
class ValidationResult:
    """
    Representa el resultado de la validación de negocio de una factura.

    Este modelo separa claramente:
    - los datos extraídos (InvoiceData)
    - el resultado de aplicar reglas de validación
    """

    is_valid: bool = False

    missing_fields: list[str] = field(default_factory=list)

    receiver_valid: bool = False
    amounts_valid: bool = False
    rounding_difference: float = 0.0

    duplicate_detected: bool = False
    duplicate_reference: str = ""
    duplicate_key: str = ""

    confidence_level: str = ""

    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    system_notes: str = ""

    def add_warning(self, message: str) -> None:
        """
        Agrega una advertencia si no existe ya.
        """
        if message and message not in self.warnings:
            self.warnings.append(message)

    def add_error(self, message: str) -> None:
        """
        Agrega un error si no existe ya.
        """
        if message and message not in self.errors:
            self.errors.append(message)

    def add_missing_field(self, field_name: str) -> None:
        """
        Registra un campo faltante si no existe ya.
        """
        if field_name and field_name not in self.missing_fields:
            self.missing_fields.append(field_name)

    def build_system_notes(self) -> str:
        """
        Consolida warnings y errors en un texto breve para mostrar
        en tablas, logs o exportaciones.
        """
        parts: list[str] = []

        if self.missing_fields:
            parts.append(f"Campos faltantes: {', '.join(self.missing_fields)}")

        if self.warnings:
            parts.append(f"Warnings: {' | '.join(self.warnings)}")

        if self.errors:
            parts.append(f"Errors: {' | '.join(self.errors)}")

        self.system_notes = " || ".join(parts)
        return self.system_notes

    def evaluate_validity(self) -> bool:
        """
        Determina si la validación general puede considerarse satisfactoria.

        Regla inicial:
        - no debe haber errores
        - no debe haber faltantes críticos sin resolver
        - receptor debe ser válido
        - importes deben ser válidos
        - no invalida por duplicado automáticamente, porque eso puede requerir decisión del usuario
        """
        self.is_valid = (
            len(self.errors) == 0
            and len(self.missing_fields) == 0
            and self.receiver_valid
            and self.amounts_valid
        )
        return self.is_valid

    def to_dict(self) -> dict:
        """
        Convierte el modelo a diccionario serializable.
        """
        return asdict(self)