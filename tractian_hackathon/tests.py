from openai import OpenAI
import PyPDF2
import os
import tiktoken
import numpy as np
import json
import asyncio
from typing import List, Dict
from fastapi import FastAPI
import pymongo


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
    """Generates embeddings for a list of texts using the new OpenAI client."""
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


async def process_pdf_with_assistant(pdf_path: str, problema: str, client: OpenAI) -> Dict:
    """Process PDF and generate response using the new OpenAI client."""
    # Step 1: Extract text from the PDF
    text = extract_text_from_pdf(pdf_path)

    # Step 2: Split the text into chunks
    chunks = split_text(text, max_tokens=500)

    # Step 3: Create embeddings for each chunk
    print("Creating embeddings for chunks...")
    chunk_embeddings = await get_embeddings(chunks, client)

    # Step 4: Create an embedding for the query/problem
    query_embedding_response = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: client.embeddings.create(
            input=problema,
            model="text-embedding-ada-002"
        )
    )
    query_embedding = query_embedding_response.data[0].embedding

    # Step 5: Retrieve relevant chunks using vector search
    top_k_indices = vector_search(query_embedding, chunk_embeddings, top_k=5)
    relevant_chunks = [chunks[i] for i in top_k_indices]

    # Step 6: Prepare the prompt for the assistant
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
            }
        ],
        "equipamentos_necessarios": ["lista de equipamentos"],
        "observacoes": ["observações importantes"],
        "referencias": ["referências específicas da norma"]
    }
}
Mantenha suas respostas técnicas e precisas, fundamentadas no conteúdo do documento.
"""
    prompt = f"{instructions}\n\nContexto:\n{
        context}\n\nProblema: {problema}\nResposta:"

    # Step 7: Get the assistant's response using the new chat completion endpoint
    print("Generating assistant's response...")
    response = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500
        )
    )
    assistant_reply = response.choices[0].message.content

    # Step 8: Parse the assistant's response as JSON
    try:
        json_response = json.loads(assistant_reply)
        output_filename = f"resposta_{problema[:30]}.json"
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(json_response, f, ensure_ascii=False, indent=4)
        print(f"\nResposta salva em: {output_filename}")
        return json_response
    except json.JSONDecodeError:
        print("Aviso: Não foi possível converter a resposta para JSON")
        return {
            "erro": "Formato de resposta inválido",
            "resposta_original": assistant_reply
        }


client = OpenAI()  # Make sure OPENAI_API_KEY is set in your environment variables

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["Gearing"]

app = FastAPI()

pdf_path = "prompts/nr-12-atualizada-2022-1.pdf"
problema = "Como realizar a manutenção segura de uma máquina de solda?"


@app.get("/addService")
async def read_item():
    mycol = mydb["serviceOrders"]
    try:
        resposta = await process_pdf_with_assistant(pdf_path, problema, client)
        mycol.insert_one(resposta)
        print("Aqui?")
        return "Added with success!"
    except Exception as e:
        print(f"Erro ao processar PDF: {e}")
        return "Deu problema " + e


@app.get("/listServices")
