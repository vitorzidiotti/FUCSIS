# /api/controllers/auth_controller.py
import bcrypt
import re
from database import supabase

def login_usuario(email_input, senha_input):
    """ Tenta logar um usuário. Retorna (dados_usuario, erro). """
    try:
        # ATUALIZADO: Usando id_grupo em vez de is_admin
        result = supabase.table("usuario").select("id_usuario, nome, senha, id_grupo").eq("email", email_input).limit(1).execute()
        
        if not result.data:
            return None, "Este usuário não está cadastrado."

        usuario = result.data[0]
        stored_senha_hash = usuario['senha'].encode('utf-8')
        
        if bcrypt.checkpw(senha_input.encode('utf-8'), stored_senha_hash):
            dados_sessao = {
                'id_usuario': usuario['id_usuario'],
                'nome_usuario': usuario['nome'],
                'id_grupo': usuario.get('id_grupo') # Guarda o ID do grupo
            }
            return dados_sessao, None
        else:
            return None, "A senha está incorreta."
            
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
        
        existing_user = supabase.table("usuario").select("id_usuario").or_(f"cpf.eq.{cpf_limpo},email.eq.{email}").limit(1).execute()
        if existing_user.data:
            return None, 'Este CPF ou Email já está cadastrado.'
        
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # ATUALIZADO: Inserindo id_grupo (Vamos assumir que 2 é o usuário padrão/cliente)
        # Ajuste esse número se no seu banco de dados o grupo de cliente for outro!
        insert_response = supabase.table("usuario").insert({
            "nome": nome, 
            "cpf": cpf_limpo, 
            "email": email, 
            "senha": senha_hash, 
            "id_grupo": 2 
        }).execute()

        # Verifica se a inserção deu certo
        if not insert_response.data:
             return None, "Erro ao inserir no banco."

        usuario_criado = insert_response.data[0]
        dados_sessao = {
            'id_usuario': usuario_criado['id_usuario'],
            'nome_usuario': usuario_criado['nome'],
            'id_grupo': usuario_criado.get('id_grupo')
        }
        return dados_sessao, None

    except Exception as e:
        print(f"Erro no cadastrar_usuario: {e}")
        return None, f"Ocorreu um erro ao cadastrar: {e}"