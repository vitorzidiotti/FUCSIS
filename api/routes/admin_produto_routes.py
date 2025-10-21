# /api/routes/admin_produto_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..utils.decorators import admin_required, nocache
from ..controllers import admin_produto_controller

produto_bp = Blueprint(
    'produto', __name__,
    template_folder='../../templates/produto'
)

@produto_bp.route('/')
@admin_required()
@nocache
def gerenciar_produtos():
    termo_busca = request.args.get('q', '').strip()
    produtos, erro = admin_produto_controller.listar_produtos(termo_busca)
    
    if erro:
        flash(f"Erro ao carregar produtos: {erro}", "erro")
        
    return render_template('gerenciar_produtos.html', produtos=produtos, termo_busca=termo_busca)

@produto_bp.route('/adicionar', methods=['GET', 'POST'])
@admin_required()
def adicionar_produto():
    if request.method == 'POST':
        sucesso, erro = admin_produto_controller.adicionar_novo_produto(request.form)
        
        if sucesso:
            flash("Produto adicionado com sucesso!", "sucesso")
            return redirect(url_for('produto.gerenciar_produtos'))
        else:
            flash(f"Erro ao adicionar produto: {erro}", "erro")
            
    return render_template('adicionar_produto.html')

@produto_bp.route('/editar/<int:id_produto>', methods=['GET', 'POST'])
@admin_required()
def editar_produto(id_produto):
    if request.method == 'POST':
        sucesso, erro = admin_produto_controller.atualizar_produto_existente(id_produto, request.form)
        
        if sucesso:
            flash("Produto atualizado com sucesso!", "sucesso")
            return redirect(url_for('produto.gerenciar_produtos'))
        else:
            flash(f"Erro ao atualizar produto: {erro}", "erro")

    # Se for GET ou se o POST falhar
    produto, erro = admin_produto_controller.get_produto_por_id(id_produto)
    if erro:
        flash(f"Não foi possível carregar o produto: {erro}", "erro")
        return redirect(url_for('produto.gerenciar_produtos'))
        
    return render_template('editar_produto.html', produto=produto)

@produto_bp.route('/excluir/<int:id_produto>', methods=['POST'])
@admin_required()
def excluir_produto(id_produto):
    sucesso, erro = admin_produto_controller.excluir_produto_por_id(id_produto)
    
    if sucesso:
        flash("Produto excluído com sucesso!", "sucesso")
    else:
        flash(f"Erro ao excluir produto: {erro}", "erro")
        
    return redirect(url_for('produto.gerenciar_produtos'))