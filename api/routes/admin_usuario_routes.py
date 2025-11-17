import re 
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from ..utils.decorators import admin_required, nocache
from ..controllers import admin_usuario_controller

usuario_bp = Blueprint(
    'usuario', __name__,
    template_folder='../../templates/usuario' 
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
        
        # <<< INÍCIO DA CORREÇÃO >>>
        # 1. Copia o formulário imutável para um dicionário mutável
        form_data = request.form.to_dict()
        
        # 2. Limpa o campo CPF (remove pontos e traço) se ele existir
        if 'cpf' in form_data:
            form_data['cpf'] = re.sub(r'\D', '', form_data['cpf'])
        
        # 3. Passa o dicionário 'form_data' (limpo) para o controller
        sucesso, erro = admin_usuario_controller.adicionar_novo_usuario_admin(form_data)
        # <<< FIM DA CORREÇÃO >>>
        
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

        # <<< INÍCIO DA CORREÇÃO >>>
        # 1. Copia o formulário imutável para um dicionário mutável
        form_data = request.form.to_dict()
        
        # 2. Limpa o campo CPF (remove pontos e traço) se ele existir
        if 'cpf' in form_data:
            form_data['cpf'] = re.sub(r'\D', '', form_data['cpf'])
        
        # 3. Passa o dicionário 'form_data' (limpo) para o controller
        sucesso, erro = admin_usuario_controller.atualizar_usuario_admin(id_usuario, form_data)
        # <<< FIM DA CORREÇÃO >>>
        
        if sucesso:
            flash("Usuário atualizado com sucesso!", "sucesso")
            return redirect(url_for('usuario.gerenciar_usuarios'))
        else:
            flash(erro, "erro")

    # Lógica do GET (permanece igual)
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