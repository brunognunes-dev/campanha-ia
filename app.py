"""
MarketFlow AI — Intelligent Marketing Campaign Studio
Interface principal desenvolvida com Streamlit.
Conceito: Modern AI Studio — Premium Dark SaaS Interface.
"""

import hmac
from pathlib import Path
from typing import Any
import streamlit as st
from agents import generate_full_campaign, build_campaign_reports
from automation_service import send_campaign_to_n8n, sanitize_error_message
from demo_service import (
    DEMO_FORM_DATA,
    build_demo_campaign_reports,
    run_demo_workflow_simulation,
    block_demo_automation
)
from guardrails import validate_campaign_guardrails
from ui_components import (
    inject_custom_css,
    render_app_header,
    render_sidebar,
    render_ai_workflow_panel,
    render_automation_workflow_panel,
    render_guardrails_panel
)

# Configuracao da pagina
st.set_page_config(
    page_title="MarketFlow AI 2.0 — Intelligent Campaign Studio",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injetar estilizacao personalizada Dark SaaS
inject_custom_css()

# Inicializacao de variaveis no session_state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "app_mode" not in st.session_state:
    st.session_state.app_mode = "real"

if "form_data" not in st.session_state:
    st.session_state.form_data = None

if "campaign_result" not in st.session_state:
    st.session_state.campaign_result = None

if "automation_status" not in st.session_state:
    st.session_state.automation_status = None

if "image_prompts" not in st.session_state:
    st.session_state.image_prompts = None

if "research_data" not in st.session_state:
    st.session_state.research_data = None

if "guardrails_result" not in st.session_state:
    st.session_state.guardrails_result = None

if "ai_workflow_states" not in st.session_state:
    st.session_state.ai_workflow_states = {
        "briefing": "pending",
        "research": "pending",
        "strategist": "pending",
        "copywriter": "pending",
        "reviewer": "pending",
        "image_designer": "pending",
        "ready": "pending"
    }


def _get_demo_access_password() -> str:
    """Recupera a credencial de demonstracao com tratamento seguro e fallback."""
    raw_pwd = ""
    try:
        raw_pwd = str(st.secrets.get("DEMO_ACCESS_PASSWORD", "") or "").strip()
    except Exception:
        pass

    if not raw_pwd:
        secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
        if secrets_path.exists():
            try:
                from automation_service import tomllib
                if tomllib is not None:
                    with open(secrets_path, "rb") as f:
                        data = tomllib.load(f)
                        raw_pwd = str(data.get("DEMO_ACCESS_PASSWORD", "") or "").strip()
            except Exception:
                pass

    return raw_pwd


def check_password() -> bool:
    """
    Verifica a credencial de demonstracao configurada nos segredos.
    Utiliza comparacao segura em tempo constante (hmac.compare_digest)
    para evitar vulnerabilidades de timing attack e preserva a interface estilizada.
    """
    expected_password = _get_demo_access_password()

    # Se nao houver senha configurada, libera o acesso imediatamente
    if not expected_password:
        return True

    if st.session_state.authenticated:
        return True

    st.markdown(
        """
        <div style="max-width: 460px; margin: 3rem auto; padding: 2rem; background: #111525; border: 1px solid #293047; border-radius: 14px; text-align: center;">
            <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">🔐</div>
            <h2 style="margin: 0; color: #F8FAFC; font-size: 1.5rem; font-weight: 700;">Acesso ao MarketFlow AI</h2>
            <p style="color: #94A3B8; font-size: 0.9rem; margin-top: 0.5rem; margin-bottom: 1.5rem;">
                Informe a credencial de demonstração para acessar o estúdio.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_center = st.columns([1, 1.2, 1])[1]
    with col_center:
        with st.form("login_form"):
            password_input = st.text_input("Senha de acesso:", type="password", placeholder="Digite a senha de demonstração")
            submit_button = st.form_submit_button("Entrar no Estúdio", use_container_width=True, type="primary")

            if submit_button:
                cleaned_input = str(password_input or "").strip()
                is_valid = False
                try:
                    is_valid = hmac.compare_digest(
                        cleaned_input.encode("utf-8"),
                        expected_password.encode("utf-8")
                    )
                except Exception:
                    is_valid = (cleaned_input == expected_password)

                if is_valid:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Credencial incorreta. Verifique a senha informada.")

    st.stop()
    return False


# Valida autenticacao antes de exibir o restante da aplicacao
check_password()

# Renderiza a barra lateral personalizada e detecta o modo de operacao selecionado
current_mode = st.session_state.get("app_mode", "real")
selected_mode = render_sidebar(
    authenticated=st.session_state.authenticated,
    current_mode=current_mode
)

if selected_mode != current_mode:
    st.session_state.app_mode = selected_mode
    # Limpeza estrita dos estados ao alternar de modo para evitar contaminacao
    st.session_state.form_data = None
    st.session_state.campaign_result = None
    st.session_state.strategy = None
    st.session_state.copy_content = None
    st.session_state.review_and_final = None
    st.session_state.image_prompts = None
    st.session_state.research_data = None
    st.session_state.guardrails_result = None
    st.session_state.report_md = None
    st.session_state.report_txt = None
    st.session_state.automation_status = None
    st.session_state.last_submission_sent = False
    st.session_state.ai_workflow_states = {
        "briefing": "pending",
        "research": "pending",
        "strategist": "pending",
        "copywriter": "pending",
        "reviewer": "pending",
        "image_designer": "pending",
        "ready": "pending"
    }
    st.rerun()

is_demo_mode = (st.session_state.app_mode == "demo")

# Renderiza o cabecalho premium da marca com badge contextual
render_app_header(is_demo=is_demo_mode)

# ==============================================================================
# SEÇÃO 1: CONFIGURAÇÃO DA CAMPANHA (MODO REAL OU MODO DEMONSTRAÇÃO)
# ==============================================================================
if is_demo_mode:
    st.markdown("### 🎭 1. MODO DEMONSTRAÇÃO — Apresentação Offline & Didática")
    st.markdown(
        "<span style='color: #94A3B8; font-size: 0.92rem;'>"
        "Ambiente 100% offline para apresentações acadêmicas. Simula a execução conceitual dos quatro agentes "
        "e dos guardrails sem depender de chamadas externas ao OpenRouter, Tavily Search API ou n8n."
        "</span>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div style="background: rgba(139, 92, 246, 0.08); border: 1px solid rgba(139, 92, 246, 0.25); border-radius: 12px; padding: 1.2rem; margin-bottom: 1.2rem;">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.6rem;">
                <div style="font-weight: 700; color: #F8FAFC; font-size: 1.1rem; display: flex; align-items: center; gap: 0.5rem;">
                    <span>☕</span> <span>Cenário Pré-Carregado: Café Aurora (Fortaleza — CE)</span>
                </div>
                <span class="badge-pill badge-pill-cyan">🔒 100% Offline • Sem Custos</span>
            </div>
            <p style="color: #CBD5E1; font-size: 0.88rem; margin: 0 0 0.8rem 0; line-height: 1.5;">
                <strong>Campanha:</strong> 'Sua Pausa Especial' • <strong>Oferta:</strong> Cafeteria artesanal focada em cafés especiais, bebidas quentes/geladas e acompanhamentos frescos.<br>
                <strong>Público-Alvo:</strong> Jovens adultos, universitários e profissionais de 20 a 45 anos interessados em cafés especiais e momentos de pausa na rotina.<br>
                <strong>Canais:</strong> Instagram, WhatsApp, E-mail marketing.
            </p>
            <div style="font-size: 0.78rem; color: #A78BFA;">
                ℹ️ Clique em <strong>'▶ Iniciar demonstração'</strong> para acompanhar a execução didática e carregar os resultados fictícios dos 4 agentes.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_demo1, col_demo2 = st.columns([1.5, 1])
    with col_demo1:
        start_demo_button = st.button("▶ Iniciar demonstração", type="primary", use_container_width=True)
    with col_demo2:
        if st.button("🔄 Alternar para Modo Real", use_container_width=True):
            st.session_state.app_mode = "real"
            st.session_state.form_data = None
            st.session_state.campaign_result = None
            st.session_state.strategy = None
            st.session_state.copy_content = None
            st.session_state.review_and_final = None
            st.session_state.image_prompts = None
            st.session_state.research_data = None
            st.session_state.guardrails_result = None
            st.session_state.report_md = None
            st.session_state.report_txt = None
            st.session_state.automation_status = None
            st.session_state.last_submission_sent = False
            st.session_state.ai_workflow_states = {
                "briefing": "pending",
                "research": "pending",
                "strategist": "pending",
                "copywriter": "pending",
                "reviewer": "pending",
                "image_designer": "pending",
                "ready": "pending"
            }
            st.rerun()

    if start_demo_button:
        st.session_state.ai_workflow_states = {
            "briefing": "completed",
            "research": "pending",
            "strategist": "pending",
            "copywriter": "pending",
            "reviewer": "pending",
            "image_designer": "pending",
            "ready": "pending"
        }

        with st.status("🚀 Reprodução Ilustrativa do Pipeline (Modo Demonstração)...", expanded=True) as status_box:
            def on_demo_progress(stage: str, state: str, message: str, result: Any = None):
                st.session_state.ai_workflow_states[stage] = state
                status_box.write(f"🔄 {message}")
                if state == "completed" and result is not None:
                    if stage == "research":
                        st.session_state.research_data = result
                    elif stage == "strategist":
                        st.session_state.strategy = result
                    elif stage == "copywriter":
                        st.session_state.copy_content = result
                    elif stage == "reviewer":
                        st.session_state.review_and_final = result
                    elif stage == "image_designer":
                        st.session_state.image_prompts = result

            demo_campaign = run_demo_workflow_simulation(progress_callback=on_demo_progress)
            rep_md, rep_txt = build_demo_campaign_reports(demo_campaign)

            st.session_state.form_data = demo_campaign["form_data"]
            st.session_state.research_data = demo_campaign["research_data"]
            st.session_state.strategy = demo_campaign["strategy"]
            st.session_state.copy_content = demo_campaign["preliminary_copy"]
            st.session_state.review_and_final = demo_campaign["review_and_final"]
            st.session_state.image_prompts = demo_campaign["image_prompts"]
            st.session_state.guardrails_result = demo_campaign["guardrails_result"]
            st.session_state.campaign_result = demo_campaign
            st.session_state.report_md = rep_md
            st.session_state.report_txt = rep_txt
            st.session_state.last_submission_sent = False
            st.session_state.automation_status = None

            status_box.update(label="✨ Simulação do Modo Demonstração concluída com sucesso!", state="complete", expanded=False)
            st.success("✅ Resultados ilustrativos dos 4 agentes e validação dos Guardrails carregados!")
            st.rerun()

else:
    st.markdown("### 🎯 1. Briefing e Configuração da Campanha")
    st.markdown(
        "<span style='color: #94A3B8; font-size: 0.92rem;'>"
        "Estruture as informações fundamentais do produto ou serviço. "
        "Os agentes de IA utilizarão estes dados para criar uma estratégia coesa e redigir conteúdos sem inventar fatos."
        "</span>",
        unsafe_allow_html=True
    )

    with st.form(key="campaign_form"):
        col_group_a, col_group_b = st.columns(2)

        with col_group_a:
            st.markdown(
                """
                <div class="card-header-title">
                    <span>📦 Grupo A: Informações da Oferta</span>
                </div>
                """,
                unsafe_allow_html=True
            )

            product_name = st.text_input(
                "Nome do produto ou serviço *",
                placeholder="Ex: Consultoria Financeira Ágil, Café Especial da Serra...",
                max_chars=120,
                help="Campo obrigatório. Identificação clara da sua oferta."
            )

            product_description = st.text_area(
                "Descrição do produto ou serviço *",
                placeholder="Descreva o que é a oferta, como funciona e quais problemas ela resolve...",
                max_chars=1000,
                height=130,
                help="Campo obrigatório. Dados essenciais para a IA trabalhar sem inventar características."
            )

            differentials = st.text_area(
                "Diferenciais reais (opcional)",
                placeholder="Ex: Metodologia própria em 3 passos, diagnóstico inicial sem custo, suporte ágil...",
                max_chars=500,
                height=85,
                help="Características exclusivas e verdadeiras que devem ser destacadas na campanha."
            )

        with col_group_b:
            st.markdown(
                """
                <div class="card-header-title">
                    <span>🎯 Grupo B: Estratégia e Comunicação</span>
                </div>
                """,
                unsafe_allow_html=True
            )

            target_audience = st.text_input(
                "Público-alvo *",
                placeholder="Ex: Microempreendedores e donos de pequenos negócios que faturam até R$ 50 mil...",
                max_chars=300,
                help="Campo obrigatório. Para quem a comunicação é direcionada."
            )

            objective = st.selectbox(
                "Objetivo da campanha *",
                options=[
                    "Atrair novos clientes e gerar leads",
                    "Divulgar lançamento de produto ou serviço",
                    "Promover oferta especial ou evento",
                    "Fortalecer autoridade de marca e engajamento"
                ],
                help="Finalidade estratégica principal da campanha."
            )

            tone = st.selectbox(
                "Tom de comunicação *",
                options=[
                    "Profissional e confiável",
                    "Informal, amigável e acessível",
                    "Criativo, descontraído e dinâmico",
                    "Persuasivo, urgente e direto ao ponto"
                ],
                help="A voz e o estilo que devem permear todas as mensagens."
            )

            cta = st.text_input(
                "Chamada para ação desejada — CTA (opcional)",
                placeholder="Ex: Agende uma sessão gratuita de 30 minutos pelo WhatsApp...",
                max_chars=150,
                help="Ação clara que o cliente deve tomar ao ler o conteúdo."
            )

        st.markdown(
            """
            <div class="card-header-title" style="margin-top: 1rem;">
                <span>📢 Grupo C: Canais de Distribuição Selecionados</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        channels = st.multiselect(
            "Canais de divulgação * (Selecione ao menos um canal para geração)",
            options=["Instagram", "WhatsApp", "E-mail marketing"],
            default=["Instagram", "WhatsApp", "E-mail marketing"],
            help="O Agente Copywriter criará conteúdos adaptados com exclusividade aos canais marcados."
        )

        st.markdown("<br>", unsafe_allow_html=True)
        submit_button = st.form_submit_button("✨ Gerar campanha com IA", type="primary", use_container_width=True)

    # Validacao e disparo do pipeline multiagente
    if submit_button:
        errors = []
        if not product_name.strip():
            errors.append("O campo **Nome do produto ou serviço** é obrigatório.")
        if not product_description.strip():
            errors.append("O campo **Descrição do produto ou serviço** é obrigatório.")
        if not target_audience.strip():
            errors.append("O campo **Público-alvo** é obrigatório.")
        if not channels:
            errors.append("Selecione **ao menos um canal de divulgação**.")

        if errors:
            for err in errors:
                st.error(f"❌ {err}")
        else:
            st.session_state.form_data = {
                "product_name": product_name.strip(),
                "product_description": product_description.strip(),
                "target_audience": target_audience.strip(),
                "objective": objective,
                "tone": tone,
                "differentials": differentials.strip() if differentials else "",
                "cta": cta.strip() if cta else "",
                "channels": channels
            }

            # Inicializa os estados do workflow visual
            st.session_state.ai_workflow_states = {
                "briefing": "completed",
                "research": "pending",
                "strategist": "pending",
                "copywriter": "pending",
                "reviewer": "pending",
                "image_designer": "pending",
                "ready": "pending"
            }

            with st.status("🚀 Orquestrando Pipeline Multiagente...", expanded=True) as status_box:
                try:
                    def on_agent_progress(stage: str, state: str, message: str, result: Any = None):
                        st.session_state.ai_workflow_states[stage] = state
                        status_box.write(f"🔄 {message}")
                        # Preservacao incremental de resultados intermediarios
                        if state == "completed" and result:
                            if stage == "research":
                                st.session_state.research_data = result
                            elif stage == "strategist":
                                st.session_state.strategy = result
                            elif stage == "copywriter":
                                st.session_state.copy_content = result
                            elif stage == "reviewer":
                                st.session_state.review_and_final = result
                            elif stage == "image_designer":
                                st.session_state.image_prompts = result

                    campaign_data = generate_full_campaign(
                        st.session_state.form_data,
                        progress_callback=on_agent_progress
                    )

                    report_md, report_txt = build_campaign_reports(campaign_data)

                    st.session_state.research_data = campaign_data.get("research_data")
                    st.session_state.strategy = campaign_data["strategy"]
                    st.session_state.copy_content = campaign_data["preliminary_copy"]
                    st.session_state.review_and_final = campaign_data["review_and_final"]
                    st.session_state.image_prompts = campaign_data.get("image_prompts", "")
                    st.session_state.campaign_result = campaign_data
                    st.session_state.report_md = report_md
                    st.session_state.report_txt = report_txt
                    st.session_state.last_submission_sent = False
                    st.session_state.automation_status = None

                    # Guardrails: prioriza o resultado ja calculado pelo LangGraph internamente.
                    # Fallback: executa localmente caso o grafo nao retorne guardrails_result.
                    guardrails_from_graph = campaign_data.get("guardrails_result")
                    if guardrails_from_graph and isinstance(guardrails_from_graph, dict):
                        st.session_state.guardrails_result = guardrails_from_graph
                    else:
                        st.session_state.guardrails_result = validate_campaign_guardrails(
                            campaign_data=campaign_data,
                            report_markdown=report_md
                        )

                    st.session_state.ai_workflow_states["ready"] = "completed"
                    status_box.update(label="✨ Campanha gerada e revisada com sucesso!", state="complete", expanded=False)

                    # Mensagem de conclusao diferenciada: completa vs incompleta vs bloqueada
                    _gr = st.session_state.guardrails_result or {}
                    _is_blocked = bool(_gr.get("is_blocked", False))
                    _is_complete = bool(campaign_data.get("is_complete", True))

                    if _is_blocked:
                        st.warning(
                            "⚠️ Campanha gerada, mas os **Guardrails** identificaram problemas críticos de compliance. "
                            "O envio automático está bloqueado até a correção do briefing. "
                            "Veja o painel de Guardrails abaixo para detalhes."
                        )
                    elif not _is_complete:
                        st.warning(
                            "⚠️ Um ou mais agentes não conseguiram completar sua etapa integralmente (limite de tokens ou indisponibilidade do modelo). "
                            "O relatório foi gerado com marcação **[RASCUNHO INCOMPLETO]** nas seções afetadas. "
                            "Recomendamos revisar e reexecutar com um briefing mais curto."
                        )
                    else:
                        st.success("✅ Todos os 4 agentes completaram suas etapas com êxito!")

                except Exception as e:
                    for k, v in st.session_state.ai_workflow_states.items():
                        if v == "running":
                            st.session_state.ai_workflow_states[k] = "error"
                    status_box.update(label="❌ Falha na orquestração dos agentes", state="error", expanded=True)
                    safe_err_msg = sanitize_error_message(e)
                    st.error(f"Erro durante a execução do pipeline: {safe_err_msg}")

                    # Preserva o estado das etapas preliminares concluidas
                    if (
                        st.session_state.get("research_data")
                        or st.session_state.get("strategy")
                        or st.session_state.get("copy_content")
                        or st.session_state.get("review_and_final")
                        or st.session_state.get("image_prompts")
                    ):
                        st.info("ℹ️ As etapas já concluídas com sucesso foram preservadas nas abas de resultados abaixo.")

st.divider()

# ==============================================================================
# SEÇÃO 2: PAINEL AI WORKFLOW (VISUALIZAÇÃO DO PIPELINE)
# ==============================================================================
st.markdown("### 🤖 AI Workflow")
st.markdown(
    "<span style='color: #94A3B8; font-size: 0.92rem;'>"
    "Acompanhe cada etapa da construção da sua campanha pelos agentes de IA generativa."
    "</span>",
    unsafe_allow_html=True
)

# Renderiza o estado atual do workflow
render_ai_workflow_panel(st.session_state.ai_workflow_states)

st.divider()

# ==============================================================================
# SEÇÃO 3: DASHBOARD DE RESULTADOS (MODERN SAAS STUDIO)
# ==============================================================================
st.markdown("### 📊 Studio Dashboard — Resultados da Campanha")

has_campaign_content = bool(
    st.session_state.get("campaign_result")
    or st.session_state.get("strategy")
    or st.session_state.get("copy_content")
    or st.session_state.get("review_and_final")
    or st.session_state.get("image_prompts")
    or st.session_state.get("research_data")
)

if not st.session_state.get("form_data") or not has_campaign_content:
    st.info("ℹ️ Preencha os campos de configuração acima e clique em **Gerar campanha com IA** para visualizar os resultados.")
else:
    # Metricas reais de acompanhamento
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        prod_title = str(st.session_state.form_data.get("product_name", "Campanha"))
        st.metric(label="Produto / Oferta", value=prod_title[:18] + ("..." if len(prod_title) > 18 else ""))
    with mcol2:
        completed_agents = sum(
            1 for st_name in ["strategist", "copywriter", "reviewer", "image_designer"]
            if st.session_state.ai_workflow_states.get(st_name) == "completed"
        )
        st.metric(label="Agentes Executados", value=f"{completed_agents} de 4 Concluídos")
    with mcol3:
        ch_count = len(st.session_state.form_data.get("channels", []))
        st.metric(label="Canais Gerados", value=f"{ch_count} Canais")
    with mcol4:
        campaign_status_label = "Revisada & Pronta" if st.session_state.get("campaign_result") else "Parcial / Em Andamento"
        st.metric(label="Status da Campanha", value=campaign_status_label)

    st.markdown("<br>", unsafe_allow_html=True)

    # Abas estruturadas de apresentacao
    tab_strategy, tab_copy, tab_review, tab_images = st.tabs([
        "📋 1. Estratégia de Marketing",
        "✍️ 2. Conteúdos Multicanal",
        "🔍 3. AI Review & Otimização",
        "🎨 4. Prompts de Imagem"
    ])

    with tab_strategy:
        st.markdown(
            """
            <div class="card-header-title">
                <span>🎯 Plano Estratégico & Pesquisa de Tendências (Agente 1)</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Exibição de fontes de pesquisa de mercado
        res_data = st.session_state.get("research_data") or (st.session_state.get("campaign_result") or {}).get("research_data")
        if res_data and isinstance(res_data, dict):
            if res_data.get("is_demo"):
                query_text = res_data.get("query", "")
                sources_count = len(res_data.get("results", []))
                st.markdown(
                    f"""
                    <div style="background: rgba(139, 92, 246, 0.08); border: 1px solid rgba(139, 92, 246, 0.25); border-radius: 10px; padding: 1rem; margin-bottom: 1rem;">
                        <div style="font-weight: 700; color: #C4B5FD; font-size: 0.95rem; margin-bottom: 0.35rem;">
                            🌐 Pesquisa ilustrativa — Modo Demonstração. Nenhuma consulta externa foi realizada.
                        </div>
                        <div style="font-size: 0.82rem; color: #94A3B8;">
                            Consulta conceitual de referência: <code>{query_text}</code> • Fontes ilustrativas pré-carregadas: <strong>{sources_count}</strong>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                for idx, item in enumerate(res_data["results"], 1):
                    src_title = item.get("title", f"Exemplo {idx}")
                    src_date = item.get("published_date")
                    date_info = f" • <span style='color: #64748B;'>{src_date}</span>" if src_date else ""
                    st.markdown(f"**{idx}. {src_title}**{date_info}", unsafe_allow_html=True)
                    if item.get("content"):
                        with st.expander(f"Ver trecho ilustrativo da fonte {idx}", expanded=False):
                            st.caption(item.get("content"))
                st.markdown("<br>", unsafe_allow_html=True)
            elif res_data.get("success") and res_data.get("results"):
                cache_badge = " • <em>(Resultados de cache em memória)</em>" if res_data.get("cached") else ""
                query_text = res_data.get("query", "")
                sources_count = len(res_data.get("results", []))

                st.markdown(
                    f"""
                    <div style="background: rgba(139, 92, 246, 0.08); border: 1px solid rgba(139, 92, 246, 0.25); border-radius: 10px; padding: 1rem; margin-bottom: 1rem;">
                        <div style="font-weight: 700; color: #C4B5FD; font-size: 0.95rem; margin-bottom: 0.35rem;">
                            🌐 Fontes Reais de Mercado Consultadas em Tempo Real (Tavily API)
                        </div>
                        <div style="font-size: 0.82rem; color: #94A3B8;">
                            Consulta: <code>{query_text}</code> • Fontes reais consultadas: <strong>{sources_count}</strong>{cache_badge}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                for idx, item in enumerate(res_data["results"], 1):
                    src_title = item.get("title", f"Fonte {idx}")
                    src_url = item.get("url", "#")
                    src_date = item.get("published_date")
                    date_info = f" • <span style='color: #64748B;'>Publicado em: {src_date}</span>" if src_date else ""
                    st.markdown(f"**{idx}. [{src_title}]({src_url})**{date_info}", unsafe_allow_html=True)
                    if item.get("content"):
                        with st.expander(f"Ver trecho observado da fonte {idx}", expanded=False):
                            st.caption(item.get("content"))
                st.markdown("<br>", unsafe_allow_html=True)
            elif not res_data.get("success") or not res_data.get("results"):
                err_reason = res_data.get("error") or "Serviço temporariamente indisponível"
                st.warning(
                    f"⚠️ **Pesquisa de tendências externas indisponível:** {err_reason}\n\n"
                    "*A estratégia foi fundamentada estritamente nas informações fornecidas no briefing, sem invenção de fontes ou URLs.*"
                )
                st.markdown("<br>", unsafe_allow_html=True)

        if st.session_state.get("strategy"):
            st.markdown(st.session_state.strategy)
        else:
            st.info("A estratégia de marketing será exibida aqui após a geração.")

    with tab_copy:
        st.markdown(
            """
            <div class="card-header-title">
                <span>✍️ Textos Publicitários por Canal (Agente 2 — Copywriter)</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.session_state.get("copy_content"):
            st.markdown(st.session_state.copy_content)
        else:
            st.warning("⚠️ Os textos publicitários por canal ainda não foram gerados. Execute a campanha para gerar este conteúdo.")

    with tab_review:
        st.markdown(
            """
            <div class="card-header-title">
                <span>🔍 Avaliação Crítica, SEO e Versão Final (Agente 3 — Revisor)</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.session_state.get("review_and_final"):
            st.markdown(st.session_state.review_and_final)
        else:
            st.warning("⚠️ A revisão crítica e versão final ainda não foram geradas. Execute a campanha para gerar este conteúdo.")

    with tab_images:
        st.markdown(
            """
            <div class="card-header-title">
                <span>🎨 Direção Visual e Prompts de Imagem (Agente 4 — Designer de Prompts)</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.caption(
            "ℹ️ **Nota:** Esta aba exibe prompts textuais otimizados (em inglês) para uso em ferramentas de geração de imagens "
            "como Midjourney, DALL-E ou Flux. Os prompts são gerados pelo Agente 4 — nenhuma imagem é gerada diretamente aqui."
        )
        if st.session_state.get("image_prompts"):
            st.markdown(st.session_state.image_prompts)
        else:
            st.warning("⚠️ Os prompts visuais e diretrizes de arte ainda não foram gerados. Execute a campanha para gerar este conteúdo.")

st.divider()

# ==============================================================================
# SEÇÃO 4: EXPORTAÇÃO E AUTOMAÇÃO N8N
# ==============================================================================
st.markdown("### ⚡ Automation Workflow & Exportação")
st.markdown(
    "<span style='color: #94A3B8; font-size: 0.92rem;'>"
    "Exporte os arquivos da campanha ou utilize a automação integrada para encaminhar o relatório para revisão por e-mail."
    "</span>",
    unsafe_allow_html=True
)

# Painel de Exportacao
st.markdown(
    """
    <div class="card-header-title" style="font-size: 1rem; margin-top: 0.5rem;">
        <span>📥 Download dos Materiais da Campanha</span>
    </div>
    """,
    unsafe_allow_html=True
)

col_exp1, col_exp2 = st.columns(2)

product_slug = "campanha"
if st.session_state.form_data:
    raw_slug = st.session_state.form_data.get("product_name", "campanha").lower()
    product_slug = "".join(c if c.isalnum() else "_" for c in raw_slug).strip("_")

if is_demo_mode:
    product_slug = "cafe_aurora_demonstracao"

with col_exp1:
    if st.session_state.campaign_result and st.session_state.get("report_md"):
        st.download_button(
            label="📥 Baixar Campanha Completa em Markdown (.md)",
            data=st.session_state.report_md,
            file_name=f"marketflow_{product_slug}.md",
            mime="text/markdown",
            use_container_width=True
        )
    else:
        st.button("📥 Baixar em Markdown (.md)", disabled=True, use_container_width=True)

with col_exp2:
    if st.session_state.campaign_result and st.session_state.get("report_txt"):
        st.download_button(
            label="📄 Baixar Campanha em Texto Puro (.txt)",
            data=st.session_state.report_txt,
            file_name=f"marketflow_{product_slug}.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.button("📄 Baixar em Texto Puro (.txt)", disabled=True, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Painel de Guardrails & Compliance
is_guardrail_blocked = False
if st.session_state.get("campaign_result"):
    if not st.session_state.get("guardrails_result"):
        st.session_state.guardrails_result = validate_campaign_guardrails(
            campaign_data=st.session_state.campaign_result,
            report_markdown=st.session_state.get("report_md", "")
        )
    render_guardrails_panel(st.session_state.guardrails_result)
    is_guardrail_blocked = bool(st.session_state.guardrails_result.get("is_blocked", False))

# Painel Visual do Automation Workflow (n8n & Gmail)
current_auto_state = "ready"
if is_demo_mode:
    current_auto_state = "ready"
elif st.session_state.get("automation_status"):
    if st.session_state.automation_status.get("success"):
        current_auto_state = "completed"
    elif st.session_state.automation_status.get("uncertain"):
        current_auto_state = "timeout"
    else:
        current_auto_state = "error"

render_automation_workflow_panel(current_auto_state)

st.markdown("<br>", unsafe_allow_html=True)

if is_demo_mode:
    st.markdown(
        """
        <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 10px; padding: 1rem; margin-bottom: 1rem;">
            <strong style="color: #FCA5A5;">🔒 Disparos Externos Desativados no Modo Demonstração:</strong>
            <p style="color: #CBD5E1; font-size: 0.85rem; margin: 0.3rem 0 0 0;">
                Para proteger sistemas em produção e evitar disparos acidentais com dados fictícios, 
                as integrações com n8n, Gmail e Google Sheets estão estritamente bloqueadas. 
                Para testar o fluxo de automação real, alterne para o Modo Real.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

col_auth, col_send = st.columns([1.2, 1.8])

with col_auth:
    confirm_review = st.checkbox(
        "Autorizo o envio: Confirmo que revisei os conteúdos gerados.",
        disabled=(st.session_state.campaign_result is None or is_guardrail_blocked or is_demo_mode)
    )

with col_send:
    send_label = (
        "🔒 Disparo n8n Desativado (Modo Demonstração)"
        if is_demo_mode else
        "🚀 Disparar automação n8n (Encaminhar para revisão via Gmail)"
    )
    send_button = st.button(
        send_label,
        disabled=(st.session_state.campaign_result is None or not confirm_review or is_guardrail_blocked or is_demo_mode),
        type="primary" if (st.session_state.campaign_result and confirm_review and not is_guardrail_blocked and not is_demo_mode) else "secondary",
        use_container_width=True
    )

if is_guardrail_blocked:
    st.error(
        "⛔ O encaminhamento para a automação n8n está bloqueado devido a inconsistências críticas identificadas nos Guardrails. "
        "Você ainda pode visualizar e baixar os relatórios acima para efetuar as correções necessárias no briefing."
    )

if send_button:
    if is_demo_mode:
        res = block_demo_automation()
        st.session_state.automation_status = res
        st.warning(f"⚠️ {res['message']}")
    elif st.session_state.get("last_submission_sent"):
        st.info("ℹ️ Esta campanha já foi encaminhada com sucesso para o n8n nesta sessão.")
    else:
        with st.spinner("⚡ Conectando ao Webhook do n8n e disparando e-mail via Gmail API..."):
            render_automation_workflow_panel("sending")
            try:
                res = send_campaign_to_n8n(
                    product_name=st.session_state.form_data["product_name"],
                    objective=st.session_state.form_data["objective"],
                    channels=st.session_state.form_data["channels"],
                    report_markdown=st.session_state.report_md,
                    is_demo=is_demo_mode
                )
            except Exception as e:
                res = {
                    "success": False,
                    "uncertain": False,
                    "message": f"Erro inesperado ao conectar ao n8n: {sanitize_error_message(e)}"
                }
            st.session_state.automation_status = res

            if res["success"]:
                st.session_state.last_submission_sent = True
                st.success(f"✅ {res['message']}")
                st.caption(f"ID da submissão: `{res.get('submission_id')}`")
            elif res.get("uncertain"):
                st.warning(f"⚠️ {res['message']}")
            else:
                st.error(f"❌ {res['message']}")
            st.rerun()

elif st.session_state.get("automation_status"):
    prev = st.session_state.automation_status
    if prev.get("success"):
        st.success(f"✅ {prev['message']}")
        st.caption(f"ID da submissão: `{prev.get('submission_id')}`")
    elif prev.get("uncertain"):
        st.warning(f"⚠️ {prev['message']}")
    else:
        st.error(f"❌ {prev['message']}")

st.markdown(
    """
    <div style="font-size: 0.8rem; color: #64748B; border-top: 1px solid #1E293B; padding-top: 1rem; margin-top: 2rem;">
        <div style="margin-bottom: 0.5rem;">
            ⚠️ <strong>Aviso Ético e Legal:</strong> Os textos, estratégias e sugestões de SEO contidos nesta plataforma 
            são gerados por Inteligência Artificial Generativa com caráter orientativo. Todo conteúdo deve ser submetido 
            à criteriosa validação e revisão humana antes de veiculação pública ou comercial.
        </div>
        <div style="font-size: 0.75rem; color: #94A3B8; border-top: 1px dashed rgba(255,255,255,0.06); padding-top: 0.5rem;">
            Desenvolvido por <strong>Bruno Gabriel Nunes</strong> • Programa Geração Tech 2026 — Curso de IA Generativa
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
