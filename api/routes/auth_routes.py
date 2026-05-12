from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from ..controllers import auth_controller

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        dados_sessao, erro = auth_controller.login_usuario(email, senha)
        
        if erro:
            flash(erro, 'erro')
            return render_template('autenticacao/login.html') 
        
        # Salvando na sessão garantindo que os valores existam
        session.update({
            'logged_in': True,
            'id_usuario': dados_sessao.get('id_usuario'),
            'nome_usuario': dados_sessao.get('nome_usuario'),
            'id_grupo': dados_sessao.get('id_grupo')
        })
        
        flash(f"Bem-vindo(a), {dados_sessao.get('nome_usuario')}!", 'sucesso')
        
        # --- AJUSTE NO REDIRECIONAMENTO ---
        # Convertemos para int() para garantir que a comparação numérica funcione
        id_grupo = int(session.get('id_grupo', 0))
        
        if id_grupo == 1:
            return redirect(url_for('main.admin'))
        else:
            return redirect(url_for('main.inicio'))
            
    return render_template('autenticacao/login.html') 

@auth_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        _, erro = auth_controller.cadastrar_usuario(request.form)
        
        if erro:
            flash(erro, 'erro')
            return render_template('autenticacao/cadastro.html') 
        
        flash("Cadastro realizado com sucesso! Faça login.", 'sucesso')
        return redirect(url_for('auth.login'))

    return render_template('autenticacao/cadastro.html') 

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'sucesso')
    return redirect(url_for('auth.login'))