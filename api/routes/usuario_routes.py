import re 
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from ..utils.decorators import admin_required, nocache
from ..controllers import usuario_controller

usuario_bp = Blueprint('usuario', __name__)

@usuario_bp.route('/gerenciar')
@admin_required()
@nocache
def gerenciar_usuarios():
    termo_busca = request.args.get('busca', '').strip()
    tipo_filtro = request.args.get('tipo_filtro', 'nome')
    
    usuarios, erro = usuario_controller.listar_usuarios(termo_busca, tipo_filtro)
    if erro: flash(erro, "erro")
        
    return render_template('configuracoes/usuario/gerenciar_usuarios.html', 
                           usuarios=usuarios, termo_busca=termo_busca, 
                           tipo_filtro=tipo_filtro, back_url=url_for('configuracoes'))

@usuario_bp.route('/adicionar', methods=['GET', 'POST'])
@admin_required()
def adicionar_usuario():
    if request.method == 'POST':
        form_data = request.form.to_dict()
        if 'ra' in form_data:
            form_data['ra'] = re.sub(r'[^0-9-]', '', form_data['ra'])
        
        sucesso, erro = usuario_controller.adicionar_novo_usuario_admin(form_data)
        if sucesso:
            flash("Usuário cadastrado com sucesso!", "sucesso")
            return redirect(url_for('usuario.gerenciar_usuarios'))
        flash(erro, "erro")
            
    grupos, _ = usuario_controller.listar_grupos()
    return render_template('configuracoes/usuario/adicionar_usuarios.html', 
                           grupos=grupos, back_url=url_for('usuario.gerenciar_usuarios'))

@usuario_bp.route('/editar/<int:id_usuario>', methods=['GET', 'POST'])
@admin_required()
def editar_usuario(id_usuario):
    if request.method == 'POST':
        form_data = request.form.to_dict()
        if 'ra' in form_data:
            form_data['ra'] = re.sub(r'[^0-9-]', '', form_data['ra'])
            
        sucesso, erro = usuario_controller.atualizar_usuario_admin(id_usuario, form_data)
        if sucesso:
            flash("Dados do usuário atualizados!", "sucesso")
            return redirect(url_for('usuario.gerenciar_usuarios'))
        flash(erro, "erro")

    usuario, erro = usuario_controller.get_usuario_por_id(id_usuario)
    grupos, _ = usuario_controller.listar_grupos()
    
    if erro:
        flash(erro, "erro")
        return redirect(url_for('usuario.gerenciar_usuarios'))
        
    return render_template('configuracoes/usuario/editar_usuarios.html', 
                           usuario=usuario, grupos=grupos,
                           back_url=url_for('usuario.gerenciar_usuarios'))

@usuario_bp.route('/excluir/<int:id_usuario>', methods=['POST'])
@admin_required()
def excluir_usuario(id_usuario):
    sucesso, erro = usuario_controller.excluir_usuario_admin(id_usuario, session.get('id_usuario'))
    if sucesso:
        flash("Usuário removido com sucesso!", "sucesso")
    else:
        flash(erro, "erro")
    return redirect(url_for('usuario.gerenciar_usuarios'))