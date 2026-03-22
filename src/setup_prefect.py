import asyncio
import os
from dotenv import load_dotenv

# Importa os tipos de blocos do Prefect
from prefect.blocks.system import Secret

# Carrega as variáveis de ambiente do .env
load_dotenv()

async def create_prefect_blocks():
    """
    Registra credenciais do .env como Secret Blocks no Prefect.
    Estes blocos ficam criptografados e salvos no servidor/container do Prefect.
    """
    
    # 1. Configurando a Chave da OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    
    # Verifica se a chave foi preenchida (não é o valor padrão do exemplo)
    if openai_key and openai_key != "sua_chave_openai_aqui":
        try:
            # Cria/Sobrescreve o bloco secreto chamado "openai-key"
            openai_block = Secret(value=openai_key)
            await openai_block.save(name="openai-api-key", overwrite=True)
            print("Bloco 'openai-api-key' registrado com sucesso no Prefect.")
        except Exception as e:
            print(f"Erro ao registrar bloco da OpenAI: {e}")
    else:
        print("OPENAI_API_KEY não encontrada ou ainda é o valor padrão no .env. Pulando...")

    # No futuro, se definirmos outros serviços, podemos adicionar aqui:
    # cohere_key = os.getenv("COHERE_API_KEY")
    # if cohere_key: ...
    
    print("\nSetup de Blocos do Prefect Finalizado!")

if __name__ == "__main__":
    # Roda o setup de forma assíncrona (exigido pelo Prefect)
    asyncio.run(create_prefect_blocks())
