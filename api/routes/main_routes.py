from flask import Blueprint, render_template, url_for
from ..controllers.main_controller import home_ctrl, inicio_ctrl, perfil_ctrl
from ..utils.auth_middleware import login_required
from ..utils.decorators import admin_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return home_ctrl()

@main_bp.route('/inicio')
@login_required
def inicio():
    return inicio_ctrl()

# ADICIONADO: Rota do Dashboard Admin
@main_bp.route('/admin')
@admin_required() # Garante que só o grupo 1 acesse
def admin():
    return render_template('admin.html')

@main_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    return perfil_ctrl()