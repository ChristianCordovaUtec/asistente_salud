import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app import db


class ConfiguracionAlertasGlucosa(db.Model):
    __tablename__ = "configuracion_alertas_glucosa"

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

    umbral_minimo = db.Column(Numeric(6, 2))
    umbral_maximo = db.Column(Numeric(6, 2))

    unidad = db.Column(
        String(10),
        nullable=False,
        default="mg/dL",
        server_default=text("'mg/dL'")
    )

    detectar_tendencia = db.Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("FALSE")
    )

    dias_analisis = db.Column(
        SmallInteger,
        nullable=False,
        default=4,
        server_default=text("4")
    )

    activa = db.Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("TRUE")
    )

    fecha_actualizacion = db.Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()")
    )

    paciente = db.relationship(
        "Paciente",
        back_populates="configuracion_alertas_glucosa"
    )

    __table_args__ = (
        UniqueConstraint(
            "paciente_id",
            name="uq_configuracion_alertas_paciente"
        ),
        CheckConstraint(
            "unidad IN ('mg/dL', 'mmol/L')",
            name="ck_configuracion_alertas_unidad"
        ),
        CheckConstraint(
            """
            (umbral_minimo IS NULL OR umbral_minimo > 0)
            AND (umbral_maximo IS NULL OR umbral_maximo > 0)
            AND (
                umbral_minimo IS NULL
                OR umbral_maximo IS NULL
                OR umbral_minimo < umbral_maximo
            )
            """,
            name="ck_configuracion_alertas_umbrales"
        ),
        CheckConstraint(
            """
            (detectar_tendencia = FALSE AND dias_analisis = 4)
            OR (detectar_tendencia = TRUE AND dias_analisis >= 1)
            """,
            name="ck_configuracion_alertas_dias"
        ),
    )