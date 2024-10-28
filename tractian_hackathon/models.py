from typing import List, Literal
from pydantic import BaseModel

class Equipament(BaseModel):
    nome: str
    sap_code: str
    quantidade: int

class SafetyStep(BaseModel):
    ordem: int
    descricao: str
    justificativa: str
    medidas_seguranca: List[str]
    duracao: str

class SafetySolution(BaseModel):
    problema: str
    passos: List[SafetyStep]
    equipamentos_necessarios: List[Equipament]
    observacoes: List[str]
    referencias: List[str]
    prioridade: Literal['baixa', 'media', 'alta', 'maxima']

class SafetyResponse(BaseModel):
    ordem_servico: List[SafetySolution]