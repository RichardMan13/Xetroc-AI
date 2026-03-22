# Xetroc: Inteligência Generativa para Normas Técnicas e Manutenção

![Xetroc Banner](docs/xetroc_banner.png)

![Status](https://img.shields.io/badge/Status-Project%20Operational-green?style=for-the-badge)
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
  - **Vector DB (Qdrant):** Armazenamento de normas técnicas com metadados detalhados (ID, capítulo, revisão) usando busca híbrida.
- **Stack de Embeddings:** Uso do modelo `text-embedding-3-small` da OpenAI para alta precisão semântica e suporte multilingue.

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
- `search_technical_norms`: Consulta profunda no Vector DB usando RAG híbrido.
- `query_maintenance_history`: Cérebro Text-to-SQL que consulta dinamicamente o banco PostgreSQL.


### Lógica do Grafo
- **Nodo Roteador:** O LLM analisa a intenção do usuário e direciona para a ferramenta adequada (Normas vs SQL).
- **Nodo de Reflexão:** O agente valida se a resposta gerada (ex: um método de conserto) está em conformidade com as normas técnicas antes de entregar ao usuário final.

---

## 🗺️ Plano de Execução (Roadmap Detalhado)

Abaixo estão as etapas de desenvolvimento organizadas em formato de checklist para acompanhamento do progresso:

### 🚀 Fase 0: Setup e Infraestrutura
- [x] **Configuração do Ambiente Docker**: Provisionar containers para PostgreSQL, Qdrant, Prefect e MLFlow.
- [x] **Estruturação do Repositório**: Definir módulos para `src/etl`, `src/agents`, `src/database` e `src/ui`.
- [x] **Gerenciamento de Segredos**: Configurar `.env` e integração com Prefect Blocks para chaves de API.
- [x] **Infraestrutura MLOps (Novo)**: Provisionar servidor MLFlow para tracking de experimentos e artefatos.

### 📥 Fase 1: Ingestão e ETL (Orquestração Prefect)
- [x] **Extração de PDF (Parsing)**: Implementar leitura de normas técnicas preservando metadados e hierarquia.
- [x] **Chunking Estratégico**: Criar lógica de divisão de texto baseada em capítulos e seções das normas.
- [x] **Pipeline de Embeddings**: Configurar geração de vetores usando modelos multilingues.
- [x] **Automação de Indexação**: Criar flows no Prefect para monitoramento de pastas e atualização automática do Vector DB.

### 🔍 Fase 2: Recuperação Avançada (Advanced RAG)
- [x] **Busca Híbrida**: Implementar busca combinada (Semântica + Keyword/BM25).
- [x] **Re-ranking**: Integrar Cross-Encoder (BGE-Reranker) para filtrar os top resultados.
- [x] **Injeção de Contexto**: Refinar prompts para evitar alucinações técnicas.

### 🤖 Fase 3: Inteligência Agêntica (LangGraph) 🏆
- [x] **Modelagem do Grafo**: Definir estados e transições (Roteamento -> Recuperação -> Reflexão).
- [x] **Implementação de Ferramentas (Tools)**: `search_technical_norms` e `Text-to-SQL`.
- [x] **Nodo de Reflexão**: Lógica de autocrítica para validação técnica da resposta.

### 📊 Fase 4: MLOps & Observabilidade 🏆
- [x] **Rastreamento de Experimentos**: Integração total com MLFlow para logs de produção.
- [x] **Monitoramento de Dados**: Implementação de Dashboards de Qualidade com Evidently AI.
- [x] **Logs de Produção**: Auditoria técnica via Tags estruturadas e Snapshots.

### 🔬 Fase 5: Interface e Validação 🏆
- [x] **Streamlit Chat UI**: Criar aplicação web para interação em tempo real.
- [x] **Integração de Dashboard**: Exibir métricas de qualidade dentro da interface Streamlit.
- [x] **Validação Técnica Final**: Testes fim-a-fim com massa de dados real.

- [x] **Documentação Final**: Completar guias de setup, diagramas de arquitetura e manual do usuário. Ver [MANUAL_TECNICO.md](./MANUAL_TECNICO.md).

---

## Tecnologias Utilizadas

- **Linguagem:** Python 3.10+
- **Orquestração:** Prefect
- **IA/ML:** LangGraph, OpenAI (Embeddings/LLM), BGE-Reranker
- **Banco de Dados:** PostgreSQL, Qdrant
- **Interface:** Streamlit
- **DevOps:** Docker, Prefect, MLFlow

---

## 🚀 Como Iniciar

Este projeto utiliza uma infraestrutura robusta, containerizada e orquestrada. Siga os passos abaixo para preparar seu ambiente de ponta a ponta:

### 1. Preparação do Ambiente
Clone o repositório e configure seu ambiente virtual Python:
```bash
git clone https://github.com/RichardMan13/Xetroc-AI.git
cd Xetroc-AI
python -m venv .venv
.\.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Configurações de Segredos (`.env`)
Crie o arquivo `.env` baseado no `.env.example` e preencha suas chaves. As principais são:
- `OPENAI_API_KEY`: Necessária para Embeddings e Agente RAG.
- `POSTGRES_PASSWORD`: Senha para o PostgreSQL (Padrão: `postgres123`).

### 3. Subida da Infraestrutura (Docker)
Inicie todos os serviços (Postgres, Qdrant, Prefect, MLFlow) em segundo plano:
```bash
docker-compose up -d --build --force-recreate
```
*Dica: Use `docker-compose ps` para verificar se todos os serviços estão **(healthy)**. Se o MLFlow demorar, aguarde alguns segundos enquanto ele processa as migrações.*

### 4. Configuração do Orquestrador (Prefect)
Com o Docker rodando, aponte seu CLI local para o servidor e registre os segredos:
```bash
# Aponta o Prefect local para o Docker
prefect config set PREFECT_API_URL="http://localhost:4200/api"

# Registra a OpenAI API Key como um Prefect Secret Block
python -m src.setup_prefect

# Cria o pool de execução local (necessário apenas uma vez)
prefect work-pool create "default-agent-pool" --type process
```

### 5. Deploy e Início do Worker
Dê o "deploy" nos fluxos de ETL no servidor e ligue o "motor" (Worker):
```bash
# Registra os fluxos de Ingestão e Indexação Híbrida no servidor
python -m src.etl.deploy_flows

# Inicia o worker para ouvir e executar as tarefas (mantenha este terminal aberto)
prefect worker start --pool "default-agent-pool"
```

### 6. Processamento de Dados (ETL)
Coloque seus PDFs em `data/raw` e dispare a ingestão via terminal ou via Dashboard ([localhost:4200](http://localhost:4200)):
```bash
# 1. Extração de texto dos PDFs
prefect deployment run "Xetroc PDF-Only Ingestion/Ingestao-PDF-Normas"

# 2. Indexação Vetorial no Qdrant (após finalizar o passo 1)
prefect deployment run "Xetroc PDF-Only Ingestion/Indexacao-Vetor-Qdrant"
```

### 7. Interface e Monitoramento (UI)
Para interagir com o Xetroc e ver os relatórios de qualidade:
```bash
# Terminal 1: Interface Streamlit (Chat Principal)
streamlit run src/ui/app.py

# Terminal 2: Servidor de Relatórios (Quality Monitor)
python -m http.server 8001 --directory reports
```
*Acesse o chat em: [http://localhost:8501](http://localhost:8501)*

---

## 📂 Estrutura do Projeto
- `src/etl`: Pipeline de extração PDF, detecção de mudanças e indexação híbrida.
- `src/agents`: Cérebro do sistema: LangGraph, Retriever com Re-ranker e Answer Generator.
- `src/database`: Interfaces de persistência (Qdrant para Vetores e Postgres para SQL).
- `src/ui`: Interface moderna Streamlit com temas Dark Mode e Glassmorphism.
- `reports`: Relatórios de Drift e Qualidade gerados pelo Evidently AI.
- `artifacts`: Logs de experimentos e métricas de latência do MLFlow.