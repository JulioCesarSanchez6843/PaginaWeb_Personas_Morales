# app/__init__.py

from flask import Flask
import os

def create_app():
    app = Flask(__name__, template_folder='templates')

    # Clave secreta para sesiones y flash
    app.secret_key = os.environ.get('FLASK_SECRET_KEY') or 'clave_muy_secreta_y_larga_1234567890_!@#$%^&*()'

    # Importa y registra los blueprints dentro de la función
    from app.personas_morales import personas_morales_bp
    from app.views import (
    inicio_view,
    personas_morales_view,
    representantes_legales_view,
    actividades_economicas_view,  # ✅ Este es el nombre correcto
    moral_actividades_view,
    documentos_view)


    app.register_blueprint(personas_morales_bp)
    app.register_blueprint(inicio_view)
    app.register_blueprint(personas_morales_view)
    app.register_blueprint(representantes_legales_view)
    app.register_blueprint(actividades_economicas_view)
    app.register_blueprint(moral_actividades_view)
    app.register_blueprint(documentos_view)

    return app
