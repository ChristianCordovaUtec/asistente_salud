
from datetime import datetime, timezone
from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Paciente, PerfilCorporal


perfiles_bp = Blueprint("perfiles", __name__)


# ---------------------------------------------------------
# SERIALIZADORES
# ---------------------------------------------------------

def serializar_perfil(perfil):
    return {
        "id": str(perfil.id),
        "paciente_id": str(perfil.paciente_id),
        "peso_kg": float(perfil.peso_kg) if perfil.peso_kg is not None else None,
        "altura_cm": float(perfil.altura_cm) if perfil.altura_cm is not None else None,
        "horas_sueno_promedio": (
            float(perfil.horas_sueno_promedio)
            if perfil.horas_sueno_promedio is not None else None
        ),
        "fecha_registro": (
            perfil.fecha_registro.isoformat()
            if perfil.fecha_registro else None
        )
    }


# ---------------------------------------------------------
# VALIDACIONES
# ---------------------------------------------------------

def validar_perfil(data, parcial=False):
    campos = {
        "peso_kg": (0, 500),
        "altura_cm": (0, 300),
        "horas_sueno_promedio": (0, 24)
    }

    for campo, (minimo, maximo) in campos.items():
        if campo not in data:
            if not parcial:
                return f"El campo {campo} es obligatorio."
            continue

        valor = data[campo]

        if valor is None:
            continue

        try:
            valor = float(valor)
        except (ValueError, TypeError):
            return f"El campo {campo} debe ser numérico."

        if not minimo < valor <= maximo:
            return f"El campo {campo} debe ser mayor que {minimo} y máximo {maximo}."

    return None


# ---------------------------------------------------------
# PERFILES CORPORALES
# ---------------------------------------------------------

# GET: historial de perfiles corporales
@perfiles_bp.route(
    "/api/pacientes/<uuid:paciente_id>/perfiles-corporales",
    methods=["GET"]
)
def listar_perfiles(paciente_id):
    paciente = db.session.get(Paciente, paciente_id)

    if not paciente:
        return {"error": "El paciente no existe."}, 404

    perfiles = db.session.execute(
        db.select(PerfilCorporal)
        .where(PerfilCorporal.paciente_id == paciente_id)
        .order_by(PerfilCorporal.fecha_registro.desc())
    ).scalars().all()

    return {
        "total": len(perfiles),
        "perfiles": [serializar_perfil(p) for p in perfiles]
    }, 200


# POST: registrar perfil corporal
@perfiles_bp.route(
    "/api/pacientes/<uuid:paciente_id>/perfiles-corporales",
    methods=["POST"]
)
def crear_perfil(paciente_id):
    paciente = db.session.get(Paciente, paciente_id)

    if not paciente or not paciente.activo:
        return {"error": "El paciente no existe o está inactivo."}, 404

    data = request.get_json(silent=True) or {}

    error = validar_perfil(data)
    if error:
        return {"error": error}, 400

    perfil = PerfilCorporal(
        paciente_id=paciente_id,
        peso_kg=data["peso_kg"],
        altura_cm=data["altura_cm"],
        horas_sueno_promedio=data["horas_sueno_promedio"]
    )

    try:
        db.session.add(perfil)
        db.session.commit()
        return serializar_perfil(perfil), 201

    except Exception:
        db.session.rollback()
        raise


# PUT: actualizar un perfil corporal
@perfiles_bp.route(
    "/api/perfiles-corporales/<uuid:perfil_id>",
    methods=["PUT"]
)
def actualizar_perfil(perfil_id):
    perfil = db.session.get(PerfilCorporal, perfil_id)

    if not perfil:
        return {"error": "El perfil corporal no existe."}, 404

    data = request.get_json(silent=True) or {}

    error = validar_perfil(data, parcial=True)
    if error:
        return {"error": error}, 400

    for campo in ("peso_kg", "altura_cm", "horas_sueno_promedio"):
        if campo in data:
            setattr(perfil, campo, data[campo])

    try:
        db.session.commit()
        return serializar_perfil(perfil), 200

    except Exception:
        db.session.rollback()
        raise


# DELETE: eliminar un registro del historial
@perfiles_bp.route(
    "/api/perfiles-corporales/<uuid:perfil_id>",
    methods=["DELETE"]
)
def eliminar_perfil(perfil_id):
    perfil = db.session.get(PerfilCorporal, perfil_id)

    if not perfil:
        return {"error": "El perfil corporal no existe."}, 404

    try:
        db.session.delete(perfil)
        db.session.commit()
        return {"mensaje": "Perfil corporal eliminado correctamente."}, 200

    except Exception:
        db.session.rollback()
        raise
