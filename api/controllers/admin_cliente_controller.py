# /api/controllers/admin_cliente_controller.py
import re
from ..database import supabase

def listar_clientes(termo_busca):
    """ Lista todos os clientes, com filtro de busca. """
    try:
        query = supabase.table("tb_cliente").select("*").order("nome")
        if termo_busca:
            query = query.or_(f"nome.ilike.%{termo_busca}%,cpf.ilike.%{termo_busca}%")
        clientes = query.execute().data
        return clientes, None
    except Exception as e:
        print(f"Erro no listar_clientes: {e}")
        return [], f"Erro ao carregar clientes: {e}"

def get_cliente_por_id(id_cliente):
    """ Busca um cliente específico pelo ID. """
    try:
        cliente = supabase.table("tb_cliente").select("*").eq("id_cliente", id_cliente).single().execute().data
        return cliente, None
    except Exception as e:
        print(f"Erro no get_cliente_por_id: {e}")
        return None, f"Erro ao carregar cliente: {e}"

def adicionar_novo_cliente(dados_formulario):
    """ Admin adiciona um novo cliente. """
    try:
        cpf = re.sub(r'\D', '', dados_formulario.get('cpf'))
        
        existing = supabase.table("tb_cliente").select("id_cliente").eq("cpf", cpf).execute().data
        if existing:
            return False, "Cliente já cadastrado com esse CPF."
            
        dados = {
            "nome": dados_formulario.get('nome'), 
            "email": dados_formulario.get('email'), 
            "cpf": cpf
        }
        supabase.table("tb_cliente").insert(dados).execute()
        return True, None
    except Exception as e:
        print(f"Erro no adicionar_novo_cliente: {e}")
        return False, f"Erro ao adicionar cliente: {e}"

def atualizar_cliente_existente(id_cliente, dados_formulario):
    """ Admin atualiza um cliente existente. """
    try:
        dados = {
            "nome": dados_formulario.get('nome'), 
            "email": dados_formulario.get('email'), 
            "cpf": re.sub(r'\D', '', dados_formulario.get('cpf'))
        }
        supabase.table("tb_cliente").update(dados).eq("id_cliente", id_cliente).execute()
        return True, None
    except Exception as e:
        print(f"Erro no atualizar_cliente_existente: {e}")
        return False, f"Erro ao atualizar cliente: {e}"

def excluir_cliente_por_id(id_cliente):
    """ Admin exclui um cliente. """
    try:
        # Verificação de segurança: checar se o cliente tem vendas
        vendas = supabase.table("tb_venda").select("id_venda", count='exact').eq("id_cliente", id_cliente).execute()
        if vendas.count > 0:
            return False, "Este cliente não pode ser excluído, pois está associado a vendas."

        supabase.table("tb_cliente").delete().eq("id_cliente", id_cliente).execute()
        return True, None
    except Exception as e:
        print(f"Erro no excluir_cliente_por_id: {e}")
        return False, f"Erro ao excluir cliente: {e}"