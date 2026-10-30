
from datetime import datetime, timezone
from math import isfinite

from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Paciente, ConfiguracionAlertasGlucosa


configuracion_alertas_bp = Blueprint(
    "configuracion_alertas_glucosa",
    __name__
)

UNIDADES_VALIDAS = {"mg/dL", "mmol/L"}


# ---------------------------------------------------------
# SERIALIZADORES
# ---------------------------------------------------------

def serializar_configuracion(config):
    return {
        "id": str(config.id),
        "paciente_id": str(config.paciente_id),
        "umbral_minimo": float(config.umbral_minimo) if config.umbral_minimo is not None else None,
        "umbral_maximo": float(config.umbral_maximo) if config.umbral_maximo is not None else None,
        "unidad": config.unidad,
        "detectar_tendencia": config.detectar_tendencia,
        "dias_analisis": config.dias_analisis,
        "activa": config.activa,
        "fecha_actualizacion": (
            config.fecha_actualizacion.isoformat()
            if config.fecha_actualizacion else None
        )
    }


# ---------------------------------------------------------
# VALIDACIONES
# ---------------------------------------------------------

def validar_configuracion(data, parcial=False):
    campos_numericos = ("umbral_minimo", "umbral_maximo")

    for campo in campos_numericos:
        if campo in data and data[campo] is not None:
            if isinstance(data[campo], bool):
                return f"El campo {campo} debe ser numérico."

            try:
                valor = float(data[campo])
            except (ValueError, TypeError):
                return f"El campo {campo} debe ser numérico."

            if not isfinite(valor) or valor <= 0:
                return f"El campo {campo} debe ser mayor que cero."

    if "unidad" in data and data["unidad"] not in UNIDADES_VALIDAS:
        return "La unidad debe ser mg/dL o mmol/L."

    if "detectar_tendencia" in data and not isinstance(data["detectar_tendencia"], bool):
        return "detectar_tendencia debe ser booleano."

    if "activa" in data and not isinstance(data["activa"], bool):
        return "activa debe ser booleano."

    if "dias_analisis" in data:
        dias = data["dias_analisis"]

        if isinstance(dias, bool) or not isinstance(dias, int):
            return "dias_analisis debe ser un número entero."

        if dias < 1:
            return "dias_analisis debe ser mayor o igual a 1."

    if not parcial:
        detectar = data.get("detectar_tendencia", False)
        dias = data.get("dias_analisis", 4)

        if not detectar and dias != 4:
            return "Si detectar_tendencia es false, dias_analisis debe ser 4."

    return None


def validar_umbrales(minimo, maximo):
    if minimo is not None and maximo is not None:
        if float(minimo) >= float(maximo):
            return "umbral_minimo debe ser menor que umbral_maximo."

    return None


# ---------------------------------------------------------
# RUTAS DE CONFIGURACIÓN DE ALERTAS DE GLUCOSA
# ---------------------------------------------------------

# GET /api/pacientes/<uuid:paciente_id>/configuracion-alertas-glucosa
@configuracion_alertas_bp.route(
    "/api/pacientes/<uuid:paciente_id>/configuracion-alertas-glucosa",
    methods=["GET"]
)
def obtener_configuracion(paciente_id):
    config = ConfiguracionAlertasGlucosa.query.filter_by(
        paciente_id=paciente_id
    ).first()

    if not config:
        return {"error": "El paciente no tiene una configuración de alertas."}, 404

    return serializar_configuracion(config), 200


# POST /api/pacientes/<uuid:paciente_id>/configuracion-alertas-glucosa
@configuracion_alertas_bp.route(
    "/api/pacientes/<uuid:paciente_id>/configuracion-alertas-glucosa",
    methods=["POST"]
)
def crear_configuracion(paciente_id):
    paciente = db.session.get(Paciente, paciente_id)

    if not paciente or not paciente.activo:
        return {"error": "Paciente no encontrado o inactivo."}, 404

    data = request.get_json(silent=True) or {}

    error = validar_configuracion(data)
    if error:
        return {"error": error}, 400

    minimo = data.get("umbral_minimo")
    maximo = data.get("umbral_maximo")

    error = validar_umbrales(minimo, maximo)
    if error:
        return {"error": error}, 400

    config = ConfiguracionAlertasGlucosa(
        paciente_id=paciente_id,
        umbral_minimo=minimo,
        umbral_maximo=maximo,
        unidad=data.get("unidad", "mg/dL"),
        detectar_tendencia=data.get("detectar_tendencia", False),
        dias_analisis=data.get("dias_analisis", 4),
        activa=data.get("activa", True)
    )

    try:
        db.session.add(config)
        db.session.commit()
        db.session.refresh(config)
        return serializar_configuracion(config), 201

    except IntegrityError:
        db.session.rollback()
        return {"error": "El paciente ya tiene una configuración de alertas."}, 409

    except Exception:
        db.session.rollback()
        raise


# PUT /api/pacientes/<uuid:paciente_id>/configuracion-alertas-glucosa
@configuracion_alertas_bp.route(
    "/api/pacientes/<uuid:paciente_id>/configuracion-alertas-glucosa",
    methods=["PUT"]
)
def actualizar_configuracion(paciente_id):
    config = ConfiguracionAlertasGlucosa.query.filter_by(
        paciente_id=paciente_id
    ).first()

    if not config:
        return {"error": "Configuración no encontrada."}, 404

    data = request.get_json(silent=True) or {}

    error = validar_configuracion(data, parcial=True)
    if error:
        return {"error": error}, 400

    minimo = data.get("umbral_minimo", config.umbral_minimo)
    maximo = data.get("umbral_maximo", config.umbral_maximo)

    error = validar_umbrales(minimo, maximo)
    if error:
        return {"error": error}, 400

    detectar = data.get("detectar_tendencia", config.detectar_tendencia)
    dias = data.get("dias_analisis", config.dias_analisis)

    if not detectar and dias != 4:
        return {
            "error": "Si detectar_tendencia es false, dias_analisis debe ser 4."
        }, 400

    campos = [
        "umbral_minimo",
        "umbral_maximo",
        "unidad",
        "detectar_tendencia",
        "dias_analisis",
        "activa"
    ]

    for campo in campos:
        if campo in data:
            setattr(config, campo, data[campo])

    config.fecha_actualizacion = datetime.now(timezone.utc)

    try:
        db.session.commit()
        db.session.refresh(config)
        return serializar_configuracion(config), 200

    except Exception:
        db.session.rollback()
        raise


# DELETE /api/pacientes/<uuid:paciente_id>/configuracion-alertas-glucosa
@configuracion_alertas_bp.route(
    "/api/pacientes/<uuid:paciente_id>/configuracion-alertas-glucosa",
    methods=["DELETE"]
)
def desactivar_configuracion(paciente_id):
    config = ConfiguracionAlertasGlucosa.query.filter_by(
        paciente_id=paciente_id
    ).first()

    if not config:
        return {"error": "Configuración no encontrada."}, 404

    config.activa = False
    config.fecha_actualizacion = datetime.now(timezone.utc)

    db.session.commit()

    return {
        "mensaje": "Configuración de alertas desactivada correctamente."
    }, 200
