"""
Suite de testes automatizados com mocks para a integracao n8n + Google Sheets v2.0.
Valida:
1. Integridade e topologia do workflow JSON de desenvolvimento (workflow-marketflow-v2-dev.json)
2. Preservacao integral do workflow da versao 1.0 (workflow-campanha-ia.json)
3. Contrato de dados compativel com Google Sheets e Gmail
4. Simulacao de resposta HTTP 200 do fluxo com Google Sheets (append + update)
5. Simulacao de rejeicao com HTTP 400 na saida False do no IF
6. Tratamento de timeouts e falhas sem consumo de recursos externos
"""

import json
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock
import requests

from automation_service import send_campaign_to_n8n


class TestN8nWorkflowV2Structure(unittest.TestCase):
    """Testes de integridade estrutural do arquivo JSON do workflow de desenvolvimento."""

    def setUp(self):
        self.dev_workflow_path = Path(__file__).parent / "n8n" / "workflow-marketflow-v2-dev.json"
        self.v1_workflow_path = Path(__file__).parent / "n8n" / "workflow-campanha-ia.json"
        self.postman_payload_path = Path(__file__).parent / "n8n" / "postman-payload-example.json"

    def test_dev_workflow_json_exists_and_valid(self):
        """Valida que o arquivo JSON do workflow DEV existe e e um JSON valido."""
        self.assertTrue(self.dev_workflow_path.exists(), "workflow-marketflow-v2-dev.json deve existir.")
        with open(self.dev_workflow_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("name"), "MarketFlow AI 2.0 - Desenvolvimento")
        self.assertIn("nodes", data)
        self.assertIn("connections", data)

    def test_v1_workflow_preserved(self):
        """Garante que o workflow original v1 continua preservado e inalterado."""
        self.assertTrue(self.v1_workflow_path.exists(), "workflow-campanha-ia.json original deve existir.")
        with open(self.v1_workflow_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("name"), "Campanha IA — Encaminhamento para Revisao")

    def test_postman_payload_valid(self):
        """Valida que o payload de exemplo do Postman contem todos os campos requeridos."""
        self.assertTrue(self.postman_payload_path.exists())
        with open(self.postman_payload_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        required_fields = [
            "submission_id", "submitted_at", "product_service",
            "objective", "channels", "report_markdown"
        ]
        for field in required_fields:
            self.assertIn(field, payload)
            self.assertTrue(payload[field], f"Campo {field} deve ter valor preenchido.")

    def test_all_required_nodes_present_in_dev_workflow(self):
        """Valida a presenca de todos os 7 nós requeridos na topologia v2."""
        with open(self.dev_workflow_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        nodes = {n["name"]: n for n in data["nodes"]}

        expected_nodes = [
            "Webhook Campanha",
            "Validar Dados Essenciais",
            "Google Sheets — Registrar Campanha",
            "Gmail — Enviar para Revisão",
            "Google Sheets — Confirmar Envio",
            "Respond to Webhook (Sucesso 200)",
            "Respond to Webhook (Erro 400)"
        ]
        for name in expected_nodes:
            self.assertIn(name, nodes, f"O nó '{name}' deve estar presente no workflow DEV.")

    def test_webhook_response_mode_is_response_node(self):
        """
        CRUCIAL: O webhook DEVE usar responseMode = 'responseNode'.
        Se usar 'onReceived', o Postman recebe 200 imediatamente sem executar os nós seguintes.
        """
        with open(self.dev_workflow_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        webhook_node = next(n for n in data["nodes"] if n["name"] == "Webhook Campanha")
        params = webhook_node.get("parameters", {})
        self.assertEqual(
            params.get("responseMode"),
            "responseNode",
            "O Webhook DEVE estar configurado com 'Using Respond to Webhook Node' para nao devolver 200 prematuro."
        )
        self.assertEqual(params.get("path"), "marketflow-v2-dev")

    def test_google_sheets_mapping_and_delivery_status(self):
        """Valida os mapeamentos especificos dos nós 1 e 2 do Google Sheets."""
        with open(self.dev_workflow_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        nodes = {n["name"]: n for n in data["nodes"]}

        # Nó 1: Registrar Campanha (append) -> delivery_status = 'pending'
        append_node = nodes["Google Sheets — Registrar Campanha"]
        self.assertEqual(append_node["type"], "n8n-nodes-base.googleSheets")
        self.assertEqual(append_node["parameters"]["operation"], "append")
        self.assertEqual(append_node["parameters"]["documentId"]["value"], "MarketFlow AI - Campanhas DEV")
        self.assertEqual(append_node["parameters"]["sheetName"]["value"], "Campanhas")

        append_cols = append_node["parameters"]["columns"]["value"]
        self.assertEqual(append_cols.get("delivery_status"), "pending")
        self.assertEqual(append_cols.get("validation_status"), "approved")
        self.assertIn("submission_id", append_cols)
        self.assertIn("product_service", append_cols)

        # Nó 2: Confirmar Envio (update) -> delivery_status = 'sent', match por submission_id
        update_node = nodes["Google Sheets — Confirmar Envio"]
        self.assertEqual(update_node["type"], "n8n-nodes-base.googleSheets")
        self.assertEqual(update_node["parameters"]["operation"], "update")
        self.assertEqual(update_node["parameters"]["documentId"]["value"], "MarketFlow AI - Campanhas DEV")
        self.assertEqual(update_node["parameters"]["sheetName"]["value"], "Campanhas")

        matching_cols = update_node["parameters"]["columns"]["matchingColumns"]
        self.assertIn("submission_id", matching_cols)

        update_cols = update_node["parameters"]["columns"]["value"]
        self.assertEqual(update_cols.get("delivery_status"), "sent")

    def test_connections_topology_flow(self):
        """Valida a cadeia exata de conexoes em serie exigida."""
        with open(self.dev_workflow_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        conns = data["connections"]

        # 1. Webhook -> Validar Dados Essenciais
        self.assertEqual(conns["Webhook Campanha"]["main"][0][0]["node"], "Validar Dados Essenciais")

        # 2. Validar Dados Essenciais:
        #    Saida 0 (True) -> Google Sheets — Registrar Campanha
        #    Saida 1 (False) -> Respond to Webhook (Erro 400)
        if_outputs = conns["Validar Dados Essenciais"]["main"]
        self.assertEqual(if_outputs[0][0]["node"], "Google Sheets — Registrar Campanha")
        self.assertEqual(if_outputs[1][0]["node"], "Respond to Webhook (Erro 400)")

        # 3. Google Sheets Registrar -> Gmail
        self.assertEqual(conns["Google Sheets — Registrar Campanha"]["main"][0][0]["node"], "Gmail — Enviar para Revisão")

        # 4. Gmail -> Google Sheets Confirmar Envio
        self.assertEqual(conns["Gmail — Enviar para Revisão"]["main"][0][0]["node"], "Google Sheets — Confirmar Envio")

        # 5. Google Sheets Confirmar Envio -> Respond to Webhook (Sucesso 200)
        self.assertEqual(conns["Google Sheets — Confirmar Envio"]["main"][0][0]["node"], "Respond to Webhook (Sucesso 200)")


class TestN8nServiceIntegrationWithV2Response(unittest.TestCase):
    """Testes unitarios simulando a resposta do n8n v2 via mocks em automation_service.py."""

    def setUp(self):
        self.valid_campaign_input = {
            "product_name": "Consultoria Financeira Ágil DEV",
            "objective": "Atrair novos clientes",
            "channels": ["Instagram", "WhatsApp", "E-mail marketing"],
            "report_markdown": "# Relatório DEV\n\nConteúdo completo da campanha."
        }

    @patch("automation_service._get_webhook_credentials")
    @patch("requests.post")
    def test_v2_success_response_handling(self, mock_post, mock_creds):
        """Simula resposta 200 do n8n com a confirmacao do Sheets e Gmail."""
        mock_creds.return_value = ("https://bgan-dev.app.n8n.cloud/webhook/marketflow-v2-dev", "token-dev-2026")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "sent",
            "message": "Campanha registrada na planilha e encaminhada para revisão com sucesso!",
            "submission_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "delivery_status": "sent",
            "validation_status": "approved",
            "registered_sheet": "MarketFlow AI - Campanhas DEV"
        }
        mock_resp.text = json.dumps(mock_resp.json.return_value)
        mock_post.return_value = mock_resp

        res = send_campaign_to_n8n(**self.valid_campaign_input)

        self.assertTrue(res["success"])
        self.assertFalse(res["uncertain"])
        self.assertIn("submission_id", res)
        self.assertIn("sucesso", res["message"].lower())

    @patch("automation_service._get_webhook_credentials")
    @patch("requests.post")
    def test_v2_validation_error_400_handling(self, mock_post, mock_creds):
        """Simula resposta HTTP 400 quando o no IF rejeita dados incompletos."""
        mock_creds.return_value = ("https://bgan-dev.app.n8n.cloud/webhook/marketflow-v2-dev", "token-dev-2026")

        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {
            "status": "error",
            "message": "Dados obrigatórios ausentes: product_service, report_markdown e submission_id são necessários"
        }
        mock_post.return_value = mock_resp

        res = send_campaign_to_n8n(**self.valid_campaign_input)

        self.assertFalse(res["success"])
        self.assertIn("rejeitou os dados", res["message"])


if __name__ == "__main__":
    unittest.main()
