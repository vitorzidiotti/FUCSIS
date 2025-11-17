# /api/models/venda.py
from dataclasses import dataclass
from typing import Optional, List
# Importe os outros modelos se quiser aninhar os dados
from .usuario import Usuario
@dataclass
class VendaItem:
    id_venda_item: int
    id_venda: int
    id_produto: int
    quantidade: int
    preco_unitario: float
    subtotal: float

@dataclass
class Venda:
    id_venda: int
    id_usuario: int
    id_cliente: int
    data_venda: str
    total: float
    tb_usuario: Optional[Usuario] = None 
    itens_da_venda: List[VendaItem] = None