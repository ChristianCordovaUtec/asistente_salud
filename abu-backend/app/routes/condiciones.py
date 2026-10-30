
from datetime import date, datetime, timezone
from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Paciente, TipoCondicion, CondicionPaciente


condiciones_bp = Blueprint("condiciones", __name__)

ESTADOS_VALIDOS = {
    "activa",
    "controlada",
    "en_remision",
    "inactiva"
}


# ---------------------------------------------------------
# SERIALIZADORES
# ---------------------------------------------------------

def serializar_tipo(tipo):
    return {
        "id": tipo.id,
        "nombre": tipo.nombre
    }


def serializar_condicion(condicion):
    return {
        "id": str(condicion.id),
        "paciente_id": str(condicion.paciente_id),
        "tipo_condicion_id": condicion.tipo_condicion_id,
        "tipo_condicion": (
            condicion.tipo_condicion.nombre
            if condicion.tipo_condicion else None
        ),
        "estado": condicion.estado,
        "fuente": condicion.fuente,
        "fecha_diagnosticada": (
            condicion.fecha_diagnosticada.isoformat()
            if condicion.fecha_diagnosticada else None
        ),
        "fecha_actualizada": (
            condicion.fecha_actualizada.isoformat()
            if condicion.fecha_actualizada else None
        )
    }


# ---------------------------------------------------------
# VALIDACIONES
# ---------------------------------------------------------

def validar_fecha(valor):
    if valor is None:
        return None

    try:
        return date.fromisoformat(valor)
    except (ValueError, TypeError):
        return False


def validar_condicion(data, parcial=False):
    if not parcial and "tipo_condicion_id" not in data:
        return "El campo tipo_condicion_id es obligatorio."

    if "tipo_condicion_id" in data:
        try:
            int(data["tipo_condicion_id"])
        except (ValueError, TypeError):
            return "tipo_condicion_id debe ser un número entero."

    if "estado" in data and data["estado"] not in ESTADOS_VALIDOS:
        return "El estado no es válido."

    if "fecha_diagnosticada" in data:
        fecha = validar_fecha(data["fecha_diagnosticada"])
        if fecha is False:
            return "fecha_diagnosticada debe tener formato YYYY-MM-DD."

    return None


# ---------------------------------------------------------
# CONDICION PACIENTE
# ---------------------------------------------------------

# GET: tipos de condiciones disponibles
@condiciones_bp.route("/api/condiciones/tipos", methods=["GET"])
def listar_tipos_condicion():
    tipos = db.session.execute(
        db.select(TipoCondicion).order_by(TipoCondicion.nombre)
    ).scalars().all()

    return {
        "total": len(tipos),
        "tipos": [serializar_tipo(t) for t in tipos]
    }, 200


# GET: condiciones de un paciente
@condiciones_bp.route(
    "/api/pacientes/<uuid:paciente_id>/condiciones",
    methods=["GET"]
)
def listar_condiciones(paciente_id):
    paciente = db.session.get(Paciente, paciente_id)

    if not paciente:
        return {"error": "El paciente no existe."}, 404

    condiciones = db.session.execute(
        db.select(CondicionPaciente)
        .where(CondicionPaciente.paciente_id == paciente_id)
        .order_by(CondicionPaciente.fecha_actualizada.desc())
    ).scalars().all()

    return {
        "total": len(condiciones),
        "condiciones": [serializar_condicion(c) for c in condiciones]
    }, 200


# POST: registrar condición
@condiciones_bp.route(
    "/api/pacientes/<uuid:paciente_id>/condiciones",
    methods=["POST"]
)
def crear_condicion(paciente_id):
    paciente = db.session.get(Paciente, paciente_id)

    if not paciente or not paciente.activo:
        return {"error": "El paciente no existe o está inactivo."}, 404

    data = request.get_json(silent=True) or {}

    error = validar_condicion(data)
    if error:
        return {"error": error}, 400

    tipo_id = int(data["tipo_condicion_id"])
    tipo = db.session.get(TipoCondicion, tipo_id)

    if not tipo:
        return {"error": "El tipo de condición no existe."}, 404

    fecha_diagnosticada = validar_fecha(
        data.get("fecha_diagnosticada")
    )

    condicion = CondicionPaciente(
        paciente_id=paciente_id,
        tipo_condicion_id=tipo_id,
        estado=data.get("estado", "activa"),
        fuente=data.get("fuente"),
        fecha_diagnosticada=fecha_diagnosticada,
        fecha_actualizada=datetime.now(timezone.utc)
    )

    try:
        db.session.add(condicion)
        db.session.commit()
        return serializar_condicion(condicion), 201

    except IntegrityError:
        db.session.rollback()
        return {
            "error": "El paciente ya tiene registrada esta condición."
        }, 409

    except Exception:
        db.session.rollback()
        raise


# PUT: actualizar condición
@condiciones_bp.route(
    "/api/condiciones/<uuid:condicion_id>",
    methods=["PUT"]
)
def actualizar_condicion(condicion_id):
    condicion = db.session.get(CondicionPaciente, condicion_id)

    if not condicion:
        return {"error": "La condición no existe."}, 404

    data = request.get_json(silent=True) or {}

    error = validar_condicion(data, parcial=True)
    if error:
        return {"error": error}, 400

    if "tipo_condicion_id" in data:
        tipo_id = int(data["tipo_condicion_id"])

        if not db.session.get(TipoCondicion, tipo_id):
            return {"error": "El tipo de condición no existe."}, 404

        condicion.tipo_condicion_id = tipo_id

    if "estado" in data:
        condicion.estado = data["estado"]

    if "fuente" in data:
        condicion.fuente = data["fuente"]

    if "fecha_diagnosticada" in data:
        condicion.fecha_diagnosticada = validar_fecha(
            data["fecha_diagnosticada"]
        )

    condicion.fecha_actualizada = datetime.now(timezone.utc)

    try:
        db.session.commit()
        return serializar_condicion(condicion), 200

    except IntegrityError:
        db.session.rollback()
        return {
            "error": "El paciente ya tiene registrada esta condición."
        }, 409

    except Exception:
        db.session.rollback()
        raise


# DELETE: marcar condición como inactiva
@condiciones_bp.route(
    "/api/condiciones/<uuid:condicion_id>",
    methods=["DELETE"]
)
def eliminar_condicion(condicion_id):
    condicion = db.session.get(CondicionPaciente, condicion_id)

    if not condicion:
        return {"error": "La condición no existe."}, 404

    condicion.estado = "inactiva"
    condicion.fecha_actualizada = datetime.now(timezone.utc)

    db.session.commit()

    return {
        "mensaje": "La condición fue marcada como inactiva."
    }, 200
