# /api/models/usuario.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Usuario:
    id_usuario: int
    nome: str
    cpf: str
    email: str
    is_admin: bool
    criado_em: str 