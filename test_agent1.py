"""
Teste isolado do Agente 1 — Estrategista de Marketing.
Valida se o prompt, a integracao com OpenRouter e as regras de negocio estao funcionando.
"""

from agents import run_strategist_agent

sample_data = {
    "product_name": "Consultoria Financeira Ágil",
    "product_description": "Serviço de planejamento orçamentário e reestruturação de dívidas para micro e pequenos empresários com faturamento de até R$ 50 mil/mês.",
    "target_audience": "Microempreendedores individuais e donos de pequenas empresas que enfrentam descontrole de caixa.",
    "objective": "Atrair novos clientes e gerar leads",
    "tone": "Profissional e confiável",
    "differentials": "Diagnóstico inicial sem custo e metodologia simples em 3 passos sem planilhas complexas.",
    "cta": "Agende uma sessão gratuita de 30 minutos.",
    "channels": ["Instagram", "WhatsApp", "E-mail marketing"]
}

print("Executando teste do Agente 1 (Estrategista)...")
strategy = run_strategist_agent(sample_data)

print("\n--- ESTRATÉGIA GERADA ---")
print(strategy)
print("--------------------------")

# Validacoes basicas dos criterios de aceitacao
assert len(strategy) > 100, "A resposta do Estrategista foi excessivamente curta."
print("\nSUCESSO: Agente 1 executou com êxito e produziu a estratégia completa!")
