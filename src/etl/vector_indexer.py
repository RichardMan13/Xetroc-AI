import json
import os
from pathlib import Path
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from prefect import flow, task
from prefect.blocks.system import Secret # Novo: para acessar segredos no Servidor Prefect
from src.database.vector_db import VectorDB

class VectorIndexer:
    """Implementa a lógica de chunking e indexação vetorial dos PDFs."""

    def __init__(self, collection_name: str = "normas_tecnicas"):
        # Tenta pegar a chave do Prefect primeiro (o Bloco que criamos no setup_prefect)
        # Se nao houver conexao com o servidor ou o bloco nao existir, tenta o .env como fallback
        try:
            openai_key_block = Secret.load("openai-api-key")
            api_key = openai_key_block.get()
            print("INFO: Chave da OpenAI carregada dos Blocos do Prefect.")
        except Exception:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                print("INFO: Chave da OpenAI carregada do .env (local).")

        if not api_key:
            raise ValueError("Erro: OPENAI_API_KEY não encontrada nos Blocos do Prefect nem no .env local.")

        self.client = OpenAI(api_key=api_key)
        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.db = VectorDB(collection_name=collection_name)
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", " ", ""]
        )

    def _get_embedding(self, texts: List[str]) -> List[List[float]]:
        """Invoca o modelo da OpenAI para gerar vetores denso (Embeddings)."""
        response = self.client.embeddings.create(
            input=texts,
            model="text-embedding-3-small"
        )
        return [data.embedding for data in response.data]

    def process_json_to_chunks(self, json_path: Path) -> List[Dict]:
        """Le o arquivo JSON extraido pelo PDFParser e divide em chunks menores."""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        final_chunks = []
        for block in data:
            # Mantemos os metadados do bloco original (page, source, block_id)
            chunks = self.splitter.split_text(block["text"])
            for i, chunk_text in enumerate(chunks):
                final_chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        **block["metadata"],
                        "chunk_id": i
                    }
                })
        
        return final_chunks

from prefect.cache_policies import NO_CACHE

@task(name="Gerar e Indexar Vetores", cache_policy=NO_CACHE)
def index_file(json_path: Path):
    """Executa o pipeline de chunking -> embedding -> upsert no Qdrant."""
    indexer = VectorIndexer() # Inicializado aqui para evitar problemas de Hashing no Prefect
    print(f"Indexando vetores de: {json_path.name}")
    
    # 1. Chunking
    chunks = indexer.process_json_to_chunks(json_path)
    if not chunks:
        return f"{json_path.name}: Nenhum chunk gerado."
    
    # 2. Embeddings (Processar em lotes para evitar timeout)
    batch_size = 100
    texts = [c["text"] for c in chunks]
    embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        batch_embeddings = indexer._get_embedding(batch_texts)
        embeddings.extend(batch_embeddings)
    
    # 3. Armazenar no Qdrant (Hibrido: Dense + Sparse automatico)
    indexer.db.upsert_chunks(chunks, dense_embeddings=embeddings)
    return f"{json_path.name}: {len(chunks)} chunks indexados com sucesso (Hibrido)."

@flow(name="Xetroc Vector Indexing Pipeline")
def run_indexing(data_processed_path: str = "data/processed"):
    """Varre a pasta de processados em busca de JSONs e os indexa no Vector DB."""
    base_path = Path(data_processed_path)
    
    # Buscamos apenas arquivos JSON (output do PDFParser)
    json_files = list(base_path.glob("*.json"))
    print(f"Total de arquivos para indexar: {len(json_files)}")
    
    results = []
    for file in json_files:
        # Passamos apenas o Path, que eh serializavel (JSON-friendly)
        res = index_file(file)
        results.append(res)
    
    return results

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run_indexing()
