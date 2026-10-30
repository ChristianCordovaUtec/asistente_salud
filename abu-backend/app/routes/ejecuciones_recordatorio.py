
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import EjecucionRecordatorio, TratamientoMedicacion


ejecuciones_recordatorio_bp = Blueprint(
    "ejecuciones_recordatorio",
    __name__
)

ESTADOS_VALIDOS = {
    "pendiente",
    "notificado",
    "tomado",
    "omitido",
    "fallido"
}


def serializar_ejecucion(ejecucion):
    return {
        "id": str(ejecucion.id),
        "tratamiento_id": str(ejecucion.tratamiento_id),
        "fecha_hora_programada": (
            ejecucion.fecha_hora_programada.isoformat()
            if ejecucion.fecha_hora_programada else None
        ),
        "estado": ejecucion.estado,
        "fecha_notificacion": (
            ejecucion.fecha_notificacion.isoformat()
            if ejecucion.fecha_notificacion else None
        ),
        "fecha_toma": (
            ejecucion.fecha_toma.isoformat()
            if ejecucion.fecha_toma else None
        ),
        "observaciones": ejecucion.observaciones,
        "created_at": (
            ejecucion.created_at.isoformat()
            if ejecucion.created_at else None
        )
    }


def validar_fecha_hora(valor):
    if not valor:
        raise ValueError("fecha_hora_programada es obligatoria.")

    try:
        fecha = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        raise ValueError(
            "fecha_hora_programada debe tener formato ISO 8601."
        )

    if fecha.tzinfo is None:
        raise ValueError(
            "fecha_hora_programada debe incluir zona horaria."
        )

    return fecha


# GET: listar ejecuciones de un tratamiento
@ejecuciones_recordatorio_bp.route(
    "/api/tratamientos/<uuid:tratamiento_id>/ejecuciones-recordatorio",
    methods=["GET"]
)
def listar_ejecuciones(tratamiento_id):

    tratamiento = db.session.get(TratamientoMedicacion, tratamiento_id)

    if not tratamiento:
        return jsonify({"error": "Tratamiento no encontrado."}), 404

    consulta = EjecucionRecordatorio.query.filter_by(
        tratamiento_id=tratamiento_id
    )

    estado = request.args.get("estado")

    if estado:
        if estado not in ESTADOS_VALIDOS:
            return jsonify({"error": "Estado no válido."}), 400

        consulta = consulta.filter_by(estado=estado)

    ejecuciones = consulta.order_by(
        EjecucionRecordatorio.fecha_hora_programada.asc()
    ).all()

    return jsonify({
        "ejecuciones": [
            serializar_ejecucion(e) for e in ejecuciones
        ],
        "total": len(ejecuciones)
    }), 200


# GET: consultar una ejecución
@ejecuciones_recordatorio_bp.route(
    "/api/ejecuciones-recordatorio/<uuid:ejecucion_id>",
    methods=["GET"]
)
def obtener_ejecucion(ejecucion_id):

    ejecucion = db.session.get(EjecucionRecordatorio, ejecucion_id)

    if not ejecucion:
        return jsonify({"error": "Ejecución no encontrada."}), 404

    return jsonify(serializar_ejecucion(ejecucion)), 200


# POST: crear una ejecución
@ejecuciones_recordatorio_bp.route(
    "/api/tratamientos/<uuid:tratamiento_id>/ejecuciones-recordatorio",
    methods=["POST"]
)
def crear_ejecucion(tratamiento_id):

    tratamiento = db.session.get(TratamientoMedicacion, tratamiento_id)

    if not tratamiento:
        return jsonify({"error": "Tratamiento no encontrado."}), 404

    datos = request.get_json(silent=True) or {}

    try:
        fecha_programada = validar_fecha_hora(
            datos.get("fecha_hora_programada")
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    ejecucion = EjecucionRecordatorio(
        tratamiento_id=tratamiento_id,
        fecha_hora_programada=fecha_programada,
        estado="pendiente",
        observaciones=datos.get("observaciones")
    )

    try:
        db.session.add(ejecucion)
        db.session.commit()

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "Ya existe una ejecución para esa fecha y tratamiento."
        }), 409

    except Exception:
        db.session.rollback()
        return jsonify({"error": "No se pudo crear la ejecución."}), 500

    return jsonify({
        "mensaje": "Ejecución creada correctamente.",
        "ejecucion": serializar_ejecucion(ejecucion)
    }), 201


# PUT: actualizar estado de una ejecución
@ejecuciones_recordatorio_bp.route(
    "/api/ejecuciones-recordatorio/<uuid:ejecucion_id>",
    methods=["PUT"]
)
def actualizar_ejecucion(ejecucion_id):

    ejecucion = db.session.get(EjecucionRecordatorio, ejecucion_id)

    if not ejecucion:
        return jsonify({"error": "Ejecución no encontrada."}), 404

    datos = request.get_json(silent=True) or {}

    if "estado" in datos:
        nuevo_estado = datos["estado"]

        if nuevo_estado not in ESTADOS_VALIDOS:
            return jsonify({
                "error": "Estado no válido.",
                "estados_validos": sorted(ESTADOS_VALIDOS)
            }), 400

        ejecucion.estado = nuevo_estado

        ahora = datetime.now(timezone.utc)

        if nuevo_estado == "notificado":
            ejecucion.fecha_notificacion = ahora

        elif nuevo_estado == "tomado":
            ejecucion.fecha_toma = ahora

    if "observaciones" in datos:
        ejecucion.observaciones = datos["observaciones"]

    try:
        db.session.commit()

    except Exception:
        db.session.rollback()
        return jsonify({"error": "No se pudo actualizar la ejecución."}), 500

    return jsonify({
        "mensaje": "Ejecución actualizada correctamente.",
        "ejecucion": serializar_ejecucion(ejecucion)
    }), 200
