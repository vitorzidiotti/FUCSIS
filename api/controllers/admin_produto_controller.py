# /api/controllers/admin_produto_controller.py
from ..database import supabase
from datetime import date
from typing import List, Tuple, Optional, Any

# --- Função listar_produtos ---
def listar_produtos(termo_busca):
    """ Lista todos os produtos, com filtro de busca. """
    try:
        query = supabase.table("tb_produto").select("*").order("nome")
        if termo_busca:
            query = query.ilike('nome', f'%{termo_busca}%')
        produtos = query.execute().data
        return produtos, None
    except Exception as e:
        print(f"Erro no listar_produtos: {e}")
        return [], f"Erro ao carregar produtos: {e}"

def get_produto_por_id(id_produto):
    """ Busca um produto específico pelo ID. """
    try:
        produto = supabase.table("tb_produto").select("*").eq("id_produto", id_produto).single().execute().data
        return produto, None
    except Exception as e:
        print(f"Erro no get_produto_por_id: {e}")
        return None, f"Não foi possível carregar o produto: {e}"

def get_produtos_ativos_para_venda():
    """ Busca produtos (presumivelmente ativos) para o form de nova venda. """
    try:
        produtos = supabase.table("tb_produto").select("*").order("nome").execute().data
        return produtos, None
    except Exception as e:
        print(f"Erro no get_produtos_ativos_para_venda: {e}")
        return [], f"Não foi possível carregar os produtos: {e}"

def adicionar_novo_produto(dados_formulario):
    """ Admin adiciona um novo produto, com todos os campos obrigatórios e validação de data. """
    try:
        nome = dados_formulario.get('nome')
        marca = dados_formulario.get('marca')
        preco_str = dados_formulario.get('preco')
        medida = dados_formulario.get('medida')
        validade_str = dados_formulario.get('validade')
        lote = dados_formulario.get('lote')

        if not nome: return False, "O Nome é obrigatório."
        if not marca: return False, "A Marca é obrigatória."
        if not preco_str: return False, "O Preço é obrigatório."
        if not medida: return False, "A Medida é obrigatória."
        if not validade_str: return False, "A Validade é obrigatória."
        if not lote: return False, "O Lote é obrigatório."

        try:
            preco = float(preco_str)
            if preco < 0: return False, "O Preço não pode ser negativo."
        except ValueError:
            return False, "O Preço deve ser um número válido."

        try:
            validade_date = date.fromisoformat(validade_str)
            today = date.today()
            if validade_date < today: 
                return False, "A data de validade não pode ser anterior a hoje."
        except ValueError:
            return False, "Formato inválido para a data de validade (use YYYY-MM-DD)."

        dados = {
            "nome": nome,
            "marca": marca,
            "preco": preco,
            "estoque": 0,
            "validade": validade_str,
            "lote": lote,
            "medida": medida
        }
        supabase.table("tb_produto").insert(dados).execute()
        return True, None

    except Exception as e:
        print(f"Erro no adicionar_novo_produto: {e}")
        error_message = getattr(e, 'message', str(e))
        return False, f"Erro ao adicionar produto: {error_message}"


def atualizar_produto_existente(id_produto, dados_formulario):
    """ Admin atualiza um produto existente, com validações (exceto estoque). """
    try:
        nome = dados_formulario.get('nome')
        marca = dados_formulario.get('marca')
        preco_str = dados_formulario.get('preco')
        medida = dados_formulario.get('medida')
        validade_str = dados_formulario.get('validade')
        lote = dados_formulario.get('lote')

        if not nome: return False, "O Nome é obrigatório."
        if not marca: return False, "A Marca é obrigatória."
        if not preco_str: return False, "O Preço é obrigatório."
        if not medida: return False, "A Medida é obrigatória."
        if not validade_str: return False, "A Validade é obrigatória."
        if not lote: return False, "O Lote é obrigatório."

        try:
            preco = float(preco_str)
            if preco < 0: return False, "O Preço não pode ser negativo."
        except ValueError:
            return False, "O Preço deve ser um número válido."

        try:
            validade_date = date.fromisoformat(validade_str) 
            today = date.today()
            if validade_date < today:
                return False, "A data de validade não pode ser anterior a hoje."
        except ValueError:
            return False, "Formato inválido para a data de validade (use YYYY-MM-DD)."

        dados = {
            "nome": nome,
            "marca": marca,
            "preco": preco,
            "validade": validade_str,
            "lote": lote,
            "medida": medida
            }
        supabase.table("tb_produto").update(dados).eq("id_produto", id_produto).execute()
        return True, None

    except Exception as e:
        print(f"Erro no atualizar_produto_existente: {e}")
        error_message = getattr(e, 'message', str(e))
        return False, f"Erro ao atualizar produto: {error_message}"

def excluir_produto_por_id(id_produto):
    """ Admin exclui um produto, com verificação de dependências. """
    try:
        movimentos = supabase.table("tb_estoque_mov").select("id_mov", count='exact').eq("id_produto", id_produto).execute()
        if movimentos.count > 0:
            return False, "Este produto não pode ser excluído, pois possui um histórico de movimentações."
        itens_venda = supabase.table("tb_venda_item").select("id_venda_item", count='exact').eq("id_produto", id_produto).execute()
        if itens_venda.count > 0:
            return False, "Este produto não pode ser excluído, pois está associado a vendas."
        supabase.table("tb_produto").delete().eq("id_produto", id_produto).execute()
        return True, None
    except Exception as e:
        print(f"Erro no excluir_produto_por_id: {e}")
        return False, str(e)