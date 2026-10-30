import uuid

from sqlalchemy import Boolean, ForeignKey, Time, DateTime, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID

from app import db


class HorarioMedicacion(db.Model):
    __tablename__ = "horarios_medicacion"

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )

    tratamiento_id = db.Column(
        UUID(as_uuid=True),
        ForeignKey("tratamientos_medicacion.id", ondelete="CASCADE"),
        nullable=False
    )

    hora = db.Column(Time, nullable=False)

    activo = db.Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("TRUE")
    )

    created_at = db.Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()")
    )

    tratamiento = db.relationship(
        "TratamientoMedicacion",
        back_populates="horarios"
    )

    __table_args__ = (
        UniqueConstraint(
            "tratamiento_id",
            "hora",
            name="uq_horarios_medicacion_tratamiento_hora"
        ),
    )
