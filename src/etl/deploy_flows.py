import os
from prefect import flow
from src.etl.ingestion import run_ingestion
from src.etl.vector_indexer import run_indexing

def deploy_flows():
    """
    Registra os fluxos no Prefect Server (Docker) para automacao.
    """
    print("Iniciando registro de Deployments no servidor...")

    # Registrar Fluxo de Ingestao de PDFs
    # Em Prefect 3.0, para process workers, usamos .from_source
    run_ingestion.from_source(
        source=os.getcwd(), # Usa a pasta atual como fonte
        entrypoint="src/etl/ingestion.py:run_ingestion"
    ).deploy(
        name="Ingestao-PDF-Normas",
        work_pool_name="default-agent-pool",
    )

    # Registrar Fluxo de Indexacao Vetorial (Qdrant)
    run_indexing.from_source(
        source=os.getcwd(),
        entrypoint="src/etl/vector_indexer.py:run_indexing"
    ).deploy(
        name="Indexacao-Vetor-Qdrant",
        work_pool_name="default-agent-pool",
    )
    
    print("-" * 50)
    print("Sucesso: Fluxos registrados!")
    print("Acesse o Dashboard: http://localhost:4200")
    print("Para rodar esses fluxos agora pelo terminal, voce precisara de um worker ligado.")
    print("-" * 50)

if __name__ == "__main__":
    deploy_flows()
