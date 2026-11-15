"""
Script de teste de conexao isolada com o OpenRouter.
Possui descoberta automatica e dinamica de modelos gratuitos disponiveis,
priorizando modelos de chat com retorno textual limpo e sem custo.
"""

import sys
from pathlib import Path
import requests

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

from openai import OpenAI


def load_secrets() -> dict:
    secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        print(f"ERRO: Arquivo nao encontrado em: {secrets_path}")
        print("Crie o arquivo .streamlit/secrets.toml com sua chave do OpenRouter.")
        sys.exit(1)

    if tomllib is None:
        secrets = {}
        with open(secrets_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    secrets[key.strip()] = val.strip().strip('"').strip("'")
        return secrets

    with open(secrets_path, "rb") as f:
        return tomllib.load(f)


def get_available_free_models() -> list[str]:
    """
    Consulta a API do OpenRouter e retorna os modelos gratuitos ativos no momento,
    ordenados com preferencia para modelos de chat direto.
    """
    preferred_order = [
        "particle-ai/particle-1:free",
        "baidu/ernie-5.5-flash-preview:free",
        "cohere/north-mini-code:free",
        "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        "nvidia/nemotron-3-ultra-550b-a55b:free",
        "liquid/lfm-3-1.7b:free",
        "inclusionai/ling-3.2-flash:free",
    ]

    try:
        url = "https://openrouter.ai/api/v1/models"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json().get("data", [])
            live_free = [
                m["id"] for m in data
                if ":free" in m.get("id", "") or (
                    m.get("pricing", {}).get("prompt") == "0" and
                    m.get("pricing", {}).get("completion") == "0"
                )
            ]
            
            # Ordena com base na lista de preferencia + quaisquer outros que aparecerem
            ordered = [m for m in preferred_order if m in live_free]
            for m in live_free:
                if m not in ordered:
                    ordered.append(m)
            return ordered
    except Exception as e:
        print(f"Aviso ao consultar catalogo de modelos: {e}")
    
    return preferred_order


def test_openrouter():
    secrets = load_secrets()
    api_key = secrets.get("OPENROUTER_API_KEY", "").strip()
    configured_model = secrets.get("OPENROUTER_MODEL", "auto").strip()

    if not api_key or api_key == "sua_chave_openrouter_aqui":
        print("AVISO: Chave da API ainda nao configurada!")
        print("Abra o arquivo .streamlit/secrets.toml e insira sua chave OPENROUTER_API_KEY.")
        return False

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    models_to_try = []
    if configured_model and configured_model.lower() != "auto":
        models_to_try.append(configured_model)

    print("Obtendo modelos gratuitos ativos no OpenRouter...")
    free_models = get_available_free_models()
    for m in free_models:
        if m not in models_to_try:
            models_to_try.append(m)

    print(f"Iniciando teste com modelos disponiveis...")

    for model in models_to_try:
        try:
            print(f"Tentando modelo: {model}...")
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Voce e um assistente prestativo e conciso."},
                    {"role": "user", "content": "Escreva exatamente: Conexao com OpenRouter estabelecida com sucesso!"}
                ],
                max_tokens=100,
                temperature=0.2,
            )

            msg = response.choices[0].message
            content = msg.content or ""
            content = content.strip()

            if content:
                print(f"\nModelo conectado com sucesso: {model}")
                print("\n--- RESPOSTA DA API ---")
                print(content)
                print("-----------------------")
                print("\nSUCESSO: A conexao com o OpenRouter foi validada com exito!")
                return True
            else:
                print(f"Modelo {model} nao retornou texto no campo content, tentando proximo...")

        except Exception as e:
            error_str = str(e)
            print(f"Modelo {model} indisponivel ({error_str[:70]}...). Tentando proximo...")

    print("\nFALHA: Nenhum dos modelos gratuitos disponiveis respondeu.")
    return False


if __name__ == "__main__":
    test_openrouter()
