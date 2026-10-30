
from datetime import date
from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Paciente


pacientes_bp = Blueprint("pacientes", __name__)

TIPOS_DOCUMENTO = {"DNI", "CE", "PASAPORTE", "OTRO"}


# ---------------------------------------------------------
# SERIALIZADORES
# ---------------------------------------------------------

def serializar_paciente(paciente):
    return {
        "id": str(paciente.id),
        "nombres": paciente.nombres,
        "apellidos": paciente.apellidos,
        "documento_pais": paciente.documento_pais,
        "tipo_documento": paciente.tipo_documento,
        "documento_numero": paciente.documento_numero,
        "fecha_nacimiento": (
            paciente.fecha_nacimiento.isoformat()
            if paciente.fecha_nacimiento else None
        ),
        "sexo": paciente.sexo,
        "telefono": paciente.telefono,
        "activo": paciente.activo,
        "fecha_registro": paciente.fecha_registro.isoformat()
    }


# ---------------------------------------------------------
# VALIDACIONES
# ---------------------------------------------------------

def validar_datos(data, parcial=False):
    if not isinstance(data, dict):
        return "El cuerpo de la solicitud debe ser un objeto JSON."

    campos_obligatorios = [
        "nombres",
        "apellidos",
        "documento_pais",
        "tipo_documento",
        "documento_numero"
    ]

    if not parcial:
        for campo in campos_obligatorios:
            if not data.get(campo):
                return f"El campo '{campo}' es obligatorio."

    for campo in campos_obligatorios:
        if campo in data:
            valor = data[campo]

            if not isinstance(valor, str) or not valor.strip():
                return f"El campo '{campo}' no puede estar vacío."

    if "documento_pais" in data:
        pais = data["documento_pais"].strip().upper()

        if len(pais) != 2:
            return "documento_pais debe tener exactamente 2 caracteres."

        data["documento_pais"] = pais

    if "tipo_documento" in data:
        tipo = data["tipo_documento"].strip().upper()

        if tipo not in TIPOS_DOCUMENTO:
            return "tipo_documento no es válido."

        data["tipo_documento"] = tipo

    if "fecha_nacimiento" in data:
        valor = data["fecha_nacimiento"]

        if valor is None or valor == "":
            data["fecha_nacimiento"] = None
        else:
            try:
                data["fecha_nacimiento"] = date.fromisoformat(valor)
            except (ValueError, TypeError):
                return "fecha_nacimiento debe tener formato YYYY-MM-DD."

    # Validar longitudes según el esquema SQL.
    longitudes = {
        "nombres": 100,
        "apellidos": 100,
        "tipo_documento": 20,
        "documento_numero": 30,
        "sexo": 20,
        "telefono": 30
    }

    for campo, longitud in longitudes.items():
        valor = data.get(campo)

        if valor is not None:
            if not isinstance(valor, str) or len(valor) > longitud:
                return f"El campo '{campo}' no es válido."

    return None


def obtener_paciente(paciente_id):
    return db.session.get(Paciente, paciente_id)


# GET: listar pacientes activos
@pacientes_bp.route("/api/pacientes", methods=["GET"])
def listar_pacientes():
    incluir_inactivos = (
        request.args.get("incluir_inactivos", "false").lower() == "true"
    )

    consulta = db.select(Paciente)

    if not incluir_inactivos:
        consulta = consulta.where(Paciente.activo.is_(True))

    pacientes = db.session.execute(
        consulta.order_by(Paciente.apellidos, Paciente.nombres)
    ).scalars().all()

    return {
        "total": len(pacientes),
        "pacientes": [serializar_paciente(p) for p in pacientes]
    }, 200


# ---------------------------------------------------------
# PACIENTES
# ---------------------------------------------------------

# GET: obtener un paciente
@pacientes_bp.route("/api/pacientes/<uuid:paciente_id>", methods=["GET"])
def obtener_paciente_por_id(paciente_id):
    paciente = obtener_paciente(paciente_id)

    if not paciente:
        return {"error": "Paciente no encontrado."}, 404

    return serializar_paciente(paciente), 200


# POST: registrar paciente
@pacientes_bp.route("/api/pacientes", methods=["POST"])
def crear_paciente():
    data = request.get_json(silent=True)

    error = validar_datos(data)

    if error:
        return {"error": error}, 400

    paciente = Paciente(
        nombres=data["nombres"].strip(),
        apellidos=data["apellidos"].strip(),
        documento_pais=data["documento_pais"],
        tipo_documento=data["tipo_documento"],
        documento_numero=data["documento_numero"].strip(),
        fecha_nacimiento=data.get("fecha_nacimiento"),
        sexo=data.get("sexo"),
        telefono=data.get("telefono")
    )

    try:
        db.session.add(paciente)
        db.session.commit()

        return serializar_paciente(paciente), 201

    except IntegrityError:
        db.session.rollback()

        return {
            "error": "Ya existe un paciente con ese documento."
        }, 409


# PUT: actualizar paciente
@pacientes_bp.route("/api/pacientes/<uuid:paciente_id>", methods=["PUT"])
def actualizar_paciente(paciente_id):
    paciente = obtener_paciente(paciente_id)

    if not paciente:
        return {"error": "Paciente no encontrado."}, 404

    data = request.get_json(silent=True)

    error = validar_datos(data, parcial=True)

    if error:
        return {"error": error}, 400

    campos_permitidos = [
        "nombres",
        "apellidos",
        "documento_pais",
        "tipo_documento",
        "documento_numero",
        "fecha_nacimiento",
        "sexo",
        "telefono"
    ]

    for campo in campos_permitidos:
        if campo in data:
            valor = data[campo]

            if isinstance(valor, str):
                valor = valor.strip()

            setattr(paciente, campo, valor)

    try:
        db.session.commit()
        return serializar_paciente(paciente), 200

    except IntegrityError:
        db.session.rollback()

        return {
            "error": "El documento ya está registrado para otro paciente."
        }, 409


# DELETE: desactivar paciente (baja lógica)
@pacientes_bp.route("/api/pacientes/<uuid:paciente_id>", methods=["DELETE"])
def desactivar_paciente(paciente_id):
    paciente = obtener_paciente(paciente_id)

    if not paciente:
        return {"error": "Paciente no encontrado."}, 404

    if not paciente.activo:
        return {"mensaje": "El paciente ya se encuentra inactivo."}, 200

    paciente.activo = False
    db.session.commit()

    return {
        "mensaje": "Paciente desactivado correctamente.",
        "id": str(paciente.id)
    }, 200
