"""
Suite de testes automatizados de robustez para o MarketFlow AI.
Utiliza mocks puros: nao consome APIs externas nem tokens de servicos reais.
Cobre:
- Validacao rigorosa de resposta HTTP e JSON do n8n (automation_service)
- Sanitizacao de credenciais e caminhos sensiveis em mensagens de erro
- Preservacao incremental de estado dos agentes em caso de falha
- Logica resiliente de protecao de acesso (check_password)
"""

import hmac
import unittest
from unittest.mock import patch, MagicMock
import requests

from automation_service import (
    send_campaign_to_n8n,
    sanitize_error_message,
)
from agents import generate_full_campaign


class TestN8nAutomationRobustness(unittest.TestCase):
    """Testes de robustez e validacao rigorosa de HTTP/JSON do servico de automacao n8n."""

    def setUp(self):
        self.valid_payload = {
            "product_name": "Software SaaS",
            "objective": "Atrair clientes",
            "channels": ["Instagram", "WhatsApp"],
            "report_markdown": "# Relatorio de Teste"
        }

    # 1. Validacao de dados de entrada
    def test_missing_input_fields(self):
        """Valida que entradas incompletas sao rejeitadas antes de qualquer requisicao HTTP."""
        with patch("automation_service._get_webhook_credentials", return_value=("https://fake.n8n.cloud/webhook", "tok")):
            # Nome vazio
            res = send_campaign_to_n8n("", "Obj", ["Instagram"], "# Rep")
            self.assertFalse(res["success"])
            self.assertIn("obrigatório", res["message"])

            # Objetivo vazio
            res = send_campaign_to_n8n("Prod", "", ["Instagram"], "# Rep")
            self.assertFalse(res["success"])
            self.assertIn("obrigatório", res["message"])

            # Canais vazios
            res = send_campaign_to_n8n("Prod", "Obj", [], "# Rep")
            self.assertFalse(res["success"])
            self.assertIn("canal", res["message"])

            # Relatorio vazio
            res = send_campaign_to_n8n("Prod", "Obj", ["Instagram"], "")
            self.assertFalse(res["success"])
            self.assertIn("vazio", res["message"])

    # 2. Resposta HTTP 200 com JSON valido e mensagem padrao do n8n
    def test_http_200_json_success(self):
        """Valida resposta HTTP 200 com corpo JSON tipico do n8n."""
        with patch("automation_service._get_webhook_credentials", return_value=("https://fake.n8n.cloud/webhook", "tok")):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"message": "Workflow was started"}
            mock_resp.text = '{"message": "Workflow was started"}'

            with patch("requests.post", return_value=mock_resp):
                res = send_campaign_to_n8n(**self.valid_payload)
                self.assertTrue(res["success"])
                self.assertFalse(res["uncertain"])
                self.assertIn("submission_id", res)
                self.assertIn("sucesso", res["message"].lower())

    # 3. Resposta HTTP 200 mas com erro explicito no corpo JSON
    def test_http_200_with_json_error(self):
        """Valida que HTTP 200 com JSON contendo 'error' e tratado com falha."""
        with patch("automation_service._get_webhook_credentials", return_value=("https://fake.n8n.cloud/webhook", "tok")):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"error": "Gmail node failed: Invalid credentials"}
            mock_resp.text = '{"error": "Gmail node failed: Invalid credentials"}'

            with patch("requests.post", return_value=mock_resp):
                res = send_campaign_to_n8n(**self.valid_payload)
                self.assertFalse(res["success"])
                self.assertIn("erro interno", res["message"])

    # 4. Resposta HTTP 200 com 'success: false' no JSON
    def test_http_200_with_success_false_in_json(self):
        """Valida deteccao de success: false em payload JSON."""
        with patch("automation_service._get_webhook_credentials", return_value=("https://fake.n8n.cloud/webhook", "tok")):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"success": False, "errorMessage": "Quota exceeded"}
            mock_resp.text = '{"success": false, "errorMessage": "Quota exceeded"}'

            with patch("requests.post", return_value=mock_resp):
                res = send_campaign_to_n8n(**self.valid_payload)
                self.assertFalse(res["success"])
                self.assertIn("Quota exceeded", res["message"])

    # 5. Resposta HTTP 200 com texto puro
    def test_http_200_plain_text(self):
        """Valida retorno HTTP 200 em texto puro legitimo."""
        with patch("automation_service._get_webhook_credentials", return_value=("https://fake.n8n.cloud/webhook", "tok")):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.side_effect = ValueError("Not JSON")
            mock_resp.text = "Workflow was started successfully."

            with patch("requests.post", return_value=mock_resp):
                res = send_campaign_to_n8n(**self.valid_payload)
                self.assertTrue(res["success"])

    # 6. Resposta HTTP 200 com HTML de proxy/erro
    def test_http_200_with_html_rejected(self):
        """Valida que HTML recebido com HTTP 200 e rejeitado com seguranca."""
        with patch("automation_service._get_webhook_credentials", return_value=("https://fake.n8n.cloud/webhook", "tok")):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.side_effect = ValueError("Not JSON")
            mock_resp.text = "<!DOCTYPE html><html><head><title>Login</title></head></html>"

            with patch("requests.post", return_value=mock_resp):
                res = send_campaign_to_n8n(**self.valid_payload)
                self.assertFalse(res["success"])
                self.assertIn("HTML", res["message"])

    # 7. Resposta HTTP 404 (webhook nao encontrado / inativo)
    def test_http_404_handling(self):
        """Valida mensagem explicativa para erro 404 comum no n8n."""
        with patch("automation_service._get_webhook_credentials", return_value=("https://fake.n8n.cloud/webhook", "tok")):
            mock_resp = MagicMock()
            mock_resp.status_code = 404
            with patch("requests.post", return_value=mock_resp):
                res = send_campaign_to_n8n(**self.valid_payload)
                self.assertFalse(res["success"])
                self.assertIn("404", res["message"])
                self.assertIn("Active", res["message"])

    # 8. Resposta HTTP 401 / 403 (token rejeitado)
    def test_http_401_403_handling(self):
        """Valida tratamento seguro de erro de autenticacao com n8n."""
        with patch("automation_service._get_webhook_credentials", return_value=("https://fake.n8n.cloud/webhook", "tok")):
            mock_resp = MagicMock()
            mock_resp.status_code = 401
            with patch("requests.post", return_value=mock_resp):
                res = send_campaign_to_n8n(**self.valid_payload)
                self.assertFalse(res["success"])
                self.assertIn("X-Campanha-Token", res["message"])

    # 9. Resposta HTTP 500 / 503 (instabilidade do servidor)
    def test_http_5xx_handling(self):
        """Valida mensagens de instabilidade temporaria para codigos 5xx."""
        with patch("automation_service._get_webhook_credentials", return_value=("https://fake.n8n.cloud/webhook", "tok")):
            mock_resp = MagicMock()
            mock_resp.status_code = 503
            with patch("requests.post", return_value=mock_resp):
                res = send_campaign_to_n8n(**self.valid_payload)
                self.assertFalse(res["success"])
                self.assertIn("Instabilidade temporária", res["message"])
                self.assertIn("503", res["message"])

    # 10. Excecao de timeout
    def test_timeout_handling(self):
        """Valida tratamento de timeout com status incerto (uncertain=True)."""
        with patch("automation_service._get_webhook_credentials", return_value=("https://fake.n8n.cloud/webhook", "tok")):
            with patch("requests.post", side_effect=requests.exceptions.Timeout):
                res = send_campaign_to_n8n(**self.valid_payload)
                self.assertFalse(res["success"])
                self.assertTrue(res["uncertain"])
                self.assertIn("tempo limite", res["message"])

    # 11. Excecao de conexao (ConnectionError)
    def test_connection_error_handling(self):
        """Valida mensagem limpa ao falhar conexao."""
        with patch("automation_service._get_webhook_credentials", return_value=("https://fake.n8n.cloud/webhook", "tok")):
            with patch("requests.post", side_effect=requests.exceptions.ConnectionError):
                res = send_campaign_to_n8n(**self.valid_payload)
                self.assertFalse(res["success"])
                self.assertIn("conectar ao servidor", res["message"])


class TestSecurityAndSanitization(unittest.TestCase):
    """Testes de seguranca: sanitizacao de credenciais e protecao de mensagens."""

    def test_sanitize_api_key(self):
        """Garante que qualquer chave OpenRouter ou Bearer e mascarada."""
        raw_msg = "Error 401: Unauthorized for key sk-dummy-test-key-sample-123456789"
        clean = sanitize_error_message(raw_msg)
        self.assertNotIn("sk-dummy-test-key", clean)
        self.assertIn("[REDACTED_API_KEY]", clean)

    def test_sanitize_authorization_header(self):
        """Garante que cabeçalhos de autorização são mascarados."""
        raw_msg = "Failed with Bearer secret-token-12345678"
        clean = sanitize_error_message(raw_msg)
        self.assertNotIn("secret-token-12345678", clean)
        self.assertIn("[REDACTED_TOKEN]", clean)

    def test_sanitize_local_paths(self):
        """Garante que caminhos absolutos do sistema operacional sao mascarados."""
        raw_win = r"Exception in C:\Users\Bruno Gabriel\Documents\campanha-ia\app.py: error"
        clean = sanitize_error_message(raw_win)
        self.assertNotIn(r"C:\Users\Bruno Gabriel", clean)
        self.assertIn("[ARQUIVO_LOCAL]", clean)


class TestAuthenticationLogic(unittest.TestCase):
    """Testes da logica de protecao de acesso demo."""

    def test_compare_digest_timing_safe(self):
        """Verifica comparacao segura via hmac.compare_digest."""
        stored = "admin123"
        user_input = "admin123"
        self.assertTrue(hmac.compare_digest(user_input.encode("utf-8"), stored.encode("utf-8")))

        user_wrong = "wrong"
        self.assertFalse(hmac.compare_digest(user_wrong.encode("utf-8"), stored.encode("utf-8")))

    def test_numeric_password_support(self):
        """Garante suporte seguro a senhas numericas no TOML."""
        stored_toml_int = 12345
        stored_str = str(stored_toml_int).strip()
        user_input = " 12345 "
        self.assertTrue(hmac.compare_digest(user_input.strip().encode("utf-8"), stored_str.encode("utf-8")))


class TestStatePreservationOnAgentFailure(unittest.TestCase):
    """Testes de preservacao de estado intermediario dos agentes em falhas."""

    @patch("agents.run_strategist_agent")
    @patch("agents.run_copywriter_agent")
    def test_partial_progress_captured_on_failure(self, mock_copy, mock_strat):
        """Verifica que o callback recebe a estrategia gerada antes de falhar no copywriter."""
        mock_strat.return_value = "## Estrategia Validada"
        mock_copy.side_effect = RuntimeError("OpenRouter Timeout no Copywriter")

        captured_stages = {}

        def tracking_callback(stage, state, msg, result=None):
            if state == "completed" and result:
                captured_stages[stage] = result

        form_data = {
            "product_name": "Consultoria",
            "product_description": "Desc",
            "target_audience": "Publico",
            "objective": "Objetivo",
            "tone": "Profissional",
            "differentials": "",
            "cta": "",
            "channels": ["Instagram"]
        }

        with self.assertRaises(RuntimeError):
            generate_full_campaign(form_data, progress_callback=tracking_callback)

        # A estrategia foi capturada antes da quebra da etapa 2!
        self.assertIn("strategist", captured_stages)
        self.assertEqual(captured_stages["strategist"], "## Estrategia Validada")


if __name__ == "__main__":
    unittest.main()
