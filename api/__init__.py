import os
from flask import Flask
from dotenv import load_dotenv
# +++ IMPORTA OS FILTROS +++
from .utils.filters import format_br_date, format_br_datetime

# Carrega o .env (importante para rodar local, no Render ele usa as Env Vars do painel)
load_dotenv()

def create_app():
    # Mantendo seus caminhos de template e static
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # Em vez de usar Config, pegamos a secret_key direto do ambiente
    # O segundo parâmetro é uma chave de segurança caso o .env falhe
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "fucsis_fallback_key_2026")

    # Registro dos filtros do Jinja
    app.jinja_env.filters['format_br_date'] = format_br_date
    app.jinja_env.filters['format_br_datetime'] = format_br_datetime

    with app.app_context():
        # Importações internas com o ponto (.) indicando a pasta atual (api)
        from .routes.auth_routes import auth_bp
        from .routes.main_routes import main_bp
        from .routes.admin_usuario_routes import usuario_bp

        # Registrando os Blueprints
        app.register_blueprint(auth_bp, url_prefix='/')
        app.register_blueprint(main_bp, url_prefix='/')
        app.register_blueprint(usuario_bp, url_prefix='/admin/usuarios')

        return app