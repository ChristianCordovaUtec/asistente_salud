# configuración y conexión a la BBDD.

import os
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()


class Config:
    # Configuración de PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    # Desactivar el seguimiento de modificaciones de SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # TODO: Clave de seguridad de Flask (la configuraremos posteriormente)
    SECRET_KEY = os.getenv("SECRET_KEY", "clave-local-desarrollo")
