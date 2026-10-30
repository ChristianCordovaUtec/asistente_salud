
from datetime import datetime, timezone

from flask import Blueprint, request

from app import db
from app.models import Paciente, Alerta


alertas_bp = Blueprint("alertas", __name__)

ESTADOS_VALIDOS = {"pendiente", "atendida", "cerrada"}


# ---------------------------------------------------------
# SERIALIZADORES
# ---------------------------------------------------------

def serializar_alerta(alerta):
    return {
        "id": str(alerta.id),
        "paciente_id": str(alerta.paciente_id),
        "lectura_id": str(alerta.lectura_id) if alerta.lectura_id else None,
        "tipo": alerta.tipo,
        "descripcion": alerta.descripcion,
        "valor_detectado": (
            float(alerta.valor_detectado)
            if alerta.valor_detectado is not None else None
        ),
        "estado": alerta.estado,
        "fecha_registro": (
            alerta.fecha_registro.isoformat()
            if alerta.fecha_registro else None
        )
    }


# ---------------------------------------------------------
# RUTAS DE ALERTAS
# ---------------------------------------------------------

# GET /api/pacientes/<uuid:paciente_id>/alertas
@alertas_bp.route(
    "/api/pacientes/<uuid:paciente_id>/alertas",
    methods=["GET"]
)
def obtener_alertas_paciente(paciente_id):
    paciente = db.session.get(Paciente, paciente_id)

    if not paciente:
        return {"error": "Paciente no encontrado."}, 404

    query = Alerta.query.filter_by(paciente_id=paciente_id)

    estado = request.args.get("estado")
    if estado:
        if estado not in ESTADOS_VALIDOS:
            return {"error": "Estado de alerta no válido."}, 400
        query = query.filter_by(estado=estado)

    alertas = query.order_by(Alerta.fecha_registro.desc()).all()

    return {
        "total": len(alertas),
        "alertas": [serializar_alerta(a) for a in alertas]
    }, 200


# GET /api/alertas/<uuid:alerta_id>
@alertas_bp.route(
    "/api/alertas/<uuid:alerta_id>",
    methods=["GET"]
)
def obtener_alerta(alerta_id):
    alerta = db.session.get(Alerta, alerta_id)

    if not alerta:
        return {"error": "Alerta no encontrada."}, 404

    return serializar_alerta(alerta), 200


# PUT /api/alertas/<uuid:alerta_id>
@alertas_bp.route(
    "/api/alertas/<uuid:alerta_id>",
    methods=["PUT"]
)
def actualizar_alerta(alerta_id):
    alerta = db.session.get(Alerta, alerta_id)

    if not alerta:
        return {"error": "Alerta no encontrada."}, 404

    data = request.get_json(silent=True) or {}
    estado = data.get("estado")

    if estado not in ESTADOS_VALIDOS:
        return {
            "error": "El estado debe ser pendiente, atendida o cerrada."
        }, 400

    alerta.estado = estado

    try:
        db.session.commit()
        db.session.refresh(alerta)
        return serializar_alerta(alerta), 200

    except Exception:
        db.session.rollback()
        raise
