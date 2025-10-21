# /api/controllers/admin_estoque_controller.py
from ..database import supabase

def listar_movimentacoes_estoque():
    """ Lista o histórico de movimentações de estoque. """
    try:
        movimentos = supabase.table("tb_estoque_mov").select("*, tb_produto(nome)").order("criado_em", desc=True).execute()
        return movimentos.data, None
    except Exception as e:
        print(f"Erro no listar_movimentacoes_estoque: {e}")
        return [], f"Não foi possível carregar o histórico de estoque: {e}"

def get_produtos_para_estoque():
    """ Lista produtos para o formulário de movimentação. """
    try:
        produtos = supabase.table("tb_produto").select("id_produto, nome").order("nome").execute()
        return produtos.data, None
    except Exception as e:
        print(f"Erro no get_produtos_para_estoque: {e}")
        return [], str(e)

def adicionar_movimento_estoque(id_produto, tipo_mov, quantidade, motivo):
    """ 
    Registra uma movimentação de estoque (ENTRADA ou SAIDA).
    Esta é a função central que ATUALIZA O ESTOQUE.
    """
    try:
        produto = supabase.table("tb_produto").select("id_produto, nome, estoque").eq("id_produto", id_produto).single().execute().data
        if not produto:
            return False, "Produto não encontrado."

        quantidade_int = int(quantidade)
        if quantidade_int <= 0:
             return False, "A quantidade deve ser positiva."

        if tipo_mov == "SAIDA" and produto['estoque'] < quantidade_int:
            return False, f"Estoque insuficiente para '{produto['nome']}'. Disponível: {produto['estoque']}"

        # Calcula novo estoque
        novo_estoque = produto['estoque'] + quantidade_int if tipo_mov == "ENTRADA" else produto['estoque'] - quantidade_int
        
        # IMPORTANTE: Sem transações reais, fazemos em duas etapas.
        # Se a Etapa 2 falhar, a Etapa 1 não será desfeita.
        # Para um sistema de produção, isso deve ser uma única RPC (Stored Procedure) no Supabase.
        
        # Etapa 1: Atualiza o saldo de estoque na tabela de produto
        supabase.table("tb_produto").update({"estoque": novo_estoque}).eq("id_produto", id_produto).execute()
        
        # Etapa 2: Registra o movimento no histórico
        supabase.table("tb_estoque_mov").insert({
            "id_produto": id_produto, 
            "tipo_mov": tipo_mov, 
            "quantidade": quantidade_int, 
            "motivo": motivo
        }).execute()
        
        return True, None
    except Exception as e:
        print(f"Erro no adicionar_movimento_estoque: {e}")
        return False, f"Erro ao registrar movimentação: {e}"