"""
Modulo responsavel exclusivamente pela integracao HTTP com o webhook do n8n.
Implementa o envio seguro da campanha gerada para revisao por e-mail,
com protecoes contra timeouts, duplicidade, validacao rigorosa de resposta HTTP/JSON
e sanitizacao completa de erros.
"""

from datetime import datetime, timezone
from pathlib import Path
import re
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


def sanitize_error_message(error: Any) -> str:
    """
    Higieniza qualquer mensagem ou objeto de erro para exibicao segura ao usuario:
    - Mascara possiveis tokens de API e credenciais (ex: sk-..., Bearer ...)
    - Mascara caminhos absolutos do sistema operacional (ex: C:\\Users\\...)
    - Remove fragmentos sensíveis de URLs
    """
    raw_text = str(error) if error is not None else "Erro desconhecido."

    # 1. Mascarar tokens do tipo sk-or-... ou sk-...
    sanitized = re.sub(r"sk-[a-zA-Z0-9_-]{10,}", "[REDACTED_API_KEY]", raw_text)

    # 2. Mascarar headers de autorizacao (Bearer ou Tokens)
    sanitized = re.sub(r"(Bearer\s+)[a-zA-Z0-9_\-\.]{8,}", r"\1[REDACTED_TOKEN]", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"(X-Campanha-Token['\"]?:\s*['\"]?)[^'\",\s]+", r"\1[REDACTED_TOKEN]", sanitized, flags=re.IGNORECASE)

    # 3. Mascarar tokens em query params de URLs (?token=... ou &token=...)
    sanitized = re.sub(r"([?&](?:token|key|api_key|secret)=)[^&\s]+", r"\1[REDACTED]", sanitized, flags=re.IGNORECASE)

    # 4. Mascarar caminhos absolutos locais do Windows e Linux/macOS
    sanitized = re.sub(r"[a-zA-Z]:\\[^\s:;,]+", "[ARQUIVO_LOCAL]", sanitized)
    sanitized = re.sub(r"/(?:Users|home|root)/[^\s:;,]+", "[ARQUIVO_LOCAL]", sanitized)

    return sanitized.strip()


def _get_webhook_credentials() -> tuple[str, str]:
    """Recupera URL e Token do n8n de forma segura."""
    url = ""
    token = ""

    # Tentativa 1: st.secrets quando executado no contexto do Streamlit
    try:
        import streamlit as st
        url = str(st.secrets.get("N8N_WEBHOOK_URL", "")).strip()
        token = str(st.secrets.get("N8N_WEBHOOK_TOKEN", "")).strip()
    except Exception:
        pass

    # Tentativa 2: leitura direta do secrets.toml (fallback para scripts/testes)
    if not url:
        secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
        if secrets_path.exists() and tomllib is not None:
            try:
                with open(secrets_path, "rb") as f:
                    data = tomllib.load(f)
                    url = str(data.get("N8N_WEBHOOK_URL", "")).strip()
                    token = str(data.get("N8N_WEBHOOK_TOKEN", "")).strip()
            except Exception:
                pass

    return url, token


def send_campaign_to_n8n(
    product_name: str,
    objective: str,
    channels: list[str],
    report_markdown: str,
    is_demo: bool = False
) -> dict[str, Any]:
    """
    Dispara o webhook do n8n com o contrato de dados oficial:
    - submission_id: UUID v4
    - product_service: nome do produto/serviço
    - objective: objetivo da campanha
    - channels: canais selecionados
    - report_markdown: relatório completo em Markdown
    - submitted_at: ISO 8601 UTC

    Possui validacao rigorosa de dados de entrada, status HTTP e JSON de resposta,
    com protecao contra retentativas automaticas em caso de timeout.
    Bloqueia categoricamente envios no Modo Demonstracao ou com dados ficticios.
    """
    # 1. Validacao rigorosa dos dados de entrada
    if not product_name or not str(product_name).strip():
        return {
            "success": False,
            "uncertain": False,
            "message": "Nome do produto/serviço é obrigatório para envio à automação."
        }
    if not objective or not str(objective).strip():
        return {
            "success": False,
            "uncertain": False,
            "message": "Objetivo da campanha é obrigatório para envio à automação."
        }
    if not channels or not isinstance(channels, list) or len(channels) == 0:
        return {
            "success": False,
            "uncertain": False,
            "message": "Pelo menos um canal de distribuição deve ser selecionado para automação."
        }
    if not report_markdown or not str(report_markdown).strip():
        return {
            "success": False,
            "uncertain": False,
            "message": "O relatório da campanha em Markdown está vazio ou indisponível."
        }

    # 2. Bloqueio categorico de envio no Modo Demonstracao
    if (
        is_demo
        or "resultados pré-carregados" in str(report_markdown).lower()
        or "modo demonstração" in str(report_markdown).lower()
    ):
        return {
            "success": False,
            "uncertain": False,
            "is_blocked_by_demo": True,
            "message": "Operação bloqueada com segurança: No Modo Demonstração, os envios externos ao n8n, ao Gmail e ao Google Sheets estão desativados."
        }

    webhook_url, webhook_token = _get_webhook_credentials()

    if not webhook_url:
        return {
            "success": False,
            "uncertain": False,
            "message": "A URL do webhook do n8n não está configurada. Configure 'N8N_WEBHOOK_URL' no painel de segredos."
        }

    submission_id = str(uuid.uuid4())
    submitted_at = datetime.now(timezone.utc).isoformat()

    payload = {
        "submission_id": submission_id,
        "product_service": str(product_name).strip(),
        "objective": str(objective).strip(),
        "channels": list(channels),
        "report_markdown": str(report_markdown),
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

        status_code = response.status_code

        # Caso de sucesso: 200 OK ou 201 Created
        if status_code in (200, 201):
            # Validacao rigorosa do corpo da resposta
            response_json: dict[str, Any] = {}
            has_json = False

            try:
                parsed = response.json()
                if isinstance(parsed, dict):
                    response_json = parsed
                    has_json = True
                elif isinstance(parsed, list):
                    response_json = {"items": parsed}
                    has_json = True
            except Exception:
                # O n8n pode retornar texto puro em algumas configuracoes
                pass

            # Se retornou JSON, verificar se o n8n reportou falha interna no corpo
            if has_json:
                error_value = (
                    response_json.get("error")
                    or response_json.get("errorMessage")
                    or response_json.get("errors")
                )
                explicit_failure = response_json.get("success") is False

                if error_value or explicit_failure:
                    err_msg = sanitize_error_message(error_value or "Execução rejeitada pelo fluxo n8n.")
                    return {
                        "success": False,
                        "uncertain": False,
                        "submission_id": submission_id,
                        "message": f"O fluxo do n8n reportou um erro interno: {err_msg}"
                    }

            # Validar respostas em texto puro: rejeitar páginas HTML de erro ou proxies
            text_body = (response.text or "").strip()
            if not has_json and text_body:
                lower_text = text_body.lower()
                if "<!doctype html" in lower_text or "<html" in lower_text:
                    return {
                        "success": False,
                        "uncertain": False,
                        "submission_id": submission_id,
                        "message": "O webhook retornou uma página HTML inesperada em vez de confirmação do n8n. Verifique a URL do serviço."
                    }

            return {
                "success": True,
                "uncertain": False,
                "submission_id": submission_id,
                "message": "Campanha encaminhada com sucesso para o revisor via n8n e Gmail!"
            }

        elif status_code in (401, 403):
            return {
                "success": False,
                "uncertain": False,
                "submission_id": submission_id,
                "message": "Falha de autenticação: O cabeçalho 'X-Campanha-Token' foi rejeitado pelo n8n."
            }
        elif status_code == 400:
            return {
                "success": False,
                "uncertain": False,
                "submission_id": submission_id,
                "message": "O n8n rejeitou os dados enviados por falta de campos obrigatórios ou formato inconsistente."
            }
        elif status_code == 404:
            return {
                "success": False,
                "uncertain": False,
                "submission_id": submission_id,
                "message": (
                    "Webhook do n8n não encontrado (HTTP 404). "
                    "Verifique se o workflow está ativo (Active) no n8n e se a URL configurada é a de produção (/webhook/ e não /webhook-test/)."
                )
            }
        elif status_code == 429:
            return {
                "success": False,
                "uncertain": False,
                "submission_id": submission_id,
                "message": "Limite de requisições atingido no n8n. Aguarde alguns instantes antes de enviar novamente."
            }
        elif status_code in (500, 502, 503, 504):
            return {
                "success": False,
                "uncertain": False,
                "submission_id": submission_id,
                "message": f"Instabilidade temporária no servidor do n8n (HTTP {status_code}). Aguarde e tente novamente."
            }
        else:
            return {
                "success": False,
                "uncertain": False,
                "submission_id": submission_id,
                "message": f"O serviço n8n retornou um código de erro inesperado: HTTP {status_code}."
            }

    except requests.exceptions.Timeout:
        # Resultado incerto: o n8n pode ter recebido e estar enviando o e-mail
        return {
            "success": False,
            "uncertain": True,
            "submission_id": submission_id,
            "message": (
                "A requisição ao n8n atingiu o tempo limite (15 segundos). "
                "O e-mail pode ter sido disparado ou ainda estar em processamento. "
                "Por segurança, NÃO reenvie imediatamente; verifique a caixa de entrada do e-mail de destino."
            )
        }
    except requests.exceptions.SSLError:
        return {
            "success": False,
            "uncertain": False,
            "submission_id": submission_id,
            "message": "Falha de segurança na conexão SSL/TLS com o servidor do n8n."
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "uncertain": False,
            "submission_id": submission_id,
            "message": "Não foi possível conectar ao servidor do n8n. Verifique se o endereço do webhook está correto e acessível."
        }
    except requests.exceptions.RequestException as e:
        safe_msg = sanitize_error_message(e)
        return {
            "success": False,
            "uncertain": False,
            "submission_id": submission_id,
            "message": f"Falha de rede ao conectar com o n8n: {safe_msg}"
        }
