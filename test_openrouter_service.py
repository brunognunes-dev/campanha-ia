"""
Testes unitarios para o modulo openrouter_service.py.
Cobre: finish_reason, recuperacao de truncamento, sanitizacao de erros,
       isolamento de contexto de sessao e tratamento de falhas HTTP.

Todas as chamadas de rede e SDK da OpenAI sao mockadas.
Nenhuma chamada real a API externa e efetuada.
"""

import contextvars
import unittest
from unittest.mock import MagicMock, patch

import openrouter_service


class DummyMessage:
    def __init__(self, content):
        self.content = content


class DummyChoice:
    def __init__(self, content, finish_reason="stop"):
        self.message = DummyMessage(content)
        self.finish_reason = finish_reason


class DummyResponse:
    def __init__(self, choices):
        self.choices = choices


class TestOpenRouterService(unittest.TestCase):

    def setUp(self):
        # Reset do ContextVar de modelo ativo antes de cada teste
        openrouter_service._SESSION_ACTIVE_MODEL.set(None)

    def tearDown(self):
        openrouter_service._SESSION_ACTIVE_MODEL.set(None)

    @patch("openrouter_service._get_api_credentials")
    @patch("openrouter_service._fetch_available_free_models")
    @patch("openai.OpenAI")
    def test_successful_completion_with_stop_finish_reason(
        self, mock_openai_cls, mock_fetch_models, mock_creds
    ):
        mock_creds.return_value = ("sk-or-test-mock-key-1234567890", "auto")
        mock_fetch_models.return_value = ["mock-model-1"]

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_client.chat.completions.create.return_value = DummyResponse(
            [DummyChoice("Estratégia completa gerada com sucesso.", finish_reason="stop")]
        )

        result = openrouter_service.generate_chat_completion(
            system_prompt="Você é um estrategista.",
            user_prompt="Crie um plano.",
            max_tokens=1000
        )

        self.assertEqual(result, "Estratégia completa gerada com sucesso.")
        self.assertEqual(openrouter_service._SESSION_ACTIVE_MODEL.get(), "mock-model-1")

    @patch("openrouter_service._get_api_credentials")
    @patch("openrouter_service._fetch_available_free_models")
    @patch("openai.OpenAI")
    def test_empty_content_triggers_fallback_or_error(
        self, mock_openai_cls, mock_fetch_models, mock_creds
    ):
        mock_creds.return_value = ("sk-or-test-mock-key-1234567890", "auto")
        mock_fetch_models.return_value = ["mock-model-empty"]

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = DummyResponse(
            [DummyChoice("   ", finish_reason="stop")]
        )

        with self.assertRaises(RuntimeError) as ctx:
            openrouter_service.generate_chat_completion("sys", "user")

        self.assertIn("Falha na geração", str(ctx.exception))

    @patch("openrouter_service._get_api_credentials")
    @patch("openrouter_service._fetch_available_free_models")
    @patch("openai.OpenAI")
    def test_finish_reason_length_triggers_successful_recovery(
        self, mock_openai_cls, mock_fetch_models, mock_creds
    ):
        mock_creds.return_value = ("sk-or-test-mock-key-1234567890", "auto")
        mock_fetch_models.return_value = ["mock-model-trunc"]

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        first_chunk = (
            "Esta é a primeira parte da resposta que foi interrompida "
            "devido ao limite estrito de tokens da primeira chamada realizada."
        )
        second_chunk = "E esta é a continuação completa e finalizada com êxito."

        # 1a chamada: finish_reason="length"
        # 2a chamada (recovery): finish_reason="stop"
        mock_client.chat.completions.create.side_effect = [
            DummyResponse([DummyChoice(first_chunk, finish_reason="length")]),
            DummyResponse([DummyChoice(second_chunk, finish_reason="stop")]),
        ]

        result = openrouter_service.generate_chat_completion("sys", "user")

        self.assertIn(first_chunk, result)
        self.assertIn(second_chunk, result)
        self.assertEqual(openrouter_service._SESSION_ACTIVE_MODEL.get(), "mock-model-trunc")

    @patch("openrouter_service._get_api_credentials")
    @patch("openrouter_service._fetch_available_free_models")
    @patch("openai.OpenAI")
    def test_finish_reason_length_unrecoverable_raises_error(
        self, mock_openai_cls, mock_fetch_models, mock_creds
    ):
        mock_creds.return_value = ("sk-or-test-mock-key-1234567890", "auto")
        mock_fetch_models.return_value = ["mock-model-fail-recovery"]

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        partial = "Texto longo inicial mas que cortou." * 5

        # 1a chamada: finish_reason="length"
        # 2a chamada (recovery): falha com excecao
        mock_client.chat.completions.create.side_effect = [
            DummyResponse([DummyChoice(partial, finish_reason="length")]),
            Exception("Gateway timeout durante a recuperacao"),
        ]

        with self.assertRaises(RuntimeError) as ctx:
            openrouter_service.generate_chat_completion("sys", "user")

        self.assertIn("Falha na geração", str(ctx.exception))

    @patch("openrouter_service._get_api_credentials")
    @patch("openrouter_service._fetch_available_free_models")
    @patch("openai.OpenAI")
    def test_missing_choices_handled_safely(
        self, mock_openai_cls, mock_fetch_models, mock_creds
    ):
        mock_creds.return_value = ("sk-or-test-mock-key-1234567890", "auto")
        mock_fetch_models.return_value = ["mock-model-nochoices"]

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = DummyResponse([])

        with self.assertRaises(RuntimeError):
            openrouter_service.generate_chat_completion("sys", "user")

    @patch("openrouter_service._get_api_credentials")
    @patch("openrouter_service._fetch_available_free_models")
    @patch("openai.OpenAI")
    def test_401_authentication_error_sanitized(
        self, mock_openai_cls, mock_fetch_models, mock_creds
    ):
        mock_creds.return_value = ("sk-or-test-mock-key-1234567890", "auto")
        mock_fetch_models.return_value = ["mock-model-auth"]

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("401 Unauthorized API key invalid")

        with self.assertRaises(RuntimeError) as ctx:
            openrouter_service.generate_chat_completion("sys", "user")

        err = str(ctx.exception)
        self.assertIn("Erro de autenticação com o OpenRouter", err)
        self.assertNotIn("sk-or-test", err)

    @patch("openrouter_service._get_api_credentials")
    @patch("openrouter_service._fetch_available_free_models")
    @patch("openai.OpenAI")
    def test_429_rate_limit_error_sanitized(
        self, mock_openai_cls, mock_fetch_models, mock_creds
    ):
        mock_creds.return_value = ("sk-or-test-mock-key-1234567890", "auto")
        mock_fetch_models.return_value = ["mock-model-rate"]

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Error code 429: Rate limit exceeded")

        with self.assertRaises(RuntimeError) as ctx:
            openrouter_service.generate_chat_completion("sys", "user")

        self.assertIn("Limite de requisições temporariamente atingido", str(ctx.exception))

    @patch("openrouter_service._get_api_credentials")
    @patch("openrouter_service._fetch_available_free_models")
    @patch("openai.OpenAI")
    def test_timeout_error_sanitized(
        self, mock_openai_cls, mock_fetch_models, mock_creds
    ):
        mock_creds.return_value = ("sk-or-test-mock-key-1234567890", "auto")
        mock_fetch_models.return_value = ["mock-model-timeout"]

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Read timed out after 30 seconds")

        with self.assertRaises(RuntimeError) as ctx:
            openrouter_service.generate_chat_completion("sys", "user")

        self.assertIn("Tempo limite de resposta esgotado", str(ctx.exception))

    @patch("openrouter_service._get_api_credentials")
    @patch("openrouter_service._fetch_available_free_models")
    @patch("openai.OpenAI")
    def test_connection_error_sanitized(
        self, mock_openai_cls, mock_fetch_models, mock_creds
    ):
        mock_creds.return_value = ("sk-or-test-mock-key-1234567890", "auto")
        mock_fetch_models.return_value = ["mock-model-conn"]

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Connection refused on host openrouter.ai")

        with self.assertRaises(RuntimeError) as ctx:
            openrouter_service.generate_chat_completion("sys", "user")

        self.assertIn("Falha de conexão com os servidores do OpenRouter", str(ctx.exception))

    def test_contextvar_model_isolation(self):
        # Valida que o contextvars.ContextVar isola contextos
        ctx1 = contextvars.copy_context()
        ctx2 = contextvars.copy_context()

        def set_in_ctx1():
            openrouter_service._SESSION_ACTIVE_MODEL.set("model-a")
            return openrouter_service._SESSION_ACTIVE_MODEL.get()

        def check_in_ctx2():
            return openrouter_service._SESSION_ACTIVE_MODEL.get()

        val1 = ctx1.run(set_in_ctx1)
        val2 = ctx2.run(check_in_ctx2)

        self.assertEqual(val1, "model-a")
        self.assertIsNone(val2)

    @patch("openrouter_service._read_secrets_file")
    def test_credentials_validation_short_key_raises_without_leaking_key(self, mock_secrets):
        mock_secrets.return_value = {"OPENROUTER_API_KEY": "sk-curta"}

        with patch("streamlit.secrets", {}):
            with self.assertRaises(ValueError) as ctx:
                openrouter_service._get_api_credentials()

            err_str = str(ctx.exception)
            self.assertIn("incompleta ou com tamanho insuficiente", err_str)
            self.assertNotIn("sk-curta", err_str)


if __name__ == "__main__":
    unittest.main()
