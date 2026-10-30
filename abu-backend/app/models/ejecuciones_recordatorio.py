import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID

from app import db


class EjecucionRecordatorio(db.Model):
    __tablename__ = "ejecuciones_recordatorio"

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )

    tratamiento_id = db.Column(
        UUID(as_uuid=True),
        ForeignKey("tratamientos_medicacion.id"),
        nullable=False
    )

    fecha_hora_programada = db.Column(
        DateTime(timezone=True),
        nullable=False
    )

    estado = db.Column(
        String(20),
        nullable=False,
        default="pendiente",
        server_default=text("'pendiente'")
    )

    fecha_notificacion = db.Column(DateTime(timezone=True))
    fecha_toma = db.Column(DateTime(timezone=True))

    observaciones = db.Column(Text)

    created_at = db.Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()")
    )

    tratamiento = db.relationship(
        "TratamientoMedicacion",
        back_populates="ejecuciones"
    )

    __table_args__ = (
        CheckConstraint(
            """
            estado IN (
                'pendiente', 'notificado', 'tomado',
                'omitido', 'fallido'
            )
            """,
            name="ck_ejecuciones_recordatorio_estado"
        ),
        UniqueConstraint(
            "tratamiento_id",
            "fecha_hora_programada",
            name="uq_ejecuciones_recordatorio_tratamiento_fecha"
        ),
    )
