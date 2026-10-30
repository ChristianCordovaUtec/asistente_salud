
from sqlalchemy import SmallInteger, String

from app import db


class TipoCondicion(db.Model):
    __tablename__ = "tipo_condicion"

    id = db.Column(
        SmallInteger,
        primary_key=True,
        autoincrement=True
    )

    nombre = db.Column(String(80), nullable=False, unique=True)

    condiciones_pacientes = db.relationship(
        "CondicionPaciente",
        back_populates="tipo_condicion"
    )
