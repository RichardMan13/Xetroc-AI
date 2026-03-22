import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models
from typing import List, Dict, Any, Optional
from fastembed import SparseTextEmbedding # Novo: para busca por palavras-chave (Keyword)

class VectorDB:
    """Interface evoluida para busca hibrida (Semantica Densa + Palavras-Chave Esparsas)."""

    def __init__(self, collection_name: str = "normas_tecnicas"):
        self.url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.api_key = os.getenv("QDRANT_API_KEY")
        self.client = QdrantClient(url=self.url, api_key=self.api_key)
        self.collection_name = collection_name
        
        # Inicializa o modelo de busca por palavras-chave (BM25/SPLADE moderno)
        # Ele eh carregado apenas uma vez e eh extremamente eficiente
        self.sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
        
        self._ensure_collection()

    def _ensure_collection(self):
        """Garante a colecao configurada para busca hibrida."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if exists:
            # Verifica se a colecao atual tem vetores nomeados (necessario para hibrida)
            # Se for do tipo antigo (vetores sem nome), deletamos para recriar
            info = self.client.get_collection(self.collection_name)
            if not isinstance(info.config.params.vectors, dict):
                print(f"Colecao '{self.collection_name}' legada detectada. Deletando para upgrade hibrido...")
                self.client.delete_collection(self.collection_name)
                exists = False

        if not exists:
            print(f"Criando colecao Hibrida no Qdrant: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                # Vetores Densos (Significado / OpenAI)
                vectors_config={
                    "dense": models.VectorParams(
                        size=1536,
                        distance=models.Distance.COSINE
                    )
                },
                # Vetores Esparsos (Palavras-Chave / BM25)
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams(
                        index=models.SparseIndexParams(on_disk=True)
                    )
                }
            )

    def upsert_chunks(self, chunks: List[Dict[str, Any]], dense_embeddings: List[List[float]]):
        """Insere chunks gerando vetores esparsos (keyword) automaticamente."""
        # 1. Gerar vetores esparsos (Keyword) para todos os chunks em lote
        texts = [c["text"] for c in chunks]
        # O fastembed gera um gerador, convertemos para lista para facilidade
        sparse_embeddings = list(self.sparse_model.embed(texts))

        points = []
        for chunk, dense_vec, sparse_vec in zip(chunks, dense_embeddings, sparse_embeddings):
            # ID deterministico baseado na fonte + conteudo para evitar duplicatas
            source = chunk["metadata"].get("source", "unknown")
            text_content = chunk["text"]
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{source}_{text_content}"))

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector={
                        "dense": dense_vec,
                        "sparse": models.SparseVector(
                            indices=sparse_vec.indices,
                            values=sparse_vec.values
                        )
                    },
                    payload={
                        "page_content": chunk["text"],
                        **chunk["metadata"]
                    }
                )
            )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print(f"Sucesso: {len(points)} pontos hibridos indexados no Qdrant.")

    def search(self, query: str, dense_vector: List[float], limit: int = 5):
        """Busca hibrida usando Reciprocal Rank Fusion (RRF)."""
        # Gera o vetor de palavra-chave para a pergunta
        query_sparse_vec = list(self.sparse_model.embed([query]))[0]
        
        return self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                # Busca Semantica (Dense)
                models.Prefetch(
                    query=dense_vector,
                    using="dense",
                    limit=limit * 2
                ),
                # Busca por Termos (Sparse)
                models.Prefetch(
                    query=models.SparseVector(
                        indices=query_sparse_vec.indices,
                        values=query_sparse_vec.values
                    ),
                    using="sparse",
                    limit=limit * 2
                )
            ],
            # Combina os dois resultados com RRF (o que estiver bem em ambos sobe)
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=limit
        )

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    db = VectorDB()
    print("Banco Vetorial Hibrido pronto.")
