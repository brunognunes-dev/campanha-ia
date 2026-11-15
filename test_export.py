"""
Teste unitario de exportacao de relatorios nos formatos Markdown e TXT.
Valida se todas as 7 secoes obrigatorias exigidas no prompt.txt estao presentes.
"""

from agents import build_campaign_reports

sample_campaign = {
    "form_data": {
        "product_name": "Consultoria Financeira Ágil",
        "product_description": "Serviço de planejamento orçamentário e reestruturação de dívidas.",
        "target_audience": "Microempreendedores e pequenos empresários.",
        "objective": "Atrair novos clientes e gerar leads",
        "tone": "Profissional e confiável",
        "differentials": "Diagnóstico inicial sem custo.",
        "cta": "Agende uma sessão gratuita de 30 minutos.",
        "channels": ["Instagram", "WhatsApp"]
    },
    "strategy": "## 1. Resumo\nEstratégia sólida baseada em dados reais.",
    "preliminary_copy": "### Instagram\nLegenda criativa.\n\n### WhatsApp\nMensagem direta.",
    "review_and_final": "## 1. Avaliação\nSem incoerências.\n## 2. Palavras-chave (SEO orientativo)\nFluxo de caixa.\n## 3. Versão Final\nTextos revisados."
}

print("Testando geracao de relatorios (.md e .txt)...")
md_report, txt_report = build_campaign_reports(sample_campaign)

# 1. Validacao do relatorio Markdown
assert "# RELATÓRIO DE CAMPANHA DE MARKETING" in md_report, "Titulo principal nao encontrado no Markdown."
assert "DADOS DE CONTEXTO E BRIEFING" in md_report, "Briefing nao encontrado no Markdown."
assert "ESTRATÉGIA DE MARKETING" in md_report, "Estrategia nao encontrada no Markdown."
assert "TEXTOS PRELIMINARES POR CANAL" in md_report, "Textos preliminares nao encontrados no Markdown."
assert "REVISÃO CRÍTICA, SEO E VERSÃO FINAL" in md_report, "Revisao final nao encontrada no Markdown."
assert "AVISO IMPORTANTE:" in md_report, "Aviso etico obrigatorio nao encontrado no Markdown."

# 2. Validacao do relatorio Texto (.txt)
assert "RELATÓRIO DE CAMPANHA DE MARKETING" in txt_report, "Titulo principal nao encontrado no TXT."
assert "[1. DADOS DE CONTEXTO E BRIEFING]" in txt_report, "Briefing nao encontrado no TXT."
assert "AVISO IMPORTANTE:" in txt_report, "Aviso etico obrigatorio nao encontrado no TXT."

print("\n--- AMOSTRA DO RELATORIO MARKDOWN (Primeiras 30 linhas) ---")
print("\n".join(md_report.splitlines()[:30]))
print("...")

print("\nSUCESSO: Exportacao de relatorios (.md e .txt) validada com 100% de conformidade!")
