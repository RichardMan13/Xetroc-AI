import os
import sys

# Adicionar raiz ao PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.agents.graph import app

def generate_graph_image():
    print("\n[DOCS] Gerando Imagem do Fluxo LangGraph (PNG)...")
    try:
        # Gera os bytes da imagem PNG diretamente do LangGraph
        # Nota: Requer pygraphviz ou que o ambiente suporte a renderização mermaid do LangGraph
        img_data = app.get_graph().draw_mermaid_png()
        
        # Salva em um diretório apropriadamente chamado
        os.makedirs('docs', exist_ok=True)
        image_path = 'docs/langgraph_workflow.png'
        
        with open(image_path, 'wb') as f:
            f.write(img_data)
            
        print("\n" + "="*60)
        print(f"SUCESSO: Imagem do fluxo gerada em {image_path}")
        print("="*60)
        
    except Exception as e:
        print(f"ERRO: Não foi possível gerar a imagem. {e}")

if __name__ == "__main__":
    generate_graph_image()


