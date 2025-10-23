# /api/controllers/admin_estoque_controller.py
from ..database import supabase

def listar_movimentacoes_estoque(page=1, per_page=10):
    """ Lista o histórico de movimentações de estoque com paginação. """
    try:
        offset = (page - 1) * per_page
        
        # Faz a query buscando os movimentos da página atual
        # E TAMBÉM pede a contagem total (count='exact')
        query = supabase.table("tb_estoque_mov").select(
            "*, tb_produto(nome)", # Seleciona tudo e o nome do produto relacionado
            count='exact' # Pede a contagem total de registros que batem com o filtro (nenhum filtro aqui)
        ).order(
            "criado_em", desc=True # Ordena pelos mais recentes primeiro
        ).range(
            offset, offset + per_page - 1 # Define o intervalo da página
        )
        
        response = query.execute()
        
        movimentos = response.data
        total_count = response.count # Pega a contagem total retornada

        return movimentos, total_count, None # Retorna movimentos da página, contagem total, sem erro

    except Exception as e:
        print(f"Erro no listar_movimentacoes_estoque: {e}")
        return [], 0, f"Não foi possível carregar o histórico de estoque: {e}" # Retorna listas vazias e erro

def get_produtos_para_estoque():
    """ Lista produtos para o formulário de movimentação. """
    try:
        # Pega apenas ID e Nome, ordenados por nome
        produtos = supabase.table("tb_produto").select("id_produto, nome").order("nome").execute()
        return produtos.data, None
    except Exception as e:
        print(f"Erro no get_produtos_para_estoque: {e}")
        return [], f"Não foi possível carregar os produtos: {e}"

def adicionar_movimento_estoque(id_produto, tipo_mov, quantidade, motivo):
    """ Registra uma movimentação e atualiza o saldo do produto. """
    try:
        # Busca o produto para validar estoque (se for saída)
        produto_response = supabase.table("tb_produto").select("id_produto, nome, estoque").eq("id_produto", id_produto).maybe_single().execute()
        produto = produto_response.data
        
        if not produto:
            return False, "Produto não encontrado."

        try:
            quantidade_int = int(quantidade)
            if quantidade_int <= 0:
                 return False, "A quantidade deve ser um número positivo."
        except ValueError:
            return False, "A quantidade deve ser um número válido."


        if tipo_mov == "SAIDA" and produto['estoque'] < quantidade_int:
            return False, f"Estoque insuficiente para '{produto['nome']}'. Disponível: {produto['estoque']}"

        # Calcula novo estoque
        novo_estoque = produto['estoque'] + quantidade_int if tipo_mov == "ENTRADA" else produto['estoque'] - quantidade_int

        # --- Transação Manual (Idealmente seria uma RPC/Stored Procedure no Supabase) ---
        try:
            # 1. Atualiza o estoque na tabela de produto
            supabase.table("tb_produto").update({"estoque": novo_estoque}).eq("id_produto", id_produto).execute()

            # 2. Registra o movimento no histórico
            supabase.table("tb_estoque_mov").insert({
                "id_produto": id_produto,
                "tipo_mov": tipo_mov,
                "quantidade": quantidade_int,
                "motivo": motivo
            }).execute()

            return True, None # Sucesso

        except Exception as transaction_error:
            # Se algo der errado aqui, o estoque pode ficar inconsistente.
            # Idealmente, faríamos um rollback, mas sem transações reais é difícil.
            print(f"Erro DURANTE a atualização de estoque/movimento: {transaction_error}")
            return False, f"Erro ao registrar movimentação após cálculo: {transaction_error}"
        # --- Fim da Transação Manual ---

    except Exception as e:
        print(f"Erro no adicionar_movimento_estoque: {e}")
        error_message = getattr(e, 'message', str(e))
        return False, f"Erro ao registrar movimentação: {error_message}"