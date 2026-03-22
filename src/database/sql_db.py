import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any
from dotenv import load_dotenv

class SQLDatabase:
    """Interface de comunicação com o banco de dados PostgreSQL do Xetroc."""

    def __init__(self):
        load_dotenv()
        self.host = os.getenv("POSTGRES_HOST", "127.0.0.1")
        self.port = os.getenv("POSTGRES_PORT", "5432")
        self.user = os.getenv("POSTGRES_USER", "postgres")
        self.password = os.getenv("POSTGRES_PASSWORD", "postgres123") # Prioridade para o .env
        self.db_name = os.getenv("POSTGRES_DB", "xetroc_maintenance")

    def _get_connection(self):
        """Estabelece a conexão com fallback automático para o banco padrão."""
        try:
            # Tenta a conexao com as configuracoes do .env
            print(f"DEBUG SQL: Tentando conectar em '{self.db_name}'...")
            return psycopg2.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                dbname=self.db_name,
                port=self.port,
                connect_timeout=5
            )
        except psycopg2.OperationalError as e:
            # Se o banco customizado nao existir, tenta o padrao 'postgres'
            if "database" in str(e) and self.db_name != "postgres":
                print(f"DEBUG SQL: Banco '{self.db_name}' nao encontrado. Tentando fallback para 'postgres'...")
                return psycopg2.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    dbname="postgres",
                    port=self.port,
                    connect_timeout=5
                )
            else:
                print(f"ERRO CRITICO SQL: Nao foi possível conectar ao PostgreSQL em {self.host}:{self.port}")
                print(f"DETALHE DO ERRO: {e}")
                raise e

    def setup_schema(self):
        """Cria as tabelas iniciais seguindo as Regras 1.1, 4.1 e 4.3 (PostgreSQL)."""
        conn = self._get_connection()
        cur = conn.cursor()
        
        print(f"INFO: Configurando schema no PostgreSQL...")
        
        # 1. Tabela de Ativos (Equipamentos) - Regra 4.3 (bigint identity)
        cur.execute("""
            create table if not exists assets (
                asset_id bigint generated always as identity primary key,
                tag text unique not null,
                name text not null,
                type text,
                installation_date date,
                location text
            );
            
            comment on table assets is 'Armazena informações sobre equipamentos e ativos industriais.';
            comment on column assets.tag is 'Tag única do ativo (ex: MOT-402).';
        """)

        # 2. Tabela de Manutenção - Regra 4.3 e 6.2
        cur.execute("""
            create table if not exists maintenance_history (
                maintenance_id bigint generated always as identity primary key,
                asset_tag text references assets(tag),
                event_date date not null,
                event_type text, -- preventiva, corretiva, falha
                description text,
                technician text,
                cost numeric(15, 2) -- regra 4.3 (numeric para dinheiro)
            );
            
            comment on table maintenance_history is 'Registro histórico de falhas e manutenções preventivas.';
        """)

        conn.commit()
        cur.close()
        conn.close()
        print("INFO: Schema SQL configurado com sucesso.")

    def seed_data(self):
        """Insere dados de exemplo seguindo Regra 1.1 (idempotente)."""
        conn = self._get_connection()
        cur = conn.cursor()

        print("INFO: Limpando tabelas e inserindo dados de teste (Seed IDempotente)...")

        # 1. Limpar e reiniciar IDs (Evita duplicatas em multiplas chamadas)
        cur.execute("truncate table maintenance_history, assets restart identity cascade;")

        # 2. Inserir motores e bombas
        cur.execute("""
            insert into assets (tag, name, type, installation_date, location)
            values 
                ('MOT-402', 'Motor de Passo de Alta Potência', 'Motor', '2023-01-15', 'Refinaria Setor A'),
                ('BOM-101', 'Bomba Centrífuga Principal', 'Bomba', '2022-06-10', 'Tanque de Armazenamento 1');
        """)

        # 3. Inserir histórico de manutenção (Incluindo Instalação p/ teste de 2023)
        cur.execute("""
            insert into maintenance_history (asset_tag, event_date, event_type, description, technician, cost)
            values 
                ('MOT-402', '2023-01-15', 'Instalação', 'Instalação inicial e comissionamento', 'Eng. Pedro', 0.00),
                ('MOT-402', '2024-02-10', 'Falha', 'Aquecimento excessivo nos enrolamentos', 'Eng. Pedro', 1500.00),
                ('MOT-402', '2024-03-01', 'Preventiva', 'Troca de rolamentos e lubrificação', 'Téc. Maria', 450.00),
                ('BOM-101', '2024-03-15', 'Corretiva', 'Vazamento no selo mecânico', 'Téc. João', 800.00);
        """)

        conn.commit()
        cur.close()
        conn.close()
        print("INFO: Seed finalizado. Banco populado com evento de 'Instalação' para o MOT-402.")

    def get_schema_info(self) -> str:
        """Retorna uma descrição textual do schema (lowercase p/ agente)."""
        return """
        Tabela 'assets':
        - tag (text, PK): Identificador único do ativo (ex: MOT-402)
        - name (text): Nome do equipamento
        - type (text): Tipo (Motor, Bomba, Valvula)
        
        Tabela 'maintenance_history':
        - asset_tag (text, FK): Tag do ativo relacionado
        - event_date (date): Data do evento
        - event_type (text): Tipo (Falha, Preventiva, Corretiva)
        - description (text): Detalhes da ocorrência
        - cost (numeric): Custo da manutenção
        """

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Executa uma consulta SQL arbitrária."""
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute(query)
            # Verifica se é uma consulta SELECT antes de dar fetch
            if cur.description:
                results = cur.fetchall()
                return results
            return [{"status": "success"}]
        except Exception as e:
            print(f"Erro na execução SQL: {e}")
            return [{"error": str(e)}]
        finally:
            cur.close()
            conn.close()

    def query_asset_history(self, tag: str) -> List[Dict[str, Any]]:
        """Busca histórico seguindo as Regras 1.2, 2.1 e 3.1 (PostgreSQL)."""
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # SQL seguindo Regras: Lowercase, Aliases explícitos (as), Inner Join
        query = """
            select
                a.name as asset_name,
                a.type as asset_type,
                m.event_date as event_date,
                m.event_type as event_type,
                m.description as description
            from
                assets as a
            inner join
                maintenance_history as m
                on a.tag = m.asset_tag
            where
                upper(a.tag) = upper(%s)
            order by
                m.event_date desc;
        """
        cur.execute(query, (tag,))
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        return results

if __name__ == "__main__":
    db = SQLDatabase()
    try:
        db.setup_schema()
        db.seed_data()
        
        # Teste de consulta
        print("\nTESTE DE CONSULTA (MOT-402):")
        historico = db.query_asset_history("MOT-402")
        for row in historico:
            print(f"- {row['event_date']}: {row['event_type']} -> {row['description']}")
    except Exception as e:
        print(f"ERRO FINAL: {e}")
