
from datetime import datetime, timezone
from flask import Blueprint, request

from app import db
from app.models import Paciente, LecturaGlucometro


lecturas_bp = Blueprint("lecturas_glucometro", __name__)

UNIDADES_VALIDAS = {"mg/dL", "mmol/L"}


# ---------------------------------------------------------
# SERIALIZADORES
# ---------------------------------------------------------

def serializar_lectura(lectura):
    return {
        "id": str(lectura.id),
        "paciente_id": str(lectura.paciente_id),
        "valor_ocr": float(lectura.valor_ocr),
        "valor_confirmado": float(lectura.valor_confirmado),
        "unidad": lectura.unidad,
        "fecha_medicion": (
            lectura.fecha_medicion.isoformat()
            if lectura.fecha_medicion else None
        ),
        "fecha_registro": (
            lectura.fecha_registro.isoformat()
            if lectura.fecha_registro else None
        )
    }


# ---------------------------------------------------------
# VALIDACIONES
# ---------------------------------------------------------

def validar_lectura(data):
    campos_obligatorios = [
        "valor_ocr",
        "valor_confirmado",
        "unidad",
        "fecha_medicion"
    ]

    for campo in campos_obligatorios:
        if campo not in data or data[campo] is None:
            return f"El campo {campo} es obligatorio."

    for campo in ("valor_ocr", "valor_confirmado"):
        valor = data[campo]

        if isinstance(valor, bool):
            return f"El campo {campo} debe ser numérico."

        try:
            valor = float(valor)
        except (ValueError, TypeError):
            return f"El campo {campo} debe ser numérico."

        if valor <= 0:
            return f"El campo {campo} debe ser mayor que cero."

    if data["unidad"] not in UNIDADES_VALIDAS:
        return "La unidad debe ser mg/dL o mmol/L."

    try:
        fecha = datetime.fromisoformat(
            data["fecha_medicion"].replace("Z", "+00:00")
        )

        if fecha.tzinfo is None or fecha.utcoffset() is None:
            return "fecha_medicion debe incluir zona horaria."

    except (ValueError, TypeError, AttributeError):
        return "fecha_medicion debe tener un formato ISO 8601 válido."

    return None


# ---------------------------------------------------------
# LECTURAS DE GLUCOMETRO
# ---------------------------------------------------------

# POST: registrar lectura de glucómetro
@lecturas_bp.route(
    "/api/pacientes/<uuid:paciente_id>/lecturas-glucometro",
    methods=["POST"]
)
def crear_lectura(paciente_id):
    paciente = db.session.get(Paciente, paciente_id)

    if not paciente or not paciente.activo:
        return {"error": "El paciente no existe o está inactivo."}, 404

    data = request.get_json(silent=True) or {}

    error = validar_lectura(data)
    if error:
        return {"error": error}, 400

    fecha_medicion = datetime.fromisoformat(
        data["fecha_medicion"].replace("Z", "+00:00")
    )

    lectura = LecturaGlucometro(
        paciente_id=paciente_id,
        valor_ocr=data["valor_ocr"],
        valor_confirmado=data["valor_confirmado"],
        unidad=data["unidad"],
        fecha_medicion=fecha_medicion
    )

    try:
        db.session.add(lectura)
        db.session.commit()
        db.session.refresh(lectura)

        return serializar_lectura(lectura), 201

    except Exception:
        db.session.rollback()
        raise


# GET: consultar historial de lecturas de un paciente
@lecturas_bp.route(
    "/api/pacientes/<uuid:paciente_id>/lecturas-glucometro",
    methods=["GET"]
)
def listar_lecturas(paciente_id):
    paciente = db.session.get(Paciente, paciente_id)

    if not paciente:
        return {"error": "El paciente no existe."}, 404

    lecturas = db.session.execute(
        db.select(LecturaGlucometro)
        .where(LecturaGlucometro.paciente_id == paciente_id)
        .order_by(LecturaGlucometro.fecha_medicion.desc())
    ).scalars().all()

    return {
        "total": len(lecturas),
        "lecturas": [serializar_lectura(l) for l in lecturas]
    }, 200


# GET: consultar una lectura específica
@lecturas_bp.route(
    "/api/lecturas-glucometro/<uuid:lectura_id>",
    methods=["GET"]
)
def obtener_lectura(lectura_id):
    lectura = db.session.get(LecturaGlucometro, lectura_id)

    if not lectura:
        return {"error": "La lectura no existe."}, 404

    return serializar_lectura(lectura), 200
