# /api/controllers/auth_controller.py
import bcrypt
import re
from ..database import supabase

def login_usuario(email_input, senha_input):
    """ Tenta logar um usuário. Retorna (dados_usuario, erro). """
    try:
        result = supabase.table("tb_usuario").select("id_usuario, nome, senha, is_admin").eq("email", email_input).limit(1).execute()
        
        if not result.data:
            return None, "Email ou senha incorretos."

        usuario = result.data[0]
        stored_senha_hash = usuario['senha'].encode('utf-8')
        
        if bcrypt.checkpw(senha_input.encode('utf-8'), stored_senha_hash):
            dados_sessao = {
                'id_usuario': usuario['id_usuario'],
                'nome_usuario': usuario['nome'],
                'is_admin': usuario.get('is_admin', False)
            }
            return dados_sessao, None
        else:
            return None, "Email ou senha incorretos."
            
    except Exception as e:
        print(f"Erro no login_usuario: {e}") 
        return None, f"Ocorreu um erro no servidor: {e}"

def cadastrar_usuario(dados_formulario):
    """ Tenta cadastrar um novo usuário (cliente). Retorna (dados_usuario, erro). """
    try:
        nome = dados_formulario.get('nome')
        cpf = dados_formulario.get('cpf')
        email = dados_formulario.get('email')
        senha = dados_formulario.get('senha')

        cpf_limpo = re.sub(r'\D', '', cpf)
        
        existing_user = supabase.table("tb_usuario").select("id_usuario").or_(f"cpf.eq.{cpf_limpo},email.eq.{email}").limit(1).execute()
        if existing_user.data:
            return None, 'Este CPF ou Email já está cadastrado.'
        
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        supabase.table("tb_usuario").insert({
            "nome": nome, 
            "cpf": cpf_limpo, 
            "email": email, 
            "senha": senha_hash, 
            "is_admin": False
        }).execute()
        result = supabase.table("tb_usuario").select("id_usuario, nome, is_admin").eq("email", email).limit(1).execute()
        if result.data:
            usuario = result.data[0]
            dados_sessao = {
                'id_usuario': usuario['id_usuario'],
                'nome_usuario': usuario['nome'],
                'is_admin': usuario.get('is_admin', False)
            }
            return dados_sessao, None
        else:
            return None, "Erro ao buscar usuário recém-criado."

    except Exception as e:
        print(f"Erro no cadastrar_usuario: {e}")
        return None, f"Ocorreu um erro ao cadastrar: {e}"