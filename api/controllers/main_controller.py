# /api/controllers/main_controller.py
from ..database import supabase

def get_dados_perfil(user_id):
    """ Busca os dados completos de um usuário para a página de perfil. """
    try:
        usuario = supabase.table("tb_usuario").select("*").eq("id_usuario", user_id).single().execute().data
        return usuario, None
    except Exception as e:
        print(f"Erro no get_dados_perfil: {e}")
        return None, f"Não foi possível carregar os dados do perfil: {e}"

def atualizar_dados_perfil(user_id, dados_formulario):
    """ Atualiza os dados do perfil do usuário. """
    try:
        # NOTA: O seu código original não tinha essa lógica.
        # Aqui você implementaria a atualização de 'nome', 'email', etc.
        # CUIDADO: Se houver um campo de 'senha' no formulário,
        # ele precisa ser hasheado novamente com bcrypt antes de salvar!
        
        # Exemplo (simples, sem atualização de senha):
        dados_update = {
            'nome': dados_formulario.get('nome'),
            'email': dados_formulario.get('email')
        }
        supabase.table("tb_usuario").update(dados_update).eq("id_usuario", user_id).execute()
        return True, None
    except Exception as e:
        print(f"Erro no atualizar_dados_perfil: {e}")
        return False, f"Erro ao atualizar perfil: {e}"