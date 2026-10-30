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

    # Registrar blueprints de rutas
    from app.routes.health import health_bp
    from app.routes.pacientes import pacientes_bp
    from app.routes.responsables import responsables_bp
    from app.routes.perfiles_corporales import perfiles_bp
    from app.routes.condiciones import condiciones_bp
    from app.routes.lecturas_glucometro import lecturas_bp
    from app.routes.configuracion_alertas_glucosa import configuracion_alertas_bp
    from app.routes.alertas import alertas_bp
    from app.routes.notificaciones import notificaciones_bp
    from app.routes.tratamientos_medicacion import tratamientos_bp
    from app.routes.horarios_medicacion import horarios_bp
    from app.routes.ejecuciones_recordatorio import ejecuciones_recordatorio_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(pacientes_bp)
    app.register_blueprint(responsables_bp)
    app.register_blueprint(perfiles_bp)
    app.register_blueprint(condiciones_bp)
    app.register_blueprint(lecturas_bp)
    app.register_blueprint(configuracion_alertas_bp)
    app.register_blueprint(alertas_bp)
    app.register_blueprint(notificaciones_bp)
    app.register_blueprint(tratamientos_bp)
    app.register_blueprint(horarios_bp)
    app.register_blueprint(ejecuciones_recordatorio_bp)

    return app
