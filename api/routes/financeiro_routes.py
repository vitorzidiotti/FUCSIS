from flask import Blueprint, render_template, url_for, request
from ..utils.decorators import admin_required, nocache
from ..controllers import financeiro_controller

financeiro_bp = Blueprint('financeiro', __name__, url_prefix='/admin/financeiro')

@financeiro_bp.route('/')
@admin_required()
@nocache
def index():
    return render_template('modulos/financeiro/index_financeiro.html', back_url=url_for('admin'))

@financeiro_bp.route('/contratos')
@admin_required()
def gerenciar_contratos():
    contratos = financeiro_controller.listar_contratos_ctrl()
    return render_template('modulos/financeiro/contratos/contratos.html', 
                           contratos=contratos, 
                           back_url=url_for('financeiro.index'))

@financeiro_bp.route('/fornecedores')
@admin_required()
def gerenciar_fornecedores():
    fornecedores = financeiro_controller.listar_fornecedores_ctrl()
    return render_template('modulos/financeiro/fornecedores/fornecedores.html', 
                           fornecedores=fornecedores, 
                           back_url=url_for('financeiro.index'))