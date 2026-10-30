
from datetime import datetime, time, timezone

from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import TratamientoMedicacion, HorarioMedicacion


horarios_bp = Blueprint("horarios_medicacion", __name__)


# ---------------------------------------------------------
# SERIALIZADORES
# ---------------------------------------------------------

def serializar_horario(horario):
    return {
        "id": str(horario.id),
        "tratamiento_id": str(horario.tratamiento_id),
        "hora": horario.hora.strftime("%H:%M:%S"),
        "activo": horario.activo
    }


# ---------------------------------------------------------
# VALIDACIONES
# ---------------------------------------------------------

def validar_hora(valor):
    if not isinstance(valor, str):
        return None

    try:
        return time.fromisoformat(valor)
    except ValueError:
        return None


# ---------------------------------------------------------
# RUTAS HORARIOS DE MEDICACION
# ---------------------------------------------------------

# GET /api/tratamientos/<uuid:tratamiento_id>/horarios
@horarios_bp.route(
    "/api/tratamientos/<uuid:tratamiento_id>/horarios",
    methods=["GET"]
)
def obtener_horarios(tratamiento_id):
    tratamiento = db.session.get(
        TratamientoMedicacion, tratamiento_id
    )

    if not tratamiento:
        return {"error": "Tratamiento no encontrado."}, 404

    query = HorarioMedicacion.query.filter_by(
        tratamiento_id=tratamiento_id
    )

    activo = request.args.get("activo")
    if activo is not None:
        if activo.lower() not in ("true", "false"):
            return {"error": "El filtro activo debe ser true o false."}, 400

        query = query.filter_by(activo=activo.lower() == "true")

    horarios = query.order_by(HorarioMedicacion.hora.asc()).all()

    return {
        "total": len(horarios),
        "horarios": [serializar_horario(h) for h in horarios]
    }, 200


# POST /api/tratamientos/<uuid:tratamiento_id>/horarios
@horarios_bp.route(
    "/api/tratamientos/<uuid:tratamiento_id>/horarios",
    methods=["POST"]
)
def crear_horario(tratamiento_id):
    tratamiento = db.session.get(
        TratamientoMedicacion, tratamiento_id
    )

    if not tratamiento:
        return {"error": "Tratamiento no encontrado."}, 404

    data = request.get_json(silent=True) or {}

    if "hora" not in data:
        return {"error": "El campo hora es obligatorio."}, 400

    hora = validar_hora(data["hora"])
    if hora is None:
        return {
            "error": "hora debe tener formato HH:MM o HH:MM:SS."
        }, 400

    activo = data.get("activo", True)
    if not isinstance(activo, bool):
        return {"error": "activo debe ser booleano."}, 400

    horario = HorarioMedicacion(
        tratamiento_id=tratamiento_id,
        hora=hora,
        activo=activo
    )

    try:
        db.session.add(horario)
        db.session.commit()
        db.session.refresh(horario)

        return serializar_horario(horario), 201

    except IntegrityError:
        db.session.rollback()
        return {
            "error": "Ya existe ese horario para el tratamiento."
        }, 409

    except Exception:
        db.session.rollback()
        raise


# PUT /api/horarios-medicacion/<uuid:horario_id>
@horarios_bp.route(
    "/api/horarios-medicacion/<uuid:horario_id>",
    methods=["PUT"]
)
def actualizar_horario(horario_id):
    horario = db.session.get(HorarioMedicacion, horario_id)

    if not horario:
        return {"error": "Horario no encontrado."}, 404

    data = request.get_json(silent=True) or {}

    if "hora" in data:
        hora = validar_hora(data["hora"])

        if hora is None:
            return {
                "error": "hora debe tener formato HH:MM o HH:MM:SS."
            }, 400

        horario.hora = hora

    if "activo" in data:
        if not isinstance(data["activo"], bool):
            return {"error": "activo debe ser booleano."}, 400

        horario.activo = data["activo"]

    try:
        db.session.commit()
        db.session.refresh(horario)

        return serializar_horario(horario), 200

    except IntegrityError:
        db.session.rollback()
        return {
            "error": "Ya existe ese horario para el tratamiento."
        }, 409

    except Exception:
        db.session.rollback()
        raise


# DELETE /api/horarios-medicacion/<uuid:horario_id>
@horarios_bp.route(
    "/api/horarios-medicacion/<uuid:horario_id>",
    methods=["DELETE"]
)
def eliminar_horario(horario_id):
    horario = db.session.get(HorarioMedicacion, horario_id)

    if not horario:
        return {"error": "Horario no encontrado."}, 404

    try:
        db.session.delete(horario)
        db.session.commit()

        return {
            "mensaje": "Horario eliminado correctamente."
        }, 200

    except Exception:
        db.session.rollback()
        raise
