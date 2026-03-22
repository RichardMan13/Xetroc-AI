import asyncio
import os
import sys
import time
from typing import List, Optional

# --- Ajuste de Caminho para suportar imports de 'src' ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
from dotenv import load_dotenv

from src.agents.graph import run_xetroc_final


# 1. Configurações de Elite (Cachadas p/ Performance)
@st.cache_resource
def setup_page() -> None:
    """Configura o layout básico da página e o branding.

    Define o título da página, ícone e modo de layout de acordo com as melhores práticas do Streamlit.
    """
    st.set_page_config(
        page_title="Xetroc: GenAI para Normas Tecnicas", 
        page_icon="[X]",
        layout="wide"
    )


def apply_custom_css() -> None:
    """Injeta CSS customizado para o visual industrial do Xetroc.

    Estiliza mensagens de chat e caixas de fontes para melhor legibilidade.
    """
    st.markdown("""
        <style>
        .stApp { background-color: #0E1117; color: #E0E0E0; }
        .stChatMessage { border-radius: 10px; margin-bottom: 10px; border: 1px solid #1E2129; }
        .source-box { 
            font-size: 0.85rem; color: #00FFCC; background-color: #1A1C23; 
            padding: 8px 12px; border-radius: 6px; margin-top: 5px; 
            border-left: 3px solid #00FFCC;
        }
        </style>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Renderiza a barra lateral de status e navegação.

    Contém imagens de branding, indicadores de status do sistema e botões de controle.
    """
    with st.sidebar:
        st.image("https://img.icons8.com/isometric/512/processor.png", width=100)
        st.title("XETROC")
        st.info("Sistema de Auditoria Agentica Ativo")
        st.success("Conectado ao MLFlow Port 5000")
        st.warning("Relatorio de Qualidade Port 8001")
        
        if st.button("Limpar Historico", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()


async def handle_user_input(prompt: str) -> None:
    """Processa a entrada do usuário através do grafo do agente.

    :param prompt: A consulta bruta do usuário.
    """
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Consultando normas e historico tecnico..."):
            try:
                # Execução do Grafo (Assíncrona)
                result = await run_xetroc_final(prompt)
                ans = result["answer"]
                srcs = result.get("sources", [])
                
                st.markdown(ans)
                if srcs:
                    st.markdown("**Fontes Consultadas:**")
                    for s in srcs:
                        st.markdown(f"<div class='source-box'>[L] {s}</div>", unsafe_allow_html=True)
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": ans,
                    "sources": srcs
                })
            except Exception as e:
                st.error(f"Erro no processamento agentico: {e}")


def render_chat_tab() -> None:
    """Renderiza a aba principal de interação com o chat do agente."""
    st.title("Xetroc: Inteligencia Industrial")
    st.markdown("---")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Mostrar histórico
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                st.markdown("**Fontes:**")
                for s in message["sources"]:
                    st.markdown(f"<div class='source-box'>[L] {s}</div>", unsafe_allow_html=True)

    # Input do Usuário
    if user_prompt := st.chat_input("Ex: Qual o limite de pressao para a valvula V-101?"):
        asyncio.run(handle_user_input(user_prompt))


def render_monitor_tab() -> None:
    """Renderiza a aba de monitoramento com o iframe do relatório Evidently AI."""
    st.title("Dashboard de Auditoria (Evidently AI)")
    st.markdown("Relatorio interativo de qualidade e deteccao de drift via porta 8001.")
    st.components.v1.iframe(src="http://localhost:8001/xetroc_quality_report.html", height=800, scrolling=True)


def main() -> None:
    """Ponto de entrada principal da aplicação.

    Orquestra configurações, estilos, barra lateral e navegação por abas.
    """
    load_dotenv()
    setup_page()
    apply_custom_css()
    render_sidebar()

    # Layout de Abas (Regra 3.2)
    tab_chat, tab_monitor = st.tabs(["INTERAÇÃO AGENTICA", "AUDITORIA DE QUALIDADE"])
    
    with tab_chat:
        render_chat_tab()

    with tab_monitor:
        render_monitor_tab()


if __name__ == "__main__":
    main()
