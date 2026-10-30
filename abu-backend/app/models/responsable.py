
import uuid

from sqlalchemy import Boolean, DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID

from app import db


class Responsable(db.Model):
    __tablename__ = "responsable"

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )

    nombres = db.Column(String(100), nullable=False)
    apellidos = db.Column(String(100), nullable=False)
    telefono = db.Column(String(30), nullable=False)
    email = db.Column(String(150))

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

    # Relación con pacientes
    pacientes_responsables = db.relationship(
        "PacienteResponsable",
        back_populates="responsable"
    )
