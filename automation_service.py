"""
Modulo responsavel exclusivamente pela integracao HTTP com o webhook do n8n.
Implementa o envio seguro da campanha gerada para revisao por e-mail,
com protecoes contra timeouts, duplicidade e tratamento de erros.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import uuid
import requests

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


def _get_webhook_credentials() -> tuple[str, str]:
    """Recupera URL e Token do n8n de forma segura."""
    url = ""
    token = ""

    # Tentativa 1: st.secrets quando executado no contexto do Streamlit
    try:
        import streamlit as st
        url = st.secrets.get("N8N_WEBHOOK_URL", "").strip()
        token = st.secrets.get("N8N_WEBHOOK_TOKEN", "").strip()
    except Exception:
        pass

    # Tentativa 2: leitura direta do secrets.toml (fallback para scripts/testes)
    if not url:
        secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
        if secrets_path.exists() and tomllib is not None:
            try:
                with open(secrets_path, "rb") as f:
                    data = tomllib.load(f)
                    url = data.get("N8N_WEBHOOK_URL", "").strip()
                    token = data.get("N8N_WEBHOOK_TOKEN", "").strip()
            except Exception:
                pass

    return url, token


def send_campaign_to_n8n(
    product_name: str,
    objective: str,
    channels: list[str],
    report_markdown: str
) -> dict[str, Any]:
    """
    Dispara o webhook do n8n com o contrato de dados oficial:
    - submission_id: UUID v4
    - product_service: nome do produto/serviço
    - objective: objetivo da campanha
    - channels: canais selecionados
    - report_markdown: relatório completo em Markdown
    - submitted_at: ISO 8601 UTC

    Não reexecuta automaticamente em caso de timeout para evitar duplicidade de e-mails.
    """
    webhook_url, webhook_token = _get_webhook_credentials()

    if not webhook_url:
        return {
            "success": False,
            "uncertain": False,
            "message": "A URL do webhook do n8n não está configurada. Configure 'N8N_WEBHOOK_URL' no arquivo de segredos."
        }

    submission_id = str(uuid.uuid4())
    submitted_at = datetime.now(timezone.utc).isoformat()

    payload = {
        "submission_id": submission_id,
        "product_service": product_name,
        "objective": objective,
        "channels": channels,
        "report_markdown": report_markdown,
        "submitted_at": submitted_at
    }

    headers = {
        "Content-Type": "application/json"
    }
    if webhook_token:
        # Autenticacao via Header Auth protegida
        headers["X-Campanha-Token"] = webhook_token

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers=headers,
            timeout=15.0
        )

        if response.status_code == 200:
            return {
                "success": True,
                "uncertain": False,
                "submission_id": submission_id,
                "message": "Campanha encaminhada com sucesso para o revisor via n8n e Gmail!"
            }
        elif response.status_code in (401, 403):
            return {
                "success": False,
                "uncertain": False,
                "message": "Falha de autenticação: O cabeçalho 'X-Campanha-Token' foi rejeitado pelo n8n."
            }
        elif response.status_code == 400:
            return {
                "success": False,
                "uncertain": False,
                "message": "O n8n rejeitou os dados enviados por falta de campos obrigatórios."
            }
        else:
            return {
                "success": False,
                "uncertain": False,
                "message": f"O serviço n8n retornou um código de erro inesperado: HTTP {response.status_code}."
            }

    except requests.exceptions.Timeout:
        # Resultado incerto: o n8n pode ter recebido e estar enviando o e-mail
        return {
            "success": False,
            "uncertain": True,
            "message": (
                "A requisição ao n8n atingiu o tempo limite (15 segundos). "
                "O e-mail pode ter sido disparado ou ainda estar em processamento. "
                "Por segurança, NÃO reenvie imediatamente; verifique a caixa de entrada do e-mail de destino."
            )
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "uncertain": False,
            "message": f"Falha de rede ao conectar com o n8n: {e}"
        }
