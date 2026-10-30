# Ruta de health check para verificar la conexión con la base de datos.

from flask import Blueprint
from sqlalchemy import text

from app import db

health_bp = Blueprint("health", __name__)

# TODO: por ahora:  http://127.0.0.1:5000/api/health
@health_bp.route("/api/health", methods=["GET"])
def health():
    try:
        # Comprobar conexión con PostgreSQL
        db.session.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected"
        }, 200

    except Exception as e:
        db.session.rollback()

        return {
            "status": "error",
            "database": "disconnected",
            "detail": str(e)
        }, 500
