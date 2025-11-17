# /api/routes/admin_venda_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, session, jsonify
from ..utils.decorators import admin_required, nocache
from ..controllers import admin_venda_controller, admin_produto_controller, admin_usuario_controller

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
    produtos, erro_prod = admin_produto_controller.get_produtos_ativos_para_venda()
    clientes, erro_cli = admin_usuario_controller.listar_apenas_clientes() 
    
    if erro_prod:
        flash(f"Não foi possível carregar os produtos: {erro_prod}", "erro")
    if erro_cli:
        flash(f"Não foi possível carregar os clientes: {erro_cli}", "erro")

    return render_template('adicionar_venda.html', produtos=produtos, clientes=None,form_data=request.form)

@venda_bp.route('/detalhes/<int:id_venda>')
@admin_required()
@nocache
def detalhes_venda(id_venda):
    """ Mostra os itens de uma venda específica. """
    venda, itens, erro = admin_venda_controller.get_detalhes_venda(id_venda)
    if erro:
        flash(erro, "erro")
        return redirect(url_for('venda.gerenciar_vendas'))
    return render_template('detalhes_venda.html', venda=venda, itens=itens)
@venda_bp.route('/buscar_cliente', methods=['POST'])
@admin_required()
def buscar_cliente():
    """
    Endpoint de API para o JavaScript buscar dados do cliente por CPF.
    Espera um JSON com {"cpf": "..."} e retorna um JSON com os dados.
    """
    cpf_raw = request.json.get('cpf')
    
    cliente_info, erro = admin_venda_controller.buscar_cliente_por_cpf(cpf_raw)
    
    if erro:
        return jsonify({"erro": erro}), 404
        
    return jsonify(cliente_info)