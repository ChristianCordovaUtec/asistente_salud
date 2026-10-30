
import uuid

from sqlalchemy import (
    CHAR,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app import db


class Paciente(db.Model):
    __tablename__ = "paciente"

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )

    nombres = db.Column(String(100), nullable=False)
    apellidos = db.Column(String(100), nullable=False)

    documento_pais = db.Column(CHAR(2), nullable=False)
    tipo_documento = db.Column(String(20), nullable=False)
    documento_numero = db.Column(String(30), nullable=False)

    fecha_nacimiento = db.Column(Date)
    sexo = db.Column(String(20))
    telefono = db.Column(String(30))

    activo = db.Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("TRUE")
    )

    fecha_registro = db.Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()")
    )

    __table_args__ = (
        CheckConstraint(
            "tipo_documento IN ('DNI', 'CE', 'PASAPORTE', 'OTRO')",
            name="ck_paciente_tipo_documento"
        ),
        UniqueConstraint(
            "documento_pais",
            "tipo_documento",
            "documento_numero",
            name="uq_paciente_documento"
        ),
    )

    # Relación con responsables
    pacientes_responsables = db.relationship(
        "PacienteResponsable",
        back_populates="paciente"
    )

    # Relación con perfiles corporales
    perfiles_corporales = db.relationship(
        "PerfilCorporal",
        back_populates="paciente"
    )

    # Relación con condiciones de salud
    condiciones = db.relationship(
        "CondicionPaciente",
        back_populates="paciente"
    )

    # Relación con lecturas de glucosa
    lecturas_glucometro = db.relationship(
        "LecturaGlucometro",
        back_populates="paciente"
    )

    # Configuración de alertas (una por paciente)
    configuracion_alertas_glucosa = db.relationship(
        "ConfiguracionAlertasGlucosa",
        back_populates="paciente",
        uselist=False       # cada paciente tiene una sola configuración de alertas
    )

    # Relación con alertas
    alertas = db.relationship(
        "Alerta",
        back_populates="paciente"
    )

    # Relación con notificaciones asociadas al paciente
    tratamientos_medicacion = db.relationship(
        "TratamientoMedicacion",
        back_populates="paciente"
    )
