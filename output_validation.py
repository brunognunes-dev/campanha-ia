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
    - Avaliacao critica/ajustes presentes.
    - Palavras-chave SEO com aviso presentes.
    - OBRIGATORIO: Versao final completa para CADA canal solicitado (nao apenas observacoes).
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

    # Checagem de secao de versao final consolidada
    has_final_version_header = any(
        k in text_lower for k in [
            "versão final", "versao final", "textos finais",
            "conteúdo final", "conteudo final", "textos revisados"
        ]
    )
    if not has_final_version_header:
        missing_sections.append("Versão Final Revisada dos Conteúdos")

    # Checagem de palavras-chave SEO
    has_seo = any(k in text_lower for k in ["palavras-chave", "palavra-chave", "seo", "otimização temática"])
    if not has_seo:
        missing_sections.append("Palavras-Chave e Otimização Temática")

    # Verifica se os canais estao presentes na versao final
    for ch in channels:
        ch_lower = ch.lower()
        if "instagram" in ch_lower and not any(k in text_lower for k in ["instagram", "feed", "legenda"]):
            missing_channels.append("Instagram")
        elif "whatsapp" in ch_lower and not any(k in text_lower for k in ["whatsapp", "zap"]):
            missing_channels.append("WhatsApp")
        elif ("e-mail" in ch_lower or "email" in ch_lower) and not any(k in text_lower for k in ["e-mail", "email", "assunto"]):
            missing_channels.append("E-mail marketing")

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
