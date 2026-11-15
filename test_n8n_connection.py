"""
Script de teste de conexao e envio com o webhook do n8n.
Valida se a URL, o Header Auth (X-Campanha-Token) e o contrato de dados estao corretos.
"""

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
import requests

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


def load_secrets() -> dict:
    secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        print(f"ERRO: Arquivo nao encontrado em: {secrets_path}")
        sys.exit(1)

    if tomllib is not None:
        with open(secrets_path, "rb") as f:
            return tomllib.load(f)

    secrets = {}
    with open(secrets_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                secrets[k.strip()] = v.strip().strip('"').strip("'")
    return secrets


def test_n8n_webhook():
    secrets = load_secrets()
    webhook_url = secrets.get("N8N_WEBHOOK_URL", "").strip()
    webhook_token = secrets.get("N8N_WEBHOOK_TOKEN", "").strip()

    if not webhook_url:
        print("AVISO: 'N8N_WEBHOOK_URL' ainda não foi configurada em .streamlit/secrets.toml.")
        print("Siga as orientações para criar ou ativar o workflow no n8n e insira a URL.")
        return False

    payload = {
        "submission_id": str(uuid.uuid4()),
        "product_service": "Teste Automatizado de Validação n8n",
        "objective": "Verificar integração e entrega de e-mail",
        "channels": ["Instagram", "WhatsApp", "E-mail marketing"],
        "report_markdown": "# Relatório de Teste de Integração\n\nEste é um disparo de teste gerado pelo script de validação.",
        "submitted_at": datetime.now(timezone.utc).isoformat()
    }

    headers = {
        "Content-Type": "application/json"
    }
    if webhook_token:
        headers["X-Campanha-Token"] = webhook_token

    print(f"Enviando requisição de teste para o webhook do n8n...")
    print(f"URL: {webhook_url}")
    print(f"Header Auth configurado: {'Sim (X-Campanha-Token)' if webhook_token else 'Não (Sem token)'}")

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers=headers,
            timeout=15.0
        )

        print(f"\nCódigo HTTP Retornado: {response.status_code}")
        print(f"Resposta do n8n: {response.text}")

        if response.status_code == 200:
            print("\nSUCESSO: Webhook do n8n validado com êxito! Resposta 200 recebida.")
            return True
        elif response.status_code in (401, 403):
            print("\nERRO DE AUTENTICAÇÃO: O token Header Auth enviado não coincide com o configurado no n8n.")
            return False
        elif response.status_code == 400:
            print("\nERRO DE VALIDAÇÃO: O nó IF do n8n rejeitou os dados enviados.")
            return False
        else:
            print(f"\nFALHA: O n8n retornou código inesperado {response.status_code}.")
            return False

    except requests.exceptions.Timeout:
        print("\nERRO: Tempo limite esgotado (timeout de 15s). Verifique se o n8n está online e se o workflow está ativo ou em modo 'Listen for Test Event'.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"\nFALHA DE REDE: Não foi possível conectar ao webhook: {e}")
        return False


if __name__ == "__main__":
    test_n8n_webhook()
