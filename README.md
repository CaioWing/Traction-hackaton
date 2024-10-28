# Gearing - Sistema de Gerenciamento de Ordens de Serviço de Manutenção

## Visão Geral
Gearing é uma aplicação baseada em FastAPI que auxilia no gerenciamento de ordens de serviço de manutenção através da análise de documentação técnica, processamento de transcrições de áudio e geração de procedimentos de segurança detalhados. O sistema integra-se com modelos da OpenAI para análise inteligente de documentos e recursos de conversão de fala em texto.

## Funcionalidades

### 1. Gerenciamento de Ordens de Serviço
- Geração de procedimentos de manutenção detalhados a partir de documentação técnica
- Análise simultânea de múltiplas fontes em PDF
- Priorização de tarefas baseada em urgência e requisitos de segurança
- Rastreamento de equipamentos necessários com códigos SAP
- Armazenamento e recuperação de ordens de serviço via MongoDB

### 2. Processamento de Áudio
- Transcrição de comandos de voz para texto usando o modelo Whisper da OpenAI
- Suporte para entrada de microfone em tempo real e upload de arquivos de áudio
- Ajuste automático de ruído para melhor qualidade de gravação

### 3. Análise Inteligente de Documentos
- Processamento simultâneo de múltiplos documentos técnicos (PDFs)
- Extração de informações relevantes usando busca por similaridade vetorial

## Estrutura do Código

### Principais Componentes

1. **app.py**
   - Configuração principal da aplicação FastAPI
   - Gerenciamento de conexão com MongoDB
   - Configuração de CORS e logging

2. **models.py**
   - Definição dos modelos Pydantic para validação de dados
   - Classes: `Equipament`, `SafetyStep`, `SafetySolution`, `SafetyResponse`

3. **services/**
   - **audio_service.py**: Serviço de processamento de áudio
   - **llm_service.py**: Serviço de processamento de linguagem natural

4. **routes.py**
   - Definição dos endpoints da API
   - Lógica de manipulação de requisições

## Endpoints da API

### 1. Gerenciamento de Ordens de Serviço

```python
GET /addService
```
- **Descrição**: Adiciona uma nova ordem de serviço
- **Parâmetros**: 
  - `problema` (query): Descrição do problema de manutenção
- **Resposta**: Detalhes da ordem de serviço criada

```python
GET /getServices
```
- **Descrição**: Recupera todas as ordens de serviço
- **Resposta**: Lista de todas as ordens de serviço

```python
GET /service/{item_id}
```
- **Descrição**: Recupera uma ordem de serviço específica
- **Parâmetros**:
  - `item_id` (path): ID da ordem de serviço
- **Resposta**: Detalhes da ordem de serviço solicitada

### 2. Processamento de Áudio

```python
POST /transcribe
```
- **Descrição**: Transcreve áudio do microfone e cria ordem de serviço
- **Resposta**: Ordem de serviço baseada na transcrição do áudio

```python
POST /audioupload/
```
- **Descrição**: Processa arquivo de áudio enviado
- **Parâmetros**:
  - `file` (form-data): Arquivo de áudio
- **Resposta**: Transcrição do áudio

## Modelos de Dados

### SafetyResponse
```python
{
    "ordem_servico": [
        {
            "problema": str,
            "passos": [
                {
                    "ordem": int,
                    "descricao": str,
                    "justificativa": str,
                    "medidas_seguranca": List[str],
                    "duracao": str
                }
            ],
            "equipamentos_necessarios": [
                {
                    "codigo_sap": str,
                    "descricao": str,
                    "quantidade": str
                }
            ],
            "observacoes": List[str],
            "referencias": List[str],
            "prioridade": Literal['baixa', 'media', 'alta', 'maxima']
        }
    ]
}
```

## Requisitos do Sistema
- Python 3.8+
- MongoDB
- Chave de API da OpenAI
- Dependências:
  - fastapi
  - pymongo
  - openai
  - speech_recognition
  - PyPDF2
  - tiktoken
  - numpy
  - pandas

## Configuração

1. Clone o repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```
3. Configure as variáveis de ambiente:
```bash
export OPENAI_API_KEY='sua-chave-api'
```
4. Inicie o MongoDB
5. Execute a aplicação:
```bash
uvicorn app:app --reload
```

## Observações
- O sistema possui fallback para armazenamento em arquivo quando o MongoDB não está disponível
- Todos os endpoints possuem tratamento de erros e logging
- A aplicação utiliza o modelo mais recente da OpenAI para processamento de linguagem natural
- O sistema é projetado para ser escalável e manutenível