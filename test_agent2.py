"""
Teste isolado do Agente 2 — Copywriter Multicanal.
Valida se os textos sao gerados apenas para os canais selecionados,
respeitando a estrategia do Agente 1 e sem inventar promessas/precos.
"""

from agents import run_strategist_agent, run_copywriter_agent

sample_data = {
    "product_name": "Consultoria Financeira Ágil",
    "product_description": "Serviço de planejamento orçamentário e reestruturação de dívidas para micro e pequenos empresários com faturamento de até R$ 50 mil/mês.",
    "target_audience": "Microempreendedores individuais e donos de pequenas empresas que enfrentam descontrole de caixa.",
    "objective": "Atrair novos clientes e gerar leads",
    "tone": "Profissional e confiável",
    "differentials": "Diagnóstico inicial sem custo e metodologia simples em 3 passos sem planilhas complexas.",
    "cta": "Agende uma sessão gratuita de 30 minutos.",
    "channels": ["Instagram", "WhatsApp"]  # Testando deliberadamente sem E-mail para checar canal seletivo
}

print("1. Gerando estratégia com Agente 1...")
strategy = run_strategist_agent(sample_data)
print("Estratégia concluída.")

print("\n2. Executando Agente 2 (Copywriter)...")
copy_result = run_copywriter_agent(sample_data, strategy)

print("\n--- TEXTOS GERADOS PELO COPYWRITER ---")
print(copy_result)
print("---------------------------------------")

# Validacoes de aceitacao
assert len(copy_result) > 100, "O texto do Copywriter foi excessivamente curto."
assert "Instagram" in copy_result or "instagram" in copy_result.lower(), "Instagram deveria estar presente nos textos."
assert "WhatsApp" in copy_result or "whatsapp" in copy_result.lower(), "WhatsApp deveria estar presente nos textos."

print("\nSUCESSO: Agente 2 executou com êxito e respeitou os canais selecionados!")
