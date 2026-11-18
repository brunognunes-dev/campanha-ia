"""
Modulo de orquestracao dos agentes de IA generativa.
Cada agente corresponde a uma funcao e uma chamada especializada ao OpenRouter.
"""

from typing import Any, Callable, Optional
from prompts import (
    STRATEGIST_SYSTEM_PROMPT,
    build_strategist_user_prompt,
    COPYWRITER_SYSTEM_PROMPT,
    build_copywriter_user_prompt,
    REVIEWER_SYSTEM_PROMPT,
    build_reviewer_user_prompt,
    IMAGE_DESIGNER_SYSTEM_PROMPT,
    build_image_designer_user_prompt
)
from openrouter_service import generate_chat_completion
from research_service import search_market_trends


def run_strategist_agent(form_data: dict, research_data: Optional[dict] = None) -> str:
    """
    Executa o Agente 1 — Pesquisador de Tendências e Estrategista de Marketing.
    Interpreta os dados brutos e os resultados normalizados de pesquisa externa para gerar o plano estratégico estruturado.
    """
    user_prompt = build_strategist_user_prompt(form_data, research_data=research_data)
    strategy = generate_chat_completion(
        system_prompt=STRATEGIST_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=1600,
        temperature=0.3
    )
    return strategy


def run_copywriter_agent(form_data: dict, strategy: str) -> str:
    """
    Executa o Agente 2 — Copywriter Multicanal.
    Utiliza os dados originais e a estratégia do Agente 1 para gerar textos publicitários
    específicos e adaptados apenas para os canais selecionados.
    """
    user_prompt = build_copywriter_user_prompt(form_data, strategy)
    copy_content = generate_chat_completion(
        system_prompt=COPYWRITER_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=1600,
        temperature=0.5
    )
    return copy_content


def run_reviewer_agent(form_data: dict, strategy: str, copy_content: str) -> str:
    """
    Executa o Agente 3 — Revisor e Otimizador.
    Revisa criticamente os textos em relação à estratégia e aos dados reais,
    sugere palavras-chave e apresenta a versão final consolidada.
    """
    user_prompt = build_reviewer_user_prompt(form_data, strategy, copy_content)
    review_content = generate_chat_completion(
        system_prompt=REVIEWER_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=1800,
        temperature=0.3
    )
    return review_content


def run_image_designer_agent(form_data: dict, strategy: str, review_and_final: str) -> str:
    """
    Executa o Agente 4 — Designer de Prompts de Imagem.
    Gera especificações de direção visual e prompts textuais para geradores de imagens (Midjourney, DALL-E, etc.)
    com base no briefing, na estratégia do Agente 1 e nos textos finais revisados do Agente 3.
    """
    user_prompt = build_image_designer_user_prompt(form_data, strategy, review_and_final)
    image_prompts = generate_chat_completion(
        system_prompt=IMAGE_DESIGNER_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=1800,
        temperature=0.4
    )
    return image_prompts


def generate_full_campaign(
    form_data: dict,
    progress_callback: Optional[Callable[..., None]] = None
) -> dict:
    """
    Orquestra a sequencia do pipeline utilizando o StateGraph do LangGraph:
    0. Pesquisa Externa de Tendências (Tavily Search API)
    1. Pesquisador & Estrategista -> 2. Copywriter -> 3. Revisor & SEO -> 4. Designer de Prompts de Imagem -> 5. Guardrails
    Retorna o dicionario consolidado com todas as etapas intermediarias e finais.
    Notifica o callback com eventos reais de início e conclusão de cada etapa,
    preservando resultados parciais em caso de falha nas etapas subsequentes.
    """
    from graph_orchestrator import run_campaign_graph
    return run_campaign_graph(form_data, progress_callback=progress_callback)


def build_campaign_reports(campaign_data: dict) -> tuple[str, str]:
    """
    Gera o relatório consolidado da campanha nos formatos Markdown (.md) e Texto Puro (.txt).
    Inclui identificação, briefing, fontes reais de pesquisa/tendências, estratégia fundamentada,
    textos de cada canal, revisão crítica, direção visual e aviso legal.
    """
    import datetime

    form = campaign_data.get("form_data", {})
    research = campaign_data.get("research_data")
    strategy = campaign_data.get("strategy", "")
    copy = campaign_data.get("preliminary_copy", "")
    review = campaign_data.get("review_and_final", "")
    image_prompts = campaign_data.get("image_prompts", "")
    now_str = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M")
    product_name = form.get("product_name", "Campanha IA")

    # Formatacao da secao de pesquisa para o relatorio Markdown
    md_research_lines = [
        "## FONTES DE PESQUISA E TENDÊNCIAS DE MERCADO (TAVILY SEARCH API)"
    ]
    if research and isinstance(research, dict):
        if research.get("success") and research.get("results"):
            query_str = research.get("query", "")
            md_research_lines.append(f"- **Consulta de Busca Realizada:** `{query_str}`")
            md_research_lines.append(f"- **Total de Fontes Reais Consultadas:** {len(research['results'])}")
            md_research_lines.append("")
            for idx, src in enumerate(research["results"], 1):
                src_title = src.get("title", f"Fonte {idx}")
                src_url = src.get("url", "")
                src_date = src.get("published_date")
                date_txt = f" (Publicado em: {src_date})" if src_date else ""
                md_research_lines.append(f"{idx}. [{src_title}]({src_url}){date_txt}")
        elif not research.get("success"):
            err_msg = research.get("error") or "Não informada"
            md_research_lines.append(
                f"*Pesquisa de mercado externa esteve indisponível durante a geração: {err_msg}*\n"
                f"*A estratégia foi desenvolvida fundamentando-se estritamente nas premissas e dados do briefing.*"
            )
        else:
            md_research_lines.append("*Nenhuma fonte externa consultada para esta campanha.*")
    else:
        md_research_lines.append("*Pesquisa externa de mercado não registrada para esta execução.*")

    # 1. Relatório em Markdown (.md)
    md_lines = [
        f"# RELATÓRIO DE CAMPANHA DE MARKETING — {product_name.upper()}",
        f"*Data de geração: {now_str}*",
        "",
        "---",
        "## 1. DADOS DE CONTEXTO E BRIEFING",
        f"- **Produto/Serviço:** {form.get('product_name', '')}",
        f"- **Descrição:** {form.get('product_description', '')}",
        f"- **Público-Alvo:** {form.get('target_audience', '')}",
        f"- **Objetivo da Campanha:** {form.get('objective', '')}",
        f"- **Tom de Comunicação:** {form.get('tone', '')}",
        f"- **Diferenciais Informados:** {form.get('differentials', 'Nenhum diferencial adicional informado.')}",
        f"- **Chamada para Ação (CTA):** {form.get('cta', 'Não especificada.')}",
        f"- **Canais Selecionados:** {', '.join(form.get('channels', []))}",
        "",
        "---",
    ]
    md_lines.extend(md_research_lines)
    md_lines.extend([
        "",
        "---",
        "## 2. ESTRATÉGIA DE MARKETING (AGENTE 1 — ESTRATEGISTA)",
        strategy,
        "",
        "---",
        "## 3. TEXTOS PRELIMINARES POR CANAL (AGENTE 2 — COPYWRITER)",
        copy,
        "",
        "---",
        "## 4. REVISÃO CRÍTICA, SEO E VERSÃO FINAL (AGENTE 3 — REVISOR)",
        review,
        "",
    ])

    if image_prompts:
        md_lines.extend([
            "---",
            "## 5. DIREÇÃO VISUAL E PROMPTS DE IMAGEM (AGENTE 4 — DESIGNER DE PROMPTS)",
            image_prompts,
            "",
            "---",
            "## 6. AVISO ÉTICO E LEGAL",
        ])
    else:
        md_lines.extend([
            "---",
            "## 5. AVISO ÉTICO E LEGAL",
        ])

    md_lines.extend([
        "> **AVISO IMPORTANTE:** Os textos, análises e especificações visuais contidos neste relatório foram elaborados por sistemas de Inteligência Artificial Generativa. "
        "A análise de SEO possui caráter estritamente orientativo e não garante posicionamento em buscas ou resultados de vendas. "
        "Todos os conteúdos devem passar por criteriosa revisão humana e validação antes de veiculação comercial."
    ])
    report_md = "\n".join(md_lines)

    # Formatacao da secao de pesquisa para o relatorio Texto Puro (.txt)
    txt_research_lines = [
        "-" * 70,
        "[FONTES DE PESQUISA E TENDÊNCIAS DE MERCADO (TAVILY SEARCH API)]",
        "-" * 70,
    ]
    if research and isinstance(research, dict):
        if research.get("success") and research.get("results"):
            query_str = research.get("query", "")
            txt_research_lines.append(f"Consulta de Busca: {query_str}")
            txt_research_lines.append(f"Total de Fontes Reais: {len(research['results'])}")
            txt_research_lines.append("")
            for idx, src in enumerate(research["results"], 1):
                src_title = src.get("title", f"Fonte {idx}")
                src_url = src.get("url", "")
                src_date = src.get("published_date")
                date_txt = f" [Data: {src_date}]" if src_date else ""
                txt_research_lines.append(f"{idx}. {src_title}: {src_url}{date_txt}")
        elif not research.get("success"):
            err_msg = research.get("error") or "Não informada"
            txt_research_lines.append(f"Pesquisa externa esteve indisponível durante a geração: {err_msg}")
            txt_research_lines.append("A estratégia foi elaborada com base nas informações do briefing.")
        else:
            txt_research_lines.append("Nenhuma fonte externa consultada para esta campanha.")
    else:
        txt_research_lines.append("Pesquisa externa de mercado não registrada para esta execução.")

    # 2. Relatório em Texto Puro (.txt)
    txt_lines = [
        "=" * 70,
        f"RELATÓRIO DE CAMPANHA DE MARKETING — {product_name.upper()}",
        f"Data de geração: {now_str}",
        "=" * 70,
        "",
        "[1. DADOS DE CONTEXTO E BRIEFING]",
        f"Produto/Serviço: {form.get('product_name', '')}",
        f"Descrição: {form.get('product_description', '')}",
        f"Público-Alvo: {form.get('target_audience', '')}",
        f"Objetivo da Campanha: {form.get('objective', '')}",
        f"Tom de Comunicação: {form.get('tone', '')}",
        f"Diferenciais: {form.get('differentials', 'Nenhum')}",
        f"CTA Desejada: {form.get('cta', 'Não especificada')}",
        f"Canais: {', '.join(form.get('channels', []))}",
        "",
    ]
    txt_lines.extend(txt_research_lines)
    txt_lines.extend([
        "",
        "-" * 70,
        "[2. ESTRATÉGIA DE MARKETING (AGENTE 1 — ESTRATEGISTA)]",
        "-" * 70,
        strategy,
        "",
        "-" * 70,
        "[3. TEXTOS PRELIMINARES POR CANAL (AGENTE 2 — COPYWRITER)]",
        "-" * 70,
        copy,
        "",
        "-" * 70,
        "[4. REVISÃO CRÍTICA, SEO E VERSÃO FINAL (AGENTE 3 — REVISOR)]",
        "-" * 70,
        review,
        "",
    ])

    if image_prompts:
        txt_lines.extend([
            "-" * 70,
            "[5. DIREÇÃO VISUAL E PROMPTS DE IMAGEM (AGENTE 4 — DESIGNER DE PROMPTS)]",
            "-" * 70,
            image_prompts,
            "",
            "=" * 70,
            "[6. AVISO ÉTICO E LEGAL]",
            "=" * 70,
        ])
    else:
        txt_lines.extend([
            "=" * 70,
            "[5. AVISO ÉTICO E LEGAL]",
            "=" * 70,
        ])

    txt_lines.extend([
        "AVISO IMPORTANTE: Os textos, análises e sugestões visuais contidos neste relatório foram",
        "elaborados por sistemas de Inteligência Artificial Generativa.",
        "A análise de SEO possui caráter estritamente orientativo e não garante",
        "posicionamento em buscas ou resultados comerciais.",
        "Todos os conteúdos devem passar por criteriosa revisão humana antes",
        "de qualquer veiculação comercial.",
        "=" * 70
    ])
    report_txt = "\n".join(txt_lines)

    return report_md, report_txt
