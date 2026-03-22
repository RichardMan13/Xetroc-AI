import mlflow
import pandas as pd
import numpy as np
import os
from evidently import Report 
from evidently.presets import DataSummaryPreset

# Servidor MLFlow
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
mlflow.set_tracking_uri(MLFLOW_URI)

def generate_quality_report():
    print(f"\n[MONITOR] Orquestrando Métricas Enriquecidas...")
    
    try:
        df_runs = mlflow.search_runs(experiment_names=["Xetroc-RAG-Agent"])
    except Exception as e:
        print(f"XERRO: {e}")
        return

    # 1. Pipeline de Extração com Inteligência Manual
    rows = []
    for _, row in df_runs.iterrows():
        q = row.get('params.user_query') or row.get('params.query')
        r = row.get('tags.final_response')
        
        if q and r:
            resp_str = str(r)
            # Calculamos as métricas de qualidade aqui no Python (Seguro!)
            rows.append({
                'query': str(q),
                'response': resp_str,
                'resp_words': len(resp_str.split()),
                'resp_chars': len(resp_str)
            })
    
    m_df = pd.DataFrame(rows).replace([np.nan, None], 0)
    print(f"[MONITOR] Analisando {len(m_df)} rodadas com estatísticas de texto.")

    # 2. Configuração do Report (Usa o Preset estável)
    report = Report(metrics=[
        DataSummaryPreset()
    ])

    print("[MONITOR] Finalizando Dashboard Visual...")
    try:
        mid = len(m_df) // 2
        result = report.run(reference_data=m_df.iloc[:mid], 
                          current_data=m_df.iloc[mid:])
        
        os.makedirs('reports', exist_ok=True)
        report_path = 'reports/xetroc_quality_report.html'
        result.save_html(report_path)
        
        print("\n" + "="*60)
        print(f"✅ MONITORAMENTO 100% OPERACIONAL!")
        print(f"📍 Link: http://localhost:8001/xetroc_quality_report.html")
        print("="*60)
    except Exception as e:
        print(f"XERRO Final: {e}")

if __name__ == "__main__":
    generate_quality_report()
