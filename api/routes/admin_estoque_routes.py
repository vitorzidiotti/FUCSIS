from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..utils.decorators import admin_required, nocache
from ..controllers import admin_estoque_controller 
import math

estoque_bp = Blueprint(
    'estoque',
    __name__,
    template_folder='../../templates/estoque'
)

@estoque_bp.route('/', methods=['GET'])
@admin_required()
@nocache
def estoque_mov():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    termo_busca_produto = request.args.get('produto_q', '').strip()
    
    produtos_encontrados = []
    erro_busca_prod = None
    
    if termo_busca_produto:
        produtos_encontrados, erro_busca_prod = admin_estoque_controller.buscar_produtos_para_estoque(termo_busca_produto)
        if erro_busca_prod:
            flash(f"Erro ao buscar produtos: {erro_busca_prod}", "erro")

    movimentos, total_count, erro_mov = admin_estoque_controller.listar_movimentacoes_estoque(page=page, per_page=per_page)
    
    if erro_mov:
        flash(f"Não foi possível carregar o histórico: {erro_mov}", "erro")

    total_pages = math.ceil(total_count / per_page) if total_count and total_count > 0 else 0

    if page <= 0:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
        movimentos, total_count, erro_mov = admin_estoque_controller.listar_movimentacoes_estoque(page=page, per_page=per_page)
        if erro_mov:
            flash(f"Não foi possível recarregar o histórico para a última página: {erro_mov}", "erro")

    return render_template(
        'estoque.html',
        movimentos=movimentos,
        termo_busca_produto=termo_busca_produto,
        produtos_encontrados=produtos_encontrados,
        page=page,
        total_pages=total_pages,
        per_page=per_page
    )

@estoque_bp.route('/salvar_ajustes_individuais', methods=['POST'])
@admin_required()
def salvar_ajustes_individuais():
    termo_busca_hidden = request.form.get('termo_busca_hidden', '')
    produto_ids = request.form.getlist('produto_id[]')
    
    if not produto_ids:
        flash("Nenhum produto foi enviado para ajuste.", "erro")
        return redirect(url_for('estoque.estoque_mov', produto_q=termo_busca_hidden))

    erros_gerais = []
    sucessos_count = 0

    for p_id in produto_ids:
        tipo_mov = request.form.get(f'tipo_mov_{p_id}')
        quantidade_str = request.form.get(f'quantidade_{p_id}')
        motivo = request.form.get(f'motivo_{p_id}')

        if not tipo_mov or not quantidade_str or not motivo or motivo.strip() == "":
            erros_gerais.append(f"Dados incompletos (Tipo, Qtd ou Motivo) para o produto ID {p_id}.")
            continue
            
        try:
            quantidade_int = int(quantidade_str)
            if quantidade_int <= 0:
                erros_gerais.append(f"Quantidade inválida para o produto ID {p_id}.")
                continue
        except ValueError:
            erros_gerais.append(f"Quantidade não numérica para o produto ID {p_id}.")
            continue

        sucesso_item, erro_item_msg = admin_estoque_controller.adicionar_movimento_estoque(
            id_produto=p_id,
            tipo_mov=tipo_mov,
            quantidade=quantidade_int,
            motivo=motivo
        )
        
        if not sucesso_item:
            erros_gerais.append(erro_item_msg)
        else:
            sucessos_count += 1

    if not erros_gerais:
        flash(f"{sucessos_count} movimentação(ões) de estoque registrada(s) com sucesso!", "sucesso")
        return redirect(url_for('estoque.estoque_mov', page=1))
    else:
        if sucessos_count > 0:
            flash(f"{sucessos_count} produto(s) atualizado(s) com sucesso. Erros nos demais:", "aviso")
        
        for erro_msg in erros_gerais:
            flash(f"Erro: {erro_msg}", "erro")
            
        return redirect(url_for('estoque.estoque_mov', produto_q=termo_busca_hidden))