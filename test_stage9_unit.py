"""
Teste unitario do servico de automacao n8n (automation_service.py).
Valida o contrato de dados, tratamento de erros e protecoes de envio.
"""

from unittest.mock import patch, MagicMock
from automation_service import send_campaign_to_n8n

print("Testando automation_service.py...")

# 1. Teste de erro quando a URL do webhook nao esta configurada
with patch("automation_service._get_webhook_credentials", return_value=("", "")):
    res = send_campaign_to_n8n(
        product_name="Produto Teste",
        objective="Objetivo",
        channels=["Instagram"],
        report_markdown="# Teste"
    )
    assert res["success"] is False, "Deveria falhar na ausencia de URL."
    assert "não está configurada" in res["message"]
    print("✓ Tratamento de URL ausente validado.")

# 2. Teste de sucesso simulando resposta HTTP 200 do n8n
with patch("automation_service._get_webhook_credentials", return_value=("https://fake-n8n.cloud/webhook", "fake-token")):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "sent"}

    with patch("requests.post", return_value=mock_resp) as mock_post:
        res = send_campaign_to_n8n(
            product_name="Consultoria Ágil",
            objective="Atrair leads",
            channels=["WhatsApp"],
            report_markdown="# Relatorio Completo"
        )
        assert res["success"] is True, "Deveria retornar sucesso para HTTP 200."
        assert "submission_id" in res, "Deveria conter submission_id gerado."
        
        # Validar payload enviado
        called_args, called_kwargs = mock_post.call_args
        payload = called_kwargs["json"]
        headers = called_kwargs["headers"]
        
        assert payload["product_service"] == "Consultoria Ágil"
        assert payload["objective"] == "Atrair leads"
        assert payload["channels"] == ["WhatsApp"]
        assert payload["report_markdown"] == "# Relatorio Completo"
        assert "submitted_at" in payload
        assert headers["X-Campanha-Token"] == "fake-token"
        assert called_kwargs["timeout"] == 15.0
        print("✓ Contrato de dados e chamada HTTP 200 validados.")

# 3. Teste de timeout (resultado incerto sem retentativa automatica)
import requests
with patch("automation_service._get_webhook_credentials", return_value=("https://fake-n8n.cloud/webhook", "fake-token")):
    with patch("requests.post", side_effect=requests.exceptions.Timeout):
        res = send_campaign_to_n8n(
            product_name="Consultoria Ágil",
            objective="Atrair leads",
            channels=["Instagram"],
            report_markdown="# Relatorio"
        )
        assert res["success"] is False
        assert res["uncertain"] is True
        assert "tempo limite" in res["message"]
        print("✓ Protecao contra timeout e distincao de incerteza validadas.")

print("\nSUCESSO: automation_service.py validado com 100% de conformidade com os requisitos!")
