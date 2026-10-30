# punto de entrada de la aplicación Flask.

from app import create_app

# inicia la aplicación Flask.
app = create_app()

if __name__ == "__main__":
    # levanta el servidor
    # TODO: Desactivar el modo debug antes de pasar a producción.
    app.run(host="127.0.0.1", port=5000, debug=True)
