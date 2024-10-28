import json
import asyncio
import numpy as np
import tiktoken
import PyPDF2
import pandas as pd
from typing import List, Dict, Union
from openai import OpenAI
from models import SafetyResponse

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text from a PDF file."""
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()
    return text

def process_csv_data(csv_path: str) -> str:
    """Processes CSV data into a structured text format preserving all information."""
    df = pd.read_csv(csv_path, sep=';')
    
    # Start with a header for the equipment catalog
    text_chunks = ["CATÁLOGO DE EQUIPAMENTOS E MATERIAIS\n"]
    
    # Initialize variables
    current_category = None
    
    # Process each row
    for _, row in df.iterrows():
        # If there's a category, add it
        if pd.notna(row['Categoria']):
            current_category = row['Categoria']
            text_chunks.append(f"\nCATEGORIA: {current_category}")
            
        # Add all item information, including any empty fields
        description = row['Descrição do Material/Equipamento'] if pd.notna(row['Descrição do Material/Equipamento']) else ""
        code = row['Código SAP'] if pd.notna(row['Código SAP']) else ""
        
        # Format the item entry
        if description or code:  # Add entry if there's either a description or code
            entry = []
            if description:
                entry.append(f"Descrição: {description}")
            if code:
                entry.append(f"Código SAP: {code}")
            if current_category:
                entry.append(f"Categoria: {current_category}")
                
            text_chunks.append(" | ".join(entry))
    
    # Add a footer to separate the catalog from other content
    text_chunks.append("\nFIM DO CATÁLOGO DE EQUIPAMENTOS E MATERIAIS\n")
    
    # Join all chunks with newlines
    return "\n".join(text_chunks)

def split_text(text: str, max_tokens: int = 500) -> List[str]:
    """Splits text into chunks of a specified maximum number of tokens."""
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = start + max_tokens
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)
        start = end
    return chunks

async def get_embeddings(texts: List[str], client: OpenAI) -> List[List[float]]:
    """Generates embeddings for a list of texts."""
    embeddings = []
    batch_size = 1000
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.embeddings.create(
                input=batch,
                model="text-embedding-ada-002"
            )
        )
        embeddings.extend([data.embedding for data in response.data])
    return embeddings

def vector_search(query_embedding: List[float], embeddings: List[List[float]], top_k: int = 5) -> List[int]:
    """Performs a vector search to find the most similar embeddings."""
    embeddings = np.array(embeddings)
    query_embedding = np.array(query_embedding)
    similarities = np.dot(embeddings, query_embedding)
    top_k_indices = similarities.argsort()[-top_k:][::-1]
    return top_k_indices

async def process_documents_with_assistant(
    pdf_paths: List[str],
    csv_path: str,
    problema: str,
    client: OpenAI
) -> SafetyResponse:
    """Process multiple PDFs and CSV data to generate response using OpenAI."""
    
    # Process CSV data first to ensure it's always included in the context
    csv_text = process_csv_data(csv_path)
    
    # Process all PDFs
    pdf_texts = []
    for pdf_path in pdf_paths:
        pdf_text = extract_text_from_pdf(pdf_path)
        pdf_texts.append(pdf_text)
    
    # Split CSV text into chunks while preserving its structure
    csv_chunks = split_text(csv_text, max_tokens=500)
    
    # Split PDF texts into chunks
    pdf_chunks = []
    for pdf_text in pdf_texts:
        chunks = split_text(pdf_text, max_tokens=500)
        pdf_chunks.extend(chunks)
    
    # Combine all chunks, ensuring CSV chunks are at the beginning
    all_chunks = csv_chunks + pdf_chunks
    
    print("Creating embeddings for chunks...")
    chunk_embeddings = await get_embeddings(all_chunks, client)

    query_embedding_response = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: client.embeddings.create(
            input=problema,
            model="text-embedding-ada-002"
        )
    )
    query_embedding = query_embedding_response.data[0].embedding

    # Always include at least one chunk of CSV data in the context
    top_k_indices = vector_search(query_embedding, chunk_embeddings, top_k=10)
    
    # Ensure at least one CSV chunk is included
    has_csv_chunk = any(i < len(csv_chunks) for i in top_k_indices)
    if not has_csv_chunk:
        # Replace the last chunk with the most relevant CSV chunk
        csv_similarities = np.dot(np.array(chunk_embeddings[:len(csv_chunks)]), query_embedding)
        best_csv_index = csv_similarities.argmax()
        top_k_indices = list(top_k_indices[:-1]) + [best_csv_index]
    
    relevant_chunks = [all_chunks[i] for i in top_k_indices]
    
    # Always include the full equipment catalog at the end of the context
    context = "\n\n".join(relevant_chunks) + "\n\nCATÁLOGO COMPLETO DE EQUIPAMENTOS:\n" + csv_text

    instructions = """
Você é um especialista em análise de normas técnicas e segurança.
Use o conteúdo dos documentos fornecidos para responder problemas específicos.
Os códigos SAP e equipamentos mencionados devem corresponder *EXATAMENTE* aos listados no catálogo fornecido.
Suas respostas devem ser em português e estruturadas no seguinte formato JSON:
{
    "ordem_servico": [
        {
            "problema": "descrição do problema-1",
            "passos": [
                {
                    "ordem": 1,
                    "descricao": "descrição detalhada do passo",
                    "justificativa": "baseado em qual parte da norma",
                    "medidas_seguranca": ["lista de medidas de segurança"],
                    "duracao": "20min"
                }
            ],
            "equipamentos_necessarios": [
                {
                    "codigo_sap": "código do equipamento",
                    "descricao": "descrição do equipamento",
                    "quantidade": "quantidade necessária"
                }
            ],
            "observacoes": ["observações importantes"],
            "referencias": ["referências específicas da norma"]
            "prioridade": Literal['baixa', 'media', 'alta', 'maxima']
        },
        {
            "problema": "descrição do problema-2",
            "passos": [
                {
                    "ordem": 2,
                    "descricao": "descrição detalhada do passo",
                    "justificativa": "baseado em qual parte da norma",
                    "medidas_seguranca": ["lista de medidas de segurança"],
                    "duracao": "20min"
                }
            ],
            "equipamentos_necessarios": [
                {
                    "codigo_sap": "código do equipamento",
                    "descricao": "descrição do equipamento",
                    "quantidade": "quantidade necessária"
                }
            ],
            "observacoes": ["observações importantes"],
            "referencias": ["referências específicas da norma"]
            "prioridade": Literal['baixa', 'media', 'alta', 'maxima']
        },

    ]
}
Mantenha suas respostas técnicas e precisas, fundamentadas no conteúdo do documento.
Certifique-se de usar apenas equipamentos e códigos SAP que existam no catálogo fornecido.
Todos os equipamentos mencionados DEVEM ter seus códigos SAP correspondentes do catálogo. 
Para a prioridade, se atente ao nível de gravidade e urgência no problema especificado,
caso não tenha essas informações, compare as atividades existentes para classificar as
mais urgentes.
"""
    prompt = f"{instructions}\n\nContexto:\n{context}\n\nProblema: {problema}\nResposta:"

    print("Generating assistant's response...")
    response = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500,
            response_format=SafetyResponse,
        )
    )

    safety_response = response.choices[0].message.parsed
    return safety_response