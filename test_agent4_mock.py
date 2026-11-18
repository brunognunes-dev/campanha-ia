"""
Suite de testes automatizados com mocks para o Quarto Agente:
Designer de Prompts de Imagem (Image Prompt Designer).
Valida:
- Prompt de sistema e montagem de user prompt
- Execucao isolada de run_image_designer_agent via mock do OpenRouter
- Orquestracao completa de 4 agentes em generate_full_campaign()
- Integracao dos prompts de imagem nos relatorios Markdown e TXT (build_campaign_reports)
- Preservacao de estado e eventos reais no callback de progresso
"""

import unittest
from unittest.mock import patch, MagicMock

from prompts import (
    IMAGE_DESIGNER_SYSTEM_PROMPT,
    build_image_designer_user_prompt
)
from agents import (
    run_image_designer_agent,
    generate_full_campaign,
    build_campaign_reports
)


class TestImageDesignerAgent(unittest.TestCase):
    """Testes unitarios para o Agente 4 — Designer de Prompts de Imagem."""

    def setUp(self):
        self.sample_form_data = {
            "product_name": "EcoGarrafa Térmica Inteligente",
            "product_description": "Garrafa com display de temperatura digital e aço inox reciclado.",
            "target_audience": "Profissionais e praticantes de esportes ao ar livre.",
            "objective": "Divulgar lançamento de produto ou serviço",
            "tone": "Criativo, descontraído e dinâmico",
            "differentials": "Isolamento a vácuo de 24h e sensor touch.",
            "cta": "Garanta a sua no lançamento com frete grátis.",
            "channels": ["Instagram", "WhatsApp", "E-mail marketing"]
        }
        self.sample_strategy = "## 1. Resumo\nEstratégia voltada para lifestyle sustentável e inovação."
        self.sample_copy = "### Instagram\nTexto de legenda criativa para feed."
        self.sample_review = "## 3. Versão Final Revisada\nTextos finais revisados e lapidados para os 3 canais."
        self.sample_image_prompts = (
            "## 1. Conceito Visual Geral e Guia de Estilo\n"
            "Estética minimalista com iluminação natural suave e tons terrosos e ciano.\n\n"
            "## 2. Prompts de Imagem por Canal de Divulgação\n"
            "### Instagram — Foto Lifestyle em Trilha\n"
            "- **Objetivo Visual:** Demonstrar o uso prático da garrafa em ambiente natural.\n"
            "- **Formato / Aspect Ratio:** 1:1\n"
            "- **Prompt em Inglês:**\n"
            "> `Minimalist stainless steel water bottle with digital LED temperature display on lid, resting on a mossy rock, morning mountain sunlight, soft bokeh background, photorealistic 8k, --ar 1:1`\n"
            "- **Composição em Português:** Garrafa ecológica de inox sobre rocha em trilha montanhosa.\n"
            "- **Elementos a Evitar:** Plastic, low quality, oversaturated colors.\n\n"
            "## 3. Recomendações Técnicas para Produção Visual\n"
            "Manter consistência de temperatura de cor e evitar reflexos distorcidos no inox."
        )

    def test_build_image_designer_user_prompt(self):
        """Valida que o prompt de usuario combina briefing, estrategia e textos finais revisados."""
        prompt = build_image_designer_user_prompt(
            self.sample_form_data,
            self.sample_strategy,
            self.sample_review
        )
        self.assertIn("EcoGarrafa Térmica Inteligente", prompt)
        self.assertIn("Profissionais e praticantes de esportes", prompt)
        self.assertIn("Instagram, WhatsApp, E-mail marketing", prompt)
        self.assertIn("ESTRATÉGIA DE MARKETING (AGENTE 1)", prompt)
        self.assertIn("TEXTOS REVISADOS E VERSÃO FINAL (AGENTE 3)", prompt)
        self.assertIn(self.sample_strategy, prompt)
        self.assertIn(self.sample_review, prompt)

    def test_system_prompt_rules(self):
        """Valida diretrizes essenciais no prompt de sistema do Agente 4."""
        self.assertIn("Diretor de Arte e Designer de Prompts", IMAGE_DESIGNER_SYSTEM_PROMPT)
        self.assertIn("NUNCA inclua código", IMAGE_DESIGNER_SYSTEM_PROMPT)
        self.assertIn("Midjourney", IMAGE_DESIGNER_SYSTEM_PROMPT)
        self.assertIn("Aspect Ratio", IMAGE_DESIGNER_SYSTEM_PROMPT)
        self.assertIn("Negative Prompt", IMAGE_DESIGNER_SYSTEM_PROMPT)

    @patch("agents.generate_chat_completion")
    def test_run_image_designer_agent(self, mock_chat):
        """Valida a chamada do Agente 4 ao servico OpenRouter."""
        mock_chat.return_value = self.sample_image_prompts

        result = run_image_designer_agent(
            self.sample_form_data,
            self.sample_strategy,
            self.sample_review
        )

        self.assertEqual(result, self.sample_image_prompts)
        mock_chat.assert_called_once()
        call_kwargs = mock_chat.call_args[1]
        self.assertEqual(call_kwargs["system_prompt"], IMAGE_DESIGNER_SYSTEM_PROMPT)
        self.assertIn("EcoGarrafa", call_kwargs["user_prompt"])
        self.assertEqual(call_kwargs["max_tokens"], 1800)

    @patch("agents.search_market_trends")
    @patch("agents.run_strategist_agent")
    @patch("agents.run_copywriter_agent")
    @patch("agents.run_reviewer_agent")
    @patch("agents.run_image_designer_agent")
    def test_generate_full_campaign_4_agents_orchestration(
        self, mock_img, mock_rev, mock_copy, mock_strat, mock_search
    ):
        """Valida orquestracao completa dos 4 agentes e eventos de callback em ordem."""
        mock_search.return_value = {
            "success": True,
            "query": "tendências mercado garrafa sustentável",
            "total_results": 1,
            "results": [{
                "title": "Tendências Sustentáveis",
                "url": "https://example.com/trends",
                "content": "Crescimento de 40% em produtos ecológicos.",
                "published_date": "2026-01-15",
                "score": 0.95
            }],
            "error": None,
            "cached": False
        }
        mock_strat.return_value = self.sample_strategy
        mock_copy.return_value = self.sample_copy
        mock_rev.return_value = self.sample_review
        mock_img.return_value = self.sample_image_prompts

        events_sequence = []

        def callback_tracer(stage, state, msg, result=None):
            events_sequence.append((stage, state))

        campaign = generate_full_campaign(
            self.sample_form_data,
            progress_callback=callback_tracer
        )

        # 1. Verifica retorno de todas as etapas no dicionario consolidado
        self.assertIn("form_data", campaign)
        self.assertIn("research_data", campaign)
        self.assertIn("strategy", campaign)
        self.assertIn("preliminary_copy", campaign)
        self.assertIn("review_and_final", campaign)
        self.assertIn("image_prompts", campaign)
        self.assertEqual(campaign["image_prompts"], self.sample_image_prompts)
        self.assertTrue(campaign["research_data"]["success"])

        # 2. Verifica sequencia real de eventos: pesquisa externa + 4 agentes
        expected_events = [
            ("research", "running"),
            ("research", "completed"),
            ("strategist", "running"),
            ("strategist", "completed"),
            ("copywriter", "running"),
            ("copywriter", "completed"),
            ("reviewer", "running"),
            ("reviewer", "completed"),
            ("image_designer", "running"),
            ("image_designer", "completed"),
            ("ready", "completed")
        ]
        self.assertEqual(events_sequence, expected_events)

    def test_build_campaign_reports_with_image_prompts(self):
        """Valida inclusao da secao de prompts de imagem no relatorio Markdown e TXT."""
        campaign_data = {
            "form_data": self.sample_form_data,
            "strategy": self.sample_strategy,
            "preliminary_copy": self.sample_copy,
            "review_and_final": self.sample_review,
            "image_prompts": self.sample_image_prompts
        }

        md_report, txt_report = build_campaign_reports(campaign_data)

        # 1. Markdown
        self.assertIn("## 5. DIREÇÃO VISUAL E PROMPTS DE IMAGEM", md_report)
        self.assertIn("Minimalist stainless steel water bottle", md_report)
        self.assertIn("## 6. AVISO ÉTICO E LEGAL", md_report)

        # 2. TXT
        self.assertIn("[5. DIREÇÃO VISUAL E PROMPTS DE IMAGEM (AGENTE 4 — DESIGNER DE PROMPTS)]", txt_report)
        self.assertIn("Minimalist stainless steel water bottle", txt_report)
        self.assertIn("[6. AVISO ÉTICO E LEGAL]", txt_report)

    def test_build_campaign_reports_backward_compatibility(self):
        """Valida que campanhas legadas sem image_prompts continuam gerando relatorios validos."""
        legacy_campaign_data = {
            "form_data": self.sample_form_data,
            "strategy": self.sample_strategy,
            "preliminary_copy": self.sample_copy,
            "review_and_final": self.sample_review
            # image_prompts ausente
        }

        md_report, txt_report = build_campaign_reports(legacy_campaign_data)
        self.assertIn("## 4. REVISÃO CRÍTICA, SEO E VERSÃO FINAL", md_report)
        self.assertIn("## 5. AVISO ÉTICO E LEGAL", md_report)
        self.assertNotIn("## 5. DIREÇÃO VISUAL", md_report)


if __name__ == "__main__":
    unittest.main()
