# /api/__init__.py
from flask import Flask
from config import Config

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)
    app.secret_key = Config.FLASK_SECRET_KEY

    with app.app_context():
        # Importar e registrar os Blueprints (as Rotas)
        from .routes.auth_routes import auth_bp
        from .routes.admin_usuario_routes import usuario_bp
        from .routes.admin_produto_routes import produto_bp
        from .routes.admin_cliente_routes import cliente_bp
        from .routes.admin_venda_routes import venda_bp
        from .routes.admin_estoque_routes import estoque_bp
        from .routes.main_routes import main_bp

        # Rotas de Autenticação (login, cadastro, etc)
        app.register_blueprint(auth_bp, url_prefix='/') 
        # Rotas principais do usuário logado (inicio, perfil)
        app.register_blueprint(main_bp, url_prefix='/')
        
        # Rotas do Admin
        app.register_blueprint(usuario_bp, url_prefix='/admin/usuarios')
        app.register_blueprint(produto_bp, url_prefix='/admin/produtos')
        app.register_blueprint(cliente_bp, url_prefix='/admin/clientes')
        app.register_blueprint(venda_bp, url_prefix='/admin/vendas')
        app.register_blueprint(estoque_bp, url_prefix='/admin/estoque')

        return app