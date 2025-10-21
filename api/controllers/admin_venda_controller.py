# /api/controllers/admin_venda_controller.py
from ..database import supabase
from . import admin_estoque_controller # Importa o controller de estoque
from . import admin_produto_controller # Importa o controller de produto

def listar_vendas():
    """ Lista o histórico de vendas. """
    try:
        vendas = supabase.table("tb_venda").select("*, tb_usuario(nome)").order("data_venda", desc=True).execute()
        return vendas.data, None
    except Exception as e:
        print(f"Erro no listar_vendas: {e}")
        return [], "Não foi possível carregar a lista de vendas."

def processar_nova_venda(id_usuario_logado, dados_formulario):
    """ Processa uma nova venda, valida estoque e dá baixa. """
    try:
        produtos_selecionados = dados_formulario.getlist('produtos[]')
        quantidades = dados_formulario.getlist('quantidades[]')
        # NOTA: O seu form precisa ter um campo 'id_cliente'
        id_cliente = dados_formulario.get('id_cliente') 

        if not id_cliente:
            return False, "Cliente não selecionado."
        if not produtos_selecionados:
            return False, "Nenhum produto selecionado."

        # --- Etapa 1: Pré-verificação de estoque e cálculo de total ---
        itens_para_venda = []
        valor_total_venda = 0
        
        for i, id_produto_str in enumerate(produtos_selecionados):
            id_produto = int(id_produto_str)
            qtd = int(quantidades[i])
            if qtd <= 0:
                continue # Ignora produtos com quantidade 0

            produto_data, erro = admin_produto_controller.get_produto_por_id(id_produto)
            if erro or not produto_data:
                return False, f"Produto ID {id_produto} não encontrado."
            
            if produto_data['estoque'] < qtd:
                return False, f"Venda não realizada. Estoque de '{produto_data['nome']}' (Disponível: {produto_data['estoque']}) insuficiente."
            
            preco_unitario = produto_data.get('preco', 0)
            valor_total_item = preco_unitario * qtd
            valor_total_venda += valor_total_item
            
            itens_para_venda.append({
                "id_produto": id_produto,
                "quantidade": qtd,
                "preco_unitario": preco_unitario
            })

        if not itens_para_venda:
            return False, "Nenhum item com quantidade válida."

        # --- Etapa 2: Criar o "Cabeçalho" da Venda ---
        nova_venda_dados = {
            "id_usuario": id_usuario_logado,
            "id_cliente": int(id_cliente),
            "valor_total": valor_total_venda
            # "data_venda" é automática (now()) no Supabase
        }
        venda_criada = supabase.table("tb_venda").insert(nova_venda_dados).execute().data[0]
        id_venda_nova = venda_criada['id_venda']

        # --- Etapa 3: Inserir Itens da Venda e Dar Baixa no Estoque ---
        # (Novamente, sem transações, isso é perigoso. Se falhar no meio,
        # o estoque ficará errado)
        for item in itens_para_venda:
            # 3a. Inserir o item na tb_venda_item
            item_dados = {
                "id_venda": id_venda_nova,
                "id_produto": item['id_produto'],
                "quantidade": item['quantidade'],
                "preco_unitario": item['preco_unitario']
            }
            supabase.table("tb_venda_item").insert(item_dados).execute()
            
            # 3b. Chamar o controlador de estoque para dar baixa
            motivo_baixa = f"Venda ID: {id_venda_nova}"
            admin_estoque_controller.adicionar_movimento_estoque(
                id_produto=item['id_produto'],
                tipo_mov="SAIDA",
                quantidade=item['quantidade'],
                motivo=motivo_baixa
            )
            
        return True, None # Sucesso!

    except Exception as e:
        print(f"Erro no processar_nova_venda: {e}")
        # Tentar deletar a venda recém-criada se algo deu errado
        # (Lógica de rollback manual)
        if 'id_venda_nova' in locals():
            supabase.table("tb_venda_item").delete().eq("id_venda", id_venda_nova).execute()
            supabase.table("tb_venda").delete().eq("id_venda", id_venda_nova).execute()
            
        return False, f"Ocorreu um erro crítico ao registrar a venda: {e}"