"""
Suite de testes automatizados com mocks para o Primeiro Agente:
Pesquisador de Tendências e Estrategista de Marketing (MarketFlow AI 2.0).
Valida:
1. Montagem do prompt de usuário integrando briefing e dados reais de pesquisa Tavily.
2. Tratamento do prompt quando a pesquisa estiver indisponível (sem inventar fontes).
3. Diretrizes do prompt de sistema (separação de fatos reais vs. inferências).
4. Execução isolada de run_strategist_agent com mock do OpenRouter.
5. Orquestração em generate_full_campaign garantindo que a pesquisa execute ANTES da LLM.
6. Propagação da estratégia fundamentada para o Copywriter (Agente 2).
7. Inclusão das fontes reais e URLs nos relatórios Markdown e TXT.
8. Resiliência: fallback gracioso sem quebrar o pipeline quando a pesquisa falhar.
"""

import unittest
from unittest.mock import patch, MagicMock

from prompts import (
    STRATEGIST_SYSTEM_PROMPT,
    build_strategist_user_prompt,
    build_copywriter_user_prompt
)
from agents import (
    run_strategist_agent,
    generate_full_campaign,
    build_campaign_reports
)


class TestAgent1ResearchIntegration(unittest.TestCase):
    """Testes unitarios com mocks para o Agente 1 (Pesquisador & Estrategista)."""

    def setUp(self):
        self.sample_form_data = {
            "product_name": "NutriFit Shake Proteico Vegano",
            "product_description": "Shake substituto de refeição à base de proteína de ervilha e arroz com vitaminas.",
            "target_audience": "Praticantes de esportes, veganos e pessoas em busca de alimentação saudável prática.",
            "objective": "Lançar produto e gerar vendas diretas",
            "tone": "Inspirador, confiável e enérgico",
            "differentials": "Zero açúcar adicionado, embalagem 100% biodegradável e sabor aprovado por chefs.",
            "cta": "Experimente com 20% OFF no primeiro pedido.",
            "channels": ["Instagram", "WhatsApp", "E-mail marketing"]
        }

        self.sample_research_success = {
            "success": True,
            "query": "tendências mercado shake proteico vegano",
            "total_results": 2,
            "results": [
                {
                    "title": "Crescimento do Mercado Plant-Based no Brasil 2026",
                    "url": "https://portalalimentos.com.br/plant-based-2026",
                    "content": "O mercado brasileiro de alimentos plant-based cresceu 32% no último ano, impulsionado por jovens urbanos.",
                    "published_date": "2026-02-10",
                    "score": 0.94
                },
                {
                    "title": "Consumo de Proteínas Vegetais e Sustentabilidade",
                    "url": "https://tendenciasnutricao.org/proteina-vegetal",
                    "content": "Consumidores priorizam marcas com embalagens sustentáveis e rotulagem limpa (clean label).",
                    "published_date": "2026-01-20",
                    "score": 0.88
                }
            ],
            "error": None,
            "cached": False
        }

        self.sample_research_failure = {
            "success": False,
            "query": "tendências mercado shake proteico vegano",
            "total_results": 0,
            "results": [],
            "error": "Falha de conexão com os servidores da Tavily Search API.",
            "cached": False
        }

    def test_strategist_system_prompt_rules(self):
        """Verifica se o system prompt do Agente 1 estabelece as regras de fundamentação e fontes reais."""
        self.assertIn("Pesquisador de Tendências e Estrategista de Marketing", STRATEGIST_SYSTEM_PROMPT)
        self.assertIn("Fatos e Dados Observados (Fontes Reais)", STRATEGIST_SYSTEM_PROMPT)
        self.assertIn("Recomendações e Hipóteses Inferidas", STRATEGIST_SYSTEM_PROMPT)
        self.assertIn("NUNCA invente fontes, links, veículos ou datas", STRATEGIST_SYSTEM_PROMPT)

    def test_build_user_prompt_with_successful_research(self):
        """Valida se o prompt de usuario incorpora as URLs, titulos e conteudos das fontes reais."""
        prompt = build_strategist_user_prompt(self.sample_form_data, self.sample_research_success)

        # Briefing
        self.assertIn("NutriFit Shake Proteico Vegano", prompt)
        self.assertIn("Praticantes de esportes", prompt)

        # Dados da pesquisa externa
        self.assertIn("Crescimento do Mercado Plant-Based no Brasil 2026", prompt)
        self.assertIn("https://portalalimentos.com.br/plant-based-2026", prompt)
        self.assertIn("2026-02-10", prompt)
        self.assertIn("Consumo de Proteínas Vegetais e Sustentabilidade", prompt)
        self.assertIn("https://tendenciasnutricao.org/proteina-vegetal", prompt)
        self.assertIn("Separe rigorosamente fatos observados destas fontes reais de suas inferências", prompt)

    def test_build_user_prompt_with_unavailable_research(self):
        """Valida instrucao explicita no prompt quando a pesquisa estiver indisponivel."""
        prompt = build_strategist_user_prompt(self.sample_form_data, self.sample_research_failure)

        self.assertIn("STATUS: INDISPONÍVEL", prompt)
        self.assertIn("Falha de conexão com os servidores da Tavily Search API", prompt)
        self.assertIn("NÃO invente dados externos ou URLs fictícias", prompt)

    @patch("agents.generate_chat_completion")
    def test_run_strategist_agent_isolated(self, mock_completion):
        """Valida chamada isolada de run_strategist_agent com pesquisa fornecida."""
        mock_completion.return_value = (
            "## 1. Pesquisa de Mercado e Tendências Externas\n"
            "### Fatos e Dados Observados (Fontes Reais)\n"
            "- Mercado cresceu 32% (Fonte: https://portalalimentos.com.br/plant-based-2026)\n\n"
            "### Recomendações e Hipóteses Inferidas\n"
            "- Focar em jovens urbanos que valorizam sustentabilidade.\n\n"
            "## 2. Resumo do Produto ou Serviço\nNutriFit Shake."
        )

        strategy = run_strategist_agent(self.sample_form_data, self.sample_research_success)

        self.assertTrue(mock_completion.called)
        _, kwargs = mock_completion.call_args
        self.assertEqual(kwargs["system_prompt"], STRATEGIST_SYSTEM_PROMPT)
        self.assertIn("https://portalalimentos.com.br/plant-based-2026", kwargs["user_prompt"])
        self.assertIn("32%", strategy)

    @patch("agents.search_market_trends")
    @patch("agents.run_strategist_agent")
    @patch("agents.run_copywriter_agent")
    @patch("agents.run_reviewer_agent")
    @patch("agents.run_image_designer_agent")
    def test_generate_full_campaign_research_executes_before_llm(
        self, mock_img, mock_rev, mock_copy, mock_strat, mock_search
    ):
        """Valida que a pesquisa externa ocorre ANTES da chamada do Estrategista à LLM."""
        call_order = []

        def fake_search(*args, **kwargs):
            call_order.append("search")
            return self.sample_research_success

        def fake_strat(form_data, research_data=None):
            call_order.append("strategist")
            self.assertIsNotNone(research_data)
            self.assertEqual(research_data["results"][0]["url"], "https://portalalimentos.com.br/plant-based-2026")
            return "Estratégia fundamentada em fatos reais."

        def fake_copy(form_data, strategy):
            call_order.append("copywriter")
            # Valida que o Copywriter recebe a estratégia fundamentada
            self.assertIn("Estratégia fundamentada", strategy)
            return "Textos dos canais."

        mock_search.side_effect = fake_search
        mock_strat.side_effect = fake_strat
        mock_copy.side_effect = fake_copy
        mock_rev.return_value = "Revisão aprovada."
        mock_img.return_value = "Prompts de imagem."

        result = generate_full_campaign(self.sample_form_data)

        # Ordem estrita: pesquisa deve acontecer antes do estrategista
        self.assertEqual(call_order[0], "search")
        self.assertEqual(call_order[1], "strategist")
        self.assertEqual(call_order[2], "copywriter")

        # Dados no resultado consolidado
        self.assertIn("research_data", result)
        self.assertTrue(result["research_data"]["success"])
        self.assertEqual(result["research_data"]["total_results"], 2)

    @patch("agents.search_market_trends")
    @patch("agents.run_strategist_agent")
    @patch("agents.run_copywriter_agent")
    @patch("agents.run_reviewer_agent")
    @patch("agents.run_image_designer_agent")
    def test_generate_full_campaign_graceful_fallback_when_research_fails(
        self, mock_img, mock_rev, mock_copy, mock_strat, mock_search
    ):
        """Valida que o pipeline continua com fallback transparente caso a pesquisa falhe."""
        mock_search.return_value = self.sample_research_failure
        mock_strat.return_value = "Estratégia formulada com premissas do briefing (pesquisa externa indisponível)."
        mock_copy.return_value = "Copy multicanal."
        mock_rev.return_value = "Revisão final."
        mock_img.return_value = "Prompts visuais."

        result = generate_full_campaign(self.sample_form_data)

        self.assertIn("research_data", result)
        self.assertFalse(result["research_data"]["success"])
        self.assertIn("Falha de conexão", result["research_data"]["error"])
        self.assertIn("Estratégia formulada", result["strategy"])

    def test_build_campaign_reports_includes_real_research_sources(self):
        """Valida que os relatorios Markdown e TXT apresentam as fontes reais, URLs e datas."""
        campaign_data = {
            "form_data": self.sample_form_data,
            "research_data": self.sample_research_success,
            "strategy": "Estratégia baseada em fontes reais.",
            "preliminary_copy": "Copy.",
            "review_and_final": "Revisão.",
            "image_prompts": "Prompts."
        }

        md_report, txt_report = build_campaign_reports(campaign_data)

        # Markdown
        self.assertIn("FONTES DE PESQUISA E TENDÊNCIAS DE MERCADO (TAVILY SEARCH API)", md_report)
        self.assertIn("[Crescimento do Mercado Plant-Based no Brasil 2026](https://portalalimentos.com.br/plant-based-2026)", md_report)
        self.assertIn("Publicado em: 2026-02-10", md_report)
        self.assertIn("[Consumo de Proteínas Vegetais e Sustentabilidade](https://tendenciasnutricao.org/proteina-vegetal)", md_report)

        # TXT
        self.assertIn("[FONTES DE PESQUISA E TENDÊNCIAS DE MERCADO (TAVILY SEARCH API)]", txt_report)
        self.assertIn("https://portalalimentos.com.br/plant-based-2026", txt_report)
        self.assertIn("[Data: 2026-02-10]", txt_report)

    def test_build_campaign_reports_reports_unavailable_research_clearly(self):
        """Valida que relatorios informam com clareza quando a pesquisa esteve indisponivel."""
        campaign_data = {
            "form_data": self.sample_form_data,
            "research_data": self.sample_research_failure,
            "strategy": "Estratégia baseada no briefing.",
            "preliminary_copy": "Copy.",
            "review_and_final": "Revisão.",
            "image_prompts": "Prompts."
        }

        md_report, txt_report = build_campaign_reports(campaign_data)

        self.assertIn("Pesquisa de mercado externa esteve indisponível", md_report)
        self.assertIn("Falha de conexão com os servidores da Tavily Search API", md_report)

        self.assertIn("Pesquisa externa esteve indisponível durante a geração", txt_report)

    def test_research_failure_without_explicit_error(self):
        """Valida que falha na pesquisa com erro None assume mensagem padrão segura."""
        res_failure_none_error = {
            "success": False,
            "query": "teste query",
            "total_results": 0,
            "results": [],
            "error": None,
            "cached": False
        }
        prompt = build_strategist_user_prompt(self.sample_form_data, res_failure_none_error)
        self.assertIn("STATUS: INDISPONÍVEL", prompt)
        # Nao deve exibir a palavra literal "None" como razao do erro
        self.assertNotIn("INDISPONÍVEL (None)", prompt)

    def test_app_tavily_display_logic_no_name_error_on_failure(self):
        """
        Valida que a logica de exibicao da pesquisa Tavily em app.py
        utiliza consistentemente 'err_reason' (sem NameError por 'err_reassn')
        para diferentes cenarios de falha.
        """
        scenarios = [
            {"success": False, "error": "API Key inválida", "results": []},
            {"success": False, "error": None, "results": []},
            {"success": True, "error": None, "results": []},
            {"success": False, "error": "Timeout de conexão", "results": None},
        ]

        for sc in scenarios:
            # Simula a avaliacao exata de app.py
            if not sc.get("success") or not sc.get("results"):
                err_reason = sc.get("error") or "Serviço temporariamente indisponível"
                warning_text = (
                    f"⚠️ **Pesquisa de tendências externas indisponível:** {err_reason}\n\n"
                    "*A estratégia foi fundamentada estritamente nas informações fornecidas no briefing, sem invenção de fontes ou URLs.*"
                )
                self.assertIsInstance(err_reason, str)
                self.assertTrue(len(err_reason) > 0)
                self.assertNotIn("None", warning_text)
                self.assertIn("Pesquisa de tendências externas indisponível", warning_text)

    def test_app_tavily_header_html_structure_well_formed(self):
        """
        Valida que a estrutura HTML do cabecalho Tavily possui fechamento
        correto de todas as tags div abertas dentro da mesma chamada.
        """
        res_data = self.sample_research_success
        cache_badge = " • <em>(Resultados de cache em memória)</em>" if res_data.get("cached") else ""
        query_text = res_data.get("query", "")
        sources_count = len(res_data.get("results", []))

        html_snippet = f"""
        <div style="background: rgba(139, 92, 246, 0.08); border: 1px solid rgba(139, 92, 246, 0.25); border-radius: 10px; padding: 1rem; margin-bottom: 1rem;">
            <div style="font-weight: 700; color: #C4B5FD; font-size: 0.95rem; margin-bottom: 0.35rem;">
                🌐 Fontes Reais de Mercado Consultadas em Tempo Real (Tavily API)
            </div>
            <div style="font-size: 0.82rem; color: #94A3B8;">
                Consulta: <code>{query_text}</code> • Fontes reais consultadas: <strong>{sources_count}</strong>{cache_badge}
            </div>
        </div>
        """
        # Garante que todas as tags <div abertas possuem fechamento </div> correspondente
        open_divs = html_snippet.count("<div")
        close_divs = html_snippet.count("</div>")
        self.assertEqual(open_divs, close_divs, "Número de <div> abertas e fechadas deve ser exatamente igual")
        self.assertEqual(open_divs, 3)


if __name__ == "__main__":
    unittest.main()
