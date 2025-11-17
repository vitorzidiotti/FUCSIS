from ..database import supabase
from typing import List, Tuple, Optional, Any

def listar_movimentacoes_estoque(page=1, per_page=10):
    """
    Lista o histórico de movimentações de estoque com paginação.
    """
    try:
        offset = (page - 1) * per_page
        query = supabase.table("tb_estoque_mov").select(
            "*, tb_produto(nome, marca)", 
            count='exact'
        ).order(
            "criado_em", desc=True
        ).range(
            offset, offset + per_page - 1
        )
        
        response = query.execute()
        movimentos = response.data
        total_count = response.count
        return movimentos, total_count, None
        
    except Exception as e:
        print(f"Erro no listar_movimentacoes_estoque: {e}")
        return [], 0, f"Não foi possível carregar o histórico: {e}"

def adicionar_movimento_estoque(id_produto, tipo_mov, quantidade, motivo):
    """
    (INTERNA) Registra UM movimento e atualiza UM saldo.
    """
    try:
        produto_response = supabase.table("tb_produto").select("id_produto, nome, estoque").eq("id_produto", id_produto).maybe_single().execute()
        produto = produto_response.data
        
        if not produto:
            return False, f"Produto ID {id_produto} não encontrado."

        try:
            quantidade_int = int(quantidade)
            if quantidade_int <= 0:
                return False, f"Quantidade inválida ({quantidade}) para produto ID {id_produto}."
        except ValueError:
            return False, f"Quantidade inválida ({quantidade}) para produto ID {id_produto}."

        if tipo_mov == "SAIDA" and produto['estoque'] < quantidade_int:
            return False, f"Estoque insuficiente ({produto['estoque']}) para '{produto['nome']}' (ID:{id_produto})."

        novo_estoque = produto['estoque'] + quantidade_int if tipo_mov == "ENTRADA" else produto['estoque'] - quantidade_int

        try:
            supabase.table("tb_produto").update({"estoque": novo_estoque}).eq("id_produto", id_produto).execute()
            supabase.table("tb_estoque_mov").insert({
                "id_produto": id_produto,
                "tipo_mov": tipo_mov,
                "quantidade": quantidade_int,
                "motivo": motivo
            }).execute()
            
            return True, None
            
        except Exception as transaction_error:
            print(f"Erro DURANTE transação para ID {id_produto}: {transaction_error}")
            return False, f"Erro ao salvar movimento para ID {id_produto}: {transaction_error}"
            
    except Exception as e:
        print(f"Erro geral no adicionar_movimento_estoque para ID {id_produto}: {e}")
        error_message = getattr(e, 'message', str(e))
        return False, f"Erro ao processar produto ID {id_produto}: {error_message}"

def ajustar_estoque_massa(lista_ids_produtos, tipo_mov, quantidade, motivo):
    """
    Aplica uma movimentação de estoque (Entrada/Saída) para múltiplos produtos.
    (Sem alterações, mas agora usará o adicionar_movimento_estoque corrigido)
    """
    if not lista_ids_produtos:
        return False, ["Nenhum produto selecionado."]

    erros = []
    sucessos = 0
    
    try:
        quantidade_int = int(quantidade)
        if quantidade_int <= 0:
            return False, ["A quantidade deve ser um número positivo."]
    except ValueError:
        return False, ["A quantidade deve ser um número válido."]

    for id_produto_str in lista_ids_produtos:
        try:
            id_produto = int(id_produto_str)
            sucesso_item, erro_item = adicionar_movimento_estoque(id_produto, tipo_mov, quantidade_int, motivo)
            
            if not sucesso_item:
                erros.append(erro_item)
            else:
                sucessos += 1
                
        except ValueError:
            erros.append(f"ID de produto inválido: '{id_produto_str}'")
        except Exception as loop_error:
            erros.append(f"Erro inesperado processando ID '{id_produto_str}': {loop_error}")

    if not erros:
        return True, []
    else:
        if sucessos > 0:
            erros.insert(0, f"{sucessos} produto(s) atualizado(s) com sucesso, mas ocorreram erros:")
        return False, erros

def buscar_produtos_para_estoque(termo_busca: str) -> Tuple[List[Any], Optional[str]]:
    """
    Busca produtos para a tela de estoque, retornando os campos necessários.
    Busca por NOME, MARCA ou LOTE.
    """
    if not termo_busca:
        return [], None
        
    try:
        termo_like = f"%{termo_busca}%"
        filtros_or = f"nome.ilike.{termo_like},marca.ilike.{termo_like},lote.ilike.{termo_like}"
        
        query = supabase.table("tb_produto").select(
            "id_produto, nome, marca, lote, estoque"
        ).or_(
            filtros_or
        ).order(
            "nome", desc=False
        )
        
        response = query.execute()
        produtos_encontrados = response.data
        return produtos_encontrados, None
        
    except Exception as e:
        print(f"Erro no buscar_produtos_para_estoque: {e}")
        error_message = getattr(e, 'message', str(e))
        return [], f"Erro ao consultar o banco de dados: {error_message}"