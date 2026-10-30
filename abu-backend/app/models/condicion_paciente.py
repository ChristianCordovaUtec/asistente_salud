
import uuid

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app import db


class CondicionPaciente(db.Model):
    __tablename__ = "condicion_paciente"

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

    tipo_condicion_id = db.Column(
        SmallInteger,
        ForeignKey("tipo_condicion.id"),
        nullable=False
    )

    estado = db.Column(String(20), nullable=False)

    fuente = db.Column(Text)
    fecha_diagnosticada = db.Column(Date)

    fecha_actualizada = db.Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()")
    )

    paciente = db.relationship(
        "Paciente",
        back_populates="condiciones"
    )

    tipo_condicion = db.relationship(
        "TipoCondicion",
        back_populates="condiciones_pacientes"
    )

    __table_args__ = (
        CheckConstraint(
            "estado IN ('activa', 'controlada', 'en_remision', 'inactiva')",
            name="ck_condicion_paciente_estado"
        ),
        UniqueConstraint(
            "paciente_id",
            "tipo_condicion_id",
            name="uq_paciente_tipo_condicion"
        ),
    )
