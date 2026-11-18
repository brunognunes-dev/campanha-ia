"""
Suite de testes automatizados para a camada de Guardrails e Compliance (guardrails.py).
Valida:
1. Conteudos validos e em conformidade (aprovacao sem bloqueio)
2. Conteudos incompletos (bloqueio estrutural deterministico)
3. Conteudos suspeitos com alegacoes proibidas (bloqueio por compliance)
4. Palavras isoladas e conteudos legitimos (sem falsos positivos)
5. Amparo contextual no briefing
6. Avisos leves (warnings sem bloqueio)
7. Presenca do disclaimer oficial
"""

import copy
import unittest
from guardrails import validate_campaign_guardrails, GUARDRAILS_DISCLAIMER


class TestCampaignGuardrails(unittest.TestCase):
    """Bateria de testes deterministicos dos Guardrails do MarketFlow AI."""

    def setUp(self):
        self.valid_campaign = {
            "form_data": {
                "product_name": "Consultoria Financeira Ágil",
                "product_description": "Serviço de planejamento orçamentário e consultoria de negócios.",
                "target_audience": "Microempreendedores e gestores de pequenas empresas.",
                "objective": "Atrair novos clientes e gerar leads",
                "tone": "Profissional e confiável",
                "differentials": "Diagnóstico inicial sem custo e metodologia em 3 etapas.",
                "cta": "Agende uma sessão gratuita de 30 minutos.",
                "channels": ["Instagram", "WhatsApp"]
            },
            "strategy": (
                "## 1. Resumo do Produto\nConsultoria estratégica de finanças para pequenos negócios.\n"
                "## 2. Objetivo Principal\nAtrair leads qualificados.\n"
                "## 3. Público-Alvo\nMicroempresários com foco em organização contábil e crescimento sustentável."
            ),
            "preliminary_copy": (
                "### Instagram\nGanhe clareza na gestão financeira da sua empresa. Agende seu diagnóstico.\n\n"
                "### WhatsApp\nOlá! Quer organizar o fluxo de caixa do seu negócio este mês? Vamos conversar."
            ),
            "review_and_final": (
                "## 1. Avaliação Crítica\nTextos alinhados e objetivos.\n"
                "## 3. Versão Final Revisada\n"
                "### Instagram\nLegenda revisada para feed do Instagram com chamada clara.\n"
                "### WhatsApp\nMensagem personalizada para contato direto no WhatsApp."
            )
        }
        self.valid_report = (
            "# RELATÓRIO DE CAMPANHA\n\n"
            "## 1. DADOS DE BRIEFING\n...\n"
            "## 5. AVISO ÉTICO E LEGAL\n"
            "AVISO IMPORTANTE: Os textos e análises contidos neste relatório foram elaborados por sistemas "
            "de Inteligência Artificial Generativa com caráter orientativo. Todo conteúdo deve passar por "
            "criteriosa revisão humana antes de veiculação."
        )

    # 1. Teste de Conteudo Valido
    def test_valid_campaign_approved(self):
        """Valida que uma campanha integra e etica e aprovada sem bloqueios."""
        result = validate_campaign_guardrails(self.valid_campaign, self.valid_report)

        self.assertEqual(result["status"], "approved")
        self.assertFalse(result["is_blocked"])
        self.assertEqual(len(result["critical_issues"]), 0)
        self.assertGreaterEqual(result["score"], 80)
        self.assertIn("disclaimer", result)
        self.assertIn("não substitui a criteriosa revisão humana", result["disclaimer"])

    # 2. Teste de Conteudo Incompleto (Briefing ausente)
    def test_incomplete_briefing_blocked(self):
        """Valida bloqueio quando campos essenciais do briefing estao ausentes."""
        bad_campaign = dict(self.valid_campaign)
        bad_campaign["form_data"] = {
            "product_name": "",  # Vazio
            "product_description": "",
            "target_audience": "",
            "channels": []
        }

        result = validate_campaign_guardrails(bad_campaign, self.valid_report)
        self.assertTrue(result["is_blocked"])
        self.assertEqual(result["status"], "blocked")

        codes = [i["code"] for i in result["critical_issues"]]
        self.assertIn("INCOMPLETE_BRIEFING", codes)

    # 3. Teste de Conteudo Incompleto (Estrategia ou Revisao vazia)
    def test_empty_agent_content_blocked(self):
        """Valida bloqueio quando o resultado dos agentes estiver vazio."""
        empty_strat_campaign = dict(self.valid_campaign)
        empty_strat_campaign["strategy"] = ""  # Agente 1 falhou

        result = validate_campaign_guardrails(empty_strat_campaign, self.valid_report)
        self.assertTrue(result["is_blocked"])
        codes = [i["code"] for i in result["critical_issues"]]
        self.assertIn("EMPTY_STRATEGY", codes)

    # 4. Teste de Conteudo Suspeito — Promessa de Lucro Garantido sem Risco
    def test_suspicious_guaranteed_profit_blocked(self):
        """Valida bloqueio critico em promessas categóricas de lucro garantido sem risco."""
        suspicious_campaign = dict(self.valid_campaign)
        suspicious_campaign["review_and_final"] = (
            "Com nosso método exclusivo, você tem lucro garantido sem risco de 500% ao mês. "
            "Fique rico em 7 dias sem esforço algum!"
        )

        result = validate_campaign_guardrails(suspicious_campaign, self.valid_report)
        self.assertTrue(result["is_blocked"])
        self.assertEqual(result["status"], "blocked")

        codes = [i["code"] for i in result["critical_issues"]]
        self.assertIn("CRITICAL_UNGROUNDED_CLAIM", codes)

        messages = " ".join([i["message"] for i in result["critical_issues"]])
        self.assertIn("lucro garantido sem risco", messages.lower())

    # 5. Teste de Conteudo Suspeito — Promessa de Cura Milagrosa
    def test_suspicious_miracle_cure_blocked(self):
        """Valida bloqueio em alegações médicas de cura milagrosa."""
        medical_campaign = copy.deepcopy(self.valid_campaign)
        medical_campaign["review_and_final"] += (
            "\n\nATENÇÃO: Nosso suplemento natural cura definitivamente qualquer tipo de doença e enfermidade."
        )

        result = validate_campaign_guardrails(medical_campaign, self.valid_report)
        self.assertTrue(result["is_blocked"])
        codes = [i["code"] for i in result["critical_issues"]]
        self.assertIn("CRITICAL_UNGROUNDED_CLAIM", codes)

    # 6. Teste de Palavras Isoladas Legítimas (NÃO devem bloquear)
    def test_legitimate_words_not_blocked(self):
        """
        Garante que termos comuns como 'lucro', 'garantia legal', 'dinheiro' ou 'resultados'
        em contextos legitimos e profissionais NUNCA geram bloqueio isoladamente.
        """
        legit_campaign = copy.deepcopy(self.valid_campaign)
        legit_campaign["review_and_final"] += (
            "\n\nEntenda como otimizar o lucro operacional da sua empresa. "
            "Acompanhe o fluxo de dinheiro com precisão e conte com a garantia de conformidade contábil. "
            "Veja os resultados alcançados por gestores que aplicaram organização financeira."
        )

        result = validate_campaign_guardrails(legit_campaign, self.valid_report)
        self.assertFalse(result["is_blocked"])
        self.assertNotEqual(result["status"], "blocked")

    # 7. Teste de Alegacao Fundamentada no Briefing
    def test_grounded_claim_in_briefing_accepted(self):
        """Garante que alegacoes respaldadas no proprio briefing do usuario nao geram falso positivo."""
        grounded_campaign = copy.deepcopy(self.valid_campaign)
        grounded_campaign["form_data"]["differentials"] = "Oferecemos garantia de 30 dias para devolução."
        grounded_campaign["review_and_final"] += (
            "\n\nAproveite nossa consultoria com garantia de 30 dias para devolução caso não fique satisfeito."
        )

        result = validate_campaign_guardrails(grounded_campaign, self.valid_report)
        self.assertFalse(result["is_blocked"])

    # 8. Teste de Avisos Leves (Warnings sem bloqueio)
    def test_warning_claims_not_blocking(self):
        """Valida que gatilhos de urgencia sem amparo geram warnings, mas NAO bloqueiam o envio."""
        warning_campaign = copy.deepcopy(self.valid_campaign)
        warning_campaign["review_and_final"] += (
            "\n\nAproveite nosso mega desconto de 80% que encerra hoje às 23:59!"
        )

        result = validate_campaign_guardrails(warning_campaign, self.valid_report)
        # Deve gerar warning, mas is_blocked deve ser False
        self.assertFalse(result["is_blocked"])
        self.assertEqual(result["status"], "warning")
        self.assertGreater(len(result["warnings"]), 0)

    # 9. Teste do Disclaimer Oficial e Infalibilidade
    def test_disclaimer_presence_and_humility(self):
        """Valida que o sistema nao afirma ser infalivel e declara carater orientativo."""
        result = validate_campaign_guardrails(self.valid_campaign, self.valid_report)
        disclaimer = result["disclaimer"]
        self.assertIn("orientativo", disclaimer)
        self.assertIn("não é infalível", disclaimer)


if __name__ == "__main__":
    unittest.main()
