import uuid

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app import db


class TratamientoMedicacion(db.Model):
    __tablename__ = "tratamientos_medicacion"

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

    nombre_medicamento = db.Column(String(150), nullable=False)
    dosis_valor = db.Column(Numeric(10, 2), nullable=False)
    dosis_unidad = db.Column(String(50), nullable=False)

    fecha_inicio = db.Column(Date, nullable=False)
    fecha_fin = db.Column(Date, nullable=False)

    estado = db.Column(
        String(20),
        nullable=False,
        default="pendiente",
        server_default=text("'pendiente'")
    )

    fecha_confirmacion = db.Column(DateTime(timezone=True))

    observaciones = db.Column(Text)

    created_at = db.Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()")
    )

    updated_at = db.Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()")
    )

    paciente = db.relationship(
        "Paciente",
        back_populates="tratamientos_medicacion"
    )

    horarios = db.relationship(
        "HorarioMedicacion",
        back_populates="tratamiento",
        cascade="all, delete-orphan"
    )

    ejecuciones = db.relationship(
        "EjecucionRecordatorio",
        back_populates="tratamiento"
    )

    __table_args__ = (
        CheckConstraint(
            """
            estado IN (
                'pendiente', 'activo', 'pausado',
                'completado', 'cancelado'
            )
            """,
            name="ck_tratamientos_medicacion_estado"
        ),
        CheckConstraint(
            "dosis_valor > 0",
            name="ck_tratamientos_medicacion_dosis"
        ),
        CheckConstraint(
            "fecha_fin >= fecha_inicio",
            name="ck_tratamientos_medicacion_fechas"
        ),
    )
