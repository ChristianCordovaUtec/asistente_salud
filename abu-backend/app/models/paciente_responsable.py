
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app import db


class PacienteResponsable(db.Model):
    __tablename__ = "paciente_responsable"

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )

    paciente_id = db.Column(
        UUID(as_uuid=True),
        ForeignKey("paciente.id"),
        nullable=False
    )

    responsable_id = db.Column(
        UUID(as_uuid=True),
        ForeignKey("responsable.id"),
        nullable=False
    )

    tipo_relacion = db.Column(String(50), nullable=False)
    tipo_relacion_otro = db.Column(String(100))

    puede_ver = db.Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("TRUE")
    )

    puede_editar = db.Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE")
    )

    desde = db.Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()")
    )

    hasta = db.Column(DateTime(timezone=True))

    # Relaciones ORM
    paciente = db.relationship(
        "Paciente",
        back_populates="pacientes_responsables"
    )

    responsable = db.relationship(
        "Responsable",
        back_populates="pacientes_responsables"
    )

    __table_args__ = (
        UniqueConstraint(
            "paciente_id",
            "responsable_id",
            name="uq_paciente_responsable"
        ),
        CheckConstraint(
            "hasta IS NULL OR hasta >= desde",
            name="ck_paciente_responsable_fechas"
        ),
    )

    # Relación con notificaciones asociadas al paciente responsable
    notificaciones = db.relationship(
        "Notificacion",
        back_populates="paciente_responsable"
    )
