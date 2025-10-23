# /api/__init__.py
from flask import Flask
from config import Config
# +++ 1. IMPORTA O FILTRO +++
from .utils.filters import format_br_date, format_br_datetime

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)
    app.secret_key = Config.FLASK_SECRET_KEY

    # +++ 2. REGISTRA O FILTRO NO AMBIENTE JINJA +++
    # Diz ao Jinja que `| format_br_date` nos templates deve usar nossa função Python
    app.jinja_env.filters['format_br_date'] = format_br_date
    app.jinja_env.filters['format_br_datetime'] = format_br_datetime # <-- REGISTRA O NOVO
    # +++ FIM DO REGISTRO +++

    with app.app_context():
        # --- Importa e Registra os Blueprints (Rotas) ---
        from .routes.auth_routes import auth_bp
        from .routes.main_routes import main_bp
        from .routes.admin_usuario_routes import usuario_bp
        # Lembre-se que removemos o cliente_bp
        from .routes.admin_produto_routes import produto_bp
        from .routes.admin_estoque_routes import estoque_bp
        from .routes.admin_venda_routes import venda_bp

        # --- Registra os Blueprints na Aplicação ---
        app.register_blueprint(auth_bp, url_prefix='/')
        app.register_blueprint(main_bp, url_prefix='/')
        app.register_blueprint(usuario_bp, url_prefix='/admin/usuarios')
        app.register_blueprint(produto_bp, url_prefix='/admin/produtos')
        app.register_blueprint(estoque_bp, url_prefix='/admin/estoque')
        app.register_blueprint(venda_bp, url_prefix='/admin/vendas')

        return app