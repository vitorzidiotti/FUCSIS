from flask import render_template, redirect, url_for, session, request, flash
from ..database import supabase
import bcrypt

def home_ctrl():
    """Gerencia o redirecionamento da página inicial baseada no login."""
    if session.get('logged_in'):
        # Grupo 1 = Administrador (conforme padrão do projeto)
        return redirect(url_for('admin')) if session.get('id_grupo') == 1 else redirect(url_for('main.inicio'))
    return redirect(url_for('auth.login'))

def inicio_ctrl():
    """Renderiza a página inicial do usuário comum."""
    return render_template('inicio.html')

def perfil_ctrl():
    """Gerencia a exibição e a atualização de senha do perfil."""
    user_id = session.get('id_usuario')
    
    if request.method == 'POST':
        sucesso, mensagem = _atualizar_senha_perfil(user_id, request.form)
        flash(mensagem, "sucesso" if sucesso else "erro")
        return redirect(url_for('main.perfil'))

    # Lógica GET: Busca dados para exibir
    try:
        usuario = supabase.table("tb_usuario").select("*").eq("id_usuario", user_id).single().execute().data
        return render_template('perfil.html', usuario=usuario)
    except Exception as e:
        flash(f"Erro ao carregar perfil: {e}", "erro")
        return redirect(url_for('main.inicio'))

def _atualizar_senha_perfil(user_id, dados_formulario):
    """Lógica interna para validar e trocar a senha."""
    senha_antiga = dados_formulario.get('senha_antiga')
    nova_senha = dados_formulario.get('nova_senha')
    confirmar_nova_senha = dados_formulario.get('confirmar_nova_senha')

    if not senha_antiga or not nova_senha:
        return False, "Preencha todos os campos para alterar a senha."
    
    if nova_senha != confirmar_nova_senha:
        return False, "A nova senha e a confirmação não coincidem."

    try:
        usuario_db = supabase.table("tb_usuario").select("senha").eq("id_usuario", user_id).single().execute().data
        if not usuario_db or not bcrypt.checkpw(senha_antiga.encode('utf-8'), usuario_db['senha'].encode('utf-8')):
            return False, "A senha atual está incorreta."

        novo_hash = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        supabase.table("tb_usuario").update({"senha": novo_hash}).eq("id_usuario", user_id).execute()
        return True, "Senha atualizada com sucesso!"
    except Exception as e:
        return False, f"Erro técnico: {str(e)}"