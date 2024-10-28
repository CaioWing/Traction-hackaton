from openai import OpenAI
from typing_extensions import override
from openai import AssistantEventHandler
import PyPDF2
import base64
import os
from typing import List

class PDFHandler:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.chunk_size = 200000  # Safe limit below OpenAI's 256000 character limit
    
    def extract_text_by_pages(self) -> List[str]:
        """Extract text from PDF file page by page"""
        pages_text = []
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    pages_text.append(page.extract_text())
            return pages_text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return []
    
    def create_chunks(self, pages_text: List[str]) -> List[str]:
        """Create chunks of text that respect the token limit"""
        chunks = []
        current_chunk = ""
        
        for page_text in pages_text:
            if len(current_chunk) + len(page_text) < self.chunk_size:
                current_chunk += page_text + "\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = page_text + "\n"
        
        if current_chunk:  # Add the last chunk
            chunks.append(current_chunk)
            
        return chunks

class EventHandler(AssistantEventHandler):
    @override
    def on_text_created(self, text) -> None:
        print(f"\nassistant > ", end="", flush=True)
    
    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)
    
    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)
    
    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == 'code_interpreter':
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                print(f"\n\noutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"\n{output.logs}", flush=True)

def process_pdf_with_assistant(pdf_path: str):
    # Initialize OpenAI client
    client = OpenAI()
    
    # Create PDF handler and extract text
    pdf_handler = PDFHandler(pdf_path)
    pages_text = pdf_handler.extract_text_by_pages()
    
    if not pages_text:
        raise Exception("Failed to extract text from PDF")
    
    # Create chunks that respect the token limit
    chunks = pdf_handler.create_chunks(pages_text)
    
    # Create assistant
    assistant = client.beta.assistants.create(
        name="PDF Analyzer",
        instructions="""You are a PDF document analyzer. Process and analyze the content of PDF documents.
        You will receive the document in chunks. Keep track of the context across chunks and provide a 
        comprehensive analysis.""",
        tools=[{"type": "code_interpreter"}],
        model="gpt-4"
    )
    
    # Create thread for the conversation
    thread = client.beta.threads.create()
    
    # Process each chunk
    for i, chunk in enumerate(chunks):
        print(f"\nProcessing chunk {i+1} of {len(chunks)}...")
        
        # Create message with chunk content
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"This is part {i+1} of {len(chunks)} of the PDF content:\n\n{chunk}"
        )
        
        # Stream the response for this chunk
        with client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=assistant.id,
            event_handler=EventHandler(),
        ) as stream:
            stream.until_done()
        
        # Add a separator between chunks
        print("\n" + "="*50 + "\n")
    
    # Request final summary
    final_message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="Now that you have processed all chunks, please provide a comprehensive summary of the entire document."
    )
    
    # Stream the final summary
    with client.beta.threads.runs.stream(
        thread_id=thread.id,
        assistant_id=assistant.id,
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done()

def process_multiple_pdfs(pdf_paths: List[str]):
    """Process multiple PDFs sequentially"""
    for pdf_path in pdf_paths:
        print(f"\nProcessing PDF: {pdf_path}")
        print("="*50)
        try:
            process_pdf_with_assistant(pdf_path)
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {e}")
        print("\n" + "="*50 + "\n")

# Usage example
if __name__ == "__main__":
    # Single PDF processing
    pdf_path = "prompts/nr-12-atualizada-2022-1.pdf"
    try:
        process_pdf_with_assistant(pdf_path)
    except Exception as e:
        print(f"Error processing PDF: {e}")
    
    # Multiple PDFs processing
    # pdf_paths = ["path1.pdf", "path2.pdf", "path3.pdf"]
    # process_multiple_pdfs(pdf_paths)