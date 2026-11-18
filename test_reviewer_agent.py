"""
Suite de testes automatizados com mocks para validacao da correcao do Agente 3
(Revisor SEO e Entrega de Textos Finais) — prompt14.txt.

Cenários cobertos (100% mocked, sem consumo de APIs externas):
1. Revisor entrega apenas diagnostico, sem textos finais: REPROVAR.
2. Revisor entrega Instagram, mas omite WhatsApp e E-mail: REPROVAR.
3. Revisor entrega canais, mas o corpo do E-mail esta vazio: REPROVAR / ALERTA CRITICO.
4. Revisor utiliza placeholders como '[inserir texto]' ou '[reescrever aqui]': REPROVAR.
5. Revisor entrega diagnostico e textos finais completos para todos os canais: APROVAR.
6. Revisor produz uma resposta truncada: REPROVAR / DETECTAR TRUNCAMENTO.
7. Agente 4 recebe corretamente o material final revisado.
8. Relatorios Markdown e TXT incluem os textos finais.
9. Falha de revisao impede que o pipeline apresente sucesso irrestrito.
"""

import unittest
from unittest.mock import MagicMock, patch

from agents import (
    build_campaign_reports,
    run_image_designer_agent,
    run_reviewer_agent,
)
from graph_orchestrator import (
    designer_prompts_imagem_node,
    especialista_seo_node,
)
from output_validation import (
    ValidationResult,
    _check_truncation,
    validate_reviewer_output,
)


class TestReviewerAgentDelivery(unittest.TestCase):
    """Testes com mocks para o Agente 3 — Revisor e Otimizador de Textos Finais."""

    def setUp(self):
        self.sample_form_data = {
            "product_name": "Café Aurora",
            "product_description": "Cafeteria artesanal em Fortaleza com grãos de microlotes cearenses.",
            "target_audience": "Jovens adultos e profissionais de 20 a 45 anos em Fortaleza.",
            "objective": "Divulgar a campanha Sua Pausa Especial",
            "tone": "Acolhedor, moderno e natural",
            "differentials": "Grãos de microlotes cearenses e ambiente acolhedor.",
            "cta": "Visite o Café Aurora e ganhe um espresso de boas-vindas.",
            "channels": ["Instagram", "WhatsApp", "E-mail marketing"]
        }
        self.sample_strategy = (
            "## 1. Pesquisa de Mercado\nPesquisa com grãos de microlotes.\n\n"
            "## 2. Mensagem Central\nSua Pausa Especial no Café Aurora.\n\n"
            "## 3. Proposta de Valor\nCafé artesanal cearense com acolhimento."
        )
        self.sample_copy = (
            "## Instagram\nLegenda preliminar para o feed do Café Aurora.\n\n"
            "## WhatsApp\nMensagem preliminar para clientes.\n\n"
            "## E-mail marketing\nAssunto: Sua pausa especial no Café Aurora."
        )

        # Exemplo de saída COMPLETA E VÁLIDA do Revisor
        self.valid_full_review = (
            "## 1. Diagnóstico de Revisão e Otimização SEO\n"
            "- **Problemas Identificados e Ajustes Aplicados:** Ajustado tom para maior proximidade, "
            "eliminadas redundâncias e reforçado o benefício dos grãos cearenses.\n"
            "- **Melhorias de Persuasão e CTA:** Criadas chamadas diretas com convite irresistível para a pausa do dia.\n"
            "- **Palavras-Chave e Otimização Temática (SEO Orientativo):** Café especial Fortaleza, "
            "cafeteria acolhedora, microlotes cearenses, pausa para o café.\n"
            "- **Aviso Ético e Legal:** *A análise de SEO possui caráter estritamente orientativo e não garante resultados comerciais.*\n\n"
            "## 2. Versões Finais Corrigidas dos Conteúdos\n\n"
            "### Instagram — Versão Final Pronta para Uso\n"
            "- **Gancho:** O seu dia pede mais que um café rápido: pede uma pausa especial.\n"
            "- **Legenda Completa:** No Café Aurora, cada xícara é preparada com grãos selecionados de "
            "microlotes cearenses e torra fresca. Um espaço pensado para você desacelerar, respirar e saborear o momento.\n"
            "- **Chamada para Ação (CTA):** Venha nos visitar hoje e ganhe um espresso de boas-vindas na sua primeira pausa. Link na bio!\n"
            "- **Hashtags:** #CafeAurora #CafesEspeciaisFortaleza #SuaPausaEspecial #Fortaleza\n\n"
            "### WhatsApp — Versão Final Pronta para Uso\n"
            "- **Mensagem Completa:** Olá! Que tal transformar o seu intervalo em um momento inesquecível? "
            "O Café Aurora preparou grãos cearenses premiados esperando por você hoje.\n"
            "- **Chamada para Ação (CTA):** Responda esta mensagem com 'QUERO MEU ESPRESSO' e garanta seu café de boas-vindas na visita!\n\n"
            "### E-mail marketing — Versão Final Pronta para Uso\n"
            "- **Assunto:** Sua pausa especial tem aroma de café fresco em Fortaleza ☕\n"
            "- **Preheader:** Conheça os microlotes cearenses e ganhe um espresso de boas-vindas.\n"
            "- **Saudação:** Olá, tudo bem?\n"
            "- **Corpo do E-mail:** Na correria da semana, encontrar um refúgio acolhedor faz toda a diferença. "
            "Criamos o Café Aurora para ser o seu ponto de paz no coração de Fortaleza, com métodos filtrados artesanais, "
            "ambiente tranquilo e grãos premiados da nossa serra.\n"
            "- **Chamada para Ação (CTA):** Clique aqui para agendar sua visita e resgatar seu presente especial.\n"
            "- **Encerramento:** Esperamos por você com o café pronto. Equipe Café Aurora."
        )

    # -------------------------------------------------------------------------
    # 1. Revisor entrega apenas diagnostico, sem textos finais: REPROVAR
    # -------------------------------------------------------------------------
    def test_reviewer_only_diagnosis_no_final_texts_rejected(self):
        """Valida que entregar apenas analise e diagnostico sem a secao de textos finais e REPROVADO."""
        only_diagnosis = (
            "## 1. Diagnóstico de Revisão e Otimização SEO\n"
            "- **Problemas Identificados:** O texto do Instagram precisa de uma chamada mais clara. "
            "O WhatsApp está muito formal para o público jovem. O E-mail precisa de preheader.\n"
            "- **Melhorias de Persuasão:** Sugiro fortalecer a oferta do espresso gratuito.\n"
            "- **Palavras-Chave SEO:** Cafés especiais, Fortaleza, café artesanal.\n\n"
            "Recomendo que o time aplique as mudanças acima nas peças de comunicação."
        )
        val = validate_reviewer_output(only_diagnosis, self.sample_form_data["channels"])
        self.assertFalse(val.is_valid)
        self.assertIn("Versão Final Revisada dos Conteúdos", val.missing_sections)

    # -------------------------------------------------------------------------
    # 2. Revisor entrega Instagram, mas omite WhatsApp e E-mail: REPROVAR
    # -------------------------------------------------------------------------
    def test_reviewer_omits_channels_in_final_version_rejected(self):
        """Valida que entregar apenas parte dos canais solicitados na versao final e REPROVADO."""
        partial_channels = (
            "## 1. Diagnóstico de Revisão\n"
            "Ajustes aplicados e otimização temática SEO com foco no público de Fortaleza.\n\n"
            "## 2. Versões Finais Corrigidas dos Conteúdos\n\n"
            "### Instagram — Versão Final Pronta para Uso\n"
            "- **Gancho:** Sua pausa especial começa aqui.\n"
            "- **Legenda Completa:** Venha saborear os melhores cafés artesanais de Fortaleza.\n"
            "- **Chamada para Ação (CTA):** Visite nosso espaço hoje e clique no link na bio!\n"
            "- **Hashtags:** #CafeAurora #Fortaleza"
            # WhatsApp e E-mail ausentes
        )
        val = validate_reviewer_output(partial_channels, self.sample_form_data["channels"])
        self.assertFalse(val.is_valid)
        self.assertIn("WhatsApp", val.missing_channels)
        self.assertIn("E-mail marketing", val.missing_channels)

    # -------------------------------------------------------------------------
    # 3. Revisor entrega canais, mas o corpo do E-mail esta vazio: REPROVAR
    # -------------------------------------------------------------------------
    def test_reviewer_empty_email_body_flagged(self):
        """Valida que versao final de e-mail sem corpo ou sem assunto gera reprovacao."""
        review_empty_email = (
            "## 1. Diagnóstico de Revisão\n"
            "Ajustes realizados e palavras-chave SEO definidas.\n\n"
            "## 2. Versões Finais Corrigidas dos Conteúdos\n\n"
            "### Instagram\nLegenda completa e CTA: Link na bio!\n\n"
            "### WhatsApp\nMensagem completa e CTA: Responda aqui!\n\n"
            "### E-mail marketing\n"
            # Sem linha de assunto e sem corpo estruturado
            "Configurações para envio por newsletter."
        )
        val = validate_reviewer_output(review_empty_email, self.sample_form_data["channels"])
        self.assertFalse(val.is_valid)
        self.assertIn("E-mail marketing", val.missing_channels)

    # -------------------------------------------------------------------------
    # 4. Revisor utiliza placeholders: REPROVAR
    # -------------------------------------------------------------------------
    def test_reviewer_with_placeholders_rejected(self):
        """Valida que utilizar placeholders como '[inserir texto]' ou '[reescrever aqui]' e REPROVADO."""
        review_with_placeholder = (
            "## 1. Diagnóstico de Revisão\n"
            "Ajustes aplicados e termos SEO levantados.\n\n"
            "## 2. Versões Finais Corrigidas dos Conteúdos\n\n"
            "### Instagram\nLegenda: Descubra o Café Aurora. CTA: link na bio.\n\n"
            "### WhatsApp\nMensagem: Olá! [reescrever aqui com oferta de espresso]. CTA: responda.\n\n"
            "### E-mail marketing\nAssunto: Café especial.\nCorpo: [inserir texto do e-mail com detalhes]."
        )
        val = validate_reviewer_output(review_with_placeholder, self.sample_form_data["channels"])
        self.assertFalse(val.is_valid)
        self.assertTrue(any("placeholders" in s.lower() for s in val.missing_sections))

    # -------------------------------------------------------------------------
    # 5. Revisor entrega diagnostico e textos finais completos: APROVAR
    # -------------------------------------------------------------------------
    def test_reviewer_complete_diagnosis_and_all_channels_accepted(self):
        """Valida que a entrega completa com diagnostico, SEO e versoes finais de todos os canais e APROVADA."""
        val = validate_reviewer_output(self.valid_full_review, self.sample_form_data["channels"])
        self.assertTrue(val.is_valid)
        self.assertEqual(val.missing_sections, [])
        self.assertEqual(val.missing_channels, [])
        self.assertFalse(val.is_truncated)

    # -------------------------------------------------------------------------
    # 6. Revisor produz resposta truncada: REPROVAR / DETECTAR TRUNCAMENTO
    # -------------------------------------------------------------------------
    def test_reviewer_truncated_output_detected(self):
        """Valida que resposta interrompida ou cortada pelo limite de tokens e detectada."""
        truncated_review = (
            self.valid_full_review + "\n\nObservação adicional que foi interrompida no meio de uma frase e"
        )
        self.assertTrue(_check_truncation(truncated_review))
        val = validate_reviewer_output(truncated_review, self.sample_form_data["channels"])
        self.assertTrue(val.is_truncated)
        self.assertFalse(val.is_valid)

    # -------------------------------------------------------------------------
    # 7. Agente 4 recebe corretamente o material final revisado
    # -------------------------------------------------------------------------
    @patch("agents.generate_chat_completion")
    def test_agent4_receives_final_reviewed_texts_in_langgraph(self, mock_chat):
        """Valida que o Agente 4 (Designer Visual) recebe os textos finais revisados no LangGraph."""
        mock_chat.return_value = (
            "## 1. Conceito Visual Geral\nEstética acolhedora.\n\n"
            "## 2. Prompts de Imagem por Canal\n"
            "### Instagram\nFormato: 1:1\nPrompt em Inglês: Specialty coffee --ar 1:1\n\n"
            "### WhatsApp\nFormato: 9:16\nPrompt em Inglês: Coffee card --ar 9:16\n\n"
            "### E-mail marketing\nFormato: 16:9\nPrompt em Inglês: Header banner --ar 16:9\n"
        )

        state = {
            "form_data": self.sample_form_data,
            "strategy": self.sample_strategy,
            "preliminary_copy": self.sample_copy,
            "review_and_final": self.valid_full_review
        }

        output = designer_prompts_imagem_node(state)
        self.assertIn("image_prompts", output)
        mock_chat.assert_called_once()
        user_prompt_passed = mock_chat.call_args[1]["user_prompt"]

        # O prompt do Agente 4 deve conter o material final do Revisor
        self.assertIn("Sua pausa especial tem aroma de café fresco", user_prompt_passed)
        self.assertIn("Versões Finais", user_prompt_passed)

    # -------------------------------------------------------------------------
    # 8. Relatorios incluem os textos finais corrigidos
    # -------------------------------------------------------------------------
    def test_reports_include_final_revised_texts(self):
        """Valida que os relatorios Markdown e TXT apresentam os textos finais da revisao."""
        campaign_data = {
            "form_data": self.sample_form_data,
            "strategy": self.sample_strategy,
            "preliminary_copy": self.sample_copy,
            "review_and_final": self.valid_full_review,
            "image_prompts": "## Conceito Visual\nEstilo acolhedor."
        }
        md_rep, txt_rep = build_campaign_reports(campaign_data)

        # Markdown deve conter a seção de revisão com os textos finais
        self.assertIn("REVISÃO CRÍTICA, SEO E VERSÃO FINAL", md_rep)
        self.assertIn("Sua pausa especial tem aroma de café fresco", md_rep)
        self.assertIn("Instagram — Versão Final Pronta para Uso", md_rep)
        self.assertIn("WhatsApp — Versão Final Pronta para Uso", md_rep)

        # TXT deve conter as seções finais
        self.assertIn("[4. REVISÃO CRÍTICA, SEO E VERSÃO FINAL (AGENTE 3 — REVISOR)]", txt_rep)
        self.assertIn("Sua pausa especial tem aroma de café fresco", txt_rep)

    # -------------------------------------------------------------------------
    # 9. Falha de revisao impede que o pipeline apresente sucesso irrestrito
    # -------------------------------------------------------------------------
    @patch("agents.generate_chat_completion")
    def test_reviewer_failure_notifies_incomplete_status(self, mock_chat):
        """Valida que revisao incompleta emite alerta de ressalva nos callbacks."""
        # Retorna apenas o diagnóstico sem a seção de textos finais
        mock_chat.return_value = (
            "## 1. Diagnóstico de Revisão\n"
            "Análise crítica detalhada sem entrega dos textos finais dos canais."
        )

        callback_events = []

        def dummy_callback(stage, status, msg, res=None):
            callback_events.append((stage, status, msg))

        state = {
            "form_data": self.sample_form_data,
            "strategy": self.sample_strategy,
            "preliminary_copy": self.sample_copy
        }
        config = {"configurable": {"progress_callback": dummy_callback}}

        output = especialista_seo_node(state, config=config)
        self.assertIn("review_and_final", output)

        # Verifica se o evento de conclusao sinalizou ressalva
        completed_events = [ev for ev in callback_events if ev[0] == "reviewer" and ev[1] == "completed"]
        self.assertTrue(len(completed_events) > 0)
        self.assertIn("ressalvas", completed_events[0][2].lower())


if __name__ == "__main__":
    unittest.main()
