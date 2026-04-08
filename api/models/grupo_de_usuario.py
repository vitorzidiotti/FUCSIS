# /api/models/usuario.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class grupo_de_usuario:
    id_grupo: int
    nome: str
    descricao: str
    criado_em: datetime
    criado_por: int 