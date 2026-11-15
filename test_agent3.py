"""
Teste isolado do Agente 3 — Revisor e Otimizador (e pipeline completo dos 3 agentes).
Valida se o Revisor recebe o contexto dos agentes 1 e 2,
produzindo a versao final com revisao critica e palavras-chave.
"""

from agents import generate_full_campaign

sample_data = {
    "product_name": "Consultoria Financeira Ágil",
    "product_description": "Serviço de planejamento orçamentário e reestruturação de dívidas para micro e pequenos empresários com faturamento de até R$ 50 mil/mês.",
    "target_audience": "Microempreendedores individuais e donos de pequenas empresas que enfrentam descontrole de caixa.",
    "objective": "Atrair novos clientes e gerar leads",
    "tone": "Profissional e confiável",
    "differentials": "Diagnóstico inicial sem custo e metodologia simples em 3 passos sem planilhas complexas.",
    "cta": "Agende uma sessão gratuita de 30 minutos.",
    "channels": ["Instagram", "WhatsApp"]
}

def on_step(msg: str, step: int):
    print(f"[{step}/3] {msg}")

print("Iniciando orquestração completa dos 3 agentes...")
result = generate_full_campaign(sample_data, progress_callback=on_step)

print("\n===============================")
print("RESULTADO DO AGENTE 3 (REVISOR)")
print("===============================")
print(result["review_and_final"])
print("===============================\n")

# Validacoes de aceitacao
assert result.get("strategy"), "Estratégia do Agente 1 não encontrada."
assert result.get("preliminary_copy"), "Textos do Agente 2 não encontrados."
assert result.get("review_and_final"), "Revisão do Agente 3 não encontrada."
assert len(result["review_and_final"]) > 150, "A saída do revisor foi excessivamente curta."

print("SUCESSO: Pipeline multiagente completo validado com êxito!")
