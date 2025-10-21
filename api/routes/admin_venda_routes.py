# /api/routes/admin_venda_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from ..utils.decorators import admin_required, nocache
from ..controllers import admin_venda_controller, admin_produto_controller, admin_cliente_controller

venda_bp = Blueprint(
    'venda', __name__,
    template_folder='../../templates/venda'
)

@venda_bp.route('/')
@admin_required()
@nocache
def gerenciar_vendas():
    vendas, erro = admin_venda_controller.listar_vendas()
    
    if erro:
        flash(erro, "erro")
        
    return render_template('gerenciar_vendas.html', vendas=vendas)

@venda_bp.route('/adicionar', methods=['GET', 'POST'])
@admin_required()
def adicionar_venda():
    if request.method == 'POST':
        id_usuario_logado = session.get('id_usuario')
        sucesso, erro = admin_venda_controller.processar_nova_venda(id_usuario_logado, request.form)
        
        if sucesso:
            flash("Venda registrada com sucesso!", "sucesso")
            return redirect(url_for('venda.gerenciar_vendas'))
        else:
            flash(f"Erro ao registrar venda: {erro}", "erro")
            # Redireciona de volta para o form de adicionar, para não perder os dados
            return redirect(url_for('venda.adicionar_venda'))

    # Se for GET, precisa carregar os produtos e clientes para o formulário
    produtos, erro_prod = admin_produto_controller.get_produtos_ativos_para_venda()
    clientes, erro_cli = admin_cliente_controller.listar_clientes(termo_busca=None) # Lista todos
    
    if erro_prod:
        flash(f"Não foi possível carregar os produtos: {erro_prod}", "erro")
    if erro_cli:
        flash(f"Não foi possível carregar os clientes: {erro_cli}", "erro")

    return render_template('adicionar_venda.html', produtos=produtos, clientes=clientes)