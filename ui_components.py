"""
Componentes visuais e estilizacao para o MarketFlow AI.
Conceito: Modern AI Studio — Premium Dark SaaS Interface.
Otimizado para alto desempenho de renderizacao e fluidez.
"""

import streamlit as st


def inject_custom_css():
    """Injeta estilos CSS refinados utilizando fontes do sistema para carregamento instantaneo."""
    st.markdown(
        """
        <style>
        /* Tipografia de sistema de alta performance (sem dependencia externa de rede) */
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }

        /* Fundo e superficies refinadas */
        .stApp {
            background-color: #090B13;
            color: #F8FAFC;
        }

        /* Cabecalho gradiente */
        .brand-title {
            background: linear-gradient(135deg, #F8FAFC 0%, #C4B5FD 50%, #8B5CF6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.3rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            margin-bottom: 0.15rem;
            display: inline-block;
        }

        .brand-subtitle {
            color: #A78BFA;
            font-size: 0.95rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-bottom: 0.4rem;
        }

        .brand-description {
            color: #94A3B8;
            font-size: 0.95rem;
            line-height: 1.5;
            margin-bottom: 1.2rem;
        }

        /* Badges de Destaque */
        .badge-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.2rem 0.65rem;
            border-radius: 9999px;
            font-size: 0.78rem;
            font-weight: 600;
            background: rgba(139, 92, 246, 0.15);
            color: #C4B5FD;
            border: 1px solid rgba(139, 92, 246, 0.3);
            margin-right: 0.4rem;
            margin-bottom: 0.5rem;
        }

        .badge-pill-cyan {
            background: rgba(34, 211, 238, 0.12);
            color: #67E8F9;
            border: 1px solid rgba(34, 211, 238, 0.25);
        }

        .card-header-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #F8FAFC;
            margin-bottom: 0.6rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }

        /* Grid do Workflow com CSS puro de alta performance (1 unico elemento DOM) */
        .wf-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 0.6rem;
            margin: 0.8rem 0;
            width: 100%;
        }

        .wf-node {
            background: #111525;
            border: 1px solid #293047;
            border-radius: 10px;
            padding: 0.85rem 0.6rem;
            text-align: center;
            transition: border-color 0.15s ease, background-color 0.15s ease;
        }

        .wf-node-pending {
            opacity: 0.55;
            border-color: #1E293B;
        }

        .wf-node-running {
            background: rgba(139, 92, 246, 0.15);
            border: 1px solid #8B5CF6;
            box-shadow: 0 0 12px rgba(139, 92, 246, 0.25);
            opacity: 1;
        }

        .wf-node-completed {
            background: rgba(34, 197, 94, 0.08);
            border: 1px solid #22C55E;
            opacity: 1;
        }

        .wf-node-error {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid #EF4444;
            opacity: 1;
        }

        .wf-icon {
            font-size: 1.4rem;
            margin-bottom: 0.2rem;
            line-height: 1;
        }

        .wf-name {
            font-weight: 700;
            font-size: 0.82rem;
            color: #F8FAFC;
            margin-bottom: 0.15rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .wf-desc {
            font-size: 0.7rem;
            color: #94A3B8;
            margin-bottom: 0.4rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .wf-status-tag {
            display: inline-block;
            font-size: 0.65rem;
            font-weight: 700;
            padding: 0.12rem 0.45rem;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }

        .tag-pending   { background: #1E293B; color: #94A3B8; }
        .tag-running   { background: #8B5CF6; color: #FFFFFF; }
        .tag-completed { background: #166534; color: #86EFAC; }
        .tag-error     { background: #991B1B; color: #FCA5A5; }

        /* Abas nativas estilizadas */
        button[data-baseweb="tab"] {
            font-weight: 600;
            color: #94A3B8;
            padding: 0.65rem 1.1rem;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: #F8FAFC;
            border-bottom-color: #8B5CF6;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def render_app_header():
    """Renderiza o cabecalho premium do MarketFlow AI."""
    st.markdown(
        """
        <div>
            <div class="brand-subtitle">Intelligent Marketing Campaign Studio</div>
            <div class="brand-title">MarketFlow AI</div>
            <p class="brand-description">
                Crie, otimize e automatize campanhas de marketing com inteligência artificial.
                Transforme briefings brutos em campanhas completas com estratégia, copy persuasivo e automação de entrega.
            </p>
            <div>
                <span class="badge-pill">✨ Pipeline Multiagente (4 Agentes de IA)</span>
                <span class="badge-pill badge-pill-cyan">🌐 Pesquisa Web / Tavily API</span>
                <span class="badge-pill badge-pill-cyan">⚡ Automação n8n &amp; Gmail</span>
                <span class="badge-pill">🔒 Header Auth &amp; Secrets Seguros</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.divider()


def render_sidebar(authenticated: bool = True):
    """Renderiza a barra lateral com identidade e navegacao do estudio."""
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align: left; padding-bottom: 1rem;">
                <h2 style="margin:0; font-size: 1.4rem; font-weight:800; background: linear-gradient(135deg, #F8FAFC, #8B5CF6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    MarketFlow AI
                </h2>
                <div style="color: #A78BFA; font-size: 0.78rem; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;">
                    Campaign Studio
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            **Módulos do Sistema:**
            - 🎯 **1. Configuração:** Briefing e canais
            - 🤖 **2. AI Workflow:** 4 agentes + pesquisa web
            - 📊 **3. Studio Dashboard:** Conteúdos e revisão
            - 🚀 **4. Automação:** n8n e disparo Gmail

            ---
            **Arquitetura de Agentes:**
            1. 🎯 *Pesquisador & Estrategista (Tavily API)*
            2. ✍️ *Copywriter Multicanal*
            3. 🔍 *Revisor & Otimizador SEO*
            4. 🎨 *Designer de Prompts de Imagem*

            ---
            <div style="font-size: 0.75rem; color: #64748B; margin-top: 1.5rem;">
                Programa Geração Tech 2026<br>
                Curso de IA Generativa
            </div>
            """,
            unsafe_allow_html=True
        )

        try:
            _pwd = st.secrets.get("DEMO_ACCESS_PASSWORD", "")
        except Exception:
            _pwd = ""
        if authenticated and _pwd:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚪 Sair da sessão", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.form_data = None
                st.session_state.campaign_result = None
                st.session_state.automation_status = None
                st.rerun()


def render_ai_workflow_panel(stage_states: dict):
    """
    Renderiza o painel visual do AI Workflow em um unico bloco HTML otimizado.

    Exibe 7 nos com estados reais de execucao:
      briefing → research (Tavily) → strategist → copywriter → reviewer → image_designer → ready

    Evita multiplas chamadas de st.columns para manter a interface fluida e sem lag.
    """
    nodes_info = [
        ("briefing",       "📋", "Entrada de Dados",   "Briefing validado"),
        ("research",       "🌐", "Pesquisa Web",        "Tavily Search API"),
        ("strategist",     "🎯", "Estrategista",        "Agente 1 (Marketing)"),
        ("copywriter",     "✍️",  "Copywriter",          "Agente 2 (Redação)"),
        ("reviewer",       "🔍", "Revisor & SEO",       "Agente 3 (Otimização)"),
        ("image_designer", "🎨", "Prompts de Imagem",   "Agente 4 (Direção Visual)"),
        ("ready",          "🚀", "Campanha Pronta",     "Consolidação final"),
    ]

    status_labels = {
        "pending":   "Pendente",
        "running":   "Executando...",
        "completed": "Concluído",
        "error":     "Erro",
    }

    cards = []
    for node_id, icon, name, desc in nodes_info:
        status = stage_states.get(node_id, "pending")
        label = status_labels.get(status, status)
        cards.append(
            '<div class="wf-node wf-node-' + status + '">'
            + '<div class="wf-icon">' + icon + '</div>'
            + '<div class="wf-name">' + name + '</div>'
            + '<div class="wf-desc">' + desc + '</div>'
            + '<span class="wf-status-tag tag-' + status + '">' + label + '</span>'
            + '</div>'
        )

    st.markdown('<div class="wf-container">' + "".join(cards) + '</div>', unsafe_allow_html=True)


def render_guardrails_panel(guardrails_result: dict):
    """
    Renderiza o painel visual de Guardrails e Compliance Publicitario.

    Chaves esperadas no dict:
      status          : "approved" | "warning" | "blocked"
      is_blocked      : bool
      score           : int (0-100)
      critical_issues : list[dict] com keys title, message, remediation
      warnings        : list[dict] com keys title, message, remediation
      passed_checks   : list[str]
      disclaimer      : str
    """
    if not guardrails_result:
        return

    status = guardrails_result.get("status", "approved")
    score = guardrails_result.get("score", 100)
    critical_issues = guardrails_result.get("critical_issues", [])
    warnings_list = guardrails_result.get("warnings", [])
    passed_checks = guardrails_result.get("passed_checks", [])
    disclaimer = guardrails_result.get("disclaimer", "")

    status_config = {
        "approved": {
            "icon":        "🛡️",
            "badge_class": "tag-completed",
            "badge_text":  "🟢 Conforme — Aprovado para Envio",
            "border":      "#22C55E",
            "bg":          "rgba(34, 197, 94, 0.05)",
            "summary":     "Todos os testes determinísticos de estrutura, cobertura de canais e alegações foram validados com êxito.",
        },
        "warning": {
            "icon":        "⚠️",
            "badge_class": "tag-running",
            "badge_text":  "🟡 Avisos de Atenção — Revisão Recomendada",
            "border":      "#F59E0B",
            "bg":          "rgba(245, 158, 11, 0.06)",
            "summary":     "A campanha possui pontos de atenção comerciais identificados. O envio está liberado mediante conferência humana.",
        },
        "blocked": {
            "icon":        "⛔",
            "badge_class": "tag-error",
            "badge_text":  "🔴 Bloqueado — Falha Crítica de Compliance",
            "border":      "#EF4444",
            "bg":          "rgba(239, 68, 68, 0.08)",
            "summary":     "O envio para a automação n8n foi preventivamente bloqueado devido a inconsistências críticas identificadas abaixo.",
        },
    }

    cfg = status_config.get(status, status_config["approved"])

    header_html = (
        '<div style="background: ' + cfg["bg"] + '; border: 1px solid ' + cfg["border"] + '; '
        'border-radius: 12px; padding: 1.2rem; margin: 1.2rem 0;">'
        '<div style="display: flex; justify-content: space-between; align-items: center; '
        'flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.8rem;">'
        '<div style="display: flex; align-items: center; gap: 0.5rem;">'
        '<span style="font-size: 1.4rem;">' + cfg["icon"] + '</span>'
        '<strong style="color: #F8FAFC; font-size: 1.05rem;">Guardrails &amp; Compliance da Campanha</strong>'
        '</div>'
        '<div style="display: flex; align-items: center; gap: 0.8rem;">'
        '<span style="font-size: 0.85rem; color: #94A3B8; font-weight: 600;">'
        'Índice de Conformidade: <strong style="color: #F8FAFC;">' + str(score) + '/100</strong>'
        '</span>'
        '<span class="wf-status-tag ' + cfg["badge_class"] + '">' + cfg["badge_text"] + '</span>'
        '</div>'
        '</div>'
        '<p style="color: #CBD5E1; font-size: 0.88rem; margin: 0 0 0.8rem 0;">' + cfg["summary"] + '</p>'
        '</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

    # Falhas criticas (bloqueadoras)
    if critical_issues:
        st.markdown(
            "<strong style='color: #FCA5A5; font-size: 0.95rem;'>⛔ Falhas Críticas Identificadas (Bloqueadoras):</strong>",
            unsafe_allow_html=True,
        )
        for issue in critical_issues:
            st.error(
                "**" + issue.get("title", "") + "**\n\n"
                + issue.get("message", "") + "\n\n"
                + "💡 **Como corrigir:** " + issue.get("remediation", "")
            )

    # Avisos nao bloqueadores
    if warnings_list:
        st.markdown(
            "<strong style='color: #FDE047; font-size: 0.95rem;'>⚠️ Pontos de Atenção (Não Bloqueadores):</strong>",
            unsafe_allow_html=True,
        )
        for warn in warnings_list:
            st.warning(
                "**" + warn.get("title", "") + "**\n\n"
                + warn.get("message", "") + "\n\n"
                + "🔍 **Recomendação:** " + warn.get("remediation", "")
            )

    # Checks aprovados (expansivel para manter a interface limpa)
    if passed_checks:
        with st.expander("✅ Verificações aprovadas (" + str(len(passed_checks)) + " itens validados)"):
            for check in passed_checks:
                st.markdown(
                    "- <span style='color: #86EFAC;'>✓</span> "
                    "<span style='color: #94A3B8; font-size: 0.85rem;'>" + str(check) + "</span>",
                    unsafe_allow_html=True,
                )

    # Disclaimer oficial
    if disclaimer:
        st.markdown(
            '<div style="font-size: 0.75rem; color: #64748B; margin-top: 0.6rem; line-height: 1.4;">'
            "ℹ️ <em>" + disclaimer + "</em>"
            "</div>",
            unsafe_allow_html=True,
        )


def render_automation_workflow_panel(automation_state: str, details_text: str = ""):
    """
    Renderiza o painel visual do Automation Workflow em HTML unico otimizado.

    Reflete APENAS estados observaveis pela aplicacao Streamlit:
    - ready:     Campanha pronta, aguardando autorizacao do usuario
    - sending:   Requisicao HTTP ao webhook sendo disparada (unico passo observavel)
    - completed: HTTP 200 recebido; n8n e Gmail exibidos como concluidos
    - error:     Falha confirmada na requisicao HTTP ao webhook
    - timeout:   Resposta incerta (timeout ou status ambiguo)

    Nao simula progresso interno dos nos do n8n: n8n e Gmail so mudam com base
    na resposta HTTP final, nao durante o envio.
    """
    nodes_auto = [
        ("campanha",    "📄", "Campanha Pronta",  "Conteúdo aprovado"),
        ("autorizacao", "🛡️", "Autorização",      "Confirmação do usuário"),
        ("webhook",     "⚡", "Webhook HTTP",      "Header Auth seguro"),
        ("n8n",         "⚙️", "n8n Workflow",      "Encaminhado ao n8n"),
        ("gmail",       "✉️",  "Gmail API",         "Envio ao revisor"),
        ("confirmacao", "✅", "Confirmação",       "HTTP 200 recebido"),
    ]

    # Apenas estados OBSERVAVEIS.
    # Durante 'sending': somente o webhook esta em execucao.
    # n8n e gmail sao internos ao n8n — nao observaveis durante o disparo.
    state_map = {
        "campanha":    "completed",
        "autorizacao": "completed" if automation_state in ("sending", "completed", "error", "timeout") else "running",
        "webhook": (
            "running"   if automation_state == "sending"   else
            "completed" if automation_state == "completed" else
            "error"     if automation_state == "error"     else
            "pending"
        ),
        # n8n e gmail: internos ao n8n — apenas confirmados via resposta HTTP final
        "n8n":   "completed" if automation_state == "completed" else (
                 "error"     if automation_state == "error"     else "pending"),
        "gmail": "completed" if automation_state == "completed" else "pending",
        "confirmacao": (
            "completed" if automation_state == "completed" else
            "error"     if automation_state == "error"     else
            "running"   if automation_state == "timeout"   else
            "pending"
        ),
    }

    status_labels = {
        "pending":   "Pendente",
        "running":   "Enviando...",
        "completed": "Concluído",
        "error":     "Erro",
    }

    cards = []
    for node_id, icon, name, desc in nodes_auto:
        st_val = state_map[node_id]
        label = status_labels.get(st_val, st_val)
        cards.append(
            '<div class="wf-node wf-node-' + st_val + '">'
            + '<div class="wf-icon">' + icon + '</div>'
            + '<div class="wf-name">' + name + '</div>'
            + '<div class="wf-desc">' + desc + '</div>'
            + '<span class="wf-status-tag tag-' + st_val + '">' + label + '</span>'
            + '</div>'
        )

    st.markdown('<div class="wf-container">' + "".join(cards) + '</div>', unsafe_allow_html=True)
