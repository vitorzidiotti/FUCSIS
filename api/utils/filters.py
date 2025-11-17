# /api/utils/filters.py
from datetime import datetime, timezone

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

def format_br_datetime(value):
    """Converte string ISO de data/hora (Supabase) para DD/MM/YYYY HH:MM."""
    if not value:
        return '-'
    try:
        date_obj_utc = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        date_obj_local = date_obj_utc.astimezone(None)
        return date_obj_local.strftime('%d/%m/%Y %H:%M')
    except (ValueError, TypeError) as e:
        print(f"Erro ao formatar datetime '{value}': {e}. Tentando apenas data.")
        return format_br_date(value)