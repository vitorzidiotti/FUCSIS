# /api/controllers/main_controller.py
from ..database import supabase
import bcrypt

def get_dados_perfil(user_id):
    """ Busca os dados completos de um usuário para a página de perfil. """
    try:
        usuario = supabase.table("tb_usuario").select("*").eq("id_usuario", user_id).single().execute().data
        return usuario, None
    except Exception as e:
        print(f"Erro no get_dados_perfil: {e}")
        return None, f"Não foi possível carregar os dados do perfil: {e}"

def atualizar_dados_perfil(user_id, dados_formulario):
    """ Atualiza os dados do perfil do usuário.Os campos de nome/email são readonly no HTML, então esta função
    foca apenas na lógica de alteração de senha. """
    try:
        nome = dados_formulario.get('nome'),
        email = dados_formulario.get('email')
        senha_antiga = dados_formulario.get('senha_antiga')
        nova_senha = dados_formulario.get('nova_senha')
        confirmar_nova_senha = dados_formulario.get('confirmar_nova_senha')
        if not senha_antiga and not nova_senha and not confirmar_nova_senha:
            return True, None
        if not senha_antiga or not nova_senha or not confirmar_nova_senha:
            return False, "Para alterar a senha, preencha os campos: Senha Atual, Nova Senha e Confirmar Nova Senha."
        if nova_senha != confirmar_nova_senha:
            return False, "A 'Nova Senha' e a 'Confirmação' não coincidem."
        if len(nova_senha) < 6:
            return False, "A 'Nova Senha' deve ter no mínimo 6 caracteres."
        usuario_db = supabase.table("tb_usuario").select("senha").eq("id_usuario", user_id).single().execute().data
        if not usuario_db:
            return False, "Usuário não encontrado."
        hash_senha_db = usuario_db['senha'].encode('utf-8')
        if not bcrypt.checkpw(senha_antiga.encode('utf-8'), hash_senha_db):
            return False, "A 'Senha Atual' está incorreta."
        novo_hash_senha = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        supabase.table("tb_usuario").update({"senha": novo_hash_senha}).eq("id_usuario", user_id).execute()
        return True, "Senha atualizada com sucesso!"
    except Exception as e:
        print(f"Erro no atualizar_dados_perfil: {e}")
        error_message = getattr(e, 'message', str(e))
        return False, f"Erro ao atualizar perfil: {error_message}"