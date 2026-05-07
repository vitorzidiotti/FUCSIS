# api/__init__.py
import os
from flask import Flask
from .utils.filters import format_br_date, format_br_datetime

def create_app():
    # Removido o '../' pois as pastas estão dentro de 'api'
    app = Flask(__name__, 
                template_folder='templates', 
                static_folder='static')
    
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "fucsis_fallback_key_2026")

    # Registro dos filtros
    app.jinja_env.filters['format_br_date'] = format_br_date
    app.jinja_env.filters['format_br_datetime'] = format_br_datetime

    with app.app_context():
        from .routes.auth_routes import auth_bp
        from .routes.main_routes import main_bp
        from .routes.usuario_routes import usuario_bp
        from .routes.financeiro_routes import financeiro_bp

        # Registrando os Blueprints
        app.register_blueprint(auth_bp)
        app.register_blueprint(main_bp)
        app.register_blueprint(usuario_bp, url_prefix='/admin/usuarios')
        app.register_blueprint(financeiro_bp)

        return app