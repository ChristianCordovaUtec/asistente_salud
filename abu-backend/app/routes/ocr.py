
from flask import Blueprint, request, jsonify, current_app

from app.servicios.ocr import procesar_glucometro


ocr_bp = Blueprint("ocr", __name__)


@ocr_bp.route("/api/ocr/glucometro", methods=["POST"])
def reconocer_glucometro():
    """
    Recibe una imagen de glucómetro y devuelve el resultado del OCR.
    No almacena la imagen ni registra lecturas en la base de datos.
    """
    if "imagen" not in request.files:
        return jsonify({
            "error": "No se recibió ninguna imagen."
        }), 400

    archivo = request.files["imagen"]

    if not archivo.filename:
        return jsonify({
            "error": "No se seleccionó ninguna imagen."
        }), 400

    if not archivo.mimetype or not archivo.mimetype.startswith("image/"):
        return jsonify({
            "error": "El archivo debe ser una imagen."
        }), 400

    imagen_bytes = archivo.read()

    if not imagen_bytes:
        return jsonify({
            "error": "La imagen está vacía."
        }), 400

    if len(imagen_bytes) > 10 * 1024 * 1024:
        return jsonify({
            "error": "La imagen supera el tamaño máximo de 10 MB."
        }), 400

    try:
        resultado = procesar_glucometro(imagen_bytes)

        return jsonify(resultado), 200

    except ValueError as e:
        return jsonify({
            "error": str(e)
        }), 400

    except Exception:
        current_app.logger.exception(
            "Error procesando imagen del glucómetro."
        )

        return jsonify({
            "error": "No se pudo procesar la imagen."
        }), 500
