# /api/routes/main_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from ..utils.decorators import login_required, admin_required
from ..controllers import main_controller

main_bp = Blueprint(
    'main', __name__,
    template_folder='../../templates'
)

@main_bp.route('/')
def home():
    if session.get('logged_in'):
        if session.get('is_admin'):
            return redirect(url_for('main.admin_dashboard'))
        else:
            return redirect(url_for('main.inicio'))
    return redirect(url_for('auth.login'))

@main_bp.route('/inicio')
@login_required()
def inicio():
    return render_template('inicio.html')

@main_bp.route('/perfil', methods=['GET', 'POST'])
@login_required()
def perfil():
    user_id = session.get('id_usuario')
    
    if request.method == 'POST':
        sucesso, erro = main_controller.atualizar_dados_perfil(user_id, request.form)
        if sucesso:
            flash('Perfil atualizado com sucesso!', 'sucesso')
            session['nome_usuario'] = request.form.get('nome')
        else:
            flash(f'Erro ao atualizar perfil: {erro}', 'erro')
        return redirect(url_for('main.perfil'))

    usuario, erro = main_controller.get_dados_perfil(user_id)
    if erro:
        flash(erro, 'erro')
        return redirect(url_for('main.inicio'))
        
    return render_template('perfil.html', usuario=usuario)

@main_bp.route('/admin')
@admin_required()
def admin_dashboard():
    return render_template('admin.html')