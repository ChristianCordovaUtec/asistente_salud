
from datetime import date, datetime, timezone

from flask import Blueprint, request

from app import db
from app.models import Paciente, TratamientoMedicacion
from app.servicios.medicamentos import (
    confirmar_tratamiento as servicio_confirmar_tratamiento
)


tratamientos_bp = Blueprint("tratamientos_medicacion", __name__)

ESTADOS_VALIDOS = {
    "pendiente",
    "activo",
    "pausado",
    "completado",
    "cancelado"
}


# ---------------------------------------------------------
# SERIALIZADORES
# ---------------------------------------------------------

def serializar_tratamiento(tratamiento):
    """
    Convierte un tratamiento de SQLAlchemy a un diccionario
    JSON con sus datos principales.
    """

    return {
        "id": str(tratamiento.id),
        "paciente_id": str(tratamiento.paciente_id),
        "nombre_medicamento": tratamiento.nombre_medicamento,
        "dosis_valor": float(tratamiento.dosis_valor),
        "dosis_unidad": tratamiento.dosis_unidad,
        "fecha_inicio": tratamiento.fecha_inicio.isoformat(),
        "fecha_fin": tratamiento.fecha_fin.isoformat(),
        "estado": tratamiento.estado,
        "fecha_confirmacion": (
            tratamiento.fecha_confirmacion.isoformat()
            if tratamiento.fecha_confirmacion else None
        ),
        "observaciones": tratamiento.observaciones,
        "created_at": (
            tratamiento.created_at.isoformat()
            if tratamiento.created_at else None
        ),
        "updated_at": (
            tratamiento.updated_at.isoformat()
            if tratamiento.updated_at else None
        )
    }


# ---------------------------------------------------------
# VALIDACIONES
# ---------------------------------------------------------

def validar_tratamiento(data, parcial=False):
    """
    Valida los datos recibidos para crear o actualizar
    un tratamiento de medicación.
    """

    obligatorios = [
        "nombre_medicamento",
        "dosis_valor",
        "dosis_unidad",
        "fecha_inicio",
        "fecha_fin"
    ]

    if not parcial:
        for campo in obligatorios:
            if campo not in data or data[campo] is None:
                return f"El campo {campo} es obligatorio."

    if "nombre_medicamento" in data:
        valor = data["nombre_medicamento"]

        if not isinstance(valor, str) or not valor.strip():
            return "nombre_medicamento debe ser un texto no vacío."

    if "dosis_valor" in data:
        valor = data["dosis_valor"]

        if isinstance(valor, bool):
            return "dosis_valor debe ser numérico."

        try:
            valor = float(valor)
        except (ValueError, TypeError):
            return "dosis_valor debe ser numérico."

        if valor <= 0:
            return "dosis_valor debe ser mayor que cero."

    if "dosis_unidad" in data:
        valor = data["dosis_unidad"]

        if not isinstance(valor, str) or not valor.strip():
            return "dosis_unidad debe ser un texto no vacío."

    for campo in ("fecha_inicio", "fecha_fin"):
        if campo in data:
            if data[campo] is None:
                return f"{campo} no puede ser nulo."

            try:
                date.fromisoformat(data[campo])
            except (ValueError, TypeError):
                return f"{campo} debe tener formato YYYY-MM-DD."

    if "estado" in data:
        if data["estado"] not in ESTADOS_VALIDOS:
            return "Estado de tratamiento no válido."

    if "observaciones" in data and data["observaciones"] is not None:
        if not isinstance(data["observaciones"], str):
            return "observaciones debe ser un texto."

    return None


# ---------------------------------------------------------
# GET: LISTAR TRATAMIENTOS
# ---------------------------------------------------------

@tratamientos_bp.route(
    "/api/pacientes/<uuid:paciente_id>/tratamientos",
    methods=["GET"]
)
def obtener_tratamientos(paciente_id):
    """
    Lista los tratamientos de un paciente.

    Permite filtrar por estado mediante el parámetro opcional
    ?estado=activo, pendiente, pausado, etc.
    """

    paciente = db.session.get(Paciente, paciente_id)

    if not paciente:
        return {"error": "Paciente no encontrado."}, 404

    query = TratamientoMedicacion.query.filter_by(
        paciente_id=paciente_id
    )

    estado = request.args.get("estado")

    if estado:
        if estado not in ESTADOS_VALIDOS:
            return {"error": "Estado no válido."}, 400

        query = query.filter_by(estado=estado)

    tratamientos = query.order_by(
        TratamientoMedicacion.fecha_inicio.desc()
    ).all()

    return {
        "total": len(tratamientos),
        "tratamientos": [
            serializar_tratamiento(t) for t in tratamientos
        ]
    }, 200


# ---------------------------------------------------------
# GET: OBTENER UN TRATAMIENTO
# ---------------------------------------------------------

@tratamientos_bp.route(
    "/api/tratamientos/<uuid:tratamiento_id>",
    methods=["GET"]
)
def obtener_tratamiento(tratamiento_id):
    """
    Obtiene los datos de un tratamiento específico
    mediante su identificador.
    """

    tratamiento = db.session.get(
        TratamientoMedicacion, tratamiento_id
    )

    if not tratamiento:
        return {"error": "Tratamiento no encontrado."}, 404

    return serializar_tratamiento(tratamiento), 200


# ---------------------------------------------------------
# POST: CREAR TRATAMIENTO
# ---------------------------------------------------------

@tratamientos_bp.route(
    "/api/pacientes/<uuid:paciente_id>/tratamientos",
    methods=["POST"]
)
def crear_tratamiento(paciente_id):
    """
    Registra un tratamiento nuevo en estado pendiente.

    No lo confirma ni genera ejecuciones de recordatorio.
    La confirmación se realiza posteriormente, cuando el
    paciente haya aceptado todos los datos y horarios.
    """

    paciente = db.session.get(Paciente, paciente_id)

    if not paciente or not paciente.activo:
        return {"error": "Paciente no encontrado o inactivo."}, 404

    data = request.get_json(silent=True) or {}

    error = validar_tratamiento(data)

    if error:
        return {"error": error}, 400

    fecha_inicio = date.fromisoformat(data["fecha_inicio"])
    fecha_fin = date.fromisoformat(data["fecha_fin"])

    if fecha_fin < fecha_inicio:
        return {
            "error": "fecha_fin no puede ser anterior a fecha_inicio."
        }, 400

    tratamiento = TratamientoMedicacion(
        paciente_id=paciente_id,
        nombre_medicamento=data["nombre_medicamento"].strip(),
        dosis_valor=data["dosis_valor"],
        dosis_unidad=data["dosis_unidad"].strip(),
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        estado="pendiente",
        fecha_confirmacion=None,
        observaciones=data.get("observaciones")
    )

    try:
        db.session.add(tratamiento)
        db.session.commit()
        db.session.refresh(tratamiento)

        return serializar_tratamiento(tratamiento), 201

    except Exception:
        db.session.rollback()
        raise


# ---------------------------------------------------------
# POST: CONFIRMAR TRATAMIENTO
# ---------------------------------------------------------

@tratamientos_bp.route(
    "/api/tratamientos/<uuid:tratamiento_id>/confirmar",
    methods=["POST"]
)
def confirmar_tratamiento(tratamiento_id):
    """
    Confirma el tratamiento después de que el paciente haya
    aceptado el medicamento, dosis, horarios y periodo.

    Delega al servicio la activación del tratamiento y la
    generación de todas sus ejecuciones de recordatorio.
    """

    try:
        resultado = servicio_confirmar_tratamiento(tratamiento_id)

        return resultado, 200

    except ValueError as error:
        return {"error": str(error)}, 400

    except Exception:
        db.session.rollback()

        return {
            "error": "No se pudo confirmar el tratamiento."
        }, 500


# ---------------------------------------------------------
# PUT: ACTUALIZAR TRATAMIENTO
# ---------------------------------------------------------

@tratamientos_bp.route(
    "/api/tratamientos/<uuid:tratamiento_id>",
    methods=["PUT"]
)
def actualizar_tratamiento(tratamiento_id):
    """
    Actualiza los datos de un tratamiento existente.

    No modifica la confirmación del paciente. Si se necesita
    confirmar, debe utilizarse el endpoint específico.
    """

    tratamiento = db.session.get(
        TratamientoMedicacion, tratamiento_id
    )

    if not tratamiento:
        return {"error": "Tratamiento no encontrado."}, 404

    data = request.get_json(silent=True) or {}

    # La confirmación se gestiona exclusivamente mediante POST /confirmar.
    if "confirmado" in data or "fecha_confirmacion" in data:
        return {
            "error": "La confirmación debe realizarse mediante el endpoint específico."
        }, 400

    error = validar_tratamiento(data, parcial=True)

    if error:
        return {"error": error}, 400

    fecha_inicio = (
        date.fromisoformat(data["fecha_inicio"])
        if "fecha_inicio" in data
        else tratamiento.fecha_inicio
    )

    fecha_fin = (
        date.fromisoformat(data["fecha_fin"])
        if "fecha_fin" in data
        else tratamiento.fecha_fin
    )

    if fecha_fin < fecha_inicio:
        return {
            "error": "fecha_fin no puede ser anterior a fecha_inicio."
        }, 400

    campos = [
        "nombre_medicamento",
        "dosis_valor",
        "dosis_unidad",
        "estado",
        "observaciones"
    ]

    for campo in campos:
        if campo in data:
            valor = data[campo]

            if campo in ("nombre_medicamento", "dosis_unidad"):
                valor = valor.strip()

            setattr(tratamiento, campo, valor)

    tratamiento.fecha_inicio = fecha_inicio
    tratamiento.fecha_fin = fecha_fin
    tratamiento.updated_at = datetime.now(timezone.utc)

    try:
        db.session.commit()
        db.session.refresh(tratamiento)

        return serializar_tratamiento(tratamiento), 200

    except Exception:
        db.session.rollback()
        raise


# ---------------------------------------------------------
# DELETE: CANCELAR TRATAMIENTO
# ---------------------------------------------------------

@tratamientos_bp.route(
    "/api/tratamientos/<uuid:tratamiento_id>",
    methods=["DELETE"]
)
def cancelar_tratamiento(tratamiento_id):
    """
    Cancela un tratamiento cambiando su estado.

    Conserva el registro y su historial de ejecuciones
    para mantener la trazabilidad.
    """

    tratamiento = db.session.get(
        TratamientoMedicacion, tratamiento_id
    )

    if not tratamiento:
        return {"error": "Tratamiento no encontrado."}, 404

    tratamiento.estado = "cancelado"
    tratamiento.updated_at = datetime.now(timezone.utc)

    try:
        db.session.commit()

        return {
            "mensaje": "Tratamiento cancelado correctamente."
        }, 200

    except Exception:
        db.session.rollback()

        raise
