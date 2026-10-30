import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID

from app import db


class Notificacion(db.Model):
    __tablename__ = "notificacion"

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )

    alerta_id = db.Column(
        UUID(as_uuid=True),
        ForeignKey("alerta.id"),
        nullable=False
    )

    paciente_responsable_id = db.Column(
        UUID(as_uuid=True),
        ForeignKey("paciente_responsable.id"),
        nullable=False
    )

    canal = db.Column(String(20), nullable=False)
    destinatario = db.Column(String(150), nullable=False)
    mensaje = db.Column(Text, nullable=False)

    estado = db.Column(
        String(20),
        nullable=False,
        default="pendiente",
        server_default=text("'pendiente'")
    )

    proveedor = db.Column(String(50))
    proveedor_mensaje_id = db.Column(String(150))

    fecha_registro = db.Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()")
    )

    fecha_envio = db.Column(DateTime(timezone=True))
    fecha_entrega = db.Column(DateTime(timezone=True))

    error_detalle = db.Column(Text)

    alerta = db.relationship(
        "Alerta",
        back_populates="notificaciones"
    )

    paciente_responsable = db.relationship(
        "PacienteResponsable",
        back_populates="notificaciones"
    )

    __table_args__ = (
        CheckConstraint(
            "canal IN ('whatsapp', 'email', 'web')",
            name="ck_notificacion_canal"
        ),
        CheckConstraint(
            "estado IN ('pendiente', 'enviada', 'entregada', 'fallida')",
            name="ck_notificacion_estado"
        ),
    )
