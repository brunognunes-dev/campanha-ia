"""
Modulo responsavel pelo servico de pesquisa externa de tendencias de mercado
utilizando o SDK oficial Tavily Search API (tavily-python).

Diretrizes:
- Leitura segura de credenciais (TAVILY_API_KEY).
- Cache em memoria para evitar buscas duplicadas por reexecucoes do Streamlit.
- Normalizacao rigorosa de resultados preservando titulos e URLs reais.
- Higienizacao de dados externos nao confiaveis contra prompt injection indireto.
- Tratamento defensivo de timeouts, autenticacao invalida e respostas vazias.
"""

from hashlib import sha256
from pathlib import Path
import re
from typing import Any, Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

# Cache em memoria indexado pelo hash da consulta para evitar buscas redundantes
_SEARCH_CACHE: dict[str, dict[str, Any]] = {}

# Padroes conhecidos de prompt injection indireto presentes em conteudos web
_INJECTION_PATTERNS = [
    re.compile(r"(?:ignore|disregard|forget)\s+(?:all\s+)?(?:previous\s+)?instructions", re.IGNORECASE),
    re.compile(r"(?:desconsidere|ignore|esqueça)\s+(?:todas\s+as\s+)?instruções\s+anteriores", re.IGNORECASE),
    re.compile(r"###\s*(?:system|user|assistant)\s*:", re.IGNORECASE),
    re.compile(r"\[(?:system|instruction|admin)\]", re.IGNORECASE),
]


def _read_secrets_file() -> dict[str, str]:
    """Leitura direta do arquivo secrets.toml como fallback (ambiente local)."""
    secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        return {}

    if tomllib is not None:
        try:
            with open(secrets_path, "rb") as f:
                raw_data = tomllib.load(f)
                return {k: str(v).strip() for k, v in raw_data.items() if isinstance(v, (str, int, float))}
        except Exception:
            return {}

    data: dict[str, str] = {}
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


def get_tavily_api_key() -> str:
    """
    Recupera a chave da Tavily Search API de forma segura.
    Prioriza st.secrets (Streamlit Cloud/App) e possui fallback para secrets.toml local.
    Nunca registra ou exibe o valor da credencial em logs.
    """
    api_key = ""

    # Tentativa 1: st.secrets quando no contexto do Streamlit
    try:
        import streamlit as st
        api_key = str(st.secrets.get("TAVILY_API_KEY", "") or "").strip()
    except Exception:
        pass

    # Tentativa 2: fallback seguro para o arquivo local
    placeholder_values = {"sua_chave_tavily_aqui", "sua_chave_aqui", ""}
    if not api_key or api_key in placeholder_values:
        file_secrets = _read_secrets_file()
        api_key = str(file_secrets.get("TAVILY_API_KEY", "") or "").strip()

    if not api_key or api_key in placeholder_values:
        raise ValueError(
            "Chave de API da Tavily não configurada. "
            "Configure 'TAVILY_API_KEY' na seção de segredos do Streamlit (.streamlit/secrets.toml)."
        )

    return api_key


def build_search_query(
    product_name: str,
    product_description: str,
    target_audience: str
) -> str:
    """
    Constroi uma consulta de pesquisa objetiva focada em tendencias de mercado,
    dores do publico e insights comerciais sem redundancias.
    """
    clean_product = re.sub(r"[^\w\s-]", "", str(product_name or "").strip())
    clean_audience = re.sub(r"[^\w\s-]", "", str(target_audience or "").strip())

    # Seleciona as primeiras palavras do publico para manter a query concisa e relevante
    audience_keywords = " ".join(clean_audience.split()[:4])

    if clean_product and audience_keywords:
        query = f"tendências mercado {clean_product} {audience_keywords}"
    elif clean_product:
        query = f"tendências mercado inovação {clean_product}"
    else:
        query = "tendências marketing digital comportamento consumidor"

    # Limita o comprimento maximo da query para respeitar os padroes de busca
    return query[:120].strip()


def sanitize_web_content(content: str) -> str:
    """
    Higieniza textos extraidos de paginas externas (dados nao confiaveis):
    - Neutraliza instrucoes de prompt injection indireto.
    - Remove delimitadores que possam tentar alterar diretrizes de agentes.
    - Normaliza espacos e quebras de linha excessivas.
    """
    if not content:
        return ""

    sanitized = str(content)

    # 1. Neutraliza tentativas de prompt injection comuns
    for pattern in _INJECTION_PATTERNS:
        sanitized = pattern.sub("[TRECHO_REMOVIDO_POR_SEGURANCA]", sanitized)

    # 2. Remove blocos de comandos em markdown ou delimitadores de sistema
    sanitized = sanitized.replace("```", "'''")

    # 3. Limpa espacos em branco repetitivos
    sanitized = re.sub(r"\s+", " ", sanitized)

    return sanitized.strip()


def normalize_search_results(raw_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Normaliza e valida deterministicamente a lista de resultados retornada pela API:
    - Exige URL real e valida (iniciando com http:// ou https://).
    - Exige presenca de titulo e conteudo.
    - Preserva URLs e titulos reais sem invencoes.
    - Registra published_date somente quando fornecida.
    - Descarta resultados incompletos ou invalidos.
    """
    normalized: list[dict[str, Any]] = []

    if not isinstance(raw_results, list):
        return normalized

    for item in raw_results:
        if not isinstance(item, dict):
            continue

        raw_url = str(item.get("url") or "").strip()
        raw_title = str(item.get("title") or "").strip()
        raw_content = str(item.get("content") or "").strip()

        # Validacao essencial de integridade
        if not raw_url.startswith(("http://", "https://")):
            continue
        if not raw_title or not raw_content:
            continue

        # Data de publicacao: apenas se genuinamente fornecida
        raw_date = item.get("published_date")
        clean_date = str(raw_date).strip() if raw_date else None
        if clean_date in ("", "None", "null", "undefined"):
            clean_date = None

        # Score de relevancia retornado pela API (se presente)
        score = float(item.get("score") or 0.0)

        # Higienizacao de seguranca do conteudo
        safe_content = sanitize_web_content(raw_content)

        normalized.append({
            "title": raw_title,
            "url": raw_url,
            "content": safe_content,
            "published_date": clean_date,
            "score": round(score, 4)
        })

    return normalized


def search_market_trends(
    product_name: str,
    product_description: str,
    target_audience: str,
    max_results: int = 5,
    force_refresh: bool = False
) -> dict[str, Any]:
    """
    Executa a pesquisa de tendencias de mercado via Tavily Search API.

    Parametros:
    - product_name: Nome do produto/servico.
    - product_description: Descricao da oferta.
    - target_audience: Publico-alvo desejado.
    - max_results: Limite de resultados (padrao 5).
    - force_refresh: Se True, ignora o cache em memoria.

    Retorno estruturado:
    {
        "success": bool,
        "query": str,
        "total_results": int,
        "results": list[dict],
        "error": Optional[str],
        "cached": bool
    }
    """
    query = build_search_query(product_name, product_description, target_audience)

    # 1. Verificacao de Cache (evita consumo de creditos em reruns do Streamlit)
    cache_key = sha256(f"{query}:{max_results}".encode("utf-8")).hexdigest()
    if not force_refresh and cache_key in _SEARCH_CACHE:
        cached_data = dict(_SEARCH_CACHE[cache_key])
        cached_data["cached"] = True
        return cached_data

    # 2. Obtenção Segura da Chave
    try:
        api_key = get_tavily_api_key()
    except ValueError as e:
        return {
            "success": False,
            "query": query,
            "total_results": 0,
            "results": [],
            "error": str(e),
            "cached": False
        }

    # 3. Execucao via SDK oficial tavily-python
    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)

        response = client.search(
            query=query,
            search_depth="basic",
            max_results=min(max_results, 5),
            include_answer=False,
            include_raw_content=False
        )

        raw_results = response.get("results", []) if isinstance(response, dict) else []
        normalized_results = normalize_search_results(raw_results)

        result_payload = {
            "success": True,
            "query": query,
            "total_results": len(normalized_results),
            "results": normalized_results,
            "error": None,
            "cached": False
        }

        # Armazena no cache para chamadas subsequentes com a mesma consulta
        _SEARCH_CACHE[cache_key] = result_payload
        return result_payload

    except Exception as e:
        error_str = str(e)
        error_lower = error_str.lower()

        # Deteccao amigavel e segura de erros sem vazar credenciais
        if "401" in error_str or "unauthorized" in error_lower or "api key" in error_lower:
            friendly_error = "Falha de autenticação na Tavily Search API. Verifique se TAVILY_API_KEY é válida."
        elif "429" in error_str or "rate limit" in error_lower:
            friendly_error = "Limite de requisições atingido na Tavily Search API. Aguarde alguns instantes."
        elif "timeout" in error_lower or "timed out" in error_lower:
            friendly_error = "Tempo limite esgotado ao consultar a Tavily Search API. Tente novamente."
        elif "connection" in error_lower:
            friendly_error = "Falha de conexão com os servidores da Tavily Search API."
        else:
            friendly_error = f"Erro na consulta à Tavily Search API: {type(e).__name__}"

        return {
            "success": False,
            "query": query,
            "total_results": 0,
            "results": [],
            "error": friendly_error,
            "cached": False
        }
