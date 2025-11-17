from ..database import supabase
from . import admin_estoque_controller
import re 
from flask import session
from datetime import datetime

def listar_vendas():
    """ Lista o histórico de vendas, incluindo nome do vendedor e do cliente. """
    try:
        vendas = supabase.table("tb_venda").select(
            """
            *, 
            vendedor:tb_usuario!tb_venda_id_usuario_fkey(nome), 
            cliente:tb_usuario!tb_venda_id_cliente_fkey(nome)
            """
        ).order("data_venda", desc=True).execute()
        
        return vendas.data, None
    except Exception as e:
        print(f"Erro no listar_vendas (com joins): {e}")
        try:
            vendas_simples = supabase.table("tb_venda").select(
                "*, tb_usuario(nome)"
            ).order("data_venda", desc=True).execute()
            print("--- ATENÇÃO: Usando consulta 'listar_vendas' simples. Nomes de clientes não aparecerão. ---")
            return vendas_simples.data, None
        except Exception as e2:
            print(f"Erro no listar_vendas (plano B): {e2}")
            return [], "Não foi possível carregar a lista de vendas."


def processar_nova_venda(id_usuario_logado, dados_formulario):
    """ 
    Processa uma nova venda, validando o cliente pela tabela tb_usuario 
    onde is_admin = False.
    """
    
    cpf_cliente_raw = dados_formulario.get('cpf_cliente')
    if not cpf_cliente_raw:
        return False, "O CPF do cliente é obrigatório."

    cpf_limpo = re.sub(r'\D', '', cpf_cliente_raw)
    
    try:
        response = supabase.table("tb_usuario").select(
            "id_usuario"
        ).eq(
            "cpf", cpf_limpo
        ).eq(
            "is_admin", False  
        ).limit(1).execute() 
        
        if not response.data:
            return False, f"Nenhum *cliente* (com 'is_admin=False') foi encontrado com o CPF: {cpf_limpo}"
        
        cliente = response.data[0]
        id_cliente_comprador = cliente['id_usuario'] 
        
    except Exception as e:
        print(f"Erro ao buscar cliente por CPF: {e}")
        return False, f"Erro ao validar CPF: {e}"
    
    produtos_ids = dados_formulario.getlist('produtos[]')
    quantidades_str = dados_formulario.getlist('quantidades[]')

    itens_pedidos_map = {}
    for i, id_str in enumerate(produtos_ids):
        try:
            qtd = int(quantidades_str[i])
            if qtd > 0:
                itens_pedidos_map[int(id_str)] = qtd
        except (ValueError, IndexError):
            continue
            
    if not itens_pedidos_map:
        return False, "Nenhum produto com quantidade válida foi selecionado."

    try:
        ids_para_buscar = list(itens_pedidos_map.keys())
        
        produtos_db = supabase.table("tb_produto").select(
            "id_produto, nome, preco, estoque"
        ).in_(
            "id_produto", ids_para_buscar
        ).execute().data
        
        mapa_produtos_db = {p['id_produto']: p for p in produtos_db}
        
        itens_para_venda_item = [] 
        itens_para_estoque = [] 
        valor_total_venda = 0.0
        erros_validacao = []

        for id_prod, qtd_pedida in itens_pedidos_map.items():
            if id_prod not in mapa_produtos_db:
                erros_validacao.append(f"Produto ID {id_prod} não encontrado no banco.")
                continue

            produto_info = mapa_produtos_db[id_prod]
            
            if produto_info['estoque'] < qtd_pedida:
                erros_validacao.append(f"Estoque de '{produto_info['nome']}' insuficiente (Disponível: {produto_info['estoque']})")
                continue
            
            preco_unitario = produto_info.get('preco', 0)
            subtotal = preco_unitario * qtd_pedida
            valor_total_venda += subtotal
            
            itens_para_venda_item.append({
                "id_produto": id_prod,
                "quantidade": qtd_pedida,
                "preco_unitario": preco_unitario
            })
            
            itens_para_estoque.append({
                "id_produto": id_prod,
                "quantidade": qtd_pedida
            })

        if erros_validacao:
            return False, " | ".join(erros_validacao)
        
        nova_venda_dados = {
            "id_usuario": id_usuario_logado,      
            "id_cliente": int(id_cliente_comprador), 
            "total": valor_total_venda, # <-- CORREÇÃO: De 'valor_total' para 'total'
            "data_venda": datetime.now().isoformat()
        }
        
        response = supabase.table("tb_venda").insert(
            nova_venda_dados, 
            returning="representation" 
        ).execute()
        
        venda_criada = response.data[0]
        id_venda_nova = venda_criada['id_venda']

        for item in itens_para_venda_item:
            item['id_venda'] = id_venda_nova
            
        supabase.table("tb_venda_item").insert(itens_para_venda_item).execute()
        
        motivo_baixa = f"Venda ID: {id_venda_nova}"
        for item in itens_para_estoque:
            admin_estoque_controller.adicionar_movimento_estoque(
                id_produto=item['id_produto'],
                tipo_mov="SAIDA",
                quantidade=item['quantidade'],
                motivo=motivo_baixa
            )
            
        return True, "Venda registrada com sucesso!"

    except Exception as e:
        print(f"Erro no processar_nova_venda: {e}")
        if 'id_venda_nova' in locals():
            print(f"Tentando reverter Venda ID: {id_venda_nova}")
            supabase.table("tb_venda_item").delete().eq("id_venda", id_venda_nova).execute()
            supabase.table("tb_venda").delete().eq("id_venda", id_venda_nova).execute()
        
        return False, f"Ocorreu um erro crítico ao registrar a venda: {e}"
def get_detalhes_venda(id_venda):
    """
    Busca os detalhes de uma venda específica, incluindo os itens vendidos.
    """
    try:
        venda_info = supabase.table("tb_venda").select(
             """
            *, 
            vendedor:tb_usuario!tb_venda_id_usuario_fkey(nome), 
            cliente:tb_usuario!tb_venda_id_cliente_fkey(nome)
            """
        ).eq("id_venda", id_venda).single().execute().data
        
        if not venda_info:
            return None, None, "Venda não encontrada."
        itens_venda = supabase.table("tb_venda_item").select(
            "*, tb_produto(nome, marca)"
        ).eq("id_venda", id_venda).execute().data

        return venda_info, itens_venda, None

    except Exception as e:
         print(f"Erro no get_detalhes_venda: {e}")
         return None, None, f"Erro ao buscar detalhes da venda: {e}"
    
def buscar_cliente_por_cpf(cpf_raw):
    """
    Busca um cliente (is_admin=False) pelo CPF e calcula o total gasto por ele.
    """
    if not cpf_raw:
        return None, "CPF não fornecido."
        
    cpf_limpo = re.sub(r'\D', '', cpf_raw)
    
    try:
        response = supabase.table("tb_usuario").select(
            "id_usuario, nome, cpf, email"
        ).eq(
            "cpf", cpf_limpo
        ).eq(
            "is_admin", False  
        ).limit(1).execute() 

        if not response.data:
            return None, "Nenhum cliente encontrado com este CPF."

        cliente_info = response.data[0]
        id_cliente = cliente_info['id_usuario']

        vendas_response = supabase.table("tb_venda").select(
            "total"
        ).eq(
            "id_cliente", id_cliente
        ).execute()
        
        total_gasto = 0.0
        if vendas_response.data:
            total_gasto = sum(item['total'] for item in vendas_response.data)

        cliente_info['total_gasto'] = total_gasto

        return cliente_info, None

    except Exception as e:
        print(f"Erro no buscar_cliente_por_cpf: {e}")
        error_message = getattr(e, 'message', str(e))
        return None, f"Erro ao consultar banco: {error_message}"