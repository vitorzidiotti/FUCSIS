# /api/models/produto.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Produto:
    id_produto: int
    nome: str
    preco: float
    estoque: int
    criado_em: str
    marca: Optional[str] = None
    validade: Optional[str] = None