"""
Modulo responsavel exclusivamente pela comunicacao com o gateway OpenRouter.
Otimizado para alta performance:
- Descoberta dinamica dos modelos gratuitos disponiveis
- Memorizacao do modelo gratuito ativo (evita tentativas redundantes entre agentes)
- Timeouts ajustados para failover rapido em caso de congestionamento
- Cliente criado a cada chamada para garantir leitura correta de st.secrets no Streamlit Cloud
"""

from pathlib import Path
from typing import Optional
import requests

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

# Cache de modelos — seguro manter em nivel de modulo (nao envolve credenciais)
_CACHED_FREE_MODELS: list[str] = []
_ACTIVE_WORKING_MODEL: Optional[str] = None


def _read_secrets_file() -> dict:
    """Leitura direta do arquivo secrets.toml como fallback (ambiente local)."""
    secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        return {}

    if tomllib is not None:
        try:
            with open(secrets_path, "rb") as f:
                return tomllib.load(f)
        except Exception:
            return {}

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
    """
    Recupera API key e modelo de st.secrets ou diretamente do arquivo de configuracao.
    A importacao de streamlit e feita aqui (lazy) para garantir que st.secrets
    ja esteja totalmente inicializado quando esta funcao for chamada em runtime.
    """
    import streamlit as st  # import lazy — garante leitura correta no Streamlit Cloud

    api_key = ""
    configured_model = "auto"

    try:
        api_key = st.secrets.get("OPENROUTER_API_KEY", "").strip()
        configured_model = st.secrets.get("OPENROUTER_MODEL", "auto").strip()
    except Exception:
        pass

    # Fallback para arquivo local (ambiente de desenvolvimento)
    if not api_key or api_key == "sua_chave_openrouter_aqui":
        file_secrets = _read_secrets_file()
        api_key = file_secrets.get("OPENROUTER_API_KEY", "").strip()
        configured_model = file_secrets.get("OPENROUTER_MODEL", "auto").strip() or "auto"

    if not api_key or api_key == "sua_chave_openrouter_aqui":
        raise ValueError(
            "Chave de API do OpenRouter não encontrada. "
            "No Streamlit Cloud, configure 'OPENROUTER_API_KEY' na seção Secrets do painel do app. "
            "No ambiente local, configure em .streamlit/secrets.toml."
        )

    return api_key, configured_model


def _fetch_available_free_models() -> list[str]:
    """Consulta os modelos gratuitos (:free) com cache em memoria."""
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
        response = requests.get(url, timeout=5)
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
    max_tokens: int = 1200,
    temperature: float = 0.35
) -> str:
    """
    Executa uma chamada de chat completion ao OpenRouter com mensagens de sistema e usuario.
    - O cliente OpenAI e criado a cada chamada para garantir que a api_key lida de
      st.secrets seja sempre a mais atual (corrige autenticacao no Streamlit Cloud).
    - Prioriza o modelo que ja respondeu com sucesso na chamada anterior (mesma sessao).
    - Failover rapido em caso de erro.
    """
    from openai import OpenAI  # import lazy — evita erro de import antes de st.secrets estar pronto

    global _ACTIVE_WORKING_MODEL

    api_key, configured_model = _get_api_credentials()

    # Cliente criado aqui, apos credenciais confirmadas — sem singleton para evitar
    # cache de chave invalida na inicializacao do modulo no Streamlit Cloud
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        timeout=25.0,
        max_retries=1
    )

    models_to_try: list[str] = []

    # 1. Se ja temos um modelo confirmado que respondeu na mesma sessao, coloca no topo!
    if _ACTIVE_WORKING_MODEL:
        models_to_try.append(_ACTIVE_WORKING_MODEL)

    # 2. Modelo configurado explicitamente no secrets (se diferente de auto)
    if configured_model and configured_model.lower() != "auto":
        if configured_model not in models_to_try:
            models_to_try.append(configured_model)

    # 3. Modelos gratuitos ativos como fallback
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
                # Memoriza o modelo que funcionou para as proximas chamadas dos outros agentes!
                _ACTIVE_WORKING_MODEL = model
                return content
        except Exception as e:
            last_error = e
            # Se o modelo falhou e era o memorizado, reseta para testar o proximo
            if _ACTIVE_WORKING_MODEL == model:
                _ACTIVE_WORKING_MODEL = None
            continue

    error_msg = str(last_error) if last_error else "Nenhum conteúdo foi retornado pelo modelo."
    error_lower = error_msg.lower()

    # Deteccao ampliada de erros de autenticacao (cobre variacoes do SDK openai)
    if (
        "401" in error_msg
        or "authentication" in error_lower
        or "api key" in error_lower
        or "invalid" in error_lower
        or "unauthorized" in error_lower
        or "authenticationerror" in error_lower
    ):
        raise RuntimeError("Erro de autenticação: Verifique se sua chave do OpenRouter é válida.")
    elif "429" in error_msg or "rate limit" in error_lower:
        raise RuntimeError("Limite de requisições atingido no OpenRouter. Aguarde alguns instantes e tente novamente.")
    else:
        raise RuntimeError(f"Falha na comunicação com o OpenRouter: {error_msg}")
