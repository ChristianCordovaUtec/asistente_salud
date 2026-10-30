
from datetime import datetime, timezone

from flask import Blueprint, request

from app import db
from app.models import Alerta, Notificacion


notificaciones_bp = Blueprint("notificaciones", __name__)

ESTADOS_VALIDOS = {
    "pendiente",
    "enviada",
    "entregada",
    "fallida"
}


# ---------------------------------------------------------
# SERIALIZADORES
# ---------------------------------------------------------

def serializar_notificacion(notificacion):
    return {
        "id": str(notificacion.id),
        "alerta_id": str(notificacion.alerta_id),
        "paciente_responsable_id": str(
            notificacion.paciente_responsable_id
        ),
        "canal": notificacion.canal,
        "destinatario": notificacion.destinatario,
        "mensaje": notificacion.mensaje,
        "estado": notificacion.estado,
        "proveedor": notificacion.proveedor,
        "proveedor_mensaje_id": notificacion.proveedor_mensaje_id,
        "fecha_registro": (
            notificacion.fecha_registro.isoformat()
            if notificacion.fecha_registro else None
        ),
        "fecha_envio": (
            notificacion.fecha_envio.isoformat()
            if notificacion.fecha_envio else None
        ),
        "fecha_entrega": (
            notificacion.fecha_entrega.isoformat()
            if notificacion.fecha_entrega else None
        ),
        "error_detalle": notificacion.error_detalle
    }


# ---------------------------------------------------------
# RUTAS DE NOTIFICACIONES
# ---------------------------------------------------------

# GET /api/alertas/<uuid:alerta_id>/notificaciones
@notificaciones_bp.route(
    "/api/alertas/<uuid:alerta_id>/notificaciones",
    methods=["GET"]
)
def obtener_notificaciones_alerta(alerta_id):
    alerta = db.session.get(Alerta, alerta_id)

    if not alerta:
        return {"error": "Alerta no encontrada."}, 404

    query = Notificacion.query.filter_by(alerta_id=alerta_id)

    estado = request.args.get("estado")
    if estado:
        if estado not in ESTADOS_VALIDOS:
            return {"error": "Estado de notificación no válido."}, 400

        query = query.filter_by(estado=estado)

    notificaciones = query.order_by(
        Notificacion.fecha_registro.desc()
    ).all()

    return {
        "total": len(notificaciones),
        "notificaciones": [
            serializar_notificacion(n) for n in notificaciones
        ]
    }, 200


# GET /api/notificaciones/<uuid:notificacion_id>
@notificaciones_bp.route(
    "/api/notificaciones/<uuid:notificacion_id>",
    methods=["GET"]
)
def obtener_notificacion(notificacion_id):
    notificacion = db.session.get(Notificacion, notificacion_id)

    if not notificacion:
        return {"error": "Notificación no encontrada."}, 404

    return serializar_notificacion(notificacion), 200


# PUT /api/notificaciones/<uuid:notificacion_id>
@notificaciones_bp.route(
    "/api/notificaciones/<uuid:notificacion_id>",
    methods=["PUT"]
)
def actualizar_notificacion(notificacion_id):
    notificacion = db.session.get(Notificacion, notificacion_id)

    if not notificacion:
        return {"error": "Notificación no encontrada."}, 404

    data = request.get_json(silent=True) or {}
    estado = data.get("estado")

    if estado not in ESTADOS_VALIDOS:
        return {
            "error": (
                "El estado debe ser pendiente, enviada, "
                "entregada o fallida."
            )
        }, 400

    notificacion.estado = estado

    ahora = datetime.now(timezone.utc)

    if estado == "enviada":
        notificacion.fecha_envio = ahora

    elif estado == "entregada":
        notificacion.fecha_entrega = ahora

    if "proveedor_mensaje_id" in data:
        notificacion.proveedor_mensaje_id = data["proveedor_mensaje_id"]

    if "error_detalle" in data:
        notificacion.error_detalle = data["error_detalle"]

    try:
        db.session.commit()
        db.session.refresh(notificacion)

        return serializar_notificacion(notificacion), 200

    except Exception:
        db.session.rollback()
        raise
