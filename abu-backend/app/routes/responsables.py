
from datetime import datetime, timezone

from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Responsable, Paciente, PacienteResponsable


responsables_bp = Blueprint("responsables", __name__)


# ---------------------------------------------------------
# SERIALIZADORES
# ---------------------------------------------------------

def serializar_responsable(responsable):
    return {
        "id": str(responsable.id),
        "nombres": responsable.nombres,
        "apellidos": responsable.apellidos,
        "telefono": responsable.telefono,
        "email": responsable.email,
        "activo": responsable.activo,
        "fecha_registro": responsable.fecha_registro.isoformat()
    }


def serializar_relacion(relacion):
    return {
        "id": str(relacion.id),
        "paciente_id": str(relacion.paciente_id),
        "responsable_id": str(relacion.responsable_id),
        "tipo_relacion": relacion.tipo_relacion,
        "tipo_relacion_otro": relacion.tipo_relacion_otro,
        "puede_ver": relacion.puede_ver,
        "puede_editar": relacion.puede_editar,
        "desde": relacion.desde.isoformat(),
        "hasta": relacion.hasta.isoformat() if relacion.hasta else None
    }


# ---------------------------------------------------------
# VALIDACIONES
# ---------------------------------------------------------

def validar_responsable(data, parcial=False):
    if not isinstance(data, dict):
        return "El cuerpo debe ser un objeto JSON."

    obligatorios = ["nombres", "apellidos", "telefono"]

    if not parcial:
        for campo in obligatorios:
            if not data.get(campo):
                return f"El campo '{campo}' es obligatorio."

    longitudes = {
        "nombres": 100,
        "apellidos": 100,
        "telefono": 30,
        "email": 150
    }

    for campo, longitud in longitudes.items():
        if campo not in data:
            continue

        valor = data[campo]

        if campo in obligatorios and (
            not isinstance(valor, str) or not valor.strip()
        ):
            return f"El campo '{campo}' no puede estar vacío."

        if valor is not None:
            if not isinstance(valor, str) or len(valor.strip()) > longitud:
                return f"El campo '{campo}' no es válido."

    return None


def validar_relacion(data, parcial=False):
    if not isinstance(data, dict):
        return "El cuerpo debe ser un objeto JSON."

    if not parcial:
        if not data.get("responsable_id"):
            return "El campo 'responsable_id' es obligatorio."

        if not data.get("tipo_relacion"):
            return "El campo 'tipo_relacion' es obligatorio."

    if "tipo_relacion" in data:
        valor = data["tipo_relacion"]

        if not isinstance(valor, str) or not valor.strip():
            return "tipo_relacion no puede estar vacío."

        if len(valor.strip()) > 50:
            return "tipo_relacion supera los 50 caracteres."

    if "tipo_relacion_otro" in data:
        valor = data["tipo_relacion_otro"]

        if valor is not None and (
            not isinstance(valor, str) or len(valor) > 100
        ):
            return "tipo_relacion_otro no es válido."

    for campo in ("puede_ver", "puede_editar"):
        if campo in data and not isinstance(data[campo], bool):
            return f"El campo '{campo}' debe ser booleano."

    return None


# ---------------------------------------------------------
# RESPONSABLES
# ---------------------------------------------------------

@responsables_bp.route("/api/responsables", methods=["GET"])
def listar_responsables():
    responsables = db.session.execute(
        db.select(Responsable)
        .where(Responsable.activo.is_(True))
        .order_by(Responsable.apellidos, Responsable.nombres)
    ).scalars().all()

    return {
        "total": len(responsables),
        "responsables": [
            serializar_responsable(r) for r in responsables
        ]
    }, 200


@responsables_bp.route(
    "/api/responsables/<uuid:responsable_id>",
    methods=["GET"]
)
def obtener_responsable(responsable_id):
    responsable = db.session.get(Responsable, responsable_id)

    if not responsable:
        return {"error": "Responsable no encontrado."}, 404

    return serializar_responsable(responsable), 200


@responsables_bp.route("/api/responsables", methods=["POST"])
def crear_responsable():
    data = request.get_json(silent=True)

    error = validar_responsable(data)

    if error:
        return {"error": error}, 400

    responsable = Responsable(
        nombres=data["nombres"].strip(),
        apellidos=data["apellidos"].strip(),
        telefono=data["telefono"].strip(),
        email=data.get("email", "").strip() or None
    )

    db.session.add(responsable)
    db.session.commit()

    return serializar_responsable(responsable), 201


@responsables_bp.route(
    "/api/responsables/<uuid:responsable_id>",
    methods=["PUT"]
)
def actualizar_responsable(responsable_id):
    responsable = db.session.get(Responsable, responsable_id)

    if not responsable:
        return {"error": "Responsable no encontrado."}, 404

    data = request.get_json(silent=True)
    error = validar_responsable(data, parcial=True)

    if error:
        return {"error": error}, 400

    for campo in ("nombres", "apellidos", "telefono", "email"):
        if campo in data:
            valor = data[campo]
            setattr(
                responsable,
                campo,
                valor.strip() if valor else None
            )

    db.session.commit()

    return serializar_responsable(responsable), 200


@responsables_bp.route(
    "/api/responsables/<uuid:responsable_id>",
    methods=["DELETE"]
)
def desactivar_responsable(responsable_id):
    responsable = db.session.get(Responsable, responsable_id)

    if not responsable:
        return {"error": "Responsable no encontrado."}, 404

    responsable.activo = False
    db.session.commit()

    return {
        "mensaje": "Responsable desactivado correctamente.",
        "id": str(responsable.id)
    }, 200


# ---------------------------------------------------------
# ASOCIACION PACIENTE - RESPONSABLE
# ---------------------------------------------------------

@responsables_bp.route(
    "/api/pacientes/<uuid:paciente_id>/responsables",
    methods=["GET"]
)
def listar_responsables_paciente(paciente_id):
    paciente = db.session.get(Paciente, paciente_id)

    if not paciente:
        return {"error": "Paciente no encontrado."}, 404

    incluir_finalizadas = (
        request.args.get("incluir_finalizadas", "false").lower() == "true"
    )

    consulta = db.select(PacienteResponsable).where(
        PacienteResponsable.paciente_id == paciente_id
    )

    if not incluir_finalizadas:
        consulta = consulta.where(PacienteResponsable.hasta.is_(None))

    relaciones = db.session.execute(consulta).scalars().all()

    return {
        "total": len(relaciones),
        "responsables": [
            {
                **serializar_relacion(relacion),
                "responsable": serializar_responsable(relacion.responsable)
            }
            for relacion in relaciones
        ]
    }, 200


@responsables_bp.route(
    "/api/pacientes/<uuid:paciente_id>/responsables",
    methods=["POST"]
)
def asociar_responsable(paciente_id):
    paciente = db.session.get(Paciente, paciente_id)

    if not paciente:
        return {"error": "Paciente no encontrado."}, 404

    if not paciente.activo:
        return {"error": "El paciente está inactivo."}, 400

    data = request.get_json(silent=True)
    error = validar_relacion(data)

    if error:
        return {"error": error}, 400

    responsable = db.session.get(
        Responsable,
        data["responsable_id"]
    )

    if not responsable:
        return {"error": "Responsable no encontrado."}, 404

    if not responsable.activo:
        return {"error": "El responsable está inactivo."}, 400

    relacion = PacienteResponsable(
        paciente_id=paciente_id,
        responsable_id=responsable.id,
        tipo_relacion=data["tipo_relacion"].strip(),
        tipo_relacion_otro=data.get("tipo_relacion_otro"),
        puede_ver=data.get("puede_ver", True),
        puede_editar=data.get("puede_editar", False)
    )

    try:
        db.session.add(relacion)
        db.session.commit()

        return serializar_relacion(relacion), 201

    except IntegrityError:
        db.session.rollback()

        return {
            "error": "Este responsable ya está asociado al paciente."
        }, 409


@responsables_bp.route(
    "/api/pacientes/<uuid:paciente_id>/responsables/"
    "<uuid:relacion_id>",
    methods=["PUT"]
)
def actualizar_relacion(paciente_id, relacion_id):
    relacion = db.session.get(PacienteResponsable, relacion_id)

    if not relacion or relacion.paciente_id != paciente_id:
        return {"error": "Asociación no encontrada."}, 404

    if relacion.hasta is not None:
        return {"error": "La asociación ya está finalizada."}, 400

    data = request.get_json(silent=True)
    error = validar_relacion(data, parcial=True)

    if error:
        return {"error": error}, 400

    campos = (
        "tipo_relacion",
        "tipo_relacion_otro",
        "puede_ver",
        "puede_editar"
    )

    for campo in campos:
        if campo in data:
            valor = data[campo]
            setattr(
                relacion,
                campo,
                valor.strip() if campo == "tipo_relacion" else valor
            )

    db.session.commit()

    return serializar_relacion(relacion), 200


@responsables_bp.route(
    "/api/pacientes/<uuid:paciente_id>/responsables/"
    "<uuid:relacion_id>",
    methods=["DELETE"]
)
def finalizar_relacion(paciente_id, relacion_id):
    relacion = db.session.get(PacienteResponsable, relacion_id)

    if not relacion or relacion.paciente_id != paciente_id:
        return {"error": "Asociación no encontrada."}, 404

    if relacion.hasta is not None:
        return {"mensaje": "La asociación ya estaba finalizada."}, 200

    relacion.hasta = datetime.now(timezone.utc)
    db.session.commit()

    return {
        "mensaje": "Asociación finalizada correctamente.",
        "id": str(relacion.id),
        "hasta": relacion.hasta.isoformat()
    }, 200
