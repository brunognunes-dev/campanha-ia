"""
Modulo de orquestracao multiagente via LangGraph para o MarketFlow AI 2.0.

Implementa StateGraph deterministico com estado compartilhado entre os agentes:
1. pesquisador_tendencias: Pesquisa de mercado (Tavily) + Agente 1 (Estrategista)
2. copywriter: Agente 2 (Redação publicitária multicanal)
3. especialista_seo: Agente 3 (Revisão crítica e otimização SEO)
4. designer_prompts_imagem: Agente 4 (Direção visual e prompts generativos)
5. guardrails: Validação determinística de compliance e integridade

Preserva o modo automatico do OpenRouter, callbacks de progresso para o Streamlit,
validacao estrutural intermediaria entre nos e tratamento rigoroso de excecoes.
"""

import contextvars
from typing import Any, Callable, Optional, TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig

import agents
from guardrails import validate_campaign_guardrails
from output_validation import (
    validate_strategist_output,
    validate_copywriter_output,
    validate_reviewer_output,
    validate_image_designer_output
)

# ContextVar para propagacao robusta do callback de progresso mesmo em execucoes assincronas
_CURRENT_PROGRESS_CALLBACK: contextvars.ContextVar[Optional[Callable]] = contextvars.ContextVar(
    "_CURRENT_PROGRESS_CALLBACK", default=None
)


class CampaignState(TypedDict, total=False):
    """Estado estruturado compartilhado entre os nos do LangGraph."""
    form_data: dict[str, Any]
    research_data: Optional[dict[str, Any]]
    strategy: str
    preliminary_copy: str
    review_and_final: str
    image_prompts: str
    guardrails_result: Optional[dict[str, Any]]
    error: Optional[str]


def _notify_progress(
    config: Optional[RunnableConfig],
    stage: str,
    status: str,
    msg: str,
    result: Optional[Any] = None
) -> None:
    """Dispara eventos de progresso de forma compativel para o callback da interface."""
    callback = None
    if config and isinstance(config, dict):
        callback = config.get("configurable", {}).get("progress_callback")
    if not callback:
        callback = _CURRENT_PROGRESS_CALLBACK.get()

    if not callback:
        return

    try:
        callback(stage, status, msg, result)
    except TypeError:
        try:
            callback(stage, status, msg)
        except TypeError:
            callback(msg, 1)


# ==============================================================================
# NOS DO GRAFO LANGGRAPH
# ==============================================================================

def pesquisador_tendencias_node(
    state: CampaignState,
    config: Optional[RunnableConfig] = None
) -> dict[str, Any]:
    """
    No 1: Pesquisador de Tendencias e Estrategista de Marketing.
    Executa a pesquisa externa de mercado via Tavily ANTES da chamada a LLM,
    e em seguida invoca o Agente 1 para elaborar a estrategia fundamentada.
    Valida a completude estrutural antes de prosseguir.
    """
    form_data = state.get("form_data", {})

    # 1. Pesquisa externa de mercado
    _notify_progress(config, "research", "running", "Consultando tendências de mercado em tempo real via Tavily Search API...")
    try:
        research_data = agents.search_market_trends(
            product_name=form_data.get("product_name", ""),
            product_description=form_data.get("product_description", ""),
            target_audience=form_data.get("target_audience", ""),
            max_results=5
        )
    except Exception as e:
        research_data = {
            "success": False,
            "query": "",
            "total_results": 0,
            "results": [],
            "error": str(e),
            "cached": False
        }

    if research_data.get("success"):
        total_src = research_data.get("total_results", len(research_data.get("results", [])))
        _notify_progress(
            config,
            "research",
            "completed",
            f"Pesquisa concluída com sucesso: {total_src} fontes reais consultadas.",
            research_data
        )
    else:
        err_msg = research_data.get("error", "Indisponível no momento")
        _notify_progress(
            config,
            "research",
            "completed",
            f"Pesquisa externa indisponível ({err_msg}). Prosseguindo com o briefing.",
            research_data
        )

    # 2. Agente 1 (Estrategista com dados de mercado)
    _notify_progress(config, "strategist", "running", "Agente 1 (Pesquisador & Estrategista) elaborando o plano fundamentado...")
    strategy = agents.run_strategist_agent(form_data, research_data=research_data)

    val = validate_strategist_output(strategy)
    if not val.is_valid and val.is_truncated:
        _notify_progress(config, "strategist", "completed", "Estratégia concluída (com alerta de extensão).", strategy)
    else:
        _notify_progress(config, "strategist", "completed", "Estratégia de marketing fundamentada concluída.", strategy)

    return {
        "research_data": research_data,
        "strategy": strategy
    }


def copywriter_node(
    state: CampaignState,
    config: Optional[RunnableConfig] = None
) -> dict[str, Any]:
    """
    No 2: Copywriter Multicanal.
    Gera textos publicitarios persuasivos e adaptados para os canais solicitados,
    utilizando a estrategia fundamentada produzida no No 1.
    """
    form_data = state.get("form_data", {})
    strategy = state.get("strategy", "")
    channels = form_data.get("channels", [])

    _notify_progress(config, "copywriter", "running", "Agente 2 (Copywriter) redigindo os textos para os canais selecionados...")
    copy_content = agents.run_copywriter_agent(form_data, strategy)

    val = validate_copywriter_output(copy_content, channels)
    if not val.is_valid and val.missing_channels:
        _notify_progress(
            config,
            "copywriter",
            "completed",
            f"Textos gerados (atenção: canais {', '.join(val.missing_channels)} requerem revisão).",
            copy_content
        )
    else:
        _notify_progress(config, "copywriter", "completed", "Textos dos canais criados com sucesso.", copy_content)

    return {
        "preliminary_copy": copy_content
    }


def especialista_seo_node(
    state: CampaignState,
    config: Optional[RunnableConfig] = None
) -> dict[str, Any]:
    """
    No 3: Especialista em SEO e Revisor.
    Revisa criticamente a qualidade dos textos em relacao a estrategia e ao briefing,
    sugere palavras-chave orientativas e consolida a versao final.
    """
    form_data = state.get("form_data", {})
    strategy = state.get("strategy", "")
    copy_content = state.get("preliminary_copy", "")
    channels = form_data.get("channels", [])

    _notify_progress(config, "reviewer", "running", "Agente 3 (Revisor & SEO) refinando os textos e otimizando a versão final...")
    review_content = agents.run_reviewer_agent(form_data, strategy, copy_content)

    val = validate_reviewer_output(review_content, channels)
    _notify_progress(config, "reviewer", "completed", "Revisão e versão final concluídas.", review_content)

    return {
        "review_and_final": review_content
    }


def designer_prompts_imagem_node(
    state: CampaignState,
    config: Optional[RunnableConfig] = None
) -> dict[str, Any]:
    """
    No 4: Designer de Prompts de Imagem.
    Gera direcao de arte visual e especificacoes tecnicas de prompts textuais
    para geradores de imagem (Midjourney, DALL-E, Flux) por canal de divulgacao.
    """
    form_data = state.get("form_data", {})
    strategy = state.get("strategy", "")
    review_content = state.get("review_and_final", "")

    _notify_progress(config, "image_designer", "running", "Agente 4 (Designer Visual) elaborando prompts de imagem publicitária...")
    image_prompts = agents.run_image_designer_agent(form_data, strategy, review_content)

    _notify_progress(config, "image_designer", "completed", "Prompts e direção visual concluídos com sucesso.", image_prompts)

    return {
        "image_prompts": image_prompts
    }


def guardrails_node(
    state: CampaignState,
    config: Optional[RunnableConfig] = None
) -> dict[str, Any]:
    """
    No 5: Guardrails Deterministicos e Finalizacao.
    Executa a camada deterministica de compliance etico e consistencia sobre todo o conteudo gerado.
    """
    campaign_data = {
        "form_data": state.get("form_data", {}),
        "research_data": state.get("research_data"),
        "strategy": state.get("strategy", ""),
        "preliminary_copy": state.get("preliminary_copy", ""),
        "review_and_final": state.get("review_and_final", ""),
        "image_prompts": state.get("image_prompts", "")
    }

    guardrails_res = validate_campaign_guardrails(campaign_data=campaign_data)

    if guardrails_res.get("is_blocked"):
        _notify_progress(
            config,
            "ready",
            "completed",
            "Campanha gerada (bloqueada para envio automático por inconformidade crítica)."
        )
    else:
        _notify_progress(config, "ready", "completed", "Campanha pronta para uso e exportação.")

    return {
        "guardrails_result": guardrails_res
    }


# ==============================================================================
# CONSTRUCAO DO GRAFO LANGGRAPH
# ==============================================================================

def build_campaign_graph() -> Any:
    """
    Constroi e compila o StateGraph sequencial do MarketFlow AI 2.0.
    Sequencia estrita de nos:
    START -> pesquisador_tendencias -> copywriter -> especialista_seo -> designer_prompts_imagem -> guardrails -> END
    """
    builder = StateGraph(CampaignState)

    # 1. Adicao dos nos especializados
    builder.add_node("pesquisador_tendencias", pesquisador_tendencias_node)
    builder.add_node("copywriter", copywriter_node)
    builder.add_node("especialista_seo", especialista_seo_node)
    builder.add_node("designer_prompts_imagem", designer_prompts_imagem_node)
    builder.add_node("guardrails", guardrails_node)

    # 2. Definicao da sequencia linear deterministica
    builder.add_edge(START, "pesquisador_tendencias")
    builder.add_edge("pesquisador_tendencias", "copywriter")
    builder.add_edge("copywriter", "especialista_seo")
    builder.add_edge("especialista_seo", "designer_prompts_imagem")
    builder.add_edge("designer_prompts_imagem", "guardrails")
    builder.add_edge("guardrails", END)

    return builder.compile()


# Instancia compilada singleton do grafo
_COMPILED_GRAPH = None


def get_compiled_campaign_graph() -> Any:
    """Retorna o grafo compilado com cache singleton para maxima performance."""
    global _COMPILED_GRAPH
    if _COMPILED_GRAPH is None:
        _COMPILED_GRAPH = build_campaign_graph()
    return _COMPILED_GRAPH


def run_campaign_graph(
    form_data: dict[str, Any],
    progress_callback: Optional[Callable[..., None]] = None
) -> dict[str, Any]:
    """
    Executa o grafo LangGraph de orquestracao multiagente.
    Preserva a assinatura, compatibilidade e dicionario de retorno para a aplicacao.
    """
    token = _CURRENT_PROGRESS_CALLBACK.set(progress_callback)
    try:
        graph = get_compiled_campaign_graph()

        initial_state: CampaignState = {
            "form_data": form_data,
            "research_data": None,
            "strategy": "",
            "preliminary_copy": "",
            "review_and_final": "",
            "image_prompts": "",
            "guardrails_result": None,
            "error": None
        }

        config: RunnableConfig = {
            "configurable": {
                "progress_callback": progress_callback
            }
        }

        final_state = graph.invoke(initial_state, config=config)

        return {
            "form_data": final_state.get("form_data", form_data),
            "research_data": final_state.get("research_data"),
            "strategy": final_state.get("strategy", ""),
            "preliminary_copy": final_state.get("preliminary_copy", ""),
            "review_and_final": final_state.get("review_and_final", ""),
            "image_prompts": final_state.get("image_prompts", ""),
            "guardrails_result": final_state.get("guardrails_result")
        }
    finally:
        _CURRENT_PROGRESS_CALLBACK.reset(token)
