"""
Modulo de Guardrails Independentes do MarketFlow AI.
Realiza verificacoes deterministicas de estrutura, consistencia de briefing,
cobertura de canais solicitados e deteccao contextual de alegacoes comerciais
nao fundamentadas ou potencialmente enganosas.

Diretrizes:
- Verificacoes 100% deterministicas (sem dependencia de chamada adicional a LLM).
- Nao bloqueia conteudos legitimos apenas por palavras isoladas.
- Valida amparo nos dados do briefing informado pelo usuario.
- A validacao automatica e orientativa e nao se afirma infalivel.
"""

import re
from typing import Any, Optional


# Disclaimer oficial sobre a natureza orientativa dos guardrails
GUARDRAILS_DISCLAIMER = (
    "Aviso Institucional dos Guardrails: Esta validação é automatizada, "
    "determinística e de caráter estritamente orientativo. O sistema não é infalível "
    "e não substitui a criteriosa revisão humana, ética e jurídica dos conteúdos antes "
    "de qualquer veiculação comercial ou publicação."
)

# Padroes contextuais de severidade CRITICA (alegacoes fraudulentas ou promessas enganosas sem risco)
# Nao utiliza palavras isoladas; exige combinacoes contextuais categóricas.
CRITICAL_UNGROUNDED_PATTERNS = [
    (
        r"(?:retorno|lucro|ganho|rendimento)\s+(?:financeiro\s+)?(?:garantido|100%|certo|sem\s+(?:qualquer\s+)?risco)",
        "Promessa de retorno ou lucro garantido sem risco (vedado pelo Código de Defesa do Consumidor e CONAR)."
    ),
    (
        r"(?:fique|ficar|torne-se)\s+(?:rico|milion[áa]rio)\s+(?:da\s+noite\s+para\s+o\s+dia|r[áa]pido|em\s+\d+\s+dias|sem\s+esfor[çc]o)",
        "Promessa categórica de enriquecimento rápido ou fácil sem esforço."
    ),
    (
        r"(?:cura|elimina|acaba\s+com)\s+(?:[\w\s]{0,25})?(?:definitivamente|100%|qualquer(?:\s+tipo\s+de)?|todas\s+as)\s+(?:[\w\s]{0,25})?(?:doen[çc]as?|enfermidades?|c[âa]ncer)",
        "Alegação de cura médica milagrosa ou eliminação categórica de enfermidades."
    ),
    (
        r"(?:ganhe|fature|receba)\s+(?:r\$\s*[\d\.\,]+|\d+\s*mil)\s+(?:sem\s+(?:fazer\s+nada|trabalhar|sair\s+do\s+sof[áa]))",
        "Promessa de ganhos financeiros sem contraprestação ou esforço real."
    ),
    (
        r"(?:f[óo]rmula|m[ée]todo|segredo)\s+(?:100%\s+)?(?:infal[íi]vel|m[áa]gic[oa]|milagros[oa])",
        "Alegação de infalibilidade absoluta ou método milagroso."
    ),
]

# Padroes contextuais de severidade WARNING (pontos de atencao que exigem verificacao humana, sem bloqueio automatico)
WARNING_SUSPICIOUS_PATTERNS = [
    (
        r"(?:desconto|off)\s+de\s+(?:[6-9]\d|100)%",
        "Desconto elevado (acima de 60%) mencionado; confirme se o percentual consta no briefing original."
    ),
    (
        r"(?:[úu]ltimas\s+(?:unidades|vagas)|restam\s+poucos\s+minutos|encerra\s+hoje\s+[àa]s\s+23:59)",
        "Gatilho de escassez ou urgência extrema; confirme a autenticidade da data/estoque."
    ),
    (
        r"(?:aprovado\s+por\s+\d+%\s+dos\s+(?:m[ée]dicos|especialistas)|estudo\s+comprova)",
        "Menção a aprovação por especialistas ou estudos científicos; confirme a fonte real dos dados."
    ),
]


def _text_contains_pattern(pattern: str, text: str) -> Optional[str]:
    """Busca um padrao regex no texto e retorna o trecho casado ou None."""
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(0)
    return None


def _is_claim_grounded_in_briefing(claim_matched: str, briefing_text: str) -> bool:
    """
    Verifica se a alegacao encontrada nos textos da campanha possui respaldo
    direto informado pelo proprio usuario nos campos do briefing.
    Evita falsos positivos quando o proprio usuario configurou a caracteristica.
    """
    if not briefing_text:
        return False

    b_lower = briefing_text.lower()
    c_lower = claim_matched.lower()

    # Se o trecho exato ou substantivos centrais estiverem no briefing, considera amparado
    words = [w for w in re.split(r"\W+", c_lower) if len(w) > 4]
    if len(words) >= 2:
        matching_words = sum(1 for w in words if w in b_lower)
        if matching_words >= 2:
            return True

    return c_lower in b_lower


def validate_campaign_guardrails(
    campaign_data: dict,
    report_markdown: str = ""
) -> dict[str, Any]:
    """
    Executa a bateria de guardrails deterministicos sobre a campanha.

    Retorna:
    - status: "approved" (100% conforme), "warning" (avisos de atencao), "blocked" (bloqueio critico)
    - is_blocked: True se houver ao menos 1 problema critico (bloqueia o envio ao n8n)
    - score: Pontuacao de conformidade de 0 a 100
    - critical_issues: Lista de problemas que impedem o envio
    - warnings: Lista de alertas para orientacao do usuario
    - passed_checks: Lista de verificacoes aprovadas com sucesso
    - disclaimer: Nota oficial sobre a natureza orientativa da ferramenta
    """
    form_data = campaign_data.get("form_data") or {}
    strategy = str(campaign_data.get("strategy") or "").strip()
    copy_content = str(campaign_data.get("preliminary_copy") or "").strip()
    review_content = str(campaign_data.get("review_and_final") or "").strip()
    report_md = str(report_markdown or "").strip()

    # Texto agregado de todos os conteudos gerados para analise global
    all_generated_text = f"{strategy}\n\n{copy_content}\n\n{review_content}\n\n{report_md}"

    # Texto de referencia do briefing (dados fornecidos pelo usuario)
    briefing_corpus = " ".join([
        str(form_data.get("product_name") or ""),
        str(form_data.get("product_description") or ""),
        str(form_data.get("differentials") or ""),
        str(form_data.get("target_audience") or ""),
        str(form_data.get("cta") or ""),
    ]).strip()

    critical_issues: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    passed_checks: list[str] = []

    # =========================================================================
    # CHECK 1: Integridade Estrutural do Briefing
    # =========================================================================
    prod_name = str(form_data.get("product_name") or "").strip()
    prod_desc = str(form_data.get("product_description") or "").strip()
    audience = str(form_data.get("target_audience") or "").strip()
    channels = form_data.get("channels") or []

    if not prod_name or not prod_desc or not audience:
        critical_issues.append({
            "code": "INCOMPLETE_BRIEFING",
            "title": "Briefing com Campos Fundamentais Ausentes",
            "message": "Nome do produto, descrição ou público-alvo não foram encontrados no formulário da campanha.",
            "remediation": "Preencha todos os campos obrigatórios do briefing antes de prosseguir."
        })
    else:
        passed_checks.append("Integridade dos campos fundamentais do briefing")

    # =========================================================================
    # CHECK 2: Consistencia e Completude dos Agentes
    # =========================================================================
    # Verifica se a estrategia (Agente 1) possui substancia
    if len(strategy) < 30:
        critical_issues.append({
            "code": "EMPTY_STRATEGY",
            "title": "Estratégia Incompleta ou Ausente",
            "message": "O plano estratégico (Agente 1) está vazio ou não possui densidade suficiente.",
            "remediation": "Execute novamente a geração da campanha para consolidar a etapa estratégica."
        })
    else:
        passed_checks.append("Densidade e estrutura do plano estratégico (Agente 1)")

    # Verifica se a versao revisada final (Agente 3) possui substancia
    if len(review_content) < 30:
        critical_issues.append({
            "code": "EMPTY_REVIEW",
            "title": "Revisão e Versão Final Ausente",
            "message": "Os textos finais revisados (Agente 3) não foram consolidados no resultado da campanha.",
            "remediation": "Certifique-se de que o Agente Revisor completou sua etapa com êxito."
        })
    else:
        passed_checks.append("Validação da versão final revisada (Agente 3)")

    # =========================================================================
    # CHECK 3: Cobertura dos Canais Selecionados
    # =========================================================================
    if not channels or not isinstance(channels, list):
        critical_issues.append({
            "code": "NO_CHANNELS_SELECTED",
            "title": "Nenhum Canal de Distribuição Informado",
            "message": "A campanha não possui canais de divulgação associados.",
            "remediation": "Selecione ao menos um canal de distribuição (Instagram, WhatsApp ou E-mail)."
        })
    else:
        missing_channels = []
        for ch in channels:
            ch_str = str(ch).strip()
            # Mapeamento de termos de busca por canal
            terms_to_look = [ch_str.lower()]
            if "instagram" in ch_str.lower():
                terms_to_look.extend(["feed", "stories", "legenda", "reels"])
            elif "whatsapp" in ch_str.lower():
                terms_to_look.extend(["mensagem", "zap", "conversa"])
            elif "e-mail" in ch_str.lower() or "email" in ch_str.lower():
                terms_to_look.extend(["assunto", "pre-header", "corpo do e-mail", "email"])

            matched = any(t in all_generated_text.lower() for t in terms_to_look)
            if not matched:
                missing_channels.append(ch_str)

        if len(missing_channels) == len(channels) and len(channels) > 0:
            critical_issues.append({
                "code": "ALL_CHANNELS_MISSING",
                "title": "Conteúdo dos Canais Solicitados Ausente",
                "message": f"Nenhum dos canais solicitados ({', '.join(channels)}) foi identificado nos textos produzidos.",
                "remediation": "Regere a campanha para garantir que o Copywriter estruture o conteúdo por canal."
            })
        elif missing_channels:
            warnings.append({
                "code": "PARTIAL_CHANNEL_COVERAGE",
                "title": "Cobertura Parcial de Canais",
                "message": f"Não foi encontrada seção explícita para o(s) canal(is): {', '.join(missing_channels)}.",
                "remediation": "Verifique se o Agente Copywriter adaptou o conteúdo para todos os canais marcados."
            })
        else:
            passed_checks.append(f"Cobertura confirmada de todos os {len(channels)} canais selecionados")

    # =========================================================================
    # CHECK 4: Compliance Publicitário — Alegações Críticas Não Fundamentadas
    # =========================================================================
    detected_critical_claims = []
    for pattern, rationale in CRITICAL_UNGROUNDED_PATTERNS:
        matched_str = _text_contains_pattern(pattern, all_generated_text)
        if matched_str:
            # Checa se o briefing embasa a alegacao (ex: se o usuario escreveu no briefing)
            is_grounded = _is_claim_grounded_in_briefing(matched_str, briefing_corpus)
            if not is_grounded:
                detected_critical_claims.append({
                    "matched": matched_str,
                    "rationale": rationale
                })

    if detected_critical_claims:
        for claim in detected_critical_claims:
            critical_issues.append({
                "code": "CRITICAL_UNGROUNDED_CLAIM",
                "title": "Alegação Comercial Não Fundamentada (Crítica)",
                "message": (
                    f"Identificada alegação comercial desprovida de fundamentação no briefing: \"{claim['matched']}\". "
                    f"Motivo: {claim['rationale']}"
                ),
                "matched_pattern": claim["matched"],
                "remediation": (
                    "Remova promessas de ganhos financeiros garantidos ou curas milagrosas nos textos, "
                    "ou informe comprovações factuais no briefing."
                )
            })
    else:
        passed_checks.append("Ausência de promessas de lucro garantido ou alegações milagrosas vedadas")

    # =========================================================================
    # CHECK 5: Alertas de Atenção — Gatilhos e Alegações Suspeitas
    # =========================================================================
    detected_warning_claims = []
    for pattern, rationale in WARNING_SUSPICIOUS_PATTERNS:
        matched_str = _text_contains_pattern(pattern, all_generated_text)
        if matched_str:
            is_grounded = _is_claim_grounded_in_briefing(matched_str, briefing_corpus)
            if not is_grounded:
                detected_warning_claims.append({
                    "matched": matched_str,
                    "rationale": rationale
                })

    if detected_warning_claims:
        for claim in detected_warning_claims:
            warnings.append({
                "code": "SUSPICIOUS_CLAIM_WARNING",
                "title": "Gatilho Comercial Suspeito para Revisão",
                "message": (
                    f"Termo identificado: \"{claim['matched']}\". "
                    f"Observação: {claim['rationale']}"
                ),
                "matched_pattern": claim["matched"],
                "remediation": "Avalie se este gatilho é verdadeiro antes de aprovar o disparo."
            })
    else:
        passed_checks.append("Consistência de gatilhos de urgência e percentuais de desconto")

    # =========================================================================
    # CHECK 6: Presença do Aviso Ético e Orientativo Obrigatório
    # =========================================================================
    disclaimer_keywords = ["aviso importante", "caráter orientativo", "revisão humana", "inteligência artificial"]
    lower_report = (report_md + " " + review_content).lower()
    has_disclaimer = any(k in lower_report for k in disclaimer_keywords)

    if not has_disclaimer:
        warnings.append({
            "code": "MISSING_ETHICAL_DISCLAIMER",
            "title": "Aviso Ético e Legal Ausente no Relatório",
            "message": "O relatório não contém a cláusula explícita de caráter orientativo da IA generativa.",
            "remediation": "Assegure que a seção de aviso legal esteja anexada ao documento final."
        })
    else:
        passed_checks.append("Presença de aviso ético e legal sobre o caráter orientativo da IA")

    # =========================================================================
    # CÁLCULO DO SCORE E STATUS FINAL
    # =========================================================================
    is_blocked = len(critical_issues) > 0

    if is_blocked:
        final_status = "blocked"
    elif len(warnings) > 0:
        final_status = "warning"
    else:
        final_status = "approved"

    # Score deterministico ponderado
    total_checks = len(passed_checks) + len(critical_issues) + len(warnings)
    if total_checks > 0:
        penalty = (len(critical_issues) * 35) + (len(warnings) * 12)
        score = max(0, min(100, 100 - penalty))
    else:
        score = 0

    return {
        "status": final_status,
        "is_blocked": is_blocked,
        "score": score,
        "critical_issues": critical_issues,
        "warnings": warnings,
        "passed_checks": passed_checks,
        "disclaimer": GUARDRAILS_DISCLAIMER
    }
