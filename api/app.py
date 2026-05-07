import os
from flask import Flask, session, redirect, url_for, render_template
from supabase import create_client, Client
from dotenv import load_dotenv
from api.routes.auth_routes import auth_bp
from api.routes.usuario_routes import usuario_bp
from api.routes.financeiro_routes import financeiro_bp

load_dotenv()

# Inicialização Supabase
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "uma-chave-secreta-padrao")

# Registro dos Blueprints (A organização vive aqui)
app.register_blueprint(auth_bp)
app.register_blueprint(usuario_bp)
app.register_blueprint(financeiro_bp)

# --- ROTAS DE NÍVEL SUPERIOR (Dashboard e Home) ---
@app.route('/')
def home():
    if session.get('logged_in'):
        return redirect(url_for('admin') if session.get('id_grupo') == 1 else url_for('inicio'))
    return redirect(url_for('auth.login'))

@app.route('/inicio')
def inicio():
    return render_template('inicio.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/admin/configuracoes')
def configuracoes():
    return render_template('configuracoes/configuracoes.html', back_url=url_for('admin'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)