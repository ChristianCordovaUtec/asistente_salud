
import uuid

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app import db


class PerfilCorporal(db.Model):
    __tablename__ = "perfil_corporal"

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

    peso_kg = db.Column(Numeric(6, 2))
    altura_cm = db.Column(Numeric(6, 2))
    horas_sueno_promedio = db.Column(Numeric(4, 2))

    fecha_registro = db.Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()")
    )

    paciente = db.relationship(
        "Paciente",
        back_populates="perfiles_corporales"
    )

    __table_args__ = (
        CheckConstraint(
            "peso_kg IS NULL OR peso_kg > 0",
            name="ck_perfil_peso"
        ),
        CheckConstraint(
            "altura_cm IS NULL OR altura_cm > 0",
            name="ck_perfil_altura"
        ),
        CheckConstraint(
            "horas_sueno_promedio IS NULL OR "
            "horas_sueno_promedio BETWEEN 0 AND 24",
            name="ck_perfil_sueno"
        ),
    )
