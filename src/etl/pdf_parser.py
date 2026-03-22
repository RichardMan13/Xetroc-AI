import fitz  # PyMuPDF
import os
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict

class PDFParser:
    """Extrai texto e tabelas de PDFs mantendo o contexto das seções para um RAG preciso."""

    def __init__(self, output_dir: str = "data/processed"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def parse(self, pdf_path: str) -> List[Dict]:
        """Extrai texto e tabelas, mantendo o contexto da secao atual."""
        doc = fitz.open(pdf_path)
        extracted_data = []
        current_section = "Introducao"
        
        print(f"Iniciando Extracao Full-RAG: {os.path.basename(pdf_path)}")

        for page_num, page in enumerate(doc, start=1):
            # 1. Extrair Tabelas (Convertendo para Markdown para melhor entendimento do LLM)
            try:
                tables = page.find_tables()
                for i, table in enumerate(tables):
                    df = table.to_pandas()
                    if not df.empty:
                        table_md = df.to_markdown(index=False)
                        extracted_data.append({
                            "text": f"Tabela encontrada na secao {current_section}:\n{table_md}",
                            "metadata": {
                                "source": os.path.basename(pdf_path),
                                "page": page_num,
                                "type": "table",
                                "section": current_section,
                                "block_id": f"table_{i}"
                            }
                        })
            except Exception as e:
                print(f"Erro ao extrair tabela na pagina {page_num}: {e}")

            # 2. Processar blocos de texto com deteccao de titulos
            blocks = page.get_text("dict")["blocks"]
            
            # Estatisticas de fontes
            font_sizes = []
            for b in blocks:
                if "lines" in b:
                    for l in b["lines"]:
                        for s in l["spans"]:
                            font_sizes.append(round(s["size"], 1))
            
            main_font_size = max(set(font_sizes), key=font_sizes.count) if font_sizes else 11

            for b_idx, b in enumerate(blocks):
                if "lines" not in b:
                    continue
                
                block_text = ""
                is_header = False

                for l in b["lines"]:
                    for s in l["spans"]:
                        span_text = s["text"].strip()
                        if not span_text:
                            continue
                        block_text += " " + span_text
                        
                        # Deteccao de Titulo (Heuristica de tamanho/estilo)
                        if s["size"] > (main_font_size + 1.5) or "bold" in s["font"].lower():
                            is_header = True

                block_text = block_text.strip()
                
                # Filtros de ruído
                if len(block_text) < 20 or block_text.isdigit():
                    continue
                
                # Se for um titulo, atualizamos a secao atual para os proximos blocos
                if is_header and len(block_text) < 150: # Evita confundir textos longos e em negrito com titulos
                    current_section = block_text

                extracted_data.append({
                    "text": block_text,
                    "metadata": {
                        "source": os.path.basename(pdf_path),
                        "page": page_num,
                        "section": current_section,
                        "is_header": is_header,
                        "block_id": b_idx,
                        "type": "text"
                    }
                })

        doc.close()
        return extracted_data

    def save_json(self, data: List[Dict], filename: str):
        """Salva os dados extraídos em um arquivo JSON para auditoria/cache."""
        output_file = self.output_dir / f"{filename}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Dados salvos em: {output_file}")

if __name__ == "__main__":
    # Teste rápido se o script for executado diretamente
    from dotenv import load_dotenv
    load_dotenv()
    parser = PDFParser()
    # Adicione um PDF na pasta data/raw e troque o nome abaixo para testar localmente:
    # results = parser.parse("data/raw/exemplo.pdf")
    # parser.save_json(results, "exemplo")
