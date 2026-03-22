import asyncio
import json
import os
import time
from typing import Any, Dict, List, Literal, TypedDict

import mlflow
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from src.agents.answer_generator import TechnicalAnswerGenerator
from src.agents.prompts import (
    REFLECTION_SYSTEM_PROMPT,
    REFLECTION_USER_PROMPT,
    ROUTER_SYSTEM_PROMPT,
    ROUTER_USER_PROMPT,
    SQL_SYSTEM_PROMPT,
    SQL_USER_PROMPT,
)
from src.agents.retriever import TechnicalRetriever
from src.database.sql_db import SQLDatabase

# 1. Global Setup (MLFlow)
# --------------------------------------------------------------------------
MLFLOW_URI: str = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
mlflow.set_tracking_uri(MLFLOW_URI)
mlflow.set_experiment("Xetroc-RAG-Agent")


# 2. Estado e Esquemas
# --------------------------------------------------------------------------
class AgentState(TypedDict):
    """Representa o estado interno para orquestracao de RAG e Reflexao.

    :param query: A pergunta original do usuario.
    :param target: Decisao de roteamento (vector, sql, none, unknown).
    :param contexts: Lista de documentos de contexto recuperados.
    :param answer: A string de resposta final gerada.
    :param sources: Lista de fontes de documentos ou dados utilizadas.
    :param reflection_count: Numero de tentativas de auditoria de qualidade.
    :param is_valid: Se a resposta atual e considerada satisfatoria.
    """
    query: str
    target: Literal["vector", "sql", "none", "unknown"]
    contexts: List[Dict[str, Any]]
    answer: str
    sources: List[str]
    reflection_count: int 
    is_valid: bool       


class ReflectionSchema(BaseModel):
    """Validacao estruturada da qualidade da resposta tecnica.

    :param valid: Booleano indicando se a resposta esta fundamentada no contexto.
    :param reason: Explicacao detalhada sobre a decisao de validade.
    """
    valid: bool = Field(description="Se a resposta esta fundamentada no contexto")
    reason: str = Field(description="Explicacao da decisao")


# 3. Nos do Grafo (Async)
# --------------------------------------------------------------------------
async def router_node(state: AgentState) -> Dict[str, Any]:
    """Cerebro de Decisao: Roteia a consulta para Normas (Vector) ou Historico (SQL) usando LCEL.

    :param state: Estado atual do agente.
    :return: Estado atualizado com o alvo do roteamento.
    """
    print(f"LOG: [ROUTER] Analisando: '{state['query'][:50]}...'")
    
    prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages([
        ("system", ROUTER_SYSTEM_PROMPT),
        ("user", ROUTER_USER_PROMPT)
    ])
    
    llm: ChatOpenAI = ChatOpenAI(model="gpt-4o", temperature=0)
    chain = prompt | llm | StrOutputParser()
    
    decision: str = await chain.ainvoke({"query": state["query"]})
    decision = decision.strip().lower()
    
    if "vector" in decision:
        final_decision = "vector"
    elif "sql" in decision:
        final_decision = "sql"
    else:
        final_decision = "none"
    
    return {"target": final_decision, "reflection_count": 0}


async def retrieve_vector_node(state: AgentState) -> Dict[str, Any]:
    """Recupera documentos do banco de dados vetorial Qdrant.

    :param state: Estado atual do agente.
    :return: Estado atualizado com contextos e fontes recuperados.
    """
    print("LOG: [AGENT] Consultando Qdrant (Async)...")
    retriever: TechnicalRetriever = TechnicalRetriever()
    contexts: List[Dict[str, Any]] = await retriever.aretrieve(state["query"])
    sources: List[str] = [
        f"{c['metadata'].get('source')} (Pag {c['metadata'].get('page')})" 
        for c in contexts
    ]
    return {"contexts": contexts, "sources": sources}


async def query_sql_node(state: AgentState) -> Dict[str, Any]:
    """Trabalhador SQL agentico usando LCEL para traducao de Texto-para-SQL.

    :param state: Estado atual do agente.
    :return: Estado atualizado com resultados SQL encapsulados como contexto.
    """
    print("LOG: [AGENT] Traduzindo pergunta para SQL (LCEL)...")
    db: SQLDatabase = SQLDatabase()
    schema: str = db.get_schema_info()
    
    prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages([
        ("system", SQL_SYSTEM_PROMPT),
        ("user", SQL_USER_PROMPT)
    ])
    
    llm: ChatOpenAI = ChatOpenAI(model="gpt-4o", temperature=0)
    chain = prompt | llm | StrOutputParser()
    
    sql_query: str = await chain.ainvoke({"schema": schema, "query": state["query"]})
    sql_query = sql_query.strip().replace("```sql", "").replace("```", "")
    
    # Executa no pool de threads para não travar o loop de eventos assíncrono
    loop = asyncio.get_event_loop()
    results: List[Dict[str, Any]] = await loop.run_in_executor(
        None, lambda: db.execute_query(sql_query)
    )
    
    # Validação de Resultados (Regra de Segurança: Index Out of Range)
    if not results:
        return {
            "answer": "Não encontrei registros que satisfaçam essa consulta no banco de dados.",
            "contexts": [],
            "sources": ["PostgreSQL (Consulta sem resultados)"]
        }

    if "error" in results[0]:
        return {
            "answer": f"Ocorreu um erro técnico ao consultar o banco: {results[0].get('error')}",
            "contexts": [],
            "sources": ["PostgreSQL (Erro de Execução)"]
        }
    
    # Sucesso: Converte resultados para string e anexa ao contexto
    text_results: str = json.dumps(results, indent=2, default=str)
    return {
        "contexts": [
            {"text": f"RESULTADOS SQL:\n{text_results}", "metadata": {"source": "Banco de Dados de Ativos"}}
        ],
        "sources": ["Banco de Dados de Ativos (Consulta em Tempo Real)"]
    }


async def generate_answer_node(state: AgentState) -> Dict[str, Any]:
    """Sintetiza a resposta técnica final ou mantém a resposta do SQL se já existir.
    
    Se o nó SQL já produziu uma resposta (ex: registros não encontrados),
    esta fase é ignorada para preservar a precisão do banco de dados.
    """
    # Verificação de Prioridade: Se já houver resposta e contexto vazio, não sobrescrever
    if state.get("answer") and not state.get("contexts"):
        return {"answer": state["answer"]}

    attempt: int = state.get("reflection_count", 0) + 1
    print(f"LOG: [AGENT] Gerando Resposta Final (Tentativa #{attempt})...")
    
    generator: TechnicalAnswerGenerator = TechnicalAnswerGenerator()
    
    result: Dict[str, Any] = await generator.agenerate_answer(
        query=state["query"], 
        prefetched_contexts=state.get("contexts", [])
    )
    
    return {"answer": result["answer"]}


async def reflect_node(state: AgentState) -> Dict[str, Any]:
    """No de auditoria de qualidade usando Saida Estruturada.

    :param state: Estado atual do agente.
    :return: Estado atualizado com a flag de satisfacao e contagem.
    """
    if state.get("reflection_count", 0) >= 1: 
        return {"is_valid": True}

    prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages([
        ("system", REFLECTION_SYSTEM_PROMPT),
        ("user", REFLECTION_USER_PROMPT)
    ])
    
    llm: ChatOpenAI = ChatOpenAI(model="gpt-4o", temperature=0)
    structured_llm = llm.with_structured_output(ReflectionSchema)
    
    chain = prompt | structured_llm
    
    validation = await chain.ainvoke({
        "context": json.dumps(state.get('contexts', [])),
        "answer": state['answer']
    })
    
    print(f"LOG: [REFLECTION] Valido: {validation.valid} | Motivo: {validation.reason}")
    return {
        "is_valid": validation.valid, 
        "reflection_count": state.get("reflection_count", 0) + 1
    }


# 4. Construcao do Grafo (LangGraph)
# --------------------------------------------------------------------------
workflow = StateGraph(AgentState)

workflow.add_node("vector_path", retrieve_vector_node)
workflow.add_node("sql_path", query_sql_node)
workflow.add_node("generate", generate_answer_node)
workflow.add_node("reflect", reflect_node)
workflow.add_node("router", router_node)

workflow.add_edge(START, "router")
workflow.add_conditional_edges("router", lambda s: s["target"], {
    "vector": "vector_path", 
    "sql": "sql_path", 
    "none": "generate"
})

workflow.add_edge("vector_path", "generate")
workflow.add_edge("sql_path", "generate")
workflow.add_edge("generate", "reflect")

workflow.add_conditional_edges(
    "reflect", 
    lambda s: "end" if s["is_valid"] else "generate", 
    {"end": END, "generate": "generate"}
)

app = workflow.compile()


# 5. Funcoes Principais de Execucao
# --------------------------------------------------------------------------
async def run_xetroc_final(query: str) -> Dict[str, Any]:
    """Execucao assincrona do Grafo Xetroc com rastreamento MLFlow.

    :param query: String de consulta original do usuario.
    :return: Dicionario de estado final.
    """
    run_name: str = f"Run-{time.strftime('%H%M%S')}"
    with mlflow.start_run(run_name=run_name):
        mlflow.log_param("user_query", query)
        start_time: float = time.time()
        print(f"\nLOG: [START] Processando: {query}")
        
        try:
            # Invoca o grafo assincronamente (Regra 5)
            res: Dict[str, Any] = await app.ainvoke({"query": query})
            
            mlflow.log_metric("total_latency", time.time() - start_time)
            mlflow.set_tag("final_response", res["answer"])
            mlflow.log_param("router_decision", res.get("target"))
            
            print(f"\nXETROC: {res['answer']}\n")
            return res
        except Exception as e:
            mlflow.log_param("error", str(e))
            print(f"ERROR: {e}")
            raise e


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    async def main_test() -> None:
        """Integration test for the refactored agent graph."""
        await run_xetroc_final("Qual o limite de cinzas sulfatadas no diesel?")
        await run_xetroc_final("Quais ativos custaram mais de 500 reais?")
        
    asyncio.run(main_test())


