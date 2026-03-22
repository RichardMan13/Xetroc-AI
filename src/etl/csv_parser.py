import pandas as pd
from pathlib import Path
from typing import List, Dict

class CSVParser:
    """Processa arquivos CSV de produção tecnica, lidando com delimitadores e headers complexos."""

    def __init__(self, output_dir: str = "data/processed"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def parse(self, csv_path: str) -> pd.DataFrame:
        """Le o CSV e retorna um DataFrame limpo."""
        csv_path = Path(csv_path)
        print(f"Iniciando Extração CSV: {csv_path.name}")

        # Os arquivos da ANP geralmente usam ; como separador e latin-1
        # Pulando as primeias 4 linhas de metadados do orgao
        try:
            df = pd.read_csv(
                csv_path, 
                sep=';', 
                encoding='latin-1', 
                skiprows=4,
                low_memory=False
            )
            
            # Limpeza básica de nomes de colunas (remover quebras de linha e espaços)
            df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
            
            # Remover colunas totalmente nulas (geradas pelo excesso de ; no final das linhas)
            df = df.dropna(axis=1, how='all')
            
            # Adicionar metadadado de origem
            df['source_file'] = csv_path.name
            
            return df
        except Exception as e:
            print(f"Erro ao processar CSV {csv_path.name}: {e}")
            return pd.DataFrame()

    def save_parquet(self, df: pd.DataFrame, filename: str):
        """Salva em Parquet para eficiência ou JSON para auditoria."""
        if df.empty:
            return
        
        output_file = self.output_dir / f"{filename}.parquet"
        df.to_parquet(output_file, index=False)
        print(f"Dados salvos em: {output_file}")

if __name__ == "__main__":
    # Teste rápido
    parser = CSVParser()
    # df = parser.parse("data/raw/2018/2018_producao_mar.csv")
    # print(df.head())
