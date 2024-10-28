from typing import List
from pydantic import BaseModel

class SafetyStep(BaseModel):
    ordem: int
    descricao: str
    justificativa: str
    medidas_seguranca: List[str]
    duracao: str

class SafetySolution(BaseModel):
    passos: List[SafetyStep]
    equipamentos_necessarios: List[str]
    observacoes: List[str]
    referencias: List[str]

class SafetyResponse(BaseModel):
    problema: str
    solucao: SafetySolution