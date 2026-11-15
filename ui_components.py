"""
Componentes visuais e estilizacao para o MarketFlow AI.
Conceito: Modern AI Studio — Premium Dark SaaS Interface.
"""

import streamlit as st


def inject_custom_css():
    """Injeta estilos CSS personalizados refinados para a identidade Dark SaaS."""
    st.markdown(
        """
        <style>
        /* Importacao de fonte moderna */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
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
            font-size: 2.5rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            margin-bottom: 0.2rem;
            display: inline-block;
        }

        .brand-subtitle {
            color: #A78BFA;
            font-size: 1.05rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        }

        .brand-description {
            color: #94A3B8;
            font-size: 1rem;
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }

        /* Badges de Destaque */
        .badge-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
            background: rgba(139, 92, 246, 0.15);
            color: #C4B5FD;
            border: 1px solid rgba(139, 92, 246, 0.3);
            margin-right: 0.5rem;
            margin-bottom: 0.8rem;
        }

        .badge-pill-cyan {
            background: rgba(34, 211, 238, 0.12);
            color: #67E8F9;
            border: 1px solid rgba(34, 211, 238, 0.25);
        }

        /* Cartoes e Containers escuros */
        .dark-card {
            background-color: #111525;
            border: 1px solid #293047;
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
        }

        .dark-card-highlight {
            background: linear-gradient(180deg, #171C2E 0%, #111525 100%);
            border: 1px solid #3B4261;
        }

        .card-header-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: #F8FAFC;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        /* Cards do Fluxo de Trabalho (Workflow Nodes) */
        .workflow-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 0.75rem;
            margin: 1.2rem 0;
        }

        .wf-node {
            background: #111525;
            border: 1px solid #293047;
            border-radius: 10px;
            padding: 1rem 0.85rem;
            text-align: center;
            transition: all 0.2s ease;
        }

        .wf-node-pending {
            opacity: 0.6;
            border-color: #1E293B;
        }

        .wf-node-running {
            background: rgba(139, 92, 246, 0.12);
            border: 1px solid #8B5CF6;
            box-shadow: 0 0 15px rgba(139, 92, 246, 0.25);
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
            font-size: 1.6rem;
            margin-bottom: 0.35rem;
        }

        .wf-name {
            font-weight: 700;
            font-size: 0.88rem;
            color: #F8FAFC;
            margin-bottom: 0.2rem;
        }

        .wf-desc {
            font-size: 0.75rem;
            color: #94A3B8;
        }

        .wf-status-tag {
            display: inline-block;
            font-size: 0.7rem;
            font-weight: 700;
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
            margin-top: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }

        .tag-pending { background: #1E293B; color: #94A3B8; }
        .tag-running { background: #8B5CF6; color: #FFFFFF; }
        .tag-completed { background: #166534; color: #86EFAC; }
        .tag-error { background: #991B1B; color: #FCA5A5; }

        /* Botao Principal com Gradiente */
        div.stButton > button:first-child[kind="primary"],
        div.stButton > button:first-child {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.2s ease;
        }

        /* Estilizacao das abas nativas */
        button[data-baseweb="tab"] {
            font-weight: 600;
            color: #94A3B8;
            padding: 0.75rem 1.25rem;
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
                <span class="badge-pill">✨ Pipeline Multiagente (3 Agentes de IA)</span>
                <span class="badge-pill badge-pill-cyan">⚡ Automação n8n & Gmail</span>
                <span class="badge-pill">🔒 Header Auth & Secrets Seguros</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.divider()


def render_sidebar(authenticated: bool = True):
    """Renderiza a barra lateral com identidade e navegacao do estúdio."""
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
            - 🤖 **2. AI Workflow:** 3 agentes em cadeia
            - 📊 **3. Studio Dashboard:** Conteúdos e revisão
            - 🚀 **4. Automação:** n8n e disparo Gmail
            
            ---
            **Arquitetura de Agentes:**
            1. 🎯 *Estrategista de Marketing*
            2. ✍️ *Copywriter Multicanal*
            3. 🔍 *Revisor & Otimizador*
            
            ---
            <div style="font-size: 0.75rem; color: #64748B; margin-top: 1.5rem;">
                Programa Geração Tech 2026<br>
                Curso de IA Generativa
            </div>
            """,
            unsafe_allow_html=True
        )

        if authenticated and st.secrets.get("DEMO_ACCESS_PASSWORD", ""):
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚪 Sair da sessão", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.form_data = None
                st.session_state.campaign_result = None
                st.session_state.automation_status = None
                st.rerun()


def render_ai_workflow_panel(stage_states: dict):
    """
    Renderiza o painel visual do AI Workflow com 4 nós conectados e estados reais:
    - pending, running, completed, error
    """
    nodes_info = [
        ("briefing", "📋", "Entrada de Dados", "Briefing validado"),
        ("strategist", "🎯", "Estrategista", "Agente 1 (Marketing)"),
        ("copywriter", "✍️", "Copywriter", "Agente 2 (Redação)"),
        ("reviewer", "🔍", "Revisor & SEO", "Agente 3 (Otimização)"),
        ("ready", "🚀", "Campanha Pronta", "Consolidação final")
    ]

    cols = st.columns(len(nodes_info))

    for idx, (node_id, icon, name, desc) in enumerate(nodes_info):
        status = stage_states.get(node_id, "pending")
        
        status_labels = {
            "pending": "Pendente",
            "running": "Em execução",
            "completed": "Concluído",
            "error": "Erro"
        }
        
        with cols[idx]:
            st.markdown(
                f"""
                <div class="wf-node wf-node-{status}">
                    <div class="wf-icon">{icon}</div>
                    <div class="wf-name">{name}</div>
                    <div class="wf-desc">{desc}</div>
                    <span class="wf-status-tag tag-{status}">{status_labels.get(status, status)}</span>
                </div>
                """,
                unsafe_allow_html=True
            )


def render_automation_workflow_panel(automation_state: str, details_text: str = ""):
    """
    Renderiza o painel visual do Automation Workflow com nós conectados do n8n:
    - ready: Campanha pronta, aguardando envio
    - sending: Enviando requisição HTTP ao webhook
    - completed: Sucesso confirmado pelo n8n
    - error: Erro na automação
    - timeout: Resultado incerto (timeout)
    """
    nodes_auto = [
        ("campanha", "📄", "Campanha Pronta", "Conteúdo aprovado"),
        ("autorizacao", "🛡️", "Autorização", "Confirmação do usuário"),
        ("webhook", "⚡", "Webhook HTTP", "Header Auth seguro"),
        ("n8n", "⚙️", "n8n Workflow", "Processamento e IF"),
        ("gmail", "✉️", "Gmail API", "Disparo ao revisor"),
        ("confirmacao", "✅", "Confirmação", "HTTP 200 recebido")
    ]

    cols = st.columns(len(nodes_auto))

    # Mapeamento do estado global para cada no
    state_map = {
        "campanha": "completed",
        "autorizacao": "completed" if automation_state in ("sending", "completed", "error", "timeout") else "running",
        "webhook": "completed" if automation_state in ("completed",) else ("running" if automation_state == "sending" else "pending"),
        "n8n": "completed" if automation_state in ("completed",) else ("running" if automation_state == "sending" else "pending"),
        "gmail": "completed" if automation_state in ("completed",) else ("running" if automation_state == "sending" else "pending"),
        "confirmacao": "completed" if automation_state == "completed" else ("error" if automation_state == "error" else ("pending" if automation_state != "timeout" else "running"))
    }

    if automation_state == "error":
        state_map["n8n"] = "error"
        state_map["confirmacao"] = "error"

    for idx, (node_id, icon, name, desc) in enumerate(nodes_auto):
        st_val = state_map[node_id]
        with cols[idx]:
            st.markdown(
                f"""
                <div class="wf-node wf-node-{st_val}">
                    <div class="wf-icon">{icon}</div>
                    <div class="wf-name">{name}</div>
                    <div class="wf-desc">{desc}</div>
                    <span class="wf-status-tag tag-{st_val}">
                        {"Concluído" if st_val == "completed" else ("Ativo" if st_val == "running" else ("Erro" if st_val == "error" else "Pendente"))}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )
