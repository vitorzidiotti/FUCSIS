# /api/routes/admin_cliente_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..utils.decorators import admin_required, nocache
from ..controllers import admin_cliente_controller

# A LINHA CRÍTICA É ESTA:
cliente_bp = Blueprint(
    'cliente', __name__,
    template_folder='../../templates/cliente'
)

@cliente_bp.route('/')
@admin_required()
@nocache
def gerenciar_clientes():
    termo_busca = request.args.get('q', '').strip()
    clientes, erro = admin_cliente_controller.listar_clientes(termo_busca)
    
    if erro:
        flash(erro, "erro")
        
    return render_template('gerenciar_clientes.html', clientes=clientes, termo_busca=termo_busca)

@cliente_bp.route('/adicionar', methods=['GET', 'POST'])
@admin_required()
def adicionar_cliente():
    if request.method == 'POST':
        sucesso, erro = admin_cliente_controller.adicionar_novo_cliente(request.form)
        
        if sucesso:
            flash("Cliente adicionado com sucesso!", "sucesso")
            return redirect(url_for('cliente.gerenciar_clientes'))
        else:
            flash(erro, "erro")
            
    return render_template('adicionar_cliente.html')

@cliente_bp.route('/editar/<int:id_cliente>', methods=['GET', 'POST'])
@admin_required()
def editar_cliente(id_cliente):
    if request.method == 'POST':
        sucesso, erro = admin_cliente_controller.atualizar_cliente_existente(id_cliente, request.form)
        
        if sucesso:
            flash("Cliente atualizado com sucesso!", "sucesso")
            return redirect(url_for('cliente.gerenciar_clientes'))
        else:
            flash(erro, "erro")

    # Se for GET ou se o POST falhar
    cliente, erro = admin_cliente_controller.get_cliente_por_id(id_cliente)
    if erro:
        flash(erro, "erro")
        return redirect(url_for('cliente.gerenciar_clientes'))
        
    return render_template('editar_cliente.html', cliente=cliente)

@cliente_bp.route('/excluir/<int:id_cliente>', methods=['POST'])
@admin_required()
def excluir_cliente(id_cliente):
    sucesso, erro = admin_cliente_controller.excluir_cliente_por_id(id_cliente)
    
    if sucesso:
        flash("Cliente excluído com sucesso!", "sucesso")
    else:
        flash(erro, "erro")
        
    return redirect(url_for('cliente.gerenciar_clientes'))