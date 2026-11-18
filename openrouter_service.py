"""
Modulo responsavel exclusivamente pela comunicacao com o gateway OpenRouter.
Otimizado para alta performance e confiabilidade:
- Inspecao e validacao rigorosa de finalizacao de resposta (finish_reason)
- Deteccao e recuperacao controlada de respostas truncadas por limite de tokens
- Roteamento inteligente de modelos com selecao preferencial de modelos de alta qualidade para PT-BR
- Isolamento de contexto de sessao para selecao de modelo ativo
- Sanitizacao completa de credenciais e erros sem exposicao de prefixos de chaves
- Timeouts ajustados para failover rapido em caso de congestionamento
"""

import contextvars
from pathlib import Path
from typing import Any, Optional
import requests

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

# Cache em memoria de modelos gratuitos conhecidos
_CACHED_FREE_MODELS: list[str] = []

# ContextVar para isolamento de sessao do modelo ativo (thread-safe e async-safe)
_SESSION_ACTIVE_MODEL: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "_SESSION_ACTIVE_MODEL", default=None
)


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
    A importacao de streamlit e feita de forma lazy para garantir que st.secrets
    ja esteja totalmente inicializado quando esta funcao for chamada em runtime.
    """
    import streamlit as st

    api_key = ""
    configured_model = "auto"

    try:
        api_key = st.secrets.get("OPENROUTER_API_KEY", "").strip()
        configured_model = st.secrets.get("OPENROUTER_MODEL", "auto").strip()
    except Exception:
        pass

    _PLACEHOLDER_VALUES = {"sua_chave_openrouter_aqui", "sua_chave_aqui", "sua_api_key_aqui", ""}

    # Fallback para arquivo local (ambiente de desenvolvimento)
    if not api_key or api_key in _PLACEHOLDER_VALUES:
        file_secrets = _read_secrets_file()
        api_key = file_secrets.get("OPENROUTER_API_KEY", "").strip()
        configured_model = file_secrets.get("OPENROUTER_MODEL", "auto").strip() or "auto"

    if not api_key or api_key in _PLACEHOLDER_VALUES:
        raise ValueError(
            "Chave de API do OpenRouter não encontrada. "
            "No Streamlit Cloud, configure 'OPENROUTER_API_KEY' na seção Secrets do painel do app. "
            "No ambiente local, configure em .streamlit/secrets.toml."
        )

    # Validacao de formato minimo sem expor prefixos ou dados parciais da chave
    if len(api_key) < 20:
        raise ValueError(
            "A chave OPENROUTER_API_KEY parece incompleta ou com tamanho insuficiente. "
            "Verifique se o token foi copiado integralmente no painel de Secrets ou no arquivo secrets.toml."
        )

    return api_key, configured_model


def _fetch_available_free_models() -> list[str]:
    """
    Consulta os modelos gratuitos (:free) disponiveis no catalogo do OpenRouter.
    Prioriza modelos com reconhecida capacidade de contexto, raciocinio estruturado e fluencia em Portugues.
    """
    global _CACHED_FREE_MODELS
    if _CACHED_FREE_MODELS:
        return _CACHED_FREE_MODELS

    # Lista prioritária de modelos com alta qualidade em geração estruturada e suporte a PT-BR
    preferred_order = [
        "meta-llama/llama-3.3-70b-instruct:free",
        "google/gemini-2.0-flash-exp:free",
        "qwen/qwen-2.5-72b-instruct:free",
        "mistralai/mistral-small-24b-instruct-2501:free",
        "deepseek/deepseek-r1:free",
        "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        "nvidia/nemotron-3-ultra-550b-a55b:free",
        "liquid/lfm-3-1.7b:free",
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


def _try_recover_truncated_completion(
    client: Any,
    model: str,
    system_prompt: str,
    user_prompt: str,
    partial_content: str,
    max_tokens: int,
    temperature: float
) -> Optional[str]:
    """
    Tenta uma unica recuperacao controlada de uma resposta interrompida por limite de tokens (finish_reason='length').
    Fornece o trecho anterior como contexto de assistente e instrui a continuacao estrita do ponto onde parou.
    """
    if not partial_content or len(partial_content) < 50:
        return None

    tail_snip = partial_content[-150:].replace("\n", " ")
    continuation_instruction = (
        f"Sua geração anterior foi interrompida no seguinte ponto final:\n"
        f"\"{tail_snip}\"\n\n"
        "INSTRUÇÃO DE RECUPERAÇÃO: Continue o texto EXATAMENTE a partir deste ponto onde parou até concluir "
        "todas as seções e canais obrigatórios pendentes. NÃO repita nada do que já foi escrito acima. "
        "Não inclua saudações ou preâmbulos, retome diretamente o conteúdo faltante."
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": partial_content},
                {"role": "user", "content": continuation_instruction}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )

        if resp and hasattr(resp, "choices") and resp.choices:
            choice = resp.choices[0]
            if hasattr(choice, "message") and choice.message:
                tail = (choice.message.content or "").strip()
                finish_reason = getattr(choice, "finish_reason", None)
                if tail and finish_reason in ("stop", None):
                    return f"{partial_content.rstrip()}\n\n{tail.lstrip()}"
    except Exception:
        pass

    return None


def generate_chat_completion(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1500,
    temperature: float = 0.35
) -> str:
    """
    Executa uma chamada de chat completion ao OpenRouter com mensagens de sistema e usuario.
    - Valida presenca de escolhas (choices), objeto message e conteudo retornado.
    - Analisa finish_reason: detecta respostas truncadas por limite de tokens e tenta recuperacao controlada.
    - Prioriza modelo confirmado na sessao atual com failover inteligente.
    - Tratamento seguro de excecoes com mensagens sanitizadas.
    """
    from openai import OpenAI

    api_key, configured_model = _get_api_credentials()

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        timeout=30.0,
        max_retries=1
    )

    models_to_try: list[str] = []

    # 1. Prioriza o modelo ativo confirmado para a sessao corrente
    active_session_model = _SESSION_ACTIVE_MODEL.get()
    if active_session_model:
        models_to_try.append(active_session_model)

    # 2. Modelo configurado explicitamente no secrets (se diferente de auto)
    if configured_model and configured_model.lower() != "auto":
        if configured_model not in models_to_try:
            models_to_try.append(configured_model)

    # 3. Modelos gratuitos de alta qualidade como pool de fallback
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

            # Validacao defensiva da estrutura da resposta
            if not response or not hasattr(response, "choices") or not response.choices:
                raise ValueError(f"Resposta vazia ou sem choices retornada pelo modelo {model}.")

            choice = response.choices[0]
            if not hasattr(choice, "message") or not choice.message:
                raise ValueError(f"Choice sem objeto message retornado pelo modelo {model}.")

            content = choice.message.content or ""
            content = content.strip()

            if not content:
                raise ValueError(f"Conteúdo vazio gerado pelo modelo {model}.")

            # Inspecao do motivo de encerramento da geracao
            finish_reason = getattr(choice, "finish_reason", None)

            # Se interrompido por limite de tokens, tenta uma recuperacao controlada
            if finish_reason == "length":
                recovered = _try_recover_truncated_completion(
                    client=client,
                    model=model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    partial_content=content,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                if recovered:
                    content = recovered
                else:
                    raise ValueError(
                        f"A geração do modelo {model} foi interrompida pelo limite de tokens (finish_reason='length') "
                        f"e não pôde ser recuperada com integridade."
                    )

            # Sucesso validado
            _SESSION_ACTIVE_MODEL.set(model)
            return content

        except Exception as e:
            last_error = e
            # Se o modelo falhou e era o ativo da sessao, reseta para testar o proximo
            if _SESSION_ACTIVE_MODEL.get() == model:
                _SESSION_ACTIVE_MODEL.set(None)
            continue

    # Tratamento seguro e sanitizado da falha final
    error_msg = str(last_error) if last_error else "Nenhum conteúdo válido foi retornado pelos modelos consultados."
    error_lower = error_msg.lower()

    if (
        "401" in error_msg
        or "authentication" in error_lower
        or "api key" in error_lower
        or "unauthorized" in error_lower
    ):
        raise RuntimeError(
            "Erro de autenticação com o OpenRouter: Verifique se sua credencial OPENROUTER_API_KEY é válida."
        )
    elif "429" in error_msg or "rate limit" in error_lower:
        raise RuntimeError(
            "Limite de requisições temporariamente atingido no gateway OpenRouter. Aguarde alguns instantes."
        )
    elif "timeout" in error_lower or "timed out" in error_lower:
        raise RuntimeError(
            "Tempo limite de resposta esgotado ao consultar o OpenRouter. Tente novamente."
        )
    elif "connection" in error_lower or "failed to connect" in error_lower:
        raise RuntimeError(
            "Falha de conexão com os servidores do OpenRouter. Verifique sua conexão de rede."
        )
    else:
        raise RuntimeError(f"Falha na geração com os modelos do OpenRouter: {error_msg}")
