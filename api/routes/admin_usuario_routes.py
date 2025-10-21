# /api/routes/admin_usuario_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from ..utils.decorators import admin_required, nocache
from ..controllers import admin_usuario_controller

usuario_bp = Blueprint(
    'usuario', __name__,
    template_folder='../../templates/usuario' # Pasta dos templates (ex: gerenciar_usuarios.html)
)

@usuario_bp.route('/')
@admin_required()
@nocache
def gerenciar_usuarios():
    termo_busca = request.args.get('busca', '').strip()
    usuarios, erro = admin_usuario_controller.listar_usuarios(termo_busca)
    
    if erro:
        flash(erro, "erro")
        
    return render_template('gerenciar_usuarios.html', usuarios=usuarios, termo_busca=termo_busca)

@usuario_bp.route('/adicionar', methods=['GET', 'POST'])
@admin_required()
def adicionar_usuario():
    if request.method == 'POST':
        sucesso, erro = admin_usuario_controller.adicionar_novo_usuario_admin(request.form)
        
        if sucesso:
            flash("Usuário administrador adicionado com sucesso!", "sucesso")
            return redirect(url_for('usuario.gerenciar_usuarios'))
        else:
            flash(erro, "erro")
            
    return render_template('adicionar_usuario.html')

@usuario_bp.route('/editar/<int:id_usuario>', methods=['GET', 'POST'])
@admin_required()
def editar_usuario(id_usuario):
    if request.method == 'POST':
        sucesso, erro = admin_usuario_controller.atualizar_usuario_admin(id_usuario, request.form)
        
        if sucesso:
            flash("Usuário atualizado com sucesso!", "sucesso")
            return redirect(url_for('usuario.gerenciar_usuarios'))
        else:
            flash(erro, "erro")

    # Se for GET ou se o POST falhar
    usuario, erro = admin_usuario_controller.get_usuario_por_id(id_usuario)
    if erro:
        flash(erro, "erro")
        return redirect(url_for('usuario.gerenciar_usuarios'))
        
    return render_template('editar_usuario.html', usuario=usuario)

@usuario_bp.route('/excluir/<int:id_usuario>', methods=['POST'])
@admin_required()
def excluir_usuario(id_usuario):
    id_usuario_logado = session.get('id_usuario')
    sucesso, erro = admin_usuario_controller.excluir_usuario_admin(id_usuario, id_usuario_logado)
    
    if sucesso:
        flash("Usuário excluído com sucesso!", "sucesso")
    else:
        flash(erro, "erro")
        
    return redirect(url_for('usuario.gerenciar_usuarios'))