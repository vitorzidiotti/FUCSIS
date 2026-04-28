import os
import re
import bcrypt
from flask import Flask, request, redirect, url_for, session, render_template, flash, make_response
from functools import wraps
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from api.routes.auth_routes import auth_bp
import calendar

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
    tipo_filtro = request.args.get('tipo_filtro', 'nome') # Pega o tipo (Nome, CPF, etc)

    try:
        query = supabase.table("usuario").select("*, grupo_de_usuario(nome)")

        if termo_busca:
            if tipo_filtro == 'nome':
                query = query.ilike('nome', f'%{termo_busca}%')
            elif tipo_filtro == 'cpf':
                termo_limpo = re.sub(r'\D', '', termo_busca)
                query = query.ilike('cpf', f'%{termo_limpo}%')
            elif tipo_filtro == 'email':
                query = query.ilike('email', f'%{termo_busca}%')
            elif tipo_filtro == 'grupo':
                query = query.filter('grupo_de_usuario.nome', 'ilike', f'%{termo_busca}%')
        usuarios = query.order("nome").execute().data
        return render_template('configuracoes/usuario/gerenciar_usuarios.html', 
                               usuarios=usuarios, 
                               termo_busca=termo_busca,
                               tipo_filtro=tipo_filtro, # Passamos de volta para o HTML
                               back_url=url_for('configuracoes'))     
    except Exception as e:
        flash(f"Erro ao carregar usuários: {e}", "erro")
        return render_template('configuracoes/usuario/gerenciar_usuarios.html', 
                               usuarios=[], 
                               termo_busca=termo_busca,
                               tipo_filtro=tipo_filtro,
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

# ==========================================================================
# --- GERENCIAR CONTRATOS (VITRINE DE CARDS) ---
# ==========================================================================

@app.route('/admin/financeiro/contratos')
@admin_required()
@nocache
def gerenciar_contratos():
    try:
        # Versão simplificada para a Vitrine de Cards
        contratos = supabase.table("contrato").select("id_contrato, titulo_contrato, fornecedor(nome_fantasia)").order("titulo_contrato").execute().data
        
        # AQUI ESTAVA O ERRO: Faltava passar o back_url
        return render_template('modulos/financeiro/contratos/contratos.html', 
                               contratos=contratos,
                               back_url=url_for('modulo_financeiro')) 
    except Exception as e:
        flash(f"Erro ao carregar lista: {e}", "erro")
        return redirect(url_for('modulo_financeiro'))

@app.route('/admin/financeiro/contratos/gestao/<int:id_contrato>')
@admin_required()
def detalhe_contrato(id_contrato):
    try:
        # Esta é a Central de Gestão que havia sumido!
        contrato = supabase.table("contrato").select("*, fornecedor(*)").eq("id_contrato", id_contrato).single().execute().data
        parcelas = supabase.table("financeiro_parcelas").select("*").eq("id_contrato", id_contrato).order("data_vencimento").execute().data
        
        # Cálculos robustos (ignora canceladas no total e recupera valores)
        v_pago = sum(p['valor_esperado'] for p in parcelas if p['status_pagamento'].lower() == 'pago')
        v_restante = sum(p['valor_esperado'] for p in parcelas if p['status_pagamento'].lower() not in ['pago', 'cancelada'])
        p_pagas = len([p for p in parcelas if p['status_pagamento'].lower() == 'pago'])
        p_totais = len([p for p in parcelas if p['status_pagamento'].lower() != 'cancelada'])

        return render_template('modulos/financeiro/contratos/gestao_contrato.html', 
                               c=contrato, parcelas=parcelas, 
                               v_pago=v_pago, v_restante=v_restante,
                               p_pagas=p_pagas, p_totais=p_totais,
                               datetime=datetime, hoje=date.today(),
                               back_url=url_for('gerenciar_contratos'))
    except Exception as e:
        flash(f"Erro ao acessar gestão: {e}", "erro")
        return redirect(url_for('gerenciar_contratos'))

@app.route('/admin/financeiro/contratos/adicionar', methods=['GET', 'POST'])
@admin_required()
def adicionar_contrato():
    if request.method == 'POST':
        try:
            # 1. Upload do PDF (Opcional)
            link_pdf = None
            if 'arquivo_pdf' in request.files:
                file = request.files['arquivo_pdf']
                if file and file.filename != '':
                    file_path = f"pdf_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
                    supabase.storage.from_("contratos").upload(file_path, file.read(), {"content-type": "application/pdf"})
                    link_pdf = supabase.storage.from_("contratos").get_public_url(file_path)

            # 2. Insere Contrato
            id_fornecedor = request.form.get('id_fornecedor')
            titulo = request.form.get('titulo_contrato')
            valor_total = float(request.form.get('valor_total'))
            data_ini = datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%d').date()
            dia_venc = int(request.form.get('dia_vencimento'))
            num_parcelas = int(request.form.get('numero_parcelas'))

            res_c = supabase.table("contrato").insert({
                "id_fornecedor": id_fornecedor,
                "titulo_contrato": titulo,
                "valor_total": valor_total,
                "data_inicio": str(data_ini),
                "dia_vencimento": dia_venc,
                "link_pdf": link_pdf,
                "status": "Ativo"
            }).execute()

            id_gerado = res_c.data[0]['id_contrato']

            # --- 3. Geração de Parcelas com Ajuste de Centavos ---
            # Calculamos o valor base arredondado para 2 casas
            valor_parcela_base = round(valor_total / num_parcelas, 2)
            soma_acumulada = 0

            for i in range(num_parcelas):
                # Se for a ÚLTIMA parcela, ela assume a diferença para fechar o total exato
                if i == num_parcelas - 1:
                    valor_final_parcela = round(valor_total - soma_acumulada, 2)
                else:
                    valor_final_parcela = valor_parcela_base
                    soma_acumulada = round(soma_acumulada + valor_final_parcela, 2)

                vencimento = data_ini + relativedelta(months=i)
                try:
                    vencimento = vencimento.replace(day=dia_venc)
                except ValueError:
                    # Ajuste para meses que não possuem o dia escolhido (ex: 31/02)
                    vencimento = vencimento + relativedelta(day=31)

                supabase.table("financeiro_parcelas").insert({
                    "id_contrato": id_gerado,
                    "descricao": titulo,
                    "numero_parcela": i + 1,
                    "total_parcelas": num_parcelas,
                    "valor_esperado": valor_final_parcela,
                    "data_vencimento": str(vencimento),
                    "status_pagamento": "Pendente"
                }).execute()

            flash("Contrato e parcelas gerados com ajuste de centavos!", "sucesso")
            return redirect(url_for('detalhe_contrato', id_contrato=id_gerado))
            
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
            novo_status = request.form.get('status')
            
            # Recupera link atual se não houver novo upload
            link_pdf = supabase.table("contrato").select("link_pdf").eq("id_contrato", id_contrato).single().execute().data['link_pdf']
            
            if 'arquivo_pdf' in request.files:
                file = request.files['arquivo_pdf']
                if file and file.filename != '':
                    file_path = f"pdf_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
                    supabase.storage.from_("contratos").upload(file_path, file.read(), {"content-type": "application/pdf"})
                    link_pdf = supabase.storage.from_("contratos").get_public_url(file_path)

            dados_update = {
                "titulo_contrato": request.form.get('titulo_contrato'),
                "status": novo_status,
                "valor_total": float(request.form.get('valor_total')),
                "dia_vencimento": int(request.form.get('dia_vencimento')),
                "link_pdf": link_pdf
            }
            
            supabase.table("contrato").update(dados_update).eq("id_contrato", id_contrato).execute()

            # --- Lógica Reversível (Ativo/Encerrado) ---
            if novo_status == 'Encerrado':
                supabase.table("financeiro_parcelas").update({"status_pagamento": "Cancelada"})\
                    .eq("id_contrato", id_contrato).eq("status_pagamento", "Pendente").execute()
                flash("Contrato encerrado e parcelas pendentes canceladas.", "aviso")
            elif novo_status == 'Ativo':
                supabase.table("financeiro_parcelas").update({"status_pagamento": "Pendente"})\
                    .eq("id_contrato", id_contrato).eq("status_pagamento", "Cancelada").execute()
                flash("Contrato reativado e parcelas recuperadas.", "sucesso")
            
            return redirect(url_for('detalhe_contrato', id_contrato=id_contrato))

        # GET
        contrato = supabase.table("contrato").select("*, fornecedor(nome_fantasia)").eq("id_contrato", id_contrato).single().execute().data
        return render_template('modulos/financeiro/contratos/editar_contratos.html', 
                               contrato=contrato,
                               back_url=url_for('detalhe_contrato', id_contrato=id_contrato))
    except Exception as e:
        flash(f"Erro: {e}", "erro")
        return redirect(url_for('gerenciar_contratos'))

@app.route('/admin/financeiro/contratos/excluir/<int:id_contrato>', methods=['POST'])
@admin_required()
def excluir_contrato(id_contrato):
    try:
        pagas = supabase.table("financeiro_parcelas").select("id_parcela").eq("id_contrato", id_contrato).eq("status_pagamento", "Pago").execute().data
        
        if pagas:
            flash("Bloqueado: Existem parcelas PAGAS. Use o status 'Encerrado'.", "erro")
            return redirect(url_for('detalhe_contrato', id_contrato=id_contrato))

        supabase.table("financeiro_parcelas").delete().eq("id_contrato", id_contrato).execute()
        supabase.table("contrato").delete().eq("id_contrato", id_contrato).execute()
        
        flash("Contrato e histórico removidos.", "sucesso")
        return redirect(url_for('gerenciar_contratos'))
    except Exception as e:
        flash(f"Erro ao excluir: {e}", "erro")
        return redirect(url_for('gerenciar_contratos'))

# --- GERENCIAR FORNECEDORES ---

@app.route('/admin/financeiro/fornecedores')
@admin_required()
@nocache
def gerenciar_fornecedores():
    try:
        # Busca a lista completa para a tabela
        fornecedores = supabase.table("fornecedor").select("*").order("nome_fantasia").execute().data
        
        return render_template('modulos/financeiro/fornecedores/fornecedores.html', 
                               fornecedores=fornecedores,
                               back_url=url_for('modulo_financeiro')) # Volta para o Menu Financeiro
    except Exception as e:
        flash(f"Erro ao carregar lista de fornecedores: {e}", "erro")
        return redirect(url_for('modulo_financeiro'))


@app.route('/admin/financeiro/fornecedores/adicionar', methods=['GET', 'POST'])
@admin_required()
def adicionar_fornecedor():
    if request.method == 'POST':
        nome = request.form.get('nome_fantasia')
        # Limpa o CNPJ deixando apenas números
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

            flash(f"Fornecedor '{nome}' cadastrado com sucesso!", "sucesso")
            return redirect(url_for('gerenciar_fornecedores'))
        except Exception as e:
            flash(f"Erro ao salvar fornecedor: {e}", "erro")
            
    # GET: Abre o formulário
    return render_template('modulos/financeiro/fornecedores/adicionar_fornecedores.html',
                           back_url=url_for('gerenciar_fornecedores')) # Volta para a Lista


@app.route('/admin/financeiro/fornecedores/editar/<int:id_fornecedor>', methods=['GET', 'POST'])
@admin_required()
def editar_fornecedor(id_fornecedor):
    try:
        if request.method == 'POST':
            dados = {
                "nome_fantasia": request.form.get('nome_fantasia'),
                "cnpj": re.sub(r'\D', '', request.form.get('cnpj')),
                "contato_nome": request.form.get('contato_nome'),
                "contato_email": request.form.get('contato_email')
            }
            
            # Atualiza usando a chave id_fornecedor
            supabase.table("fornecedor").update(dados).eq("id_fornecedor", id_fornecedor).execute()
            
            flash("Dados do fornecedor atualizados!", "sucesso")
            return redirect(url_for('gerenciar_fornecedores'))

        # GET: Busca o registro atual
        res = supabase.table("fornecedor").select("*").eq("id_fornecedor", id_fornecedor).execute()
        
        if not res.data:
            flash("Fornecedor não encontrado.", "erro")
            return redirect(url_for('gerenciar_fornecedores'))

        return render_template('modulos/financeiro/fornecedores/editar_fornecedores.html', 
                               fornecedor=res.data[0],
                               back_url=url_for('gerenciar_fornecedores'))

    except Exception as e:
        flash(f"Erro técnico na edição: {e}", "erro")
        return redirect(url_for('gerenciar_fornecedores'))


@app.route('/admin/financeiro/fornecedores/excluir/<int:id_fornecedor>', methods=['POST'])
@admin_required()
def excluir_fornecedor(id_fornecedor):
    try:
        # TRAVA DE SEGURANÇA: Verifica se existem contratos vinculados a este fornecedor
        contratos = supabase.table("contrato").select("id_contrato").eq("id_fornecedor", id_fornecedor).execute().data
        
        if contratos:
            flash("Ação Bloqueada: Este fornecedor possui contratos ativos no sistema. Exclua os contratos primeiro.", "erro")
            return redirect(url_for('gerenciar_fornecedores'))

        supabase.table("fornecedor").delete().eq("id_fornecedor", id_fornecedor).execute()
        flash("Fornecedor removido da base de dados.", "sucesso")
        
    except Exception as e:
        flash(f"Erro ao excluir fornecedor: {e}", "erro")
        
    return redirect(url_for('gerenciar_fornecedores'))

# GERENCIAR FLUXO ---

@app.route('/admin/financeiro/fluxos')
@admin_required()
@nocache
def gerenciar_fluxos():
    try:
        hoje = date.today()
        
        # 1. Captura de Filtros do GET
        f_fornecedor = request.args.get('id_fornecedor', '')
        f_contrato = request.args.get('id_contrato', '')
        f_data_ini = request.args.get('data_inicio', '').strip() # Removi o padrão automático aqui
        f_data_fim = request.args.get('data_fim', '').strip()   # para permitir busca global

        # 2. Query Base
        query = supabase.table("financeiro_parcelas")\
            .select("*, contrato!inner(*, fornecedor!inner(*))")

        # 3. Aplicação DINÂMICA (Só aplica se o campo não estiver vazio)
        if f_fornecedor:
            query = query.eq('contrato.id_fornecedor', f_fornecedor)
        
        if f_contrato:
            query = query.eq('id_contrato', f_contrato)
        
        # Filtros de Data Condicionais (Resolve o erro 22007)
        if f_data_ini:
            query = query.gte('data_vencimento', f_data_ini)
        
        if f_data_fim:
            query = query.lte('data_vencimento', f_data_fim)

        # Executa a busca
        parcelas = query.order("data_vencimento").execute().data

        # 4. Cálculo dos Totais baseados no que está na tela
        total_pendente = sum(p['valor_esperado'] for p in parcelas if p['status_pagamento'] == 'Pendente')
        total_pago = sum(p['valor_esperado'] for p in parcelas if p['status_pagamento'] == 'Pago')

        # 5. Dados para os Dropdowns
        fornecedores = supabase.table("fornecedor").select("id_fornecedor, nome_fantasia").order("nome_fantasia").execute().data
        contratos = supabase.table("contrato").select("id_contrato, titulo_contrato").order("titulo_contrato").execute().data

        return render_template('modulos/financeiro/fluxos/fluxos.html', 
                               parcelas=parcelas, 
                               total_pendente=total_pendente, 
                               total_pago=total_pago,
                               hoje=hoje,
                               datetime=datetime,
                               fornecedores=fornecedores,
                               contratos=contratos,
                               filtros={
                                   'id_fornecedor': f_fornecedor,
                                   'id_contrato': f_contrato,
                                   'data_inicio': f_data_ini,
                                   'data_fim': f_data_fim
                               },
                               back_url=url_for('modulo_financeiro'))
    except Exception as e:
        print(f"Erro Real no Fluxo: {e}")
        flash(f"Erro ao filtrar fluxos: {e}", "erro")
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
        # 1. Pegar dados da parcela antes de apagar
        p = supabase.table("financeiro_parcelas").select("*").eq("id_parcela", id_parcela).single().execute().data
        manter_valor = request.form.get('manter_valor') == 'sim'
        id_contrato = p.get('id_contrato')
        valor_excluido = p['valor_esperado']

        # 2. Deleta a parcela
        supabase.table("financeiro_parcelas").delete().eq("id_parcela", id_parcela).execute()

        # 3. Redistribuição (Só se o usuário escolheu 'sim' e for de um contrato)
        if manter_valor and id_contrato:
            restantes = supabase.table("financeiro_parcelas").select("*")\
                .eq("id_contrato", id_contrato).eq("status_pagamento", "Pendente").execute().data
            
            if restantes:
                incremento = valor_excluido / len(restantes)
                for res in restantes:
                    novo_v = res['valor_esperado'] + incremento
                    supabase.table("financeiro_parcelas").update({"valor_esperado": novo_v})\
                        .eq("id_parcela", res['id_parcela']).execute()
                flash(f"Parcela excluída. R$ {valor_excluido:.2f} redistribuído nas restantes.", "sucesso")
            else:
                flash("Parcela excluída. Não há outras parcelas pendentes para redistribuir.", "aviso")
        else:
            flash("Parcela excluída. O valor total do contrato foi reduzido.", "sucesso")

    except Exception as e:
        flash(f"Erro: {e}", "erro")
    return redirect(url_for('gerenciar_fluxos'))
# --- EXECUÇÃO DO APP ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)