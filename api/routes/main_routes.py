from flask import Blueprint, render_template, url_for
from ..controllers.main_controller import home_ctrl, inicio_ctrl, perfil_ctrl
from ..utils.decorators import admin_required, login_required 

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return home_ctrl()

@main_bp.route('/inicio')
@login_required()
def inicio():
    return inicio_ctrl()

@main_bp.route('/admin')
@admin_required() 
def admin():
    return render_template('admin.html')

@main_bp.route('/perfil', methods=['GET', 'POST'])
@login_required()
def perfil():
    return perfil_ctrl()