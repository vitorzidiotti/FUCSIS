import os
import re
import bcrypt
from flask import Flask, request, redirect, url_for, session, render_template, flash, make_response
from functools import wraps
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from routes.auth_routes import auth_bp


# --- CONFIGURAÇÃO INICIAL ---
load_dotenv()

# Configurações do Supabase
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
if not url or not key:
    raise ValueError("Erro: Variáveis SUPABASE_URL ou SUPABASE_KEY não encontradas no .env.")

supabase: Client = create_client(url, key)

# Configuração da App Flask
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "uma-chave-secreta-padrao-muito-segura")

# 2. REGISTRE O BLUEPRINT
app.register_blueprint(auth_bp)

# --- DECORATORS E FUNÇÕES HELPER ---

def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
    return no_cache

def login_required():
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'logged_in' not in session:
                flash('Por favor, faça login para acessar esta página.', 'erro')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

def admin_required():
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'logged_in' not in session:
                flash('Por favor, faça login para acessar esta página.', 'erro')
                return redirect(url_for('auth.login'))
            
            # ATUALIZADO: Usando id_grupo (Vamos assumir que 1 = Administrador)
            if session.get('id_grupo') != 1:
                flash('Você não tem permissão para acessar esta página.', 'erro')
                return redirect(url_for('inicio'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

# --- ROTAS PRINCIPAIS ---

@app.route('/')
def home():
    if session.get('logged_in'):
        # ATUALIZADO: Usando id_grupo
        if session.get('id_grupo') == 1:
            return redirect(url_for('admin')) 
        else:
            return redirect(url_for('inicio'))
    return redirect(url_for('auth.login'))

@app.route('/inicio')
@login_required()
def inicio():
    return render_template('inicio.html')

@app.route('/perfil', methods=['GET', 'POST'])
@login_required()
def perfil():
    user_id = session.get('id_usuario')
    try:
        current_user_data = supabase.table("usuario").select("*").eq("id_usuario", user_id).single().execute().data
    except Exception as e:
        flash(f'Não foi possível carregar os dados do perfil: {e}', 'erro')
        return redirect(url_for('inicio'))

    if request.method == 'POST':
        flash('Funcionalidade de atualização de perfil em desenvolvimento.', 'info')
        return redirect(url_for('perfil'))
        
    return render_template('perfil.html', usuario=current_user_data) # Correção: adicionei o .html

# --- ROTAS DE ADMINISTRAÇÃO ---
@app.route('/admin')
@admin_required()
def admin():
    return render_template('admin.html')

# --- GERENCIAR USUÁRIOS (LISTAGEM) ---
@app.route('/admin/gerenciar-usuarios', methods=['GET'])
@admin_required()
@nocache
def gerenciar_usuarios():
    termo_busca = request.args.get('busca', '').strip()
    try:
        # Busca usuários com o nome do grupo
        query = supabase.table("usuario").select("*, grupo_de_usuario(nome)").order("nome")
        if termo_busca:
            query = query.ilike('nome', f'%{termo_busca}%')
        
        usuarios = query.execute().data
        
        # O 'Voltar' da listagem vai para o menu de Configurações
        return render_template('configuracoes/usuario/gerenciar_usuarios.html', 
                               usuarios=usuarios, 
                               termo_busca=termo_busca,
                               back_url=url_for('configuracoes'))
    except Exception as e:
        flash(f"Erro ao carregar usuários: {e}", "erro")
        return render_template('configuracoes/usuario/gerenciar_usuarios.html', 
                               usuarios=[], 
                               termo_busca=termo_busca,
                               back_url=url_for('configuracoes'))

@app.route('/admin/usuarios/adicionar', methods=['GET', 'POST'])
@admin_required()
def adicionar_usuario():
    if request.method == 'POST':
        try:
            nome = request.form.get('nome')
            email = request.form.get('email')
            cpf_limpo = re.sub(r'\D', '', request.form.get('cpf'))
            senha = request.form.get('senha')
            id_grupo = request.form.get('id_grupo')

            senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            supabase.table("usuario").insert({
                "nome": nome, "email": email, "cpf": cpf_limpo, "senha": senha_hash, "id_grupo": id_grupo
            }).execute()
            
            flash("Usuário adicionado!", "sucesso")
            return redirect(url_for('gerenciar_usuarios'))
        except Exception as e:
            flash(f"Erro: {e}", "erro")
            
    # GET: Busca grupos e define o 'Voltar' para a listagem de usuários
    grupos = supabase.table("grupo_de_usuario").select("*").execute().data
    return render_template('configuracoes/usuario/adicionar_usuarios.html', 
                           grupos=grupos,
                           back_url=url_for('gerenciar_usuarios'))

@app.route('/admin/usuarios/editar/<int:id_usuario>', methods=['GET', 'POST'])
@admin_required()
def editar_usuario(id_usuario):
    if request.method == 'POST':
        try:
            dados = {
                'nome': request.form.get('nome'), 
                'email': request.form.get('email'), 
                'id_grupo': request.form.get('id_grupo')
            }
            if request.form.get('senha'):
                dados['senha'] = bcrypt.hashpw(request.form.get('senha').encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            supabase.table("usuario").update(dados).eq("id_usuario", id_usuario).execute()
            flash("Usuário atualizado!", "sucesso")
            return redirect(url_for('gerenciar_usuarios'))
        except Exception as e:
            flash(f"Erro ao atualizar: {e}", "erro")
    
    try:
        # GET: Busca usuário, grupos e define o 'Voltar' para a listagem
        usuario = supabase.table("usuario").select("*").eq("id_usuario", id_usuario).single().execute().data
        grupos = supabase.table("grupo_de_usuario").select("*").execute().data
        
        return render_template('configuracoes/usuario/editar_usuarios.html', 
                               usuario=usuario, 
                               grupos=grupos,
                               back_url=url_for('gerenciar_usuarios'))
    except Exception as e:
        flash("Erro ao carregar dados do usuário.", "erro")
        return redirect(url_for('gerenciar_usuarios'))

@app.route('/admin/usuarios/excluir/<int:id_usuario>', methods=['POST'])
@admin_required()
def excluir_usuario(id_usuario):
    # Nota: Esta rota não precisa de back_url pois é apenas um POST que redireciona
    if id_usuario == session.get('id_usuario'):
        flash("Você não pode se excluir.", "erro")
    else:
        try:
            supabase.table("usuario").delete().eq("id_usuario", id_usuario).execute()
            flash("Usuário removido.", "sucesso")
        except Exception as e:
            flash(f"Erro ao excluir: {e}", "erro")
            
    return redirect(url_for('gerenciar_usuarios'))

# --- TELA DE CONFIGURAÇÕES (O MENU INTERMEDIÁRIO) ---
@app.route('/admin/configuracoes')
@admin_required()
def configuracoes():
    # O 'Voltar' daqui leva o usuário de volta para a tela principal do Admin
    return render_template('configuracoes/configuracoes.html', 
                           back_url=url_for('admin'))
# --- GERENCIAMENTO DE GRUPOS ---

@app.route('/admin/gerenciar-grupos')
@admin_required()
@nocache
def gerenciar_grupos():
    try:
        grupos = supabase.table("grupo_de_usuario").select("*").order("id_grupo").execute().data
        # A listagem de grupos volta para o menu principal de Configurações
        return render_template('configuracoes/grupo/gerenciar_grupos.html', 
                               grupos=grupos, 
                               back_url=url_for('configuracoes'))
    except Exception as e:
        flash(f"Erro ao carregar grupos: {e}", "erro")
        return redirect(url_for('configuracoes'))

@app.route('/admin/grupos/adicionar', methods=['GET', 'POST'])
@admin_required()
def adicionar_grupo():
    if request.method == 'POST':
        nome = request.form.get('nome').strip()
        try:
            if not nome:
                flash("O nome do grupo é obrigatório.", "erro")
                return redirect(url_for('adicionar_grupo'))
            
            supabase.table("grupo_de_usuario").insert({"nome": nome}).execute()
            flash(f"Grupo '{nome}' criado com sucesso!", "sucesso")
            return redirect(url_for('gerenciar_grupos'))
        except Exception as e:
            flash(f"Erro ao criar grupo: {e}", "erro")
            
    # O formulário de adição volta para a listagem de grupos
    return render_template('configuracoes/grupo/adicionar_grupos.html', 
                           back_url=url_for('gerenciar_grupos'))

@app.route('/admin/grupos/editar/<int:id_grupo>', methods=['GET', 'POST'])
@admin_required()
def editar_grupo(id_grupo):
    try:
        grupo = supabase.table("grupo_de_usuario").select("*").eq("id_grupo", id_grupo).single().execute().data
    except Exception as e:
        flash("Grupo não encontrado.", "erro")
        return redirect(url_for('gerenciar_grupos'))

    if request.method == 'POST':
        novo_nome = request.form.get('nome').strip()
        try:
            supabase.table("grupo_de_usuario").update({"nome": novo_nome}).eq("id_grupo", id_grupo).execute()
            flash("Grupo atualizado com sucesso!", "sucesso")
            return redirect(url_for('gerenciar_grupos'))
        except Exception as e:
            flash(f"Erro ao atualizar: {e}", "erro")

    # O formulário de edição volta para a listagem de grupos
    return render_template('configuracoes/grupo/editar_grupos.html', 
                           grupo=grupo, 
                           back_url=url_for('gerenciar_grupos'))
@app.route('/admin/grupos/excluir/<int:id_grupo>', methods=['POST'])
@admin_required()
def excluir_grupo(id_grupo):
    # Proteção: Não deixa excluir o grupo 1 (Administrador)
    if id_grupo == 1:
        flash("O grupo Administrador não pode ser excluído.", "erro")
        return redirect(url_for('gerenciar_grupos'))
        
    try:
        # Verifica se há usuários vinculados a este grupo antes de excluir
        usuarios_no_grupo = supabase.table("usuario").select("id_usuario").eq("id_grupo", id_grupo).execute().data
        if usuarios_no_grupo:
            flash("Não é possível excluir: existem usuários vinculados a este grupo.", "erro")
            return redirect(url_for('gerenciar_grupos'))

        supabase.table("grupo_de_usuario").delete().eq("id_grupo", id_grupo).execute()
        flash("Grupo excluído com sucesso!", "sucesso")
    except Exception as e:
        flash(f"Erro ao excluir: {e}", "erro")
        
    return redirect(url_for('gerenciar_grupos'))


# --- MÓDULO FINANCEIRO (HUB PRINCIPAL) ---

@app.route('/admin/financeiro')
@admin_required()
@nocache
def modulo_financeiro():
    # O Voltar do menu financeiro vai para o Dashboard Admin
    return render_template('modulos/financeiro/index_financeiro.html', 
                           back_url=url_for('admin'))

# --- GERENCIAR CONTRATOS ---

@app.route('/admin/financeiro/contratos')
@admin_required()
@nocache
def gerenciar_contratos():
    try:
        contratos = supabase.table("contrato").select("*, fornecedor(nome_fantasia)").execute().data
        return render_template('modulos/financeiro/contratos/contratos.html', 
                               contratos=contratos, 
                               hoje=date.today(), 
                               datetime=datetime,
                               back_url=url_for('modulo_financeiro'))
    except Exception as e:
        print(f"Erro Real: {e}")
        flash(f"Erro ao carregar módulo de contratos.", "erro")
        return redirect(url_for('modulo_financeiro'))

@app.route('/admin/financeiro/contratos/adicionar', methods=['GET', 'POST'])
@admin_required()
def adicionar_contrato():

    if request.method == 'POST':
        try:
            # 1. Lógica do Upload do PDF
            link_pdf = None
            if 'arquivo_pdf' in request.files:
                file = request.files['arquivo_pdf']
                if file.filename != '':
                    file_path = f"pdf_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
                    supabase.storage.from_("contratos").upload(file_path, file.read(), {"content-type": "application/pdf"})
                    link_pdf = supabase.storage.from_("contratos").get_public_url(file_path)
            # 2. Dados do Form
            id_fornecedor = request.form.get('id_fornecedor')
            titulo = request.form.get('titulo_contrato')
            valor_total = float(request.form.get('valor_total'))
            data_ini = datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%d').date()
            data_fim = datetime.strptime(request.form.get('data_fim'), '%Y-%m-%d').date()
            dia_venc = int(request.form.get('dia_vencimento'))
            # 3. Salva no Banco
            novo_contrato = supabase.table("contrato").insert({
                "id_fornecedor": id_fornecedor,
                "titulo_contrato": titulo,
                "valor_total": valor_total,
                "data_inicio": str(data_ini),
                "data_fim": str(data_fim),
                "dia_vencimento": dia_venc,
                "link_pdf": link_pdf,
                "status": "Ativo"
            }).execute()
            id_gerado = novo_contrato.data[0]['id_contrato']
            # 4. Geração Automática de Parcelas
            diff = relativedelta(data_fim, data_ini)
            total_meses = diff.years * 12 + diff.months + 1
            valor_parcela = valor_total / total_meses
            for i in range(total_meses):
                vencimento_parcela = data_ini + relativedelta(months=i)
                try:
                    vencimento_parcela = vencimento_parcela.replace(day=dia_venc)
                except ValueError:
                    vencimento_parcela = vencimento_parcela + relativedelta(day=31)
                supabase.table("financeiro_parcelas").insert({
                    "id_contrato": id_gerado,
                    "descricao": f"Parcela {i+1}/{total_meses}",
                    "valor_esperado": valor_parcela,
                    "data_vencimento": str(vencimento_parcela),
                    "status_pagamento": "Pendente"
                }).execute()
            flash("Contrato e parcelas gerados com sucesso!", "sucesso")
            return redirect(url_for('gerenciar_contratos'))
        except Exception as e:
            flash(f"Erro ao salvar: {e}", "erro")
    fornecedores = supabase.table("fornecedor").select("*").order("nome_fantasia").execute().data
    return render_template('modulos/financeiro/contratos/adicionar_contratos.html', 
                           fornecedores=fornecedores,
                           back_url=url_for('gerenciar_contratos'))
    
@app.route('/admin/financeiro/contratos/editar/<int:id_contrato>', methods=['GET', 'POST'])
@admin_required()
def editar_contrato(id_contrato):
    try:
        if request.method == 'POST':
            dados = {
                "titulo_contrato": request.form.get('titulo_contrato'),
                "status": request.form.get('status'),
                "valor_total": float(request.form.get('valor_total')),
                "dia_vencimento": int(request.form.get('dia_vencimento'))
            }
            supabase.table("contrato").update(dados).eq("id_contrato", id_contrato).execute()
            flash("Contrato atualizado com sucesso!", "sucesso")
            return redirect(url_for('gerenciar_contratos'))

        contrato = supabase.table("contrato").select("*, fornecedor(nome_fantasia)").eq("id_contrato", id_contrato).single().execute().data
        fornecedores = supabase.table("fornecedor").select("*").order("nome_fantasia").execute().data
        
        return render_template('modulos/financeiro/contratos/editar_contratos.html', 
                               contrato=contrato, 
                               fornecedores=fornecedores,
                               back_url=url_for('gerenciar_contratos'))
    except Exception as e:
        flash(f"Erro ao acessar contrato: {e}", "erro")
        return redirect(url_for('gerenciar_contratos'))

@app.route('/admin/financeiro/contratos/excluir/<int:id_contrato>', methods=['POST'])
@admin_required()
def excluir_contrato(id_contrato):
    try:
        supabase.table("financeiro_parcelas").delete().eq("id_contrato", id_contrato).execute()
        supabase.table("contrato").delete().eq("id_contrato", id_contrato).execute()
        flash("Contrato e parcelas removidos.", "sucesso")
    except Exception as e:
        flash(f"Erro ao excluir: {e}", "erro")
    return redirect(url_for('gerenciar_contratos'))

# --- GERENCIAR FORNECEDORES ---

@app.route('/admin/financeiro/fornecedores')
@admin_required()
@nocache
def gerenciar_fornecedores():
    try:
        fornecedores = supabase.table("fornecedor").select("*").order("nome_fantasia").execute().data
        return render_template('modulos/financeiro/fornecedores/fornecedores.html', 
                               fornecedores=fornecedores,
                               back_url=url_for('modulo_financeiro'))
    except Exception as e:
        flash(f"Erro ao carregar fornecedores: {e}", "erro")
        return redirect(url_for('modulo_financeiro'))

@app.route('/admin/financeiro/fornecedores/adicionar', methods=['GET', 'POST'])
@admin_required()
def adicionar_fornecedor():
    if request.method == 'POST':
        nome = request.form.get('nome_fantasia')
        cnpj = re.sub(r'\D', '', request.form.get('cnpj'))
        contato = request.form.get('contato_nome')
        email = request.form.get('contato_email')

        try:
            supabase.table("fornecedor").insert({
                "nome_fantasia": nome,
                "cnpj": cnpj,
                "contato_nome": contato,
                "contato_email": email
            }).execute()

            flash(f"Fornecedor '{nome}' cadastrado!", "sucesso")
            return redirect(url_for('gerenciar_fornecedores'))
        except Exception as e:
            flash(f"Erro ao cadastrar: {e}", "erro")
            
    return render_template('modulos/financeiro/fornecedores/adicionar_fornecedores.html',
                           back_url=url_for('gerenciar_fornecedores'))

@app.route('/admin/financeiro/fornecedores/editar/<int:id_fornecedor>', methods=['GET', 'POST'])
@admin_required()
def editar_fornecedor(id_fornecedor):
    try:
        if request.method == 'POST':
            # 1. Coleta os dados do formulário
            dados = {
                "nome_fantasia": request.form.get('nome_fantasia'),
                "cnpj": re.sub(r'\D', '', request.form.get('cnpj')),
                "contato_nome": request.form.get('contato_nome'),
                "contato_email": request.form.get('contato_email')
            }
            
            # 2. Executa o update
            # CRÍTICO: Verifique se no Supabase a coluna é 'id_fornecedor' ou 'id'
            supabase.table("fornecedor").update(dados).eq("id_fornecedor", id_fornecedor).execute()
            
            flash("Fornecedor atualizado com sucesso!", "sucesso")
            return redirect(url_for('gerenciar_fornecedores'))

        # --- LÓGICA DO GET (ABRIR A TELA) ---
        
        # Busca o fornecedor. Usamos .execute() e verificamos se há dados
        res = supabase.table("fornecedor").select("*").eq("id_fornecedor", id_fornecedor).execute()
        
        if not res.data:
            flash("Fornecedor não encontrado no banco de dados.", "erro")
            return redirect(url_for('gerenciar_fornecedores'))

        # Pegamos o primeiro (e único) resultado
        fornecedor_data = res.data[0]

        # Renderiza a página passando o fornecedor e a URL de volta
        return render_template('modulos/financeiro/fornecedores/editar_fornecedores.html', 
                               fornecedor=fornecedor_data,
                               back_url=url_for('gerenciar_fornecedores'))

    except Exception as e:
        # Se der erro, ele imprime no terminal para você ver
        print(f"Erro ao carregar edição: {e}")
        flash(f"Erro técnico ao abrir a tela: {e}", "erro")
        return redirect(url_for('gerenciar_fornecedores'))

@app.route('/admin/financeiro/fornecedores/excluir/<int:id_fornecedor>', methods=['POST'])
@admin_required()
def excluir_fornecedor(id_fornecedor):
    try:
        contratos = supabase.table("contrato").select("id_contrato").eq("id_fornecedor", id_fornecedor).execute().data
        if contratos:
            flash("Não é possível excluir: existem contratos vinculados.", "erro")
            return redirect(url_for('gerenciar_fornecedores'))

        supabase.table("fornecedor").delete().eq("id_fornecedor", id_fornecedor).execute()
        flash("Fornecedor removido com sucesso.", "sucesso")
    except Exception as e:
        flash(f"Erro ao excluir: {e}", "erro")
    return redirect(url_for('gerenciar_fornecedores'))


# GERENCIAR FLUXO ---


@app.route('/admin/financeiro/fluxos')
@admin_required()
@nocache
def gerenciar_fluxos():
    try:
        hoje = date.today()
        # Busca parcelas, contratos e fornecedores em uma única consulta
        parcelas = supabase.table("financeiro_parcelas")\
            .select("*, contrato(titulo_contrato, fornecedor(nome_fantasia))")\
            .order("data_vencimento").execute().data

        total_pendente = sum(p['valor_esperado'] for p in parcelas if p['status_pagamento'] == 'Pendente')
        total_pago = sum(p['valor_esperado'] for p in parcelas if p['status_pagamento'] == 'Pago')
        
        return render_template('modulos/financeiro/fluxos/fluxos.html', 
                               parcelas=parcelas, 
                               total_pendente=total_pendente, 
                               total_pago=total_pago,
                               hoje=hoje,
                               datetime=datetime,
                               back_url=url_for('modulo_financeiro'))
    except Exception as e:
        flash(f"Erro ao carregar fluxos: {e}", "erro")
        return redirect(url_for('modulo_financeiro'))


@app.route('/admin/financeiro/fluxos/adicionar', methods=['GET', 'POST'])
@admin_required()
def adicionar_fluxo():
    if request.method == 'POST':
        try:
            dados = {
                "descricao": request.form.get('descricao'),
                "valor_esperado": float(request.form.get('valor')),
                "data_vencimento": request.form.get('data_vencimento'),
                "status_pagamento": request.form.get('status_pagamento'),
                "id_contrato": None 
            }

            supabase.table("financeiro_parcelas").insert(dados).execute()

            flash(f"Lançamento realizado com sucesso!", "sucesso")
            return redirect(url_for('gerenciar_fluxos'))
        except Exception as e:
            flash(f"Erro ao realizar lançamento: {e}", "erro")
            return redirect(url_for('gerenciar_fluxos'))

    return render_template('modulos/financeiro/fluxos/adicionar_fluxos.html', 
                           back_url=url_for('gerenciar_fluxos'))

@app.route('/admin/financeiro/fluxos/editar/<int:id_parcela>', methods=['GET', 'POST'])
@admin_required()
def editar_fluxo(id_parcela):
    try:
        if request.method == 'POST':
            dados = {
                "descricao": request.form.get('descricao'),
                "valor_esperado": float(request.form.get('valor')),
                "data_vencimento": request.form.get('data_vencimento'),
                "status_pagamento": request.form.get('status_pagamento')
            }
            supabase.table("financeiro_parcelas").update(dados).eq("id_parcela", id_parcela).execute()
            flash("Lançamento atualizado!", "sucesso")
            return redirect(url_for('gerenciar_fluxos'))
        res = supabase.table("financeiro_parcelas").select("*").eq("id_parcela", id_parcela).single().execute()
        parcela = res.data
        return render_template('modulos/financeiro/fluxos/editar_fluxos.html', 
                               parcela=parcela,
                               back_url=url_for('gerenciar_fluxos'))
    except Exception as e:
        flash(f"Erro ao editar: {e}", "erro")
        return redirect(url_for('gerenciar_fluxos'))

@app.route('/admin/financeiro/fluxos/excluir/<int:id_parcela>', methods=['POST'])
@admin_required()
def excluir_fluxo(id_parcela):
    try:
        supabase.table("financeiro_parcelas").delete().eq("id_parcela", id_parcela).execute()
        flash("Lançamento removido!", "sucesso")
    except Exception as e:
        flash(f"Erro ao excluir: {e}", "erro")
    return redirect(url_for('gerenciar_fluxos'))
    try:
        supabase.table("financeiro_parcelas").delete().eq("id_parcela", id_parcela).execute()
        flash("Lançamento removido do fluxo!", "sucesso")
    except Exception as e:
        print(f"Erro ao excluir do fluxo: {e}")
        flash(f"Erro ao excluir: {e}", "erro")
    return redirect(url_for('gerenciar_fluxo'))

# --- EXECUÇÃO DO APP ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)