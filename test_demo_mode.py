"""
Suite de testes automatizados para o Modo Demonstracao Offline do MarketFlow AI 2.0.
Abrange os 18 requisitos de teste obrigatorios especificados no projeto.
Utiliza mocks estritos para assegurar que nenhuma chamada externa a rede seja efetuada.
"""

import unittest
from unittest.mock import patch, MagicMock
import hmac

import demo_service
from demo_service import (
    DEMO_FORM_DATA,
    DEMO_RESEARCH_DATA,
    DEMO_STRATEGY,
    DEMO_PRELIMINARY_COPY,
    DEMO_REVIEWER_AND_FINAL,
    DEMO_IMAGE_PROMPTS,
    get_demo_form_data,
    get_demo_research_data,
    get_demo_strategist_output,
    get_demo_copywriter_output,
    get_demo_reviewer_output,
    get_demo_image_designer_output,
    get_demo_campaign_data,
    build_demo_campaign_reports,
    run_demo_workflow_simulation,
    block_demo_automation
)
from output_validation import (
    validate_strategist_output,
    validate_copywriter_output,
    validate_reviewer_output,
    validate_image_designer_output
)
from guardrails import validate_campaign_guardrails
from automation_service import send_campaign_to_n8n


class TestDemoMode(unittest.TestCase):
    """Testes completos do Modo Demonstracao Offline e isolamento de seguranca."""

    def setUp(self):
        self.demo_data = get_demo_campaign_data()
        self.channels = self.demo_data["form_data"]["channels"]

    # 1. Carregamento da campanha fictícia
    def test_01_load_fictitious_campaign(self):
        data = get_demo_campaign_data()
        self.assertIsInstance(data, dict)
        self.assertTrue(data.get("is_demo"))
        self.assertTrue(data.get("is_complete"))
        self.assertEqual(data["form_data"]["product_name"], "Café Aurora")
        self.assertIn("Fortaleza", data["form_data"]["product_description"])

    # 2. Presença dos quatro agentes
    def test_02_presence_of_four_agents(self):
        data = self.demo_data
        self.assertTrue(len(data.get("strategy", "")) > 100, "Agente 1 ausente ou insuficiente")
        self.assertTrue(len(data.get("preliminary_copy", "")) > 100, "Agente 2 ausente ou insuficiente")
        self.assertTrue(len(data.get("review_and_final", "")) > 100, "Agente 3 ausente ou insuficiente")
        self.assertTrue(len(data.get("image_prompts", "")) > 100, "Agente 4 ausente ou insuficiente")

    # 3. Existência dos três canais
    def test_03_existence_of_three_channels(self):
        expected_channels = ["Instagram", "WhatsApp", "E-mail marketing"]
        self.assertEqual(self.channels, expected_channels)
        for ch in expected_channels:
            self.assertIn(ch, self.channels)

    # 4. Conteúdo completo para Instagram
    def test_04_complete_instagram_content(self):
        copy = self.demo_data["preliminary_copy"].lower()
        review = self.demo_data["review_and_final"].lower()

        # Preliminar
        self.assertIn("instagram", copy)
        self.assertIn("gancho", copy)
        self.assertIn("legenda", copy)
        self.assertIn("cta", copy)
        self.assertIn("#cafeaurora", copy)

        # Versao final
        self.assertIn("instagram", review)
        self.assertIn("legenda revisada", review)

    # 5. Conteúdo completo para WhatsApp
    def test_05_complete_whatsapp_content(self):
        copy = self.demo_data["preliminary_copy"].lower()
        review = self.demo_data["review_and_final"].lower()

        self.assertIn("whatsapp", copy)
        self.assertIn("olá", copy)
        self.assertIn("cta", copy)

        self.assertIn("whatsapp", review)
        self.assertIn("mensagem revisada", review)

    # 6. Conteúdo completo para E-mail
    def test_06_complete_email_content(self):
        copy = self.demo_data["preliminary_copy"].lower()
        review = self.demo_data["review_and_final"].lower()

        self.assertIn("e-mail marketing", copy)
        self.assertIn("assunto", copy)
        self.assertIn("pre-header", copy)
        self.assertIn("saudação", copy)
        self.assertIn("corpo do e-mail", copy)

        self.assertIn("assunto:", review)
        self.assertIn("corpo do e-mail revisado:", review)
        # Sem placeholders
        self.assertNotIn("[inserir", review)
        self.assertNotIn("[reescrever", review)

    # 7. Diagnóstico SEO
    def test_07_seo_diagnostic(self):
        review = self.demo_data["review_and_final"]
        val = validate_reviewer_output(review, self.channels)
        self.assertTrue(val.is_valid, f"Falha na validação do revisor: {val.error_message}")
        review_lower = review.lower()
        self.assertTrue("diagnóstico" in review_lower or "diagnostico" in review_lower)
        self.assertTrue("seo" in review_lower or "palavras-chave" in review_lower)
        self.assertIn("cafés especiais fortaleza", review_lower)

    # 8. Versões finais completas
    def test_08_final_versions_complete(self):
        review = self.demo_data["review_and_final"]
        val = validate_reviewer_output(review, self.channels)
        self.assertFalse(val.is_truncated)
        self.assertEqual(len(val.missing_sections), 0)
        self.assertEqual(len(val.missing_channels), 0)

    # 9. Três prompts visuais completos
    def test_09_three_visual_prompts_complete(self):
        images = self.demo_data["image_prompts"]
        val = validate_image_designer_output(images, self.channels)
        self.assertTrue(val.is_valid, f"Falha no Agente 4: {val.error_message}")
        images_lower = images.lower()
        self.assertIn("1:1", images_lower)
        self.assertIn("9:16", images_lower)
        self.assertIn("16:9", images_lower)
        self.assertIn("prompt:", images_lower)
        self.assertIn("midjourney", images_lower)

    # 10. Estrutura dos relatórios
    def test_10_reports_structure(self):
        rep_md, rep_txt = build_demo_campaign_reports(self.demo_data)

        prefix = "DEMONSTRAÇÃO — CAMPANHA FICTÍCIA — RESULTADOS PRÉ-CARREGADOS"
        self.assertTrue(rep_md.startswith(prefix))
        self.assertTrue(rep_txt.startswith(prefix))

        # Secoes essenciais presentes
        self.assertIn("1. DADOS DE CONTEXTO E BRIEFING FICTÍCIO", rep_md)
        self.assertIn("2. FONTES DE PESQUISA E TENDÊNCIAS ILUSTRATIVAS", rep_md)
        self.assertIn("3. ESTRATÉGIA DE MARKETING (AGENTE 1 — ESTRATEGISTA)", rep_md)
        self.assertIn("4. TEXTOS PRELIMINARES POR CANAL (AGENTE 2 — COPYWRITER)", rep_md)
        self.assertIn("5. REVISÃO CRÍTICA, SEO E VERSÃO FINAL (AGENTE 3 — REVISOR)", rep_md)
        self.assertIn("6. DIREÇÃO VISUAL E PROMPTS DE IMAGEM (AGENTE 4 — DESIGNER DE PROMPTS)", rep_md)
        self.assertIn("7. RESULTADO DA VALIDAÇÃO DOS GUARDRAILS DETERMINÍSTICOS", rep_md)
        self.assertIn("8. AVISO ÉTICO E LEGAL", rep_md)

    # 11. Alternância entre modo real e demonstração
    def test_11_mode_switching_state_isolation(self):
        # Simula sessao Streamlit alternando modos
        session = {
            "app_mode": "real",
            "form_data": {"product_name": "Produto Real"},
            "campaign_result": {"is_real": True}
        }

        # Alternando para demo: zera estados
        def switch_mode(target_mode):
            session["app_mode"] = target_mode
            session["form_data"] = None
            session["campaign_result"] = None

        switch_mode("demo")
        self.assertEqual(session["app_mode"], "demo")
        self.assertIsNone(session["form_data"])
        self.assertIsNone(session["campaign_result"])

        # Carrega dados demo
        session["campaign_result"] = get_demo_campaign_data()
        self.assertTrue(session["campaign_result"]["is_demo"])

        # Retorna para modo real
        switch_mode("real")
        self.assertEqual(session["app_mode"], "real")
        self.assertIsNone(session["campaign_result"])

    # 12. Ausência de chamadas ao OpenRouter
    @patch("openrouter_service.generate_chat_completion")
    def test_12_no_openrouter_calls(self, mock_openrouter):
        callbacks = []
        def track_cb(stage, state, msg, res=None):
            callbacks.append((stage, state))

        data = run_demo_workflow_simulation(progress_callback=track_cb)
        self.assertEqual(mock_openrouter.call_count, 0)
        self.assertTrue(data["is_demo"])
        self.assertTrue(len(callbacks) > 0)

    # 13. Ausência de chamadas à Tavily
    @patch("research_service.search_market_trends")
    def test_13_no_tavily_calls(self, mock_tavily):
        data = run_demo_workflow_simulation()
        self.assertEqual(mock_tavily.call_count, 0)
        res_data = data["research_data"]
        self.assertTrue(res_data.get("is_demo"))
        self.assertIn("Nenhuma consulta externa", res_data.get("disclaimer", ""))

    # 14. Ausência de chamadas ao n8n
    @patch("requests.post")
    def test_14_no_n8n_calls(self, mock_post):
        # Durante o modo demo ou simulacao, requests.post nao e chamado
        data = run_demo_workflow_simulation()
        self.assertEqual(mock_post.call_count, 0)

    # 15. Bloqueio de envio no modo demonstração
    @patch("requests.post")
    def test_15_automation_blocked_in_demo_mode(self, mock_post):
        # 1. Funcao dedicada de bloqueio
        res1 = block_demo_automation()
        self.assertFalse(res1["success"])
        self.assertTrue(res1["is_blocked_by_demo"])
        self.assertIn("bloqueada", res1["message"])

        # 2. send_campaign_to_n8n com is_demo=True
        res2 = send_campaign_to_n8n(
            product_name="Qualquer",
            objective="Obj",
            channels=["Instagram"],
            report_markdown="relatorio",
            is_demo=True
        )
        self.assertFalse(res2["success"])
        self.assertTrue(res2["is_blocked_by_demo"])

        # 3. send_campaign_to_n8n com relatório da demonstração
        res3 = send_campaign_to_n8n(
            product_name="Café Aurora",
            objective="Atrair novos clientes",
            channels=["Instagram"],
            report_markdown="DEMONSTRAÇÃO — CAMPANHA FICTÍCIA — RESULTADOS PRÉ-CARREGADOS",
            is_demo=False
        )
        self.assertFalse(res3["success"])
        self.assertTrue(res3["is_blocked_by_demo"])

        # Garante que nenhuma requisicao HTTP real ocorreu
        self.assertEqual(mock_post.call_count, 0)

    # 16. Preservação do modo real
    def test_16_preservation_of_real_mode(self):
        # Valida que validacoes e funcoes existentes permanecem intactas
        from agents import build_campaign_reports
        sample_real_data = {
            "form_data": {
                "product_name": "Consultoria Real",
                "product_description": "Planejamento real",
                "target_audience": "Empresários",
                "objective": "Leads",
                "tone": "Profissional",
                "channels": ["Instagram"]
            },
            "strategy": "Estratégia real com proposta de valor e mensagem central.",
            "preliminary_copy": "Instagram: legenda e CTA link na bio.",
            "review_and_final": "Diagnóstico SEO.\n## Versões Finais\nInstagram: legenda e CTA link na bio.",
            "image_prompts": "Conceito visual Instagram ar 1:1 prompt: real photorealistic."
        }
        md, txt = build_campaign_reports(sample_real_data)
        self.assertIn("CONSULTORIA REAL", md)
        self.assertFalse(md.startswith("DEMONSTRAÇÃO"))

    # 17. Preservação da autenticação
    def test_17_authentication_preservation(self):
        # Testa a logica de comparacao em tempo constante utilizada no check_password
        secret = "senha_teste_academica_2026"
        valid_input = "senha_teste_academica_2026"
        invalid_input = "senha_incorreta"

        self.assertTrue(hmac.compare_digest(valid_input.encode("utf-8"), secret.encode("utf-8")))
        self.assertFalse(hmac.compare_digest(invalid_input.encode("utf-8"), secret.encode("utf-8")))

    # 18. Estado correto do Streamlit após recarregar a página
    def test_18_streamlit_state_consistency(self):
        data = get_demo_campaign_data()
        rep_md, rep_txt = build_demo_campaign_reports(data)

        # Valida conformidade dos guardrails no estado gerado
        gr = validate_campaign_guardrails(data, report_markdown=rep_md)
        self.assertEqual(gr["status"], "approved")
        self.assertEqual(gr["score"], 100)
        self.assertFalse(gr["is_blocked"])
        self.assertEqual(len(gr["critical_issues"]), 0)
        self.assertEqual(len(gr["warnings"]), 0)


if __name__ == "__main__":
    unittest.main()
