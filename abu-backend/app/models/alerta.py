import uuid

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app import db


class Alerta(db.Model):
    __tablename__ = "alerta"

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

    lectura_id = db.Column(
        UUID(as_uuid=True),
        ForeignKey("lectura_glucometro.id")
    )

    tipo = db.Column(String(30), nullable=False)
    descripcion = db.Column(Text, nullable=False)
    valor_detectado = db.Column(Numeric(6, 2))

    estado = db.Column(
        String(20),
        nullable=False,
        default="pendiente",
        server_default=text("'pendiente'")
    )

    fecha_registro = db.Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()")
    )

    lectura = db.relationship(
        "LecturaGlucometro",
        back_populates="alertas"
    )

    paciente = db.relationship(
        "Paciente",
        back_populates="alertas"
    )

    __table_args__ = (
        CheckConstraint(
            "tipo IN ('umbral_glucosa', 'tendencia_glucosa')",
            name="ck_alerta_tipo"
        ),
        CheckConstraint(
            "estado IN ('pendiente', 'atendida', 'cerrada')",
            name="ck_alerta_estado"
        ),
        CheckConstraint(
            "valor_detectado IS NULL OR valor_detectado > 0",
            name="ck_alerta_valor_detectado"
        ),
    )

    # Relación con notificaciones asociadas a la alerta
    notificaciones = db.relationship(
        "Notificacion",
        back_populates="alerta"
    )
