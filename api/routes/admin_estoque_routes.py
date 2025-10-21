# /api/routes/admin_estoque_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..utils.decorators import admin_required, nocache
from ..controllers import admin_estoque_controller

estoque_bp = Blueprint(
    'estoque', __name__,
    template_folder='../../templates/estoque'
)

@estoque_bp.route('/')
@admin_required()
@nocache
def estoque_mov():
    movimentos, erro_mov = admin_estoque_controller.listar_movimentacoes_estoque()
    produtos, erro_prod = admin_estoque_controller.get_produtos_para_estoque()
    
    if erro_mov:
        flash(f"Não foi possível carregar o histórico de estoque: {erro_mov}", "erro")
    if erro_prod:
        flash(f"Não foi possível carregar os produtos: {erro_prod}", "erro")

    return render_template('estoque.html', movimentos=movimentos, produtos=produtos)

@estoque_bp.route('/adicionar', methods=['POST'])
@admin_required()
def adicionar_movimento():
    sucesso, erro = admin_estoque_controller.adicionar_movimento_estoque(
        id_produto=request.form.get('id_produto'),
        tipo_mov=request.form.get('tipo_mov'),
        quantidade=request.form.get('quantidade'),
        motivo=request.form.get('motivo')
    )
    
    if sucesso:
        flash("Movimentação registrada com sucesso!", "sucesso")
    else:
        flash(f"Erro ao registrar movimentação: {erro}", "erro")
        
    return redirect(url_for('estoque.estoque_mov'))