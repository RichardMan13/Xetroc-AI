import asyncio
import os
from typing import Any, Dict, List, Optional

from langchain_openai import OpenAIEmbeddings
from prefect.blocks.system import Secret
from sentence_transformers import CrossEncoder

from src.database.vector_db import VectorDB


class TechnicalRetriever:
    """Camada de recuperacao avancada de documentos tecnicos com Re-ranking.

    Esta classe orquestra a busca vetorial no Qdrant e o refinamento dos resultados 
    usando um modelo Cross-Encoder.
    """

    def __init__(
        self, 
        collection_name: str = "normas_tecnicas", 
        rerank: bool = True,
        top_k_initial: int = 15,
        top_k_final: int = 5
    ):
        """Inicializa o retriever com as conexoes de DB e modelos.

        :param collection_name: Nome da colecao vetorial no Qdrant.
        :param rerank: Se deve aplicar o re-ranker Cross-Encoder.
        :param top_k_initial: Numero inicial de candidatos da busca vetorial.
        :param top_k_final: Numero de documentos a retornar apos o re-ranking.
        """
        self.db: VectorDB = VectorDB(collection_name=collection_name)
        self.rerank: bool = rerank
        self.top_k_initial: int = top_k_initial
        self.top_k_final: int = top_k_final
        
        # Inicializa o cliente OpenAI via LangChain
        try:
            openai_key_block = Secret.load("openai-api-key")
            api_key: str = openai_key_block.get()
        except Exception:
            api_key: str = os.getenv("OPENAI_API_KEY", "")

        if not api_key:
            raise ValueError("OPENAI_API_KEY nao encontrada.")
            
        self.embeddings: OpenAIEmbeddings = OpenAIEmbeddings(
            api_key=api_key,
            model="text-embedding-3-small"
        )

        # Inicializa o modelo de Re-ranking (Cross-Encoder)
        if self.rerank:
            print("LOG: [SYSTEM] Carregando modelo de Re-ranking (BGE-Reranker-v2-m3)...")
            self.reranker: CrossEncoder = CrossEncoder('BAAI/bge-reranker-v2-m3', revision=None)

    async def aretrieve(self, query: str) -> List[Dict[str, Any]]:
        """Executa o pipeline de recuperacao assincrona (Busca Densa + Re-ranking).

        :param query: A consulta tecnica do usuario.
        :return: Lista dos principais documentos com pontuacoes e metadados.
        """
        print(f"LOG: [RETRIEVER] Buscando contexto para: '{query[:50]}...'")
        
        # 1. Gerar embedding da consulta (LangChain Async)
        query_dense_vec: List[float] = await self.embeddings.aembed_query(query)
        
        # 2. Busca Hibrida no Qdrant (Executar no executor para evitar bloqueio)
        loop = asyncio.get_event_loop()
        search_results = await loop.run_in_executor(
            None, 
            lambda: self.db.search(
                query=query, 
                dense_vector=query_dense_vec, 
                limit=self.top_k_initial
            )
        )
        
        if not search_results.points:
            return []

        # 3. Preparar candidatos
        candidates: List[Dict[str, Any]] = []
        for p in search_results.points:
            candidates.append({
                "text": p.payload.get("page_content", ""),
                "metadata": {k: v for k, v in p.payload.items() if k != "page_content"},
                "score": p.score
            })

        # 4. Aplicar Re-ranking (Intensivo em CPU)
        if self.rerank and len(candidates) > 1:
            print(f"LOG: [RETRIEVER] Refinando {len(candidates)} candidatos...")
            pairs: List[List[str]] = [[query, c["text"]] for c in candidates]
            
            rerank_scores = await loop.run_in_executor(
                None,
                lambda: self.reranker.predict(pairs)
            )

            for i, score in enumerate(rerank_scores):
                candidates[i]["rerank_score"] = float(score)
            
            candidates = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)

        return candidates[:self.top_k_final]

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """Wrapper de compatibilidade sincronica para recuperacao.

        :param query: Pergunta tecnica.
        :return: Lista de documentos recuperados.
        """
        return asyncio.run(self.aretrieve(query))


async def main_test() -> None:
    """Teste de integracao para o modulo retriever."""
    from dotenv import load_dotenv
    load_dotenv()
    
    retriever: TechnicalRetriever = TechnicalRetriever()
    pergunta: str = "Como e feito o monitoramento da conformidade do oleo diesel?"
    contextos: List[Dict[str, Any]] = await retriever.aretrieve(pergunta)
    
    print("\n" + "="*50)
    print(f"TOP {len(contextos)} RESULTADOS RE-RANKEADOS:")
    print("="*50)
    for i, c in enumerate(contextos):
        score: float = c.get("rerank_score", c["score"])
        source: str = c["metadata"].get("source", "N/A")
        page: str = c["metadata"].get("page", "?")
        print(f"\n[{i+1}] Score: {score:.4f} | Source: {source} (Pag {page})")
        print(f"Texto: {c['text'][:200]}...")


if __name__ == "__main__":
    asyncio.run(main_test())
