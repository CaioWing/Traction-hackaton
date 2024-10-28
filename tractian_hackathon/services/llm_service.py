import json
import asyncio
import numpy as np
import tiktoken
import PyPDF2
from typing import List, Dict
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

async def process_pdf_with_assistant(pdf_path: str, problema: str, client: OpenAI) -> SafetyResponse:
    """Process PDF and generate response using OpenAI."""
    text = extract_text_from_pdf(pdf_path)
    chunks = split_text(text, max_tokens=500)
    
    print("Creating embeddings for chunks...")
    chunk_embeddings = await get_embeddings(chunks, client)

    query_embedding_response = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: client.embeddings.create(
            input=problema,
            model="text-embedding-ada-002"
        )
    )
    query_embedding = query_embedding_response.data[0].embedding

    top_k_indices = vector_search(query_embedding, chunk_embeddings, top_k=5)
    relevant_chunks = [chunks[i] for i in top_k_indices]

    context = "\n\n".join(relevant_chunks)
    instructions = """
Você é um especialista em análise de normas técnicas e segurança.
Use o conteúdo dos documentos fornecidos para responder problemas específicos.
Suas respostas devem ser em português e estruturadas no seguinte formato JSON:
{
    "problema": "descrição do problema",
    "solucao": {
        "passos": [
            {
                "ordem": 1,
                "descricao": "descrição detalhada do passo",
                "justificativa": "baseado em qual parte da norma",
                "medidas_seguranca": ["lista de medidas de segurança"]
                "duracao": "20min"
            }
        ],
        "equipamentos_necessarios": ["lista de equipamentos necessários para realização dos serviços"],
        "observacoes": ["observações importantes"],
        "referencias": ["referências específicas da norma"]
    }
}
Mantenha suas respostas técnicas e precisas, fundamentadas no conteúdo do documento.
"""
    prompt = f"{instructions}\n\nContexto:\n{context}\n\nProblema: {problema}\nResposta:"

    print("Generating assistant's response...")
    response = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: client.beta.chat.completions.parse(
            model="gpt-4o-mini-2024-07-18",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500,
            response_format=SafetyResponse,
        )
    )

    safety_response = response.choices[0].message.parsed
    # breakpoint()

    # # Save response to file
    # output_filename = f"resposta_problema.json"
    # with open(output_filename, "w", encoding="utf-8") as f:
    #     json.dump(safety_response.model_dump(), f, ensure_ascii=False, indent=4)
    # print(f"\nResposta salva em: {output_filename}")

    return safety_response