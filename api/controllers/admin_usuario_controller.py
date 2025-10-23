# /api/controllers/admin_usuario_controller.py
import bcrypt
import re
from ..database import supabase

def listar_usuarios(termo_busca):
    """ Lista todos os usuários (admin), com filtro de busca. """
    try:
        query = supabase.table("tb_usuario").select("*").order("nome")
        if termo_busca:
            query = query.ilike('nome', f'%{termo_busca}%')
        usuarios = query.execute().data
        return usuarios, None
    except Exception as e:
        print(f"Erro no listar_usuarios: {e}")
        return [], f"Erro ao carregar usuários: {e}"

def get_usuario_por_id(id_usuario):
    """ Busca um usuário específico pelo ID. """
    try:
        usuario = supabase.table("tb_usuario").select("*").eq("id_usuario", id_usuario).single().execute().data
        return usuario, None
    except Exception as e:
        print(f"Erro no get_usuario_por_id: {e}")
        return None, f"Erro ao carregar usuário: {e}"

def adicionar_novo_usuario_admin(dados_formulario):
    """ Admin adiciona um novo usuário (admin ou não). """
    try:
        nome = dados_formulario.get('nome')
        email = dados_formulario.get('email')
        cpf = dados_formulario.get('cpf')
        senha = dados_formulario.get('senha')
        is_admin = dados_formulario.get('is_admin') == 'on' # Checkbox

        cpf_limpo = re.sub(r'\D', '', cpf)
        
        existing = supabase.table("tb_usuario").select("id_usuario").or_(f"cpf.eq.{cpf_limpo},email.eq.{email}").execute().data
        if existing:
            return False, "Já existe um usuário com este CPF ou Email."

        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        supabase.table("tb_usuario").insert({
            "nome": nome, 
            "email": email, 
            "cpf": cpf_limpo, 
            "senha": senha_hash, 
            "is_admin": is_admin
        }).execute()
        
        return True, None
    except Exception as e:
        print(f"Erro no adicionar_novo_usuario_admin: {e}")
        return False, f"Erro ao adicionar usuário: {e}"

def atualizar_usuario_admin(id_usuario, dados_formulario):
    """ Admin atualiza um usuário existente. """
    try:
        dados_update = {
            'nome': dados_formulario.get('nome'), 
            'email': dados_formulario.get('email'), 
            'is_admin': dados_formulario.get('is_admin') == 'on',
            'cpf': dados_formulario.get('cpf') 
        }
        
        # Opcional: Atualizar senha se ela for fornecida
        senha = dados_formulario.get('senha')
        if senha:
            senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            dados_update['senha'] = senha_hash
            
        supabase.table("tb_usuario").update(dados_update).eq("id_usuario", id_usuario).execute()
        return True, None
    except Exception as e:
        print(f"Erro no atualizar_usuario_admin: {e}")
        return False, f"Erro ao atualizar usuário: {e}"

def excluir_usuario_admin(id_usuario_a_excluir, id_usuario_logado):
    """ Admin exclui um usuário. """
    try:
        if id_usuario_a_excluir == id_usuario_logado:
            return False, "Você não pode excluir sua própria conta."
            
        supabase.table("tb_usuario").delete().eq("id_usuario", id_usuario_a_excluir).execute()
        return True, None
    except Exception as e:
        print(f"Erro no excluir_usuario_admin: {e}")
        return False, f"Erro ao excluir usuário: {e}"
    
    
def listar_apenas_clientes():
    """ Lista apenas usuários que são clientes (is_admin=False). """
    try:
        query = supabase.table("tb_usuario").select("*").eq("is_admin", False).order("nome")
        clientes = query.execute().data
        return clientes, None
    except Exception as e:
        print(f"Erro no listar_apenas_clientes: {e}")
        return [], f"Erro ao carregar clientes: {e}"    