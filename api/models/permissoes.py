# /api/models/usuario.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class permissoes:
    id_permissao: int
    nome: str
    descricao: str
    criado_em: datetime
    criado_por: int 