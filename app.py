"""
Campanha IA — Central Automatizada de Campanhas de Marketing Multicanal
Interface principal desenvolvida com Streamlit.
"""

import streamlit as st
from agents import generate_full_campaign, build_campaign_reports
from automation_service import send_campaign_to_n8n

# Configuracao da pagina
st.set_page_config(
    page_title="Campanha IA",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializacao de variaveis no session_state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "form_data" not in st.session_state:
    st.session_state.form_data = None

if "campaign_result" not in st.session_state:
    st.session_state.campaign_result = None

if "automation_status" not in st.session_state:
    st.session_state.automation_status = None


def check_password() -> bool:
    """Verifica a senha de demonstracao configurada no secrets.toml."""
    expected_password = st.secrets.get("DEMO_ACCESS_PASSWORD", "")
    
    # Se nao houver senha definida, libera o acesso direto
    if not expected_password:
        return True

    if st.session_state.authenticated:
        return True

    st.markdown("### 🔐 Acesso Restrito à Demonstração")
    st.markdown("Por favor, informe a senha de acesso para utilizar a aplicação.")

    with st.form("login_form"):
        password_input = st.text_input("Senha de acesso:", type="password")
        submit_button = st.form_submit_button("Entrar")

        if submit_button:
            if password_input == expected_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Senha incorreta. Verifique a credencial informada.")

    st.stop()
    return False


# Valida autenticacao antes de exibir o restante da aplicacao
check_password()

# Barra lateral com informacoes do sistema
with st.sidebar:
    st.title("🚀 Campanha IA")
    st.markdown(
        """
        **Central Automatizada de Marketing Multicanal**
        
        Sistema acadêmico orientado por arquitetura multiagente com IA generativa e automação n8n.
        
        ---
        **Pipeline de Agentes:**
        1. 🎯 *Estrategista de Marketing*
        2. ✍️ *Copywriter Multicanal*
        3. 🔍 *Revisor e Otimizador*
        
        ---
        *(Programa Geração Tech — IA Generativa 2026)*
        """
    )
    if st.session_state.authenticated and st.secrets.get("DEMO_ACCESS_PASSWORD", ""):
        if st.button("Sair da sessão"):
            st.session_state.authenticated = False
            st.session_state.form_data = None
            st.session_state.campaign_result = None
            st.rerun()

# Cabecalho principal
st.title("🎯 Criação de Campanha Multicanal")
st.markdown(
    "Preencha as informações sobre o produto ou serviço abaixo. "
    "Três agentes de inteligência artificial trabalharão em sequência para planejar, redigir e revisar sua campanha."
)

st.divider()

# Area 1: Formulario de Entrada do Usuario
st.subheader("1. Informações da Campanha")

with st.form(key="campaign_form"):
    col1, col2 = st.columns(2)

    with col1:
        product_name = st.text_input(
            "Nome do produto ou serviço *",
            placeholder="Ex: Consultoria Financeira Ágil, Café Especial da Serra...",
            max_chars=120,
            help="Campo obrigatório. Identificação clara da sua oferta."
        )

        objective = st.selectbox(
            "Objetivo da campanha *",
            options=[
                "Divulgar lançamento de produto ou serviço",
                "Atrair novos clientes e gerar leads",
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

        channels = st.multiselect(
            "Canais de divulgação * (selecione ao menos um)",
            options=["Instagram", "WhatsApp", "E-mail marketing"],
            default=["Instagram", "WhatsApp", "E-mail marketing"],
            help="Os textos serão criados e adaptados especificamente para os canais marcados."
        )

    with col2:
        product_description = st.text_area(
            "Descrição do produto ou serviço *",
            placeholder="Descreva o que é a oferta, como funciona e quais problemas ela resolve...",
            max_chars=1000,
            height=120,
            help="Campo obrigatório. Dados essenciais para a inteligência artificial trabalhar sem inventar características."
        )

        target_audience = st.text_input(
            "Público-alvo *",
            placeholder="Ex: Jovens profissionais de 25 a 35 anos, pequenos empreendedores...",
            max_chars=300,
            help="Campo obrigatório. Para quem a comunicação é direcionada."
        )

        differentials = st.text_area(
            "Diferenciais reais (opcional)",
            placeholder="Ex: Metodologia própria, atendimento em até 1h, sem taxa de adesão...",
            max_chars=500,
            height=80,
            help="Características exclusivas e verdadeiras que devem ser destacadas."
        )

        cta = st.text_input(
            "Chamada para ação desejada - CTA (opcional)",
            placeholder="Ex: Envie uma mensagem pelo WhatsApp e receba um diagnóstico...",
            max_chars=150,
            help="Ação clara que o cliente deve tomar ao ler o conteúdo."
        )

    submit_button = st.form_submit_button("🚀 Gerar campanha", use_container_width=True)

# Validacao do Formulario
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
        
        # Pipeline Multiagente: Agente 1 (Estrategista) -> Agente 2 (Copywriter) -> Agente 3 (Revisor)
        with st.status("🤖 Orquestrando os 3 Agentes de Inteligência Artificial...", expanded=True) as status:
            try:
                status.write("🎯 **Etapa 1/3:** Agente 1 (Estrategista) elaborando o plano de marketing...")
                # Funcao de callback de progresso para a UI
                def on_progress(message: str, step: int):
                    status.write(f"🔄 **Etapa {step}/3:** {message}")

                campaign_data = generate_full_campaign(st.session_state.form_data)
                report_md, report_txt = build_campaign_reports(campaign_data)
                
                st.session_state.strategy = campaign_data["strategy"]
                st.session_state.copy_content = campaign_data["preliminary_copy"]
                st.session_state.review_and_final = campaign_data["review_and_final"]
                st.session_state.campaign_result = campaign_data
                st.session_state.report_md = report_md
                st.session_state.report_txt = report_txt
                st.session_state.last_submission_sent = False
                st.session_state.automation_status = None
                
                status.update(label="🚀 Campanha gerada e revisada com sucesso!", state="complete", expanded=False)
                st.success("✅ Orquestração dos 3 agentes concluída com êxito!")
            except Exception as e:
                status.update(label="❌ Falha na orquestração dos agentes", state="error", expanded=True)
                st.error(f"Erro durante a geração da campanha: {e}")

st.divider()

# Area 2: Resultados (Apresentacao dos Agentes)
st.subheader("2. Resultados da Campanha")

if not st.session_state.form_data or not st.session_state.campaign_result:
    st.info("ℹ️ Preencha o formulário acima e clique em **Gerar campanha** para iniciar a orquestração.")
else:
    st.markdown(
        f"**Campanha ativa:** `{st.session_state.form_data['product_name']}` | "
        f"**Canais:** {', '.join(st.session_state.form_data['channels'])}"
    )
    
    # Abas estruturadas de apresentacao
    tab_strategy, tab_copy, tab_review = st.tabs([
        "📋 1. Estratégia de Marketing",
        "✍️ 2. Conteúdos por Canal",
        "🔍 3. Revisão e Otimização"
    ])
    
    with tab_strategy:
        if st.session_state.get("strategy"):
            st.markdown(st.session_state.strategy)
        else:
            st.info("A estratégia do Agente 1 (Estrategista) será exibida aqui após a execução.")
        
    with tab_copy:
        if st.session_state.get("copy_content"):
            st.markdown(st.session_state.copy_content)
        else:
            st.info("Os textos publicitários do Agente 2 (Copywriter) serão exibidos aqui após a execução.")
        
    with tab_review:
        if st.session_state.get("review_and_final"):
            st.markdown(st.session_state.review_and_final)
        else:
            st.info("A análise crítica, SEO orientativo e versão final do Agente 3 serão exibidos aqui.")

st.divider()

# Area 3: Exportacao e Automacao
st.subheader("3. Exportação e Automação")
st.markdown("Após a conclusão da geração, você poderá baixar o relatório ou encaminhá-lo para revisão.")

col_exp1, col_exp2, col_auto = st.columns([1, 1, 2])

product_slug = "campanha"
if st.session_state.form_data:
    raw_slug = st.session_state.form_data.get("product_name", "campanha").lower()
    product_slug = "".join(c if c.isalnum() else "_" for c in raw_slug).strip("_")

with col_exp1:
    if st.session_state.campaign_result and st.session_state.get("report_md"):
        st.download_button(
            label="📥 Baixar em Markdown (.md)",
            data=st.session_state.report_md,
            file_name=f"campanha_{product_slug}.md",
            mime="text/markdown",
            use_container_width=True
        )
    else:
        st.button("📥 Baixar em Markdown (.md)", disabled=True, use_container_width=True)

with col_exp2:
    if st.session_state.campaign_result and st.session_state.get("report_txt"):
        st.download_button(
            label="📄 Baixar em Texto (.txt)",
            data=st.session_state.report_txt,
            file_name=f"campanha_{product_slug}.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        st.button("📄 Baixar em Texto (.txt)", disabled=True, use_container_width=True)

with col_auto:
    confirm_review = st.checkbox(
        "Confirmo que revisei o conteúdo gerado e autorizo o envio para revisão.",
        disabled=(st.session_state.campaign_result is None)
    )
    send_button = st.button(
        "✉️ Encaminhar para revisão por e-mail (n8n)",
        disabled=(st.session_state.campaign_result is None or not confirm_review),
        use_container_width=True
    )

    if send_button:
        if st.session_state.get("last_submission_sent"):
            st.info("ℹ️ Esta campanha já foi encaminhada com sucesso nesta sessão.")
        else:
            with st.spinner("✉️ Enviando relatório ao n8n e disparando e-mail pelo Gmail..."):
                res = send_campaign_to_n8n(
                    product_name=st.session_state.form_data["product_name"],
                    objective=st.session_state.form_data["objective"],
                    channels=st.session_state.form_data["channels"],
                    report_markdown=st.session_state.report_md
                )
                st.session_state.automation_status = res
                if res["success"]:
                    st.session_state.last_submission_sent = True
                    st.success(f"✅ {res['message']}")
                    st.caption(f"ID da submissão: `{res.get('submission_id')}`")
                elif res.get("uncertain"):
                    st.warning(f"⚠️ {res['message']}")
                else:
                    st.error(f"❌ {res['message']}")
    elif st.session_state.get("automation_status"):
        prev = st.session_state.automation_status
        if prev.get("success"):
            st.success(f"✅ {prev['message']}")
            st.caption(f"ID da submissão: `{prev.get('submission_id')}`")
        elif prev.get("uncertain"):
            st.warning(f"⚠️ {prev['message']}")
        else:
            st.error(f"❌ {prev['message']}")

st.caption("⚠️ Nota importante: Os conteúdos sugeridos por inteligência artificial devem passar por revisão e validação humana antes de publicação oficial.")
