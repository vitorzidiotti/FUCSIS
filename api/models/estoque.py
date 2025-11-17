# /api/models/estoque.py
from dataclasses import dataclass
from typing import Optional
from .produto import Produto

@dataclass
class EstoqueMovimento:
    id_mov: int
    id_produto: int
    tipo_mov: str
    quantidade: int
    criado_em: str
    motivo: Optional[str] = None
    tb_produto: Optional[Produto] = None