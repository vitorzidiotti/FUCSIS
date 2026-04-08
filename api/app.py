import os
import datetime
import bcrypt
import re
from flask import (
    Flask, request, redirect, url_for, 
    session, render_template, flash, make_response
)
from functools import wraps
from supabase import create_client, Client
from dotenv import load_dotenv

# 1. IMPORTE O SEU BLUEPRINT DE AUTENTICAÇÃO
from routes.auth_routes import auth_bp

# --- CONFIGURAÇÃO INICIAL ---
load_dotenv()

# Configurações do Supabase
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
if not url or not key:
    raise ValueError("Erro: Variáveis SUPABASE_URL ou SUPABASE_KEY não encontradas no .env.")

supabase: Client = create_client(url, key)

# Configuração da App Flask
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "uma-chave-secreta-padrao-muito-segura")

# 2. REGISTRE O BLUEPRINT
app.register_blueprint(auth_bp)

# --- DECORATORS E FUNÇÕES HELPER ---

def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
    return no_cache

def login_required():
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'logged_in' not in session:
                flash('Por favor, faça login para acessar esta página.', 'erro')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

def admin_required():
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'logged_in' not in session:
                flash('Por favor, faça login para acessar esta página.', 'erro')
                return redirect(url_for('auth.login'))
            
            # ATUALIZADO: Usando id_grupo (Vamos assumir que 1 = Administrador)
            if session.get('id_grupo') != 1:
                flash('Você não tem permissão para acessar esta página.', 'erro')
                return redirect(url_for('inicio'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper


# --- ROTAS PRINCIPAIS ---

@app.route('/')
def home():
    if session.get('logged_in'):
        # ATUALIZADO: Usando id_grupo
        if session.get('id_grupo') == 1:
            return redirect(url_for('admin')) 
        else:
            return redirect(url_for('inicio'))
    return redirect(url_for('auth.login'))

@app.route('/inicio')
@login_required()
def inicio():
    return render_template('inicio.html')

@app.route('/perfil', methods=['GET', 'POST'])
@login_required()
def perfil():
    user_id = session.get('id_usuario')
    try:
        current_user_data = supabase.table("usuario").select("*").eq("id_usuario", user_id).single().execute().data
    except Exception as e:
        flash(f'Não foi possível carregar os dados do perfil: {e}', 'erro')
        return redirect(url_for('inicio'))

    if request.method == 'POST':
        flash('Funcionalidade de atualização de perfil em desenvolvimento.', 'info')
        return redirect(url_for('perfil'))
        
    return render_template('perfil.html', usuario=current_user_data) # Correção: adicionei o .html

# --- ROTAS DE ADMINISTRAÇÃO ---
@app.route('/admin')
@admin_required()
def admin():
    return render_template('admin.html')

@app.route('/admin/gerenciar-usuarios', methods=['GET'])
@admin_required()
@nocache
def gerenciar_usuarios():
    termo_busca = request.args.get('busca', '').strip()
    try:
        # Busca o relacionamento correto com 'nome'
        query = supabase.table("usuario").select("*, grupo_de_usuario(nome)").order("nome")
        if termo_busca:
            query = query.ilike('nome', f'%{termo_busca}%')
        usuarios = query.execute().data
        return render_template('configuracoes/usuario/gerenciar_usuarios.html', usuarios=usuarios, termo_busca=termo_busca)
    except Exception as e:
        flash(f"Erro ao carregar usuários: {e}", "erro")
        return render_template('configuracoes/usuario/gerenciar_usuarios.html', usuarios=[], termo_busca=termo_busca)

@app.route('/admin/usuarios/adicionar', methods=['GET', 'POST'])
@admin_required()
def adicionar_usuario():
    if request.method == 'POST':
        try:
            nome = request.form.get('nome')
            email = request.form.get('email')
            cpf_limpo = re.sub(r'\D', '', request.form.get('cpf'))
            senha = request.form.get('senha')
            id_grupo = request.form.get('id_grupo')

            senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            supabase.table("usuario").insert({
                "nome": nome, "email": email, "cpf": cpf_limpo, "senha": senha_hash, "id_grupo": id_grupo
            }).execute()
            
            flash("Usuário adicionado!", "sucesso")
            return redirect(url_for('gerenciar_usuarios')) # NOME DA FUNÇÃO, NÃO O CAMINHO
        except Exception as e:
            flash(f"Erro: {e}", "erro")
            
    grupos = supabase.table("grupo_de_usuario").select("*").execute().data
    return render_template('configuracoes/usuario/adicionar_usuarios.html', grupos=grupos)

@app.route('/admin/usuarios/editar/<int:id_usuario>', methods=['GET', 'POST'])
@admin_required()
def editar_usuario(id_usuario):
    if request.method == 'POST':
        try:
            dados = {
                'nome': request.form.get('nome'), 
                'email': request.form.get('email'), 
                'id_grupo': request.form.get('id_grupo')
            }
            # Se digitou senha nova, atualiza
            if request.form.get('senha'):
                dados['senha'] = bcrypt.hashpw(request.form.get('senha').encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            supabase.table("usuario").update(dados).eq("id_usuario", id_usuario).execute()
            flash("Usuário atualizado!", "sucesso")
            return redirect(url_for('gerenciar_usuarios'))
        except Exception as e:
            flash(f"Erro ao atualizar: {e}", "erro")
    
    # GET: Busca usuário e também a lista de grupos para o select
    usuario = supabase.table("usuario").select("*").eq("id_usuario", id_usuario).single().execute().data
    grupos = supabase.table("grupo_de_usuario").select("*").execute().data
    return render_template('configuracoes/usuario/editar_usuarios.html', usuario=usuario, grupos=grupos)

@app.route('/admin/usuarios/excluir/<int:id_usuario>', methods=['POST'])
@admin_required()
def excluir_usuario(id_usuario):
    if id_usuario == session.get('id_usuario'):
        flash("Você não pode se excluir.", "erro")
    else:
        supabase.table("usuario").delete().eq("id_usuario", id_usuario).execute()
        flash("Usuário removido.", "sucesso")
    return redirect(url_for('gerenciar_usuarios'))


# --- TELA DE CONFIGURAÇÕES (O MENU INTERMEDIÁRIO) ---
@app.route('/admin/configuracoes')
@admin_required()
def configuracoes():
    return render_template('configuracoes/configuracoes.html')

# --- GERENCIAMENTO DE GRUPOS ---

@app.route('/admin/gerenciar-grupos')
@admin_required()
@nocache
def gerenciar_grupos():
    try:
        # Busca todos os grupos ordenados por ID
        grupos = supabase.table("grupo_de_usuario").select("*").order("id_grupo").execute().data
        return render_template('configuracoes/grupo/gerenciar_grupos.html', grupos=grupos)
    except Exception as e:
        flash(f"Erro ao carregar grupos: {e}", "erro")
        return redirect(url_for('configuracoes'))

@app.route('/admin/grupos/adicionar', methods=['GET', 'POST'])
@admin_required()
def adicionar_grupo():
    if request.method == 'POST':
        nome = request.form.get('nome').strip()
        try:
            if not nome:
                flash("O nome do grupo é obrigatório.", "erro")
                return redirect(url_for('adicionar_grupo'))
            
            supabase.table("grupo_de_usuario").insert({"nome": nome}).execute()
            flash(f"Grupo '{nome}' criado com sucesso!", "sucesso")
            return redirect(url_for('gerenciar_grupos'))
        except Exception as e:
            flash(f"Erro ao criar grupo: {e}", "erro")
            
    return render_template('configuracoes/grupo/adicionar_grupos.html')

@app.route('/admin/grupos/editar/<int:id_grupo>', methods=['GET', 'POST'])
@admin_required()
def editar_grupo(id_grupo):
    try:
        # Busca o grupo específico
        grupo = supabase.table("grupo_de_usuario").select("*").eq("id_grupo", id_grupo).single().execute().data
    except Exception as e:
        flash("Grupo não encontrado.", "erro")
        return redirect(url_for('gerenciar_grupos'))

    if request.method == 'POST':
        novo_nome = request.form.get('nome').strip()
        try:
            supabase.table("grupo_de_usuario").update({"nome": novo_nome}).eq("id_grupo", id_grupo).execute()
            flash("Grupo atualizado com sucesso!", "sucesso")
            return redirect(url_for('gerenciar_grupos'))
        except Exception as e:
            flash(f"Erro ao atualizar: {e}", "erro")

    return render_template('configuracoes/grupo/editar_grupos.html', grupo=grupo)

@app.route('/admin/grupos/excluir/<int:id_grupo>', methods=['POST'])
@admin_required()
def excluir_grupo(id_grupo):
    # Proteção: Não deixa excluir o grupo 1 (Administrador)
    if id_grupo == 1:
        flash("O grupo Administrador não pode ser excluído.", "erro")
        return redirect(url_for('gerenciar_grupos'))
        
    try:
        # Verifica se há usuários vinculados a este grupo antes de excluir
        usuarios_no_grupo = supabase.table("usuario").select("id_usuario").eq("id_grupo", id_grupo).execute().data
        if usuarios_no_grupo:
            flash("Não é possível excluir: existem usuários vinculados a este grupo.", "erro")
            return redirect(url_for('gerenciar_grupos'))

        supabase.table("grupo_de_usuario").delete().eq("id_grupo", id_grupo).execute()
        flash("Grupo excluído com sucesso!", "sucesso")
    except Exception as e:
        flash(f"Erro ao excluir: {e}", "erro")
        
    return redirect(url_for('gerenciar_grupos'))

# Rota temporária para o erro sumir
@app.route('/admin/financeiro')
@admin_required()
def modulo_financeiro():
    flash('Módulo Financeiro em desenvolvimento.', 'info')
    return redirect(url_for('admin'))

# --- EXECUÇÃO DO APP ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)