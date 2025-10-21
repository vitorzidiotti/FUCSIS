# /api/routes/auth_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from ..controllers import auth_controller # <--- 1. Importa o CONTROLLER

auth_bp = Blueprint(
    'auth', __name__,
    template_folder='../../templates/auth' # Pasta dos templates (ex: login.html)
)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        # 2. Chama o CONTROLLER para fazer a lógica
        dados_sessao, erro = auth_controller.login_usuario(email, senha)
        
        if erro:
            flash(erro, 'erro')
            return render_template('login.html')
        
        # Se o login for bem-sucedido
        session['logged_in'] = True
        session['id_usuario'] = dados_sessao['id_usuario']
        session['nome_usuario'] = dados_sessao['nome_usuario']
        session['is_admin'] = dados_sessao['is_admin']
        
        flash(f"Bem-vindo(a), {dados_sessao['nome_usuario']}!", 'sucesso')
        
        if dados_sessao['is_admin']:
            return redirect(url_for('main.admin_dashboard'))
        else:
            return redirect(url_for('main.inicio'))
            
    # Se for GET
    return render_template('login.html')

@auth_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        # 3. Chama o CONTROLLER
        dados_sessao, erro = auth_controller.cadastrar_usuario(request.form)
        
        if erro:
            flash(erro, 'erro')
            return render_template('cadastro.html')
        
        # Se o cadastro for bem-sucedido, loga o usuário
        session['logged_in'] = True
        session['id_usuario'] = dados_sessao['id_usuario']
        session['nome_usuario'] = dados_sessao['nome_usuario']
        session['is_admin'] = dados_sessao['is_admin']
        
        flash(f"Bem-vindo(a), {dados_sessao['nome_usuario']}! Cadastro realizado.", 'sucesso')
        return redirect(url_for('main.inicio'))

    # Se for GET
    return render_template('cadastro.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'sucesso')
    return redirect(url_for('auth.login'))