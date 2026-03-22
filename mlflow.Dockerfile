# --- MLFlow Custom Image with PostgreSQL Support (Regra 2) ---
FROM ghcr.io/mlflow/mlflow:v2.11.3

# Instala o driver necessário (psycopg2) e curl para o healthcheck
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    pip install --no-cache-dir psycopg2-binary && \
    rm -rf /var/lib/apt/lists/*

# Configura usuário não-root (Regra 5 - Least Privilege)
RUN adduser --disabled-password --gecos "" mlflowuser && \
    mkdir -p /mlflow && \
    chown -R mlflowuser:mlflowuser /mlflow

USER mlflowuser
WORKDIR /mlflow
