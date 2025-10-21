# /api/controllers/admin_produto_controller.py
from ..database import supabase 

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
    """ Busca produtos ativos (para o form de nova venda). """
    try:
        produtos = supabase.table("tb_produto").select("*").eq('ativo', True).order("nome").execute().data
        return produtos, None
    except Exception as e:
        print(f"Erro no get_produtos_ativos_para_venda: {e}")
        return [], f"Não foi possível carregar os produtos: {e}"

def adicionar_novo_produto(dados_formulario):
    """ Admin adiciona um novo produto. """
    try:
        dados = {
            "nome": dados_formulario.get('nome'), 
            "marca": dados_formulario.get('marca'),
            "preco": float(dados_formulario.get('preco', 0)), 
            "estoque": 0, # Estoque inicial é 0 via formulário
            "validade": dados_formulario.get('validade') or None
        }
        supabase.table("tb_produto").insert(dados).execute()
        return True, None
    except Exception as e:
        print(f"Erro no adicionar_novo_produto: {e}")
        return False, f"Erro ao adicionar produto: {e}"

def atualizar_produto_existente(id_produto, dados_formulario):
    """ Admin atualiza um produto existente. """
    try:
        dados = {
            "nome": dados_formulario.get('nome'), 
            "marca": dados_formulario.get('marca'),
            "preco": float(dados_formulario.get('preco', 0)), 
            "estoque": int(dados_formulario.get('estoque', 0)),
            "validade": dados_formulario.get('validade') or None
        }
        supabase.table("tb_produto").update(dados).eq("id_produto", id_produto).execute()
        return True, None
    except Exception as e:
        print(f"Erro no atualizar_produto_existente: {e}")
        return False, f"Erro ao atualizar produto: {e}"

def excluir_produto_por_id(id_produto):
    """ Admin exclui um produto, com verificação de dependências. """
    try:
        # 1. Verifica movimentos de estoque
        movimentos = supabase.table("tb_estoque_mov").select("id_mov", count='exact').eq("id_produto", id_produto).execute()
        if movimentos.count > 0:
            return False, "Este produto não pode ser excluído, pois possui um histórico de movimentações."
        
        # 2. Verifica itens de venda
        itens_venda = supabase.table("tb_venda_item").select("id_venda_item", count='exact').eq("id_produto", id_produto).execute()
        if itens_venda.count > 0:
            return False, "Este produto não pode ser excluído, pois está associado a vendas."

        # 3. Exclui o produto
        supabase.table("tb_produto").delete().eq("id_produto", id_produto).execute()
        return True, None
    except Exception as e:
        print(f"Erro no excluir_produto_por_id: {e}")
        return False, str(e)