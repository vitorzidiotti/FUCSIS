# /api/routes/auth_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from controllers import auth_controller # Lembre-se de manter o import corrigido!

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        dados_sessao, erro = auth_controller.login_usuario(email, senha)
        
        if erro:
            flash(erro, 'erro')
            # 🔴 CORRIGIDO AQUI
            return render_template('autenticacao/login.html') 
        
        session['logged_in'] = True
        session['id_usuario'] = dados_sessao['id_usuario']
        session['nome_usuario'] = dados_sessao['nome_usuario']
        session['id_grupo'] = dados_sessao.get('id_grupo') # Atualizado para id_grupo
        
        flash(f"Bem-vindo(a), {dados_sessao['nome_usuario']}!", 'sucesso')
        
        if session['id_grupo'] == 1:
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('inicio'))
            
    # 🔴 CORRIGIDO AQUI
    return render_template('autenticacao/login.html') 

@auth_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        dados_sessao, erro = auth_controller.cadastrar_usuario(request.form)
        
        if erro:
            flash(erro, 'erro')
            # 🔴 CORRIGIDO AQUI
            return render_template('autenticacao/cadastro.html') 
        
        # Se deu tudo certo no cadastro, você pode decidir se loga ele direto ou manda pro login
        flash("Cadastro realizado com sucesso! Faça login.", 'sucesso')
        return redirect(url_for('auth.login'))

    # 🔴 CORRIGIDO AQUI
    return render_template('autenticacao/cadastro.html') 

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'sucesso')
    return redirect(url_for('auth.login'))