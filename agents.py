"""
Modulo de orquestracao dos agentes de IA generativa.
Cada agente corresponde a uma funcao e uma chamada especializada ao OpenRouter.
"""

from typing import Callable, Optional
from prompts import (
    STRATEGIST_SYSTEM_PROMPT,
    build_strategist_user_prompt,
    COPYWRITER_SYSTEM_PROMPT,
    build_copywriter_user_prompt,
    REVIEWER_SYSTEM_PROMPT,
    build_reviewer_user_prompt
)
from openrouter_service import generate_chat_completion


def run_strategist_agent(form_data: dict) -> str:
    """
    Executa o Agente 1 — Estrategista de Marketing.
    Interpreta os dados brutos e gera o plano estrategico estruturado.
    """
    user_prompt = build_strategist_user_prompt(form_data)
    strategy = generate_chat_completion(
        system_prompt=STRATEGIST_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=1400,
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


def generate_full_campaign(
    form_data: dict,
    progress_callback: Optional[Callable[..., None]] = None
) -> dict:
    """
    Orquestra a sequencia completa dos 3 agentes:
    1. Estrategista -> 2. Copywriter -> 3. Revisor
    Retorna o dicionario consolidado com todas as etapas intermediarias e finais.
    Notifica o callback com eventos reais de início e conclusão de cada agente.
    """
    def notify(stage: str, status: str, msg: str):
        if progress_callback:
            try:
                progress_callback(stage, status, msg)
            except TypeError:
                progress_callback(msg, 1)

    # Etapa 1: Estrategista
    notify("strategist", "running", "Agente 1 (Estrategista) elaborando o plano de marketing...")
    strategy = run_strategist_agent(form_data)
    notify("strategist", "completed", "Estratégia de marketing concluída.")

    # Etapa 2: Copywriter
    notify("copywriter", "running", "Agente 2 (Copywriter) redigindo os textos para os canais selecionados...")
    copy_content = run_copywriter_agent(form_data, strategy)
    notify("copywriter", "completed", "Textos dos canais criados com sucesso.")

    # Etapa 3: Revisor e Otimizador
    notify("reviewer", "running", "Agente 3 (Revisor) refinando os textos e otimizando a versão final...")
    review_content = run_reviewer_agent(form_data, strategy, copy_content)
    notify("reviewer", "completed", "Revisão e versão final concluídas.")

    notify("ready", "completed", "Campanha pronta para uso e exportação.")

    return {
        "form_data": form_data,
        "strategy": strategy,
        "preliminary_copy": copy_content,
        "review_and_final": review_content
    }


def build_campaign_reports(campaign_data: dict) -> tuple[str, str]:
    """
    Gera o relatório consolidado da campanha nos formatos Markdown (.md) e Texto Puro (.txt).
    Inclui identificação, briefing, estratégia, textos de cada canal, revisão e aviso legal.
    """
    import datetime

    form = campaign_data.get("form_data", {})
    strategy = campaign_data.get("strategy", "")
    copy = campaign_data.get("preliminary_copy", "")
    review = campaign_data.get("review_and_final", "")
    now_str = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M")
    product_name = form.get("product_name", "Campanha IA")

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
        "---",
        "## 5. AVISO ÉTICO E LEGAL",
        "> **AVISO IMPORTANTE:** Os textos e análises contidos neste relatório foram elaborados por sistemas de Inteligência Artificial Generativa. "
        "A análise de SEO possui caráter estritamente orientativo e não garante posicionamento em buscas ou resultados de vendas. "
        "Todos os conteúdos devem passar por criteriosa revisão humana e validação antes de veiculação comercial."
    ]
    report_md = "\n".join(md_lines)

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
        "=" * 70,
        "[5. AVISO ÉTICO E LEGAL]",
        "=" * 70,
        "AVISO IMPORTANTE: Os textos e análises contidos neste relatório foram",
        "elaborados por sistemas de Inteligência Artificial Generativa.",
        "A análise de SEO possui caráter estritamente orientativo e não garante",
        "posicionamento em buscas ou resultados comerciais.",
        "Todos os conteúdos devem passar por criteriosa revisão humana antes",
        "de qualquer veiculação comercial.",
        "=" * 70
    ]
    report_txt = "\n".join(txt_lines)

    return report_md, report_txt
