# Sólo para verificar la correcta importación de los modelos

from sqlalchemy import inspect
from sqlalchemy.orm import configure_mappers

from app import create_app, db

# Registrar los 13 modelos
from app.models import (
    Paciente,
    Responsable,
    PacienteResponsable,
    PerfilCorporal,
    TipoCondicion,
    CondicionPaciente,
    LecturaGlucometro,
    ConfiguracionAlertasGlucosa,
    Alerta,
    Notificacion,
    TratamientoMedicacion,
    HorarioMedicacion,
    EjecucionRecordatorio,
)


app = create_app()

with app.app_context():

    # 1. Validar relaciones entre modelos
    configure_mappers()
    print("OK: relaciones entre modelos")

    # 2. Validar que existan las 13 tablas en PostgreSQL
    tablas_bd = set(inspect(db.engine).get_table_names())
    tablas_modelos = set(db.metadata.tables.keys())

    faltantes = tablas_modelos - tablas_bd

    if faltantes:
        print("ERROR: faltan tablas en PostgreSQL:", faltantes)
    else:
        print(f"OK: {len(tablas_modelos)} tablas registradas y existentes")

    # 3. Probar una consulta real
    paciente = db.session.execute(
        db.select(Paciente).limit(1)
    ).scalar_one_or_none()

    print("OK: consulta a paciente ejecutada")
