# Xetroc: Inteligência Generativa para Normas Técnicas e Manutenção

![Xetroc Banner](https://img.shields.io/badge/Status-Project%20In%20Development-blueviolet?style=for-the-badge)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Prefect](https://img.shields.io/badge/Orchestration-Prefect-white?style=for-the-badge&logo=prefect)
![LangGraph](https://img.shields.io/badge/Agentic-LangGraph-orange?style=for-the-badge)

O **Xetroc** é um projeto de alta complexidade que integra Engenharia de Dados robusta com o estado da arte em IA Generativa (GenAI). O objetivo é transformar a gestão de ativos industriais através de um sistema que não apenas consulta normas técnicas, mas também analisa o histórico de manutenção de forma agêntica e precisa.

---

## Arquitetura e Estrutura Inicial

O projeto utiliza uma infraestrutura moderna focada em escalabilidade e precisão técnica:

- **Ambiente:** Serviços containerizados com Docker para garantir portabilidade.
- **Armazenamento Híbrido:**
  - **SQL (PostgreSQL):** Gerenciamento do histórico estruturado de ordens de serviço, falhas e ativos.
  - **Vector DB (ChromaDB/Qdrant):** Armazenamento de normas técnicas com metadados detalhados (ID, capítulo, revisão).
- **Stack de Embeddings:** Uso de modelos otimizados para a língua portuguesa (ex: `paraphrase-multilingual-MiniLM-L12-v2`).

---

## Ingestão Orquestrada (Camada Prefect)

O fluxo de dados é gerenciado por pipelines de ETL que garantem a atualização contínua do conhecimento da IA:

1.  **Scraping/Parsing:** Tasks no Prefect monitoram fontes de normas. Extração via PyMuPDF/Unstructured preservando hierarquia de títulos e tabelas.
2.  **Chunking Estratégico:** Divisão focada em seções lógicas de normas técnicas (Recursive Character Text Splitter).
3.  **Pipeline de Vetorização:** Cálculo de embeddings em batch e operações de *upsert* no Vector Database.
4.  **Trigger de Atualização:** Re-indexação automática disparada pela detecção de novos arquivos.

---

## Motor de Recuperação (Advanced RAG)

Diferente de sistemas RAG simples, o Xetroc foca na precisão extrema necessária para normas industriais:

*   **Retrieval Híbrido:** Combinação de busca vetorial (semântica) com busca textual clássica (Keyword/BM25) para capturar termos técnicos específicos.
*   **Camada de Re-ranking:**
    *   Filtragem inicial dos Top 20 resultados.
    *   Refinamento via **Cross-Encoder** (BGE-Reranker).
    *   Entrega dos Top 5 resultados mais relevantes para o LLM, reduzindo ruído e otimizando custos.
*   **Prompt Optimization:** Context window configurada para diferenciar claramente entre "Normas" e "Histórico de Manutenção".

---

## Camada Agêntica (LangGraph)

Utilizamos o **LangGraph** para permitir fluxos cíclicos e tomadas de decisão baseadas em estado, fugindo da linearidade de um chatbot comum.

### Ferramentas (Tools)
- `search_technical_norms`: Consulta profunda no Vector DB.
- `query_maintenance_history`: Consulta SQL no histórico de falhas.
- `calculate_risk`: Função Python para cálculos matemáticos específicos baseados em normas.

### Lógica do Grafo
- **Nodo Roteador:** O LLM analisa a intenção do usuário e direciona para a ferramenta adequada (Normas vs SQL).
- **Nodo de Reflexão:** O agente valida se a resposta gerada (ex: um método de conserto) está em conformidade com as normas técnicas antes de entregar ao usuário final.

---

## Roadmap de Implementação

| Fase | Duração | Entregável Principal |
| :--- | :--- | :--- |
| **Fase 1: Ingestão** | Semanas 1-2 | Pipeline Prefect funcional e Vector DB populado. |
| **Fase 2: RAG Advanced** | Semana 3 | Busca com Re-ranking e métricas de precisão (Hit Rate). |
| **Fase 3: Agentes** | Semanas 4-5 | Integradção SQL + PDF via LangGraph com chamadas de função. |
| **Fase 4: UI e Avaliação** | Semana 6 | Frontend em Streamlit e testes com especialistas técnicos. |

---

## Tecnologias Utilizadas

- **Linguagem:** Python 3.10+
- **Orquestração:** Prefect
- **IA/ML:** LangGraph (LangChain), OpenAI/Cohere, Cross-Encoders
- **Banco de Dados:** PostgreSQL, ChromaDB/Qdrant
- **Interface:** Streamlit
- **DevOps:** Docker

---

## Como Iniciar (Em breve)

*Nota: Este projeto está em fase inicial de desenvolvimento.*

1. Clone o repositório:
   ```bash
   git clone https://github.com/RichardMan13/Xetroc-AI.git
   ```
2. Configure o ambiente virtual e variáveis de ambiente.
3. Suba os serviços via Docker Compose.