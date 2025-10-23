# /api/controllers/admin_produto_controller.py
from ..database import supabase
from datetime import date # Importa o tipo 'date' para comparação

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

# --- Função get_produto_por_id ---
def get_produto_por_id(id_produto):
    """ Busca um produto específico pelo ID. """
    try:
        produto = supabase.table("tb_produto").select("*").eq("id_produto", id_produto).single().execute().data
        return produto, None
    except Exception as e:
        print(f"Erro no get_produto_por_id: {e}")
        return None, f"Não foi possível carregar o produto: {e}"

# --- Função get_produtos_ativos_para_venda ---
def get_produtos_ativos_para_venda():
    """ Busca produtos (presumivelmente ativos) para o form de nova venda. """
    # Se você tiver a coluna 'ativo', descomente: .eq('ativo', True)
    try:
        produtos = supabase.table("tb_produto").select("*").order("nome").execute().data
        return produtos, None
    except Exception as e:
        print(f"Erro no get_produtos_ativos_para_venda: {e}")
        return [], f"Não foi possível carregar os produtos: {e}"

# --- Função adicionar_novo_produto ---
def adicionar_novo_produto(dados_formulario):
    """ Admin adiciona um novo produto, com todos os campos obrigatórios e validação de data. """
    try:
        # Pega os dados do formulário
        nome = dados_formulario.get('nome')
        marca = dados_formulario.get('marca')
        preco_str = dados_formulario.get('preco')
        medida = dados_formulario.get('medida')
        validade_str = dados_formulario.get('validade') # Data como string 'YYYY-MM-DD'
        lote = dados_formulario.get('lote')

        # Validações de campos obrigatórios
        if not nome: return False, "O Nome é obrigatório."
        if not marca: return False, "A Marca é obrigatória."
        if not preco_str: return False, "O Preço é obrigatório."
        if not medida: return False, "A Medida é obrigatória."
        if not validade_str: return False, "A Validade é obrigatória."
        if not lote: return False, "O Lote é obrigatório."

        # Validação do Preço
        try:
            preco = float(preco_str)
            if preco < 0: return False, "O Preço não pode ser negativo."
        except ValueError:
            return False, "O Preço deve ser um número válido."

        # Validação da Data de Validade
        try:
            validade_date = date.fromisoformat(validade_str) # Converte string para objeto date
            today = date.today()
            if validade_date < today: # Compara com a data de hoje
                return False, "A data de validade não pode ser anterior a hoje."
        except ValueError:
            # Se a string não estiver no formato YYYY-MM-DD
            return False, "Formato inválido para a data de validade (use YYYY-MM-DD)."

        # Se todas as validações passaram, monta os dados para inserir
        dados = {
            "nome": nome,
            "marca": marca,
            "preco": preco,
            "estoque": 0, # Estoque inicial sempre 0 ao adicionar
            "validade": validade_str, # Salva a data como string no banco
            "lote": lote,
            "medida": medida
        }
        supabase.table("tb_produto").insert(dados).execute()
        return True, None # Sucesso

    except Exception as e: # Captura outros erros (ex: erro de banco)
        print(f"Erro no adicionar_novo_produto: {e}")
        # Tenta pegar a mensagem de erro específica do Supabase/Postgres
        error_message = getattr(e, 'message', str(e))
        return False, f"Erro ao adicionar produto: {error_message}"

# --- Função atualizar_produto_existente ---
def atualizar_produto_existente(id_produto, dados_formulario):
    """ Admin atualiza um produto existente, com validações (exceto estoque). """
    try:
        # Pega os dados do formulário
        nome = dados_formulario.get('nome')
        marca = dados_formulario.get('marca')
        preco_str = dados_formulario.get('preco')
        medida = dados_formulario.get('medida')
        validade_str = dados_formulario.get('validade') # Data como string 'YYYY-MM-DD'
        lote = dados_formulario.get('lote')

        # Validações de campos obrigatórios
        if not nome: return False, "O Nome é obrigatório."
        if not marca: return False, "A Marca é obrigatória."
        if not preco_str: return False, "O Preço é obrigatório."
        if not medida: return False, "A Medida é obrigatória."
        if not validade_str: return False, "A Validade é obrigatória."
        if not lote: return False, "O Lote é obrigatório."

        # Validação do Preço
        try:
            preco = float(preco_str)
            if preco < 0: return False, "O Preço não pode ser negativo."
        except ValueError:
            return False, "O Preço deve ser um número válido."

        # Validação da Data de Validade
        try:
            validade_date = date.fromisoformat(validade_str) # Converte string para objeto date
            today = date.today()
            if validade_date < today: # Compara com a data de hoje
                return False, "A data de validade não pode ser anterior a hoje."
        except ValueError:
            # Se a string não estiver no formato YYYY-MM-DD
            return False, "Formato inválido para a data de validade (use YYYY-MM-DD)."

        # Se todas as validações passaram, monta os dados para atualizar
        dados = {
            "nome": nome,
            "marca": marca,
            "preco": preco,
            "validade": validade_str, # Salva a data como string no banco
            "lote": lote,
            "medida": medida
            # O estoque não é atualizado nesta função
        }
        supabase.table("tb_produto").update(dados).eq("id_produto", id_produto).execute()
        return True, None # Sucesso

    except Exception as e: # Captura outros erros (ex: erro de banco)
        print(f"Erro no atualizar_produto_existente: {e}")
        # Tenta pegar a mensagem de erro específica do Supabase/Postgres
        error_message = getattr(e, 'message', str(e))
        return False, f"Erro ao atualizar produto: {error_message}"

# --- Função excluir_produto_por_id ---
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
        return True, None # Sucesso
    except Exception as e: # Captura outros erros
        print(f"Erro no excluir_produto_por_id: {e}")
        return False, str(e)