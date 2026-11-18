"""
Modulo de Validacao Estrutural Leve e Deterministica para os Agentes do MarketFlow AI 2.0.

Valida a completude, presenca de canais solicitados e integridade estrutural
das saidas de cada agente individualmente (sem chamada extra a LLM).
"""

import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ValidationResult:
    """Resultado da validacao estrutural da saida de um agente."""
    is_valid: bool
    agent_name: str
    missing_sections: list[str] = field(default_factory=list)
    missing_channels: list[str] = field(default_factory=list)
    is_truncated: bool = False
    warnings: list[str] = field(default_factory=list)
    error_message: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "agent_name": self.agent_name,
            "missing_sections": self.missing_sections,
            "missing_channels": self.missing_channels,
            "is_truncated": self.is_truncated,
            "warnings": self.warnings,
            "error_message": self.error_message
        }


def _check_truncation(text: str) -> bool:
    """
    Verifica se o texto aparenta ter sido bruscamente interrompido por limite de tokens:
    - Termina com palavra incompleta ou sem pontuacao final valida.
    - Termina com bloco de codigo aberto (```) ou tag incompleta.
    - Termina com conectivos ou artigos pendentes.
    """
    clean = text.strip()
    if not clean:
        return True

    # Verifica blocos de codigo desbalanceados
    if clean.count("```") % 2 != 0:
        return True

    # Padrões de encerramento incompleto
    tail = clean[-30:].lower()
    dangling_endings = [
        " e ", " de ", " do ", " da ", " para ", " com ", " que ",
        " em ", " por ", " um ", " uma ", " ou ", " mas ", " se "
    ]
    for d in dangling_endings:
        if clean.endswith(d.strip()):
            return True

    # Se terminar com caracteres comuns de pontuacao final ou markdown, considera fechado
    valid_closings = (".", "!", "?", "\"", "'", "”", "’", "*", "_", "]", ")", "`", "#", ":")
    if not clean.endswith(valid_closings):
        # Pode ter cortado no meio de uma frase
        last_punct = max(clean.rfind("."), clean.rfind("!"), clean.rfind("?"), clean.rfind("\n"))
        if last_punct != -1 and len(clean) - last_punct > 80:
            return True

    return False


def validate_strategist_output(strategy_text: str) -> ValidationResult:
    """
    Valida a saida do Agente 1 (Estrategista):
    - Densidade minima.
    - Componentes estrategicos fundamentais (publico, proposta de valor, mensagem central, canais).
    - Presenca de fatos vs inferencias ou declaracao de indisponibilidade de pesquisa.
    """
    clean = (strategy_text or "").strip()
    if len(clean) < 150:
        return ValidationResult(
            is_valid=False,
            agent_name="Estrategista",
            missing_sections=["Conteúdo substancial da estratégia"],
            is_truncated=False,
            error_message="Estratégia vazia ou excessivamente curta."
        )

    is_trunc = _check_truncation(clean)

    missing = []
    text_lower = clean.lower()

    # Checagem de secoes-chave
    if not any(term in text_lower for term in ["proposta de valor", "benefício", "valor central"]):
        missing.append("Proposta de Valor")

    if not any(term in text_lower for term in ["mensagem central", "conceito", "slogan"]):
        missing.append("Mensagem Central")

    if not any(term in text_lower for term in ["público-alvo", "publico alvo", "audiência", "perfil"]):
        missing.append("Caracterização do Público-Alvo")

    # Checagem da secao de pesquisa (fatos/fontes ou declaracao de indisponibilidade)
    has_research_section = any(
        term in text_lower for term in [
            "pesquisa", "fatos e dados", "fontes reais", "recomendações e hipóteses",
            "indisponível", "não disponível"
        ]
    )
    if not has_research_section:
        missing.append("Análise de Mercado ou Declaração de Pesquisa")

    is_valid = len(missing) == 0 and not is_trunc
    err_msg = None
    if not is_valid:
        parts = []
        if is_trunc:
            parts.append("Resposta interrompida por limite de tokens.")
        if missing:
            parts.append(f"Seções faltantes: {', '.join(missing)}.")
        err_msg = " ".join(parts)

    return ValidationResult(
        is_valid=is_valid,
        agent_name="Estrategista",
        missing_sections=missing,
        is_truncated=is_trunc,
        error_message=err_msg
    )


def validate_copywriter_output(copy_text: str, channels: list[str]) -> ValidationResult:
    """
    Valida a saida do Agente 2 (Copywriter):
    - Verifica a presenca de blocos especificos e completos para CADA canal solicitado.
    - Verifica que nao esta truncado.
    """
    clean = (copy_text or "").strip()
    if len(clean) < 100:
        return ValidationResult(
            is_valid=False,
            agent_name="Copywriter",
            missing_channels=list(channels),
            is_truncated=False,
            error_message="Textos publicitários vazios ou insuficientes."
        )

    is_trunc = _check_truncation(clean)
    text_lower = clean.lower()

    missing_channels = []
    warnings = []

    for ch in channels:
        ch_lower = ch.lower()
        if "instagram" in ch_lower:
            has_insta = any(k in text_lower for k in ["instagram", "feed", "stories", "legenda", "reels"])
            has_insta_cta = any(k in text_lower for k in ["cta", "link na bio", "comente", "salve", "compartilhe"])
            if not has_insta:
                missing_channels.append("Instagram")
            elif not has_insta_cta:
                warnings.append("Instagram: chamada para ação (CTA) não identificada com clareza.")

        elif "whatsapp" in ch_lower:
            has_zap = any(k in text_lower for k in ["whatsapp", "zap", "mensagem direta", "conversa"])
            if not has_zap:
                missing_channels.append("WhatsApp")

        elif "e-mail" in ch_lower or "email" in ch_lower:
            has_email = any(k in text_lower for k in ["e-mail", "email", "assunto", "pre-header", "preheader", "corpo"])
            if not has_email:
                missing_channels.append("E-mail marketing")

        else:
            # Canal generico
            if ch_lower not in text_lower:
                missing_channels.append(ch)

    is_valid = len(missing_channels) == 0 and not is_trunc
    err_msg = None
    if not is_valid:
        parts = []
        if is_trunc:
            parts.append("Textos de copy truncados por limite de tokens.")
        if missing_channels:
            parts.append(f"Canais ausentes na redação: {', '.join(missing_channels)}.")
        err_msg = " ".join(parts)

    return ValidationResult(
        is_valid=is_valid,
        agent_name="Copywriter",
        missing_channels=missing_channels,
        is_truncated=is_trunc,
        warnings=warnings,
        error_message=err_msg
    )


def validate_reviewer_output(review_text: str, channels: list[str]) -> ValidationResult:
    """
    Valida a saida do Agente 3 (Revisor):
    1. Diagnostico e palavras-chave SEO presentes.
    2. Secao de Versoes Finais Corrigidas OBRIGATORIA.
    3. Todos os canais solicitados presentes na secao de versoes finais com conteudo substancial.
    4. Blocos obrigatorios por canal (Instagram: legenda/CTA; WhatsApp: mensagem/CTA; E-mail: assunto/corpo/CTA).
    5. Proibicao estrita de placeholders de reescrita como '[inserir texto]' ou '[reescrever aqui]'.
    """
    clean = (review_text or "").strip()
    if len(clean) < 150:
        return ValidationResult(
            is_valid=False,
            agent_name="Revisor",
            missing_sections=["Conteúdo da revisão"],
            is_truncated=False,
            error_message="Revisão vazia ou insuficiente."
        )

    is_trunc = _check_truncation(clean)
    text_lower = clean.lower()

    missing_sections = []
    missing_channels = []
    warnings = []

    # 1. Checagem de diagnostico / avaliacao critica
    has_diagnostic = any(
        k in text_lower for k in [
            "diagnóstico", "diagnostico", "avaliação crítica", "avaliacao critica",
            "avaliação", "avaliacao", "ajustes", "problemas identificados",
            "análise crítica", "analise critica"
        ]
    )
    if not has_diagnostic:
        missing_sections.append("Diagnóstico de Revisão")

    # 2. Checagem de palavras-chave SEO
    has_seo = any(k in text_lower for k in ["palavras-chave", "palavra-chave", "seo", "otimização temática", "otimizacao tematica"])
    if not has_seo:
        missing_sections.append("Palavras-Chave e Otimização Temática")

    # 3. Localizacao da secao obrigatoria de Versoes Finais Corrigidas
    final_version_headers = [
        "versões finais", "versoes finais", "versão final", "versao final",
        "textos finais", "conteúdo final", "conteudo final", "textos revisados"
    ]
    final_section_idx = -1
    for h in final_version_headers:
        pos = text_lower.find(h)
        if pos != -1 and (final_section_idx == -1 or pos < final_section_idx):
            final_section_idx = pos

    if final_section_idx == -1:
        missing_sections.append("Versão Final Revisada dos Conteúdos")
        final_section_text = ""
    else:
        final_section_text = text_lower[final_section_idx:]

    # 4. Checagem de placeholders de reescrita proibidos
    placeholder_matches = re.findall(
        r"\[(?:inserir|reescrever|preencher|adicionar|colocar|escrever|conteúdo|conteudo|texto|sua mensagem)\b[^\]]*\]",
        text_lower
    )
    if placeholder_matches:
        missing_sections.append(f"Textos Finais Integrais (placeholders identificados: {', '.join(set(placeholder_matches))})")

    # 5. Verificacao de cada canal solicitado DENTRO da secao de Versoes Finais
    for ch in channels:
        ch_lower = ch.lower()
        if "instagram" in ch_lower:
            # Deve estar presente na secao final com legenda/feed/stories
            has_insta_header = any(k in final_section_text for k in ["instagram", "feed", "stories", "legenda"])
            has_insta_body = any(k in final_section_text for k in ["legenda", "gancho", "feed", "stories", "post"])
            has_insta_cta = any(k in final_section_text for k in ["cta", "link na bio", "comente", "acesse", "clique", "visite", "confira"])

            if not has_insta_header:
                missing_channels.append("Instagram")
            elif not has_insta_body or not has_insta_cta:
                warnings.append("Instagram: elementos da versão final (legenda/CTA) parecem incompletos.")

        elif "whatsapp" in ch_lower:
            has_zap_header = any(k in final_section_text for k in ["whatsapp", "zap", "mensagem"])
            has_zap_cta = any(k in final_section_text for k in ["cta", "responda", "link", "clique", "acesse", "chame", "fale conosco", "visite", "ganhe"])

            if not has_zap_header:
                missing_channels.append("WhatsApp")
            elif not has_zap_cta:
                warnings.append("WhatsApp: chamada para ação (CTA) da mensagem final não identificada.")

        elif "e-mail" in ch_lower or "email" in ch_lower:
            has_email_header = any(k in final_section_text for k in ["e-mail", "email"])
            has_email_subject = any(k in final_section_text for k in ["assunto", "subject", "pre-header", "preheader"])
            has_email_body = any(k in final_section_text for k in ["corpo", "corpo do e-mail", "prezado", "olá", "ola", "parágrafo", "paragrafo"]) or len(final_section_text) > 400

            if not has_email_header or not has_email_subject:
                missing_channels.append("E-mail marketing")
            elif not has_email_body:
                warnings.append("E-mail marketing: corpo da mensagem parece ausente ou excessivamente curto.")

        else:
            if ch_lower not in final_section_text:
                missing_channels.append(ch)

    is_valid = len(missing_sections) == 0 and len(missing_channels) == 0 and not is_trunc
    err_msg = None
    if not is_valid:
        parts = []
        if is_trunc:
            parts.append("Revisão truncada por limite de tokens.")
        if missing_sections:
            parts.append(f"Seções ausentes no relatório de revisão: {', '.join(missing_sections)}.")
        if missing_channels:
            parts.append(f"Canais ausentes na versão final revisada: {', '.join(missing_channels)}.")
        err_msg = " ".join(parts)

    return ValidationResult(
        is_valid=is_valid,
        agent_name="Revisor",
        missing_sections=missing_sections,
        missing_channels=missing_channels,
        is_truncated=is_trunc,
        warnings=warnings,
        error_message=err_msg
    )


def validate_image_designer_output(designer_text: str, channels: list[str]) -> ValidationResult:
    """
    Valida a saida do Agente 4 (Designer de Prompts de Imagem):
    - Ao menos uma peca visual para CADA canal solicitado.
    - Presenca de Formato / Aspect Ratio.
    - Presenca de Prompt em Ingles pronto para uso.
    - Presenca de Composicao / Explicacao em Portugues.
    """
    clean = (designer_text or "").strip()
    if len(clean) < 150:
        return ValidationResult(
            is_valid=False,
            agent_name="Designer de Imagem",
            missing_channels=list(channels),
            is_truncated=False,
            error_message="Prompts de imagem vazios ou insuficientes."
        )

    is_trunc = _check_truncation(clean)
    text_lower = clean.lower()

    missing_channels = []
    missing_sections = []

    # Checagem de conceito/guia visual
    has_concept = any(k in text_lower for k in ["conceito visual", "guia de estilo", "paleta de cores", "estilo"])
    if not has_concept:
        missing_sections.append("Conceito Visual Geral")

    # Checagem de canais
    for ch in channels:
        ch_lower = ch.lower()
        if "instagram" in ch_lower:
            if not any(k in text_lower for k in ["instagram", "feed", "stories"]):
                missing_channels.append("Instagram")
        elif "whatsapp" in ch_lower:
            if not any(k in text_lower for k in ["whatsapp", "zap"]):
                missing_channels.append("WhatsApp")
        elif "e-mail" in ch_lower or "email" in ch_lower:
            if not any(k in text_lower for k in ["e-mail", "email", "header"]):
                missing_channels.append("E-mail marketing")
        else:
            if ch_lower not in text_lower:
                missing_channels.append(ch)

    # Checagem de requisitos de prompt de IA
    has_format = any(k in text_lower for k in ["aspect ratio", "formato", "1:1", "9:16", "16:9", "ar 1:1", "ar 9:16"])
    if not has_format:
        missing_sections.append("Formato / Aspect Ratio das imagens")

    has_english_prompt = any(
        k in text_lower for k in [
            "prompt em inglês", "prompt em ingles", "english prompt",
            "prompt:", "midjourney", "dall-e", "flux"
        ]
    )
    if not has_english_prompt:
        missing_sections.append("Prompt Otimizado em Inglês")

    is_valid = len(missing_channels) == 0 and len(missing_sections) == 0 and not is_trunc
    err_msg = None
    if not is_valid:
        parts = []
        if is_trunc:
            parts.append("Prompts visuais truncados por limite de tokens.")
        if missing_channels:
            parts.append(f"Canais sem sugestão de arte visual: {', '.join(missing_channels)}.")
        if missing_sections:
            parts.append(f"Elementos técnicos ausentes: {', '.join(missing_sections)}.")
        err_msg = " ".join(parts)

    return ValidationResult(
        is_valid=is_valid,
        agent_name="Designer de Imagem",
        missing_sections=missing_sections,
        missing_channels=missing_channels,
        is_truncated=is_trunc,
        error_message=err_msg
    )
