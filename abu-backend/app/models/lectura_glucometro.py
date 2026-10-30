import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID

from app import db


class LecturaGlucometro(db.Model):
    __tablename__ = "lectura_glucometro"

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

    valor_ocr = db.Column(Numeric(6, 2), nullable=False)
    valor_confirmado = db.Column(Numeric(6, 2), nullable=False)

    unidad = db.Column(
        String(10),
        nullable=False,
        default="mg/dL",
        server_default=text("'mg/dL'")
    )

    fecha_medicion = db.Column(DateTime(timezone=True), nullable=False)

    fecha_registro = db.Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()")
    )

    paciente = db.relationship(
        "Paciente",
        back_populates="lecturas_glucometro"
    )

    alertas = db.relationship(
        "Alerta",
        back_populates="lectura"
    )

    __table_args__ = (
        CheckConstraint(
            "unidad IN ('mg/dL', 'mmol/L')",
            name="ck_lectura_glucometro_unidad"
        ),
        CheckConstraint(
            "valor_ocr > 0",
            name="ck_lectura_glucometro_valor_ocr"
        ),
        CheckConstraint(
            "valor_confirmado > 0",
            name="ck_lectura_glucometro_valor_confirmado"
        ),
    )