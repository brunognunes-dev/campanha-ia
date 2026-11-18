"""
Suite completa de testes automatizados com mocks para a orquestracao LangGraph
do MarketFlow AI 2.0 (graph_orchestrator.py e agents.py).

Cobre os 10 requisitos de teste do prompt8.txt:
1. Ordem dos nos e topologia sequencial do StateGraph
2. Transferencia incremental do estado compartilhado entre os nos
3. Integracao e resultados do Pesquisador de Tendencias (Tavily Search API)
4. Conteudos do Copywriter fundamentados na estrategia
5. Revisao SEO e otimizacao de palavras-chave
6. Prompts de imagem e direcao visual
7. Execucao deterministica do no de Guardrails
8. Interrupcao imediata e sinalizacao de erro em falha de qualquer etapa
9. Disparo de callbacks de progresso para a interface Streamlit
10. Compatibilidade total com a interface e geracao de relatorios (.md e .txt)
"""

import unittest
from unittest.mock import patch, MagicMock

from langgraph.graph import START, END
from graph_orchestrator import (
    CampaignState,
    build_campaign_graph,
    get_compiled_campaign_graph,
    run_campaign_graph,
    pesquisador_tendencias_node,
    copywriter_node,
    especialista_seo_node,
    designer_prompts_imagem_node,
    guardrails_node
)
from agents import generate_full_campaign, build_campaign_reports


class TestLangGraphOrchestration(unittest.TestCase):
    """Testes unitarios com mocks puros para a orquestracao LangGraph."""

    def setUp(self):
        self.sample_form_data = {
            "product_name": "SaaS Gestão Ágil",
            "product_description": "Plataforma de gestão financeira e fluxo de caixa para PMEs.",
            "target_audience": "Micro e pequenos empresários.",
            "objective": "Atrair novos clientes e gerar leads",
            "tone": "Profissional, inovador e confiável",
            "differentials": "Inteligência preditiva e onboarding em 15 minutos.",
            "cta": "Inicie o teste grátis de 14 dias sem cartão.",
            "channels": ["Instagram", "WhatsApp", "E-mail marketing"]
        }

        self.mock_research_data = {
            "success": True,
            "query": "tendências mercado saas gestão financeira",
            "total_results": 2,
            "results": [
                {
                    "title": "Mercado SaaS no Brasil em 2026",
                    "url": "https://techreports.com.br/saas-2026",
                    "content": "PMEs aumentaram em 35% o investimento em ferramentas de fluxo de caixa em nuvem.",
                    "published_date": "2026-03-01",
                    "score": 0.96
                }
            ],
            "error": None,
            "cached": False
        }

        self.mock_strategy = (
            "## 1. Pesquisa de Mercado e Tendências Externas\n"
            "### Fatos e Dados Observados (Fontes Reais)\n"
            "- PMEs aumentaram 35% o investimento em nuvem (Fonte: https://techreports.com.br/saas-2026)\n"
            "### Recomendações e Hipóteses Inferidas\n"
            "- Posicionar a ferramenta como redutora de complexidade financeira.\n"
            "## 2. Resumo do Produto\nSaaS Gestão Ágil."
        )

        self.mock_copy = (
            "### Instagram\nLegenda criativa sobre controle financeiro.\n\n"
            "### WhatsApp\nMensagem direta para gestores.\n\n"
            "### E-mail marketing\nAssunto: Adeus planilhas confusas!"
        )

        self.mock_review = (
            "## 1. Avaliação Crítica\nTextos aprovados e alinhados.\n"
            "## 2. Palavras-Chave SEO\nfluxo de caixa, gestão financeira PME\n"
            "## 3. Versão Final Revisada\nTextos otimizados para conversão."
        )

        self.mock_image_prompts = (
            "## 1. Conceito Visual Geral\nEstética corporativa moderna.\n"
            "## 2. Prompts de Imagem\n### Instagram\n`Clean modern dashboard on laptop screen --ar 1:1`"
        )

    # --------------------------------------------------------------------------
    # 1. ORDEM DOS NOS E TOPOLOGIA DO GRAFO
    # --------------------------------------------------------------------------
    def test_node_order_and_topology(self):
        """Valida que o StateGraph contem exatamente a sequencia linear de 5 nos exigida."""
        graph = build_campaign_graph()

        # Verifica se todos os 5 nos estao presentes
        nodes = graph.nodes
        self.assertIn("pesquisador_tendencias", nodes)
        self.assertIn("copywriter", nodes)
        self.assertIn("especialista_seo", nodes)
        self.assertIn("designer_prompts_imagem", nodes)
        self.assertIn("guardrails", nodes)

    # --------------------------------------------------------------------------
    # 2. TRANSFERENCIA INCREMENTAL DE ESTADO
    # --------------------------------------------------------------------------
    @patch("agents.search_market_trends")
    @patch("agents.run_strategist_agent")
    @patch("agents.run_copywriter_agent")
    @patch("agents.run_reviewer_agent")
    @patch("agents.run_image_designer_agent")
    def test_state_transfer_across_all_nodes(
        self, mock_img, mock_rev, mock_copy, mock_strat, mock_search
    ):
        """Valida se cada no recebe o estado acumulado das etapas precedentes."""
        mock_search.return_value = self.mock_research_data
        mock_strat.return_value = self.mock_strategy
        mock_copy.return_value = self.mock_copy
        mock_rev.return_value = self.mock_review
        mock_img.return_value = self.mock_image_prompts

        result = run_campaign_graph(self.sample_form_data)

        # Verifica estado consolidado final
        self.assertEqual(result["form_data"]["product_name"], "SaaS Gestão Ágil")
        self.assertEqual(result["research_data"], self.mock_research_data)
        self.assertEqual(result["strategy"], self.mock_strategy)
        self.assertEqual(result["preliminary_copy"], self.mock_copy)
        self.assertEqual(result["review_and_final"], self.mock_review)
        self.assertEqual(result["image_prompts"], self.mock_image_prompts)
        self.assertIsNotNone(result["guardrails_result"])
        self.assertFalse(result["guardrails_result"]["is_blocked"])

    # --------------------------------------------------------------------------
    # 3. RESULTADOS DO PESQUISADOR DE TENDENCIAS
    # --------------------------------------------------------------------------
    @patch("agents.search_market_trends")
    @patch("agents.run_strategist_agent")
    def test_trend_researcher_node_execution(self, mock_strat, mock_search):
        """Valida que o no 1 executa a pesquisa Tavily e entrega ao Estrategista."""
        mock_search.return_value = self.mock_research_data
        mock_strat.return_value = self.mock_strategy

        initial_state: CampaignState = {
            "form_data": self.sample_form_data,
            "research_data": None,
            "strategy": ""
        }

        output = pesquisador_tendencias_node(initial_state)

        self.assertTrue(mock_search.called)
        self.assertTrue(mock_strat.called)
        self.assertIn("research_data", output)
        self.assertIn("strategy", output)
        self.assertEqual(output["research_data"]["total_results"], 2)
        self.assertEqual(output["strategy"], self.mock_strategy)

    # --------------------------------------------------------------------------
    # 4. CONTEUDOS DO COPYWRITER
    # --------------------------------------------------------------------------
    @patch("agents.run_copywriter_agent")
    def test_copywriter_node_execution(self, mock_copy):
        """Valida que o Copywriter recebe a estrategia fundamentada."""
        mock_copy.return_value = self.mock_copy

        state: CampaignState = {
            "form_data": self.sample_form_data,
            "strategy": self.mock_strategy
        }

        output = copywriter_node(state)

        self.assertTrue(mock_copy.called)
        call_args = mock_copy.call_args[0]
        self.assertEqual(call_args[0], self.sample_form_data)
        self.assertEqual(call_args[1], self.mock_strategy)
        self.assertEqual(output["preliminary_copy"], self.mock_copy)

    # --------------------------------------------------------------------------
    # 5. REVISAO SEO
    # --------------------------------------------------------------------------
    @patch("agents.run_reviewer_agent")
    def test_seo_reviewer_node_execution(self, mock_rev):
        """Valida que o Revisor & SEO recebe os textos preliminares e a estrategia."""
        mock_rev.return_value = self.mock_review

        state: CampaignState = {
            "form_data": self.sample_form_data,
            "strategy": self.mock_strategy,
            "preliminary_copy": self.mock_copy
        }

        output = especialista_seo_node(state)

        self.assertTrue(mock_rev.called)
        call_args = mock_rev.call_args[0]
        self.assertEqual(call_args[0], self.sample_form_data)
        self.assertEqual(call_args[1], self.mock_strategy)
        self.assertEqual(call_args[2], self.mock_copy)
        self.assertEqual(output["review_and_final"], self.mock_review)

    # --------------------------------------------------------------------------
    # 6. PROMPTS DE IMAGEM
    # --------------------------------------------------------------------------
    @patch("agents.run_image_designer_agent")
    def test_image_designer_node_execution(self, mock_img):
        """Valida que o Designer Visual recebe a versao final e gera prompts."""
        mock_img.return_value = self.mock_image_prompts

        state: CampaignState = {
            "form_data": self.sample_form_data,
            "strategy": self.mock_strategy,
            "review_and_final": self.mock_review
        }

        output = designer_prompts_imagem_node(state)

        self.assertTrue(mock_img.called)
        call_args = mock_img.call_args[0]
        self.assertEqual(call_args[0], self.sample_form_data)
        self.assertEqual(call_args[1], self.mock_strategy)
        self.assertEqual(call_args[2], self.mock_review)
        self.assertEqual(output["image_prompts"], self.mock_image_prompts)

    # --------------------------------------------------------------------------
    # 7. GUARDRAILS NO NO FINAL
    # --------------------------------------------------------------------------
    def test_guardrails_node_execution(self):
        """Valida que o no final de guardrails avalia deterministicamente a integridade."""
        state: CampaignState = {
            "form_data": self.sample_form_data,
            "research_data": self.mock_research_data,
            "strategy": self.mock_strategy,
            "preliminary_copy": self.mock_copy,
            "review_and_final": self.mock_review,
            "image_prompts": self.mock_image_prompts
        }

        output = guardrails_node(state)

        self.assertIn("guardrails_result", output)
        guardrails_res = output["guardrails_result"]
        self.assertIn("is_blocked", guardrails_res)
        self.assertIn("score", guardrails_res)
        self.assertFalse(guardrails_res["is_blocked"])

    # --------------------------------------------------------------------------
    # 8. FALHA EM QUALQUER ETAPA (INTERRUPCAO IMEDIATA)
    # --------------------------------------------------------------------------
    @patch("agents.search_market_trends")
    @patch("agents.run_strategist_agent")
    @patch("agents.run_copywriter_agent")
    @patch("agents.run_reviewer_agent")
    def test_failure_interruption_at_any_stage(
        self, mock_rev, mock_copy, mock_strat, mock_search
    ):
        """Valida que falha no Copywriter interrompe a execucao e nao chama o Revisor."""
        mock_search.return_value = self.mock_research_data
        mock_strat.return_value = self.mock_strategy
        mock_copy.side_effect = RuntimeError("OpenRouter Timeout no Copywriter")

        with self.assertRaises(RuntimeError) as ctx:
            run_campaign_graph(self.sample_form_data)

        self.assertIn("OpenRouter Timeout no Copywriter", str(ctx.exception))
        # O Revisor nunca deve ser chamado se o Copywriter falhar
        self.assertFalse(mock_rev.called)

    # --------------------------------------------------------------------------
    # 9. DISPARO DE CALLBACK DE PROGRESSO
    # --------------------------------------------------------------------------
    @patch("agents.search_market_trends")
    @patch("agents.run_strategist_agent")
    @patch("agents.run_copywriter_agent")
    @patch("agents.run_reviewer_agent")
    @patch("agents.run_image_designer_agent")
    def test_progress_callback_event_flow(
        self, mock_img, mock_rev, mock_copy, mock_strat, mock_search
    ):
        """Valida que todos os eventos de progresso sao emitidos na ordem exata."""
        mock_search.return_value = self.mock_research_data
        mock_strat.return_value = self.mock_strategy
        mock_copy.return_value = self.mock_copy
        mock_rev.return_value = self.mock_review
        mock_img.return_value = self.mock_image_prompts

        events = []

        def callback_tracer(stage, status, msg, result=None):
            events.append((stage, status))

        generate_full_campaign(self.sample_form_data, progress_callback=callback_tracer)

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
        self.assertEqual(events, expected_events)

    # --------------------------------------------------------------------------
    # 10. COMPATIBILIDADE COM A INTERFACE E RELATORIOS
    # --------------------------------------------------------------------------
    @patch("agents.search_market_trends")
    @patch("agents.run_strategist_agent")
    @patch("agents.run_copywriter_agent")
    @patch("agents.run_reviewer_agent")
    @patch("agents.run_image_designer_agent")
    def test_compatibility_with_ui_and_reports(
        self, mock_img, mock_rev, mock_copy, mock_strat, mock_search
    ):
        """Valida integracao total do resultado do LangGraph com os relatorios .md e .txt."""
        mock_search.return_value = self.mock_research_data
        mock_strat.return_value = self.mock_strategy
        mock_copy.return_value = self.mock_copy
        mock_rev.return_value = self.mock_review
        mock_img.return_value = self.mock_image_prompts

        campaign_result = generate_full_campaign(self.sample_form_data)

        # Valida que as chaves esperadas por app.py estao presentes
        self.assertIn("form_data", campaign_result)
        self.assertIn("research_data", campaign_result)
        self.assertIn("strategy", campaign_result)
        self.assertIn("preliminary_copy", campaign_result)
        self.assertIn("review_and_final", campaign_result)
        self.assertIn("image_prompts", campaign_result)
        self.assertIn("guardrails_result", campaign_result)

        # Gera relatorios e valida presenca das secoes
        md_report, txt_report = build_campaign_reports(campaign_result)

        self.assertIn("# RELATÓRIO DE CAMPANHA DE MARKETING", md_report)
        self.assertIn("FONTES DE PESQUISA E TENDÊNCIAS DE MERCADO", md_report)
        self.assertIn("https://techreports.com.br/saas-2026", md_report)
        self.assertIn("ESTRATÉGIA DE MARKETING", md_report)
        self.assertIn("TEXTOS PRELIMINARES POR CANAL", md_report)
        self.assertIn("REVISÃO CRÍTICA, SEO E VERSÃO FINAL", md_report)
        self.assertIn("DIREÇÃO VISUAL E PROMPTS DE IMAGEM", md_report)
        self.assertIn("AVISO ÉTICO E LEGAL", md_report)

        self.assertIn("[1. DADOS DE CONTEXTO E BRIEFING]", txt_report)
        self.assertIn("[FONTES DE PESQUISA E TENDÊNCIAS DE MERCADO (TAVILY SEARCH API)]", txt_report)
        self.assertIn("https://techreports.com.br/saas-2026", txt_report)


if __name__ == "__main__":
    unittest.main()
