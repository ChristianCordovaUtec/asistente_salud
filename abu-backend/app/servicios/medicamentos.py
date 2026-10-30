
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app import db
from app.models import (
    TratamientoMedicacion,
    HorarioMedicacion,
    EjecucionRecordatorio
)

# TODO: por ahora solo se maneja la zona horaria de Lima
ZONA_HORARIA = ZoneInfo("America/Lima")


def confirmar_tratamiento(tratamiento_id):
    """
    Confirma el tratamiento una vez que el paciente ha aceptado
    todos sus datos: medicamento, dosis, horarios y fechas.

    Cambia el estado a activo, registra la fecha de confirmación
    y genera todas las ejecuciones de recordatorio.
    """

    tratamiento = db.session.get(
        TratamientoMedicacion,
        tratamiento_id
    )

    if not tratamiento:
        raise ValueError("Tratamiento no encontrado.")

    if tratamiento.estado == "cancelado":
        raise ValueError("No se puede confirmar un tratamiento cancelado.")

    horarios = HorarioMedicacion.query.filter_by(
        tratamiento_id=tratamiento_id,
        activo=True
    ).all()

    if not horarios:
        raise ValueError(
            "El tratamiento debe tener al menos un horario activo."
        )

    if tratamiento.fecha_fin < tratamiento.fecha_inicio:
        raise ValueError("La fecha de fin no puede ser anterior al inicio.")

    try:
        # Registrar la confirmación solamente la primera vez.
        if tratamiento.fecha_confirmacion is None:
            tratamiento.fecha_confirmacion = datetime.now(ZONA_HORARIA)

        # Activar el tratamiento confirmado.
        tratamiento.estado = "activo"

        # Generar las ejecuciones correspondientes a todos sus horarios.
        total_generadas = generar_ejecuciones(
            tratamiento,
            horarios
        )

        db.session.commit()

        return {
            "mensaje": "Tratamiento confirmado correctamente.",
            "tratamiento_id": str(tratamiento.id),
            "estado": tratamiento.estado,
            "total_ejecuciones_generadas": total_generadas
        }

    except Exception:
        db.session.rollback()
        raise


def generar_ejecuciones(tratamiento, horarios):
    """
    Genera una ejecución por cada horario activo y por cada día
    comprendido entre fecha_inicio y fecha_fin, ambas inclusive.

    Omite las ejecuciones que ya existen para evitar duplicados.
    Debe ejecutarse dentro de la transacción de confirmación.
    """

    # Consultar las ejecuciones existentes del tratamiento.
    ejecuciones_existentes = EjecucionRecordatorio.query.filter_by(
        tratamiento_id=tratamiento.id
    ).all()

    fechas_existentes = {
        ejecucion.fecha_hora_programada
        for ejecucion in ejecuciones_existentes
    }

    nuevas_ejecuciones = []

    # Recorrer todos los días del tratamiento, incluyendo el último.
    fecha_actual = tratamiento.fecha_inicio

    while fecha_actual <= tratamiento.fecha_fin:

        # Generar una ejecución por cada horario activo.
        for horario in horarios:

            fecha_hora = datetime.combine(
                fecha_actual,
                horario.hora,
                tzinfo=ZONA_HORARIA
            )

            # No crear nuevamente una ejecución existente.
            if fecha_hora in fechas_existentes:
                continue

            ejecucion = EjecucionRecordatorio(
                tratamiento_id=tratamiento.id,
                fecha_hora_programada=fecha_hora,
                estado="pendiente"
            )

            nuevas_ejecuciones.append(ejecucion)
            fechas_existentes.add(fecha_hora)

        fecha_actual += timedelta(days=1)

    # Guardar todas las ejecuciones dentro de la transacción actual.
    if nuevas_ejecuciones:
        db.session.add_all(nuevas_ejecuciones)
        db.session.flush()

    return len(nuevas_ejecuciones)
