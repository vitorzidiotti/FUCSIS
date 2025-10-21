# /api/models/cliente.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Cliente:
    id_cliente: int
    nome: str
    cpf: str
    criado_em: str
    email: Optional[str] = None