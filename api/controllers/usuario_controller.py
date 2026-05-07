# /api/controllers/usuario_controller.py
import bcrypt
import re
from ..database import supabase

def listar_usuarios(termo_busca=None, tipo_filtro='nome'):
    """ Lista usuários com busca avançada usando a tabela tb_usuario. """
    try:
        # Busca usuários e o nome do grupo relacionado
        query = supabase.table("tb_usuario").select("*, grupo_de_usuario(nome)")

        if termo_busca:
            if tipo_filtro == 'nome':
                query = query.ilike('nome', f'%{termo_busca}%')
            elif tipo_filtro == 'ra':
                # Filtro por RA (Registro Acadêmico) conforme solicitado
                termo_limpo = re.sub(r'[^0-9-]', '', termo_busca)
                query = query.ilike('ra', f'%{termo_limpo}%')
            elif tipo_filtro == 'email':
                query = query.ilike('email', f'%{termo_busca}%')
            elif tipo_filtro == 'grupo':
                query = query.filter('grupo_de_usuario.nome', 'ilike', f'%{termo_busca}%')

        usuarios = query.order("nome").execute().data
        return usuarios, None
    except Exception as e:
        return [], str(e)

def get_usuario_por_id(id_usuario):
    """ Busca um usuário específico pelo ID na tabela tb_usuario. """
    try:
        usuario = supabase.table("tb_usuario").select("*").eq("id_usuario", id_usuario).single().execute().data
        return usuario, None
    except Exception as e:
        return None, str(e)

def adicionar_novo_usuario_admin(dados_formulario):
    """ Adiciona usuário usando id_grupo e RA. """
    try:
        ra_limpo = re.sub(r'[^0-9-]', '', dados_formulario.get('ra', ''))
        email = dados_formulario.get('email')
        
        # Validação de duplicidade na tb_usuario
        existing = supabase.table("tb_usuario").select("id_usuario").or_(f"ra.eq.{ra_limpo},email.eq.{email}").execute().data
        if existing:
            return False, "RA ou Email já cadastrados."

        senha_hash = bcrypt.hashpw(dados_formulario.get('senha').encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        supabase.table("tb_usuario").insert({
            "nome": dados_formulario.get('nome'), 
            "email": email, 
            "ra": ra_limpo, 
            "senha": senha_hash, 
            "id_grupo": dados_formulario.get('id_grupo')
        }).execute()
        
        return True, None
    except Exception as e:
        return False, str(e)

def atualizar_usuario_admin(id_usuario, dados_formulario):
    """ Atualiza usuário na tb_usuario. """
    try:
        dados_update = {
            'nome': dados_formulario.get('nome'), 
            'email': dados_formulario.get('email'), 
            'id_grupo': dados_formulario.get('id_grupo'),
            'ra': re.sub(r'[^0-9-]', '', dados_formulario.get('ra', ''))
        }
        
        senha = dados_formulario.get('senha')
        if senha:
            dados_update['senha'] = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
        supabase.table("tb_usuario").update(dados_update).eq("id_usuario", id_usuario).execute()
        return True, None
    except Exception as e:
        return False, str(e)

def excluir_usuario_admin(id_usuario_a_excluir, id_usuario_logado):
    """ Exclui um usuário da tb_usuario. """
    try:
        if str(id_usuario_a_excluir) == str(id_usuario_logado):
            return False, "Você não pode excluir sua própria conta."
            
        supabase.table("tb_usuario").delete().eq("id_usuario", id_usuario_a_excluir).execute()
        return True, None
    except Exception as e:
        return False, str(e)

def listar_grupos():
    """ Carrega os grupos para os formulários. """
    try:
        grupos = supabase.table("grupo_de_usuario").select("*").order("nome").execute().data
        return grupos, None
    except Exception as e:
        return [], str(e)