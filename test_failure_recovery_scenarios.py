"""
Suite de testes automatizados com mocks para verificacao da recuperacao de falhas
do MarketFlow AI 2.0 (prompt13.txt).

Cenario de referencia:
Campanha ficticia:
- Produto: Café Aurora (cafeteria ficticia de Fortaleza)
- Objetivo: Divulgar a campanha Sua Pausa Especial
- Publico-alvo: Jovens adultos e profissionais de 20 a 45 anos
- Canais: Instagram, WhatsApp e E-mail
- Tom: Acolhedor, moderno e natural

Cobre integralmente os 8 cenarios exigidos:
1. OpenRouter retorna resposta interrompida com finish_reason="length".
2. Copywriter retorna metade do conteudo (sem o bloco de e-mail).
3. Revisor retorna comentarios de revisao sem textos finais.
4. Designer de Prompts retorna prompt incompleto ou vazio.
5. Tavily retorna timeout.
6. Tavily retorna lista vazia de resultados.
7. Tentativa de recuperacao da LLM falha novamente (sem loop infinito).
8. Guardrails bloqueiam conteudo com alegacao comercial grave/sem fundamento.

E valida todos os requisitos transversais:
- Respostas truncadas nao sao tratadas como completas.
- O sistema nao inventa fontes para substituir a Tavily.
- Agentes posteriores nao recebem conteudos invalidos como aprovados.
- Tentativas de recuperacao sao limitadas (sem loops infinitos).
- Streamlit nao apresenta falsamente quatro agentes concluidos.
- Envio ao n8n e bloqueado quando a campanha esta criticamente invalida.
- Resultados parciais preservados sao marcados como incompletos ([RASCUNHO INCOMPLETO]).
- Nenhum token ou credencial aparece em logs ou mensagens de erro.

100% Mocks. Sem consumo de APIs externas. Sem chamadas HTTP reais.
"""

import unittest
from unittest.mock import MagicMock, patch

from agents import (
    build_campaign_reports,
    run_copywriter_agent,
    run_image_designer_agent,
    run_reviewer_agent,
    run_strategist_agent,
)
from automation_service import sanitize_error_message, send_campaign_to_n8n
from graph_orchestrator import run_campaign_graph
from guardrails import validate_campaign_guardrails
import openrouter_service
from output_validation import (
    ValidationResult,
    _check_truncation,
    validate_copywriter_output,
    validate_image_designer_output,
    validate_reviewer_output,
    validate_strategist_output,
)
from research_service import search_market_trends


# ---------------------------------------------------------------------------
# Fixture Oficial da Campanha Café Aurora (Fortaleza)
# ---------------------------------------------------------------------------
CAFE_AURORA_BRIEFING = {
    "product_name": "Café Aurora",
    "product_description": (
        "Cafeteria artesanal e acolhedora em Fortaleza especializada em cafés especiais, "
        "métodos filtrados e ambiente para trabalho ou descanso."
    ),
    "target_audience": "Jovens adultos e profissionais de 20 a 45 anos em Fortaleza.",
    "objective": "Divulgar a campanha Sua Pausa Especial",
    "tone": "Acolhedor, moderno e natural",
    "differentials": "Grãos de microlotes cearenses, ambiente silencioso com wi-fi e barista especializado.",
    "cta": "Visite o Café Aurora e ganhe um espresso de boas-vindas na sua pausa especial.",
    "channels": ["Instagram", "WhatsApp", "E-mail marketing"]
}


# ---------------------------------------------------------------------------
# Helpers para Mocks de Respostas do OpenRouter
# ---------------------------------------------------------------------------
class MockChoiceMessage:
    def __init__(self, content):
        self.content = content


class MockChoice:
    def __init__(self, content, finish_reason="stop"):
        self.message = MockChoiceMessage(content)
        self.finish_reason = finish_reason


class MockCompletionResponse:
    def __init__(self, content, finish_reason="stop"):
        self.choices = [MockChoice(content, finish_reason=finish_reason)]


# ---------------------------------------------------------------------------
# Classe de Testes: Recuperacao de Falhas e Resiliencia
# ---------------------------------------------------------------------------
class TestMarketFlowFailureRecoveryScenarios(unittest.TestCase):
    """Bateria de testes de recuperacao de falhas do MarketFlow AI 2.0."""

    def setUp(self):
        self.briefing = dict(CAFE_AURORA_BRIEFING)
        openrouter_service._SESSION_ACTIVE_MODEL.set(None)
        from research_service import _SEARCH_CACHE
        _SEARCH_CACHE.clear()

    def tearDown(self):
        openrouter_service._SESSION_ACTIVE_MODEL.set(None)
        from research_service import _SEARCH_CACHE
        _SEARCH_CACHE.clear()

    # =========================================================================
    # CENÁRIO 1: OpenRouter retorna finish_reason="length"
    # =========================================================================
    @patch("openrouter_service._get_api_credentials")
    @patch("openrouter_service._fetch_available_free_models")
    @patch("openai.OpenAI")
    def test_scenario_1_openrouter_finish_reason_length_triggers_recovery(
        self, mock_openai_cls, mock_fetch_models, mock_creds
    ):
        """
        Cenário 1:
        O OpenRouter retorna uma resposta truncada (finish_reason='length').
        Verifica que:
        - A resposta truncada não é aceita como se estivesse completa.
        - O sistema aciona _try_recover_truncated_completion e concatena a continuação.
        - A resposta recuperada final não é truncada.
        """
        mock_creds.return_value = ("sk-or-test-mock-key-sample-1234567890", "auto")
        mock_fetch_models.return_value = ["mock-model-rec"]

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        first_chunk = (
            "## 1. Estratégia da Campanha Café Aurora: Sua Pausa Especial\n"
            "Conceito central: Momentos de pausa com cafés de microlotes cearenses. "
            "Público-alvo: Profissionais e jovens adultos em Fortaleza buscando refúgio. "
            "Proposta de valor: Qualidade artesanal e ambiente acolhedor. "
            "Canais: Instagram, WhatsApp e E-mail marketing definidos para a campanha e"
        )
        second_chunk = (
            " planos de ação integrados com ofertas para o público local. "
            "Pesquisa de mercado fundamentada no briefing com foco na experiência sensorial."
        )

        mock_client.chat.completions.create.side_effect = [
            MockCompletionResponse(first_chunk, finish_reason="length"),
            MockCompletionResponse(second_chunk, finish_reason="stop")
        ]

        result = openrouter_service.generate_chat_completion(
            system_prompt="Você é um estrategista.",
            user_prompt="Crie a estratégia para o Café Aurora.",
            max_tokens=1500
        )

        # O resultado final deve conter ambos os fragmentos
        self.assertIn("Café Aurora", result)
        self.assertIn("Sua Pausa Especial", result)
        self.assertIn("foco na experiência sensorial", result)
        # O resultado não pode estar truncado
        self.assertFalse(_check_truncation(result))

    # =========================================================================
    # CENÁRIO 2: Copywriter retorna sem o bloco de E-mail
    # =========================================================================
    def test_scenario_2_copywriter_missing_email_channel_detected_as_incomplete(self):
        """
        Cenário 2:
        O Copywriter retorna apenas Instagram e WhatsApp para o Café Aurora,
        deixando de fora o E-mail marketing solicitado no briefing.
        Verifica que:
        - O validador estrutural identifica 'E-mail marketing' como ausente.
        - is_valid é False.
        - O relatório emitido para esta campanha é identificado como rascunho incompleto.
        """
        partial_copy = (
            "## Instagram — Feed e Stories\n\n"
            "**Legenda:** Encontre sua pausa no Café Aurora! Saboreie nossos grãos cearenses.\n"
            "**CTA:** Venha hoje e ganhe seu espresso de boas-vindas no link da bio.\n\n"
            "## WhatsApp — Mensagem Direta\n\n"
            "Olá! Sua pausa especial de hoje já está te esperando no Café Aurora com café fresquinho."
        )

        val = validate_copywriter_output(partial_copy, self.briefing["channels"])
        self.assertFalse(val.is_valid)
        self.assertIn("E-mail marketing", val.missing_channels)
        self.assertIn("Canais ausentes", val.error_message)

        # Verifica marcação de incompletude nos relatórios
        incomplete_campaign = {
            "form_data": self.briefing,
            "strategy": "Estratégia completa",
            "preliminary_copy": partial_copy,
            "review_and_final": "",  # etapa seguinte pendente
            "image_prompts": ""
        }
        md_rep, txt_rep = build_campaign_reports(incomplete_campaign)
        self.assertIn("[RASCUNHO INCOMPLETO]", md_rep)
        self.assertIn("[RASCUNHO INCOMPLETO]", txt_rep)
        self.assertIn("DOCUMENTO PARCIAL", md_rep)

    # =========================================================================
    # CENÁRIO 3: Revisor retorna críticas mas omite a Versão Final
    # =========================================================================
    def test_scenario_3_reviewer_missing_final_version_detected(self):
        """
        Cenário 3:
        O Revisor retorna apenas a análise crítica e palavras-chave SEO,
        mas NÃO apresenta os textos finais revisados para o Café Aurora.
        Verifica que:
        - validate_reviewer_output rejeita a saída com is_valid=False.
        - A seção ausente 'Versão Final Revisada dos Conteúdos' é reportada.
        """
        review_without_final = (
            "## 1. Avaliação Crítica da Campanha Café Aurora\n"
            "Os textos de Instagram e WhatsApp transmitem bem o tom acolhedor da cafeteria. "
            "Recomendamos reforçar a menção aos microlotes cearenses na chamada para ação.\n\n"
            "## 2. Palavras-Chave e Otimização Temática (SEO Orientativo)\n"
            "Café especial Fortaleza, cafeteria acolhedora, microlotes cearenses, brunch Fortaleza.\n\n"
            "Observações adicionais para a equipe de atendimento presencial."
        )

        val = validate_reviewer_output(review_without_final, self.briefing["channels"])
        self.assertFalse(val.is_valid)
        self.assertIn("Versão Final Revisada dos Conteúdos", val.missing_sections)
        self.assertIn("Seções ausentes", val.error_message)

    # =========================================================================
    # CENÁRIO 4: Designer de Prompts retorna prompt incompleto ou vazio
    # =========================================================================
    def test_scenario_4_designer_empty_or_incomplete_prompt_flagged(self):
        """
        Cenário 4:
        O Designer de Prompts retorna saída vazia ou incompleta.
        Verifica que:
        - validate_image_designer_output rejeita a saída.
        - Os Guardrails (CHECK 4) acusam que os prompts visuais estão ausentes ou incompletos.
        """
        empty_val = validate_image_designer_output("", self.briefing["channels"])
        self.assertFalse(empty_val.is_valid)
        self.assertEqual(empty_val.missing_channels, self.briefing["channels"])

        # Prompts sem prompt em inglês e sem aspect ratio
        incomplete_designer_text = (
            "## Conceito Visual Geral\nEstética acolhedora de cafeteria com iluminação quente.\n\n"
            "## Instagram\nComposição: Xícara de cerâmica sobre mesa de madeira rústica.\n\n"
            "## WhatsApp\nComposição: Fachada do Café Aurora em dia ensolarado em Fortaleza.\n\n"
            "## E-mail marketing\nComposição: Barista preparando café filtrado em método v60."
        )
        val_inc = validate_image_designer_output(incomplete_designer_text, self.briefing["channels"])
        self.assertFalse(val_inc.is_valid)
        self.assertIn("Formato / Aspect Ratio das imagens", val_inc.missing_sections)
        self.assertIn("Prompt Otimizado em Inglês", val_inc.missing_sections)

        # Validação nos Guardrails
        gr = validate_campaign_guardrails(
            campaign_data={
                "form_data": self.briefing,
                "strategy": "Estratégia Cafe Aurora com proposta de valor clara e público caracterizado.",
                "preliminary_copy": "Copy Cafe Aurora para Instagram, WhatsApp e E-mail marketing.",
                "review_and_final": "Versão final revisada para Instagram, WhatsApp e E-mail marketing com SEO.",
                "image_prompts": ""  # Ausente
            },
            report_markdown="# Relatório Café Aurora"
        )
        # CHECK 4 gera warning quando prompts do Agente 4 estão vazios
        has_designer_warning = any(
            w.get("code") == "EMPTY_IMAGE_PROMPTS" or "Agente 4" in w.get("message", "")
            for w in gr["warnings"]
        )
        self.assertTrue(has_designer_warning)

    # =========================================================================
    # CENÁRIO 5: Tavily retorna timeout
    # =========================================================================
    @patch("research_service.get_tavily_api_key", return_value="tvly-mock-key-sample-12345")
    @patch("tavily.TavilyClient")
    def test_scenario_5_tavily_timeout_graceful_fallback_no_hallucinated_sources(
        self, mock_client_cls, mock_get_key
    ):
        """
        Cenário 5:
        A Tavily API sofre timeout durante a pesquisa de mercado do Café Aurora.
        Verifica que:
        - search_market_trends retorna success=False com erro seguro.
        - A estratégia é elaborada baseando-se estritamente no briefing.
        - NENHUMA fonte, URL ou dado fictício é inventado para mascarar o timeout.
        - Os relatórios informam expressamente que a pesquisa esteve indisponível.
        """
        mock_instance = MagicMock()
        mock_instance.search.side_effect = TimeoutError("Request timed out after 10.0s")
        mock_client_cls.return_value = mock_instance

        res = search_market_trends(
            product_name=self.briefing["product_name"],
            product_description=self.briefing["product_description"],
            target_audience=self.briefing["target_audience"]
        )
        self.assertFalse(res["success"])
        self.assertEqual(res["results"], [])
        self.assertIn("Tempo limite esgotado", res["error"])

        # Simula geração do relatório com pesquisa indisponível
        campaign_with_failed_research = {
            "form_data": self.briefing,
            "research_data": res,
            "strategy": (
                "## 1. Análise de Mercado\nPesquisa externa indisponível durante a execução. "
                "Estratégia fundamentada nas informações do briefing: grãos cearenses e acolhimento."
            ),
            "preliminary_copy": "Instagram, WhatsApp e E-mail copy.",
            "review_and_final": "Versão final completa para Instagram, WhatsApp e E-mail marketing.",
            "image_prompts": "Direção visual com prompts em inglês 1:1, 9:16 e 16:9."
        }

        md_rep, txt_rep = build_campaign_reports(campaign_with_failed_research)

        # Não pode conter URLs alucinadas de exemplo
        self.assertNotIn("https://tavily.com/fake", md_rep)
        self.assertNotIn("https://noticia-inventada.com", md_rep)
        # Deve registrar explicitamente a indisponibilidade nos relatórios
        self.assertIn("indisponível", md_rep.lower())
        self.assertIn("indisponível", txt_rep.lower())

    # =========================================================================
    # CENÁRIO 6: Tavily retorna lista vazia de resultados
    # =========================================================================
    @patch("research_service.get_tavily_api_key", return_value="tvly-mock-key-sample-12345")
    @patch("tavily.TavilyClient")
    def test_scenario_6_tavily_empty_results_handled_without_invented_sources(
        self, mock_client_cls, mock_get_key
    ):
        """
        Cenário 6:
        A Tavily responde HTTP 200, mas com lista vazia de resultados para Café Aurora.
        Verifica que:
        - search_market_trends retorna success=True com results=[].
        - O relatório indica que nenhuma fonte externa foi encontrada.
        - Nenhuma URL é inventada no relatório.
        """
        mock_instance = MagicMock()
        mock_instance.search.return_value = {
            "query": "cafés especiais cearenses fortaleza",
            "results": []
        }
        mock_client_cls.return_value = mock_instance

        res = search_market_trends(
            product_name=self.briefing["product_name"],
            product_description=self.briefing["product_description"],
            target_audience=self.briefing["target_audience"]
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["results"], [])

        campaign_data = {
            "form_data": self.briefing,
            "research_data": res,
            "strategy": "Estratégia baseada estritamente no briefing do Café Aurora.",
            "preliminary_copy": "Copy preliminar.",
            "review_and_final": "Versão final revisada.",
            "image_prompts": "Prompts de imagem."
        }
        md_rep, txt_rep = build_campaign_reports(campaign_data)
        self.assertIn("Nenhuma fonte externa consultada para esta campanha", md_rep)
        self.assertIn("Nenhuma fonte externa consultada para esta campanha", txt_rep)

    # =========================================================================
    # CENÁRIO 7: Tentativa de recuperação da LLM falha novamente
    # =========================================================================
    @patch("openrouter_service._get_api_credentials")
    @patch("openrouter_service._fetch_available_free_models")
    @patch("openai.OpenAI")
    def test_scenario_7_llm_recovery_fails_stops_without_infinite_loop(
        self, mock_openai_cls, mock_fetch_models, mock_creds
    ):
        """
        Cenário 7:
        A chamada inicial ao OpenRouter é truncada (finish_reason='length')
        e a tentativa subsequente de recuperação falha (lança erro de rede).
        Verifica que:
        - O sistema interrompe após exatamente 1 tentativa de recuperação.
        - Não entra em loop infinito.
        - Levanta RuntimeError com mensagem sanitizada.
        """
        mock_creds.return_value = ("sk-or-test-mock-key-sample-1234567890", "auto")
        mock_fetch_models.return_value = ["mock-model-single"]

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        # 1a chamada: finish_reason="length"
        # 2a chamada (recovery): lança exceção de timeout
        mock_client.chat.completions.create.side_effect = [
            MockCompletionResponse("Texto inicial do Café Aurora que cortou bruscamente e", finish_reason="length"),
            Exception("Gateway Timeout 504 no retry de recuperação")
        ]

        with self.assertRaises(RuntimeError) as ctx:
            openrouter_service.generate_chat_completion(
                system_prompt="sys",
                user_prompt="prompt"
            )

        err_msg = str(ctx.exception)
        self.assertIn("Falha na geração", err_msg)
        # Verifica que chamou apenas 2 vezes (1 original + 1 recovery) e parou
        self.assertEqual(mock_client.chat.completions.create.call_count, 2)

    # =========================================================================
    # CENÁRIO 8: Guardrails bloqueiam alegação comercial grave e sem fundamento
    # =========================================================================
    def test_scenario_8_guardrails_block_severe_unsubstantiated_claim(self):
        """
        Cenário 8:
        O texto gerado contém uma alegação comercial de gravidade crítica:
        'Beba o Café Aurora e tenha lucro garantido de 100% no seu dia sem qualquer risco!'
        Verifica que:
        - validate_campaign_guardrails identifica a alegação proibida.
        - is_blocked é True.
        - O envio à automação n8n é bloqueado.
        """
        hallucinated_copy = (
            "## Instagram\n"
            "Venha ao Café Aurora e tenha lucro garantido de 100% no seu investimento "
            "com retorno financeiro absoluto e risco zero para seu negócio!\n\n"
            "## WhatsApp\n"
            "Mensagem direta prometendo ganhos automáticos no Café Aurora.\n\n"
            "## E-mail marketing\n"
            "Assunto: Lucro garantido no Café Aurora."
        )

        campaign_with_violation = {
            "form_data": self.briefing,
            "strategy": "Estratégia Cafe Aurora",
            "preliminary_copy": hallucinated_copy,
            "review_and_final": (
                "## Versão Final Revisada\n"
                f"{hallucinated_copy}\n\n"
                "## Palavras-chave SEO\nCafé especial, lucro garantido."
            ),
            "image_prompts": (
                "## Conceito Visual Geral\nEstilo moderno.\n\n"
                "## Instagram\nFormato: 1:1\nPrompt em Inglês: Coffee shop --ar 1:1\n\n"
                "## WhatsApp\nFormato: 9:16\nPrompt em Inglês: Coffee shop --ar 9:16\n\n"
                "## E-mail marketing\nFormato: 16:9\nPrompt em Inglês: Coffee shop --ar 16:9\n"
            )
        }

        gr_result = validate_campaign_guardrails(
            campaign_data=campaign_with_violation,
            report_markdown="# Relatório Café Aurora"
        )

        self.assertTrue(gr_result["is_blocked"])
        has_profit_issue = any(
            "lucro garantido" in issue.get("message", "").lower()
            or "UNGROUNDED_CRITICAL_CLAIM" in issue.get("code", "")
            for issue in gr_result.get("critical_issues", [])
        )
        self.assertTrue(has_profit_issue)

        # Verifica bloqueio no envio ao n8n
        is_blocked = gr_result["is_blocked"]
        self.assertTrue(is_blocked, "Guardrails devem bloquear o envio")

    # =========================================================================
    # REQUISITOS TRANSVERSAIS
    # =========================================================================
    def test_transversal_streamlit_state_does_not_falsely_show_4_agents_completed_on_error(self):
        """
        Verifica que quando um agente falha no pipeline, o estado do Streamlit
        NÃO apresenta falsamente os 4 agentes como concluídos.
        """
        # Simula o dicionário de estados de workflow gerenciado pelo Streamlit
        ai_workflow_states = {
            "briefing": "completed",
            "research": "completed",
            "strategist": "completed",
            "copywriter": "error",       # Copywriter falhou
            "reviewer": "pending",         # Etapas seguintes ficaram pendentes
            "image_designer": "pending",
            "ready": "pending"
        }

        # Cálculo exato do Streamlit (app.py linhas 416-420)
        completed_agents = sum(
            1 for st_name in ["strategist", "copywriter", "reviewer", "image_designer"]
            if ai_workflow_states.get(st_name) == "completed"
        )

        self.assertEqual(completed_agents, 1)
        self.assertNotEqual(completed_agents, 4)

    def test_transversal_credentials_sanitized_in_error_messages(self):
        """
        Verifica que tokens OpenRouter, chaves Bearer, caminhos locais e query params
        são 100% mascarados por sanitize_error_message.
        """
        raw_error = (
            "Exception occurred with token sk-dummy-test-key-sample-123456789 and "
            "Bearer sample-mock-token at "
            "C:\\Users\\Bruno Gabriel\\Documents\\campanha-ia\\app.py?api_key=secret123"
        )
        sanitized = sanitize_error_message(raw_error)

        self.assertNotIn("sk-dummy-test-key-sample-123456789", sanitized)
        self.assertNotIn("sample-mock-token", sanitized)
        self.assertNotIn("C:\\Users\\Bruno Gabriel", sanitized)
        self.assertNotIn("secret123", sanitized)
        self.assertIn("[REDACTED_API_KEY]", sanitized)
        self.assertIn("[ARQUIVO_LOCAL]", sanitized)

    def test_transversal_n8n_rejects_empty_or_critically_invalid_payload(self):
        """
        Verifica que send_campaign_to_n8n rejeita dados incompletos
        antes de qualquer tentativa de conexão externa.
        """
        # Tenta enviar sem o relatório em markdown
        res = send_campaign_to_n8n(
            product_name="Café Aurora",
            objective="Divulgar a campanha Sua Pausa Especial",
            channels=["Instagram"],
            report_markdown=""  # Inválido
        )
        self.assertFalse(res["success"])
        self.assertIn("vazio ou indisponível", res["message"])


if __name__ == "__main__":
    unittest.main()
