import os
from pathlib import Path
from prefect import flow, task
from src.etl.pdf_parser import PDFParser
from src.etl.csv_parser import CSVParser

@task(name="Processar PDF")
def process_file(file_path: Path):
    """Lê apenas arquivos PDF."""
    ext = file_path.suffix.lower()
    
    if ext == ".pdf":
        parser = PDFParser()
        data = parser.parse(str(file_path))
        parser.save_json(data, file_path.stem)
        return f"PDF {file_path.name} processado com sucesso"
    
    return f"Arquivo {file_path.name} ignorado (apenas PDF suportado agora)"

@flow(name="Xetroc PDF-Only Ingestion")
def run_ingestion(raw_data_path: str = "data/raw"):
    """
    Fluxo focado 100% em relatórios PDF técnicos.
    Ignora caminhos antigos de CSV.
    """
    print(f"Iniciando ingestao de PDFs em: {raw_data_path}")
    base_path = Path(raw_data_path)
    
    # Busca apenas PDFs (de forma recursiva para seguranca, mas raiz preferencial)
    pdf_files = list(base_path.rglob("*.pdf"))
    
    print(f"Total de relatorios encontrados: {len(pdf_files)}")
    
    results = []
    for file in pdf_files:
        res = process_file(file)
        results.append(res)
    
    print("Pipeline de ingestao PDF finalizado!")
    return results

if __name__ == "__main__":
    # Para rodar localmente sem o servidor Prefect iniciado:
    # run_ingestion()
    
    # Para registrar no Prefect (se o servidor estiver rodando):
    run_ingestion()
