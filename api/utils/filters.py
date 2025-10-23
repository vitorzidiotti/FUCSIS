# /api/utils/filters.py
from datetime import datetime, timezone # Importe timezone

# --- Mantenha a função format_br_date como está ---
def format_br_date(value):
    """Converte uma string de data YYYY-MM-DD para DD/MM/YYYY."""
    if not value:
        return '-'
    try:
        date_part = str(value).split('T')[0]
        date_obj = datetime.strptime(date_part, '%Y-%m-%d')
        return date_obj.strftime('%d/%m/%Y')
    except (ValueError, TypeError):
        return value if value else '-'

# --- SUBSTITUA A FUNÇÃO format_br_datetime POR ESTA ---
def format_br_datetime(value):
    """Converte string ISO de data/hora (Supabase) para DD/MM/YYYY HH:MM."""
    if not value:
        return '-'
    try:
        # datetime.fromisoformat lida nativamente com o formato do Supabase
        # incluindo 'Z' ou '+HH:MM' e microssegundos opcionais.
        date_obj_utc = datetime.fromisoformat(str(value).replace('Z', '+00:00'))

        # Converte para o fuso horário local (opcional, mas recomendado)
        # Se não quiser converter fuso, use date_obj_utc diretamente no strftime
        date_obj_local = date_obj_utc.astimezone(None) # None usa o fuso do sistema

        # Formata para DD/MM/YYYY HH:MM
        return date_obj_local.strftime('%d/%m/%Y %H:%M')
    except (ValueError, TypeError) as e:
        # Se falhar, tenta formatar apenas como data (fallback)
        print(f"Erro ao formatar datetime '{value}': {e}. Tentando apenas data.")
        return format_br_date(value) # Usa o outro filtro