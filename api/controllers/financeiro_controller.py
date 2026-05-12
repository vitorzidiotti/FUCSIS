import re
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from ..database import supabase

# --- LÓGICA DE CONTRATOS ---
def adicionar_contrato_completo(dados, arquivo=None):
    try:
        link_pdf = None
        if arquivo and arquivo.filename != '':
            file_path = f"pdf_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            supabase.storage.from_("contratos").upload(file_path, arquivo.read(), {"content-type": "application/pdf"})
            link_pdf = supabase.storage.from_("contratos").get_public_url(file_path)

        # Inserção do Contrato
        res = supabase.table("contrato").insert({
            "id_fornecedor": dados.get('id_fornecedor'),
            "titulo_contrato": dados.get('titulo_contrato'),
            "valor_total": float(dados.get('valor_total')),
            "data_inicio": dados.get('data_inicio'),
            "dia_vencimento": int(dados.get('dia_vencimento')),
            "link_pdf": link_pdf,
            "status": "Ativo"
        }).execute()

        id_gerado = res.data[0]['id_contrato']
        gerar_parcelas_automaticas(id_gerado, dados)
        return id_gerado, None
    except Exception as e:
        return None, str(e)

def gerar_parcelas_automaticas(id_contrato, dados):
    valor_total = float(dados.get('valor_total'))
    num_parcelas = int(dados.get('numero_parcelas'))
    dia_venc = int(dados.get('dia_vencimento'))
    data_ini = datetime.strptime(dados.get('data_inicio'), '%Y-%m-%d').date()
    
    valor_base = round(valor_total / num_parcelas, 2)
    soma_acumulada = 0

    for i in range(num_parcelas):
        valor_f = round(valor_total - soma_acumulada, 2) if i == num_parcelas -1 else valor_base
        soma_acumulada += valor_f
        
        vencimento = data_ini + relativedelta(months=i)
        try: vencimento = vencimento.replace(day=dia_venc)
        except: vencimento = vencimento + relativedelta(day=31)

        supabase.table("financeiro_parcelas").insert({
            "id_contrato": id_contrato,
            "descricao": dados.get('titulo_contrato'),
            "numero_parcela": i + 1,
            "total_parcelas": num_parcelas,
            "valor_esperado": valor_f,
            "data_vencimento": str(vencimento),
            "status_pagamento": "Pendente"
        }).execute()

def excluir_parcela_fluxo(id_parcela, manter_valor=False):
    try:
        p = supabase.table("financeiro_parcelas").select("*").eq("id_parcela", id_parcela).single().execute().data
        id_contrato = p.get('id_contrato')
        valor_excluido = p['valor_esperado']

        supabase.table("financeiro_parcelas").delete().eq("id_parcela", id_parcela).execute()

        if manter_valor and id_contrato:
            restantes = supabase.table("financeiro_parcelas").select("*").eq("id_contrato", id_contrato).eq("status_pagamento", "Pendente").execute().data
            if restantes:
                incremento = valor_excluido / len(restantes)
                for res in restantes:
                    novo_v = res['valor_esperado'] + incremento
                    supabase.table("financeiro_parcelas").update({"valor_esperado": novo_v}).eq("id_parcela", res['id_parcela']).execute()
        return True, None
    except Exception as e:
        return False, str(e)