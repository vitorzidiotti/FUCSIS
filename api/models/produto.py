# /api/models/produto.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Produto:
    id_produto: int
    nome: str [50]
    preco: float
    estoque: float
    criado_em: str
    marca: str [50]
    validade: str [50]
    lote: str [50]
    medida: str [20]