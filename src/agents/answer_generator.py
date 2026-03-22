import asyncio
import os
from typing import Any, AsyncGenerator, Dict, List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from prefect.blocks.system import Secret

from src.agents.prompts import RAG_SYSTEM_PROMPT, RAG_USER_PROMPT
from src.agents.retriever import TechnicalRetriever


class TechnicalAnswerGenerator:
    """O 'Cerebro' do Xetroc: Gera respostas tecnicas usando LangChain e LCEL.

    Esta classe orquestra a recuperacao e sintese usando as melhores praticas 
    modernas do LangChain.
    """

    def __init__(self, model: str = "gpt-4o"):
        """Inicializa o gerador com o LLM e o Retriever.

        :param model: A string identificadora do modelo OpenAI.
        """
        self.model_name: str = model
        self.retriever: TechnicalRetriever = TechnicalRetriever()
        
        # Inicializa o cliente ChatOpenAI via Blocos do Prefect ou variaveis de ambiente
        try:
            openai_key_block = Secret.load("openai-api-key")
            api_key: str = openai_key_block.get()
        except Exception:
            api_key: str = os.getenv("OPENAI_API_KEY", "")

        if not api_key:
            raise ValueError("OPENAI_API_KEY nao encontrada.")
            
        self.model: ChatOpenAI = ChatOpenAI(
            api_key=api_key,
            model=self.model_name,
            temperature=0
        )

    async def agenerate_answer(self, query: str, prefetched_contexts: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Executa a síntese da resposta. Se contextos já existirem, evita busca duplicada.

        :param query: Pergunta técnica do usuário.
        :param prefetched_contexts: (Opcional) Contextos já recuperados pelo nó anterior.
        :return: Dicionário com a resposta e as fontes organizadas.
        """
        # 1. Obter Contextos (Usa o fornecido ou busca agora)
        if prefetched_contexts is not None:
            contexts = prefetched_contexts
        else:
            contexts = await self.retriever.aretrieve(query)
        
        # 2. Validação de Contexto
        if not contexts:
            return {
                "answer": "Sinto muito, mas não encontrei documentos técnicos que fundamentem uma resposta específica sobre este tema.",
                "sources": []
            }

        # 3. Formatação do Prompt
        context_str: str = ""
        for i, c in enumerate(contexts):
            meta = c.get("metadata", {})
            source = meta.get("source", "Documento")
            page = meta.get("page", "?")
            context_str += f"\n--- CONTEXTO {i+1} (Fonte: {source}, Pag: {page}) ---\n"
            context_str += c.get("text", "") + "\n"

        # 4. Cadeia LCEL
        prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages([
            ("system", RAG_SYSTEM_PROMPT),
            ("user", RAG_USER_PROMPT)
        ])
        chain = prompt | self.model | StrOutputParser()
        
        print(f"INFO: Gerando resposta técnica assíncrona via {self.model_name}...")
        answer: str = await chain.ainvoke({
            "context_str": context_str,
            "query": query
        })
        
        # 5. Agregação de Fontes únicas
        unique_sources: List[str] = []
        for c in contexts:
            meta = c.get("metadata", {})
            src = f"{meta.get('source')} (Pag {meta.get('page')})"
            if src not in unique_sources:
                unique_sources.append(src)

        return {
            "answer": answer,
            "sources": unique_sources
        }

    async def astream_answer(self, query: str) -> AsyncGenerator[str, None]:
        """Gera a resposta token a token via streaming (Regra OpenAI 3.3).

        :param query: Pergunta tecnica do usuario.
        :yield: Chunks da resposta gerada.
        """
        contexts: List[Dict[str, Any]] = await self.retriever.aretrieve(query)
        
        if not contexts:
            yield "Sinto muito, mas nao encontrei nenhum documento tecnico relacionado a essa pergunta."
            return

        context_str: str = ""
        for i, c in enumerate(contexts):
            source: str = c["metadata"].get("source", "Desconhecido")
            page: str = c["metadata"].get("page", "?")
            context_str += f"\n--- CONTEXTO {i+1} (Fonte: {source}, Pag: {page}) ---\n"
            context_str += c["text"] + "\n"

        prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages([
            ("system", RAG_SYSTEM_PROMPT),
            ("user", RAG_USER_PROMPT)
        ])
        chain = prompt | self.model | StrOutputParser()

        async for chunk in chain.astream({
            "context_str": context_str,
            "query": query
        }):
            yield chunk

    def generate_answer(self, query: str) -> Dict[str, Any]:
        """Wrapper de compatibilidade sincronica para geracao de resposta.

        :param query: Pergunta tecnica do usuario.
        :return: Dicionario com o resultado da geracao.
        """
        return asyncio.run(self.agenerate_answer(query))

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    async def test():
        generator = TechnicalAnswerGenerator()
        pergunta = "Quais os impactos da degradação do biodiesel em bicos injetores e filtros?"
        
        print("\nRESPOSTA DO XETROC (STREAMING):")
        print("-" * 30)
        async for chunk in generator.astream_answer(pergunta):
            print(chunk, end="", flush=True)
        print("\n" + "-" * 30)

    asyncio.run(test())
