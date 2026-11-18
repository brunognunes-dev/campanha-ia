"""
Testes unitarios para o modulo output_validation.py.
Cobre: _check_truncation, validate_strategist_output,
       validate_copywriter_output, validate_reviewer_output,
       validate_image_designer_output.

Nenhuma chamada a LLM ou API externa. Totalmente deterministico.
"""
import unittest
from output_validation import (
    _check_truncation,
    validate_strategist_output,
    validate_copywriter_output,
    validate_reviewer_output,
    validate_image_designer_output,
    ValidationResult,
)


# ---------------------------------------------------------------------------
# _check_truncation
# ---------------------------------------------------------------------------
class TestCheckTruncation(unittest.TestCase):

    def test_empty_string_is_truncated(self):
        self.assertTrue(_check_truncation(""))

    def test_whitespace_only_is_truncated(self):
        self.assertTrue(_check_truncation("   \n  "))

    def test_unbalanced_code_block_is_truncated(self):
        text = "Veja o exemplo:\n```python\ndef foo():"
        self.assertTrue(_check_truncation(text))

    def test_balanced_code_block_not_truncated(self):
        text = "Veja o exemplo:\n```python\ndef foo(): pass\n```\nFim."
        self.assertFalse(_check_truncation(text))

    def test_dangling_connective_e_is_truncated(self):
        # termina com " e" (connective pending)
        text = "O produto tem qualidade, inovacao e"
        self.assertTrue(_check_truncation(text))

    def test_dangling_connective_para_is_truncated(self):
        text = "Estrategia voltada para"
        self.assertTrue(_check_truncation(text))

    def test_sentence_cut_mid_word_no_punctuation(self):
        # Long tail without punctuation > 80 chars from last sentence boundary
        text = "Inicio da estrategia.\n" + "palavra " * 15
        self.assertTrue(_check_truncation(text))

    def test_proper_ending_period(self):
        text = "Esta e a versao final da campanha. Revisar antes de publicar."
        self.assertFalse(_check_truncation(text))

    def test_proper_ending_exclamation(self):
        text = "Campanha aprovada com sucesso!"
        self.assertFalse(_check_truncation(text))

    def test_proper_ending_question_mark(self):
        text = "O produto resolve o problema do cliente?"
        self.assertFalse(_check_truncation(text))

    def test_proper_ending_colon(self):
        text = "Palavras-chave sugeridas:"
        self.assertFalse(_check_truncation(text))

    def test_proper_ending_markdown_bold(self):
        text = "Ultima secao **finalizada**"
        self.assertFalse(_check_truncation(text))


# ---------------------------------------------------------------------------
# validate_strategist_output
# ---------------------------------------------------------------------------
class TestValidateStrategistOutput(unittest.TestCase):

    FULL_STRATEGY = (
        "## Proposta de Valor\nSolucao inovadora com beneficio real.\n\n"
        "## Mensagem Central\nConceito que transforma vidas.\n\n"
        "## Publico-Alvo\nPerfil: jovens empreendedores de 25-40 anos.\n\n"
        "## Pesquisa de Mercado\nFatos e dados baseados em fontes reais disponibilizadas pelo cliente.\n\n"
        "Estrategia consolidada com foco em diferenciais."
    )

    def test_complete_strategy_is_valid(self):
        result = validate_strategist_output(self.FULL_STRATEGY)
        self.assertIsInstance(result, ValidationResult)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.agent_name, "Estrategista")
        self.assertEqual(result.missing_sections, [])

    def test_missing_proposta_de_valor(self):
        text = (
            "## Mensagem Central\nConceito forte.\n\n"
            "## Publico-Alvo\nPerfil bem definido.\n\n"
            "## Pesquisa\nFatos e dados disponibilizados.\n\n"
            "Texto suficientemente longo para nao cair no limite de densidade minima da validacao."
        )
        result = validate_strategist_output(text)
        self.assertFalse(result.is_valid)
        self.assertIn("Proposta de Valor", result.missing_sections)

    def test_missing_mensagem_central(self):
        text = (
            "## Proposta de Valor\nSolucao inovadora.\n\n"
            "## Publico-Alvo\nPerfil bem definido.\n\n"
            "## Pesquisa\nFatos e dados disponibilizados pelo briefing.\n\n"
            "Texto com volume suficiente para validacao estrutural."
        )
        result = validate_strategist_output(text)
        self.assertFalse(result.is_valid)
        self.assertIn("Mensagem Central", result.missing_sections)

    def test_missing_public_alvo(self):
        text = (
            "## Proposta de Valor\nSolucao com valor real.\n\n"
            "## Mensagem Central\nSlogan criativo e memoravel.\n\n"
            "## Pesquisa\nFatos reais sem inventar fontes ou URLs.\n\n"
            "Estrategia robusta e bem estruturada com volume textual adequado."
        )
        result = validate_strategist_output(text)
        self.assertFalse(result.is_valid)
        self.assertIn("Caracterização do Público-Alvo", result.missing_sections)

    def test_missing_research_section(self):
        text = (
            "## Proposta de Valor\nSolucao com valor real e benefício diferenciado.\n\n"
            "## Mensagem Central\nSlogan memoravel e conceito forte para o mercado.\n\n"
            "## Publico-Alvo\nAudiencia jovem e conectada. Perfil bem caracterizado.\n\n"
            "Documento estruturado detalhando o plano de acao e canais de comunicacao para execucao."
        )
        result = validate_strategist_output(text)
        self.assertFalse(result.is_valid)
        self.assertIn("Análise de Mercado ou Declaração de Pesquisa", result.missing_sections)

    def test_empty_text_is_invalid(self):
        result = validate_strategist_output("")
        self.assertFalse(result.is_valid)
        self.assertIsNotNone(result.error_message)

    def test_very_short_text_is_invalid(self):
        result = validate_strategist_output("Curto demais.")
        self.assertFalse(result.is_valid)

    def test_truncated_strategy_flagged(self):
        # Texto completo mas que termina com dangling connective
        text = self.FULL_STRATEGY + "\n\nO produto resolve muito bem e"
        result = validate_strategist_output(text)
        self.assertTrue(result.is_truncated)
        self.assertFalse(result.is_valid)


# ---------------------------------------------------------------------------
# validate_copywriter_output
# ---------------------------------------------------------------------------
class TestValidateCopywriterOutput(unittest.TestCase):

    CHANNELS_3 = ["Instagram", "WhatsApp", "E-mail marketing"]

    FULL_COPY = (
        "## Instagram\n\nLegenda para o feed: Descubra a qualidade que transforma.\n"
        "CTA: Comente abaixo e marque um amigo!\n\n"
        "## WhatsApp\n\nMensagem direta: Ola! Conheca nossa oferta exclusiva.\n\n"
        "## E-mail marketing\n\nAssunto: Oferta imperdivel para voce!\n"
        "Pre-header: Nao perca esta chance unica.\n"
        "Corpo do e-mail: Prezado cliente, apresentamos..."
    )

    def test_all_channels_present_valid(self):
        result = validate_copywriter_output(self.FULL_COPY, self.CHANNELS_3)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.missing_channels, [])

    def test_missing_instagram_channel(self):
        text = (
            "## WhatsApp\n\nMensagem direta: Oferece exclusiva imperdivel.\n\n"
            "## E-mail marketing\n\nAssunto: Nao perca.\nCorpo do e-mail: Prezado cliente."
        )
        result = validate_copywriter_output(text, self.CHANNELS_3)
        self.assertFalse(result.is_valid)
        self.assertIn("Instagram", result.missing_channels)

    def test_missing_whatsapp_channel(self):
        text = (
            "## Instagram\n\nLegenda feed: Qualidade real. CTA: Comente!\n\n"
            "## E-mail marketing\n\nAssunto: Oferta especial.\nCorpo: Prezado cliente."
        )
        result = validate_copywriter_output(text, self.CHANNELS_3)
        self.assertFalse(result.is_valid)
        self.assertIn("WhatsApp", result.missing_channels)

    def test_missing_email_channel(self):
        text = (
            "## Instagram\n\nLegenda feed: Qualidade real. CTA: Comente!\n\n"
            "## WhatsApp\n\nMensagem direta: Zap rapido e direto."
        )
        result = validate_copywriter_output(text, self.CHANNELS_3)
        self.assertFalse(result.is_valid)
        self.assertIn("E-mail marketing", result.missing_channels)

    def test_single_channel_instagram_valid(self):
        text = (
            "## Instagram\n\n"
            "Legenda para o feed: Descubra a qualidade e inovação que transformam o seu dia a dia. "
            "Aproveite nossa condição especial por tempo limitado.\n\n"
            "CTA: Clique no link na bio e confira todos os detalhes agora mesmo!"
        )
        result = validate_copywriter_output(text, ["Instagram"])
        self.assertTrue(result.is_valid)

    def test_empty_text_invalid(self):
        result = validate_copywriter_output("", self.CHANNELS_3)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.missing_channels, self.CHANNELS_3)

    def test_truncated_copy_flagged(self):
        # Termina com bloco de codigo desbalanceado
        text = self.FULL_COPY + "\n\nAdicional ```python\nimport sys"
        result = validate_copywriter_output(text, self.CHANNELS_3)
        self.assertTrue(result.is_truncated)
        self.assertFalse(result.is_valid)

    def test_instagram_missing_cta_produces_warning(self):
        # Instagram sem CTA gera warning, mas nao invalida
        text = (
            "## Instagram\n\nFeed: Descubra a qualidade que transforma seu negocio.\n\n"
            "## WhatsApp\n\nMensagem direta: Zap exclusivo para voce.\n\n"
            "## E-mail marketing\n\nAssunto: Oferta.\nCorpo do e-mail: Prezado."
        )
        result = validate_copywriter_output(text, self.CHANNELS_3)
        # Sem CTA → warning, mas canais presentes → is_valid pode ser True
        self.assertNotIn("Instagram", result.missing_channels)


# ---------------------------------------------------------------------------
# validate_reviewer_output
# ---------------------------------------------------------------------------
class TestValidateReviewerOutput(unittest.TestCase):

    CHANNELS_2 = ["Instagram", "E-mail marketing"]

    FULL_REVIEW = (
        "## Avaliacao Critica\nTextos bem estruturados com pequenos ajustes.\n\n"
        "## Palavras-chave SEO\nMarketing digital, conversao, engajamento.\n\n"
        "## Versao Final\n\n### Instagram\nLegenda revisada: Qualidade comprovada.\n\n"
        "### E-mail marketing\nAssunto revisado: Nao perca a oportunidade. Corpo: Prezado cliente."
    )

    def test_complete_review_is_valid(self):
        result = validate_reviewer_output(self.FULL_REVIEW, self.CHANNELS_2)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.missing_sections, [])
        self.assertEqual(result.missing_channels, [])

    def test_missing_versao_final_header(self):
        text = (
            "## Avaliacao Critica\nAjustes menores identificados na redação preliminar.\n\n"
            "## Palavras-chave SEO\nMarketing, engajamento, resultado comercial e alcance orgânico.\n\n"
            "Observações gerais do revisor sobre tom de voz, clareza da mensagem e adequação às personas."
        )
        result = validate_reviewer_output(text, self.CHANNELS_2)
        self.assertFalse(result.is_valid)
        self.assertIn("Versão Final Revisada dos Conteúdos", result.missing_sections)

    def test_missing_seo_section(self):
        text = (
            "## Avaliacao Critica\nAjustes de tom identificados.\n\n"
            "## Versao Final\n\n### Instagram\nLegenda revisada final.\n\n"
            "### E-mail marketing\nAssunto: Oferta. Corpo: prezado cliente."
        )
        result = validate_reviewer_output(text, self.CHANNELS_2)
        self.assertFalse(result.is_valid)
        self.assertIn("Palavras-Chave e Otimização Temática", result.missing_sections)

    def test_missing_channel_in_final_version(self):
        text = (
            "## Avaliacao Critica\nTextos aprovados.\n\n"
            "## Palavras-chave SEO\nEngajamento, otimizacao tematica.\n\n"
            "## Versao Final\n\n### Instagram\nLegenda revisada: perfeita."
            # E-mail ausente na versao final
        )
        result = validate_reviewer_output(text, self.CHANNELS_2)
        self.assertFalse(result.is_valid)
        self.assertIn("E-mail marketing", result.missing_channels)

    def test_empty_text_invalid(self):
        result = validate_reviewer_output("", self.CHANNELS_2)
        self.assertFalse(result.is_valid)

    def test_truncated_review_flagged(self):
        text = self.FULL_REVIEW + "\n\nConsideracao adicional sobre o produto e"
        result = validate_reviewer_output(text, self.CHANNELS_2)
        self.assertTrue(result.is_truncated)


# ---------------------------------------------------------------------------
# validate_image_designer_output
# ---------------------------------------------------------------------------
class TestValidateImageDesignerOutput(unittest.TestCase):

    CHANNELS_2 = ["Instagram", "WhatsApp"]

    FULL_DESIGN = (
        "## Conceito Visual Geral\nEstilo minimalista. Paleta de cores: azul e branco.\n\n"
        "## Instagram — Feed (1:1)\n"
        "**Formato:** 1:1 (aspect ratio quadrado)\n"
        "**Prompt em Inglês:** Minimalist product photo, blue tones, clean background, "
        "professional quality, natural lighting --ar 1:1\n"
        "**Composicao:** Produto centralizado com fundo limpo.\n\n"
        "## WhatsApp — Card (9:16)\n"
        "**Formato:** 9:16 vertical\n"
        "**Prompt em Inglês:** Bold product highlight, vibrant colors, zap-ready card "
        "design, clean typography --ar 9:16\n"
        "**Composicao:** CTA grande e legivel."
    )

    def test_complete_designer_output_valid(self):
        result = validate_image_designer_output(self.FULL_DESIGN, self.CHANNELS_2)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.missing_channels, [])
        self.assertEqual(result.missing_sections, [])

    def test_missing_visual_concept(self):
        text = (
            "## Instagram\nFormato: 1:1\nPrompt em Inglês: Product photo --ar 1:1\n\n"
            "## WhatsApp\nFormato: 9:16\nPrompt em Inglês: Card design --ar 9:16\n\n"
            "Apresentação técnica das imagens sem diretrizes criativas gerais descritas."
        )
        result = validate_image_designer_output(text, self.CHANNELS_2)
        self.assertFalse(result.is_valid)
        self.assertIn("Conceito Visual Geral", result.missing_sections)

    def test_missing_format_aspect_ratio(self):
        text = (
            "## Conceito Visual Geral\nEstética elegante e sofisticada.\n\n"
            "## Instagram\nPrompt em Inglês: Earthy tones product photo, clean composition.\n\n"
            "## WhatsApp\nPrompt em Inglês: Direct card highlight bold visual messaging.\n\n"
            "Diretrizes visuais para as peças sem especificações dimensionais fornecidas."
        )
        result = validate_image_designer_output(text, self.CHANNELS_2)
        self.assertFalse(result.is_valid)
        self.assertIn("Formato / Aspect Ratio das imagens", result.missing_sections)

    def test_missing_english_prompt(self):
        text = (
            "## Conceito Visual Geral\nEstética moderna com iluminação natural.\n\n"
            "## Instagram\nFormato: 1:1\nComposição: foto do produto em close com fundo desfocado.\n\n"
            "## WhatsApp\nFormato: 9:16\nComposição: cartão vertical ilustrado com chamada de ação clara.\n\n"
            "Todas as instruções foram redigidas apenas em língua portuguesa sem diretrizes de IA."
        )
        result = validate_image_designer_output(text, self.CHANNELS_2)
        self.assertFalse(result.is_valid)
        self.assertIn("Prompt Otimizado em Inglês", result.missing_sections)

    def test_missing_instagram_channel(self):
        text = (
            "## Conceito Visual Geral\nEstética vibrante com alta saturação e contraste.\n\n"
            "## WhatsApp\nFormato: 9:16\n"
            "Prompt em Inglês: Bold card design, striking colors --ar 9:16\n\n"
            "Composição detalhada voltada exclusivamente para mensagens instantâneas."
        )
        result = validate_image_designer_output(text, self.CHANNELS_2)
        self.assertFalse(result.is_valid)
        self.assertIn("Instagram", result.missing_channels)

    def test_missing_whatsapp_channel(self):
        text = (
            "## Conceito Visual Geral\nEstética minimalista com foco no produto.\n\n"
            "## Instagram\nFormato: 1:1\n"
            "Prompt em Inglês: Minimal product photo, studio lighting --ar 1:1\n\n"
            "Composição detalhada voltada para a rede social de fotos e vídeos."
        )
        result = validate_image_designer_output(text, self.CHANNELS_2)
        self.assertFalse(result.is_valid)
        self.assertIn("WhatsApp", result.missing_channels)

    def test_empty_text_invalid(self):
        result = validate_image_designer_output("", self.CHANNELS_2)
        self.assertFalse(result.is_valid)

    def test_truncated_designer_output_flagged(self):
        text = self.FULL_DESIGN + "\n\nConsideracao adicional e"
        result = validate_image_designer_output(text, self.CHANNELS_2)
        self.assertTrue(result.is_truncated)
        self.assertFalse(result.is_valid)

    def test_three_channels_all_present(self):
        text = (
            "## Conceito Visual\nEstilo moderno. Paleta de cores vivas.\n\n"
            "## Instagram Feed\nFormato: 1:1 (aspect ratio)\nPrompt em Inglês: Product hero --ar 1:1\n\n"
            "## WhatsApp Card\nFormato: 9:16 aspect ratio\nPrompt em Inglês: Zap bold card --ar 9:16\n\n"
            "## E-mail Header\nFormato: 16:9 (aspect ratio horizontal)\nPrompt em Inglês: Email header banner --ar 16:9\n"
        )
        result = validate_image_designer_output(text, ["Instagram", "WhatsApp", "E-mail marketing"])
        self.assertTrue(result.is_valid)


# ---------------------------------------------------------------------------
# ValidationResult.to_dict
# ---------------------------------------------------------------------------
class TestValidationResultToDict(unittest.TestCase):

    def test_to_dict_structure(self):
        vr = ValidationResult(
            is_valid=False,
            agent_name="Teste",
            missing_sections=["Secao A"],
            missing_channels=["Canal B"],
            is_truncated=True,
            warnings=["aviso"],
            error_message="Erro de teste."
        )
        d = vr.to_dict()
        self.assertIsInstance(d, dict)
        self.assertFalse(d["is_valid"])
        self.assertEqual(d["agent_name"], "Teste")
        self.assertIn("Secao A", d["missing_sections"])
        self.assertIn("Canal B", d["missing_channels"])
        self.assertTrue(d["is_truncated"])
        self.assertEqual(d["warnings"], ["aviso"])
        self.assertEqual(d["error_message"], "Erro de teste.")


if __name__ == "__main__":
    unittest.main()
