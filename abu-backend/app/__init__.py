# Inicialización de Flask y se conectará a la base de datos mediante SQLAlchemy.

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from app.config import Config

# Instancia global de SQLAlchemy
db = SQLAlchemy()


# Construye la aplicación Flask y la configura con SQLAlchemy.
def create_app():
    app = Flask(__name__)

    # Cargar configuración
    app.config.from_object(Config)

    # Inicializar SQLAlchemy
    db.init_app(app)

    # Registrar rutas
    from app.routes.health import health_bp
    app.register_blueprint(health_bp)

    return app
