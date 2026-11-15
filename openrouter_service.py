"""
Modulo responsavel exclusivamente pela comunicacao com o gateway OpenRouter.
Utiliza o SDK OpenAI oficial apontado para https://openrouter.ai/api/v1.
Inclui descoberta dinamica e fallback de modelos gratuitos, sem trocar para modelos pagos.
"""

from pathlib import Path
from typing import Optional
import requests
import streamlit as st
from openai import OpenAI

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

# Cache de modelos gratuitos para evitar requisicoes redundantes
_CACHED_FREE_MODELS: list[str] = []


def _read_secrets_file() -> dict:
    """Leitura direta do arquivo secrets.toml como fallback."""
    secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        return {}

    if tomllib is not None:
        try:
            with open(secrets_path, "rb") as f:
                return tomllib.load(f)
        except Exception:
            return {}

    # Leitura manual simples caso tomllib falhe
    data = {}
    try:
        with open(secrets_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    data[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return data


def _get_api_credentials() -> tuple[str, str]:
    """Recupera API key e modelo de st.secrets ou diretamente do arquivo de configuracao."""
    api_key = ""
    configured_model = "auto"

    # Tentativa 1: st.secrets (quando rodando via streamlit run)
    try:
        api_key = st.secrets.get("OPENROUTER_API_KEY", "").strip()
        configured_model = st.secrets.get("OPENROUTER_MODEL", "auto").strip()
    except Exception:
        pass

    # Tentativa 2: secrets.toml direto (quando rodando em testes ou scripts)
    if not api_key or api_key == "sua_chave_openrouter_aqui":
        file_secrets = _read_secrets_file()
        api_key = file_secrets.get("OPENROUTER_API_KEY", "").strip()
        configured_model = file_secrets.get("OPENROUTER_MODEL", "auto").strip()

    if not api_key or api_key == "sua_chave_openrouter_aqui":
        raise ValueError(
            "Chave de API do OpenRouter não configurada. "
            "Por favor, configure 'OPENROUTER_API_KEY' no arquivo .streamlit/secrets.toml."
        )

    return api_key, configured_model


def _fetch_available_free_models() -> list[str]:
    """Consulta os modelos gratuitos (:free) ativos no OpenRouter."""
    global _CACHED_FREE_MODELS
    if _CACHED_FREE_MODELS:
        return _CACHED_FREE_MODELS

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
        response = requests.get(url, timeout=8)
        if response.status_code == 200:
            data = response.json().get("data", [])
            live_free = [
                m["id"] for m in data
                if ":free" in m.get("id", "") or (
                    m.get("pricing", {}).get("prompt") == "0" and
                    m.get("pricing", {}).get("completion") == "0"
                )
            ]
            ordered = [m for m in preferred_order if m in live_free]
            for m in live_free:
                if m not in ordered:
                    ordered.append(m)
            _CACHED_FREE_MODELS = ordered
            return ordered
    except Exception:
        pass

    _CACHED_FREE_MODELS = preferred_order
    return preferred_order


def generate_chat_completion(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1500,
    temperature: float = 0.4
) -> str:
    """
    Executa uma chamada de chat completion ao OpenRouter com mensagens de sistema e usuario.
    Possui protecao de fallback automatico entre modelos gratuitos e tratamento de excecoes.
    """
    api_key, configured_model = _get_api_credentials()

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        timeout=60.0
    )

    models_to_try: list[str] = []
    if configured_model and configured_model.lower() != "auto":
        models_to_try.append(configured_model)

    free_models = _fetch_available_free_models()
    for m in free_models:
        if m not in models_to_try:
            models_to_try.append(m)

    last_error: Optional[Exception] = None

    for model in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )

            msg = response.choices[0].message
            content = msg.content or ""
            content = content.strip()

            if content:
                return content
        except Exception as e:
            last_error = e
            continue

    error_msg = str(last_error) if last_error else "Nenhum conteúdo foi retornado pelo modelo."
    if "401" in error_msg:
        raise RuntimeError("Erro de autenticação: Verifique se sua chave do OpenRouter é válida.")
    elif "429" in error_msg:
        raise RuntimeError("Limite de requisições atingido no OpenRouter. Aguarde alguns instantes e tente novamente.")
    else:
        raise RuntimeError(f"Falha na comunicação com o OpenRouter: {error_msg}")
